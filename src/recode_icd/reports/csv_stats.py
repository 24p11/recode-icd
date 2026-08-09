"""Statistiques déterministes sur le CSV maître final.

Produit `reports/csv_stats.md`, un rapport de chiffres bruts (aucune
observation interprétative) référencé par `docs/csv_usage_guide.md`.

Toutes les statistiques sont **pures et déterministes** : mêmes données
→ même sortie. Seule la ligne "généré le" de l'en-tête varie d'un run
à l'autre (paramètre `generated_at`, injectable pour les tests).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import polars as pl

_DEFAULT_CSV = Path("referentials/processed/inclusions_exclusions_synonymes.csv")
_DEFAULT_OUTPUT = Path("reports/csv_stats.md")

# Seuil au-delà duquel un code est listé comme "code-fourre-tout".
_FAT_CODE_THRESHOLD = 100

_TYPES = ("synonyme", "inclusion", "exclusion")


def _int(value: Any) -> int:
    """Cast d'un scalaire polars (type union large) en int. Les agrégats
    de comptes sont toujours non-null dès que le CSV a au moins un code."""
    return int(value)


def compute_csv_stats(df: pl.DataFrame) -> dict[str, Any]:
    """Calcule toutes les statistiques déterministes du CSV final.

    Args:
        df : CSV maître chargé (11 colonnes attendues, dont `code`,
            `libelle`, `type`, `source`, `source_level`).

    Returns:
        dict de stats prêt pour `render_markdown`.
    """
    n_total = df.height
    per_code = df.group_by("code").len().rename({"len": "n_notes"})
    n_codes = per_code.height
    mean_notes = n_total / n_codes if n_codes else 0.0

    # Tri secondaire par nom pour un ordre déterministe en cas d'égalité
    # de count (group_by polars n'est pas stable).
    by_source = (
        df.group_by("source")
        .len()
        .rename({"len": "n"})
        .sort(["n", "source"], descending=[True, False])
    )
    by_type = (
        df.group_by("type").len().rename({"len": "n"}).sort(["n", "type"], descending=[True, False])
    )
    by_level = (
        df.group_by("source_level")
        .len()
        .rename({"len": "n"})
        .sort(["n", "source_level"], descending=[True, False])
    )

    # Croisé source × type : pour chaque source, compte par type.
    cross = df.group_by(["source", "type"]).len().rename({"len": "n"})
    source_cross: list[dict[str, Any]] = []
    for src in by_source["source"].to_list():
        sub = cross.filter(pl.col("source") == src)
        total = int(sub["n"].sum())
        breakdown = {r["type"]: r["n"] for r in sub.iter_rows(named=True)}
        source_cross.append(
            {
                "source": src,
                "total": total,
                **{t: breakdown.get(t, 0) for t in _TYPES},
            }
        )

    # Quantiles du nombre de notes par code. `_int` neutralise le type
    # union large renvoyé par les agrégats polars (les valeurs sont des
    # comptes Int64 non-null dès que le CSV a au moins un code).
    notes = per_code["n_notes"]

    def _q(p: float) -> int:
        return _int(notes.quantile(p))

    quantiles = {
        "min": _int(notes.min()),
        "p25": _q(0.25),
        "median": _q(0.50),
        "p75": _q(0.75),
        "p90": _q(0.90),
        "p95": _q(0.95),
        "p99": _q(0.99),
        "max": _int(notes.max()),
    }

    # Codes au-delà du seuil : (code, libellé, n) triés desc, tiebreak
    # par code pour un ordre déterministe.
    fat = per_code.filter(pl.col("n_notes") > _FAT_CODE_THRESHOLD).sort(
        ["n_notes", "code"], descending=[True, False]
    )
    # Libellé systématique : 1re valeur non-nulle par code dans le CSV.
    labels = df.group_by("code").agg(pl.col("libelle").drop_nulls().first().alias("libelle"))
    fat = fat.join(labels, on="code", how="left")
    fat_codes = [
        {"code": r["code"], "libelle": r["libelle"] or "", "n_notes": r["n_notes"]}
        for r in fat.iter_rows(named=True)
    ]

    return {
        "n_total": n_total,
        "n_codes": n_codes,
        "mean_notes": mean_notes,
        "by_source": by_source.to_dicts(),
        "by_type": by_type.to_dicts(),
        "by_level": by_level.to_dicts(),
        "source_cross": source_cross,
        "quantiles": quantiles,
        "fat_codes": fat_codes,
        "fat_threshold": _FAT_CODE_THRESHOLD,
    }


def _pct(n: int, total: int) -> str:
    return f"{100 * n / total:.1f} %" if total else "0.0 %"


def render_markdown(stats: dict[str, Any], generated_at: str) -> str:
    """Rend les statistiques en markdown. `generated_at` est une chaîne
    (ex `2026-05-28`) — seul élément non déterministe du document."""
    n_total = stats["n_total"]
    lines: list[str] = []
    lines.append("# Statistiques du CSV maître")
    lines.append("")
    lines.append(
        "> Rapport déterministe généré par "
        "`recode_icd.reports.csv_stats.generate_csv_stats` "
        "(commande `recode-icd build stats`). Aucune observation "
        "interprétative — uniquement des chiffres bruts."
    )
    lines.append("")
    lines.append(f"- **Généré le** : {generated_at}")
    lines.append(f"- **Lignes totales** : {n_total}")
    lines.append(f"- **Codes uniques** : {stats['n_codes']}")
    lines.append(f"- **Moyenne notes/code** : {stats['mean_notes']:.1f}")
    lines.append("")

    # Distribution par source.
    lines.append("## Distribution par source")
    lines.append("")
    lines.append("| source | lignes | % |")
    lines.append("|---|---:|---:|")
    for r in stats["by_source"]:
        lines.append(f"| {r['source']} | {r['n']} | {_pct(r['n'], n_total)} |")
    lines.append("")

    # Distribution par type.
    lines.append("## Distribution par type")
    lines.append("")
    lines.append("| type | lignes | % |")
    lines.append("|---|---:|---:|")
    for r in stats["by_type"]:
        lines.append(f"| {r['type']} | {r['n']} | {_pct(r['n'], n_total)} |")
    lines.append("")

    # Croisé source × type.
    lines.append("## Croisé source × type")
    lines.append("")
    lines.append("| source | total | synonyme | inclusion | exclusion |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in stats["source_cross"]:
        tot = r["total"]
        lines.append(
            f"| {r['source']} | {tot} | "
            f"{r['synonyme']} ({_pct(r['synonyme'], tot)}) | "
            f"{r['inclusion']} ({_pct(r['inclusion'], tot)}) | "
            f"{r['exclusion']} ({_pct(r['exclusion'], tot)}) |"
        )
    lines.append("")

    # Distribution par source_level.
    lines.append("## Distribution par source_level")
    lines.append("")
    lines.append("| source_level | lignes | % |")
    lines.append("|---|---:|---:|")
    for r in stats["by_level"]:
        lines.append(f"| {r['source_level']} | {r['n']} | {_pct(r['n'], n_total)} |")
    lines.append("")

    # Quantiles.
    q = stats["quantiles"]
    lines.append("## Quantiles du nombre de notes par code")
    lines.append("")
    lines.append("| min | p25 | médiane | p75 | p90 | p95 | p99 | max |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    lines.append(
        f"| {q['min']} | {q['p25']} | {q['median']} | {q['p75']} | "
        f"{q['p90']} | {q['p95']} | {q['p99']} | {q['max']} |"
    )
    lines.append("")

    # Codes-fourre-tout.
    fat = stats["fat_codes"]
    lines.append(f"## Codes dépassant {stats['fat_threshold']} notes")
    lines.append("")
    lines.append(f"{len(fat)} code(s) concerné(s).")
    lines.append("")
    if fat:
        lines.append("| code | libellé | notes |")
        lines.append("|---|---|---:|")
        for r in fat:
            lines.append(f"| {r['code']} | {r['libelle']} | {r['n_notes']} |")
        lines.append("")

    return "\n".join(lines)


def generate_csv_stats(
    csv_path: Path = _DEFAULT_CSV,
    output_path: Path = _DEFAULT_OUTPUT,
    *,
    generated_at: str | None = None,
) -> Path:
    """Lit le CSV final, calcule les stats, écrit `output_path` en
    markdown. Retourne le chemin écrit."""
    df = pl.read_csv(csv_path, infer_schema_length=200_000)
    stats = compute_csv_stats(df)
    md = render_markdown(stats, generated_at or date.today().isoformat())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    return output_path
