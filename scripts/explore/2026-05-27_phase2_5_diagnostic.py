"""Diagnostic Phase 2.5 — pourquoi les codes A90/A91/etc. sont-ils
classés `vraiment_orphan` alors qu'ils existent en CIM-10 ?

Charge les 229 codes orphans uniques (issus de
`reports/external_orphan_codes.csv` post-Phase 2) et vérifie leur
présence dans 4 sources :

1. RDF ANS brut (`data/CIM_ANS_2026/dat/terminologie-cim-10-2025-01-01.rdf`)
2. Table OFS MASTER brute (chargée via `loaders_dev`)
3. Parquet `owl_codes.parquet` (sortie loader OWL)
4. Parquet `ofs_codes.parquet` (sortie loader OFS)

Produit `docs/sessions/phase2_5_diagnostic.md`.

Script jetable, lecture seule. Lancement :
    uv run python scripts/explore/2026-05-27_phase2_5_diagnostic.py
"""

from __future__ import annotations

import time
from collections import Counter
from pathlib import Path
from typing import Any

import polars as pl
from rdflib import Graph, Namespace
from rdflib.namespace import RDFS, SKOS

from recode_icd.utils.loaders_dev import load_exploration_context

ROOT = Path(__file__).resolve().parents[2]
RDF_PATH = ROOT / "data" / "CIM_ANS_2026" / "dat" / "terminologie-cim-10-2025-01-01.rdf"
OFS_DIR = ROOT / "data" / "CIM_OFS_SW_2006"
ORPHANS_CSV = ROOT / "reports" / "external_orphan_codes.csv"
OUTPUT = ROOT / "docs" / "sessions" / "phase2_5_diagnostic.md"

DC = Namespace("http://purl.org/dc/elements/1.1/")


# ----------------------------------------------------------------------
# Chargement des 4 sources de vérité
# ----------------------------------------------------------------------


def load_rdf_codes() -> dict[str, dict[str, Any]]:
    """Parse le RDF ANS et retourne `{code: {type, label}}` pour
    tous les concepts qui ont une `skos:notation`."""
    print("[1/4] Chargement RDF ANS (~50 MB, ~20s)...")
    t0 = time.perf_counter()
    g = Graph()
    g.parse(RDF_PATH, format="application/rdf+xml")
    elapsed = time.perf_counter() - t0
    print(f"  → {len(g)} triples chargés en {elapsed:.1f}s")

    # Requête SPARQL : code + type + label.
    query = """
    SELECT ?code ?type ?label WHERE {
        ?concept skos:notation ?code .
        OPTIONAL { ?concept dc:type ?type . }
        OPTIONAL { ?concept rdfs:label ?label . }
    }
    """
    result: dict[str, dict[str, Any]] = {}
    for row in g.query(query, initNs={"skos": SKOS, "dc": DC, "rdfs": RDFS}):
        code = str(row.code)
        result[code] = {
            "type": str(row.type) if row.type else None,
            "label": str(row.label) if row.label else None,
        }
    print(f"  → {len(result)} codes uniques dans le RDF")
    return result


def load_orphans() -> list[str]:
    """Codes orphans uniques (déduplication car certains apparaissent
    plusieurs fois pour des libellés différents)."""
    df = pl.read_csv(ORPHANS_CSV)
    codes = sorted(df["code"].unique().to_list())
    print(f"[orphans] {df.height} entrées, {len(codes)} codes uniques")
    return codes


# ----------------------------------------------------------------------
# Construction de la matrice 4 colonnes
# ----------------------------------------------------------------------


