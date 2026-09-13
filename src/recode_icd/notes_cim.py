"""Notes de la CIM-10 (OFS 2006 ⊕ ClaML ANS 2025) — assemblage.

Chantier « notes OFS/ANS », phase 2 (verdict RF 2026-09-14). La table
curée `referentials/curation/notes_cim_curated.csv` — issue du tri v3
validé ligne à ligne — est la **source de vérité des verdicts** :
1 003 notes, chacune avec sa classe (`classe_note`) et sa destination
de rendu. Les textes sont fusionnés selon la politique gravée : **ANS
prioritaire, OFS complément** (miroir de la politique d'existence).

Ce module :

1. charge la table curée et la **réancre** sur les deux loaders
   (`loaders.ofs.load_ofs_notes`, `loaders.claml_notes.load_claml_notes`) —
   toute note curée dont le texte n'existe plus dans sa source part au
   rapport `reports/notes_cim_ancrage.csv`, jamais au silence ;
2. résout les **cibles de rendu** : les rubriques de modificateur se
   déploient sur leurs codes concrets (`F10.3`…), les chapitres OFS en
   plage `(F00-F99)` se normalisent vers le chiffre romain du maître ;
3. écrit `referentials/processed/notes_cim.parquet` — la base sait
   TOUT (les non-rendues comprises) ; la fiche n'affiche que le
   verdict.

Jurisprudences (RF, 2026-09-14) :

- *boilerplate* : une instruction de pure permission OMS (« utiliser,
  au besoin, un code supplémentaire ») ne se rend pas ; une instruction
  substantielle se rend — le partage est par patron quand il est
  homogène, ligne à ligne sinon ;
- *niveau chapitre* : une note de chapitre ne descend JAMAIS sur les
  feuilles — elle vit sur la fiche de chapitre de la bibliothèque des
  catégories. Les notes de bloc héritent vers leurs feuilles quand le
  verdict le dit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl

from recode_icd._normalize import normalize_for_match
from recode_icd.loaders.claml_notes import load_claml_notes
from recode_icd.loaders.ofs import load_ofs_notes

_RACINE_DEPOT = Path(__file__).resolve().parents[2]
DEFAULT_CURATED_PATH = _RACINE_DEPOT / "referentials/curation/notes_cim_curated.csv"
DEFAULT_PARQUET_PATH = _RACINE_DEPOT / "referentials/processed/notes_cim.parquet"

CLASSES_NOTE = (
    "description_clinique",
    "definition",
    "instruction_codage",
    "convention_classement",
)

#: Destinations admises (verdict RF). Toute autre valeur dans la table
#: curée est une erreur bruyante.
DESTINATIONS = (
    "section Description clinique (OMS)",
    "fiche du code (définition)",
    "section Notes de la CIM-10",
    "fiche de bloc (bibliothèque catégories) + héritage borné vers les feuilles",
    "fiche de chapitre (bibliothèque catégories), sans descente",
    "non_rendue",
)

#: Destinations qui descendent vers les feuilles. Une note de CHAPITRE
#: ne descend jamais (jurisprudence) ; une note de bloc/modificateur
#: descend quand sa destination l'affiche.
_DESTINATIONS_HERITEES = (
    "fiche de bloc (bibliothèque catégories) + héritage borné vers les feuilles",
)


class NotesCimError(ValueError):
    """Incohérence de la table curée des notes."""


@dataclass(frozen=True)
class AssemblageNotes:
    """Le résultat : la table complète et le rapport d'ancrage."""

    notes: pl.DataFrame
    ancrage_manque: pl.DataFrame


def _normalise(texte: str) -> str:
    return normalize_for_match(texte) or ""


