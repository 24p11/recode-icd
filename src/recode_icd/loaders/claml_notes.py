"""Loader des rubriques de type note du ClaML ANS.

Le RDF ANS ne porte pas les notes : elles vivent dans le ClaML
(`cim10frfm2025syst_claml_20241216.xml`), sous six kinds — coding-hint,
definition, note, text, introduction, footnote — portés par les `Class`
(chapitres en romain, blocs en plage nue, catégories) et, factorisés,
par les `Modifier`/`ModifierClass` (définitions des 4ᵉ/5ᵉ caractères,
F10-F19 en tête).

Extraction du texte : les `<Reference>` incrustés sans espaces sont
restitués avec leurs espaces, et parenthésés quand
`class="in brackets"` — sans quoi « supplémentaire<Reference>U82-U84
</Reference>pour » perdrait ses séparations.

Périmètre du chantier notes OFS/ANS (phase 1, tri validé RF
2026-09-14) : 955 rubriques, dont 78 sous Modifier/ModifierClass.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import polars as pl

#: Kinds ClaML retenus comme « notes » (le tri par classe et le verdict
#: de rendu vivent dans `referentials/curation/notes_cim_curated.csv`).
NOTE_KINDS = ("coding-hint", "definition", "note", "text", "introduction", "footnote")

_KIND_NOEUD = {"chapter": "chapitre", "block": "bloc", "category": "categorie"}


def _texte_rubrique(rub: ET.Element) -> str:
    """Texte FR d'une rubrique, References restituées avec leurs espaces."""
    label = rub.find("Label")
    if label is None:
        return ""
    morceaux: list[str] = []

    def _marche(el: ET.Element) -> None:
        if el.text:
            morceaux.append(el.text)
        for enfant in el:
            if enfant.tag == "Reference":
                interieur = "".join(enfant.itertext())
                if enfant.get("class") == "in brackets":
                    morceaux.append(f" ({interieur}) ")
                else:
                    morceaux.append(f" {interieur} ")
            else:
                _marche(enfant)
            if enfant.tail:
                morceaux.append(enfant.tail)

    _marche(label)
    texte = re.sub(r"\s+", " ", "".join(morceaux)).strip()
    texte = re.sub(r"\( ", "(", texte)
    texte = re.sub(r" \)", ")", texte)
    return re.sub(r" ([.,;:])", r"\1", texte)


def load_claml_notes(claml_path: Path) -> pl.DataFrame:
    """Toutes les rubriques de type note du ClaML, une ligne par rubrique.

    Colonnes :

    - `code` : code porteur (`I64`, `B90-B94`, `X` pour un chapitre) ;
      pour une rubrique de modificateur, le code technique
      (`S05F10_4.0`) — les codes concrets sont dans `concrets` ;
    - `noeud` : chapitre | bloc | categorie | modificateur ;
    - `kind` : le kind ClaML ;
    - `rubric_id` : l'attribut `id` de la rubrique (traçabilité) ;
    - `concrets` : codes concrets couverts par une subdivision de
      modificateur (`F10.3, F11.3, …`), liste vide sinon.
    """
    root = ET.parse(claml_path).getroot()
    modifie_par: dict[str, list[str]] = defaultdict(list)
    for cl in root.iter("Class"):
        for mb in cl.findall("ModifiedBy"):
            modifie_par[str(mb.get("code"))].append(str(cl.get("code")))

    lignes: list[dict[str, object]] = []
    for cl in root.iter("Class"):
        code = str(cl.get("code"))
        noeud = _KIND_NOEUD.get(str(cl.get("kind")), str(cl.get("kind")))
        for rub in cl.findall("Rubric"):
            kind = str(rub.get("kind"))
            if kind in NOTE_KINDS:
                lignes.append(
                    {
                        "code": code,
                        "noeud": noeud,
                        "kind": kind,
                        "rubric_id": str(rub.get("id") or ""),
                        "texte": _texte_rubrique(rub),
                        "concrets": [],
                    }
                )
    for mod in root.iter("Modifier"):
        nom = str(mod.get("code"))
        # Une rubrique de niveau Modifier (« Les subdivisions suivantes
        # peuvent être utilisées… ») vise les classes que le modificateur
        # modifie — ses cibles sont ces codes, pas une subdivision.
        cibles_mod = list(modifie_par.get(nom, []))
        for rub in mod.findall("Rubric"):
            if str(rub.get("kind")) in NOTE_KINDS:
                lignes.append(
                    {
                        "code": f"MOD {nom}",
                        "noeud": "modificateur",
                        "kind": str(rub.get("kind")),
                        "rubric_id": str(rub.get("id") or ""),
                        "texte": _texte_rubrique(rub),
                        "concrets": cibles_mod,
                    }
                )
    for mc in root.iter("ModifierClass"):
        nom, sub = str(mc.get("modifier")), str(mc.get("code"))
        cibles = [c for c in modifie_par.get(nom, []) if "-" not in c]
        for rub in mc.findall("Rubric"):
            if str(rub.get("kind")) in NOTE_KINDS:
                lignes.append(
                    {
                        "code": f"{nom}{sub}",
                        "noeud": "modificateur",
                        "kind": str(rub.get("kind")),
                        "rubric_id": str(rub.get("id") or ""),
                        "texte": _texte_rubrique(rub),
                        "concrets": [f"{c}{sub}" for c in cibles],
                    }
                )
    return pl.DataFrame(
        lignes,
        schema={
            "code": pl.String,
            "noeud": pl.String,
            "kind": pl.String,
            "rubric_id": pl.String,
            "texte": pl.String,
            "concrets": pl.List(pl.String),
        },
    )


__all__ = ("NOTE_KINDS", "load_claml_notes")
