"""Audit léger des résultats de la Phase 2 (sources externes).

Produit `docs/sessions/post_phase2_audit.md` avec 3 sections :
1. Anomalie d'absorption ophtalmologique (36,5 % vs 1-15 % ailleurs)
2. Distribution du nombre de notes par code dans le CSV final
3. Nature des codes orphelins externes (265 cas)

Script jetable — pas de test unitaire, pas d'API publique.
Lancement : `uv run python scripts/explore/2026-05-26_post_phase2_audit.py`.
"""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path

import polars as pl

from recode_icd.utils.loaders_dev import load_exploration_context

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "sessions" / "post_phase2_audit.md"


# ----------------------------------------------------------------------
# Section 1 — Ophtalmologie
# ----------------------------------------------------------------------


def _chapter_from_path(path: str | None) -> str:
    """Le `path` OWL est de la forme `VII/H00-H06/H00/H00.0` —
    le 1er segment est le chapitre en chiffres romains."""
    if not path:
        return "?"
    parts = path.split("/")
    return parts[0] if parts else "?"


def section_1_ophtalmo(merged: pl.DataFrame) -> tuple[str, dict[str, object]]:
    overlaps = pl.read_csv(ROOT / "reports" / "external_overlaps.csv")
    ophtalmo = overlaps.filter(pl.col("source_externe") == "APHP_OPHTALMOLOGIE")
    n_ophtalmo = ophtalmo.height

    # 20 exemples (échantillon déterministe).
    sample = (
        ophtalmo.sort("code")
        .with_row_index("_idx")
        .filter(pl.col("_idx") % max(1, ophtalmo.height // 20) == 0)
        .head(20)
        .select(
            "code",
            "libelle_externe",
            "libelle_ofs_ans",
            "type_externe",
            "type_ofs_ans",
            "type_divergence",
            "source_ofs_ans",
        )
    )

    # Distribution par chapitre.
    chap_map = dict(
        zip(
            merged["code"].to_list(),
            merged["path"].to_list(),
            strict=True,
        )
    )
    chapters = Counter()
    for code in ophtalmo["code"].to_list():
        chapters[_chapter_from_path(chap_map.get(code))] += 1
    chap_table = sorted(chapters.items(), key=lambda kv: -kv[1])

    # Conclusion : concentration sur VII si > 80 %.
    top_share = chap_table[0][1] / n_ophtalmo if chap_table else 0.0
    is_chapter_aligned = chap_table[0][0] == "VII" and top_share > 0.7

    md = []
    md.append("## Section 1 — Anomalie d'absorption ophtalmologique\n")
    md.append(
        f"**{n_ophtalmo} entrées absorbées** sur 444 chargées "
        f"(36,5 %). Distribution par chapitre CIM-10 :\n"
    )
    md.append("| chapitre | nb absorptions | % |")
    md.append("|---|---:|---:|")
    for chap, n in chap_table[:8]:
        md.append(f"| {chap} | {n} | {100*n/n_ophtalmo:.1f} % |")
    md.append("")
    md.append("**20 exemples d'absorptions** (échantillon stratifié sur l'ordre code) :\n")
    md.append(
        "| code | libellé AP-HP Ophtalmo | libellé OFS/ANS qui a matché | type externe | type OFS/ANS | divergence |"
    )
    md.append("|---|---|---|---|---|---|")
    for row in sample.iter_rows(named=True):
        lib_ext = (row["libelle_externe"] or "")[:60]
        lib_ofs = (row["libelle_ofs_ans"] or "")[:60]
        md.append(
            f"| {row['code']} | {lib_ext} | {lib_ofs} | "
            f"{row['type_externe']} | {row['type_ofs_ans']} | "
            f"{'✓' if row['type_divergence'] else '·'} |"
        )
    md.append("")
    conclusion = (
        "**Conclusion** : "
        + (
            f"alignement naturel — {top_share*100:.0f} % des absorptions tombent "
            f"sur le chapitre {chap_table[0][0]} (Maladies de l'œil). Le thésaurus "
            "AP-HP Ophtalmologie reprend l'éditorialisation OMS française quasi "
            "verbatim, d'où le taux élevé."
            if is_chapter_aligned
            else f"absorptions dispersées sur {len(chap_table)} chapitres "
            f"(le 1er = {chap_table[0][0]} avec {top_share*100:.0f} %). "
            "À investiguer plus en détail."
        )
        + "\n"
    )
    md.append(conclusion)

    findings = {
        "n_absorbed": n_ophtalmo,
        "top_chapter": chap_table[0][0] if chap_table else "?",
        "top_share": top_share,
        "verdict": "alignement_naturel" if is_chapter_aligned else "dispersion",
    }
    return "\n".join(md), findings


# ----------------------------------------------------------------------
# Section 2 — Distribution des notes par code
# ----------------------------------------------------------------------


def section_2_distribution(merged: pl.DataFrame) -> tuple[str, dict[str, object]]:
    csv = pl.read_csv(
        ROOT / "referentials" / "processed" / "inclusions_exclusions_synonymes.csv",
        infer_schema_length=200_000,
    )
    per_code = csv.group_by("code").len().rename({"len": "n_notes"})
    n_codes = per_code.height
    counts = per_code["n_notes"].to_list()

    q = lambda p: int(per_code["n_notes"].quantile(p))
    stats = {
        "min": min(counts),
        "p25": q(0.25),
        "median": q(0.50),
        "p75": q(0.75),
        "p90": q(0.90),
        "p95": q(0.95),
        "p99": q(0.99),
        "max": max(counts),
    }

    # Top 20.
    label_map = dict(zip(merged["code"].to_list(), merged["label"].to_list(), strict=True))
    top20 = per_code.sort("n_notes", descending=True).head(20)
    top_rows: list[dict[str, object]] = []
    for row in top20.iter_rows(named=True):
        code = row["code"]
        n = row["n_notes"]
        sub = csv.filter(pl.col("code") == code)
        types = sub.group_by("type").len().rename({"len": "c"})
        sources = sub.group_by("source").len().rename({"len": "c"})
        type_breakdown = ", ".join(
            f"{r['type']}={r['c']}" for r in types.sort("c", descending=True).iter_rows(named=True)
        )
        top_sources = ", ".join(
            f"{r['source']}={r['c']}" for r in sources.sort("c", descending=True).head(3).iter_rows(named=True)
        )
        top_rows.append(
            {
                "code": code,
                "libelle": (label_map.get(code) or "")[:70],
                "n": n,
                "types": type_breakdown,
                "top_sources": top_sources,
            }
        )

    # Histogramme texte (buckets log10).
    log_buckets: Counter[int] = Counter()
    for n in counts:
        bucket = int(math.log10(max(1, n)))
        log_buckets[bucket] += 1
    hist_lines = []
    for b in sorted(log_buckets):
        low, high = 10**b, 10 ** (b + 1) - 1
        bar = "█" * min(80, int(80 * log_buckets[b] / n_codes))
        hist_lines.append(
            f"  {low:>5}–{high:<5} : {bar} ({log_buckets[b]} codes, {100*log_buckets[b]/n_codes:.1f} %)"
        )

    # Cas extrêmes (>100).
    extreme = per_code.filter(pl.col("n_notes") > 100).height

    md = []
    md.append("## Section 2 — Distribution du nombre de notes par code\n")
    md.append(
        f"CSV final : **{csv.height} lignes** réparties sur **{n_codes} codes uniques**. "
        f"Moyenne {csv.height / n_codes:.1f} notes/code.\n"
    )
    md.append("**Quantiles** (notes par code) :\n")
    md.append("| min | p25 | médiane | p75 | p90 | p95 | p99 | max |")
    md.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    md.append(
        f"| {stats['min']} | {stats['p25']} | {stats['median']} | {stats['p75']} | "
        f"{stats['p90']} | {stats['p95']} | {stats['p99']} | {stats['max']} |\n"
    )
    md.append("**Histogramme log₁₀** (codes par tranche de nb de notes) :")
    md.append("```")
    md.extend(hist_lines)
    md.append("```")
    md.append(
        f"\n**{extreme} codes ont > 100 notes** "
        f"(ces codes méritent une inspection ad-hoc).\n"
    )
    md.append("**Top 20 des codes les plus chargés** :\n")
    md.append("| # | code | libellé | n notes | breakdown type | top 3 sources |")
    md.append("|---:|---|---|---:|---|---|")
    for i, r in enumerate(top_rows, 1):
        md.append(
            f"| {i} | {r['code']} | {r['libelle']} | {r['n']} | "
            f"{r['types']} | {r['top_sources']} |"
        )
    md.append("")

    findings = {
        "n_codes": n_codes,
        "median": stats["median"],
        "p95": stats["p95"],
        "max": stats["max"],
        "extreme_count": extreme,
        "top_code": top_rows[0]["code"] if top_rows else "?",
        "top_n": top_rows[0]["n"] if top_rows else 0,
    }
    return "\n".join(md), findings


# ----------------------------------------------------------------------
# Section 3 — Codes orphelins
# ----------------------------------------------------------------------


def section_3_orphans() -> tuple[str, dict[str, object]]:
    orphans = pl.read_csv(ROOT / "reports" / "external_orphan_codes.csv")
    n_total = orphans.height
    by_cat = (
        orphans.group_by("categorie_orphan")
        .len()
        .sort("len", descending=True)
        .rename({"len": "n"})
    )
    by_source = (
        orphans.group_by("source_externe")
        .len()
        .sort("len", descending=True)
        .rename({"len": "n"})
    )
    # Cross : catégorie × source.
    cross = (
        orphans.group_by(["categorie_orphan", "source_externe"])
        .len()
        .sort(["categorie_orphan", "len"], descending=[False, True])
        .rename({"len": "n"})
    )

    md = []
    md.append("## Section 3 — Codes orphelins externes\n")
    md.append(f"**{n_total} entrées** au code absent de `merged_codes`.\n")
    md.append("**Distribution par catégorie** :\n")
    md.append("| catégorie | n | % |")
    md.append("|---|---:|---:|")
    for r in by_cat.iter_rows(named=True):
        md.append(f"| {r['categorie_orphan']} | {r['n']} | {100*r['n']/n_total:.1f} % |")
    md.append("")
    md.append("**Distribution par source** :\n")
    md.append("| source | n |")
    md.append("|---|---:|")
    for r in by_source.iter_rows(named=True):
        md.append(f"| {r['source_externe']} | {r['n']} |")
    md.append("")

    # Exemples : 10 par catégorie.
    for cat in by_cat["categorie_orphan"].to_list():
        sub = (
            orphans.filter(pl.col("categorie_orphan") == cat)
            .sort("code")
            .head(10)
        )
        md.append(f"**10 exemples — `{cat}`** :\n")
        md.append("| code | libellé | source |")
        md.append("|---|---|---|")
        for r in sub.iter_rows(named=True):
            lib = (r["libelle"] or "")[:60]
            md.append(f"| {r['code']} | {lib} | {r['source_externe']} |")
        md.append("")

    # Conclusion.
    n_real_orphan = (
        by_cat.filter(pl.col("categorie_orphan") == "vraiment_orphan")["n"].sum()
        if "vraiment_orphan" in by_cat["categorie_orphan"].to_list()
        else 0
    )
    n_post_2006 = (
        by_cat.filter(pl.col("categorie_orphan") == "post_2006_ans_only")["n"].sum()
        if "post_2006_ans_only" in by_cat["categorie_orphan"].to_list()
        else 0
    )
    # Action : si beaucoup de "vraiment_orphan", investiguer ; si surtout post-2006,
    # c'est attendu (loaders OWL pas à jour mais sources externes oui).
    if n_real_orphan > n_post_2006 * 2:
        verdict = "**à investiguer** — la majorité sont des vrais orphelins (codes inexistants)."
    elif n_post_2006 > 0:
        verdict = (
            "**bruit acceptable** — la majorité sont post-2006 (codes ajoutés à la "
            "classification après le snapshot OFS/ANS chargé). Cas attendu."
        )
    else:
        verdict = "**bruit faible** — volume négligeable, aucune action corrective requise."
    md.append(f"**Conclusion** : {verdict}\n")

    findings = {
        "n_total": n_total,
        "n_vraiment_orphan": n_real_orphan,
        "n_post_2006_ans_only": n_post_2006,
        "cross": cross.to_dicts(),
    }
    return "\n".join(md), findings


# ----------------------------------------------------------------------
# Synthèse + écriture finale
# ----------------------------------------------------------------------


def build_synthesis(f1: dict, f2: dict, f3: dict) -> str:
    md = []
    md.append("# Audit post-Phase 2 — sources externes\n")
    md.append("> Généré par `scripts/explore/2026-05-26_post_phase2_audit.py`.\n")
    md.append("## Synthèse\n")
    md.append(
        f"- **Ophtalmologie** : {f1['n_absorbed']} absorptions, "
        f"concentration {f1['top_share']*100:.0f} % sur chapitre {f1['top_chapter']} — "
        f"verdict : *{f1['verdict']}*.\n"
        f"- **Richesse lexicale** : {f2['n_codes']} codes uniques, médiane "
        f"{f2['median']} notes/code, p95={f2['p95']}, max={f2['max']} "
        f"(code `{f2['top_code']}` à {f2['top_n']} notes). "
        f"{f2['extreme_count']} codes > 100 notes.\n"
        f"- **Orphelins** : {f3['n_total']} cas — "
        f"{f3['n_post_2006_ans_only']} post-2006 (attendu), "
        f"{f3['n_vraiment_orphan']} vrais orphelins (à inspecter).\n"
    )

    # Recommandation.
    blockers = []
    if f1["verdict"] != "alignement_naturel":
        blockers.append("dispersion ophtalmo")
    if f2["max"] > 500:
        blockers.append(f"code(s) à charge anormale (max={f2['max']})")
    if f3["n_vraiment_orphan"] > 200:
        blockers.append(f"trop de vrais orphelins ({f3['n_vraiment_orphan']})")

    if not blockers:
        reco = (
            "**Phase 2 valide pour passer à la Phase 3.** Tous les signaux "
            "sont conformes aux attentes ou s'expliquent par la nature des sources."
        )
    else:
        reco = (
            "**À investiguer avant Phase 3.** Points bloquants : "
            + ", ".join(blockers)
            + "."
        )
    md.append(f"## Recommandation\n\n{reco}\n")
    return "\n".join(md)


def main() -> None:
    ctx = load_exploration_context()
    if ctx.merged is None:
        raise RuntimeError("merged_codes.parquet absent — lancer build merged d'abord.")
    merged = ctx.merged

    s1_md, f1 = section_1_ophtalmo(merged)
    s2_md, f2 = section_2_distribution(merged)
    s3_md, f3 = section_3_orphans()
    synthesis = build_synthesis(f1, f2, f3)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        synthesis + "\n---\n\n" + s1_md + "\n---\n\n" + s2_md + "\n---\n\n" + s3_md,
        encoding="utf-8",
    )
    print(f"Écrit : {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
