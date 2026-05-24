from __future__ import annotations

from pathlib import Path

import polars as pl

from recode_icd._normalize import normalize_column

_SOURCE_CSV_MAP: dict[str, str] = {
    "OFS": "CIM-10",
    "OWL_ANS": "ANS",
    "INDEX_CIM10_VOL3": "CIM-10 index",
    "SYNTHESIZED_SIBLING": "CIM-10 frères",
    "ORPHANET": "ORPHANET",
    "AP_HP": "AP-HP",
}

_TYPE_ORDER: dict[str, int] = {"inclusion": 0, "exclusion": 1, "synonyme": 2}


def _leaf_codes(merged: pl.DataFrame) -> pl.DataFrame:
    return merged.filter(
        (pl.col("type") == "category") & ((pl.col("right") - pl.col("left")) == 1)
    ).select(pl.col("code"), pl.col("label").alias("libelle"))


def _build_inclusions_exclusions(
    propagated: pl.DataFrame, siblings: pl.DataFrame
) -> pl.DataFrame:
    prop = propagated.filter(
        pl.col("note_type").is_in(["inclusion", "exclusion"])
    ).select(
        pl.col("code"),
        pl.col("note_type").alias("type"),
        pl.col("source"),
        pl.col("texte"),
    )
    sib = siblings.select(
        pl.col("code"),
        pl.col("note_type").alias("type"),
        pl.col("source"),
        pl.col("texte"),
    )
    return pl.concat([prop, sib])


def _build_synonymes(owl: pl.DataFrame, ofs: pl.DataFrame) -> pl.DataFrame:
    """Long format synonymes par code, dédup OFS-prio sur texte normalisé.

    Conforme à `docs/source_mapping.md` : priorité OFS pour les synonymes
    (puis ANS en fallback). Dédup sur texte normalisé (lowercase + accents
    + ponctuation) pour éviter que des variantes typographiques génèrent
    deux lignes CSV.
    """
    owl_syn = (
        owl.select(pl.col("code"), pl.col("synonymes").alias("texte"))
        .explode("texte")
        .filter(pl.col("texte").is_not_null())
        .with_columns(pl.lit("OWL_ANS").alias("source"))
    )
    ofs_syn = (
        ofs.with_columns(pl.col("code").str.strip_chars("()").alias("_norm"))
        .select(
            pl.col("_norm").alias("code"),
            pl.col("synonymes").alias("texte"),
        )
        .explode("texte")
        .filter(pl.col("texte").is_not_null())
        .with_columns(pl.lit("OFS").alias("source"))
    )
    return (
        pl.concat([owl_syn, ofs_syn])
        .with_columns(
            normalize_column("texte").alias("_norm_texte"),
            (pl.col("source") == "OFS").alias("_is_ofs"),
        )
        .sort(["_is_ofs", "texte"], descending=[True, False])  # OFS first
        .unique(subset=["code", "_norm_texte"], keep="first")
        .drop("_is_ofs", "_norm_texte")
        .with_columns(pl.lit("synonyme").alias("type"))
        .select("code", "type", "source", "texte")
    )


def build(
    merged: pl.DataFrame,
    propagated: pl.DataFrame,
    siblings: pl.DataFrame,
    owl: pl.DataFrame,
    ofs: pl.DataFrame,
) -> pl.DataFrame:
    leaves = _leaf_codes(merged)
    inex = _build_inclusions_exclusions(propagated, siblings)
    syn = _build_synonymes(owl, ofs)
    long = pl.concat([inex, syn])

    return (
        long.join(leaves, on="code", how="inner")
        .with_columns(
            pl.col("source").replace_strict(_SOURCE_CSV_MAP).alias("source"),
            pl.col("type").replace_strict(_TYPE_ORDER).alias("_type_order"),
        )
        .unique(subset=["code", "type", "source", "texte"])
        .sort(["code", "_type_order", "source", "texte"])
        .select("code", "libelle", "type", "source", "texte")
    )


def to_csv(
    merged_path: Path,
    propagated_path: Path,
    siblings_path: Path,
    owl_path: Path,
    ofs_path: Path,
    output_path: Path,
) -> Path:
    merged = pl.read_parquet(merged_path)
    propagated = pl.read_parquet(propagated_path)
    siblings = pl.read_parquet(siblings_path)
    owl = pl.read_parquet(owl_path)
    ofs = pl.read_parquet(ofs_path)

    csv_df = build(merged, propagated, siblings, owl, ofs)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    csv_df.write_csv(output_path)
    return output_path
