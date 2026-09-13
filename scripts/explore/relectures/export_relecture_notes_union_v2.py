"""Export CSV de tri v2 — UNION des notes OFS 2006 ⊕ ClaML ANS 2025.

Extension de la phase 1 du chantier « notes OFS » (vérification RF du
2026-09-13) : le ClaML 2025 (`cim10frfm2025syst_claml_20241216.xml`)
porte 955 rubriques de type note, ignorées par le loader ANS —
coding-hint 356, definition 290 (glossaire F 236, glossaire Z 24),
text 190, note 114, introduction 4, footnote 1 ; dont 78 factorisées
sous `Modifier`/`ModifierClass` (les définitions des 4ᵉ/5ᵉ caractères,
F10-F19 en tête). Ni l'OFS ni l'ANS n'est un sur-ensemble : le v2
soumet L'UNION à un verdict en une seule passe.

Alignement OFS ↔ ANS
--------------------
Par **code × classe proposée** (équivalences : coding-hint ↔
instruction_codage ; definition ↔ description_clinique (chapitre F) ou
définition ; note/text classés par les mêmes patrons que le v1).

- groupe présent des deux côtés → UNE ligne par rubrique ANS,
  `provenance=les_deux`, `texte_retenu` = ANS (politique de fusion
  gravée : ANS prioritaire, OFS complément) ; `divergence_textuelle`
  signalée quand aucun texte OFS du groupe ne matche toléramment, avec
  le texte OFS dans `texte_ofs_si_divergent` ;
- rubrique ANS seule → `provenance=ANS_2025` ;
- note OFS sans groupe ANS mais dont le code est couvert par une
  `ModifierClass` de même classe (F13.3 ⊂ modificateur F10-F19 « .3 »)
  → ligne émise, `provenance=OFS_2006`, `abandonnee_par_ans_2025=False`,
  motif « factorisée par le modificateur ANS » — le texte OFS par code
  est plus riche que la factorisation, RF tranche ;
- note OFS sans aucun équivalent → `abandonnee_par_ans_2025=True`
  (choix éditorial ANS possible, distinct de la péremption — le
  verdict garder/écarter appartient à RF).

Extraction ClaML : les `<Reference>` incrustés sans espaces dans les
textes (« supplémentaire<Reference>U82-U84</Reference>pour ») sont
restitués avec leurs espaces, et parenthésés quand
`class="in brackets"`.

Usage
-----
    uv run python scripts/explore/relectures/export_relecture_notes_union_v2.py
"""

from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import polars as pl
from xlsxwriter import Workbook

from recode_icd._normalize import normalize_for_match
from recode_icd.cards import _eager, charge_politique
from recode_icd.utils.loaders_dev import load_exploration_context

SORTIE = Path(__file__).parent
RACINE = Path(__file__).resolve().parents[3]
CLAML = RACINE / "data/CIM_ANS_2026/dat/cim10frfm2025syst_claml_20241216.xml"
CSV_V1 = SORTIE / "relecture_notes_ofs_v1.csv"

VERSION_REGLE = "v2"

NOTE_KINDS = ("coding-hint", "definition", "note", "text", "introduction", "footnote")

DEST_DESCRIPTION = "section Description clinique (OMS)"
DEST_DEFINITION = "fiche du code (définition)"
DEST_INSTRUCTION = "section Notes de la CIM-10"
NON_RENDUE = "non_rendue"


