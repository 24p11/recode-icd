"""Parseur des expressions de codes du guide méthodologique.

Le guide désigne ses cibles à cinq granularités différentes, et la
granularité **porte du sens** : « le DP appartient au chapitre XXI » et
« le DP est Z86.70 » sont deux consignes de portée incomparable. Le
parseur conserve cette information dans `TypeExpr`, qui devient ensuite
la clé de tri par spécificité.

⚠ **La spécificité ne se lit PAS dans le référentiel.** Dans
`merged`, la colonne `type` ne vaut que `chapter | block | category` :
`Z86.70` y est typé `category`, exactement comme `I69`. La finesse d'une
consigne se dérive donc de l'**expression écrite dans la table curée**,
jamais du nested set — qui ne sert qu'à l'expansion.

Une expression non parsable est une **erreur remontée au rapport de
build**, jamais une ligne silencieusement ignorée : une consigne perdue
est indétectable en aval.

**Notation du guide ≠ encodage du référentiel** (arbitrage n° 12, RF
2026-09-05, cas O04). Quelques catégories sont encodées par le
référentiel avec leurs 4e et 5e caractères dans l'ordre inverse de celui
qu'écrit le guide (« O04.90 » du guide = feuille `O04.-0.9`). La table
curée déclare l'expression **telle qu'écrite par le guide** ; la
traduction est confiée à une table de correspondance déclarative
(`notations.py`), passée en argument. Sans table, ou pour une forme hors
table, l'expression reste non parsable — au rapport, jamais au silence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from recode_icd.recommendations.notations import Notations

#: Tiret typographique utilisé par le guide (« I63.– »). Le guide n'est
#: pas constant : on accepte aussi le tiret ASCII et le tiret demi-cadratin.
TIRETS = "–—-"

#: Chiffres romains des 22 chapitres de la CIM-10.
CHAPITRES_ROMAINS = frozenset(
    (
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
    )
)


class TypeExpr(IntEnum):
    """Granularité d'une expression, ordonnée par spécificité croissante.

    Les valeurs sont **ordonnées** : `CODE > CATEGORIE > PLAGE >
    CHAPITRE`. C'est cette relation d'ordre qui implémente la règle
    « code > catégorie > plage/bloc > chapitre », la même convention de
    résolution que la `chapter_policy`.
    """

    CHAPITRE = 0
    PLAGE = 1
    CATEGORIE = 2
    CODE = 3


@dataclass(frozen=True)
class ExpressionCode:
    """Expression parsée.

    `debut` / `fin` ne sont renseignés que pour une `PLAGE`. Pour les
    trois autres formes, `valeur` porte le code ou le chiffre romain.

    `noeuds` n'est renseigné que pour une expression **traduite** par la
    table de notations (cf. `notations.py`) : ce sont les nœuds du
    référentiel qu'elle désigne, quand sa notation n'est pas celle du
    référentiel. Vide sinon — `valeur` suffit à la résolution.
    """

    brut: str
    type: TypeExpr
    valeur: str
    debut: str | None = None
    fin: str | None = None
    noeuds: tuple[str, ...] = ()


class CodeExprError(ValueError):
    """Expression de codes non parsable."""


# `A00` — catégorie à 3 caractères.
_RE_CATEGORIE = re.compile(r"^([A-Z]\d{2})$")
# `A00.1`, `Z86.70`, `U07.13` — code à 4 caractères ou plus.
_RE_CODE = re.compile(r"^([A-Z]\d{2}\.\d{1,3})$")
# `I63.–` — notation à tiret : désigne la catégorie et toutes ses
# subdivisions. Sémantiquement équivalente à la catégorie nue.
_RE_CATEGORIE_TIRET = re.compile(rf"^([A-Z]\d{{2}})\.[{TIRETS}]$")
# `I60-I64`, `G46.0-G46.2` — plage. Les deux bornes doivent être de même
# forme (catégorie↔catégorie ou code↔code).
_RE_PLAGE = re.compile(rf"^([A-Z]\d{{2}}(?:\.\d{{1,3}})?)[{TIRETS}]([A-Z]\d{{2}}(?:\.\d{{1,3}})?)$")


def parse_code_expr(expr: str, notations: Notations | None = None) -> ExpressionCode:
    """Parse une expression de codes, ou lève `CodeExprError`.

    `notations` : table de correspondance des catégories à encodage
    inversé (arbitrage n° 12). Consultée **avant** les formes génériques,
    pour les seules catégories qu'elle déclare : « O04.90 » ressemble à
    un code et le serait sans elle — introuvable dans le référentiel.
    Sans table, ces expressions restent non parsables ou non résolues,
    et partent au rapport.

    Cinq formes reconnues :

    >>> parse_code_expr("Z86.70").type.name
    'CODE'
    >>> parse_code_expr("I69").type.name
    'CATEGORIE'
    >>> parse_code_expr("I63.–").type.name    # tiret typographique
    'CATEGORIE'
    >>> parse_code_expr("I63.-").type.name    # tiret ASCII
    'CATEGORIE'
    >>> parse_code_expr("I60-I64").type.name
    'PLAGE'
    >>> parse_code_expr("XXI").type.name
    'CHAPITRE'

    La notation à tiret est rendue **équivalente à la catégorie nue** :
    « I63.– » et « I69 » désignent tous deux une catégorie et toutes ses
    subdivisions. Les distinguer donnerait deux niveaux de spécificité
    pour une seule réalité.
    """
    nettoye = expr.strip()
    if not nettoye:
        raise CodeExprError("Expression vide.")

    if notations is not None and (traduite := notations.traduit(nettoye, brut=expr)) is not None:
        return traduite

    if nettoye in CHAPITRES_ROMAINS:
        return ExpressionCode(brut=expr, type=TypeExpr.CHAPITRE, valeur=nettoye)

    if m := _RE_CODE.match(nettoye):
        return ExpressionCode(brut=expr, type=TypeExpr.CODE, valeur=m.group(1))

    if m := _RE_CATEGORIE.match(nettoye):
        return ExpressionCode(brut=expr, type=TypeExpr.CATEGORIE, valeur=m.group(1))

    if m := _RE_CATEGORIE_TIRET.match(nettoye):
        return ExpressionCode(brut=expr, type=TypeExpr.CATEGORIE, valeur=m.group(1))

    if m := _RE_PLAGE.match(nettoye):
        debut, fin = m.group(1), m.group(2)
        if ("." in debut) != ("." in fin):
            raise CodeExprError(
                f"Plage « {expr} » : bornes de granularités différentes "
                f"({debut} et {fin}). Écrire deux expressions plutôt qu'une "
                f"plage ambiguë."
            )
        if fin < debut:
            raise CodeExprError(f"Plage « {expr} » : borne finale antérieure à la borne initiale.")
        return ExpressionCode(
            brut=expr,
            type=TypeExpr.PLAGE,
            valeur=f"{debut}-{fin}",
            debut=debut,
            fin=fin,
        )

    # Piège fréquent : un chiffre romain inexistant (« XXV ») ressemble à
    # un chapitre. Le message doit le dire, sinon on cherche du côté du
    # format alors que c'est le contenu qui est faux.
    if re.fullmatch(r"[IVXLCDM]+", nettoye):
        raise CodeExprError(
            f"« {expr} » ressemble à un chapitre mais n'est pas l'un des 22 chapitres de la CIM-10."
        )
    raise CodeExprError(f"Expression de codes non reconnue : « {expr} ».")


__all__ = (
    "CHAPITRES_ROMAINS",
    "TIRETS",
    "CodeExprError",
    "ExpressionCode",
    "TypeExpr",
    "parse_code_expr",
)
