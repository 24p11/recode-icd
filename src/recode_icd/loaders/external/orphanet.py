"""Loader pour le mapping ORPHANET → CIM-10 (XML officiel 2025).

Le XML expose pour chaque maladie rare (`Disorder`) zéro ou plusieurs
`ExternalReference` vers des classifications externes. On filtre sur
`Source = "ICD-10"` et on lit la propriété
`DisorderMappingRelation/Name` pour déterminer la nature de la
relation :

| Sigle | Politique recode-icd |
|-------|----------------------|
| `E`   | émission `type=synonyme` (ORPHA = CIM-10)              |
| `NTBT`| émission `type=inclusion` (ORPHA ⊂ CIM-10)             |
| `BTNT`, `ND`, autres | ignorés (avec log au cas où)          |

**Piège** : ne PAS lire `DisorderMappingICDRelation/Name` qui porte
"Code attribué / Code spécifique / Terme d'inclusion / Terme index"
— c'est un axe orthogonal sans rapport avec E/NTBT. Cf
`docs/source_mapping.md` §"Sémantique de la relation ORPHANET →
CIM-10".

Pour chaque Disorder retenu, on émet une ligne pour le `Name` du
disorder, puis une ligne par `SynonymList/Synonym`.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

import polars as pl

from recode_icd._normalize import _STANDARD_CODE_RE
from recode_icd.loaders.external._schemas import ExternalSourceSchema

log = logging.getLogger(__name__)

ORPHANET_SOURCE = "ORPHANET"

# Politique d'émission par sigle de relation (cf source_mapping.md
# §"Sémantique de la relation ORPHANET → CIM-10").
_RELATION_TO_TYPE: dict[str, str] = {
    "E": "synonyme",
    "NTBT": "inclusion",
}


def _extract_sigle(name_text: str | None) -> str:
    """Extrait le sigle (1er mot) d'un libellé du type
    'NTBT (Le code ORPHA est plus restreint...)'."""
    if not name_text:
        return ""
    return name_text.strip().split(" ", 1)[0]


def load_orphanet(
    xml_path: Path | str,
    *,
    xsd_path: Path | None = None,
) -> pl.DataFrame:
    """Charge le XML ORPHANET et émet un DataFrame uniforme.

    Args :
        xml_path : chemin du fichier
            `ORPHA_ICD10_mapping_fr_2025.xml`.
        xsd_path : chemin du XSD optionnel. Si fourni mais inexistant
            sur disque → warning. La validation XSD effective n'est
            PAS implémentée (stdlib xml.etree ne supporte pas XSD ;
            ajouter lxml en dépendance reste possible plus tard).

    Returns :
        DataFrame `(code, libelle, type, source, metadata)` validé.
        `metadata` est un Struct `{orpha_code: str, relation: str}`.

    Raises :
        FileNotFoundError : si `xml_path` n'existe pas.
    """
    xml_path = Path(xml_path)
    if not xml_path.is_file():
        raise FileNotFoundError(f"XML ORPHANET introuvable : {xml_path}")

    if xsd_path is not None:
        xsd_path = Path(xsd_path)
        if not xsd_path.is_file():
            log.warning("XSD ORPHANET fourni mais introuvable : %s — validation sautée.", xsd_path)
        # NB : validation XSD effective non implémentée (xml.etree
        # stdlib ne supporte pas xs:schema). Cf TODO Phase 2.

    tree = ET.parse(xml_path)
    root = tree.getroot()

    rows: list[dict[str, Any]] = []
    skipped_sigles: Counter[str] = Counter()
    skipped_unparseable: int = 0

    for disorder in root.findall(".//Disorder"):
        orpha_code = (disorder.findtext("OrphaCode") or "").strip()
        disorder_name = (disorder.findtext("Name") or "").strip()
        synonyms = [
            (s.text or "").strip()
            for s in disorder.findall("SynonymList/Synonym")
            if (s.text or "").strip()
        ]

        for ref in disorder.findall("ExternalReferenceList/ExternalReference"):
            source = (ref.findtext("Source") or "").strip()
            if source != "ICD-10":
                continue

            # Propriété correcte : DisorderMappingRelation (sans ICD).
            # Cf source_mapping.md — l'autre propriété porte un axe
            # orthogonal ("Code attribué / spécifique / ...").
            relation_name_el = ref.find("DisorderMappingRelation/Name")
            relation_text = relation_name_el.text if relation_name_el is not None else None
            sigle = _extract_sigle(relation_text)

            note_type = _RELATION_TO_TYPE.get(sigle)
            if note_type is None:
                skipped_sigles[sigle or "<empty>"] += 1
                continue

            code_raw = (ref.findtext("Reference") or "").strip().upper()
            if not _STANDARD_CODE_RE.match(code_raw):
                skipped_unparseable += 1
                continue

            metadata = {"orpha_code": orpha_code, "relation": sigle}

            # Ligne pour le `Name` du disorder.
            if disorder_name:
                rows.append(
                    {
                        "code": code_raw,
                        "libelle": disorder_name,
                        "type": note_type,
                        "source": ORPHANET_SOURCE,
                        "metadata": metadata,
                    }
                )
            # Une ligne par synonyme.
            for syn in synonyms:
                rows.append(
                    {
                        "code": code_raw,
                        "libelle": syn,
                        "type": note_type,
                        "source": ORPHANET_SOURCE,
                        "metadata": metadata,
                    }
                )

    if skipped_sigles:
        log.info(
            "ORPHANET : sigles relation ignorés (BTNT/ND/autres) : %s",
            dict(skipped_sigles),
        )
    if skipped_unparseable:
        log.info(
            "ORPHANET : %d codes ICD-10 non parseables ignorés",
            skipped_unparseable,
        )

    if not rows:
        # Construit un DataFrame vide au schéma attendu pour ne pas
        # casser les consommateurs.
        df = pl.DataFrame(
            schema={
                "code": pl.String,
                "libelle": pl.String,
                "type": pl.String,
                "source": pl.String,
                "metadata": pl.Struct({"orpha_code": pl.String, "relation": pl.String}),
            }
        )
    else:
        df = pl.DataFrame(rows)

    # Dédup tolérante (code, libellé brut, type) — on évite les
    # doublons exacts dus à des SynonymList/Synonym strictement
    # identiques au Name. La dédup tolérante avec normalisation
    # texte est reportée au merger (Phase 2).
    df = df.unique(subset=["code", "libelle", "type"], keep="first").sort(
        ["code", "type", "libelle"]
    )

    ExternalSourceSchema.validate(df)
    return df
