"""Tests du loader ORPHANET.

La fixture `orphanet_mini.xml` contient 5 Disorder couvrant les
4 cas distincts : E avec synonymes, NTBT, BTNT (ignoré), code
non parseable (ignoré), et un piège qui distingue
DisorderMappingRelation (à lire) de DisorderMappingICDRelation (à
ne PAS lire).
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.loaders.external import load_orphanet

pytestmark = pytest.mark.unit


FIXTURE = Path(__file__).parent / "fixtures" / "orphanet_mini.xml"


@pytest.fixture(scope="module")
def df() -> pl.DataFrame:
    return load_orphanet(FIXTURE)


def test_returns_correct_schema(df: pl.DataFrame) -> None:
    assert df.columns == ["code", "libelle", "type", "source", "metadata"]
    # metadata est un pl.Struct
    assert df.schema["metadata"] == pl.Struct(
        {"orpha_code": pl.String, "relation": pl.String}
    )


def test_all_sources_are_orphanet(df: pl.DataFrame) -> None:
    assert set(df["source"].unique().to_list()) == {"ORPHANET"}


def test_filters_only_E_and_NTBT(df: pl.DataFrame) -> None:
    """BTNT (Disorder 3) et code non parseable (Disorder 5) sont
    filtrés. Seuls Disorder 1, 2, 4 produisent des lignes."""
    relations_seen = (
        df.select(pl.col("metadata").struct["relation"]).to_series().unique().to_list()
    )
    assert set(relations_seen) == {"E", "NTBT"}


def test_E_produces_synonyme(df: pl.DataFrame) -> None:
    # Disorder 1 (D59.5) : 1 Name + 2 synonymes = 3 lignes synonyme
    subset = df.filter(pl.col("code") == "D59.5")
    assert subset.height == 3
    assert set(subset["type"].to_list()) == {"synonyme"}


def test_NTBT_produces_inclusion(df: pl.DataFrame) -> None:
    # Disorder 2 (Q77.3) : 1 Name + 1 synonyme = 2 lignes inclusion
    subset = df.filter(pl.col("code") == "Q77.3")
    assert subset.height == 2
    assert set(subset["type"].to_list()) == {"inclusion"}


def test_reads_disorder_mapping_relation_not_icd_relation(df: pl.DataFrame) -> None:
    """Le piège : Disorder 4 a DisorderMappingICDRelation = "Code
    spécifique" mais DisorderMappingRelation = "E". On doit lire la
    relation E et produire un synonyme — pas confondre avec "Code
    spécifique"."""
    subset = df.filter(pl.col("code") == "M30.0")
    assert subset.height == 1, "M30.0 doit produire exactement 1 ligne (Name)"
    row = subset.row(0, named=True)
    assert row["type"] == "synonyme"
    assert row["metadata"]["relation"] == "E"
    # Si on avait lu la mauvaise propriété, on aurait trouvé
    # "Code spécifique" ou similaire ; vérifions explicitement que ce
    # texte n'a pas pollué le sigle relation.
    assert "Code" not in row["metadata"]["relation"]


def test_ignores_btnt_and_unparseable(df: pl.DataFrame) -> None:
    assert df.filter(pl.col("code") == "X99.9").is_empty(), "BTNT doit être ignoré"
    # Le code non parseable du Disorder 5 ne doit jamais sortir
    assert "NOT_A_CODE" not in df["code"].to_list()


def test_synonyms_explode_into_separate_rows(df: pl.DataFrame) -> None:
    """Disorder 1 a 2 synonymes + 1 Name → 3 lignes distinctes pour D59.5."""
    libelles = df.filter(pl.col("code") == "D59.5")["libelle"].sort().to_list()
    assert "Hémoglobinurie paroxystique nocturne" in libelles
    assert "HPN" in libelles
    assert "Maladie de Marchiafava-Micheli" in libelles


def test_metadata_carries_orpha_code(df: pl.DataFrame) -> None:
    subset = df.filter(pl.col("code") == "D59.5")
    orpha_codes = subset.select(
        pl.col("metadata").struct["orpha_code"]
    ).to_series().unique().to_list()
    assert orpha_codes == ["447"]


def test_xsd_missing_is_warning_not_error(tmp_path: Path) -> None:
    """Le paramètre xsd_path pointant vers un fichier inexistant
    produit un warning, pas une exception."""
    fake_xsd = tmp_path / "nonexistent.xsd"
    df = load_orphanet(FIXTURE, xsd_path=fake_xsd)
    assert df.height > 0  # loader a quand même tourné


def test_missing_xml_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_orphanet(tmp_path / "missing.xml")
