"""Verrou sur le filtrage par libellé de source de la section
« Formulations cliniques alternatives » des fiches.

Pourquoi ce fichier existe
--------------------------
Le filtrage se fait par famille, déclarée dans
`referentials/curation/chapter_policy.yaml` — **vérité unique** depuis
le 2026-08-13. `cards.py` ne porte plus de constantes de libellés : en
maintenir deux énumérations et les tester l'une contre l'autre ne
faisait que déplacer le risque de dérive. Le jour où le YAML a admis
ORPHANET dans les Formulations alors que la constante l'excluait,
1 467 fiches ont changé sans que personne l'ait décidé.

La couverture bidirectionnelle YAML ↔ `_SOURCE_CSV_MAP` est verrouillée
par `tests/unit/test_policy.py`. Ce fichier-ci porte les deux verrous
qui exigent des données réelles :

1. `test_*_produit_des_lignes_dans_le_csv` — un libellé peut être
   correctement rangé et pourtant ne rien produire (faute de frappe
   partagée, source vidée en amont) ;
2. `test_r51_*` et `test_le_csv_nest_pas_modifie` — vérification de bout
   en bout sur une fiche témoin, et garantie que la normalisation reste
   une transformation de rendu.
"""

from __future__ import annotations

import random

import polars as pl
import pytest

from recode_icd import cards, normalize_index
from recode_icd.policy import load_policy

pytestmark = pytest.mark.regression


# Fiche témoin : R51 (céphalée) est alimentée à la fois par l'Index
# CIM-10 vol3 et par CepiDc, et a été validée manuellement lors du
# merge CepiDc (cf docs/sessions/2026-08-09_merge_cepidc.md).
_WITNESS_CODE = "R51"


@pytest.mark.parametrize("famille", ["INDEX", "CEPIDC", "APHP"])
def test_famille_admise_produit_des_lignes_dans_le_csv(
    csv_final_df: pl.DataFrame, famille: str
) -> None:
    """Une famille admise par le YAML doit aussi exister en données."""
    policy = load_policy()
    assert famille in policy.familles_formulations, (
        f"{famille} n'alimente plus les Formulations — mettre à jour ce test "
        f"si c'est une décision, ou le YAML si c'est un accident."
    )
    libelles = [
        lib
        for lib in csv_final_df["source"].unique().to_list()
        if policy.famille_de(lib) == famille
    ]
    n = csv_final_df.filter(pl.col("source").is_in(libelles)).height
    assert n > 0, (
        f"La famille « {famille} », admise par le YAML, ne produit aucune ligne dans le CSV final."
    )


def test_orphanet_reste_hors_des_formulations() -> None:
    """ORPHANET est exclu des Formulations, et c'est une décision de fond.

    Les synonymes de maladies rares biaiseraient le corpus généré vers
    des événements à basse fréquence. Un profil de fiche « contrôle
    qualité » qui les admettrait est au backlog — mais il devra être un
    profil distinct, pas un élargissement silencieux de celui-ci.
    """
    policy = load_policy()
    assert "ORPHANET" not in policy.familles_formulations, (
        "ORPHANET a été admis dans les Formulations. Si c'est voulu, "
        "documenter la décision et mettre à jour ce test ; sinon, le "
        "retirer de `familles_formulations`. Cf. "
        "docs/backlog/profils_fiches_par_usage.md."
    )