def assemble_notes(
    curated_path: Path | None = None,
    ofs_dir: Path | None = None,
    claml_path: Path | None = None,
) -> AssemblageNotes:
    """Assemble la table des notes depuis la curation et les deux sources.

    Colonnes de `notes` : celles de la table curée, plus

    - `cibles` : codes d'attache résolus (les concrets d'un
      modificateur ; le chiffre romain d'un chapitre ; le code lui-même
      sinon, plages de bloc nues) ;
    - `herite_aux_feuilles` : la destination commande une descente
      bornée (jamais pour un chapitre) ;
    - `note_provenance` : traçabilité source (`MEMO <mid>` /
      `ClaML <rubric_id> (<kind>)`) ;
    - `source_csv` : libellé de source pour le CSV maître (`CIM-10`
      pour l'OFS, `ANS` sinon — texte ANS prioritaire).
    """
    chemin = curated_path if curated_path is not None else DEFAULT_CURATED_PATH
    curated = pl.read_csv(chemin)

    classes = set(curated["classe_note"].unique().to_list())
    if not classes <= set(CLASSES_NOTE):
        raise NotesCimError(
            f"Classes inconnues dans la table curée : {sorted(classes - set(CLASSES_NOTE))}"
        )
    destinations = set(curated["destination"].unique().to_list())
    if not destinations <= set(DESTINATIONS):
        raise NotesCimError(
            f"Destinations inconnues dans la table curée : {sorted(destinations - set(DESTINATIONS))}"
        )

    merged = pl.read_parquet(_RACINE_DEPOT / "referentials/processed/merged_codes.parquet")
    chapitres = merged.filter(pl.col("type") == "chapter").select("code", "left", "right")
    positions = dict(merged.select("code", "left").iter_rows())

    def _chapitre_romain(code_plage: str) -> str:
        """`(F00-F99)` → `V` : le chapitre du maître qui contient la plage."""
        premier = code_plage.strip("()").split("-")[0]
        gauche = positions.get(premier)
        if gauche is None:
            return code_plage
        for r in chapitres.iter_rows(named=True):
            if r["left"] < gauche < r["right"]:
                return str(r["code"])
        return code_plage

    ofs_notes = (
        load_ofs_notes(ofs_dir)
        if ofs_dir is not None
        else load_ofs_notes(_RACINE_DEPOT / "data/CIM_OFS_SW_2006")
    )
    claml = (
        load_claml_notes(claml_path)
        if claml_path is not None
        else load_claml_notes(
            _RACINE_DEPOT / "data/CIM_ANS_2026/dat/cim10frfm2025syst_claml_20241216.xml"
        )
    )

    #: texte normalisé → (id de traçabilité, concrets) par source.
    ancres_ans: dict[str, tuple[str, list[str]]] = {}
    for r in claml.iter_rows(named=True):
        cle = _normalise(str(r["texte"]))
        if cle and cle not in ancres_ans:
            ancres_ans[cle] = (
                f"ClaML {r['rubric_id']} ({r['kind']})",
                list(r["concrets"] or []),
            )
    ancres_ofs: dict[str, str] = {}
    for r in ofs_notes.iter_rows(named=True):
        cle = _normalise(str(r["texte"]))
        if cle and cle not in ancres_ofs:
            ancres_ofs[cle] = f"MEMO {r['mid']} ({r['table_attache']})"

    lignes: list[dict[str, object]] = []
    manquantes: list[dict[str, object]] = []
    for r in curated.iter_rows(named=True):
        texte = str(r["texte_retenu"])
        cle = _normalise(texte)
        provenance = str(r["provenance"])
        ans = ancres_ans.get(cle)
        ofs = ancres_ofs.get(cle)
        if ans is not None:
            note_provenance, concrets = ans
            source_csv = "ANS"
        elif ofs is not None:
            note_provenance, concrets = ofs, []
            source_csv = "CIM-10"
        else:
            manquantes.append({"code": r["code"], "provenance": provenance, "texte": texte[:120]})
            continue

        code = str(r["code"])
        noeud = str(r["type_noeud"])
        destination = str(r["destination"])
        if noeud == "modificateur":
            cibles = concrets
        elif noeud == "chapitre":
            # Normalisation : l'ANS code ses chapitres en romain, l'OFS
            # en plage parenthésée — la fiche de chapitre est unique.
            code = code if not code.startswith("(") else _chapitre_romain(code)
            cibles = [code]
        else:
            cibles = [code.strip("()")]

        lignes.append(
            {
                "code": code.strip("()") if noeud != "chapitre" else code,
                "type_noeud": noeud,
                "chapitre": str(r["chapitre"] or ""),
                "classe_note": str(r["classe_note"]),
                "destination": destination,
                "texte": texte,
                "cibles": cibles,
                "herite_aux_feuilles": destination in _DESTINATIONS_HERITEES
                or (noeud == "modificateur" and destination != "non_rendue"),
                "note_provenance": note_provenance,
                "source_csv": source_csv,
                "provenance_union": provenance,
                "source_ofs": str(r["source_ofs"] or ""),
                "kind_ans": str(r["kind_ans"] or ""),
            }
        )

    notes = pl.DataFrame(lignes).sort("code", "classe_note", "texte")
    ancrage = pl.DataFrame(
        manquantes, schema={"code": pl.String, "provenance": pl.String, "texte": pl.String}
    )
    return AssemblageNotes(notes=notes, ancrage_manque=ancrage)


def build_notes_cim(
    curated_path: Path | None = None,
    parquet_path: Path | None = None,
    reports_dir: Path | None = None,
) -> tuple[Path, int, int]:
    """`build notes-cim` : parquet + rapport d'ancrage. → (chemin, n, n_manquantes)."""
    assemblage = assemble_notes(curated_path=curated_path)
    sortie = parquet_path if parquet_path is not None else DEFAULT_PARQUET_PATH
    sortie.parent.mkdir(parents=True, exist_ok=True)
    assemblage.notes.write_parquet(sortie)
    rapports = reports_dir if reports_dir is not None else _RACINE_DEPOT / "reports"
    rapports.mkdir(parents=True, exist_ok=True)
    assemblage.ancrage_manque.write_csv(rapports / "notes_cim_ancrage.csv")
    return sortie, assemblage.notes.height, assemblage.ancrage_manque.height


__all__ = (
    "CLASSES_NOTE",
    "DEFAULT_CURATED_PATH",
    "DEFAULT_PARQUET_PATH",
    "DESTINATIONS",
    "AssemblageNotes",
    "NotesCimError",
    "assemble_notes",
    "build_notes_cim",
)
