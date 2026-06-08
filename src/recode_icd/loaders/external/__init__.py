"""Loaders pour les sources externes de synonymes/inclusions :
ORPHANET, Index CIM-10 vol3, thésaurus métiers AP-HP.

Tous les loaders émettent un DataFrame uniforme à 5 colonnes
`(code, libelle, type, source, metadata)`, validé par
`ExternalSourceSchema`. Le champ `metadata` est un `pl.Struct` dont
les sous-champs varient par source.

Cf `docs/source_mapping.md` §"Sources externes : politique
d'intégration".
"""

from __future__ import annotations

from recode_icd.loaders.external.aphp_hector import load_aphp_hector
from recode_icd.loaders.external.cepidc import load_cepidc
from recode_icd.loaders.external.index_cim10 import load_index_cim10
from recode_icd.loaders.external.orphanet import load_orphanet

__all__ = ["load_aphp_hector", "load_cepidc", "load_index_cim10", "load_orphanet"]
