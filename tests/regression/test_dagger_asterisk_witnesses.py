"""Régression sur les codes témoins dague/astérisque (cf. spec
Phase 1 §"Tester sur A18.1, A17.8, E10.2"). Charge la table enrichie
à partir des vraies données OFS et vérifie que les paires attendues
sont présentes avec leurs propriétés clés."""

from __future__ import annotations

from functools import cache
from pathlib import Path

import polars as pl
import pytest

from recode_icd.loaders.ofs import _read as _read_ofs_table
from recode_icd.relations import dagger_asterisk

pytestmark = pytest.mark.regression


_OFS_DIR_CANDIDATES = (
    "referentials/raw/ofs",
    "referentials/raw/CIM_OFS_SW_2006",
    "data/CIM_OFS_SW_2006",
)


def _find_ofs_dir() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    for candidate in _OFS_DIR_CANDIDATES:
        path = root / candidate
        if path.is_dir() and any(path.glob("*.txt")):
            return path
    return None


@cache
def _enriched_table() -> pl.DataFrame:
    ofs_dir = _find_ofs_dir()
    if ofs_dir is None:
        pytest.skip("OFS raw dir not found — regression test skipped")
    master = _read_ofs_table(ofs_dir / "MASTER.txt")
    dagstar = _read_ofs_table(ofs_dir / "DAGSTAR.txt")
    libelle = _read_ofs_table(ofs_dir / "LIBELLE.txt")
    return dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)


def test_a18_1_n33_0_pair_present() -> None:
    """A18.1+ Tuberculose génito-urinaire / N33.0* Cystite tuberculeuse —
    cas canonique cité dans docs/source_mapping.md."""
    table = _enriched_table()
    row = table.filter(
        (pl.col("dagger_code") == "A18.1") & (pl.col("asterisk_code") == "N33.0")
    )
    assert len(row) == 1, "paire A18.1/N33.0 attendue exactement une fois"
    r = row.row(0, named=True)
    # Au minimum, le côté descripteur (U) sur A18.1 doit être présent.
    assert "U" in r["levels_present"]
    assert r["redundancy_level"] == "independent"
    assert r["dagger_label"] is not None
    assert r["asterisk_label"] is not None


def test_a17_8_g05_0_pair_present() -> None:
    """A17.8+ Tuberculose système nerveux / G05.0* Encéphalite tuberculeuse —
    cas pressenti subordinate (à curer en Phase 2)."""
    table = _enriched_table()
    row = table.filter(
        (pl.col("dagger_code") == "A17.8") & (pl.col("asterisk_code") == "G05.0")
    )
    assert len(row) == 1
    r = row.row(0, named=True)
    assert r["redundancy_level"] == "independent"  # Phase 1 : pas de YAML
    assert len(r["levels_present"]) >= 1


def test_e10_2_n08_3_pair_present() -> None:
    """E10.2+ Diabète type 1 avec complications rénales / N08.3* Glomérulopathie
    au cours du diabète — cas independent évident."""
    table = _enriched_table()
    row = table.filter(
        (pl.col("dagger_code") == "E10.2") & (pl.col("asterisk_code") == "N08.3")
    )
    assert len(row) == 1
    r = row.row(0, named=True)
    assert r["redundancy_level"] == "independent"


def test_volumetrie_paires_completes_plausible() -> None:
    """Sanity-check global : le nombre de paires complètes (les deux
    faces résolues) est dans le range attendu (~1300 d'après le doc)."""
    table = _enriched_table()
    complete = table.filter(
        pl.col("dagger_code").is_not_null() & pl.col("asterisk_code").is_not_null()
    )
    n = len(complete)
    # Volumétrie réelle observée : ~720 paires complètes (les 1352
    # lignes DAGSTAR brutes représentent une même paire vue depuis
    # plusieurs angles daget). Marge large pour détecter une régression
    # majeure sans casser sur de petites évolutions de référentiel.
    assert 500 <= n <= 1000, f"nombre de paires complètes inhabituel : {n}"


def test_aucun_doublon_dagger_asterisk() -> None:
    """Une paire (dagger_code, asterisk_code) ne doit apparaître qu'une fois."""
    table = _enriched_table().filter(
        pl.col("dagger_code").is_not_null() & pl.col("asterisk_code").is_not_null()
    )
    duplicates = table.group_by(["dagger_code", "asterisk_code"]).len().filter(
        pl.col("len") > 1
    )
    assert duplicates.is_empty(), (
        f"paires en doublon détectées : {duplicates}"
    )
