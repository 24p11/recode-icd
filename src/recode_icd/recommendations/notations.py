"""Table de correspondance notation du guide ↔ encodage du référentiel.

Arbitrage n° 12 du registre (RF, 2026-09-05, cas O04 / article
INTERRUPTION DE LA GROSSESSE) : **la curation est fidèle à la notation
du guide, la résolution traduit — jamais l'inverse.**

Le guide écrit « O04.90 », « O04.4 », « O04.-1 ». Le référentiel (ATIH)
encode la même catégorie avec les 4e et 5e caractères dans l'ordre
**inverse** : le nœud de 5e position `O04.-<5e>` et la feuille
`O04.-<5e>.<4e>` — « O04.90 » du guide est la feuille `O04.-0.9`. Une
table curée qui écrirait `O04.-0.9` ne prouverait plus ce que le guide
dit ; une résolution qui devinerait l'inversion sans déclaration
traduirait en silence. D'où cette table, et sa place : les tables
curées portent la notation du guide, la traduction vit ici.

Ce module ne devine rien : il ne traduit que les catégories DÉCLARÉES
dans `referentials/curation/notations_guide.yaml`, avec les valeurs de
4e et de 5e caractère qui y sont déclarées. Toute forme hors table lève
`CodeExprError` — au rapport de build, jamais au silence. Chaque entrée
est testée dans les deux sens (guide → référentiel → guide, et retour).

Trois formes du guide, pour une catégorie déclarée `Xnn` :

| Guide          | Référentiel                                     | Granularité |
|----------------|-------------------------------------------------|-------------|
| `Xnn.<4e><5e>` | feuille `Xnn.-<5e>.<4e>`                        | `CODE`      |
| `Xnn.-<5e>`    | nœud `Xnn.-<5e>` (toutes les 4e)                | `CATEGORIE` |
| `Xnn.<4e>`     | feuilles `Xnn.-<5e>.<4e>`, une par 5e déclarée  | `CATEGORIE` |

`Xnn` nu, `Xnn.-` (tiret nu) et les plages ne sont pas concernés : ce sont les
formes génériques, que `parse_code_expr` traite comme partout ailleurs.
`Xnn.-<5e>` et `Xnn.<4e>` désignent tous deux une famille de feuilles
sans être une catégorie à 3 caractères : ils prennent la granularité
`CATEGORIE`, la plus proche — un rang intermédiaire n'a pas été créé,
l'arbitrage bornant l'extension au parseur et à cette table.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from recode_icd.policy import _RACINE_DEPOT
from recode_icd.recommendations.code_expr import (
    TIRETS,
    CodeExprError,
    ExpressionCode,
    TypeExpr,
)

#: Emplacement par défaut de la table, versionnée avec le référentiel.
DEFAULT_NOTATIONS_PATH = _RACINE_DEPOT / "referentials/curation/notations_guide.yaml"

_RE_CATEGORIE = re.compile(r"^[A-Z]\d{2}$")
_RE_CHIFFRE = re.compile(r"^\d$")

#: Forme du guide sur une catégorie inversée : `Xnn.<4e><5e>`,
#: `Xnn.-<5e>` (tiret typographique ou ASCII) ou `Xnn.<4e>`.
_RE_FORME_GUIDE = re.compile(rf"^([A-Z]\d{{2}})\.(?:(\d)(\d)|[{TIRETS}](\d)|(\d))$")
#: Forme du référentiel : nœud `Xnn.-<5e>` ou feuille `Xnn.-<5e>.<4e>`.
_RE_FORME_REFERENTIEL = re.compile(r"^([A-Z]\d{2})\.-(\d)(?:\.(\d))?$")
#: Toute expression « catégorie + point + quelque chose » : c'est le
#: périmètre où la table a le dernier mot pour une catégorie déclarée.
#: La notation à tiret nue (`Xnn.-`) en est exclue — forme générique.
_RE_SOUS_CATEGORIE = re.compile(rf"^([A-Z]\d{{2}})\.(?![{TIRETS}]$).+$")


class NotationsError(ValueError):
    """Table de notations mal formée."""


@dataclass(frozen=True)
class CategorieInversee:
    """Une catégorie dont le référentiel inverse 4e et 5e caractères."""

    categorie: str
    quatriemes: tuple[str, ...]
    cinquiemes: tuple[str, ...]
    libelle: str = ""

    def noeud(self, cinquieme: str) -> str:
        """Nœud de 5e position du référentiel : `O04.-1`."""
        return f"{self.categorie}.-{cinquieme}"

    def feuille(self, quatrieme: str, cinquieme: str) -> str:
        """Feuille du référentiel : `O04.-0.9` pour « O04.90 » du guide."""
        return f"{self.categorie}.-{cinquieme}.{quatrieme}"


@dataclass(frozen=True)
class Notations:
    """La table chargée. Vide = aucune catégorie inversée déclarée."""

    categories: Mapping[str, CategorieInversee]

    def traduit(self, expr: str, brut: str | None = None) -> ExpressionCode | None:
        """Guide → référentiel.

        Retourne `None` si l'expression ne relève pas de la table (catégorie
        non déclarée, ou forme générique : `Xnn`, `Xnn.-`, plage) : le
        parseur générique s'en charge. Lève `CodeExprError` si la catégorie
        est déclarée mais la forme hors table : une 5e position que la
        table ne connaît pas n'est pas devinée, elle est signalée.
        """
        brut = expr if brut is None else brut
        m = _RE_FORME_GUIDE.match(expr)
        if m is None:
            # « O04.123 », « O04.1-O04.3 » : sur une catégorie déclarée, une
            # forme que la table ne connaît pas n'est pas rendue au parseur
            # générique — il la prendrait pour un code ou une plage du
            # référentiel, dont l'ordre des positions est précisément
            # l'inverse. Hors table = non parsable, au rapport.
            sous = _RE_SOUS_CATEGORIE.match(expr)
            if sous is not None and sous.group(1) in self.categories:
                raise CodeExprError(
                    f"« {brut} » : forme hors de la table de notations pour "
                    f"{sous.group(1)} (formes admises : {sous.group(1)}.<4e><5e>, "
                    f"{sous.group(1)}.-<5e>, {sous.group(1)}.<4e>)."
                )
            return None
        cat = self.categories.get(m.group(1))
        if cat is None:
            return None
        quatrieme_2, cinquieme_2, cinquieme_tiret, quatrieme_1 = m.group(2, 3, 4, 5)

        if quatrieme_2 is not None:
            _verifie(cat, brut, quatrieme=quatrieme_2, cinquieme=cinquieme_2)
            return ExpressionCode(
                brut=brut,
                type=TypeExpr.CODE,
                valeur=expr,
                noeuds=(cat.feuille(quatrieme_2, cinquieme_2),),
            )
        if cinquieme_tiret is not None:
            _verifie(cat, brut, cinquieme=cinquieme_tiret)
            return ExpressionCode(
                brut=brut,
                type=TypeExpr.CATEGORIE,
                # Tiret normalisé : le tiret typographique du guide et le tiret ASCII
                # donnent la même
                # expression, comme la notation à tiret des catégories.
                valeur=cat.noeud(cinquieme_tiret),
                noeuds=(cat.noeud(cinquieme_tiret),),
            )
        _verifie(cat, brut, quatrieme=quatrieme_1)
        return ExpressionCode(
            brut=brut,
            type=TypeExpr.CATEGORIE,
            valeur=expr,
            noeuds=tuple(cat.feuille(quatrieme_1, c) for c in cat.cinquiemes),
        )

    def vers_guide(self, code_referentiel: str) -> str | None:
        """Référentiel → guide : `O04.-0.9` → « O04.90 », `O04.-1` → « O04.-1 ».

        `None` si le code ne relève pas de la table. Lève `CodeExprError`
        si la catégorie est déclarée mais la position hors table — c'est
        le sens qui détecte une table incomplète face au référentiel.
        """
        m = _RE_FORME_REFERENTIEL.match(code_referentiel)
        if m is None:
            return None
        cat = self.categories.get(m.group(1))
        if cat is None:
            return None
        cinquieme, quatrieme = m.group(2), m.group(3)
        _verifie(cat, code_referentiel, quatrieme=quatrieme, cinquieme=cinquieme)
        if quatrieme is None:
            return cat.noeud(cinquieme)
        return f"{cat.categorie}.{quatrieme}{cinquieme}"


def _verifie(
    cat: CategorieInversee,
    expr: str,
    *,
    quatrieme: str | None = None,
    cinquieme: str | None = None,
) -> None:
    if quatrieme is not None and quatrieme not in cat.quatriemes:
        raise CodeExprError(
            f"« {expr} » : 4e caractère « {quatrieme} » hors de la table de "
            f"notations pour {cat.categorie} (déclarés : {', '.join(cat.quatriemes)}). "
            f"Déclarer la position dans notations_guide.yaml si le référentiel la porte."
        )
    if cinquieme is not None and cinquieme not in cat.cinquiemes:
        raise CodeExprError(
            f"« {expr} » : 5e caractère « {cinquieme} » hors de la table de "
            f"notations pour {cat.categorie} (déclarés : {', '.join(cat.cinquiemes)}). "
            f"Déclarer la position dans notations_guide.yaml si le référentiel la porte."
        )


def _chiffres(brut: Any, champ: str, categorie: str) -> tuple[str, ...]:
    if not isinstance(brut, list) or not brut:
        raise NotationsError(f"{categorie}.{champ} : liste non vide de chiffres attendue.")
    valeurs = tuple(str(v) for v in brut)
    fautives = [v for v in valeurs if not _RE_CHIFFRE.match(v)]
    if fautives:
        raise NotationsError(f"{categorie}.{champ} : valeurs non chiffrées {fautives}.")
    if len(set(valeurs)) != len(valeurs):
        raise NotationsError(f"{categorie}.{champ} : doublons dans {list(valeurs)}.")
    return valeurs


def charge_notations(path: Path | None = None) -> Notations:
    """Charge la table depuis le YAML. Une table absente est une erreur :
    l'appelant qui n'en veut pas passe `None` au parseur, il ne tombe pas
    sur un fichier manquant en silence."""
    chemin = path if path is not None else DEFAULT_NOTATIONS_PATH
    brut: dict[str, Any] = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    entrees = brut.get("categories_inversees") or {}
    if not isinstance(entrees, dict):
        raise NotationsError("`categories_inversees` doit être un mapping catégorie → déclaration.")
    categories: dict[str, CategorieInversee] = {}
    for categorie, declaration in entrees.items():
        nom = str(categorie)
        if not _RE_CATEGORIE.match(nom):
            raise NotationsError(f"« {nom} » n'est pas une catégorie à 3 caractères.")
        if not isinstance(declaration, dict):
            raise NotationsError(f"{nom} : déclaration attendue (quatriemes, cinquiemes).")
        categories[nom] = CategorieInversee(
            categorie=nom,
            quatriemes=_chiffres(declaration.get("quatriemes"), "quatriemes", nom),
            cinquiemes=_chiffres(declaration.get("cinquiemes"), "cinquiemes", nom),
            libelle=str(declaration.get("libelle", "")),
        )
    return Notations(categories=categories)


__all__ = (
    "DEFAULT_NOTATIONS_PATH",
    "CategorieInversee",
    "Notations",
    "NotationsError",
    "charge_notations",
)