def test_r51_formulations_couvre_les_sources_plafonnees(
    csv_final_df: pl.DataFrame,
) -> None:
    """Bout en bout : la fiche R51 contient bien de l'Index ET du CepiDc.

    On ne compare pas à une liste figée de textes (trop fragile : le
    contenu bouge à chaque mise à jour de source). On vérifie que le
    markdown rendu contient au moins une entrée dont on sait, par le
    CSV, qu'elle provient de chaque source plafonnée.

    **Depuis R3, les entrées d'Index sont normalisées au rendu** : la
    forme affichée n'est plus la forme source (« Céphalée (de) » devient
    « céphalée »). On compare donc aux formes *attendues après
    normalisation* — et le fait que la comparaison brute ne suffise plus
    est en soi la preuve que R3 s'applique. Le CSV, lui, conserve la
    forme source : c'est ce que vérifie `test_le_csv_nest_pas_modifie`.
    """
    ctx = cards.load_exploration_context()
    outils = cards.charge_politique(cards._eager(ctx.merged))
    markdown = cards.build_card(_WITNESS_CODE, ctx, random.Random(cards.DEFAULT_SEED), outils)
    section = _extract_formulations(markdown)
    assert section, f"{_WITNESS_CODE} : section Formulations absente de la fiche"

    rendus = {ligne.removeprefix("- ").strip() for ligne in section}

    for label in ("CIM-10 index", "CepiDc 2015"):
        sources = (
            csv_final_df.filter((pl.col("code") == _WITNESS_CODE) & (pl.col("source") == label))[
                "texte"
            ]
            .drop_nulls()
            .to_list()
        )
        assert sources, (
            f"Prérequis du témoin cassé : {_WITNESS_CODE} n'a plus "
            f"d'entrée « {label} » dans le CSV. Changer de code témoin."
        )
        if outils.policy.famille_de(label) == "INDEX":
            attendus = {
                forme
                for texte in sources
                if (
                    forme := normalize_index.forme_normalisee(
                        texte, outils.lexiques, outils.config_normalisation
                    )
                )
            }
            assert attendus, (
                f"R3 écarte TOUTES les entrées « {label} » de {_WITNESS_CODE} : "
                f"le témoin ne prouve plus rien. Changer de code témoin."
            )
        else:
            attendus = set(sources)
        # La dédup tolérante peut absorber une entrée au profit d'une
        # variante d'une autre source ; on exige seulement qu'il en
        # reste au moins une, pas toutes.
        assert rendus & attendus, (
            f"Aucune entrée « {label} » dans la section Formulations de "
            f"{_WITNESS_CODE}. Le filtre de cards.py ne matche plus cette "
            f"source — libellé renommé d'un seul côté ?"
        )


def test_le_csv_nest_pas_modifie(csv_final_df: pl.DataFrame) -> None:
    """**Garantie centrale du chantier** : R3 réécrit le RENDU, pas les données.

    Après un assemblage de fiche, la forme source de l'Index doit
    toujours être dans le CSV, inchangée. Si ce test casse, la
    normalisation a fuité en amont — et le libellé officiel du volume 3
    devient irrécupérable, ce qui viole le principe « jamais
    d'agrégation silencieuse ».
    """
    source_index = "Céphalée (de)"
    avant = csv_final_df.filter(
        (pl.col("code") == _WITNESS_CODE) & (pl.col("texte") == source_index)
    ).height
    assert avant == 1, "prérequis : la forme source est bien dans le CSV"

    ctx = cards.load_exploration_context()
    outils = cards.charge_politique(cards._eager(ctx.merged))
    markdown = cards.build_card(_WITNESS_CODE, ctx, random.Random(cards.DEFAULT_SEED), outils)
    assert source_index not in markdown, "la fiche doit rendre la forme normalisée"

    apres = (
        cards._eager(ctx.flat)
        .filter((pl.col("code") == _WITNESS_CODE) & (pl.col("texte") == source_index))
        .height
    )
    assert apres == 1, (
        "La forme source a disparu du CSV après un build de fiche : la "
        "normalisation a fuité dans les données au lieu de rester au rendu."
    )


def _extract_formulations(markdown: str) -> list[str]:
    """Lignes `- …` de la section Formulations, ou liste vide."""
    lignes: list[str] = []
    dans_section = False
    for ligne in markdown.splitlines():
        if ligne.startswith("## "):
            dans_section = ligne.startswith("## Formulations")
            continue
        if dans_section and ligne.startswith("- "):
            lignes.append(ligne)
    return lignes
