"""Inventaire des trois sources externes de synonymes à intégrer
à `inclusions_exclusions_synonymes.csv` :

1. ORPHANET (XML, mapping ORPHA ↔ CIM-10).
2. Index CIM-10 vol3 (feuille `Cim Alphabétique` du classeur AP-HP).
3. 9 feuilles AP-HP / thésaurus métiers (Dermato, Endocrino, ...).

Lecture seule. Aucun loader de production écrit. Le livrable
principal est `docs/external_sources_inventory.md` ; ce script
produit aussi des artefacts JSON dans
`scripts/explore/_inventory_artifacts/` pour réutilisation directe
depuis le markdown.

Lancement :
    uv run --with fastexcel python \
        scripts/explore/2026-05-25_external_sources_inventory.py
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

import polars as pl

from recode_icd._normalize import normalize_for_match
from recode_icd.utils.loaders_dev import load_exploration_context

ROOT = Path(__file__).resolve().parents[2]
ART_DIR = ROOT / "scripts" / "explore" / "_inventory_artifacts"
ART_DIR.mkdir(parents=True, exist_ok=True)

ORPHANET_XML = (
    ROOT
    / "data"
    / "Orphanet_Nomenclature_Pack_FR_2025"
    / "ORPHA_ICD10_mapping_fr_2025.xml"
)
APHP_XLSX = ROOT / "data" / "CIM_APHP_2019" / "Dictionnaire_Hector_MAJ062019.xlsx"

APHP_UTIL_SHEETS: dict[str, str] = {
    # nom de feuille Excel → label fonctionnel
    "Cim Alphabétique": "INDEX_CIM10_VOL3",
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

# code au format compact AP-HP : `A000`, `B9688`. Conversion vers
# format standard `A00.0`, `B96.88`.
_COMPACT_RE = re.compile(r"^([A-Z]\d{2})(\d{1,3})$")
_STANDARD_RE = re.compile(r"^[A-Z]\d{2}(\.\d{1,3})?$")


def normalize_icd_code(raw: str | None) -> str | None:
    """Convertit un code CIM-10 au format compact (`A000`) vers le
    format standard avec point (`A00.0`).

    Retourne None si la chaîne ne ressemble à aucun code attendu —
    le caller log la valeur brute pour audit.
    """
    if raw is None:
        return None
    s = str(raw).strip().upper()
    if not s or s.lower() == "nocode":
        return None
    if _STANDARD_RE.match(s):
        return s
    m = _COMPACT_RE.match(s)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    if re.match(r"^[A-Z]\d{2}$", s):
        return s
    return None  # forme inconnue


def write_json(name: str, payload: Any) -> None:
    path = ART_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → écrit {path.relative_to(ROOT)}")


# ----------------------------------------------------------------------
# Référentiels de validation
# ----------------------------------------------------------------------


def load_validation_sets() -> tuple[set[str], set[str]]:
    """Retourne (codes_ofs, codes_owl) — sets pour validation
    rapide des codes externes."""
    ctx = load_exploration_context()
    if "master" not in ctx.ofs:
        raise RuntimeError("Table OFS MASTER absente — pipeline non préparé ?")
    if ctx.ans is None:
        raise RuntimeError("Parquet OWL/ANS absent — pipeline non préparé ?")

    # MASTER OFS : seul le code "valide" compte. Le schéma porte
    # un champ valid (str). On garde toutes les variantes pour ne
    # pas exclure prématurément.
    master = ctx.ofs["master"]
    codes_ofs = set(master["code"].drop_nulls().to_list())

    owl = ctx.ans
    codes_owl = set(owl["code"].drop_nulls().to_list())

    print(f"OFS MASTER : {len(codes_ofs)} codes")
    print(f"OWL/ANS    : {len(codes_owl)} codes")
    return codes_ofs, codes_owl


def classify(code: str | None, codes_ofs: set[str], codes_owl: set[str]) -> str:
    """Renvoie 'ofs', 'owl_only', 'orphan' ou 'unparseable'."""
    if code is None:
        return "unparseable"
    if code in codes_ofs:
        return "ofs"
    if code in codes_owl:
        return "owl_only"
    return "orphan"


# ----------------------------------------------------------------------
# 1. ORPHANET
# ----------------------------------------------------------------------


def inventory_orphanet(codes_ofs: set[str], codes_owl: set[str]) -> dict[str, Any]:
    print("\n========== ORPHANET ==========")
    tree = ET.parse(ORPHANET_XML)
    root = tree.getroot()
    disorders = root.findall(".//Disorder")
    n_disorders = len(disorders)
    print(f"Disorders : {n_disorders}")

    # Pour chaque ExternalReference ICD-10, collecter :
    # (OrphaCode, Name, synonymes, code_icd_raw, code_icd_normalisé,
    #  mapping_relation_name, mapping_icd_relation_name).
    refs: list[dict[str, Any]] = []
    mapping_relation_counter: Counter[str] = Counter()
    mapping_icd_relation_counter: Counter[str] = Counter()
    other_sources_counter: Counter[str] = Counter()

    for d in disorders:
        orpha_code = (d.findtext("OrphaCode") or "").strip()
        name = (d.findtext("Name") or "").strip()
        synonyms = [
            (s.text or "").strip()
            for s in d.findall("SynonymList/Synonym")
            if (s.text or "").strip()
        ]
        for er in d.findall("ExternalReferenceList/ExternalReference"):
            source = (er.findtext("Source") or "").strip()
            if source != "ICD-10":
                other_sources_counter[source] += 1
                continue
            ref = (er.findtext("Reference") or "").strip()
            # `DisorderMappingRelation/Name@lang=fr` porte E/NTBT/BTNT/W/ND
            # ATTENTION : le snippet du notebook prep_data_icd_models.ipynb
            # lit `DisorderMappingICDRelation` qui ne porte pas le bon
            # signal (il porte "Code attribué" / "Code emprunté" / ...).
            rel = er.find("DisorderMappingRelation/Name")
            rel_name = (rel.text or "").strip() if rel is not None else ""
            icd_rel = er.find("DisorderMappingICDRelation/Name")
            icd_rel_name = (
                (icd_rel.text or "").strip() if icd_rel is not None else ""
            )
            # extraire le sigle (E, NTBT, etc.) en début de Name
            sigle = rel_name.split(" ")[0] if rel_name else ""
            mapping_relation_counter[sigle] += 1
            icd_rel_sigle = icd_rel_name.split(":")[0].split("(")[0].strip()
            mapping_icd_relation_counter[icd_rel_sigle] += 1

            refs.append(
                {
                    "orpha_code": orpha_code,
                    "name": name,
                    "synonyms": synonyms,
                    "icd_raw": ref,
                    "icd_normalized": normalize_icd_code(ref),
                    "mapping_relation": sigle,
                    "mapping_relation_full": rel_name,
                    "mapping_icd_relation": icd_rel_sigle,
                }
            )

    n_refs = len(refs)
    n_e = sum(1 for r in refs if r["mapping_relation"] == "E")
    print(f"ExternalReference ICD-10 : {n_refs}")
    print(f"Autres sources rencontrées : {dict(other_sources_counter)}")
    print(f"DisorderMappingRelation : {dict(mapping_relation_counter)}")
    print(f"DisorderMappingICDRelation : {dict(mapping_icd_relation_counter)}")

    # Pour les relations E uniquement, classification OFS/OWL.
    e_refs = [r for r in refs if r["mapping_relation"] == "E"]
    e_codes = [r["icd_normalized"] for r in e_refs]
    classification = Counter(classify(c, codes_ofs, codes_owl) for c in e_codes)
    distinct_codes = {c for c in e_codes if c is not None}
    print(f"\nRelation E : {n_e} entrées, {len(distinct_codes)} codes distincts")
    print(f"Classification codes E : {dict(classification)}")

    # Exemples : 10 premiers Disorder ayant une relation E avec
    # synonymes non vides.
    examples = []
    for r in e_refs:
        if len(examples) >= 10:
            break
        if not r["synonyms"]:
            continue
        examples.append(
            {
                "orpha": r["orpha_code"],
                "name": r["name"],
                "synonyms": r["synonyms"],
                "icd_raw": r["icd_raw"],
                "icd_norm": r["icd_normalized"],
                "icd_classification": classify(
                    r["icd_normalized"], codes_ofs, codes_owl
                ),
            }
        )

    payload = {
        "n_disorders": n_disorders,
        "n_icd10_refs": n_refs,
        "other_sources": dict(other_sources_counter),
        "mapping_relation_distribution": dict(mapping_relation_counter),
        "mapping_icd_relation_distribution": dict(mapping_icd_relation_counter),
        "relation_E": {
            "n_entries": n_e,
            "n_distinct_codes": len(distinct_codes),
            "classification": dict(classification),
            "examples": examples,
        },
    }
    write_json("orphanet", payload)
    return payload


# ----------------------------------------------------------------------
# 2 + 3 : AP-HP unifié (toutes les feuilles ont le même schéma 4 colonnes)
# ----------------------------------------------------------------------


def read_aphp_sheet(sheet_name: str) -> pl.DataFrame:
    df = pl.read_excel(APHP_XLSX, sheet_name=sheet_name)
    cols = df.columns
    # Convention observée : 4 colonnes, [libellé, source_tag, code_raw, info4].
    # Les noms sont des étiquettes issues de la 1re ligne du fichier,
    # pas des en-têtes utilisables. On renomme par position.
    rename = {cols[0]: "libelle", cols[1]: "source_tag",
              cols[2]: "code_raw", cols[3]: "info4"}
    return df.rename(rename)


def inventory_aphp_sheet(
    sheet_name: str,
    label: str,
    codes_ofs: set[str],
    codes_owl: set[str],
    n_examples: int,
) -> dict[str, Any]:
    print(f"\n----- '{sheet_name}' → {label} -----")
    df = read_aphp_sheet(sheet_name)
    n_raw = df.height
    print(f"Lignes brutes : {n_raw}")

    df = df.with_columns(
        pl.col("code_raw").map_elements(normalize_icd_code, return_dtype=pl.String).alias("code_norm"),
    )

    # info4 distribution
    info4_counter = Counter(df["info4"].fill_null("∅").to_list())
    source_tag_counter = Counter(df["source_tag"].fill_null("∅").to_list())

    # classification des codes
    codes = df["code_norm"].to_list()
    classification = Counter(classify(c, codes_ofs, codes_owl) for c in codes)
    n_valid_ofs = classification.get("ofs", 0)
    n_valid_owl = classification.get("owl_only", 0)
    n_orphan = classification.get("orphan", 0)
    n_unparse = classification.get("unparseable", 0)

    # format des codes : longueur du code_raw (sans normalisation)
    raw_lengths = Counter(
        len(c) if c else 0 for c in df["code_raw"].to_list()
    )
    raw_has_dot = sum(1 for c in df["code_raw"].to_list() if c and "." in c)
    print(f"Longueurs code_raw : {dict(raw_lengths)}")
    print(f"Codes avec point dans la source brute : {raw_has_dot}")
    print(f"Classification : {dict(classification)}")

    # doublons internes (code_norm, libellé normalisé)
    n_dup_pairs = 0
    if "libelle" in df.columns:
        norm_df = df.with_columns(
            pl.col("libelle")
            .map_elements(lambda x: normalize_for_match(x or ""), return_dtype=pl.String)
            .alias("libelle_norm"),
        )
        dups = (
            norm_df.group_by(["code_norm", "libelle_norm"])
            .len()
            .filter(pl.col("len") > 1)
        )
        n_dup_pairs = dups.height
    print(f"Paires (code, libellé norm) dupliquées intra-feuille : {n_dup_pairs}")

    # exemples : n premières lignes valides
    examples = []
    for row in df.iter_rows(named=True):
        if len(examples) >= n_examples:
            break
        if row["code_norm"] is None:
            continue
        examples.append(
            {
                "libelle": row["libelle"],
                "code_raw": row["code_raw"],
                "code_norm": row["code_norm"],
                "icd_classification": classify(
                    row["code_norm"], codes_ofs, codes_owl
                ),
            }
        )

    payload = {
        "sheet_name": sheet_name,
        "label": label,
        "n_raw": n_raw,
        "raw_lengths": dict(raw_lengths),
        "raw_with_dot": raw_has_dot,
        "info4_distribution": dict(info4_counter),
        "source_tag_distribution": dict(source_tag_counter),
        "classification": dict(classification),
        "n_valid_ofs": n_valid_ofs,
        "n_valid_owl_only": n_valid_owl,
        "n_orphan": n_orphan,
        "n_unparseable": n_unparse,
        "n_internal_duplicates": n_dup_pairs,
        "examples": examples,
    }
    return payload


def inventory_all_aphp(
    codes_ofs: set[str], codes_owl: set[str]
) -> dict[str, Any]:
    print("\n========== AP-HP / Index CIM-10 ==========")
    results: dict[str, Any] = {}
    # 10 exemples pour Index CIM-10 (gros volume), 5 pour les autres
    for sheet, label in APHP_UTIL_SHEETS.items():
        n_ex = 10 if label == "INDEX_CIM10_VOL3" else 5
        results[label] = inventory_aphp_sheet(
            sheet, label, codes_ofs, codes_owl, n_ex
        )

    # Crossover : pour chaque paire (code_norm, libellé_norm), nombre
    # de feuilles distinctes où elle apparaît. Ne couvre QUE les
    # feuilles AP-HP métiers (pas l'Index CIM-10 vol3).
    print("\n----- Chevauchement inter-feuilles AP-HP métiers -----")
    cross_frames = []
    for sheet, label in APHP_UTIL_SHEETS.items():
        if label == "INDEX_CIM10_VOL3":
            continue
        df = read_aphp_sheet(sheet).with_columns(
            pl.col("code_raw").map_elements(normalize_icd_code, return_dtype=pl.String).alias("code_norm"),
            pl.col("libelle")
            .map_elements(lambda x: normalize_for_match(x or ""), return_dtype=pl.String)
            .alias("libelle_norm"),
            pl.lit(label).alias("source_label"),
        )
        cross_frames.append(df.select("code_norm", "libelle_norm", "source_label"))
    cross = (
        pl.concat(cross_frames)
        .filter(pl.col("code_norm").is_not_null())
        .filter(pl.col("libelle_norm").str.len_chars() > 0)
    )
    grouped = cross.group_by(["code_norm", "libelle_norm"]).agg(
        pl.col("source_label").unique().alias("sources"),
        pl.len().alias("n_occurrences"),
    )
    grouped = grouped.with_columns(pl.col("sources").list.len().alias("n_sources"))
    cross_stats = grouped.group_by("n_sources").agg(pl.len().alias("n_pairs")).sort("n_sources")
    print("Paires (code, libellé) par nombre de feuilles AP-HP où elles figurent :")
    print(cross_stats)
    # exemples de chevauchements multi-feuilles
    multi = grouped.filter(pl.col("n_sources") >= 2).head(10)
    print(f"\nExemples paires partagées entre ≥2 feuilles AP-HP :")
    with pl.Config(fmt_str_lengths=70, tbl_cols=-1):
        print(multi)

    results["__cross__"] = {
        "distribution_pairs_by_n_sources": cross_stats.to_dicts(),
        "examples_shared": multi.to_dicts(),
    }

    # Croisement Index ↔ AP-HP métiers
    print("\n----- Chevauchement Index CIM-10 ↔ AP-HP métiers -----")
    idx_df = read_aphp_sheet("Cim Alphabétique").with_columns(
        pl.col("code_raw").map_elements(normalize_icd_code, return_dtype=pl.String).alias("code_norm"),
        pl.col("libelle")
        .map_elements(lambda x: normalize_for_match(x or ""), return_dtype=pl.String)
        .alias("libelle_norm"),
    )
    idx_pairs = (
        idx_df.filter(pl.col("code_norm").is_not_null())
        .filter(pl.col("libelle_norm").str.len_chars() > 0)
        .select("code_norm", "libelle_norm")
        .unique()
    )
    aphp_pairs = grouped.select("code_norm", "libelle_norm").unique()
    intersection = idx_pairs.join(aphp_pairs, on=["code_norm", "libelle_norm"], how="inner")
    print(f"Paires AP-HP métier déjà présentes dans l'Index CIM-10 : {intersection.height}")
    results["__cross__"]["aphp_in_index"] = intersection.height

    write_json("aphp_and_index", results)
    return results


# ----------------------------------------------------------------------
# 4. Volumétrie totale (dédup tolérante intra et inter-sources)
# ----------------------------------------------------------------------


def estimate_total_volume(
    orph_payload: dict[str, Any],
    aphp_payload: dict[str, Any],
    codes_ofs: set[str],
    codes_owl: set[str],
) -> dict[str, Any]:
    print("\n========== Volumétrie totale ==========")

    # ORPHANET : pour chaque ref ICD-10 relation=E avec code valide,
    # produit 1 entrée Name + n entrées Synonym. Dédup par
    # (code, texte normalisé).
    tree = ET.parse(ORPHANET_XML)
    orph_pairs: set[tuple[str, str]] = set()
    for d in tree.findall(".//Disorder"):
        name = (d.findtext("Name") or "").strip()
        synonyms = [
            (s.text or "").strip()
            for s in d.findall("SynonymList/Synonym")
            if (s.text or "").strip()
        ]
        for er in d.findall("ExternalReferenceList/ExternalReference"):
            if (er.findtext("Source") or "").strip() != "ICD-10":
                continue
            rel = er.find("DisorderMappingRelation/Name")
            sigle = (rel.text or "").split(" ")[0] if rel is not None else ""
            if sigle != "E":
                continue
            code = normalize_icd_code((er.findtext("Reference") or "").strip())
            if code is None or classify(code, codes_ofs, codes_owl) == "orphan":
                continue
            for txt in [name] + synonyms:
                if not txt:
                    continue
                orph_pairs.add((code, normalize_for_match(txt)))
    print(f"ORPHANET (relation E, codes valides) : {len(orph_pairs)} paires (code, syn norm)")

    # AP-HP toutes feuilles (Index + métiers).
    aphp_pairs: set[tuple[str, str]] = set()
    for sheet in APHP_UTIL_SHEETS:
        df = read_aphp_sheet(sheet).with_columns(
            pl.col("code_raw").map_elements(normalize_icd_code, return_dtype=pl.String).alias("code_norm"),
            pl.col("libelle")
            .map_elements(lambda x: normalize_for_match(x or ""), return_dtype=pl.String)
            .alias("libelle_norm"),
        )
        for row in df.iter_rows(named=True):
            c = row["code_norm"]
            t = row["libelle_norm"]
            if c is None or not t:
                continue
            if classify(c, codes_ofs, codes_owl) == "orphan":
                continue
            aphp_pairs.add((c, t))
    print(f"AP-HP toutes feuilles utiles : {len(aphp_pairs)} paires (code, syn norm)")

    overlap = orph_pairs & aphp_pairs
    print(f"Chevauchement ORPHANET ∩ AP-HP : {len(overlap)} paires")
    union = orph_pairs | aphp_pairs
    print(f"Union nette (lignes à ajouter au CSV final, estimation) : {len(union)}")

    return {
        "orphanet_pairs_valid": len(orph_pairs),
        "aphp_pairs_valid": len(aphp_pairs),
        "overlap": len(overlap),
        "union": len(union),
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    codes_ofs, codes_owl = load_validation_sets()
    orph = inventory_orphanet(codes_ofs, codes_owl)
    aphp = inventory_all_aphp(codes_ofs, codes_owl)
    vol = estimate_total_volume(orph, aphp, codes_ofs, codes_owl)
    write_json("volumetry", vol)
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
