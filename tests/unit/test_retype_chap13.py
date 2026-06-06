"""Tests unitaires pour `retype_chap13_altlabels` et
`find_orphan_type_d_codes` dans `recode_icd.merge`.

Périmètre : retypage des `skos:altLabel` ANS des codes type=D du
chapitre XIII en `inclusion` ANS. Critère strict : `ofs_type=="D"` ET
`depth==5` (5e position OMS du tableau de codage de la localisation
ostéo-articulaire).

Cf `docs/sessions/2026-06-06_localisations_chap13_ofs.md`.
"""

from __future__ import annotations

import polars as pl
import pytest

from recode_icd.merge import (
    find_orphan_type_d_codes,
    retype_chap13_altlabels,
)

pytestmark = pytest.mark.unit


def _make_owl(rows: list[dict]) -> pl.DataFrame:
    """DataFrame OWL minimal — uniquement les colonnes lues par les fonctions."""
    return pl.DataFrame(
        rows,
        schema={
            "code": pl.String,
            "synonymes": pl.List(pl.String),
        },
    )


def _make_ofs(rows: list[dict]) -> pl.DataFrame:
    """DataFrame OFS minimal — colonnes nécessaires aux fonctions
    (`code`, `ofs_type`, `depth`, `path`, `label`)."""
    return pl.DataFrame(
        rows,
        schema={
            "code": pl.String,
            "ofs_type": pl.String,
            "depth": pl.Int64,
            "path": pl.String,
            "label": pl.String,
        },
    )


# ----------------------------------------------------------------------
# retype_chap13_altlabels
# ----------------------------------------------------------------------


def test_retype_strips_synonymes_for_type_d_depth5() -> None:
    """Code ofs_type=D ET depth=5 : altLabel retypés en inclusion,
    synonymes vidés dans owl_filtered."""
    owl = _make_owl(
        [
            {"code": "M01.08", "synonymes": ["cou", "tronc", "crâne"]},
        ]
    )
    ofs = _make_ofs(
        [
            {
                "code": "M01.08",
                "ofs_type": "D",
                "depth": 5,
                "path": "(M00-M99)/(M00-M03)/M01/M01.0/M01.08",
                "label": "arthrite méningococcique | autres",
            },
        ]
    )
    owl_filtered, extras = retype_chap13_altlabels(owl, ofs)

    # owl_filtered : synonymes vidés
    assert list(owl_filtered.filter(pl.col("code") == "M01.08")["synonymes"][0]) == []

    # extras : 3 lignes inclusion ANS
    assert extras.height == 3
    assert set(extras["type"].to_list()) == {"inclusion"}
    assert set(extras["source"].to_list()) == {"OWL_ANS"}
    assert sorted(extras["texte"].to_list()) == ["cou", "crâne", "tronc"]


def test_retype_ignores_type_d_other_depth() -> None:
    """Code ofs_type=D mais depth=4 (chapitres F/S-T) : non touché."""
    owl = _make_owl(
        [{"code": "F00.00", "synonymes": ["démence Alzheimer"]}]
    )
    ofs = _make_ofs(
        [
            {
                "code": "F00.00",
                "ofs_type": "D",
                "depth": 4,  # intermédiaire, hors périmètre
                "path": "(F00-F99)/(F00-F09)/F00/F00.0/F00.00",
                "label": "démence",
            }
        ]
    )
    owl_filtered, extras = retype_chap13_altlabels(owl, ofs)

    # Synonymes préservés
    assert list(
        owl_filtered.filter(pl.col("code") == "F00.00")["synonymes"][0]
    ) == ["démence Alzheimer"]
    # Aucun extra à produire
    assert extras.is_empty()


