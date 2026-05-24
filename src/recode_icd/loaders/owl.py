from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import polars as pl
from smt2parquet import core

from recode_icd.loaders.queries import load_query
from recode_icd.loaders.schemas import DaggerAsteriskSchema, OwlCodesSchema

BASE_URI = "http://data.esante.gouv.fr/atih/cim10"
RDF_FILENAME_PREFIX = "terminologie-cim-10-"
TERMINOLOGY_NAME = "cim10_ans"


def load_codes(rdf_path: Path) -> pl.DataFrame:
    graph = core.load_graph(rdf_path)
    attrs = core.dataframe_from_sparql(graph, load_query("owl_attrs"))
    edges = core.dataframe_from_sparql(graph, load_query("owl_edges"))

    attrs_agg = attrs.group_by("concept").agg(
        pl.col("code").first(),
        pl.col("label").first(),
        pl.col("type").first(),
        pl.col("synonyme").drop_nulls().unique().alias("synonymes"),
        pl.col("inclusion_note").first(),
        pl.col("exclusion_note").drop_nulls().unique().alias("exclusion_notes"),
        pl.col("definition").drop_nulls().unique().alias("definitions"),
        pl.col("scope_note").drop_nulls().unique().alias("scope_notes"),
        pl.col("structured_exclusion")
        .drop_nulls()
        .unique()
        .alias("structured_exclusions"),
    )

    code_of = dict(
        zip(attrs_agg["concept"].to_list(), attrs_agg["code"].to_list(), strict=True)
    )

    nested = core.build_nested_set(edges.iter_rows(), root=BASE_URI, code_of=code_of)

    df: pl.DataFrame = (
        nested.join(attrs_agg, left_on="node", right_on="concept", how="left")
        .select(
            "code",
            "label",
            "type",
            "depth",
            "left",
            "right",
            "path",
            "synonymes",
            "inclusion_note",
            "exclusion_notes",
            "definitions",
            "scope_notes",
            "structured_exclusions",
        )
        .sort("left")
    )

    OwlCodesSchema.validate(df)
    return df


def load_dagger_asterisk(rdf_path: Path) -> pl.DataFrame:
    graph = core.load_graph(rdf_path)
    raw = core.dataframe_from_sparql(graph, load_query("owl_dagger_asterisk"))

    if raw.is_empty():
        df = pl.DataFrame(
            schema={
                "asterisk_code": pl.String,
                "dagger_code": pl.String,
                "evidence": pl.List(pl.String),
                "source": pl.String,
            }
        )
    else:
        df = (
            raw.group_by(["asterisk_code", "dagger_code"])
            .agg(pl.col("evidence").unique().alias("evidence"))
            .with_columns(pl.lit("OWL_ANS").alias("source"))
            .sort(["asterisk_code", "dagger_code"])
        )

    DaggerAsteriskSchema.validate(df)
    return df


def to_parquet(rdf_path: Path, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "terminology": TERMINOLOGY_NAME,
        "version": core.extract_version(rdf_path, RDF_FILENAME_PREFIX),
        "source_file": rdf_path.name,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    codes_path = output_dir / "owl_codes.parquet"
    pairs_path = output_dir / "owl_dagger_asterisk.parquet"
    core.write_parquet_with_metadata(load_codes(rdf_path), codes_path, metadata)
    core.write_parquet_with_metadata(
        load_dagger_asterisk(rdf_path), pairs_path, metadata
    )
    return codes_path, pairs_path