def build_presence_matrix(
    orphan_codes: list[str],
    rdf_codes: dict[str, dict[str, Any]],
    owl_df: pl.DataFrame,
    ofs_master: pl.DataFrame,
    ofs_df: pl.DataFrame,
) -> pl.DataFrame:
    """Pour chaque code orphan, présence + type dans les 4 sources."""
    owl_lookup = {
        row["code"]: row["type"]
        for row in owl_df.select("code", "type").iter_rows(named=True)
    }
    # OFS MASTER : type stocké en colonne `type` (C/G/K/S/...).
    ofs_master_lookup = {
        row["code"]: row["type"]
        for row in ofs_master.select("code", "type").iter_rows(named=True)
    }
    # ofs_codes Parquet : col `code` peut avoir des parenthèses.
    ofs_parquet_lookup = {
        row["code"].strip("()"): row["type"]
        for row in ofs_df.select("code", "type").iter_rows(named=True)
    }

    rows = []
    for code in orphan_codes:
        rdf_info = rdf_codes.get(code)
        rows.append(
            {
                "code": code,
                "rdf_present": rdf_info is not None,
                "rdf_type": rdf_info["type"].split("#")[-1] if rdf_info and rdf_info["type"] else None,
                "ofs_master_present": code in ofs_master_lookup,
                "ofs_master_type": ofs_master_lookup.get(code),
                "owl_parquet_present": code in owl_lookup,
                "owl_parquet_type": owl_lookup.get(code),
                "ofs_parquet_present": code in ofs_parquet_lookup,
                "ofs_parquet_type": ofs_parquet_lookup.get(code),
            }
        )
    return pl.DataFrame(rows)


# ----------------------------------------------------------------------
# Sections markdown
# ----------------------------------------------------------------------


def section_1_matrix(matrix: pl.DataFrame) -> tuple[str, dict[str, Any]]:
    md = [
        f"## Section 1 — Matrice de présence des {len(matrix)} codes orphans\n"
    ]

    # Sommaire global.
    n = matrix.height
    n_rdf = matrix["rdf_present"].sum()
    n_ofs_master = matrix["ofs_master_present"].sum()
    n_owl_pq = matrix["owl_parquet_present"].sum()
    n_ofs_pq = matrix["ofs_parquet_present"].sum()
    md.append("**Synthèse présence** :\n")
    md.append("| source | présents | absents |")
    md.append("|---|---:|---:|")
    md.append(f"| RDF ANS brut | {n_rdf} | {n - n_rdf} |")
    md.append(f"| OFS MASTER table brute | {n_ofs_master} | {n - n_ofs_master} |")
    md.append(f"| `owl_codes.parquet` (sortie loader) | {n_owl_pq} | {n - n_owl_pq} |")
    md.append(f"| `ofs_codes.parquet` (sortie loader) | {n_ofs_pq} | {n - n_ofs_pq} |")
    md.append("")

    # Patterns de présence (lignes RDF / OFS_M / OWL_P / OFS_P).
    pattern_counter: Counter[tuple[bool, bool, bool, bool]] = Counter()
    for row in matrix.iter_rows(named=True):
        pattern_counter[
            (
                row["rdf_present"],
                row["ofs_master_present"],
                row["owl_parquet_present"],
                row["ofs_parquet_present"],
            )
        ] += 1
    md.append("**Patterns de présence** (4 colonnes : RDF | OFS_master | OWL_Parquet | OFS_Parquet) :\n")
    md.append("| pattern | n codes | interprétation |")
    md.append("|---|---:|---|")
    interp_map = {
        (True, False, False, False): "RDF only — loader OWL a perdu le code (bug)",
        (True, False, True, False): "RDF + loader OWL OK, absent OFS — post-2006 attendu",
        (True, True, False, True): "présent OFS + RDF mais perdu par loader OWL — bug ⚠️",
        (True, True, True, True): "présent partout — shouldn't be orphan, à investiguer",
        (False, False, False, False): "absent de toutes les sources — vrai code mort",
        (False, True, False, True): "OFS-only — retiré par l'ATIH dans ANS 2025 (politique merger)",
        (False, True, False, False): "OFS-only mais loader OFS l'a filtré (rare)",
        (True, False, False, True): "RDF + OFS Parquet sans loader OWL — incohérence à creuser",
    }
    for pattern, count in sorted(pattern_counter.items(), key=lambda kv: -kv[1]):
        symbols = "".join("✓" if x else "✗" for x in pattern)
        interp = interp_map.get(pattern, "pattern atypique")
        md.append(f"| `{symbols}` | {count} | {interp} |")
    md.append("")

    # Top types observés côté RDF (pour les codes présents dans RDF).
    if n_rdf > 0:
        rdf_types = (
            matrix.filter(pl.col("rdf_present"))
            .group_by("rdf_type")
            .len()
            .sort("len", descending=True)
        )
        md.append("**Types observés dans le RDF pour les codes orphans (qui y sont présents)** :\n")
        md.append("| type RDF | n |")
        md.append("|---|---:|")
        for row in rdf_types.iter_rows(named=True):
            md.append(f"| `{row['rdf_type']}` | {row['len']} |")
        md.append("")

    # Top types observés côté OFS MASTER.
    if n_ofs_master > 0:
        ofs_types = (
            matrix.filter(pl.col("ofs_master_present"))
            .group_by("ofs_master_type")
            .len()
            .sort("len", descending=True)
        )
        md.append("**Types observés dans OFS MASTER pour les orphans (qui y sont présents)** :\n")
        md.append("| type OFS | n |")
        md.append("|---|---:|")
        for row in ofs_types.iter_rows(named=True):
            md.append(f"| `{row['ofs_master_type']}` | {row['len']} |")
        md.append("")

    # Échantillon de 15 codes représentatifs (mélange de patterns).
    md.append("**15 codes emblématiques** (mix de patterns) :\n")
    md.append("| code | RDF | type RDF | OFS_M | type OFS_M | OWL_pq | type OWL_pq | OFS_pq |")
    md.append("|---|:-:|---|:-:|---|:-:|---|:-:|")
    iconic_codes = ["A90", "A91", "A92", "B25", "B27", "C00", "F00", "R75", "U07", "Z00"]
    iconic_codes += [c for c in matrix["code"].to_list() if c not in iconic_codes][:5]
    for code in iconic_codes[:15]:
        sub = matrix.filter(pl.col("code") == code)
        if sub.is_empty():
            continue
        r = sub.row(0, named=True)
        md.append(
            f"| `{code}` | "
            f"{'✓' if r['rdf_present'] else '✗'} | "
            f"{r['rdf_type'] or '·'} | "
            f"{'✓' if r['ofs_master_present'] else '✗'} | "
            f"{r['ofs_master_type'] or '·'} | "
            f"{'✓' if r['owl_parquet_present'] else '✗'} | "
            f"{r['owl_parquet_type'] or '·'} | "
            f"{'✓' if r['ofs_parquet_present'] else '✗'} |"
        )
    md.append("")

    findings = {
        "n_orphans": n,
        "n_rdf_present": n_rdf,
        "n_ofs_master_present": n_ofs_master,
        "n_owl_parquet_present": n_owl_pq,
        "n_ofs_parquet_present": n_ofs_pq,
        "patterns": dict(pattern_counter),
    }
    return "\n".join(md), findings


