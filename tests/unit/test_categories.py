"""Tests pytest minimaux pour `build_category_card` et
`build_categories_library`.

Smoke + régressions sur A18 (cas complet), M01 (chap XIII), R51
(catégorie = feuille). Garantie de non-régression principale = vérif
empirique sur les fiches générées (cf récap chantier).
"""

from __future__ import annotations

import random

import polars as pl
import pytest

from recode_icd.cards import (
    CATEGORY_FORMULATIONS_MAX,
    DEFAULT_SEED,
    BuildSummary,
    _category_direct_children,
    _category_leaf_codes,
    build_categories_library,
    build_category_card,
)
from recode_icd.utils.loaders_dev import ExplorationContext, load_exploration_context

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def ctx() -> ExplorationContext:
    c = load_exploration_context(with_external=True)
    if c.flat is None or c.merged is None or c.ans is None:
        pytest.skip("Artefacts pipeline absents.")
    return c


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def test_category_direct_children_a18(ctx: ExplorationContext) -> None:
    """A18 a 9 enfants directs (A18.0..A18.8)."""
    assert ctx.merged is not None
    enfants = _category_direct_children(
        "A18", ctx.merged.collect() if hasattr(ctx.merged, "collect") else ctx.merged
    )
    codes = [c for c, _ in enfants]
    assert codes == [f"A18.{i}" for i in range(9)]


def test_category_direct_children_m01_excludes_5car(
    ctx: ExplorationContext,
) -> None:
    """M01 a des enfants 4-car (M01.0..M01.8) et 5-car (M01.00..),
    seuls les 4-car sont enfants directs."""
    assert ctx.merged is not None
    enfants = _category_direct_children(
        "M01", ctx.merged.collect() if hasattr(ctx.merged, "collect") else ctx.merged
    )
    codes = [c for c, _ in enfants]
    # Tous longueur 5 (M01.X)
    assert all(len(c) == 5 for c in codes)
    assert "M01.00" not in codes


def test_category_direct_children_r51_empty(ctx: ExplorationContext) -> None:
    """R51 est catégorie = feuille → aucun enfant direct."""
    assert ctx.merged is not None
    enfants = _category_direct_children(
        "R51", ctx.merged.collect() if hasattr(ctx.merged, "collect") else ctx.merged
    )
    assert enfants == []


def test_category_leaf_codes_includes_category_if_in_csv(
    ctx: ExplorationContext,
) -> None:
    """Pour R51 (catégorie = feuille), R51 lui-même est dans la liste
    des feuilles."""
    assert ctx.flat is not None
    leaves = _category_leaf_codes(
        "R51", ctx.flat.collect() if hasattr(ctx.flat, "collect") else ctx.flat
    )
    assert "R51" in leaves


# ----------------------------------------------------------------------
# build_category_card — smoke + régression
# ----------------------------------------------------------------------


def test_build_category_card_smoke_a18(ctx: ExplorationContext) -> None:
    """A18 produit un markdown bien formé avec sections attendues."""
    rng = random.Random(DEFAULT_SEED)
    card = build_category_card("A18", ctx, rng)
    assert card.startswith('<fiche_category code="A18">')
    assert card.endswith("</fiche_category>\n")
    assert "# A18 — Tuberculose" in card
    assert "## Codes enfants directs" in card
    assert "## Périmètre clinique" in card
    assert "## À ne pas décrire" in card
    assert "## Formulations cliniques alternatives" in card


def test_build_category_card_a18_heritage_inclusions(
    ctx: ExplorationContext,
) -> None:
    """A18 doit montrer héritages chapitre I + bloc A15-A19."""
    rng = random.Random(DEFAULT_SEED)
    card = build_category_card("A18", ctx, rng)
    assert "Inclusions héritées du chapitre I :" in card
    assert "Inclusions héritées du bloc A15-A19 :" in card


