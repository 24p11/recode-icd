"""Normalisation textuelle pour le matching de notes entre OFS et OWL/ANS.

Référence canonique : `docs/source_mapping.md`, section
"Règle de réconciliation pour les notes typées" + précision sur la
dimension textuelle.

La normalisation est utilisée UNIQUEMENT pour la comparaison. Les
libellés exportés conservent leur forme originale.
"""

from __future__ import annotations

import re
import unicodedata

import polars as pl

_WHITESPACE_RE = re.compile(r"\s+")
# Ponctuation à remplacer par un espace pour le matching. Couvre les variantes
# typographiques (apostrophes courbes, tirets longs, points médians, etc.).
_PUNCT_TO_SPACE_RE = re.compile(r"[.,;:!?()\[\]{}\-–—_/\\'\"`′‘’“”…•·]")


def normalize_for_match(text: str | None) -> str | None:
    """Normalise un libellé pour comparaison sémantique.

    Étapes (cf `docs/source_mapping.md`) :
    - décomposition NFKD + suppression des combining marks (≈ strip accents)
    - lowercase
    - remplacement de toute ponctuation interne par un espace (gère
      `V.cholerae` ↔ `V cholerae`, `non-allergique` ↔ `non allergique`,
      apostrophes typographiques `’` vs `'`, etc.)
    - tous whitespaces (espaces, NBSP, tabs) → un seul espace
    - trim final

    Renvoie None si l'entrée est None. Conserve le texte original
    inchangé — la sortie sert UNIQUEMENT à la comparaison.
    """
    if text is None:
        return None
    # NFKD décompose les accents en (lettre + combining mark) ; on retire les Mn.
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = _PUNCT_TO_SPACE_RE.sub(" ", s)
    s = _WHITESPACE_RE.sub(" ", s)
    return s.strip()


# Code CIM-10 au format compact (sans point, ex `A000`, `B9688`).
# Conversion vers le format standard `<lettre><2 chiffres>.<reste>`.
# Cf `docs/source_mapping.md` §"Format des codes dans les sources externes".
_COMPACT_CODE_RE = re.compile(r"^([A-Z]\d{2})(\d{1,3})$")
# Code CIM-10 standard avec point optionnel.
_STANDARD_CODE_RE = re.compile(r"^[A-Z]\d{2}(?:\.\d{1,3})?$")
# Intervalle ouvert / racine signalée par un tiret final (ex `B65-`).
# Convention de l'Index CIM-10 vol3 pour les renvois racine.
_TRAILING_DASH_RE = re.compile(r"^([A-Z]\d{2}(?:\.\d{1,3})?)\.?-+$")


def normalize_compact_code(code: str | None) -> str | None:
    """Convertit un code CIM-10 au format compact des sources externes
    HECTOR vers le format standard avec point.

    - `A000` → `A00.0`, `B9688` → `B96.88`
    - `A00` → `A00` (déjà au format standard)
    - `A00.0` → `A00.0` (idem)
    - `B65-`, `R89-` → `B65`, `R89` (intervalle ouvert, on retire le
      tiret final pour valider ensuite contre OFS/ANS — cf
      source_mapping.md §"Codes orphelins externes")
    - `nocode`, `""`, `None`, `I200+0` et toute forme exotique → `None`

    Renvoie `None` pour signaler "code non parseable, à filtrer". Les
    appelants logguent typiquement les cas `None` pour audit.
    """
    if code is None:
        return None
    s = str(code).strip().upper()
    if not s or s == "NOCODE":
        return None
    # Forme standard déjà valide.
    if _STANDARD_CODE_RE.match(s):
        return s
    # Forme compacte (insertion du point).
    m = _COMPACT_CODE_RE.match(s)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    # Intervalle ouvert avec tiret final.
    m = _TRAILING_DASH_RE.match(s)
    if m:
        return m.group(1)
    return None


def normalize_column(col_name: str) -> pl.Expr:
    """Wrapper polars pour appliquer `normalize_for_match` sur une colonne string.

    Utilise `map_elements` (Python UDF) — polars n'a pas de natif strip-accents.
    Acceptable sur ~20k lignes (≪ 1 s).
    """
    return pl.col(col_name).map_elements(normalize_for_match, return_dtype=pl.String)
