from __future__ import annotations

from pathlib import Path

import polars as pl

from recode_icd.loaders.schemas import PropagatedNotesSchema

# Mapping interne : colonne texte → (note_type exporté, colonne source parallèle ou None).
# Quand `per_source_col` est None, la source est constante (notes_editorial = OFS seulement).
_NOTE_COLUMNS: dict[str, tuple[str, str | None]] = {
    "inclusions": ("inclusion", "inclusions_per_source"),
    "exclusions": ("exclusion", "exclusions_per_source"),
    "notes_editorial": ("note_editorial", None),
}

_LONG_SCHEMA = {
    "code": pl.String,
    "code_label": pl.String,
    "code_type": pl.String,
    "note_type": pl.String,
    "texte": pl.String,
    "source": pl.String,
    "inherited_from": pl.String,
    "inherited_from_label": pl.String,
    "inherited_from_type": pl.String,
}


def _empty_long() -> pl.DataFrame:
    return pl.DataFrame(schema=_LONG_SCHEMA)


def _build_own_rows(merged: pl.DataFrame) -> pl.DataFrame:
    parts: list[pl.DataFrame] = []
    for col, (note_type, per_source_col) in _NOTE_COLUMNS.items():
        if per_source_col:
            # Explode parallèle texte ↔ source (chaque note préserve sa source).
            own = (
                merged.filter(pl.col(col).list.len() > 0)
                .select(
                    pl.col("code"),
                    pl.col("label").alias("code_label"),
                    pl.col("type").alias("code_type"),
                    pl.lit(note_type).alias("note_type"),
                    pl.col(col).alias("texte"),
                    pl.col(per_source_col).alias("source"),
                )
                .explode(["texte", "source"])
            )
        else:
            # Source constante (OFS pour notes_editorial).
            own = (
                merged.filter(pl.col(col).list.len() > 0)
                .select(
                    pl.col("code"),
                    pl.col("label").alias("code_label"),
                    pl.col("type").alias("code_type"),
                    pl.lit(note_type).alias("note_type"),
                    pl.col(col).alias("texte"),
                    pl.lit("OFS").alias("source"),
                )
                .explode("texte")
            )

        own = own.with_columns(
            pl.lit(None, dtype=pl.String).alias("inherited_from"),
            pl.lit(None, dtype=pl.String).alias("inherited_from_label"),
            pl.lit(None, dtype=pl.String).alias("inherited_from_type"),
        ).select(list(_LONG_SCHEMA.keys()))
        parts.append(own)
    return pl.concat(parts) if parts else _empty_long()


def _build_inherited_rows(merged: pl.DataFrame) -> pl.DataFrame:
    ancestors = (
        merged.with_columns(pl.col("path").str.split("/").alias("_parts"))
        .with_columns(
            pl.col("_parts")
            .list.slice(0, pl.col("_parts").list.len() - 1)
            .alias("ancestors")
        )
        .filter(pl.col("ancestors").list.len() > 0)
        .select(
            pl.col("code"),
            pl.col("label").alias("code_label"),
            pl.col("type").alias("code_type"),
            pl.col("ancestors"),
        )
        .explode("ancestors")
        .rename({"ancestors": "ancestor_code"})
    )

    parts: list[pl.DataFrame] = []
    for col, (note_type, per_source_col) in _NOTE_COLUMNS.items():
        if per_source_col:
            anc_notes = (
                merged.select(
                    pl.col("code").alias("ancestor_code"),
                    pl.col("label").alias("inherited_from_label"),
                    pl.col("type").alias("inherited_from_type"),
                    pl.col(col).alias("texte"),
                    pl.col(per_source_col).alias("source"),
                )
                .filter(pl.col("texte").list.len() > 0)
            )

            joined = (
                ancestors.join(anc_notes, on="ancestor_code")
                .explode(["texte", "source"])
            )
        else:
            anc_notes = (
                merged.select(
                    pl.col("code").alias("ancestor_code"),
                    pl.col("label").alias("inherited_from_label"),
                    pl.col("type").alias("inherited_from_type"),
                    pl.col(col).alias("texte"),
                )
                .filter(pl.col("texte").list.len() > 0)
            )

            joined = (
                ancestors.join(anc_notes, on="ancestor_code")
                .explode("texte")
                .with_columns(pl.lit("OFS").alias("source"))
            )

        joined = joined.select(
            pl.col("code"),
            pl.col("code_label"),
            pl.col("code_type"),
            pl.lit(note_type).alias("note_type"),
            pl.col("texte"),
            pl.col("source"),
            pl.col("ancestor_code").alias("inherited_from"),
            pl.col("inherited_from_label"),
            pl.col("inherited_from_type"),
        )
        parts.append(joined)

    return pl.concat(parts) if parts else _empty_long()


def propagate(merged: pl.DataFrame) -> pl.DataFrame:
    own = _build_own_rows(merged)
    inherited = _build_inherited_rows(merged)
    out = pl.concat([own, inherited]).sort(
        ["code", "note_type", "inherited_from", "texte"], nulls_last=False
    )
    PropagatedNotesSchema.validate(out)
    return out


def to_parquet(merged_path: Path, output_path: Path) -> Path:
    merged = pl.read_parquet(merged_path)
    out = propagate(merged)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.write_parquet(output_path)
    return output_path
