"""Tests pytest minimaux pour `recode_icd.cards`.

- Smoke : `build_card` s'exécute sans erreur sur 1-2 codes
- Régression : sortie A18.1 contient des éléments attendus (titre,
  sections, contenu spécifique)

La garantie de non-régression principale reste la comparaison
byte-à-byte sur les 7 fiches témoins (cf workflow chantier).
"""

from __future__ import annotations

import random

import pytest

from recode_icd.cards import (
    DEFAULT_SEED,
    BuildSummary,
    build_card,
    build_cards_library,
)
from recode_icd.utils.loaders_dev import ExplorationContext, load_exploration_context

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def ctx() -> ExplorationContext:
    """Contexte avec sources externes (requis pour Formulations)."""
    c = load_exploration_context(with_external=True)
    if c.flat is None or c.merged is None or c.ans is None or c.ofs_codes is None:
        pytest.skip("Artefacts pipeline absents.")
    return c


# ----------------------------------------------------------------------
# Smoke tests
# ----------------------------------------------------------------------


def test_build_card_smoke_a18_1(ctx: ExplorationContext) -> None:
    """build_card produit un markdown non vide pour A18.1."""
    rng = random.Random(DEFAULT_SEED)
    card = build_card("A18.1", ctx, rng)
    assert card.startswith('<fiche_code code="A18.1">')
    assert card.endswith("</fiche_code>\n")
    assert len(card) > 500


def test_build_card_smoke_u07_1_post_2006(ctx: ExplorationContext) -> None:
    """U07.1 est un code post-2006 absent du CSV → utilise le fallback ANS.
    Doit produire une fiche valide sans erreur."""
    rng = random.Random(DEFAULT_SEED)
    card = build_card("U07.1", ctx, rng)
    assert "U07.1" in card
    assert "COVID" in card or "vapotage" in card or "Syndrome respiratoire" in card


def test_build_card_deterministic_same_seed(ctx: ExplorationContext) -> None:
    """Deux appels avec le même seed produisent des sorties identiques."""
    card1 = build_card("A18.1", ctx, random.Random(DEFAULT_SEED))
    card2 = build_card("A18.1", ctx, random.Random(DEFAULT_SEED))
    assert card1 == card2


# ----------------------------------------------------------------------
# Régression légère — A18.1
# ----------------------------------------------------------------------


def test_build_card_a18_1_has_expected_sections(ctx: ExplorationContext) -> None:
    """A18.1 doit avoir : titre + Position + Périmètre + À ne pas décrire
    + Formulations. Pas de Localisations anatomiques (pas type=D)."""
    rng = random.Random(DEFAULT_SEED)
    card = build_card("A18.1", ctx, rng)
    assert "# A18.1 — Tuberculose de l'appareil génito-urinaire" in card
    assert "## Position dans la classification" in card
    assert "## Périmètre clinique du code" in card
    assert "## À ne pas décrire" in card
    assert "## Formulations cliniques alternatives" in card
    assert "## Localisations anatomiques" not in card


def test_build_card_a18_1_has_heritage_inclusions(ctx: ExplorationContext) -> None:
    """A18.1 doit montrer les inclusions héritées du chapitre I et du
    bloc A15-A19 (chantier 2026-06-06 sur Périmètre étendu)."""
    rng = random.Random(DEFAULT_SEED)
    card = build_card("A18.1", ctx, rng)
    assert "Inclusions héritées du chapitre I :" in card
    assert "Inclusions héritées du bloc A15-A19 :" in card
    assert "Au niveau du code :" in card


def test_build_card_a18_1_exclusions_in_general_to_specific_order(
    ctx: ExplorationContext,
) -> None:
    """À ne pas décrire : ordre chapter > block > … (chantier 2026-06-06)."""
    rng = random.Random(DEFAULT_SEED)
    card = build_card("A18.1", ctx, rng)
    pos_chap = card.find("(hérité du chapitre I)")
    pos_bloc = card.find("(hérité du bloc A15-A19)")
    assert pos_chap > 0
    assert pos_bloc > pos_chap, "chapitre doit venir avant bloc"


def test_build_card_m01_08_has_localisations_section(ctx: ExplorationContext) -> None:
    """M01.08 (type=D chap XIII) doit avoir la section Localisations
    anatomiques (chantier 2026-06-06)."""
    rng = random.Random(DEFAULT_SEED)
    card = build_card("M01.08", ctx, rng)
    assert "## Localisations anatomiques" in card
    # Composantes attendues de la 5e position "autres"
    for loc in ("tronc", "cou", "crâne", "côtes", "tête", "colonne vertébrale"):
        assert loc in card.lower()


# ----------------------------------------------------------------------
# build_cards_library — smoke avec limit
# ----------------------------------------------------------------------


def test_build_cards_library_with_limit(ctx: ExplorationContext, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """build_cards_library produit N fiches + _index.csv quand limit=N."""
    summary = build_cards_library(
        ctx=ctx,
        output_dir=tmp_path / "lib",
        limit=5,
        progress=False,
    )
    assert isinstance(summary, BuildSummary)
    assert summary.n_codes_total == 5
    assert summary.n_written == 5
    assert summary.n_errors == 0
    assert summary.index_path.is_file()
    # 5 fiches .md doivent exister sous des sous-dossiers chapter/.
    md_files = list((tmp_path / "lib").rglob("*.md"))
    assert len(md_files) == 5


def test_build_cards_library_chapter_filter(ctx: ExplorationContext, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """build_cards_library filtre par chapitre romain."""
    summary = build_cards_library(
        ctx=ctx,
        output_dir=tmp_path / "lib",
        chapter_filter="XXII",
        progress=False,
    )
    # Chapitre XXII : 33 codes attendus (codes U post-2006).
    assert 20 <= summary.n_written <= 50
    # Toutes les fiches doivent être sous tmp_path/lib/XXII/.
    chap_dir = tmp_path / "lib" / "XXII"
    assert chap_dir.is_dir()
    md_in_xxii = list(chap_dir.glob("*.md"))
    assert len(md_in_xxii) == summary.n_written


def test_build_cards_library_index_csv_schema(ctx: ExplorationContext, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Le _index.csv contient les colonnes attendues."""
    import polars as pl

    summary = build_cards_library(
        ctx=ctx,
        output_dir=tmp_path / "lib",
        limit=3,
        progress=False,
    )
    index = pl.read_csv(summary.index_path)
    expected = {
        "code",
        "chapter",
        "filepath",
        "libelle",
        "has_perimetre",
        "has_localisations",
        "has_exclusions",
        "has_formulations",
        "nb_chars",
    }
    assert set(index.columns) == expected
    assert index.height == 3


# ----------------------------------------------------------------------
# _detect_sections
# ----------------------------------------------------------------------


def test_detect_sections_via_build_card(ctx: ExplorationContext) -> None:
    """Le rendu A18.1 doit déclencher les regex de détection de sections."""
    from recode_icd.cards import _detect_sections

    rng = random.Random(DEFAULT_SEED)
    card = build_card("A18.1", ctx, rng)
    sections = _detect_sections(card)
    assert sections["has_perimetre"] is True
    assert sections["has_exclusions"] is True
    assert sections["has_formulations"] is True
    assert sections["has_localisations"] is False  # A18.1 pas type=D