def test_retype_ignores_non_type_d_depth5() -> None:
    """Code depth=5 mais ofs_type=S (catégorie classique, pas 5e position)
    : non touché."""
    owl = _make_owl([{"code": "A18.1", "synonymes": ["tuberculose"]}])
    ofs = _make_ofs(
        [
            {
                "code": "A18.1",
                "ofs_type": "S",
                "depth": 5,
                "path": "(A00-B99)/(A15-A19)/A18/A18.1",
                "label": "tuberculose génito-urinaire",
            }
        ]
    )
    owl_filtered, extras = retype_chap13_altlabels(owl, ofs)

    assert list(owl_filtered.filter(pl.col("code") == "A18.1")["synonymes"][0]) == [
        "tuberculose"
    ]
    assert extras.is_empty()


def test_retype_type_d_without_synonymes_passthrough() -> None:
    """Code type=D sans altLabel : pas de panique, owl_filtered inchangé,
    extras vide."""
    owl = _make_owl([{"code": "M00.00", "synonymes": []}])
    ofs = _make_ofs(
        [
            {
                "code": "M00.00",
                "ofs_type": "D",
                "depth": 5,
                "path": "(M00-M99)/(M00-M03)/M00/M00.0/M00.00",
                "label": "arthrite à staphylocoques | sièges multiples",
            }
        ]
    )
    owl_filtered, extras = retype_chap13_altlabels(owl, ofs)

    assert list(owl_filtered.filter(pl.col("code") == "M00.00")["synonymes"][0]) == []
    assert extras.is_empty()


def test_retype_handles_chapter_codes_with_parentheses() -> None:
    """Le code OFS peut être entre parenthèses (chapitres et blocs).
    La fonction strip les parens avant de matcher avec owl_codes."""
    owl = _make_owl([{"code": "M01.08", "synonymes": ["tronc"]}])
    ofs = _make_ofs(
        [
            # Chapitre avec parenthèses (non concerné par le retypage)
            {
                "code": "(M00-M99)",
                "ofs_type": "C",
                "depth": 0,
                "path": "(M00-M99)",
                "label": "Maladies du système ostéoarticulaire",
            },
            # Code feuille type=D
            {
                "code": "M01.08",
                "ofs_type": "D",
                "depth": 5,
                "path": "(M00-M99)/(M00-M03)/M01/M01.0/M01.08",
                "label": "arthrite méningococcique | autres",
            },
        ]
    )
    _, extras = retype_chap13_altlabels(owl, ofs)
    assert extras.height == 1
    assert extras["texte"][0] == "tronc"


# ----------------------------------------------------------------------
# find_orphan_type_d_codes
# ----------------------------------------------------------------------


def test_find_orphan_type_d_lists_missing_codes() -> None:
    """Codes type=D dans OFS sans contrepartie owl_codes → rapport."""
    owl = _make_owl([{"code": "M01.08", "synonymes": []}])
    ofs = _make_ofs(
        [
            {
                "code": "M01.08",
                "ofs_type": "D",
                "depth": 5,
                "path": "(M00-M99)/(M00-M03)/M01/M01.0/M01.08",
                "label": "arthrite méningococcique | autres",
            },
            {
                "code": "M11.90",  # orphelin attendu
                "ofs_type": "D",
                "depth": 5,
                "path": "(M00-M99)/(M00-M25)/M11/M11.9/M11.90",
                "label": "arthropathie due à des microcristaux | sièges multiples",
            },
        ]
    )
    orphans = find_orphan_type_d_codes(owl, ofs)
    assert orphans.height == 1
    row = orphans.row(0, named=True)
    assert row["code"] == "M11.90"
    assert row["chapter"] == "(M00-M99)"
    assert row["categorie_orphan"] == "unknown"
    assert "arthropathie" in row["libelle_master"]


def test_find_orphan_type_d_ignores_non_type_d() -> None:
    """Code ofs_type=S absent d'owl : ne va PAS dans orphan_type_d
    (réservé aux type=D, depth=5)."""
    owl = _make_owl([])
    ofs = _make_ofs(
        [
            {
                "code": "A18.1",
                "ofs_type": "S",
                "depth": 5,
                "path": "(A00-B99)/(A15-A19)/A18/A18.1",
                "label": "tuberculose",
            }
        ]
    )
    orphans = find_orphan_type_d_codes(owl, ofs)
    assert orphans.is_empty()
