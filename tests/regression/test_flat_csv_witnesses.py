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
    "source_level", "inherited_from_code",
    "is_dagger_in_pair", "is_asterisk_in_pair",
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


def test_csv_has_9_columns() -> None:
    assert list(_final_csv().columns) == _EXPECTED_COLUMNS


def test_a17_8_is_dagger_in_pair() -> None:
    """Refonte 2026-05-30 : A17.8 (côté dague de la paire avec G05.0,
    subordinate selon la curation) doit avoir `is_dagger_in_pair=True`
    sur toutes ses lignes. Le détail de la subordinate vit désormais
    dans dagger_asterisk.parquet, plus dans le CSV."""
    df = _final_csv()
    subset = df.filter(pl.col("code") == "A17.8")
    if subset.is_empty():
        pytest.skip("A17.8 absent du CSV final.")
    assert subset.filter(~pl.col("is_dagger_in_pair")).is_empty(), (
        "A17.8 doit avoir is_dagger_in_pair=True sur toutes ses lignes"
    )


def test_e10_2_is_dagger_in_pair() -> None:
    """Refonte 2026-05-30 : E10.2 (côté dague de la paire avec N08.3,
    independent) doit avoir `is_dagger_in_pair=True`."""
    df = _final_csv()
    subset = df.filter(pl.col("code") == "E10.2")
    if subset.is_empty():
        pytest.skip("E10.2 absent du CSV final.")
    assert subset.filter(~pl.col("is_dagger_in_pair")).is_empty(), (
        "E10.2 doit avoir is_dagger_in_pair=True sur toutes ses lignes"
    )


def test_a18_1_ans_exclusion_redirects_use_parentheses() -> None:
    """Chantier 4 (2026-06-03) : les codes de redirection ANS des
    exclusions de A18.1 doivent apparaître entre parenthèses et plus
    entre crochets dans le CSV final."""
    df = _final_csv()
    subset = df.filter(
        (pl.col("code") == "A18.1")
        & (pl.col("type") == "exclusion")
        & (pl.col("source") == "ANS")
    )
    if subset.is_empty():
        pytest.skip("A18.1 sans exclusion ANS dans le CSV final.")
    joined = " || ".join(subset["texte"].drop_nulls().to_list())
    for code in ("B20.0", "J65", "B90.-", "P37.0"):
        assert f"[{code}]" not in joined, (
            f"crochet [{code}] résiduel dans A18.1 — normalisation incomplète"
        )
        assert f"({code})" in joined, (
            f"redirection ({code}) attendue dans A18.1"
        )


def test_u07_1_ans_exclusion_redirects_use_parentheses() -> None:
    """Chantier 4 (2026-06-03) : U07.1 (post-2006, ANS exclusivement)
    doit voir ses redirections normalisées en parenthèses."""
    df = _final_csv()
    subset = df.filter(
        (pl.col("code") == "U07.1")
        & (pl.col("type") == "exclusion")
        & (pl.col("source") == "ANS")
    )
    if subset.is_empty():
        pytest.skip("U07.1 sans exclusion ANS dans le CSV final.")
    joined = " || ".join(subset["texte"].drop_nulls().to_list())
    for code in ("B34.2", "B97.2", "U04.9"):
        assert f"[{code}]" not in joined, (
            f"crochet [{code}] résiduel dans U07.1"
        )
        assert f"({code})" in joined, (
            f"redirection ({code}) attendue dans U07.1"
        )


def test_u07_1_has_no_dagger_asterisk_pair() -> None:
    """U07.1 (post-2006) n'a pas d'association dague/astérisque côté OFS.
    Refonte 2026-05-30 : doit avoir les deux flags à False."""
    df = _final_csv()
    subset = df.filter(pl.col("code") == "U07.1")
    if subset.is_empty():
        pytest.skip("U07.1 absent du CSV (vérifier que U07.1 est bien dans OWL).")
    assert subset.filter(pl.col("is_dagger_in_pair")).is_empty()
    assert subset.filter(pl.col("is_asterisk_in_pair")).is_empty()
