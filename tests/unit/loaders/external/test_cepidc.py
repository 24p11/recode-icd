"""Tests du loader CepiDc 2015.

Les tests sont marqués `regression` car ils nécessitent le vrai fichier
CSV (~12 MB). Un test unitaire pur (sans le vrai fichier) couvre la
conversion code via DataFrame mocké en fin de fichier.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd._normalize import _STANDARD_CODE_RE
from recode_icd.loaders.external import load_cepidc
from recode_icd.loaders.external._constants import CEPIDC_SOURCE

pytestmark = pytest.mark.regression


CEPIDC_CSV = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "CIM_CEPIDC_2015"
    / "CepiDc_Dictionnaire2015.csv"
)


def _require_csv() -> None:
    if not CEPIDC_CSV.is_file():
        pytest.skip(f"Fichier CepiDc absent : {CEPIDC_CSV}")


@pytest.fixture(scope="module")
def df() -> pl.DataFrame:
    _require_csv()
    return load_cepidc(CEPIDC_CSV)


def test_returns_correct_schema(df: pl.DataFrame) -> None:
    assert df.columns == ["code", "libelle", "type", "source", "metadata"]
    assert df.schema["metadata"] == pl.Struct(
        {"source_file": pl.String, "version_year": pl.String}
    )


def test_all_rows_type_synonyme(df: pl.DataFrame) -> None:
    assert set(df["type"].unique().to_list()) == {"synonyme"}


def test_all_rows_source_CEPIDC_2015(df: pl.DataFrame) -> None:
    assert set(df["source"].unique().to_list()) == {CEPIDC_SOURCE}


def test_metadata_constant(df: pl.DataFrame) -> None:
    source_files = (
        df.select(pl.col("metadata").struct["source_file"])
        .to_series()
        .unique()
        .to_list()
    )
    version_years = (
        df.select(pl.col("metadata").struct["version_year"])
        .to_series()
        .unique()
        .to_list()
    )
    assert source_files == ["CepiDc_Dictionnaire2015.csv"]
    assert version_years == ["2015"]


def test_volumetry_within_range(df: pl.DataFrame) -> None:
    """147 340 lignes utilisables observées (1 null + 4 non parseables
    filtrés sur 147 341 brutes). On accepte ±5 % après dédup tolérante
    intra-source."""
    assert 140_000 <= df.height <= 150_000, f"volumétrie inattendue : {df.height}"


def test_all_codes_standard_format(df: pl.DataFrame) -> None:
    sample = df["code"].sample(n=500, seed=42).to_list()
    for code in sample:
        assert _STANDARD_CODE_RE.match(code), f"code non standard : {code!r}"


def test_specific_compact_code_normalized(df: pl.DataFrame) -> None:
    """`A181` (CepiDc compact) → `A18.1` (standard) doit être présent."""
    assert df.filter(pl.col("code") == "A18.1").height > 0


def test_3char_code_preserved(df: pl.DataFrame) -> None:
    """`R51` (code 3-car) doit rester `R51`, pas `R5.1`."""
    assert df.filter(pl.col("code") == "R51").height > 0


def test_libelle_non_empty(df: pl.DataFrame) -> None:
    empty = df.filter(pl.col("libelle").str.strip_chars().str.len_chars() == 0)
    assert empty.is_empty()


def test_libelle_no_nulls(df: pl.DataFrame) -> None:
    assert df.filter(pl.col("libelle").is_null()).is_empty()


def test_n_distinct_codes(df: pl.DataFrame) -> None:
    """~6 290 codes distincts observés après normalisation et filtrage."""
    n = df["code"].n_unique()
    assert 6_000 <= n <= 6_500, f"nb codes distincts inattendu : {n}"


# ----------------------------------------------------------------------
# Tests unitaires purs (sans le vrai fichier)
# ----------------------------------------------------------------------


@pytest.mark.unit
def test_normalize_compact_code_3char_unchanged() -> None:
    """Garantit que les codes 3-car (`R51`) ne sont pas transformés en
    `R5.1` — cas spécifique CepiDc majoritairement à 3-4 caractères."""
    from recode_icd._normalize import normalize_compact_code

    assert normalize_compact_code("R51") == "R51"
    assert normalize_compact_code("A18") == "A18"


@pytest.mark.unit
def test_normalize_compact_code_4char_split() -> None:
    """`A181` → `A18.1` (insertion du point après les 3 premiers chars)."""
    from recode_icd._normalize import normalize_compact_code

    assert normalize_compact_code("A181") == "A18.1"
    assert normalize_compact_code("Z944") == "Z94.4"
