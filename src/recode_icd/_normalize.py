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


def normalize_column(col_name: str) -> pl.Expr:
    """Wrapper polars pour appliquer `normalize_for_match` sur une colonne string.

    Utilise `map_elements` (Python UDF) — polars n'a pas de natif strip-accents.
    Acceptable sur ~20k lignes (≪ 1 s).
    """
    return pl.col(col_name).map_elements(normalize_for_match, return_dtype=pl.String)