def test_build_category_card_m01_no_localisations(
    ctx: ExplorationContext,
) -> None:
    """M01 (chap XIII) : pas de section Localisations anatomiques au
    niveau catégorie + pas d'inclusions ANS niveau code des 5-car
    (filtre type=D)."""
    rng = random.Random(DEFAULT_SEED)
    card = build_category_card("M01", ctx, rng)
    assert "## Localisations anatomiques" not in card
    # Les composantes 5e position "autres" (tronc/cou/crâne) ne doivent
    # pas apparaître dans le périmètre clinique de la catégorie M01.
    perimetre_start = card.find("## Périmètre clinique")
    perimetre_end = card.find("## À ne pas décrire")
    if perimetre_start >= 0 and perimetre_end > perimetre_start:
        perimetre = card[perimetre_start:perimetre_end].lower()
        # Vérification stricte : aucun des 6 composants atomiques de
        # la 5e position 8 n'apparaît dans le périmètre clinique.
        for forbidden in ("- tronc", "- cou", "- crâne", "- côtes"):
            assert forbidden not in perimetre, (
                f"M01 périmètre : composant 5e position '{forbidden}' "
                f"ne doit pas apparaître (filtre type=D)"
            )


def test_build_category_card_r51_omits_children_section(
    ctx: ExplorationContext,
) -> None:
    """R51 (catégorie = feuille) : section Codes enfants directs omise."""
    rng = random.Random(DEFAULT_SEED)
    card = build_category_card("R51", ctx, rng)
    assert "## Codes enfants directs" not in card


def test_build_category_card_deterministic(ctx: ExplorationContext) -> None:
    """Même seed → même fiche (incluant l'échantillonnage formulations)."""
    card1 = build_category_card("A18", ctx, random.Random(DEFAULT_SEED))
    card2 = build_category_card("A18", ctx, random.Random(DEFAULT_SEED))
    assert card1 == card2


def test_build_category_card_formulations_plafonnees(
    ctx: ExplorationContext,
) -> None:
    """A18 a >50 formulations agrégées : section plafonnée à
    CATEGORY_FORMULATIONS_MAX."""
    rng = random.Random(DEFAULT_SEED)
    card = build_category_card("A18", ctx, rng)
    formul_start = card.find("## Formulations cliniques alternatives")
    if formul_start < 0:
        pytest.skip("A18 n'a pas de formulations (inattendu).")
    # Section : entre l'amorce et la fin de fichier (ou prochaine section)
    formul = card[formul_start:]
    n_puces = formul.count("\n- ")
    assert n_puces <= CATEGORY_FORMULATIONS_MAX, (
        f"A18 formulations : {n_puces} entrées, doit être <= {CATEGORY_FORMULATIONS_MAX}"
    )


# ----------------------------------------------------------------------
# build_categories_library — smoke
# ----------------------------------------------------------------------


def test_build_categories_library_with_limit(ctx: ExplorationContext, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Limit=5 produit 5 fiches + _index.csv."""
    summary = build_categories_library(
        ctx=ctx,
        output_dir=tmp_path / "cat",
        limit=5,
        progress=False,
    )
    assert isinstance(summary, BuildSummary)
    assert summary.n_codes_total == 5
    assert summary.n_written == 5
    assert summary.n_errors == 0
    md_files = list((tmp_path / "cat").rglob("*.md"))
    assert len(md_files) == 5

    index = pl.read_csv(summary.index_path)
    expected = {
        "code",
        "chapter",
        "filepath",
        "libelle",
        "n_enfants",
        "has_perimetre",
        "has_exclusions",
        "has_formulations",
        "type_mco",
        "statut_mco",
        "nb_chars",
    }
    assert set(index.columns) == expected
    assert index.height == 5


def test_build_categories_library_chapter_filter(ctx: ExplorationContext, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Filtre par chapitre XXII (~12 catégories de codes U)."""
    summary = build_categories_library(
        ctx=ctx,
        output_dir=tmp_path / "cat",
        chapter_filter="XXII",
        progress=False,
    )
    assert 5 <= summary.n_written <= 20
    chap_dir = tmp_path / "cat" / "XXII"
    assert chap_dir.is_dir()
    assert len(list(chap_dir.glob("*.md"))) == summary.n_written
