"""Codes injectés depuis le kit ATIH, sur les artefacts réels (D3)."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.regression

_RACINE = Path(__file__).resolve().parents[2]
_PROCESSED = _RACINE / "referentials" / "processed"
_RAPPORT = _RACINE / "reports" / "atih_only_codes.csv"


@pytest.fixture(scope="module")
def merged() -> pl.DataFrame:
    path = _PROCESSED / "merged_codes.parquet"
    if not path.is_file():
        pytest.skip(f"{path} absent.")
    df = pl.read_parquet(path)
    if "source_existence" not in df.columns:
        pytest.skip("merged antérieur à D3 (`recode-icd build owl --atih`).")
    return df


def test_les_72_extensions_atih_sont_au_nested_set(merged: pl.DataFrame) -> None:
    injectes = merged.filter(pl.col("source_existence") == "ATIH")
    assert injectes.height == 72
    assert set(injectes["statut_mco"].to_list()) == {"codable"}
    assert not injectes["code"].str.contains(r"^[VWXY]").any(), "le chapitre XX se compose (D5)"


@pytest.mark.parametrize(
    ("code", "parent"),
    [
        ("I70.00", "I70.0"),
        ("J96.100", "J96.10"),
        ("M45+0", "M45"),
        ("M62.80", "M62.8"),
        ("M83.05", "M83.0"),
    ],
)
def test_un_code_injecte_est_sous_son_ancetre(merged: pl.DataFrame, code: str, parent: str) -> None:
    ligne = merged.filter(pl.col("code") == code).row(0, named=True)
    pere = merged.filter(pl.col("code") == parent).row(0, named=True)
    assert ligne["source_existence"] == "ATIH"
    assert ligne["path"].endswith(f"/{parent}/{code}")
    assert pere["left"] < ligne["left"] < ligne["right"] < pere["right"]


def test_le_rapport_liste_les_injectes() -> None:
    if not _RAPPORT.is_file():
        pytest.skip(f"{_RAPPORT} absent.")
    rapport = pl.read_csv(_RAPPORT)
    assert rapport.height == 72
    assert {"code", "code_atih", "label", "path", "type_mco", "statut_mco"} <= set(rapport.columns)


def test_un_code_injecte_herite_et_entre_au_csv() -> None:
    """`I70.00` n'a aucune note propre : ses lignes sont celles héritées de
    `I70.0` et des niveaux supérieurs — et il est au CSV (D2 + D3)."""
    csv_path = _PROCESSED / "inclusions_exclusions_synonymes.csv"
    if not csv_path.is_file():
        pytest.skip("CSV absent.")
    csv = pl.read_csv(csv_path, columns=["code", "source_level", "inherited_from_code"])
    lignes = csv.filter(pl.col("code") == "I70.00")
    assert lignes.height > 0
    assert set(lignes["source_level"].to_list()) <= {"chapter", "block", "category", "code"}
    # `I70.0` n'a aucune note propre : l'héritage vient de `I70` et du chapitre.
    herites = set(lignes["inherited_from_code"].drop_nulls().to_list())
    assert herites and herites <= {"I70", "I70-I79", "IX", "I70.0"}, herites