def _plie(texte: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texte.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


#: Mêmes patrons que le v1 (verdicts en bloc), appliqués aux deux côtés.
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
        r"^cette categorie n(?:e doit|'est) .{0,40}(?:code|cause) principal",
        "instruction_codage",
        DEST_INSTRUCTION,
        "règle de position (jamais en codage principal)",
    ),
    (
        "categories_bloc_regle_emploi",
        r"^(?:ces|les) cat[ée]gories .{0,20}(?:ne )?doivent",
        "instruction_codage",
        DEST_INSTRUCTION,
        "règle d'emploi des catégories du bloc",
    ),
    (
        "renvoi_presentation",
        r"^\[?voir (?:le debut de ce chapitre|subdivisions)",
        "convention_classement",
        NON_RENDUE,
        "renvoi de présentation du volume 1 — sans contenu propre",
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


def _patron_pour(plie: str) -> tuple[str, str, str, str] | None:
    for nom, motif_re, classe, dest, motif in PATRONS:
        if re.search(motif_re, plie):
            return nom, classe, dest, motif
    return None


def _classe_ans(kind: str, code: str, plie: str) -> tuple[str, str, str, str]:
    """(patron, classe, destination, motif) pour une rubrique ANS."""
    par_patron = _patron_pour(plie)
    if par_patron:
        return par_patron
    if kind == "coding-hint":
        return "", "instruction_codage", DEST_INSTRUCTION, "coding-hint ClaML"
    if kind == "definition":
        if code.startswith("F"):
            return (
                "",
                "description_clinique",
                DEST_DESCRIPTION,
                "définition ClaML du chapitre F — description clinique officielle",
            )
        return "", "definition", DEST_DEFINITION, "définition ClaML (glossaires Z et somatique)"
    if kind == "note":
        return (
            "",
            "instruction_codage",
            DEST_INSTRUCTION,
            "règle d'emploi (kind note ANS) — à confirmer",
        )
    if kind == "text":
        return "", "convention_classement", NON_RENDUE, "kind text ANS (présentation) — à confirmer"
    return "", "convention_classement", NON_RENDUE, f"kind {kind} ANS — éditorial"


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


RE_CODE_CITE = re.compile(r"\b([A-Z]\d{2}(?:\.\d{1,2})?)\b")


def main() -> None:
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

    # ---- côté OFS : le v1 tel que produit --------------------------------
    ofs = pl.read_csv(CSV_V1)

    # ---- côté ANS : ClaML ------------------------------------------------
    root = ET.parse(CLAML).getroot()
    kind_noeud = {"chapter": "chapitre", "block": "bloc", "category": "categorie"}
    modifie_par: dict[str, list[str]] = defaultdict(list)
    for cl in root.iter("Class"):
        for mb in cl.findall("ModifiedBy"):
            modifie_par[str(mb.get("code"))].append(str(cl.get("code")))

    ans_lignes: list[dict[str, object]] = []
    for cl in root.iter("Class"):
        code = str(cl.get("code"))
        noeud = kind_noeud.get(str(cl.get("kind")), str(cl.get("kind")))
        for rub in cl.findall("Rubric"):
            kind = str(rub.get("kind"))
            if kind in NOTE_KINDS:
                ans_lignes.append(
                    {
                        "code": code,
                        "noeud": noeud,
                        "kind": kind,
                        "texte": _texte_rubrique(rub),
                        "attache": "Class",
                    }
                )
    for mod in root.iter("Modifier"):
        nom = str(mod.get("code"))
        cibles = [c for c in modifie_par.get(nom, []) if "-" not in c]
        for rub in mod.findall("Rubric"):
            if str(rub.get("kind")) in NOTE_KINDS:
                ans_lignes.append(
                    {
                        "code": f"MOD {nom}",
                        "noeud": "modificateur",
                        "kind": str(rub.get("kind")),
                        "texte": _texte_rubrique(rub),
                        "attache": f"modificateur {nom} ({', '.join(cibles[:3])}…)",
                    }
                )
    for mc in root.iter("ModifierClass"):
        nom, sub = str(mc.get("modifier")), str(mc.get("code"))
        cibles = [c for c in modifie_par.get(nom, []) if "-" not in c]
        concrets = [f"{c}{sub}" for c in cibles]
        for rub in mc.findall("Rubric"):
            kind = str(rub.get("kind"))
            if kind in NOTE_KINDS:
                ans_lignes.append(
                    {
                        "code": f"{nom}{sub}",
                        "noeud": "modificateur",
                        "kind": kind,
                        "texte": _texte_rubrique(rub),
                        "attache": f"modificateur {nom} {sub} → {', '.join(concrets[:4])}…",
                        "concrets": concrets,
                    }
                )

    # ---- classement et clés d'alignement --------------------------------
    def _cle(code: str) -> str:
        return code.strip("()")

    groupes_ofs: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in ofs.iter_rows(named=True):
        groupes_ofs[(_cle(str(r["code"])), str(r["classe_proposee"]))].append(dict(r))

    consommes: set[int] = set()  # index de groupes OFS alignés (id() des listes)
    lignes: list[dict[str, object]] = []

    def _peremption(code_nu: str, texte: str, est_plage: bool) -> tuple[bool, str]:
        motifs: list[str] = []
        est_modificateur = code_nu.startswith("MOD") or bool(re.match(r"^S\d\d", code_nu))
        if not est_plage and code_nu and not est_modificateur:
            if code_nu not in codes_2026:
                motifs.append("code absent du référentiel 2026")
            elif statuts.get(code_nu) in ("supprime", "inconnu_atih"):
                motifs.append(f"statut MCO 2026 : {statuts.get(code_nu)}")
        # Les plages citées (« U00-U49 ») ne sont pas deux codes : on les
        # retire avant de chercher les renvois individuels caducs.
        sans_plages = re.sub(
            r"[A-Z]\d{2}(?:\.\d{1,2})?\s*[–-]\s*[A-Z]\d{2}(?:\.\d{1,2})?", " ", texte
        )
        caducs = sorted(
            {c for c in RE_CODE_CITE.findall(sans_plages) if c != code_nu and c not in codes_2026}
        )
        if caducs:
            motifs.append("renvoi caduc : " + ", ".join(caducs[:4]))
        return bool(motifs), " ; ".join(motifs)

    # 1) rubriques ANS (Class, Modifier, ModifierClass)
    couverture_par_classe: dict[tuple[str, str], str] = {}
    for ligne_ans in ans_lignes:
        code, texte, kind = str(ligne_ans["code"]), str(ligne_ans["texte"]), str(ligne_ans["kind"])
        plie = _plie(texte)
        concrets = [str(c) for c in (ligne_ans.get("concrets") or [])]
        # Une rubrique de modificateur se classe d'après ses codes CIBLES
        # (F13.3 relève du chapitre F), pas d'après son code technique.
        code_pour_classe = concrets[0] if concrets else code
        patron, classe, dest, motif = _classe_ans(kind, code_pour_classe, plie)
        noeud = str(ligne_ans["noeud"])
        # Un chapitre ClaML (code romain) ou une plage n'est jamais codable :
        # le contrôle de statut ne s'applique qu'aux codes réels.
        est_plage = ("-" in code and not code.startswith("MOD")) or noeud in (
            "chapitre",
            "modificateur",
        )
        if noeud in ("chapitre", "bloc", "modificateur") and dest != NON_RENDUE:
            if patron:
                motif += " ; attachée à un chapitre/bloc — héritage vers les catégories à trancher"
            elif noeud == "modificateur":
                motif += " ; factorisée — se rend sur les codes concrets du modificateur"
            else:
                dest = NON_RENDUE
                motif += " ; niveau chapitre/bloc — pas de fiche cible, ne descend pas"
        for concret in concrets:
            couverture_par_classe[(concret, classe)] = str(ligne_ans["attache"])

        groupe = groupes_ofs.get((_cle(code), classe))
        provenance = "ANS_2025"
        divergence, texte_ofs = False, ""
        source_ofs = ""
        if groupe:
            consommes.add(id(groupe))
            provenance = "les_deux"
            source_ofs = "/".join(sorted({str(g["source"]) for g in groupe}))
            cles_ofs = {normalize_for_match(str(g["texte"])) for g in groupe}
            if normalize_for_match(texte) not in cles_ofs:
                divergence = True
                texte_ofs = " ⧉ ".join(str(g["texte"]) for g in groupe[:2])
        suspecte, motif_peremption = _peremption(_cle(code), texte, est_plage)
        lignes.append(
            {
                "provenance": provenance,
                "code": code,
                "libelle_officiel": libelles.get(_cle(code), ""),
                "chapitre": outils.hierarchie_de(_cle(code).split("-")[0])[0] or "",
                "type_noeud": noeud,
                "source_ofs": source_ofs,
                "kind_ans": kind,
                "attache": str(ligne_ans["attache"]),
                "patron": patron,
                "classe_proposee": classe,
                "destination_proposee": dest,
                "motif": motif,
                "texte_retenu": texte,
                "divergence_textuelle": divergence,
                "texte_ofs_si_divergent": texte_ofs,
                "abandonnee_par_ans_2025": False,
                "peremption_suspecte": suspecte,
                "peremption_motif": motif_peremption,
                "version_regle": VERSION_REGLE,
            }
        )

    # 2) notes OFS sans groupe ANS
    for (code_nu, classe), groupe in groupes_ofs.items():
        if id(groupe) in consommes:
            continue
        for g in groupe:
            factorisee = couverture_par_classe.get((code_nu, classe), "")
            texte = str(g["texte"])
            suspecte, motif_peremption = _peremption(code_nu, texte, str(g["code"]).startswith("("))
            motif = str(g["motif"])
            if factorisee:
                motif += f" ; factorisée côté ANS par {factorisee} — texte OFS par code plus riche"
            lignes.append(
                {
                    "provenance": "OFS_2006",
                    "code": str(g["code"]),
                    "libelle_officiel": str(g["libelle_officiel"] or ""),
                    "chapitre": str(g["chapitre"] or ""),
                    "type_noeud": str(g["type_noeud"]),
                    "source_ofs": str(g["source"]),
                    "kind_ans": "",
                    "attache": str(g["table_attache"]),
                    "patron": str(g["patron"] or ""),
                    "classe_proposee": classe,
                    "destination_proposee": str(g["destination_proposee"]),
                    "motif": motif,
                    "texte_retenu": texte,
                    "divergence_textuelle": False,
                    "texte_ofs_si_divergent": "",
                    "abandonnee_par_ans_2025": not factorisee,
                    "peremption_suspecte": suspecte,
                    "peremption_motif": motif_peremption,
                    "version_regle": VERSION_REGLE,
                }
            )

    lignes.sort(
        key=lambda l0: (
            str(l0["classe_proposee"]),
            str(l0["patron"]),
            str(l0["code"]),
            str(l0["provenance"]),
        )
    )
    union = pl.DataFrame(lignes)
    chemin = SORTIE / f"relecture_notes_union_{VERSION_REGLE}.csv"
    union.write_csv(chemin)
    volumetrie = (
        union.group_by("provenance", "classe_proposee").len().sort("provenance", "classe_proposee")
    )
    chemin_xlsx = SORTIE / f"relecture_notes_union_{VERSION_REGLE}.xlsx"
    with Workbook(chemin_xlsx) as classeur:
        union.write_excel(workbook=classeur, worksheet="notes", autofit=True, freeze_panes="A2")
        volumetrie.write_excel(
            workbook=classeur, worksheet="volumetrie", autofit=True, freeze_panes="A2"
        )

    print(f"{union.height} lignes d'union → {chemin} + {chemin_xlsx}")
    print("\nVolumétrie provenance × classe :")
    with pl.Config(tbl_rows=30):
        print(volumetrie)
    print("\nContrôles témoins RF :")
    for temoin in ("B90-B94", "B95-B97", "A15.1", "A09", "Z61.0"):
        sub = union.filter(pl.col("code").str.contains(temoin, literal=True))
        for r in sub.iter_rows(named=True):
            print(
                f"  {r['code']} [{r['provenance']}] {r['classe_proposee']} "
                f"div={r['divergence_textuelle']} aband={r['abandonnee_par_ans_2025']}"
            )
    print(
        "\nOFS-seul :",
        union.filter(pl.col("provenance") == "OFS_2006").height,
        "| dont abandonnées :",
        union.filter(pl.col("abandonnee_par_ans_2025")).height,
        "| dont factorisées modificateur :",
        union.filter(
            (pl.col("provenance") == "OFS_2006") & (~pl.col("abandonnee_par_ans_2025"))
        ).height,
    )
    print(
        "Divergences textuelles (les_deux) :", union.filter(pl.col("divergence_textuelle")).height
    )
    print("Péremption suspecte :", union.filter(pl.col("peremption_suspecte")).height)
    f_ofs_seul = union.filter(
        (pl.col("provenance") == "OFS_2006")
        & (pl.col("classe_proposee").is_in(["description_clinique", "definition"]))
        & (pl.col("code").str.starts_with("F"))
    ).height
    print("Définitions/descriptions F OFS-seul (attendu RF ≈ 78) :", f_ofs_seul)


if __name__ == "__main__":
    main()
