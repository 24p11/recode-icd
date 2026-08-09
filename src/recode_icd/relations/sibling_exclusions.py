from __future__ import annotations

from pathlib import Path

import polars as pl

from recode_icd.loaders.schemas import SiblingExclusionsSchema

# Codes 5-char format X##.8 (exactement — exclut S82.10, B24.+0, etc.)
_DOT8_RE = r"^[A-Z][0-9]{2}\.8$"
# Frères potentiels : 5-char X##.0 à X##.7 (.8 et .9 exclus)
_SIBLING_RE = r"^[A-Z][0-9]{2}\.[0-7]$"


def _is_in_c00_c75(code: pl.Expr) -> pl.Expr:
    # Sémantique différente pour ces codes (lésion à localisations
    # contiguës) — ne pas synthétiser de frères.
    return code.str.starts_with("C") & (code.str.slice(1, 2).cast(pl.Int64) <= 75)


def synthesize(merged: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Retourne (siblings_df, skipped_df)."""
    dot8 = merged.filter(pl.col("code").str.contains(_DOT8_RE)).with_columns(
        pl.col("code").str.slice(0, 3).alias("parent_code")
    )

    is_skip = _is_in_c00_c75(pl.col("code"))
    skipped = (
        dot8.filter(is_skip)
        .select(
            pl.col("code"),
            pl.col("label"),
            pl.lit("C00-C75 contiguous lesion semantics").alias("reason"),
        )
        .sort("code")
    )
    eligible = dot8.filter(~is_skip)

    siblings_pool = (
        merged.filter(pl.col("code").str.contains(_SIBLING_RE))
        .with_columns(pl.col("code").str.slice(0, 3).alias("parent_code"))
        .select(
            pl.col("parent_code"),
            pl.col("code").alias("sibling_code"),
            pl.col("label").alias("sibling_label"),
        )
    )

    out: pl.DataFrame = (
        eligible.select(
            pl.col("code"),
            pl.col("label").alias("code_label"),
            pl.col("parent_code"),
        )
        .join(siblings_pool, on="parent_code")
        .with_columns(
            pl.lit("category").alias("code_type"),
            pl.lit("exclusion").alias("note_type"),
            pl.lit("SYNTHESIZED_SIBLING").alias("source"),
            (pl.col("sibling_label").fill_null("") + " (" + pl.col("sibling_code") + ")").alias(
                "texte"
            ),
        )
        .select(
            "code",
            "code_label",
            "code_type",
            "note_type",
            "texte",
            "source",
            "sibling_code",
            "sibling_label",
        )
        .sort(["code", "sibling_code"])
    )

    SiblingExclusionsSchema.validate(out)
    return out, skipped


def to_parquet_and_report(
    merged_path: Path, output_path: Path, report_path: Path
) -> tuple[Path, Path]:
    merged = pl.read_parquet(merged_path)
    siblings, skipped = synthesize(merged)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    siblings.write_parquet(output_path)
    skipped.write_csv(report_path)
    return output_path, report_path
