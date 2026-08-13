"""Dérivation du chapitre, des blocs et de la catégorie d'un code.

Nécessaire à la résolution de la politique par plage (`policy.regle_pour`),
qui a besoin du chapitre et de **tous** les blocs englobants.

Deux pièges, tous deux rencontrés en exploration :

1. **Les blocs ne sont pas à une position fixe du `path`.** La CIM-10 en
   imbrique jusqu'à trois niveaux — `C50.8` vit sous
   `II/C00-C97/C00-C75/C50-C50/C50/C50.8`. Prendre `path[1]` donnerait
   `C00-C97` pour le chapitre II et `A00-A09` pour le chapitre I, deux
   niveaux sémantiquement différents. On retient donc **tous** les
   segments de forme « A00-B99 », et la résolution les teste du plus
   interne au plus large.
2. **La catégorie ne se lit pas dans le `path`.** Le segment d'indice 2
   vaut `C00-C75` pour `C50.8`, c'est-à-dire un bloc. `cards.py` définit
   une catégorie comme le code à 3 caractères (`_category_leaf_codes`) :
   on la dérive du code lui-même.
"""

from __future__ import annotations

import polars as pl

#: Un bloc CIM-10 : « A00-A09 », « C00-C97 », « V01-Y98 ».
BLOC_PATTERN = r"^[A-Z]\d{2}-[A-Z]?\d{2}$"


def chapitre_et_blocs(merged: pl.DataFrame) -> pl.DataFrame:
    """`(code, chapitre, blocs, categorie)` pour chaque code de `merged`.

    `blocs` est une liste ordonnée du plus large au plus étroit ; elle
    peut être vide (chapitres, blocs eux-mêmes).
    """
    return merged.select(
        pl.col("code"),
        pl.col("path").str.split("/").list.get(0, null_on_oob=True).alias("chapitre"),
        pl.col("path")
        .str.split("/")
        .list.eval(pl.element().filter(pl.element().str.contains(BLOC_PATTERN)))
        .alias("blocs"),
        pl.col("code").str.split(".").list.first().alias("categorie"),
    )


def annote(df: pl.DataFrame, merged: pl.DataFrame) -> pl.DataFrame:
    """Joint `chapitre` / `blocs` / `categorie` à une table portant `code`."""
    return df.join(chapitre_et_blocs(merged), on="code", how="left")


__all__ = ("BLOC_PATTERN", "annote", "chapitre_et_blocs")
