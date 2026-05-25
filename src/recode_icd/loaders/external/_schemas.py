"""Schéma pandera commun aux trois loaders des sources externes.

Les loaders émettent un DataFrame uniforme à 5 colonnes ; le champ
`metadata` est un `pl.Struct` polars dont les sous-champs varient
par source (cf docstring de chaque loader pour le détail). Pandera
valide la présence de la colonne mais pas la granularité des
sous-champs Struct — limitation pandera-polars 0.21 — ce qui reste
acceptable car les loaders sont responsables de produire des
metadata cohérents.
"""

from __future__ import annotations

import pandera.polars as pa

from recode_icd.loaders.external._constants import (
    EXTERNAL_CODE_PATTERN,
    EXTERNAL_NOTE_TYPES,
    EXTERNAL_SOURCES,
)


class ExternalSourceSchema(pa.DataFrameModel):
    """Schéma uniforme retourné par `load_orphanet`,
    `load_index_cim10` et `load_aphp_hector`."""

    code: str = pa.Field(str_matches=EXTERNAL_CODE_PATTERN)
    libelle: str = pa.Field(str_matches=r"\S")  # non vide après strip
    type: str = pa.Field(isin=sorted(EXTERNAL_NOTE_TYPES))
    source: str = pa.Field(isin=sorted(EXTERNAL_SOURCES))
    # metadata : pl.Struct, sous-champs spécifiques par source. La
    # validation pandera ne porte que sur la présence ici.

    class Config:
        strict = False  # tolère la colonne metadata Struct
        coerce = False
