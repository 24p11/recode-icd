"""Résolution des expressions de codes vers les codes feuilles.

L'expansion s'appuie sur le **nested set** déjà en place dans
`merged` (`left` / `right`) : les descendants d'un nœud sont exactement
les nœuds dont l'intervalle est inclus dans le sien. Une feuille est un
nœud dont `right == left + 1`.

**Les expressions de niveau chapitre SONT résolues jusqu'aux feuilles**
(décision actée). Les fiches sont injectées telles quelles dans des
prompts : elles doivent être autonomes, donc porter la consigne, pas un
renvoi. Le bruit que cela produit est maîtrisé au **rendu** — les
consignes de chapitre sont regroupées en fin de section sous « Règles
générales du chapitre » — et non en amputant la résolution.

⚠ La spécificité vient de l'expression parsée, **jamais** du nœud
atteint : `merged.type` ne distingue pas `Z86.70` de `I69` (cf.
`code_expr`).
"""

from __future__ import annotations

import polars as pl

from recode_icd.recommendations.code_expr import ExpressionCode, TypeExpr


class ResolutionError(ValueError):
    """Expression parsable mais introuvable dans le référentiel."""


def _feuilles(merged: pl.DataFrame) -> pl.DataFrame:
    """Les codes feuilles du nested set."""
    return merged.filter(pl.col("right") == pl.col("left") + 1)


def _bornes(merged: pl.DataFrame, code: str) -> tuple[int, int]:
    ligne = merged.filter(pl.col("code") == code)
    if ligne.height == 0:
        raise ResolutionError(f"Code « {code} » absent du référentiel.")
    return int(ligne["left"][0]), int(ligne["right"][0])


def resout(expr: ExpressionCode, merged: pl.DataFrame) -> list[str]:
    """Codes feuilles couverts par `expr`, triés.

    Lève `ResolutionError` si un nœud cité est absent du référentiel —
    remonté au rapport de build, jamais avalé.

    Un `CODE` déjà feuille se résout en lui-même ; un `CODE` qui porte
    des subdivisions (rare mais réel : `U07.1` porte `U07.10`..`U07.15`)
    se résout en ses feuilles. C'est cohérent avec le CSV maître, qui ne
    retient que les feuilles.
    """
    if expr.type is TypeExpr.PLAGE:
        assert expr.debut is not None and expr.fin is not None
        gauche, _ = _bornes(merged, expr.debut)
        _, droite = _bornes(merged, expr.fin)
    else:
        gauche, droite = _bornes(merged, expr.valeur)

    couverts = _feuilles(merged).filter((pl.col("left") >= gauche) & (pl.col("right") <= droite))
    return sorted(couverts["code"].to_list())


#: Rang de tri d'une consigne pour un code donné : spécificité
#: décroissante, puis `centralite` (sujet avant exemple), puis `rec_id`
#: pour rendre le tri **total** — sans ce dernier critère, deux consignes
#: de même spécificité s'ordonneraient au gré du moteur, et le build ne
#: serait pas déterministe.
def cle_de_tri(specificite: TypeExpr, centralite: str, rec_id: str) -> tuple[int, int, str]:
    """Clé de tri d'une consigne : plus spécifique d'abord."""
    return (-int(specificite), 0 if centralite == "sujet" else 1, rec_id)


__all__ = ("ResolutionError", "cle_de_tri", "resout")