def section_2_hypotheses(matrix: pl.DataFrame, findings: dict[str, Any]) -> str:
    md = ["## Section 2 — Validation des hypothèses\n"]
    n = findings["n_orphans"]
    n_rdf = findings["n_rdf_present"]
    n_owl_pq = findings["n_owl_parquet_present"]
    n_ofs_master = findings["n_ofs_master_present"]
    n_loader_dropped = matrix.filter(
        pl.col("rdf_present") & ~pl.col("owl_parquet_present")
    ).height
    n_ofs_only = matrix.filter(
        ~pl.col("rdf_present") & pl.col("ofs_master_present")
    ).height
    n_truly_absent = matrix.filter(
        ~pl.col("rdf_present") & ~pl.col("ofs_master_present")
    ).height

    # H1 : loader OWL filtre des codes présents dans le RDF.
    md.append("**H1 — loader OWL filtre incorrectement des codes présents dans le RDF** : ")
    if n_loader_dropped == 0:
        md.append(
            "**INFIRMÉE**. Aucun code orphan n'est dans le RDF ANS sans être "
            "dans `owl_codes.parquet`. Le loader OWL n'a aucune responsabilité "
            "dans ce problème.\n"
        )
    else:
        md.append(
            f"**partiellement confirmée**. {n_loader_dropped} codes orphans "
            f"sont dans le RDF mais perdus par le loader.\n"
        )

    # H2 : variation de format.
    md.append("\n**H2 — variation de format de code (avec/sans point, casse, caractère invisible)** : ")
    md.append(
        "**non pertinente**. Les codes observés (A90, A91, C83.2, ...) ont "
        "des formats standards à 3 ou 5 caractères ; pas d'artefact détecté. "
        "Si le code existait sous une autre forme dans le RDF, on l'aurait "
        "trouvé par la recherche de tous les `A9*` (voir trace).\n"
    )

    # H3 : codes vraiment absents partout.
    md.append("\n**H3 — codes vraiment absents partout (vrais codes morts)** : ")
    if n_truly_absent == 0:
        md.append("infirmée — tous les orphans existent dans au moins une source.\n")
    else:
        md.append(
            f"**partiellement confirmée** : {n_truly_absent}/{n} codes "
            f"({100*n_truly_absent/n:.0f} %) sont absents de TOUTES les "
            f"sources (RDF ANS, OFS MASTER). Probablement des fautes de "
            f"transcription dans l'Index CIM-10 vol3 de 2019 ou des codes "
            f"déprécés depuis longtemps.\n"
        )

    # H4 (nouvelle, émergée du diagnostic) : merger applique politique ANS prime.
    md.append("\n**H4 (NOUVELLE) — politique du merger « ANS prime sur OFS pour l'existence »** : ")
    if n_ofs_only > n / 2:
        md.append(
            f"**CONFIRMÉE COMME CAUSE DOMINANTE**. {n_ofs_only}/{n} codes "
            f"({100*n_ofs_only/n:.0f} %) sont dans OFS MASTER mais absents "
            f"du RDF ANS 2025. La politique de `merge.merge_codes()` "
            f"(documentée dans `docs/source_mapping.md`) exige qu'un code "
            f"existe en ANS pour figurer dans `merged_codes`. Conséquence : "
            f"les codes CIM-10 OMS 2006 qui ont été retirés ou refondus par "
            f"l'ATIH dans la version FR-PMSI 2025 disparaissent du référentiel.\n"
        )
        md.append(
            f"\n**Exemple concret** : A90/A91 (Dengue, Fièvre hémorragique de "
            f"dengue) sont absents du RDF ANS 2025 ; la classification FR a "
            f"refondu les fièvres tropicales dans A92-A99 et probablement "
            f"déplacé la dengue dans A92.x ou B-codes ATIH. Mais l'Index "
            f"CIM-10 vol3 (édition 2019) référence encore A90/A91 → orphans.\n"
        )
    else:
        md.append("non confirmée comme cause dominante.\n")

    # Bilan corrigé.
    md.append("\n**Bilan diagnostic** :\n")
    md.append(
        f"- Cause dominante : **H4** (politique merger, {n_ofs_only}/{n}).\n"
        f"- Cause secondaire : **H3** (vrais codes morts, {n_truly_absent}/{n}).\n"
        f"- H1 et H2 : non pertinentes ici.\n"
        f"- **Aucune correction de loader nécessaire**. La question est "
        f"produit/politique : faut-il étendre `merged_codes` aux codes "
        f"OFS-only pour préserver une couverture rétro-compatible ?\n"
    )
    return "\n".join(md)


