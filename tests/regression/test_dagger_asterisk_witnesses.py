"""Régression sur les codes témoins dague/astérisque.

Construit à la volée la table DAGSTAR enrichie depuis les vraies
données OFS et y applique le CSV de curation (s'il existe) pour
matcher l'état du pipeline post-Phase 3. Vérifie ensuite que les
paires témoins ont les `redundancy_level` attendus.

Codes témoins (cf docs/source_mapping.md §"Couples dague/astérisque"
et CLAUDE.md §"Conventions de code") :
  - A17.8 / G05.0 : pressenti subordinate
  - A18.1 / N33.0 : à curer (souvent subordinate)
  - E10.2 / N08.3 : independent évident
  - U07.1         : post-2006, pas d'impact dague/astérisque
"""

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
_CURATION_CSV = Path("referentials/curation/dagger_curation.csv")


def _find_ofs_dir() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    for candidate in _OFS_DIR_CANDIDATES:
        path = root / candidate
        if path.is_dir() and any(path.glob("*.txt")):
            return path
    return None


def _find_curation_csv() -> Path | None:
    root = Path(__file__).resolve().parents[2]
    path = root / _CURATION_CSV
    return path if path.is_file() else None


@cache
def _enriched_table() -> pl.DataFrame:
    """Table DAGSTAR enrichie, curation appliquée si le CSV existe."""
    ofs_dir = _find_ofs_dir()
    if ofs_dir is None:
        pytest.skip("OFS raw dir not found — regression test skipped")
    master = _read_ofs_table(ofs_dir / "MASTER.txt")
    dagstar = _read_ofs_table(ofs_dir / "DAGSTAR.txt")
    libelle = _read_ofs_table(ofs_dir / "LIBELLE.txt")
    table = dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)
    curation = _find_curation_csv()
    if curation is not None:
        table, _ = dagger_asterisk.apply_curation(table, curation)
    return table


def _curation_row(dagger: str, asterisk: str) -> dict[str, str] | None:
    """Lit la ligne (dagger, asterisk) du CSV de curation s'il existe."""
    csv = _find_curation_csv()
    if csv is None:
        return None
    sep = ";" if csv.read_text(encoding="utf-8").splitlines()[0].count(";") > 0 else ","
    df = pl.read_csv(csv, infer_schema_length=0, separator=sep)
    row = df.filter(
        (pl.col("dagger_code") == dagger) & (pl.col("asterisk_code") == asterisk)
    )
    return row.row(0, named=True) if row.height else None


def test_a18_1_n33_0_pair_present() -> None:
    """A18.1+ Tuberculose génito-urinaire / N33.0* Cystite tuberculeuse —
    cas canonique cité dans docs/source_mapping.md. `redundancy_level`
    doit refléter la curation manuelle (si CSV présent), sinon le défaut."""
    table = _enriched_table()
    row = table.filter(
        (pl.col("dagger_code") == "A18.1") & (pl.col("asterisk_code") == "N33.0")
    )
    assert len(row) == 1, "paire A18.1/N33.0 attendue exactement une fois"
    r = row.row(0, named=True)
    assert "U" in r["levels_present"]
    assert r["dagger_label"] is not None
    assert r["asterisk_label"] is not None
    curated = _curation_row("A18.1", "N33.0")
    expected = curated["redundancy_level"] if curated else "independent"
    if expected == "":
        expected = "independent"
    assert r["redundancy_level"] == expected


def test_a17_8_g05_0_pair_is_subordinate_when_curated() -> None:
    """A17.8+ Tuberculose système nerveux / G05.0* Encéphalite tuberculeuse —
    pressenti subordinate. Si le CSV de curation est présent et marque
    cette paire `subordinate`, la table doit le refléter."""
    table = _enriched_table()
    row = table.filter(
        (pl.col("dagger_code") == "A17.8") & (pl.col("asterisk_code") == "G05.0")
    )
    assert len(row) == 1
    r = row.row(0, named=True)
    assert len(r["levels_present"]) >= 1
    curated = _curation_row("A17.8", "G05.0")
    expected = curated["redundancy_level"] if curated else "independent"
    if expected == "":
        expected = "independent"
    assert r["redundancy_level"] == expected


def test_e10_2_n08_3_pair_independent() -> None:
    """E10.2+ Diabète type 1 avec complications rénales / N08.3* Glomérulopathie
    au cours du diabète — independent évident, ne doit pas être curé subordinate."""
    table = _enriched_table()
    row = table.filter(
        (pl.col("dagger_code") == "E10.2") & (pl.col("asterisk_code") == "N08.3")
    )
    assert len(row) == 1
    r = row.row(0, named=True)
    assert r["redundancy_level"] == "independent"


def test_u07_1_no_dagger_asterisk_impact() -> None:
    """U07.1 (COVID-19) est post-2006 : il n'a pas d'entrée DAGSTAR
    côté OFS et ne doit donc apparaître dans aucune paire de la table."""
    table = _enriched_table()
    involved = table.filter(
        (pl.col("dagger_code") == "U07.1") | (pl.col("asterisk_code") == "U07.1")
    )
    assert involved.is_empty()


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
