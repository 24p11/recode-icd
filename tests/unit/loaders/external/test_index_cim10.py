"""Tests du loader Index CIM-10 vol3.

Le loader lit la feuille "Cim Alphabétique" du classeur HECTOR. Les
tests sont marqués `regression` parce qu'ils nécessitent le vrai
fichier xlsx (~50 MB), pas un mock — l'effort de mocker fastexcel
est disproportionné par rapport à l'intérêt.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd._normalize import _STANDARD_CODE_RE
from recode_icd.loaders.external import load_index_cim10
from recode_icd.loaders.external._constants import (
    INDEX_CIM10_SHEET,
    INDEX_CIM10_SHEET_LABEL,
    INDEX_CIM10_SOURCE,
)

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
    return load_index_cim10(HECTOR_XLSX)


def test_returns_correct_schema(df: pl.DataFrame) -> None:
    assert df.columns == ["code", "libelle", "type", "source", "metadata"]
    assert df.schema["metadata"] == pl.Struct(
        {"sheet_name": pl.String, "sheet_label": pl.String}
    )


def test_all_rows_type_synonyme(df: pl.DataFrame) -> None:
    assert set(df["type"].unique().to_list()) == {"synonyme"}


def test_all_rows_source_INDEX_CIM10_VOL3(df: pl.DataFrame) -> None:
    assert set(df["source"].unique().to_list()) == {INDEX_CIM10_SOURCE}


def test_metadata_constant(df: pl.DataFrame) -> None:
    sheet_names = (
        df.select(pl.col("metadata").struct["sheet_name"]).to_series().unique().to_list()
    )
    sheet_labels = (
        df.select(pl.col("metadata").struct["sheet_label"]).to_series().unique().to_list()
    )
    assert sheet_names == [INDEX_CIM10_SHEET]
    assert sheet_labels == [INDEX_CIM10_SHEET_LABEL]


def test_volumetry_within_range(df: pl.DataFrame) -> None:
    """Le rapport d'inventaire 2026-05-25 mesurait ~41 332 lignes
    valides. On accepte ±20 %."""
    assert 33_000 <= df.height <= 50_000, f"volumétrie inattendue : {df.height}"


def test_normalizes_compact_codes(df: pl.DataFrame) -> None:
    """Tous les codes émis doivent matcher le format standard
    (avec ou sans point). Le filtre des compact → standard a eu lieu."""
    sample = df["code"].sample(n=200, seed=42).to_list()
    for code in sample:
        assert _STANDARD_CODE_RE.match(code), f"code non standard : {code!r}"


def test_specific_compact_code_normalized(df: pl.DataFrame) -> None:
    """`A000` → `A00.0` doit être présent."""
    assert df.filter(pl.col("code") == "A00.0").height > 0


def test_ignores_nocode(df: pl.DataFrame) -> None:
    """Aucune ligne ne doit avoir code ∈ {"nocode", "NOCODE"}."""
    assert df.filter(pl.col("code").str.to_lowercase() == "nocode").is_empty()


def test_no_trailing_dash_codes(df: pl.DataFrame) -> None:
    """Les intervalles ouverts `B65-` doivent avoir été normalisés à
    `B65` — aucun code en sortie ne contient un tiret."""
    assert df.filter(pl.col("code").str.contains("-")).is_empty()


def test_libelle_non_empty(df: pl.DataFrame) -> None:
    """Toutes les lignes doivent avoir un libellé non vide après strip."""
    empty = df.filter(pl.col("libelle").str.strip_chars().str.len_chars() == 0)
    assert empty.is_empty()