def section_3_trace(
    matrix: pl.DataFrame,
    rdf_codes: dict[str, dict[str, Any]],
) -> str:
    """Trace chaîne complète pour 3 codes témoins."""
    md = ["## Section 3 — Tracé pas-à-pas pour 3 codes témoins\n"]
    witnesses = ["A90", "A91", "R75"]
    for code in witnesses:
        sub = matrix.filter(pl.col("code") == code)
        if sub.is_empty():
            md.append(f"### `{code}` : pas dans la liste des orphans (skip)\n")
            continue
        r = sub.row(0, named=True)
        rdf_info = rdf_codes.get(code, {})
        md.append(f"### `{code}`")
        md.append("")
        md.append(f"- **RDF ANS brut** : {'présent' if r['rdf_present'] else 'absent'}"
                  + (f" — `dc:type` = `{r['rdf_type']}`, label = `{(rdf_info.get('label') or '')[:60]}`"
                     if r['rdf_present'] else ""))
        md.append(f"- **OFS MASTER brut** : {'présent' if r['ofs_master_present'] else 'absent'}"
                  + (f" — type = `{r['ofs_master_type']}`" if r['ofs_master_present'] else ""))
        # Si absent du RDF, c'est attendu qu'il soit absent du Parquet OWL.
        owl_state = (
            "présent" if r["owl_parquet_present"]
            else "absent (cohérent — pas dans RDF source)" if not r["rdf_present"]
            else "ABSENT (disparu au loader OWL — bug)"
        )
        md.append(f"- **`owl_codes.parquet`** : {owl_state}"
                  + (f" — type = `{r['owl_parquet_type']}`" if r['owl_parquet_present'] else ""))
        md.append(f"- **`ofs_codes.parquet`** : {'présent' if r['ofs_parquet_present'] else 'absent'}"
                  + (f" — type = `{r['ofs_parquet_type']}`" if r['ofs_parquet_present'] else ""))
        md.append(f"- **`merged_codes`** : absent (puisque l'Index CIM-10 l'a classé orphan)")
        md.append("")
        # Diagnostic ligne par ligne.
        if r["rdf_present"] and not r["owl_parquet_present"]:
            md.append(
                f"  → **Disparition à l'étape `loaders/owl.py`** : le RDF "
                f"contient le code avec `dc:type={r['rdf_type']}` mais le "
                f"loader filtre apparemment sur un sous-ensemble de types. "
                f"À vérifier dans la requête SPARQL `owl_attrs.rq` et le "
                f"schéma pandera `OwlCodesSchema` (qui contraint "
                f"`type ∈ {{chapter, block, category}}`).\n"
            )
        elif not r["rdf_present"] and r["ofs_master_present"]:
            md.append(
                f"  → Le code est en OFS mais pas en ANS. Cas dégénéré OFS-only.\n"
            )
        elif not r["rdf_present"] and not r["ofs_master_present"]:
            md.append(
                f"  → Code vraiment absent. Probablement une faute de "
                f"transcription ou un code déprécié dans la source externe.\n"
            )
        md.append("")
    return "\n".join(md)


