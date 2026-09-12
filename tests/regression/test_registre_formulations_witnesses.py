"""Témoins du registre des formulations écartées (verdict RF 2026-09-09).

Ce que ces verrous affirment, sur données réelles :

1. **Préserver le vivant vaut autant qu'écarter l'archaïque.** Les
   dorés sont pris dans la liste validée : sur un même code et une même
   sonde, une formulation écartée disparaît ET une formulation gardée
   reste (« maladie tabès » / « tabès syphilitique » sur A52.1) ; sur
   F03, « démence précoce » se garde par décision explicite quand les
   « sénilité … » s'écartent.
2. **I64, le cas d'école** : le nuage « apoplexie » de l'Index vol3
   disparaît de la section, le reste de la fiche est intouché.
3. **OFS/ANS jamais filtrés** : la section « Périmètre clinique » est
   identique avec et sans registre (le refus au chargement est testé en
   unitaire).
4. **Le registre reste ancré sur le CSV** : chaque entrée correspond à
   une ligne réelle (code, source, texte) — une mise à jour de source
   qui reformulerait une écartée rendrait l'entrée muette, ce test la
   signale.
"""

from __future__ import annotations

import dataclasses
import random

import polars as pl
import pytest

from recode_icd import cards
from recode_icd.registre_formulations import (
    DEFAULT_REGISTRE_PATH,
    REGISTRE_VIDE,
)
from recode_icd.utils.loaders_dev import ExplorationContext, load_exploration_context

pytestmark = pytest.mark.regression


@pytest.fixture(scope="module")
def ctx() -> ExplorationContext:
    c = load_exploration_context(with_external=True)
    if c.flat is None or c.merged is None or c.ans is None:
        pytest.skip("Artefacts pipeline absents.")
    return c


@pytest.fixture(scope="module")
def outils(ctx: ExplorationContext) -> cards.PolitiqueFiches:
    """Politique réelle, registre chargé depuis le YAML committé."""
    if not DEFAULT_REGISTRE_PATH.exists():
        pytest.skip("registre_formulations.yaml absent.")
    return cards.charge_politique(cards._eager(ctx.merged))


@pytest.fixture(scope="module")
def outils_sans_registre(outils: cards.PolitiqueFiches) -> cards.PolitiqueFiches:
    return dataclasses.replace(outils, registre=REGISTRE_VIDE)


def _candidates(ctx: ExplorationContext, outils: cards.PolitiqueFiches, code: str) -> list[str]:
    """Formulations candidates (post-R1/R3/registre, avant plafond R2).

    On teste avant R2 : le tirage de plafonnement pourrait masquer un
    témoin par échantillonnage, pas par décision.
    """
    sub = cards._eager(ctx.flat).filter(pl.col("code") == code)
    chapitre, blocs = outils.hierarchie_de(code)
    return [c.texte for c in cards._candidates_formulations(sub, chapitre, blocs, outils)]


def test_meme_sonde_ecartee_et_gardee_tabes_a52_1(
    ctx: ExplorationContext,
    outils: cards.PolitiqueFiches,
    outils_sans_registre: cards.PolitiqueFiches,
) -> None:
    """Doré : sonde « tabès » sur A52.1 — l'écartée part, la gardée reste."""
    avant = _candidates(ctx, outils_sans_registre, "A52.1")
    assert "maladie tabès" in avant and "tabès syphilitique" in avant, (
        "Prérequis cassé : le CSV ne porte plus les deux témoins CepiDc de A52.1."
    )
    apres = _candidates(ctx, outils, "A52.1")
    assert "maladie tabès" not in apres, "écartée par verdict RF, doit disparaître"
    assert "tabès syphilitique" in apres, "gardée par verdict RF, doit rester"


def test_croup_ecarte_partout(ctx: ExplorationContext, outils: cards.PolitiqueFiches) -> None:
    """« croup » écarté sur A36.0, J05.0 ET B94.8 (correction RF 2026-09-12).

    « séquelles croup » (B94.8) était gardée au verdict initial ; RF a
    tranché : le mot est vivant (laryngite pédiatrique) mais cette
    formulation-ci est du registre diphtérique de certificat de décès.
    """
    for code in ("A36.0", "J05.0", "B94.8"):
        assert all("croup" not in t.lower() for t in _candidates(ctx, outils, code)), (
            f"{code} : une formulation croup subsiste"
        )


def test_f03_demence_precoce_gardee_par_decision_explicite(
    ctx: ExplorationContext, outils: cards.PolitiqueFiches
) -> None:
    """Doré même code, verdicts opposés : F03 (RF 2026-09-12, confirmé).

    « démence précoce » se garde — lecture moderne « démence à début
    précoce », vivante en gériatrie, prime sur l'origine kraepelinienne
    probable de la ligne. Les « sénilité … » du même code s'écartent.
    """
    apres = _candidates(ctx, outils, "F03")
    assert "démence précoce" in apres, "gardée par décision explicite RF"
    assert "sénilité mentale" not in apres and "sénilité démentielle" not in apres


def test_i64_le_nuage_apoplexie_disparait(
    ctx: ExplorationContext,
    outils: cards.PolitiqueFiches,
    outils_sans_registre: cards.PolitiqueFiches,
) -> None:
    """Cas d'école du chantier : la fiche I64 avant/après."""
    rng = random.Random(cards.DEFAULT_SEED)
    avant = cards.build_card("I64", ctx, rng, outils_sans_registre)
    apres = cards.build_card("I64", ctx, rng, outils)

    assert "apoplexie congestive" in avant, "Prérequis cassé : le nuage a déjà disparu ?"
    assert "apoplexie" not in apres.lower(), "tout le nuage apoplexie doit être écarté"
    assert "coma apoplectique" not in apres
    assert "accident vasculaire cérébral SAI" in apres, (
        "la formulation AP-HP gardée doit rester dans la section"
    )


def test_ofs_ans_intouches_sur_i64(
    ctx: ExplorationContext,
    outils: cards.PolitiqueFiches,
    outils_sans_registre: cards.PolitiqueFiches,
) -> None:
    """Le registre ne touche que la section Formulations."""
    rng = random.Random(cards.DEFAULT_SEED)
    avant = cards.build_card("I64", ctx, rng, outils_sans_registre)
    apres = cards.build_card("I64", ctx, rng, outils)

    def _hors_formulations(markdown: str) -> str:
        tete, _, reste = markdown.partition("## Formulations cliniques alternatives")
        return tete + reste.partition("\n## ")[2]

    assert _hors_formulations(avant) == _hors_formulations(apres), (
        "Hors Formulations, la fiche doit être byte-identique avec et sans registre."
    )


def test_les_entrees_du_registre_existent_dans_le_csv(
    ctx: ExplorationContext, outils: cards.PolitiqueFiches, csv_final_df: pl.DataFrame
) -> None:
    """Chaque écartée vise une ligne réelle du CSV — pas d'entrée muette."""
    lignes = {
        (str(r["code"]), str(r["source"]), str(r["texte"]))
        for r in csv_final_df.select("code", "source", "texte").drop_nulls().iter_rows(named=True)
    }
    muettes = sorted(e for e in outils.registre.ecartees if e not in lignes)
    assert not muettes, (
        f"{len(muettes)} entrée(s) du registre ne correspondent plus à aucune ligne du CSV "
        f"(source mise à jour ?) : {muettes[:5]}"
    )
