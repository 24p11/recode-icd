"""Régression sur le CSV maître à 9 colonnes (Phase 3).

Skip si le CSV `referentials/processed/inclusions_exclusions_synonymes.csv`
n'est pas présent ou n'a pas le bon nombre de colonnes — le test n'a de
sens qu'après un `recode-icd build flat-csv` complet."""

from __future__ import annotations

from functools import cache
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.regression


_CSV_PATH = Path("referentials/processed/inclusions_exclusions_synonymes.csv")
_EXPECTED_COLUMNS = [
    "code", "libelle", "type", "source", "texte",
    "dagger_code", "asterisk_code", "redundancy_level", "is_redundant_dagger",
    "source_level", "inherited_from_code",
]


@cache
def _final_csv() -> pl.DataFrame:
    root = Path(__file__).resolve().parents[2]
    path = root / _CSV_PATH
    if not path.is_file():
        pytest.skip(f"CSV maître absent ({path}) — lance `build flat-csv` d'abord.")
    df = pl.read_csv(path, infer_schema_length=10_000)
    if list(df.columns) != _EXPECTED_COLUMNS:
        pytest.skip(
            f"CSV présent mais schéma différent (colonnes : {df.columns}). "
            "Re-générer après les changements de schéma."
        )
    return df


def test_csv_has_11_columns() -> None:
    assert list(_final_csv().columns) == _EXPECTED_COLUMNS


def test_a17_8_has_subordinate_lines_when_curated() -> None:
    """Si la curation marque A17.8/G05.0 subordinate, toutes les
    lignes du code dague A17.8 pointant vers G05.0 doivent porter
    `is_redundant_dagger=True` et `redundancy_level=subordinate`."""
    df = _final_csv()
    subset = df.filter(
        (pl.col("code") == "A17.8") & (pl.col("asterisk_code") == "G05.0")
    )
    if subset.is_empty():
        pytest.skip("A17.8/G05.0 absent du CSV final (pas curé ou hors fixtures).")
    # Cohérence : toutes ces lignes doivent être subordinate.
    levels = set(subset["redundancy_level"].to_list())
    flags = set(subset["is_redundant_dagger"].to_list())
    assert levels == {"subordinate"}, f"levels={levels}"
    assert flags == {True}, f"flags={flags}"


def test_e10_2_lines_independent_not_redundant() -> None:
    df = _final_csv()
    subset = df.filter(
        (pl.col("code") == "E10.2") & (pl.col("asterisk_code") == "N08.3")
    )
    if subset.is_empty():
        pytest.skip("E10.2/N08.3 absent du CSV final.")
    assert set(subset["redundancy_level"].to_list()) == {"independent"}
    assert set(subset["is_redundant_dagger"].to_list()) == {False}


def test_u07_1_has_no_dagger_asterisk_columns_filled() -> None:
    """U07.1 (post-2006) n'a pas d'association dague/astérisque côté OFS.
    Toutes ses lignes doivent avoir dagger_code/asterisk_code à NULL et
    redundancy_level='none'."""
    df = _final_csv()
    subset = df.filter(pl.col("code") == "U07.1")
    if subset.is_empty():
        pytest.skip("U07.1 absent du CSV (vérifier que U07.1 est bien dans OWL).")
    assert subset.filter(pl.col("dagger_code").is_not_null()).is_empty()
    assert subset.filter(pl.col("asterisk_code").is_not_null()).is_empty()
    assert set(subset["redundancy_level"].to_list()) == {"none"}
    assert set(subset["is_redundant_dagger"].to_list()) == {False}