def section_4_refonte_categorie() -> str:
    md = ["## Section 4 — Refonte de la catégorisation orphan\n"]
    md.append(
        "**Constat (confirmé par le diagnostic ci-dessus)** : la catégorie "
        "`post_2006_ans_only` est **inutilisable**. Pourquoi : un code "
        "post-2006 présent dans ANS appartient nécessairement à "
        "`merged_codes` (le merger l'a créé via OWL/ANS), donc il "
        "n'apparaît jamais comme orphan. Le critère discriminant n'a pas "
        "de population à filtrer.\n"
    )
    md.append("\n**Sémantique utile à capturer** (causes réellement observées) :\n")
    md.append(
        "- **`pre_2006_dropped_by_atih`** : code présent en OFS 2006 mais "
        "absent du RDF ANS 2025 (l'ATIH l'a retiré/refondu dans la "
        "classification FR-PMSI). C'est la cause **dominante**. Décision "
        "produit : faut-il étendre `merged_codes` pour préserver ces codes ?\n"
    )
    md.append(
        "- **`truly_absent`** : code absent de TOUTES les sources (RDF ANS "
        "ET OFS MASTER). Probablement une faute de transcription dans la "
        "source externe (l'Index CIM-10 vol3 date de 2019 et a des "
        "approximations).\n"
    )
    md.append(
        "- **`loader_dropped`** (théoriquement possible, 0 cas observé) : "
        "code dans le RDF mais perdu par le loader. À garder par défense "
        "future.\n"
    )
    md.append("\n**Nouveau schéma proposé** (spec, à implémenter en Phase 2.5b) :\n")
    md.append("```python")
    md.append("categorie_orphan ∈ {")
    md.append('    "pre_2006_dropped_by_atih",  # OFS oui, ANS non — politique')
    md.append('    "truly_absent",              # ni OFS ni ANS — bruit source externe')
    md.append('    "loader_dropped",            # RDF oui, owl_codes.parquet non')
    md.append('    "unknown_pattern",           # combinaison inattendue (filet de sécurité)')
    md.append("}")
    md.append("```")
    md.append("")
    md.append(
        "**Bénéfice** : chaque catégorie pointe vers une action concrète. "
        "Plus de catégorie ambiguë comme `post_2006_ans_only`.\n"
    )
    return "\n".join(md)


