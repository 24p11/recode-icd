"""Export CSV de tri des notes OFS (MEMO) pour relecture RF.

Chantier « notes OFS » (2026-09-12), patron du registre des
formulations : les 614 textes de type « note » du modèle relationnel
OFS ne sont ni dans le CSV maître ni dans les fiches. Ce script produit
le support de tri : une ligne par note, avec classe et destination
PROPOSÉES — le verdict ligne à ligne (patrons en bloc) appartient à RF.

Ce que la reconnaissance a établi (2026-09-12)
----------------------------------------------
- `MEMO.txt` : 614 enregistrements, tous `valid=Yes`, chacun attaché à
  UN code par sa colonne `SID`. Sources : E 62 / N 204 / G 348.
  Niveaux : 1-2 (chapitres/blocs, codes en plage « (B90-B94) ») 43,
  3 (catégories) 155, 4-5 (sous-catégories, subdivisions) 416.
- `NOTE.txt` (262) et `GLOSSAIRE.txt` (347) sont de purs marqueurs de
  rattachement 1:1 (SID identique au SID du mémo, aucune multi-attache).
  **Cinq mémos ne sont dans aucune des deux** : les définitions
  A15.1/A15.2/A15.3/A16.1 et la définition G de E00 — le join actuel du
  loader (NOTE seul) perd donc GLOSSAIRE (347) ET ces cinq-là.
- `memo` vs `FR_OMS` : 7 divergences, 4 `memo` nuls (repli `FR_OMS`),
  3 `FR_OMS` nuls. Le texte retenu est `coalesce(memo, FR_OMS)`.
- Hors périmètre, au rapport : `DESCRLIB.txt` (lexique des types de
  source), `HTML.txt` (3 pages d'annexe RoboHELP : tableau des
  atteintes de la vision du chap. VII, listes des catégories astérisque
  des chap. XIV/XVI), `Exp_text.zip` (copie d'export des mêmes tables).

⚠ Les colonnes `classe_proposee` / `destination_proposee` sont des
PROPOSITIONS mécaniques (patrons lexicaux + source + niveau). Le
partage appartient à RF ; les patrons répétitifs sont regroupés
(colonne `patron`) pour être tranchés en bloc.

Usage
-----
    uv run python scripts/explore/relectures/export_relecture_notes_ofs.py
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path

import polars as pl
from xlsxwriter import Workbook

from recode_icd.cards import _eager, charge_politique
from recode_icd.loaders.ofs import _read
from recode_icd.utils.loaders_dev import load_exploration_context

SORTIE = Path(__file__).parent
OFS_DIR = Path(__file__).resolve().parents[3] / "data" / "CIM_OFS_SW_2006"

#: À incrémenter à chaque changement des heuristiques de proposition.
VERSION_REGLE = "v1"

TYPES_NOEUD = {
    "C": "chapitre",
    "G": "bloc",
    "K": "categorie",
    "S": "sous_categorie",
    "U": "subdivision",
}

#: Sections de fiche cibles proposées (phase 2, à confirmer par RF).
DEST_DESCRIPTION = "section Description clinique (OMS)"
DEST_DEFINITION = "fiche du code (définition)"
DEST_INSTRUCTION = "section Notes de la CIM-10"
NON_RENDUE = "non_rendue"


def _plie(texte: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texte.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


#: (nom de patron, regex sur texte plié, classe, destination, motif).
#: Testés dans l'ordre — le premier qui matche gagne.
PATRONS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "utiliser_code_supplementaire",
        r"^(?:utiliser,? au besoin,? un code|peut etre utilise, au besoin, comme code)",
        "instruction_codage",
        DEST_INSTRUCTION,
        "instruction transversale « code supplémentaire » — à trancher en bloc",
    ),
    (
        "toute_maladie_classee",
        r"^toute maladie classee en",
        "definition",
        DEST_DEFINITION,
        "définition de subdivision (confirmation bactériologique/histologique)",
    ),
    (
        "exclusion_conditionnelle",
        r"^cette exclusion est applicable",
        "instruction_codage",
        DEST_INSTRUCTION,
        "condition d'application d'une exclusion",
    ),
    (
        "categorie_pas_code_principal",
        r"^cette categorie n(?:e doit etre|'est) utilisee comme code pri",
        "instruction_codage",
        DEST_INSTRUCTION,
        "règle de position (jamais en codage principal)",
    ),
    (
        "categories_bloc_regle_emploi",
        r"^ces categories (?:ne )?doivent",
        "instruction_codage",
        DEST_INSTRUCTION,
        "règle d'emploi des catégories du bloc (B90-B94, B95-B97…)",
    ),
    (
        "avortement_incomplet",
        r"^avortement incomplet comprend",
        "definition",
        DEST_DEFINITION,
        "définition partagée de la subdivision « avortement incomplet »",
    ),
    (
        "historique_classification",
        r"^en mai 1980|^ce chapitre a ete partiellement etendu",
        "convention_classement",
        NON_RENDUE,
        "note historique/éditoriale de la classification",
    ),
)


def _proposition(source: str, code: str, niveau: int, plie: str) -> tuple[str, str, str, str]:
    """(patron, classe, destination, motif) proposés pour une note."""
    for nom, motif_re, classe, dest, motif in PATRONS:
        if re.search(motif_re, plie):
            return nom, classe, dest, motif
    if source == "G":
        chapitre_f = code.lstrip("(").startswith("F")
        if chapitre_f:
            return (
                "",
                "description_clinique",
                DEST_DESCRIPTION,
                ("glossaire du chapitre F — description clinique officielle du trouble"),
            )
        return "", "definition", DEST_DEFINITION, "définition somatique du glossaire OFS"
    if source == "E":
        return (
            "",
            "convention_classement",
            NON_RENDUE,
            ("convention de classement (source E) — bruit probable en fiche (leçon ANT-01)"),
        )
    return "", "definition", DEST_DEFINITION, "texte définitoire (défaut source N) — à confirmer"


RE_CODE_CITE = re.compile(r"\b([A-Z]\d{2}(?:\.\d{1,2})?)\b")


def main() -> None:
    memo = _read(OFS_DIR / "MEMO.txt", quote_char="'").filter(pl.col("valid") == "Yes")
    note = _read(OFS_DIR / "NOTE.txt")
    glos = _read(OFS_DIR / "GLOSSAIRE.txt")
    master = _read(OFS_DIR / "MASTER.txt")

    ctx = load_exploration_context()
    flat = _eager(ctx.flat)
    merged = _eager(ctx.merged)
    outils = charge_politique(merged)
    codes_2026 = set(merged["code"].to_list())
    statuts = dict(merged.select("code", "statut_mco").iter_rows())
    libelles: dict[str, str] = dict(merged.select("code", "label").drop_nulls().iter_rows())
    for c, lib in flat.select("code", "libelle").unique().iter_rows():
        if lib:
            libelles.setdefault(c, lib)

    mids_note = set(note["MID"].to_list())
    mids_glos = set(glos["MID"].to_list())

    df = memo.join(master.select("SID", "code", "level", "type"), on="SID", how="left")

    lignes: list[dict[str, object]] = []
    for r in df.iter_rows(named=True):
        code = str(r["code"])
        texte = r["memo"] or r["FR_OMS"] or ""
        niveau = int(r["level"])
        source = str(r["source"])
        plie = _plie(re.sub(r"\s+", " ", texte.strip()))
        patron, classe, dest, motif = _proposition(source, code, niveau, plie)

        # Chapitres et blocs (codes en plage — l'OFS imbrique des
        # sous-blocs jusqu'au niveau 3) : pas de fiche cible, et
        # l'héritage ne les descend pas. Un patron explicite garde sa
        # destination — c'est alors l'héritage bloc → catégories qui
        # est à trancher (cas B95-B97).
        est_plage = code.startswith("(")
        if (est_plage or niveau <= 2) and dest != NON_RENDUE:
            if patron:
                motif += " ; attachée à un chapitre/bloc — héritage vers les catégories à trancher"
            else:
                dest = NON_RENDUE
                motif += " ; niveau chapitre/bloc — pas de fiche cible, ne descend pas"

        # Péremption : contrôles mécaniques contre le maître 2026 + kit.
        # Une plage n'est jamais codable : le contrôle de statut ne
        # s'applique qu'aux codes réels.
        peremption: list[str] = []
        code_nu = code.strip("()")
        if not est_plage:
            if code_nu not in codes_2026:
                peremption.append("code absent du référentiel 2026")
            else:
                statut = statuts.get(code_nu)
                if statut in ("supprime", "inconnu_atih"):
                    peremption.append(f"statut MCO 2026 : {statut}")
        cites = [c for c in RE_CODE_CITE.findall(texte) if c != code_nu]
        caducs = sorted({c for c in cites if c not in codes_2026})
        if caducs:
            peremption.append("renvoi caduc : " + ", ".join(caducs[:4]))

        table_attache = (
            "NOTE" if r["MID"] in mids_note else "GLOSSAIRE" if r["MID"] in mids_glos else "aucune"
        )
        chapitre, _ = outils.hierarchie_de(code_nu.split("-")[0])
        lignes.append(
            {
                "mid": r["MID"],
                "code": code,
                "libelle_officiel": libelles.get(code_nu, ""),
                "chapitre": chapitre or "",
                "niveau": niveau,
                "type_noeud": TYPES_NOEUD.get(str(r["type"]), str(r["type"])),
                "source": source,
                "table_attache": table_attache,
                "texte": texte,
                "texte_divergent": bool(r["memo"] and r["FR_OMS"] and r["memo"] != r["FR_OMS"]),
                "patron": patron,
                "classe_proposee": classe,
                "destination_proposee": dest,
                "motif": motif,
                "peremption_suspecte": bool(peremption),
                "peremption_motif": " ; ".join(peremption),
                "version_regle": VERSION_REGLE,
            }
        )

    lignes.sort(key=lambda l0: (str(l0["classe_proposee"]), str(l0["patron"]), str(l0["code"])))
    tri = pl.DataFrame(lignes)
    chemin = SORTIE / f"relecture_notes_ofs_{VERSION_REGLE}.csv"
    tri.write_csv(chemin)

    volumetrie = (
        tri.group_by("classe_proposee", "niveau", "chapitre")
        .len()
        .sort("classe_proposee", "niveau", "chapitre")
    )
    chemin_xlsx = SORTIE / f"relecture_notes_ofs_{VERSION_REGLE}.xlsx"
    with Workbook(chemin_xlsx) as classeur:
        tri.write_excel(workbook=classeur, worksheet="notes", autofit=True, freeze_panes="A2")
        volumetrie.write_excel(
            workbook=classeur, worksheet="volumetrie", autofit=True, freeze_panes="A2"
        )

    print(f"{tri.height} notes → {chemin} + {chemin_xlsx}")
    print("\nPar classe proposée :")
    print(tri.group_by("classe_proposee", "destination_proposee").len().sort("classe_proposee"))
    print("\nPatrons (à trancher en bloc) :")
    for patron, n in Counter(str(l0["patron"]) for l0 in lignes if l0["patron"]).most_common():
        print(f"  {patron}: {n}")
    print("\nPéremption suspecte :", tri.filter(pl.col("peremption_suspecte")).height)
    with pl.Config(tbl_rows=40):
        print(
            tri.filter(pl.col("peremption_suspecte")).select("code", "source", "peremption_motif")
        )
    print("\nVolumétrie classe × niveau :")
    print(tri.group_by("classe_proposee", "niveau").len().sort("classe_proposee", "niveau"))


if __name__ == "__main__":
    main()
