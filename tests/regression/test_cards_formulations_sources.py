"""Verrou sur le filtrage par libellé de source de la section
« Formulations cliniques alternatives » des fiches.

Pourquoi ce fichier existe
--------------------------
`cards.py` sélectionne les sources de la section Formulations par
**égalité stricte** sur le libellé CSV (`CIM-10 index`, `CepiDc 2015`)
et par **préfixe** (`AP-HP`). Ce couplage est fragile dans un sens
précis : si un libellé est renommé dans `_SOURCE_CSV_MAP`
(`exporters/flat_csv.py`) sans être répercuté dans `cards.py`, le filtre
ne lève aucune exception — il ne matche simplement plus rien, et la
source disparaît des fiches **en silence**. Le renommage
`CepiDc_2015` → `CepiDc 2015` du 2026-08-09 a failli produire
exactement cela.

Trois niveaux de verrou, du plus structurel au plus concret :

1. `test_toute_source_du_mapping_est_tranchee` — aucune source du
   mapping ne peut rester dans un état indéterminé. Ajouter une source
   sans décider si elle alimente les Formulations fait échouer ce test.
2. `test_*_produit_des_lignes_dans_le_csv` — un libellé peut être
   cohérent entre les deux modules et pourtant ne rien produire (faute
   de frappe partagée, source vidée en amont).
3. `test_r51_*` — vérification de bout en bout sur une fiche témoin :
   les entrées attendues arrivent bien jusqu'au markdown rendu.
"""

from __future__ import annotations

import random

import polars as pl
import pytest

from recode_icd import cards, normalize_index
from recode_icd.exporters.flat_csv import _SOURCE_CSV_MAP

pytestmark = pytest.mark.regression


# Fiche témoin : R51 (céphalée) est alimentée à la fois par l'Index
# CIM-10 vol3 et par CepiDc, et a été validée manuellement lors du
# merge CepiDc (cf docs/sessions/2026-08-09_merge_cepidc.md).
_WITNESS_CODE = "R51"


def _labels_matching_prefixes() -> set[str]:
    """Libellés du mapping capturés par un préfixe de `cards.py`."""
    return {
        label
        for label in _SOURCE_CSV_MAP.values()
        if label.startswith(cards.FORMULATION_SOURCE_PREFIXES)
    }


def test_toute_source_du_mapping_est_tranchee() -> None:
    """Chaque libellé du mapping est soit inclus, soit exclu explicitement.

    C'est le verrou principal : il rend impossible l'ajout d'une source
    au CSV sans statuer sur sa présence dans la section Formulations.
    Un libellé renommé d'un seul côté apparaît ici comme « non tranché ».
    """
    connus = (
        set(cards.FORMULATION_SOURCES_EXACT)
        | _labels_matching_prefixes()
        | set(cards.FORMULATION_SOURCES_EXCLUDED)
    )
    mapping = set(_SOURCE_CSV_MAP.values())

    non_tranches = mapping - connus
    assert not non_tranches, (
        f"Sources du mapping ni incluses ni exclues de la section "
        f"Formulations : {sorted(non_tranches)}. Ajouter chaque libellé "
        f"soit à cards.FORMULATION_SOURCES_EXACT / "
        f"FORMULATION_SOURCE_PREFIXES, soit à "
        f"cards.FORMULATION_SOURCES_EXCLUDED."
    )

    fantomes = connus - mapping
    assert not fantomes, (
        f"Libellés déclarés dans cards.py mais absents de "
        f"_SOURCE_CSV_MAP : {sorted(fantomes)}. Symptôme typique d'un "
        f"renommage de libellé non répercuté — le filtre de cards.py ne "
        f"matcherait plus rien, silencieusement."
    )


def test_le_prefixe_aphp_capture_bien_des_sources() -> None:
    """Le filtre par préfixe doit désigner au moins une source réelle."""
    captures = _labels_matching_prefixes()
    assert captures, (
        f"Aucun libellé du mapping ne commence par "
        f"{cards.FORMULATION_SOURCE_PREFIXES} — le filtre par préfixe de "
        f"cards.py est devenu inopérant."
    )


@pytest.mark.parametrize("label", cards.FORMULATION_SOURCES_EXACT)
def test_source_exacte_produit_des_lignes_dans_le_csv(
    csv_final_df: pl.DataFrame, label: str
) -> None:
    """Un libellé cohérent entre les modules doit aussi exister en données."""
    n = csv_final_df.filter(pl.col("source") == label).height
    assert n > 0, (
        f"Le libellé « {label} » attendu par cards.py ne produit aucune ligne dans le CSV final."
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

    for label in cards.FORMULATION_SOURCES_EXACT:
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