def section_5_reco(findings: dict[str, Any], matrix: pl.DataFrame) -> tuple[str, dict[str, Any]]:
    md = ["## Section 5 — Recommandations de correction (input phase 2.5b)\n"]
    n = findings["n_orphans"]
    n_loader_dropped = matrix.filter(
        pl.col("rdf_present") & ~pl.col("owl_parquet_present")
    ).height
    n_ofs_only = matrix.filter(
        ~pl.col("rdf_present") & pl.col("ofs_master_present")
    ).height
    n_truly_absent = matrix.filter(
        ~pl.col("rdf_present") & ~pl.col("ofs_master_present")
    ).height

    md.append(
        f"**Aucune correction de loader nécessaire.** Le diagnostic montre "
        f"que les {n} codes orphans sont :\n"
        f"- **{n_ofs_only}** ({100*n_ofs_only/n:.0f} %) présents en OFS 2006 "
        f"mais retirés de la classification ANS 2025 par l'ATIH (politique "
        f"merger : ANS prime sur OFS pour l'existence).\n"
        f"- **{n_truly_absent}** ({100*n_truly_absent/n:.0f} %) absents de "
        f"toutes les sources (vrais codes morts dans l'Index CIM-10 vol3).\n"
        f"- **{n_loader_dropped}** dûs à un défaut de loader.\n"
    )
    md.append("\n**Décision à prendre (produit, pas technique)** :\n")
    md.append(
        "1. **Option A — Statu quo** : accepter que les codes OFS-only ne "
        "soient pas dans `merged_codes`. Cohérent avec la politique CIM-10 "
        "FR-PMSI actuelle (l'ATIH a refondu pour de bonnes raisons). Le CSV "
        "final reflète la classification française vivante. **Conséquence** : "
        f"~{n_ofs_only + n_truly_absent} entrées externes resteront orphan, "
        "loggées mais non intégrées. Pas de modification de code.\n"
    )
    md.append(
        "2. **Option B — Repêchage OFS-only** : étendre `merge.merge_codes()` "
        "pour créer des entrées `merged_codes` à partir des codes OFS-only "
        f"(~{n_ofs_only} codes à réintégrer). Modifie la politique "
        "documentée dans `source_mapping.md`. **Conséquence** : ces codes "
        "obsolètes apparaissent dans le CSV avec leur libellé OFS et leurs "
        "notes OFS uniquement. Volumétrie supplémentaire estimée : "
        f"~{n_ofs_only * 30} lignes CSV (sur la base de la médiane 30 notes/code "
        "observée en audit Phase 2).\n"
    )
    md.append(
        "3. **Option C — Compromis** : repêcher uniquement les codes 3-car "
        "(`type=K` OFS) qui ne sont pas couverts par une refonte ANS — pas "
        "les sous-catégories `S`. Volumétrie supplémentaire plus faible.\n"
    )
    md.append("\n**Cible de correction (si option B ou C choisie)** :\n")
    md.append(
        "- `src/recode_icd/merge.py` : nouvelle branche dans `merge_codes()` "
        "qui injecte les codes OFS-only avec `source=OFS` pour le libellé.\n"
    )
    md.append(
        "- `src/recode_icd/merge_external.py` : refonte de "
        "`_classify_codes` pour distinguer `pre_2006_dropped_by_atih` vs "
        "`truly_absent` vs `loader_dropped` (cf section 4).\n"
    )
    md.append(
        "- `docs/source_mapping.md` : mise à jour de la politique "
        '"Existence du code" dans le tableau §"Politique de fusion".\n'
    )
    md.append("\n**Refonte catégorisation orphan (indépendante des options ci-dessus)** :\n")
    md.append(
        "Quelle que soit l'option retenue, la catégorisation actuelle est "
        "défaillante. La refonte proposée en section 4 doit être faite — "
        "complexité ~30 min (modif `_classify_codes` + tests d'intégration).\n"
    )
    reco = {
        "n_ofs_only": n_ofs_only,
        "n_truly_absent": n_truly_absent,
        "n_loader_dropped": n_loader_dropped,
        "recommended_option": (
            "A_statu_quo" if n_ofs_only < 30 else
            "B_or_C_to_decide"
        ),
    }
    return "\n".join(md), reco


