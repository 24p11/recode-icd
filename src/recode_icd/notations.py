"""Table de notation unique des codes CIM-10 FR.

Arbitrage n° 12 du registre (RF, 2026-09-05, cas O04), étendu par le
chantier couverture ATIH (D1-c) : **la curation est fidèle à la notation
de sa source, la résolution traduit — jamais l'inverse.**

Trois écritures d'un même code coexistent :

- **compacte** (kit ATIH, RUM) : point omis, `+` possible en 4e ou 5e
  position — `O0490`, `M62810`, `B24+0`, `C169+0` ;
- **pointée** (guide MCO, usage courant) : point après le 3e caractère,
  sauf quand le 4e est `+` — `O04.90`, `M62.810`, `B24+0`, `C16.9+0` ;
- **maître** (nos livrables, héritée de l'export ANS) : pointée, sauf
  les familles déclarées dans `referentials/curation/notations_codes.yaml`
  — deux familles **inversées** (`O04.-<5e>.<4e>`, `M62.8-<6e><5e>`) et
  neuf catégories à `+` **ponctué** (`B24.+0`).

Ce module ne devine rien : il ne traduit que ce que la table déclare.
Toute forme hors table sur une famille déclarée lève `CodeExprError` —
au rapport de build, jamais au silence. Chaque entrée est testée dans
les deux sens : compacte → maître → compacte sur le kit ATIH entier,
maître → compacte injective sur le nested set.

Consommateurs : le parseur des consignes du guide
(`recommendations.code_expr`, forme pointée → nœuds du maître), le loader
du kit ATIH (`loaders.atih`, compacte → maître) et le résolveur des
consommateurs (D0, toute écriture → maître).
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
DEFAULT_NOTATIONS_PATH = _RACINE_DEPOT / "referentials/curation/notations_codes.yaml"

_RE_CATEGORIE = re.compile(r"^[A-Z]\d{2}$")
_RE_BASE_COMPACTE = re.compile(r"^[A-Z]\d{2}\d*$")
_RE_CHIFFRE = re.compile(r"^\d$")
_RE_TIRETS = re.compile(f"[{TIRETS}]")
#: `+` en 4e position (`B24+0`, `B24.+0`).
_RE_PLUS_4E = re.compile(r"^([A-Z]\d{2})\.?\+(\d+)$")


class NotationsError(ValueError):
    """Table de notations mal formée."""


def ecriture_pointee(code_compact: str) -> str:
    """Compacte → pointée : point après le 3e caractère, sauf `+` en 4e.

    C'est la règle que suivent 99,4 % des codes du maître (`A00.0`,
    `M00.00`, `S37.800`, `C16.9+0`, `T08+0`, `F03+00`). Les familles
    déclarées s'en écartent : voir `Notations.ecriture_maitre`.
    """
    if len(code_compact) <= 3 or code_compact[3] == "+":
        return code_compact
    return f"{code_compact[:3]}.{code_compact[3:]}"


def _gabarit_en_regex(gabarit: str, base: str) -> re.Pattern[str]:
    """`{base}.-{b}.{a}` → regex capturant `a` et `b` (groupes nommés)."""
    motif = re.escape(gabarit).replace(r"\{base\}", re.escape(base))
    motif = motif.replace(r"\{a\}", r"(?P<a>\d)").replace(r"\{b\}", r"(?P<b>\d)")
    return re.compile(f"^{motif}$")


@dataclass(frozen=True)
class FamilleInversee:
    """Une famille dont le maître inverse deux positions.

    `a` est la première position dans l'ordre compact, `b` la seconde ;
    le maître écrit `b` avant `a` selon `feuille_maitre`. Le nœud de
    regroupement par `b` (`noeud_maitre`) n'a pas d'équivalent compact.
    """

    nom: str
    base_compacte: str
    base_maitre: str
    feuille_maitre: str
    noeud_maitre: str
    a: tuple[str, ...]
    b: tuple[str, ...]
    libelle: str = ""

    def compact(self, a: str, b: str) -> str:
        return f"{self.base_compacte}{a}{b}"

    def feuille(self, a: str, b: str) -> str:
        return self.feuille_maitre.format(base=self.base_maitre, a=a, b=b)

    def noeud(self, b: str) -> str:
        return self.noeud_maitre.format(base=self.base_maitre, b=b)

    def verifie(self, expr: str, *, a: str | None = None, b: str | None = None) -> None:
        if a is not None and a not in self.a:
            raise CodeExprError(
                f"« {expr} » : position « {a} » hors de la table de notations pour "
                f"{self.nom} (a ∈ {{{', '.join(self.a)}}}). Déclarer la position dans "
                f"notations_codes.yaml si le référentiel la porte."
            )
        if b is not None and b not in self.b:
            raise CodeExprError(
                f"« {expr} » : position « {b} » hors de la table de notations pour "
                f"{self.nom} (b ∈ {{{', '.join(self.b)}}}). Déclarer la position dans "
                f"notations_codes.yaml si le référentiel la porte."
            )

    @property
    def _re_feuille(self) -> re.Pattern[str]:
        return _gabarit_en_regex(self.feuille_maitre, self.base_maitre)

    @property
    def _re_noeud(self) -> re.Pattern[str]:
        return _gabarit_en_regex(self.noeud_maitre, self.base_maitre)

    def releve(self, expr: str) -> bool:
        """L'expression (pointée ou maître) est-elle une sous-forme de la famille ?

        `O04` nu, `O04.-` (tiret nu) et les plages `O04-O06` n'en relèvent
        pas : formes génériques. Tout le reste sous `base_maitre` en relève
        et doit donc être l'une des trois formes admises.
        """
        if not expr.startswith(self.base_maitre) or expr == self.base_maitre:
            return False
        suite = _RE_TIRETS.sub("-", expr[len(self.base_maitre) :])
        if suite in (".-", "-"):
            return False  # notation à tiret nue : la catégorie et ses subdivisions
        # Reste : tout sauf une plage `O04-O06`.
        return re.match(r"^-[A-Z]", suite) is None


@dataclass(frozen=True)
class Notations:
    """La table chargée. Vide = aucune famille déclarée."""

    familles: Mapping[str, FamilleInversee]
    plus_ponctue: frozenset[str] = frozenset()

    # -- pointée (guide) → nœuds du maître : le parseur des consignes ----

    def traduit(self, expr: str, brut: str | None = None) -> ExpressionCode | None:
        """Forme du guide → nœuds du maître.

        Trois formes par famille : feuille pointée (`O04.90` → `CODE`),
        nœud de regroupement (`O04.-1` → `CATEGORIE`), `a` seul (`O04.4`
        → une feuille par `b`, `CATEGORIE`). `None` si l'expression ne
        relève d'aucune famille ; `CodeExprError` si elle en relève sans
        être l'une des trois formes — hors table, jamais deviné.
        """
        brut = expr if brut is None else brut
        normalise = _RE_TIRETS.sub("-", expr)
        for fam in self.familles.values():
            if not fam.releve(expr):
                continue
            m = fam._re_noeud.match(normalise)
            if m is not None:
                fam.verifie(brut, b=m.group("b"))
                return ExpressionCode(
                    brut=brut,
                    type=TypeExpr.CATEGORIE,
                    valeur=fam.noeud(m.group("b")),
                    noeuds=(fam.noeud(m.group("b")),),
                )
            compact = normalise.replace(".", "")
            if compact.startswith(fam.base_compacte):
                reste = compact[len(fam.base_compacte) :]
                if len(reste) == 2 and reste.isdigit() and normalise == ecriture_pointee(compact):
                    fam.verifie(brut, a=reste[0], b=reste[1])
                    return ExpressionCode(
                        brut=brut,
                        type=TypeExpr.CODE,
                        valeur=normalise,
                        noeuds=(fam.feuille(reste[0], reste[1]),),
                    )
                if len(reste) == 1 and reste.isdigit() and normalise == ecriture_pointee(compact):
                    fam.verifie(brut, a=reste)
                    return ExpressionCode(
                        brut=brut,
                        type=TypeExpr.CATEGORIE,
                        valeur=normalise,
                        noeuds=tuple(fam.feuille(reste, b) for b in fam.b),
                    )
            raise CodeExprError(
                f"« {brut} » : forme hors de la table de notations pour {fam.nom} "
                f"(formes admises : {ecriture_pointee(fam.compact('a', 'b'))} feuille, "
                f"{fam.noeud('b')} nœud, {ecriture_pointee(fam.base_compacte + 'a')} "
                f"toutes les positions b)."
            )
        return None

    def vers_guide(self, code_maitre: str) -> str | None:
        """Maître → forme du guide : `O04.-0.9` → « O04.90 », `O04.-1` → « O04.-1 ».

        `None` si le code ne relève d'aucune famille.
        """
        for fam in self.familles.values():
            if m := fam._re_feuille.match(code_maitre):
                fam.verifie(code_maitre, a=m.group("a"), b=m.group("b"))
                return ecriture_pointee(fam.compact(m.group("a"), m.group("b")))
            if m := fam._re_noeud.match(code_maitre):
                fam.verifie(code_maitre, b=m.group("b"))
                return fam.noeud(m.group("b"))
        return None

    # -- compacte (ATIH) ↔ maître : le loader du kit et le résolveur ----

    def ecriture_maitre(self, code_compact: str) -> str:
        """Compacte → écriture du maître.

        Famille inversée : `O0490` → `O04.-0.9`, `M62810` → `M62.8-01`.
        Un code compact de la famille qui n'est pas une feuille (`O040`,
        `M6280` — niveaux intermédiaires du kit) n'a pas d'écriture
        déclarée : il reçoit l'écriture pointée. `+` ponctué : `B24+0` →
        `B24.+0`. Sinon : pointée.
        """
        for fam in self.familles.values():
            if code_compact.startswith(fam.base_compacte):
                reste = code_compact[len(fam.base_compacte) :]
                if len(reste) == 2 and reste[0] in fam.a and reste[1] in fam.b:
                    return fam.feuille(reste[0], reste[1])
        m = _RE_PLUS_4E.match(code_compact)
        if m is not None and m.group(1) in self.plus_ponctue:
            return f"{m.group(1)}.+{m.group(2)}"
        return ecriture_pointee(code_compact)

    def cle_compacte(self, code_maitre: str) -> str | None:
        """Maître → compacte, ou `None` pour un nœud sans équivalent compact.

        Nœuds sans équivalent : les regroupements à tiret (`O04.-1`,
        `M62.8-0`, `S37.8-0`) — retirer leur tiret ferait collisionner
        `S37.8-0` (glande surrénale, nœud) avec `S37.80` (sans plaie,
        feuille). Les blocs (`A00-A09`) et chapitres ne sont pas des codes.
        """
        for fam in self.familles.values():
            if m := fam._re_feuille.match(code_maitre):
                return fam.compact(m.group("a"), m.group("b"))
            if fam._re_noeud.match(code_maitre):
                return None
        if "-" in code_maitre:
            return None
        return code_maitre.replace(".", "")

    def resout_ecriture(self, saisie: str) -> str:
        """Toute écriture (compacte, pointée, maître) → écriture du maître.

        Sert au résolveur des consommateurs : un code saisi sous n'importe
        laquelle des trois formes trouve son écriture au maître, ou lève
        `CodeExprError` si la forme est hors table.
        """
        nettoye = _RE_TIRETS.sub("-", saisie.strip().upper())
        if not nettoye:
            raise CodeExprError("Code vide.")
        if "-" in nettoye:
            # Un tiret n'existe que dans les écritures du maître (feuilles
            # inversées, nœuds de regroupement) : la forme est déjà celle
            # du maître, ou n'est rien.
            return nettoye
        return self.ecriture_maitre(nettoye.replace(".", ""))


def _chiffres(brut: Any, champ: str, nom: str) -> tuple[str, ...]:
    if not isinstance(brut, list) or not brut:
        raise NotationsError(f"{nom}.{champ} : liste non vide de chiffres attendue.")
    valeurs = tuple(str(v) for v in brut)
    fautives = [v for v in valeurs if not _RE_CHIFFRE.match(v)]
    if fautives:
        raise NotationsError(f"{nom}.{champ} : valeurs non chiffrées {fautives}.")
    if len(set(valeurs)) != len(valeurs):
        raise NotationsError(f"{nom}.{champ} : doublons dans {list(valeurs)}.")
    return valeurs


def _famille(nom: str, declaration: Any) -> FamilleInversee:
    if not isinstance(declaration, dict):
        raise NotationsError(f"{nom} : déclaration attendue (base_compacte, base_maitre, …).")
    base_compacte = str(declaration.get("base_compacte", ""))
    base_maitre = str(declaration.get("base_maitre", ""))
    if not _RE_BASE_COMPACTE.match(base_compacte):
        raise NotationsError(
            f"{nom}.base_compacte « {base_compacte} » n'est pas un préfixe compact."
        )
    if base_maitre.replace(".", "") != base_compacte:
        raise NotationsError(
            f"{nom} : base_maitre « {base_maitre} » et base_compacte « {base_compacte} » "
            f"ne désignent pas le même préfixe."
        )
    feuille = str(declaration.get("feuille_maitre", ""))
    noeud = str(declaration.get("noeud_maitre", ""))
    if not all(x in feuille for x in ("{base}", "{a}", "{b}")):
        raise NotationsError(f"{nom}.feuille_maitre doit contenir {{base}}, {{a}} et {{b}}.")
    if not all(x in noeud for x in ("{base}", "{b}")) or "{a}" in noeud:
        raise NotationsError(f"{nom}.noeud_maitre doit contenir {{base}} et {{b}}, sans {{a}}.")
    return FamilleInversee(
        nom=nom,
        base_compacte=base_compacte,
        base_maitre=base_maitre,
        feuille_maitre=feuille,
        noeud_maitre=noeud,
        a=_chiffres(declaration.get("a"), "a", nom),
        b=_chiffres(declaration.get("b"), "b", nom),
        libelle=str(declaration.get("libelle", "")),
    )


def charge_notations(path: Path | None = None) -> Notations:
    """Charge la table depuis le YAML. Une table absente est une erreur :
    l'appelant qui n'en veut pas passe `None`, il ne tombe pas sur un
    fichier manquant en silence."""
    chemin = path if path is not None else DEFAULT_NOTATIONS_PATH
    brut: dict[str, Any] = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    entrees = brut.get("familles_inversees") or {}
    if not isinstance(entrees, dict):
        raise NotationsError("`familles_inversees` doit être un mapping nom → déclaration.")
    familles = {str(nom): _famille(str(nom), decl) for nom, decl in entrees.items()}
    plus = brut.get("plus_ponctue") or []
    if not isinstance(plus, list) or any(not _RE_CATEGORIE.match(str(c)) for c in plus):
        raise NotationsError("`plus_ponctue` : liste de catégories à 3 caractères attendue.")
    return Notations(familles=familles, plus_ponctue=frozenset(str(c) for c in plus))


__all__ = (
    "DEFAULT_NOTATIONS_PATH",
    "FamilleInversee",
    "Notations",
    "NotationsError",
    "charge_notations",
    "ecriture_pointee",
)
