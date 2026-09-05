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
        "has_consignes",
        "has_formulations",
        "type_mco",
        "statut_mco",
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
    # A18.1 n'est visé que par ANT-01 (chapitre I), non rendue depuis
    # l'arbitrage n° 10 (rendu_fiche=non) : pas de section Consignes.
    assert sections["has_consignes"] is False


def test_detect_sections_consignes_millesime_variable() -> None:
    """Le titre de la section Consignes porte le millésime lu dans la
    table — la détection doit accepter n'importe quel millésime."""
    from recode_icd.cards import _detect_sections

    for millesime in ("2026-provisoire", "2027"):
        card = f"## Consignes de codage (guide méthodologique {millesime})\n\n- [X] y"
        assert _detect_sections(card)["has_consignes"] is True
    assert _detect_sections("## Consignes de codage\n")["has_consignes"] is False


def test_rang_romain_ordre_de_la_classification() -> None:
    """Le rapport par chapitre se trie par valeur romaine, pas par le
    nested set ANS (qui ordonne alphabétiquement : IX entre IV et V)."""
    from recode_icd.cards import _rang_romain

    chapitres = [
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI",
        "VII",
        "VIII",
        "IX",
        "X",
        "XI",
        "XII",
        "XIII",
        "XIV",
        "XV",
        "XVI",
        "XVII",
        "XVIII",
        "XIX",
        "XX",
        "XXI",
        "XXII",
    ]
    assert sorted(chapitres, key=_rang_romain) == chapitres
    assert _rang_romain("hors-classification") > _rang_romain("XXII")


# ----------------------------------------------------------------------
# Statut MCO (kit ATIH) — chantier couverture ATIH, D1
# ----------------------------------------------------------------------


def test_la_fiche_porte_son_statut_mco_sous_le_titre(ctx: ExplorationContext) -> None:
    """Filtre de génération : la ligne suit immédiatement le titre.

    Témoins : un code codable sans restriction, un père interdit (`W00`,
    catégorie du chapitre XX), un code supprimé (`M07.20`, SU09) et un
    code inconnu du kit (`M16.00`, localisation du chapitre XIII).
    """
    if ctx.atih is None:
        pytest.skip("atih_codes.parquet absent (`recode-icd build atih`).")
    attendus = {
        "A18.1": "Statut MCO (kit ATIH 2025) : codable en MCO, pas de restriction.",
        "W00": "Statut MCO (kit ATIH 2025) : non codable en MCO (catégorie non vide ou code père interdit).",
        "M07.20": "Statut MCO (kit ATIH 2025) : supprimé du kit ATIH (SU09).",
        "M16.00": "Statut MCO (kit ATIH 2025) : inconnu du kit ATIH.",
    }
    for code, ligne in attendus.items():
        card = build_card(code, ctx, random.Random(DEFAULT_SEED))
        lignes = card.splitlines()
        titre = next(i for i, ligne_ in enumerate(lignes) if ligne_.startswith("# "))
        assert lignes[titre + 2] == ligne, (code, lignes[titre : titre + 3])


def test_lindex_porte_type_et_statut_mco(ctx: ExplorationContext, tmp_path) -> None:  # type: ignore[no-untyped-def]
    if ctx.atih is None:
        pytest.skip("atih_codes.parquet absent (`recode-icd build atih`).")
    import polars as pl

    summary = build_cards_library(ctx=ctx, output_dir=tmp_path / "lib", limit=3, progress=False)
    index = pl.read_csv(summary.index_path)
    assert {"type_mco", "statut_mco"} <= set(index.columns)
    assert index["statut_mco"].null_count() == 0
    assert set(index["statut_mco"].to_list()) <= {
        "codable",
        "interdit_dp_dr",
        "cause_externe",
        "interdit_dp",
        "pere_interdit",
        "supprime",
        "inconnu_atih",
    }


# ----------------------------------------------------------------------
# Profils de bibliothèque (chantier couverture ATIH, D4)
# ----------------------------------------------------------------------


def test_le_profil_generation_exclut_les_non_codables(ctx: ExplorationContext, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Chapitre XXII (codes U) : `controle` construit tout, `generation`
    écarte ce qui n'est pas codable — et l'index de chaque bibliothèque
    en témoigne, autoportant."""
    if ctx.atih is None:
        pytest.skip("atih_codes.parquet absent (`recode-icd build atih`).")
    import polars as pl

    controle = build_cards_library(
        ctx=ctx,
        output_dir=tmp_path / "controle",
        chapter_filter="XXII",
        progress=False,
        profil="controle",
    )
    generation = build_cards_library(
        ctx=ctx, output_dir=tmp_path / "generation", chapter_filter="XXII", progress=False
    )
    idx_controle = pl.read_csv(controle.index_path)
    idx_generation = pl.read_csv(generation.index_path)
    non_codables = {"pere_interdit", "supprime", "inconnu_atih"}
    assert generation.profil == "generation" and controle.n_exclus_non_codables == 0
    assert idx_generation.filter(pl.col("statut_mco").is_in(non_codables)).is_empty()
    assert idx_controle.height >= idx_generation.height
    assert generation.n_exclus_non_codables > 0, "le CSV porte des non-codables avant D4"


def test_profil_generation_sans_kit_joint_echoue_bruyamment() -> None:
    """Sans statut MCO dans merged, filtrer « les codables » serait un mensonge."""
    import polars as pl

    from recode_icd.cards import codes_codables

    with pytest.raises(ValueError, match="statut MCO"):
        codes_codables(pl.DataFrame({"code": ["A00"]}))
    with pytest.raises(ValueError, match="statut MCO"):
        codes_codables(
            pl.DataFrame(
                {"code": ["A00"], "codable_mco": [None]},
                schema_overrides={"codable_mco": pl.Boolean},
            )
        )