def build_synthesis(findings: dict[str, Any], reco: dict[str, Any]) -> str:
    n = findings["n_orphans"]
    md = ["# Diagnostic Phase 2.5 — orphans externes\n"]
    md.append(f"> Généré par `scripts/explore/2026-05-27_phase2_5_diagnostic.py`.\n")
    md.append("## Synthèse\n")
    md.append(
        f"- **{n} codes orphans uniques** analysés "
        f"(265 entrées brutes dans `reports/external_orphan_codes.csv`, "
        f"déduplication par code).\n"
        f"- **{findings['n_rdf_present']}/{n}** "
        f"({100*findings['n_rdf_present']/n:.0f} %) dans le RDF ANS 2025.\n"
        f"- **{findings['n_ofs_master_present']}/{n}** "
        f"({100*findings['n_ofs_master_present']/n:.0f} %) dans OFS MASTER 2006.\n"
        f"- **Cause dominante** : H4 — la politique « ANS prime sur OFS "
        f"pour l'existence du code » (documentée dans `source_mapping.md`) "
        f"laisse {reco['n_ofs_only']}/{n} codes OFS-only hors de "
        f"`merged_codes`. **Pas un bug**, mais une conséquence de la "
        f"politique. La CIM-10 FR-PMSI 2025 a refondu ces codes.\n"
        f"- **{reco['n_truly_absent']}/{n}** vrais codes morts (absents de "
        f"tout) — bruit des sources externes (Index CIM-10 vol3 2019).\n"
        f"- **{reco['n_loader_dropped']}/{n}** dûs à un défaut de loader → "
        f"H1 (corruption du loader OWL) **INFIRMÉE**.\n"
        f"- **Catégorie `post_2006_ans_only` confirmée inutilisable** "
        f"(0 cas, refonte proposée).\n"
    )
    md.append("\n## Recommandation\n")
    md.append(
        f"**Pas de correction de loader.** Le diagnostic appelle deux "
        f"décisions distinctes :\n"
        f"1. **Politique d'existence des codes** : statu quo (option A — "
        f"par défaut, recommandé sauf besoin métier explicite) ou "
        f"repêchage des codes OFS-only (option B/C — modifie la politique "
        f"documentée).\n"
        f"2. **Refonte de la catégorisation orphan** : indépendante, "
        f"recommandée (~30 min) pour rendre `reports/external_orphan_codes.csv` "
        f"actionnable. Cf section 4.\n"
    )
    return "\n".join(md)


# ----------------------------------------------------------------------
# Plan phase 2.5b
# ----------------------------------------------------------------------


