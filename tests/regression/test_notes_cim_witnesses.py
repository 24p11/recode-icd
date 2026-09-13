"""Témoins des notes de la CIM-10 dans les fiches (verdict RF 2026-09-14).

La liste de témoins vient du message de feu vert de phase 2 :

1. une DÉFINITION sur la fiche du code (E43) ;
2. une DESCRIPTION CLINIQUE du glossaire F (F20.0) ;
3. la note de bloc I20-I25 HÉRITÉE sur une feuille I21.x (héritage
   borné, verdict par ligne) ;
4. une note de CHAPITRE présente sur la fiche de chapitre et ABSENTE
   des feuilles — contre-témoin de descente (jurisprudence : une note
   de chapitre ne descend JAMAIS) ;
5. le BOILERPLATE écarté (« Utiliser, au besoin, un code
   supplémentaire… ») absent des fiches mais présent dans la base —
   la base sait tout, la fiche n'affiche que le verdict ;
6. déterminisme par double build ;
7. une fiche sans note ne porte aucune des trois sections.
"""

from __future__ import annotations

import random

import polars as pl
import pytest

from recode_icd import cards
from recode_icd.utils.loaders_dev import ExplorationContext, load_exploration_context

pytestmark = pytest.mark.regression


@pytest.fixture(scope="module")
def ctx() -> ExplorationContext:
    c = load_exploration_context(with_external=True)
    if c.flat is None or c.merged is None or c.ans is None:
        pytest.skip("Artefacts pipeline absents.")
    if c.notes_cim is None:
        pytest.skip("notes_cim.parquet absent — lancer `recode-icd build notes-cim`.")
    return c


def _carte(ctx: ExplorationContext, code: str) -> str:
    return cards.build_card(code, ctx, random.Random(cards.DEFAULT_SEED))


def test_definition_sur_la_fiche_du_code_e43(ctx: ExplorationContext) -> None:
    carte = _carte(ctx, "E43")
    assert "## Définition (CIM-10)" in carte
    assert "Perte de poids importante" in carte


def test_description_clinique_du_glossaire_f(ctx: ExplorationContext) -> None:
    carte = _carte(ctx, "F20.0")
    assert "## Description clinique (OMS)" in carte
    assert "schizophrénie paranoïde" in carte.lower()


def test_note_de_bloc_i20_i25_heritee_sur_une_feuille(ctx: ExplorationContext) -> None:
    """Héritage borné bloc → feuilles, tranché ligne à ligne par RF."""
    carte = _carte(ctx, "I21.08")
    assert "## Notes de la CIM-10" in carte
    assert "laps de temps" in carte
    assert "*(note du bloc I20-I25)*" in carte


def test_note_de_chapitre_sans_descente(ctx: ExplorationContext) -> None:
    """La note du chapitre X vit sur la fiche de chapitre, jamais sur les feuilles."""
    fiche_chapitre = cards.build_node_note_card("X", ctx)
    assert fiche_chapitre is not None
    assert "localisation la plus basse" in fiche_chapitre

    # Contre-témoin : une feuille du chapitre X ne porte pas la note.
    carte_feuille = _carte(ctx, "J45.0")
    assert "localisation la plus basse" not in carte_feuille

    # Et aucune ligne note du CSV n'est héritée d'un chapitre.
    flat = cards._eager(ctx.flat)
    notes_chapitre = flat.filter((pl.col("type") == "note") & (pl.col("source_level") == "chapter"))
    assert notes_chapitre.is_empty(), "une note de chapitre ne descend JAMAIS (jurisprudence)"


def test_boilerplate_ecarte_present_dans_la_base_absent_des_fiches(
    ctx: ExplorationContext,
) -> None:
    """Jurisprudence boilerplate : écarté du rendu, conservé dans la base."""
    flat = cards._eager(ctx.flat)
    boilerplate = flat.filter(
        (pl.col("type") == "note")
        & (pl.col("note_destination") == "non_rendue")
        & pl.col("texte").str.starts_with("Utiliser, au besoin")
    )
    assert not boilerplate.is_empty(), (
        "le boilerplate écarté doit rester dans la base (type note, destination non_rendue)"
    )
    temoin = boilerplate.row(0, named=True)
    carte = _carte(ctx, str(temoin["code"]))
    assert str(temoin["texte"]) not in carte, "une note non_rendue ne s'affiche pas"


def test_determinisme_double_build(ctx: ExplorationContext) -> None:
    a = cards.build_card("E43", ctx, random.Random(cards.DEFAULT_SEED))
    b = cards.build_card("E43", ctx, random.Random(cards.DEFAULT_SEED))
    assert a == b


def test_fiche_sans_note_sans_sections_notes(ctx: ExplorationContext) -> None:
    """Un code hors du périmètre des notes ne gagne aucune section."""
    flat = cards._eager(ctx.flat)
    assert flat.filter((pl.col("code") == "A92.5") & (pl.col("type") == "note")).is_empty(), (
        "Prérequis cassé : A92.5 a gagné des notes — changer de témoin."
    )
    carte = _carte(ctx, "A92.5")
    for titre in (
        "## Définition (CIM-10)",
        "## Description clinique (OMS)",
        "## Notes de la CIM-10",
    ):
        assert titre not in carte


def test_parquet_complet_et_ancre(ctx: ExplorationContext) -> None:
    """La base sait tout : 1 003 notes, les non-rendues comprises."""
    notes = cards._eager(ctx.notes_cim)
    assert notes.height == 1003
    assert notes.filter(pl.col("destination") == "non_rendue").height > 300
    rapport = pl.read_csv("reports/notes_cim_ancrage.csv")
    assert rapport.is_empty(), "toute note curée doit rester ancrée sur sa source"
