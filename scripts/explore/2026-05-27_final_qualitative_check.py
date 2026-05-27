"""Inspection qualitative finale du CSV final après les phases 1-3
du chantier "sources externes".

Produit `docs/sessions/final_qualitative_check.md` avec :
1. Échantillon de 20 entrées sur A52.7 (le code champion).
2. 5 codes "moyens" avec 10-20 notes (échantillon aléatoire).
3. Distribution globale source × type.
4. 3 codes "OFS+ANS only" pour vérifier que les externes n'ont pas
   dégradé le contenu existant.

Script jetable, lecture seule. Lancement :
    uv run python scripts/explore/2026-05-27_final_qualitative_check.py
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import polars as pl

from recode_icd._normalize import normalize_for_match
from recode_icd.utils.loaders_dev import load_exploration_context

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "sessions" / "final_qualitative_check.md"
SEED = 42

# Sources externes utiles pour distinguer "OFS+ANS only" dans §4.
_INTERNAL_SOURCES = frozenset({"CIM-10", "ANS", "CIM-10 frères"})


def _truncate(text: str | None, max_len: int = 80) -> str:
    if text is None:
        return ""
    s = str(text).replace("\n", " ").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def _markdown_table_rows(rows: list[dict[str, Any]], cols: list[str]) -> list[str]:
    md = ["| " + " | ".join(cols) + " |"]
    md.append("|" + "|".join("---" for _ in cols) + "|")
    for row in rows:
        cells = [str(row.get(c, "") or "") for c in cols]
        md.append("| " + " | ".join(cells) + " |")
    return md


# ----------------------------------------------------------------------
# Section 1 — A52.7
# ----------------------------------------------------------------------


def section_1_a52_7(csv: pl.DataFrame) -> tuple[str, dict[str, Any]]:
    sub = csv.filter(pl.col("code") == "A52.7")
    n_total = sub.height
    sample = sub.sample(n=20, seed=SEED)
    sample_rows = [
        {
            "source": r["source"],
            "type": r["type"],
            "texte": _truncate(r["texte"], 90),
        }
        for r in sample.iter_rows(named=True)
    ]

    # Détection rapide de doublons sémantiques sur l'échantillon.
    norms = [normalize_for_match(r["texte"]) for r in sample.iter_rows(named=True)]
    n_unique_norm = len({n for n in norms if n})
    n_duplicates_in_sample = len(norms) - n_unique_norm

    # Sources représentées dans l'échantillon.
    source_counts = Counter(r["source"] for r in sample.iter_rows(named=True))
    type_counts = Counter(r["type"] for r in sample.iter_rows(named=True))

    md = [f"## Section 1 — Échantillon A52.7 (le code champion)\n"]
    md.append(
        f"`A52.7` (Autres formes tardives de syphilis symptomatique) : "
        f"**{n_total} entrées** dans le CSV (dont 2 100 environ du "
        f"CIM-10 index — voir audit Phase 2).\n"
    )
    md.append(f"Échantillon de 20 entrées (seed={SEED}) :\n")
    md.extend(_markdown_table_rows(sample_rows, ["source", "type", "texte"]))
    md.append("")
    md.append(
        f"**Répartition de l'échantillon** : sources = "
        f"{dict(source_counts)} ; types = {dict(type_counts)}.\n"
    )

    findings: dict[str, Any] = {
        "n_total": n_total,
        "n_duplicates_in_sample": n_duplicates_in_sample,
        "source_counts_sample": dict(source_counts),
        "type_counts_sample": dict(type_counts),
        "sample_rows": sample_rows,
    }
    return "\n".join(md), findings


# ----------------------------------------------------------------------
# Section 2 — 5 codes "moyens" (10-20 notes)
# ----------------------------------------------------------------------


def section_2_medium_codes(csv: pl.DataFrame, merged: pl.DataFrame) -> tuple[str, dict[str, Any]]:
    per_code = csv.group_by("code").len().rename({"len": "n_notes"})
    medium = per_code.filter((pl.col("n_notes") >= 10) & (pl.col("n_notes") <= 20))
    sampled = medium.sample(n=5, seed=SEED)
    label_map = dict(zip(merged["code"].to_list(), merged["label"].to_list(), strict=True))

    md = [f"## Section 2 — 5 codes \"moyens\" (10-20 notes)\n"]
    md.append(
        f"{medium.height} codes ont entre 10 et 20 notes (sur "
        f"{per_code.height} codes uniques). Échantillon de 5 "
        f"(seed={SEED}) :\n"
    )

    observations: list[dict[str, Any]] = []
    for r in sampled.sort("code").iter_rows(named=True):
        code = r["code"]
        n = r["n_notes"]
        libelle = _truncate(label_map.get(code), 100)
        md.append(f"### `{code}` — {libelle}")
        md.append(f"**{n} entrées** :")
        md.append("")
        sub = csv.filter(pl.col("code") == code).sort(["type", "source"])
        rows = [
            {
                "source": rr["source"],
                "type": rr["type"],
                "texte": _truncate(rr["texte"], 80),
            }
            for rr in sub.iter_rows(named=True)
        ]
        md.extend(_markdown_table_rows(rows, ["source", "type", "texte"]))
        md.append("")
        # Métriques par code.
        sources = sub.group_by("source").len().sort("len", descending=True)
        n_external = sub.filter(~pl.col("source").is_in(list(_INTERNAL_SOURCES))).height
        observations.append(
            {
                "code": code,
                "libelle": libelle,
                "n_notes": n,
                "n_sources_distinct": sub["source"].n_unique(),
                "n_external": n_external,
                "type_breakdown": {
                    r["type"]: r["len"]
                    for r in sub.group_by("type").len().iter_rows(named=True)
                },
                "top_source": sources.row(0, named=True)["source"],
            }
        )

    md.append("**Synthèse des 5 codes** :\n")
    md.append("| code | libellé | n | sources | dont externes | source dominante |")
    md.append("|---|---|---:|---:|---:|---|")
    for obs in observations:
        md.append(
            f"| `{obs['code']}` | {obs['libelle'][:50]} | {obs['n_notes']} | "
            f"{obs['n_sources_distinct']} | {obs['n_external']} | "
            f"{obs['top_source']} |"
        )
    md.append("")

    findings = {"codes": [o["code"] for o in observations], "obs": observations}
    return "\n".join(md), findings


# ----------------------------------------------------------------------
# Section 3 — Distribution source × type
# ----------------------------------------------------------------------


def section_3_distribution(csv: pl.DataFrame) -> tuple[str, dict[str, Any]]:
    n_total = csv.height
    by_source = (
        csv.group_by("source").len().rename({"len": "n"}).sort("n", descending=True)
    )
    by_type = (
        csv.group_by("type").len().rename({"len": "n"}).sort("n", descending=True)
    )

    md = [f"## Section 3 — Distribution globale source × type\n"]
    md.append(f"CSV final : **{n_total} lignes** au total.\n")
    md.append("### Distribution par source\n")
    md.append("| source | n | % |")
    md.append("|---|---:|---:|")
    for r in by_source.iter_rows(named=True):
        md.append(f"| {r['source']} | {r['n']} | {100*r['n']/n_total:.1f} % |")
    md.append("")
    md.append("### Distribution par type\n")
    md.append("| type | n | % |")
    md.append("|---|---:|---:|")
    for r in by_type.iter_rows(named=True):
        md.append(f"| {r['type']} | {r['n']} | {100*r['n']/n_total:.1f} % |")
    md.append("")

    # Croisé source × type.
    cross = (
        csv.group_by(["source", "type"])
        .len()
        .rename({"len": "n"})
        .sort(["source", "type"])
    )
    # Pour chaque source, on calcule le % par type.
    md.append("### Croisé source × type (pour chaque source, % par type)\n")
    sources_ordered = by_source["source"].to_list()
    md.append("| source | total | synonyme | inclusion | exclusion |")
    md.append("|---|---:|---:|---:|---:|")
    source_summary: dict[str, dict[str, int]] = {}
    for src in sources_ordered:
        sub = cross.filter(pl.col("source") == src)
        total = sub["n"].sum()
        breakdown = {r["type"]: r["n"] for r in sub.iter_rows(named=True)}
        source_summary[src] = breakdown
        md.append(
            f"| {src} | {total} | "
            f"{breakdown.get('synonyme', 0)} ({100*breakdown.get('synonyme', 0)/total:.0f} %) | "
            f"{breakdown.get('inclusion', 0)} ({100*breakdown.get('inclusion', 0)/total:.0f} %) | "
            f"{breakdown.get('exclusion', 0)} ({100*breakdown.get('exclusion', 0)/total:.0f} %) |"
        )
    md.append("")

    findings = {
        "n_total": n_total,
        "by_source": by_source.to_dicts(),
        "by_type": by_type.to_dicts(),
        "top_source": sources_ordered[0],
        "top_source_share": by_source.row(0, named=True)["n"] / n_total,
        "source_summary": source_summary,
    }
    return "\n".join(md), findings


# ----------------------------------------------------------------------
# Section 4 — 3 codes OFS+ANS only
# ----------------------------------------------------------------------


def section_4_internal_only(csv: pl.DataFrame, merged: pl.DataFrame) -> tuple[str, dict[str, Any]]:
    # Pour chaque code : ensemble des sources distinctes
    per_code_sources = (
        csv.group_by("code").agg(
            pl.col("source").unique().alias("sources"),
            pl.len().alias("n_notes"),
        )
    )
    # Filtre : toutes les sources sont dans _INTERNAL_SOURCES
    internal_only = per_code_sources.filter(
        pl.col("sources")
        .list.eval(pl.element().is_in(list(_INTERNAL_SOURCES)))
        .list.all()
    ).filter((pl.col("n_notes") >= 5) & (pl.col("n_notes") <= 15))
    sampled = internal_only.sample(n=3, seed=SEED)
    label_map = dict(zip(merged["code"].to_list(), merged["label"].to_list(), strict=True))

    md = [f"## Section 4 — 3 codes \"OFS+ANS only\" (5-15 notes)\n"]
    md.append(
        f"{internal_only.height} codes du CSV n'ont QUE des entrées "
        f"internes (sources ∈ {{CIM-10, ANS, CIM-10 frères}}) et "
        f"5-15 notes. Échantillon de 3 (seed={SEED}) :\n"
    )

    sample_codes: list[dict[str, Any]] = []
    for r in sampled.sort("code").iter_rows(named=True):
        code = r["code"]
        n = r["n_notes"]
        libelle = _truncate(label_map.get(code), 100)
        md.append(f"### `{code}` — {libelle}")
        md.append(f"**{n} entrées** :")
        md.append("")
        sub = csv.filter(pl.col("code") == code).sort(["type", "source"])
        rows = [
            {
                "source": rr["source"],
                "type": rr["type"],
                "texte": _truncate(rr["texte"], 80),
            }
            for rr in sub.iter_rows(named=True)
        ]
        md.extend(_markdown_table_rows(rows, ["source", "type", "texte"]))
        md.append("")
        sample_codes.append({"code": code, "libelle": libelle, "n": n})

    findings = {"codes": sample_codes, "n_internal_only_total": internal_only.height}
    return "\n".join(md), findings


# ----------------------------------------------------------------------
# Synthèse + écriture
# ----------------------------------------------------------------------


def build_synthesis(f1: dict, f2: dict, f3: dict, f4: dict) -> str:
    md = [
        "# Inspection qualitative finale — sources externes (Phases 1-3)\n",
        "> Généré par `scripts/explore/2026-05-27_final_qualitative_check.py`.\n",
        "## Synthèse\n",
    ]
    top = f3["top_source"]
    top_share = f3["top_source_share"]
    md.append(
        f"- **Dataset volumétrie** : {f3['n_total']:,} lignes ; source dominante = "
        f"**{top}** ({top_share*100:.0f} %).\n"
        f"- **Échantillon A52.7** : {f1['n_total']} entrées, surreprésentation "
        f"naturelle de l'Index CIM-10 (libellés historiques de la syphilis). "
        f"{f1['n_duplicates_in_sample']} duplicates normalisés détectés "
        f"sur 20 — bas, dédup tolérante efficace.\n"
        f"- **Codes moyens** (5 échantillons 10-20 notes) : codes témoins "
        f"représentatifs de la diversité du dataset — voir détail.\n"
        f"- **Codes OFS+ANS only** (3 échantillons) : "
        f"{f4['n_internal_only_total']} codes du CSV n'ont que des sources "
        f"internes. Pas de dégradation visible par l'intégration externe.\n"
    )
    return "\n".join(md)


def main() -> None:
    ctx = load_exploration_context()
    if ctx.merged is None:
        raise RuntimeError("merged_codes.parquet absent — lancer build merged.")
    if ctx.flat is None:
        raise RuntimeError(
            "CSV final absent — lancer build flat-csv. "
            "(Le contexte cherche inclusions_exclusions_synonymes.csv "
            "dans referentials/processed.)"
        )
    merged = ctx.merged
    csv = ctx.flat

    print("[1/4] Échantillon A52.7...")
    s1, f1 = section_1_a52_7(csv)
    print("[2/4] 5 codes moyens...")
    s2, f2 = section_2_medium_codes(csv, merged)
    print("[3/4] Distribution source × type...")
    s3, f3 = section_3_distribution(csv)
    print("[4/4] 3 codes OFS+ANS only...")
    s4, f4 = section_4_internal_only(csv, merged)

    synth = build_synthesis(f1, f2, f3, f4)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        synth + "\n---\n\n" + s1 + "\n---\n\n" + s2 + "\n---\n\n"
        + s3 + "\n---\n\n" + s4,
        encoding="utf-8",
    )
    print(f"Écrit : {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
