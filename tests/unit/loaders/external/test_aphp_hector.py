"""Tests du loader AP-HP HECTOR (9 feuilles métier).

Tests marqués `regression` car ils dépendent du vrai fichier xlsx.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd._normalize import _STANDARD_CODE_RE
from recode_icd.loaders.external import load_aphp_hector
from recode_icd.loaders.external._constants import APHP_SHEET_TO_SOURCE

pytestmark = pytest.mark.regression


HECTOR_XLSX = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "CIM_APHP_2019"
    / "Dictionnaire_Hector_MAJ062019.xlsx"
)


def _require_xlsx() -> None:
    if not HECTOR_XLSX.is_file():
        pytest.skip(f"Fichier HECTOR absent : {HECTOR_XLSX}")


@pytest.fixture(scope="module")
def df() -> pl.DataFrame:
    _require_xlsx()
    return load_aphp_hector(HECTOR_XLSX)


def test_returns_correct_schema(df: pl.DataFrame) -> None:
    assert df.columns == ["code", "libelle", "type", "source", "metadata"]
    assert df.schema["metadata"] == pl.Struct(
        {"sheet_name": pl.String, "sheet_label": pl.String}
    )


def test_loads_all_9_sheets(df: pl.DataFrame) -> None:
    """Une source distincte par spécialité, 9 au total."""
    sources = set(df["source"].unique().to_list())
    expected = set(APHP_SHEET_TO_SOURCE.values())
    assert sources == expected


def test_all_rows_type_synonyme(df: pl.DataFrame) -> None:
    assert set(df["type"].unique().to_list()) == {"synonyme"}


def test_endocrinologie_label_divergence(df: pl.DataFrame) -> None:
    """La feuille "Endocrinologie" porte l'étiquette `ED1` en
    colonne 2 (et non `END1`). Le loader doit utiliser le nom de
    feuille comme clé canonique → `source=APHP_ENDOCRINOLOGIE`. La
    metadata expose le `sheet_label` réel (`ED1`)."""
    endo = df.filter(pl.col("source") == "APHP_ENDOCRINOLOGIE")
    assert endo.height > 0, "feuille Endocrinologie attendue"
    labels = (
        endo.select(pl.col("metadata").struct["sheet_label"]).to_series().unique().to_list()
    )
    assert labels == ["ED1"], (
        f"sheet_label attendu = ED1 (et non END1) ; obtenu = {labels}"
    )


def test_volumetry_within_range(df: pl.DataFrame) -> None:
    """Rapport d'inventaire : ~5 040 lignes valides toutes feuilles
    confondues. ±20 %."""
    assert 4_000 <= df.height <= 6_500, f"volumétrie inattendue : {df.height}"


def test_per_sheet_volumetry_plausible(df: pl.DataFrame) -> None:
    """Chaque spécialité a au moins 30 lignes (la plus petite
    observée est SRLF avec 51 valides). Garde-fou contre une
    régression silencieuse qui chargerait une feuille vide."""
    counts = df.group_by("source").len().to_dicts()
    for row in counts:
        assert row["len"] >= 30, f"feuille trop petite : {row}"


def test_codes_match_standard_pattern(df: pl.DataFrame) -> None:
    sample = df["code"].sample(n=200, seed=42).to_list()
    for code in sample:
        assert _STANDARD_CODE_RE.match(code), f"code non standard : {code!r}"


def test_no_nocode_in_output(df: pl.DataFrame) -> None:
    assert df.filter(pl.col("code").str.to_lowercase() == "nocode").is_empty()


def test_no_internal_duplicates_per_sheet(df: pl.DataFrame) -> None:
    """Dédup tolérante intra-feuille appliquée : (code, libellé,
    source) doit être unique."""
    from recode_icd._normalize import normalize_for_match

    dups = (
        df.with_columns(
            pl.col("libelle")
            .map_elements(normalize_for_match, return_dtype=pl.String)
            .alias("_norm")
        )
        .group_by(["code", "_norm", "source"])
        .len()
        .filter(pl.col("len") > 1)
    )
    assert dups.is_empty(), f"doublons intra-feuille : {dups}"
