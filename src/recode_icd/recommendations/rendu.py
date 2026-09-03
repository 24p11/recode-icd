"""Rendu de la section « Consignes de codage » des fiches.

Prototype validé : `scripts/explore/rendu_recommandations_fiches.py`
(six témoins verrouillés par assertions) ; modèle et catalogue des rôles
dans `docs/analyses/2026-08-09_conception_base_recommandations_guide_methodo.md`.

Règles de rendu, dans l'ordre d'application :

1. filtre `centralite = sujet` par défaut (`avec_exemples=True` admet
   les codes cités en illustration, rendus à part — jamais mêlés aux
   consignes qui norment) ;
2. exclusion du rôle `contexte`, **avant** la déduplication : si une
   consigne cite le code en `contexte` et le couvre par ailleurs en
   `regi`, c'est l'association qui régit qui reste ;
3. déduplication par `rec_id` : une consigne peut atteindre le même
   code par plusieurs expressions (`Z51.31` par `Z51` et par `Z51.31`)
   voire par deux centralités (`Z20.1` en `exemple` au code et en
   `sujet` via `Z20`). `sujet` prime sur `exemple` — la consigne norme
   le code, l'illustration ne s'y ajoute pas — puis le niveau le plus
   spécifique prime ;
4. tri par `cle_de_tri` de la résolution (spécificité décroissante
   CODE > CATEGORIE > PLAGE > CHAPITRE, sujet avant exemple, `rec_id`) ;
5. les consignes de niveau chapitre sont regroupées en fin de section
   sous « Règles générales du chapitre », chacune précédée de sa
   `situation` entre parenthèses : c'est elle qui borne la portée et
   transforme une règle apparemment hors sujet en information de
   non-application (cas AVC-14 / Z23.0 du prototype) ;
6. les `exemple` sont rendus en bloc cité `>` introduit par « À titre
   d'exemple dans le guide : » — signal structurel « ceci illustre,
   ceci ne norme pas ». Le bloc précède les règles générales, sinon il
   serait visuellement rattaché à leur sous-titre `###` ;
7. chaque consigne est préfixée de son `rec_id` entre crochets, et le
   millésime du titre vient de la table, jamais d'une constante.

Cette section est **hors chapter_policy** : R1/R2/R3 gouvernent les
Formulations, pas les consignes.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from recode_icd.recommendations.code_expr import TypeExpr
from recode_icd.recommendations.resolution import cle_de_tri


def consignes_pour(
    rec_codes: pl.DataFrame,
    recs: pl.DataFrame,
    code: str,
    *,
    avec_exemples: bool = False,
    roles_exclus: tuple[str, ...] = ("contexte",),
) -> list[dict[str, Any]]:
    """Consignes à rendre sur la fiche de `code`, triées.

    Args:
        rec_codes : table résolue (`recommendation_codes.parquet`).
        recs : table des consignes (`recommendations.parquet`).
        code : code feuille de la fiche.
        avec_exemples : admettre les associations `centralite=exemple`.
        roles_exclus : rôles écartés avant déduplication.

    Returns:
        Une liste de dicts (colonnes de l'association + `texte`, `type`,
        `millesime`, `situation` de la consigne), triée par `cle_de_tri`.
    """
    assoc = rec_codes.filter(pl.col("code") == code)
    if not avec_exemples:
        assoc = assoc.filter(pl.col("centralite") == "sujet")
    assoc = assoc.filter(~pl.col("role").is_in(roles_exclus))
    assoc = assoc.sort(
        [pl.col("centralite") != "sujet", pl.col("specificite")],
        descending=[False, True],
    ).unique(subset="rec_id", keep="first", maintain_order=True)
    lignes = assoc.join(
        recs.select("rec_id", "texte", "type", "millesime", "situation"),
        on="rec_id",
        how="left",
    )
    return sorted(
        lignes.iter_rows(named=True),
        key=lambda r: cle_de_tri(TypeExpr(r["specificite"]), r["centralite"], r["rec_id"]),
    )


def _puce(r: dict[str, Any]) -> str:
    return f"- [{r['rec_id']}] {r['texte']}"


def _puce_generale(r: dict[str, Any]) -> str:
    if r["situation"]:
        return f"- [{r['rec_id']}] ({r['situation']}) {r['texte']}"
    return _puce(r)


def rendre_section_consignes(
    rec_codes: pl.DataFrame,
    recs: pl.DataFrame,
    code: str,
) -> str | None:
    """Section « Consignes de codage » de la fiche de `code`, en markdown.

    None si aucune consigne ne vise le code — la fiche reste identique
    à ce qu'elle était avant ce chantier.
    """
    lignes = consignes_pour(rec_codes, recs, code, avec_exemples=True)
    if not lignes:
        return None
    millesime = lignes[0]["millesime"]
    sujets = [r for r in lignes if r["centralite"] == "sujet"]
    exemples = [r for r in lignes if r["centralite"] == "exemple"]
    specifiques = [r for r in sujets if TypeExpr(r["specificite"]) is not TypeExpr.CHAPITRE]
    generales = [r for r in sujets if TypeExpr(r["specificite"]) is TypeExpr.CHAPITRE]

    blocs = [f"## Consignes de codage (guide méthodologique {millesime})"]
    if specifiques:
        blocs.append("\n".join(_puce(r) for r in specifiques))
    if exemples:
        cite = ["> À titre d'exemple dans le guide :", ">"]
        cite += [f"> {_puce(r)}" for r in exemples]
        blocs.append("\n".join(cite))
    if generales:
        chapitre = generales[0]["code_expr"]
        blocs.append(
            f"### Règles générales du chapitre {chapitre}\n\n"
            + "\n".join(_puce_generale(r) for r in generales)
        )
    return "\n\n".join(blocs)


__all__ = ("consignes_pour", "rendre_section_consignes")
