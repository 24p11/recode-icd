"""Constantes partagées par les loaders des sources externes
(ORPHANET, Index CIM-10 vol3, AP-HP HECTOR).
"""

from __future__ import annotations

INDEX_CIM10_SHEET = "Cim Alphabétique"
INDEX_CIM10_SOURCE = "INDEX_CIM10_VOL3"
INDEX_CIM10_SHEET_LABEL = "B"

# Source CepiDc 2015 (dictionnaire de formulations cliniques extraites
# des certificats de décès, cf `loaders.external.cepidc`).
CEPIDC_SOURCE = "CEPIDC_2015"

# Mapping nom de feuille Excel → valeur d'enum `NoteSource`. La clé
# est le nom EXACT de la feuille telle qu'écrite dans le classeur
# HECTOR ; l'étiquette en colonne 2 du fichier peut diverger (cas
# Endocrinologie où la 2e colonne porte "ED1", pas "END1") — on ne s'y
# fie pas. Cf `docs/source_mapping.md` §"Schéma uniforme des feuilles
# HECTOR".
APHP_SHEET_TO_SOURCE: dict[str, str] = {
    "Dermatologie": "APHP_DERMATOLOGIE",
    "Endocrinologie": "APHP_ENDOCRINOLOGIE",
    "GRONES": "APHP_GRONES",
    "Troubles métaboliques": "APHP_METABOLISME",
    "Néphrologie": "APHP_NEPHROLOGIE",
    "Ophtalmo": "APHP_OPHTALMOLOGIE",
    "Rhumatologie": "APHP_RHUMATOLOGIE",
    "Germes": "APHP_GERMES",
    "SRLF": "APHP_SRLF",
}

# Sources externes valides pour validation pandera.
EXTERNAL_SOURCES: frozenset[str] = frozenset(
    {"ORPHANET", INDEX_CIM10_SOURCE, CEPIDC_SOURCE, *APHP_SHEET_TO_SOURCE.values()}
)

# Types de note valides côté sources externes.
EXTERNAL_NOTE_TYPES: frozenset[str] = frozenset({"synonyme", "inclusion"})

# Code CIM-10 standard avec point optionnel (utilisé pour la
# validation pandera des codes émis par les loaders externes).
EXTERNAL_CODE_PATTERN: str = r"^[A-Z]\d{2}(?:\.\d{1,3})?$"
