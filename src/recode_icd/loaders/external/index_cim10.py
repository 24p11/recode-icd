"""Loader pour l'Index CIM-10 vol3 (feuille "Cim Alphabétique" du
classeur HECTOR).

Wrapper léger sur `aphp_hector._load_hector_sheet`. La feuille
partage strictement le schéma 4 colonnes des feuilles AP-HP (cf
`docs/source_mapping.md` §"Schéma uniforme des feuilles HECTOR")
mais elle représente l'Index alphabétique officiel CIM-10 vol3, pas
un thésaurus AP-HP — d'où un loader public dédié et une `NoteSource`
distincte (`INDEX_CIM10_VOL3`).
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from recode_icd.loaders.external._constants import (
    INDEX_CIM10_SHEET,
    INDEX_CIM10_SOURCE,
)
from recode_icd.loaders.external.aphp_hector import _load_hector_sheet


def load_index_cim10(xlsx_path: Path | str) -> pl.DataFrame:
    """Charge la feuille "Cim Alphabétique" du classeur HECTOR.

    Toutes les entrées sortent en `type=synonyme`, `source=INDEX_CIM10_VOL3`.
    Les codes au format compact (`A000`, `B9688`) sont convertis en
    format standard (`A00.0`, `B96.88`) ; les intervalles ouverts
    (`B65-`) sont normalisés au code racine (`B65`) ; les `nocode` et
    autres formes inattendues sont filtrées avec log info.

    Args :
        xlsx_path : chemin du fichier
            `Dictionnaire_Hector_MAJ062019.xlsx`.

    Returns :
        DataFrame `(code, libelle, type, source, metadata)` validé.
        `metadata` est un Struct `{sheet_name="Cim Alphabétique",
        sheet_label="B"}`.
    """
    return _load_hector_sheet(
        Path(xlsx_path),
        sheet_name=INDEX_CIM10_SHEET,
        source_label=INDEX_CIM10_SOURCE,
        note_type="synonyme",
    )