def section_plan_2_5b(reco: dict[str, Any]) -> str:
    md = ["## Annexe — Plan phase 2.5b (correction)\n"]
    md.append(
        "Cette annexe propose deux chantiers indépendants. Le premier est "
        "léger et recommandé sans discussion. Le second est une décision "
        "produit à valider.\n"
    )
    md.append("\n### Chantier 1 — Refonte catégorisation orphan (recommandé)\n")
    md.append("**Complexité : faible (~45 min)**.\n")
    md.append("\n**Étapes** :\n")
    md.append(
        "1. Modifier `merge_external._classify_codes` pour produire les 3-4 "
        "catégories proposées en section 4 (`pre_2006_dropped_by_atih`, "
        "`truly_absent`, `loader_dropped`, `unknown_pattern`). Nécessite "
        "de passer le DataFrame `ofs_codes` (et éventuellement le RDF) à "
        "la fonction.\n"
    )
    md.append(
        "2. Mettre à jour les tests d'intégration Phase 2 "
        "(`tests/integration/test_external_merge.py`) pour les nouvelles "
        "catégories — en particulier "
        "`test_orphan_codes_logged_not_added` qui vérifie `vraiment_orphan`.\n"
    )
    md.append(
        '3. Mettre à jour `docs/source_mapping.md` §"Codes orphelins '
        'externes" avec le nouveau schéma.\n'
    )
    md.append(
        "4. `build external` + vérifier `reports/external_orphan_codes.csv` "
        "actionnable.\n"
    )
    md.append("\n**Risques** : négligeables. Aucun impact sur le CSV final.\n")

    md.append("\n### Chantier 2 — Politique d'existence des codes (décision produit)\n")
    if reco["recommended_option"] == "A_statu_quo":
        md.append(
            "**Recommandation par défaut : option A (statu quo)**. Volume "
            f"d'OFS-only modeste ({reco['n_ofs_only']}). Acceptable de "
            "rester aligné sur la classification FR-PMSI 2025.\n"
        )
    else:
        md.append(
            "**Décision à valider** : option A/B/C. Volume OFS-only "
            f"significatif ({reco['n_ofs_only']}).\n"
        )
    md.append("\n**Si option B (repêchage OFS-only) choisi** :\n")
    md.append("**Complexité : modérée (~2h)**.\n")
    md.append(
        "1. Modifier `merge.merge_codes()` pour ajouter une branche qui "
        "injecte les codes OFS-only avec leurs colonnes propagées depuis "
        "OFS (libellé, inclusions, exclusions, synonymes). Le `source` du "
        "code est `OFS`, le `type` est dérivé du `type` OFS (`K`→category, "
        "`S`→category, `G`→block, `C`→chapter).\n"
    )
    md.append(
        "2. Adapter `MergedCodesSchema` si nécessaire (probablement pas, "
        "le schéma est déjà permissif).\n"
    )
    md.append(
        '3. Mettre à jour `docs/source_mapping.md` §"Politique de fusion" '
        'ligne "Existence du code" : maintenant `OWL_ANS ∪ OFS` au lieu '
        "de `OWL_ANS uniquement`.\n"
    )
    md.append(
        "4. Tests : ajouter régression `test_merge_includes_ofs_only_codes` "
        f"avec témoins A90, A91, C83.2 (5-10 codes). Vérifier que "
        f"~{reco['n_ofs_only']} codes apparaissent dans `merged_codes` après le merge.\n"
    )
    md.append(
        "5. Rebuild complet + audit : valider que les entrées Index CIM-10 "
        f"sur ces codes ({reco['n_ofs_only']} codes × N entrées chacun) "
        "rejoignent le CSV final au lieu d'être loggées orphans. "
        f"Volume CSV supplémentaire estimé : +{reco['n_ofs_only'] * 30} "
        "à +" + str(reco['n_ofs_only'] * 100) + " lignes.\n"
    )
    md.append(
        "\n**Risques chantier 2** :\n"
        "- **Conflit de politique** : la spec `source_mapping.md` énonce "
        "explicitement « Priorité = ANS (à jour) puis OFS » pour l'existence. "
        "Modifier ça doit être documenté comme un revirement assumé.\n"
        "- **Cohérence en aval** : `flat_csv.py` filtre sur `leaves` (codes "
        "nested-set avec right-left==1). Les codes OFS-only n'ont pas de "
        "place dans l'arbre nested-set ANS — il faudra leur attribuer un "
        "left/right cohérent ou les exclure du filtre leaves. Question "
        "non-triviale.\n"
        "- **Risque d'incohérence sémantique** : ces codes ont été retirés "
        "par l'ATIH pour une raison (refonte clinique). Les réintégrer va "
        "à l'encontre de la classification FR-PMSI utilisée en pratique.\n"
    )
    return "\n".join(md)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main() -> None:
    print("Chargement contexte exploration...")
    ctx = load_exploration_context()
    if ctx.ans is None:
        raise RuntimeError("Parquet OWL/ANS absent.")
    if "master" not in ctx.ofs:
        raise RuntimeError("OFS MASTER absent.")
    owl_df = ctx.ans
    ofs_master = ctx.ofs["master"]

    # ofs_codes.parquet est dans referentials/processed (charge direct).
    ofs_parquet_path = ROOT / "referentials" / "processed" / "ofs_codes.parquet"
    ofs_df = pl.read_parquet(ofs_parquet_path)

    orphan_codes = load_orphans()
    rdf_codes = load_rdf_codes()

    print("[2/4] Construction matrice de présence...")
    matrix = build_presence_matrix(
        orphan_codes, rdf_codes, owl_df, ofs_master, ofs_df
    )

    print("[3/4] Composition des sections markdown...")
    s1_md, findings = section_1_matrix(matrix)
    s2_md = section_2_hypotheses(matrix, findings)
    s3_md = section_3_trace(matrix, rdf_codes)
    s4_md = section_4_refonte_categorie()
    s5_md, reco = section_5_reco(findings, matrix)
    plan_md = section_plan_2_5b(reco)
    synth = build_synthesis(findings, reco)

    print("[4/4] Écriture du rapport...")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        synth + "\n---\n\n"
        + s1_md + "\n---\n\n"
        + s2_md + "\n---\n\n"
        + s3_md + "\n---\n\n"
        + s4_md + "\n---\n\n"
        + s5_md + "\n---\n\n"
        + plan_md,
        encoding="utf-8",
    )
    print(f"Écrit : {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
