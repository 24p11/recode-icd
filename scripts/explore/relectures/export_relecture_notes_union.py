"""Export CSV de tri — UNION des notes OFS 2006 ⊕ ClaML ANS 2025 (v3).

Phase 1 du chantier « notes OFS/ANS ». Le v2 a été SUSPENDU par la
relecture RF (message correctif du 2026-09-14) pour deux défauts,
corrigés ici :

**1. Alignement (fausses « abandonnées »).** Le v2 joignait par
(code × classe) : quand les deux côtés classaient différemment la même
note ((D00-D09) OFS « définition » vs ANS kind `note` → instruction),
elle ressortait OFS-seul « abandonnée » à tort. Le v3 **joint par code
seul et rapproche la classe en second** (les classes divergentes sont
signalées au motif) ; puis, pour CHAQUE ligne OFS-seul restante, un
**contrôle plein texte** cherche un fragment distinctif dans tout le
ClaML (colonne `controle_plein_texte` : absent | trouvé_sur=<code>) —
une note trouvée ailleurs bascule en `les_deux` avec divergence.

**2. Critère (conventions opérantes).** `convention_classement →
non_rendue` en bloc était trop grossier : la leçon ANT-01 vise les
descentes NON BORNÉES sans contenu spécifique, pas les notes de bloc à
périmètre borné. Nouveau critère sur toute la famille (source E,
conventions ANS, kind `text`) — on juge le CONTENU, pas l'étiquette
(colonne `caractere`) :

- **opérante** — enseigne quelque chose de l'emploi des codes
  (définition, équivalence terminologique, règle de priorité, extension
  ou restriction de périmètre, règle de résolution) → rendue, classe
  reproposée (souvent définition ou instruction) ; note de bloc →
  fiche de bloc + héritage borné vers les feuilles ; note de chapitre →
  descente à trancher ligne à ligne ;
- **présentationnelle** — renvoi de mise en page, organisation du
  volume 1 → non_rendue.

**Dorés (verdicts RF du 2026-09-14, intégrés).** (D00-D09) et
(D37-D48) : description_clinique, texte ANS, fiche de bloc (héritage à
instruire en phase 2 — cas D06/NIC). Rendues : (I20-I25) laps de temps
de l'infarctus, (J00-J99) localisation la plus basse, (K40-K46)
hernie gangrène > occlusion, (L20-L30) dermite = eczéma, (M15-M19)
ostéo-arthrite = arthrose, (O20-O29) O24/O25 pendant l'accouchement.

**Cadrage (consigné au CLAUDE.md)** : les fiches servent TROIS
usages — génération de texte, vérification d'un codage, entraînement à
la reconnaissance des codes. Toute note opérante sert au moins l'un
des trois ; « aide le rédacteur seul » ne gouverne jamais une
exclusion par famille.

Reconnaissance v2 (inchangée) : 955 rubriques ClaML de type note, dont
78 factorisées sous `Modifier`/`ModifierClass` ; References restituées
avec leurs espaces, parenthésées quand `class="in brackets"`.

Usage
-----
    uv run python scripts/explore/relectures/export_relecture_notes_union.py
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
CSV_V2 = SORTIE / "relecture_notes_union_v2.csv"

VERSION_REGLE = "v3"

NOTE_KINDS = ("coding-hint", "definition", "note", "text", "introduction", "footnote")

DEST_DESCRIPTION = "section Description clinique (OMS)"
DEST_DEFINITION = "fiche du code (définition)"
DEST_INSTRUCTION = "section Notes de la CIM-10"
DEST_BLOC = "fiche de bloc (bibliothèque catégories) + héritage borné vers les feuilles"
DEST_CHAPITRE = "à trancher ligne à ligne : descente chapitre → feuilles"
NON_RENDUE = "non_rendue"

#: Dorés RF 2026-09-14 : blocs D à rendre en description clinique
#: (texte ANS retenu, héritage bloc → feuilles à instruire en phase 2).
DORES_BLOCS_DESCRIPTION = ("D00-D09", "D37-D48")
#: Dorés RF 2026-09-14 : conventions OPÉRANTES, rendues.
DORES_RENDUE = ("I20-I25", "J00-J99", "K40-K46", "L20-L30", "M15-M19", "O20-O29")
MOTIF_DORE = "verdict RF 2026-09-14 (doré)"


def _plie(texte: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texte.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


#: Mêmes patrons que le v1/v2 (verdicts en bloc), appliqués aux deux côtés.
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

#: Présentationnel pur : renvois de mise en page, organisation du
#: volume, historique éditorial. Tout le RESTE de la famille des
#: conventions est proposé OPÉRANT (critère RF 2026-09-14 : on juge le
#: contenu, pas l'étiquette).
RE_PRESENTATIONNELLE = re.compile(
    r"^\[?voir (?:le debut de ce chapitre|subdivisions)"
    r"|^se reporter a la table des medicaments"
    r"|^en mai 1980|^ce chapitre a ete partiellement etendu"
    r"|^pour l'utilisation de cette categorie, se referer aux regles"
)

#: Une convention opérante qui DÉFINIT (équivalence terminologique,
#: périmètre) plutôt qu'elle ne prescrit → classe definition.
RE_DEFINITIONNEL = re.compile(
    r"designe|comprend|s'applique|au sens de|est (?:considere|synonyme)|"
    r"terme|equivalent|laps de temps|toute mention"
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
        return "", "convention_classement", NON_RENDUE, "kind text ANS — au critère opérant"
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


def _fragment_distinctif(texte: str) -> str:
    """Fragment médian normalisé pour le contrôle plein texte."""
    norme = normalize_for_match(texte) or ""
    if len(norme) <= 60:
        return norme
    debut = (len(norme) - 60) // 2
    return norme[debut : debut + 60]


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

    ans_brutes: list[dict[str, object]] = []
    for cl in root.iter("Class"):
        code = str(cl.get("code"))
        noeud = kind_noeud.get(str(cl.get("kind")), str(cl.get("kind")))
        for rub in cl.findall("Rubric"):
            kind = str(rub.get("kind"))
            if kind in NOTE_KINDS:
                ans_brutes.append(
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
                ans_brutes.append(
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
                ans_brutes.append(
                    {
                        "code": f"{nom}{sub}",
                        "noeud": "modificateur",
                        "kind": kind,
                        "texte": _texte_rubrique(rub),
                        "attache": f"modificateur {nom} {sub} → {', '.join(concrets[:4])}…",
                        "concrets": concrets,
                    }
                )

    def _cle(code: str) -> str:
        """Normalise AVANT jointure : plage parenthésée OFS ↔ plage nue ANS."""
        return code.strip("()")

    # ---- côté OFS : notes par CODE SEUL (correction v3) ------------------
    ofs_par_code: dict[str, list[dict]] = defaultdict(list)
    for r in ofs.iter_rows(named=True):
        d = dict(r)
        d["_consomme"] = False
        ofs_par_code[_cle(str(r["code"]))].append(d)

    def _peremption(code_nu: str, texte: str, est_plage: bool) -> tuple[bool, str]:
        motifs: list[str] = []
        est_modificateur = code_nu.startswith("MOD") or bool(re.match(r"^S\d\d", code_nu))
        if not est_plage and code_nu and not est_modificateur:
            if code_nu not in codes_2026:
                motifs.append("code absent du référentiel 2026")
            elif statuts.get(code_nu) in ("supprime", "inconnu_atih"):
                motifs.append(f"statut MCO 2026 : {statuts.get(code_nu)}")
        sans_plages = re.sub(
            r"[A-Z]\d{2}(?:\.\d{1,2})?\s*[–-]\s*[A-Z]\d{2}(?:\.\d{1,2})?", " ", texte
        )
        caducs = sorted(
            {c for c in RE_CODE_CITE.findall(sans_plages) if c != code_nu and c not in codes_2026}
        )
        if caducs:
            motifs.append("renvoi caduc : " + ", ".join(caducs[:4]))
        return bool(motifs), " ; ".join(motifs)

    def _critere_operant(
        classe: str, dest: str, motif: str, plie: str, noeud: str, code_nu: str
    ) -> tuple[str, str, str, str]:
        """(caractere, classe, dest, motif) — critère RF sur les conventions."""
        if classe != "convention_classement":
            return "", classe, dest, motif
        if code_nu not in DORES_RENDUE and RE_PRESENTATIONNELLE.search(plie):
            return (
                "presentationnelle",
                classe,
                NON_RENDUE,
                motif + " ; présentationnelle — mise en page/organisation du volume",
            )
        classe = "definition" if RE_DEFINITIONNEL.search(plie) else "instruction_codage"
        if noeud == "chapitre":
            dest = DEST_CHAPITRE
        elif noeud in ("bloc", "modificateur") or "-" in code_nu:
            dest = DEST_BLOC
        else:
            dest = DEST_DEFINITION if classe == "definition" else DEST_INSTRUCTION
        motif += " ; opérante (enseigne l'emploi des codes) — reclassée depuis convention"
        if code_nu in DORES_RENDUE:
            motif += f" ; {MOTIF_DORE} : rendue"
        return "operante", classe, dest, motif

    lignes: list[dict[str, object]] = []
    couverture_par_classe: dict[tuple[str, str], str] = {}

    # ---- 1) rubriques ANS : jointure par code, classe rapprochée --------
    for ligne_ans in ans_brutes:
        code, texte, kind = str(ligne_ans["code"]), str(ligne_ans["texte"]), str(ligne_ans["kind"])
        code_nu = _cle(code)
        plie = _plie(texte)
        concrets = [str(c) for c in (ligne_ans.get("concrets") or [])]
        code_pour_classe = concrets[0] if concrets else code
        patron, classe, dest, motif = _classe_ans(kind, code_pour_classe, plie)
        noeud = str(ligne_ans["noeud"])
        est_plage = ("-" in code and not code.startswith("MOD")) or noeud in (
            "chapitre",
            "modificateur",
        )

        # Rapprochement v3 : d'abord la même classe, sinon TOUTE note OFS
        # restante du même code (classes divergentes signalées au motif).
        groupe = [g for g in ofs_par_code.get(code_nu, []) if not g["_consomme"]]
        meme_classe = [g for g in groupe if str(g["classe_proposee"]) == classe]
        apparie = meme_classe or groupe
        provenance = "ANS_2025"
        divergence, texte_ofs, source_ofs = False, "", ""
        if apparie:
            provenance = "les_deux"
            for g in apparie:
                g["_consomme"] = True
            source_ofs = "/".join(sorted({str(g["source"]) for g in apparie}))
            cles_ofs = {normalize_for_match(str(g["texte"])) for g in apparie}
            if normalize_for_match(texte) not in cles_ofs:
                divergence = True
                texte_ofs = " ⧉ ".join(str(g["texte"]) for g in apparie[:2])
            if not meme_classe:
                classes_ofs = "/".join(sorted({str(g["classe_proposee"]) for g in apparie}))
                motif += (
                    f" ; classes divergentes OFS({classes_ofs}) / ANS({classe}) — "
                    "rapprochées par code (v3)"
                )

        caractere, classe, dest, motif = _critere_operant(classe, dest, motif, plie, noeud, code_nu)
        # Hors famille conventions : la règle chapitre/bloc tient, avec
        # les destinations bornées du v3.
        if (
            caractere == ""
            and noeud in ("chapitre", "bloc", "modificateur")
            and dest not in (NON_RENDUE, DEST_BLOC, DEST_CHAPITRE)
        ):
            if patron:
                motif += " ; attachée à un chapitre/bloc — héritage vers les catégories à trancher"
            elif noeud == "modificateur":
                motif += " ; factorisée — se rend sur les codes concrets du modificateur"
            else:
                dest = DEST_BLOC if noeud == "bloc" else DEST_CHAPITRE
                motif += " ; note de bloc/chapitre — destination bornée (v3)"

        if code_nu in DORES_BLOCS_DESCRIPTION:
            classe, caractere = "description_clinique", ""
            dest = (
                "fiche de bloc (bibliothèque catégories) — héritage vers les feuilles "
                "à instruire en phase 2 (cas D06/NIC)"
            )
            motif = f"{MOTIF_DORE} : description clinique, texte ANS retenu"
        elif code_nu in DORES_RENDUE and MOTIF_DORE not in motif:
            # Dorés déjà classés instruction/définition par patron : la
            # mention du verdict reste traçable dans la passe RF.
            motif += f" ; {MOTIF_DORE} : rendue"

        for concret in concrets:
            couverture_par_classe[(concret, classe)] = str(ligne_ans["attache"])

        suspecte, motif_peremption = _peremption(code_nu, texte, est_plage)
        lignes.append(
            {
                "provenance": provenance,
                "code": code,
                "libelle_officiel": libelles.get(code_nu, ""),
                "chapitre": outils.hierarchie_de(code_nu.split("-")[0])[0] or "",
                "type_noeud": noeud,
                "source_ofs": source_ofs,
                "kind_ans": kind,
                "attache": str(ligne_ans["attache"]),
                "patron": patron,
                "caractere": caractere,
                "classe_proposee": classe,
                "destination_proposee": dest,
                "motif": motif,
                "texte_retenu": texte,
                "divergence_textuelle": divergence,
                "texte_ofs_si_divergent": texte_ofs,
                "abandonnee_par_ans_2025": False,
                "controle_plein_texte": "",
                "peremption_suspecte": suspecte,
                "peremption_motif": motif_peremption,
                "version_regle": VERSION_REGLE,
                "_norme": normalize_for_match(texte) or "",
            }
        )

    # ---- 2) contrôle plein texte des notes OFS restantes (v3) -----------
    basculees_plein_texte = 0
    restantes = [g for groupe in ofs_par_code.values() for g in groupe if not g["_consomme"]]
    for g in restantes:
        code_nu = _cle(str(g["code"]))
        texte = str(g["texte"])
        frag = _fragment_distinctif(texte)
        cible = None
        if frag:
            for ligne in lignes:
                if frag in str(ligne["_norme"]):
                    cible = ligne
                    break
        if cible is not None:
            # Trouvée ailleurs dans le ClaML : les_deux avec divergence.
            # Deux vrais cas rencontrés : bloc renommé (la note de
            # (B95-B97) vit sur B95-B98, bloc étendu en 2025) et
            # chapitre (OFS code la plage (J00-J99), ClaML le romain X).
            cible["provenance"] = "les_deux"
            cible["divergence_textuelle"] = True
            if texte not in str(cible["texte_ofs_si_divergent"]):
                sep = " ⧉ " if cible["texte_ofs_si_divergent"] else ""
                cible["texte_ofs_si_divergent"] = f"{cible['texte_ofs_si_divergent']}{sep}{texte}"
            cible["source_ofs"] = "/".join(
                sorted(set(filter(None, [str(cible["source_ofs"]), str(g["source"])])))
            )
            cible["controle_plein_texte"] = f"trouvé_sur={cible['code']} (note OFS {g['code']})"
            cible["motif"] = (
                str(cible["motif"])
                + f" ; note OFS de {g['code']} retrouvée ici par contrôle plein texte (v3)"
            )
            if code_nu in DORES_RENDUE:
                cible["motif"] = str(cible["motif"]) + f" ; {MOTIF_DORE} : rendue"
                if cible["destination_proposee"] == NON_RENDUE:
                    cible["caractere"] = "operante"
                    cible["destination_proposee"] = (
                        DEST_CHAPITRE if cible["type_noeud"] == "chapitre" else DEST_BLOC
                    )
            g["_consomme"] = True
            basculees_plein_texte += 1
            continue

        # Vraie OFS-seul : critère opérant appliqué aussi, contrôle tracé.
        plie = _plie(texte)
        noeud = str(g["type_noeud"])
        caractere, classe, dest, motif = _critere_operant(
            str(g["classe_proposee"]),
            str(g["destination_proposee"]),
            str(g["motif"]),
            plie,
            noeud,
            code_nu,
        )
        factorisee = couverture_par_classe.get((code_nu, classe), "")
        if factorisee:
            motif += f" ; factorisée côté ANS par {factorisee} — texte OFS par code plus riche"
        suspecte, motif_peremption = _peremption(code_nu, texte, str(g["code"]).startswith("("))
        lignes.append(
            {
                "provenance": "OFS_2006",
                "code": str(g["code"]),
                "libelle_officiel": str(g["libelle_officiel"] or ""),
                "chapitre": str(g["chapitre"] or ""),
                "type_noeud": noeud,
                "source_ofs": str(g["source"]),
                "kind_ans": "",
                "attache": str(g["table_attache"]),
                "patron": str(g["patron"] or ""),
                "caractere": caractere,
                "classe_proposee": classe,
                "destination_proposee": dest,
                "motif": motif,
                "texte_retenu": texte,
                "divergence_textuelle": False,
                "texte_ofs_si_divergent": "",
                "abandonnee_par_ans_2025": not factorisee,
                "controle_plein_texte": "absent",
                "peremption_suspecte": suspecte,
                "peremption_motif": motif_peremption,
                "version_regle": VERSION_REGLE,
                "_norme": "",
            }
        )

    for ligne in lignes:
        del ligne["_norme"]

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
    print("\nCaractère (famille conventions) × destination :")
    print(
        union.filter(pl.col("caractere") != "")
        .group_by("caractere", "destination_proposee")
        .len()
        .sort("caractere")
    )

    # ---- comparaison avec les « abandonnées » du v2 ----------------------
    v3_abandonnees = {
        (str(r["code"]).strip("()"), normalize_for_match(str(r["texte_retenu"])) or "")
        for r in union.filter(pl.col("abandonnee_par_ans_2025")).iter_rows(named=True)
    }
    if CSV_V2.exists():
        v2 = pl.read_csv(CSV_V2)
        v2_abandonnees = {
            (str(r["code"]).strip("()"), normalize_for_match(str(r["texte_retenu"])) or "")
            for r in v2.filter(pl.col("abandonnee_par_ans_2025")).iter_rows(named=True)
        }
        fausses = v2_abandonnees - v3_abandonnees
        print(
            f"\nAbandonnées v2 : {len(v2_abandonnees)} ; v3 : {len(v3_abandonnees)} ; "
            f"fausses abandonnées du v2 corrigées : {len(fausses)}"
        )
    print(f"Basculées les_deux par contrôle plein texte : {basculees_plein_texte}")

    print("\nContrôles témoins RF (par code OU par motif — les basculées ont changé de code) :")
    for temoin in ("D00-D09", "D37-D48", "B95-B9", "I20-I25", "J00-J99", "L20-L30"):
        cible = union.filter(
            pl.col("code").str.contains(temoin, literal=True)
            | pl.col("motif").str.contains(temoin, literal=True)
        )
        for r in cible.iter_rows(named=True):
            print(
                f"  {r['code']} [{r['provenance']}] {r['classe_proposee']} → "
                f"{str(r['destination_proposee'])[:58]} aband={r['abandonnee_par_ans_2025']}"
            )
    print("Péremption suspecte :", union.filter(pl.col("peremption_suspecte")).height)


if __name__ == "__main__":
    main()
