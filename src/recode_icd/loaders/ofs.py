from __future__ import annotations

import io
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
from polars._typing import PolarsDataType
from smt2parquet import core

from recode_icd.loaders.schemas import OfsCodesSchema, OfsDaggerAsteriskSchema

_OFS_SEP = "¦"
_OFS_ENCODING = "iso-8859-1"
_OFS_SEP_SOH = "\x01"
_ROOT_SID = 0

TERMINOLOGY_NAME = "cim10_ofs_2006"

_TYPE_MAP = {
    "C": "chapter",
    "G": "block",
    "U": "block",
    "K": "category",
    "S": "category",
    "D": "category",
}


def _read(
    path: Path,
    dtypes: dict[str, PolarsDataType] | None = None,
    quote_char: str | None = None,
) -> pl.DataFrame:
    """Lecture latin-1 → str → polars (le séparateur ¦ est multi-byte UTF-8,
    refusé par polars 1.40 ; on le substitue par SOH single-byte).

    `quote_char` :
    - `None` par défaut : la plupart des tables OFS contiennent des `"`
      non-échappés dans les libellés (ex. `"mauvais voyages"`), donc
      désactiver le quoting CSV (équivalent du `doublequote=False` legacy
      pandas).
    - `"'"` : pour MEMO.txt qui utilise des apostrophes comme séparateur
      de chaîne CSV avec doublage (`d''origine`) — convention différente
      du reste de la base.
    """
    text = path.read_bytes().decode(_OFS_ENCODING).replace(_OFS_SEP, _OFS_SEP_SOH)
    return pl.read_csv(
        io.StringIO(text),
        separator=_OFS_SEP_SOH,
        has_header=True,
        schema_overrides=dtypes or {},
        infer_schema_length=10_000,
        quote_char=quote_char,
    )


def _read_version(ofs_dir: Path) -> str:
    # version/build sont des chaînes avec zéros préfixes (ex. V2B "004") —
    # forcer pl.String pour empêcher polars de les inférer comme int.
    version_df = _read(
        ofs_dir / "VERSION.txt",
        dtypes={"version": pl.String, "build": pl.String},
    ).filter(pl.col("valid") == 1)
    if version_df.is_empty():
        return "unknown"
    row = version_df.row(0, named=True)
    return f"{row['version']}{row['build']}"


def load_codes(ofs_dir: Path) -> pl.DataFrame:
    master = _read(ofs_dir / "MASTER.txt").filter(pl.col("valid") == 1)
    libelle = _read(ofs_dir / "LIBELLE.txt").filter(pl.col("valid") == 1)

    main_labels = (
        libelle.filter(pl.col("source") == "S")
        .group_by("SID")
        .agg(pl.col("libelle").first().alias("label"))
    )

    descr = _read(ofs_dir / "DESCR.txt")
    synonymes = (
        descr.join(libelle.select(["LID", "libelle"]), on="LID")
        .group_by("SID")
        .agg(pl.col("libelle").drop_nulls().unique().alias("synonymes"))
    )

    include = _read(ofs_dir / "INCLUDE.txt")
    inclusions = (
        include.join(libelle.select(["LID", "libelle"]), on="LID")
        .group_by("SID")
        .agg(pl.col("libelle").drop_nulls().unique().alias("inclusions"))
    )

    exclude = _read(ofs_dir / "EXCLUDE.txt")
    excl_text = (
        exclude.join(libelle.select(["LID", "libelle"]), on="LID")
        .group_by("SID")
        .agg(pl.col("libelle").drop_nulls().unique().alias("exclusions_text"))
    )
    excl_redir = (
        exclude.join(
            master.select(["SID", "code"]).rename(
                {"SID": "excl", "code": "redirect_code"}
            ),
            on="excl",
        )
        .group_by("SID")
        .agg(
            pl.col("redirect_code")
            .drop_nulls()
            .unique()
            .alias("exclusions_redirect")
        )
    )

    note = _read(ofs_dir / "NOTE.txt")
    # MEMO utilise un quoting `'…'` distinct du reste d'OFS (cf. _read).
    memo = _read(ofs_dir / "MEMO.txt", quote_char="'").filter(
        pl.col("valid") == "Yes"
    )
    notes = (
        note.join(memo.select(["MID", "memo"]), on="MID")
        .group_by("SID")
        .agg(pl.col("memo").drop_nulls().unique().alias("notes_editorial"))
    )

    parent_col = (
        pl.when(pl.col("level") == 1)
        .then(pl.lit(_ROOT_SID))
        .when(pl.col("level") == 2)
        .then(pl.col("id1"))
        .when(pl.col("level") == 3)
        .then(pl.col("id2"))
        .when(pl.col("level") == 4)
        .then(pl.col("id3"))
        .when(pl.col("level") == 5)
        .then(pl.col("id4"))
        .when(pl.col("level") == 6)
        .then(pl.col("id5"))
        .when(pl.col("level") == 7)
        .then(pl.col("id6"))
        .otherwise(pl.col("id7"))
    )
    edges = (
        master.with_columns(parent_col.alias("parent_SID"))
        .select(["parent_SID", "SID"])
    )

    code_of = dict(
        zip(master["SID"].to_list(), master["code"].to_list(), strict=True)
    )
    nested = core.build_nested_set(
        edges.iter_rows(),
        root=_ROOT_SID,
        code_of=code_of,
    ).with_columns(pl.col("node").cast(pl.Int64))

    master_typed = master.with_columns(
        pl.col("type").alias("ofs_type"),
        pl.col("type").replace_strict(_TYPE_MAP).alias("type"),
    )

    df: pl.DataFrame = (
        master_typed.join(nested, left_on="SID", right_on="node", how="left")
        .join(main_labels, on="SID", how="left")
        .join(synonymes, on="SID", how="left")
        .join(inclusions, on="SID", how="left")
        .join(excl_text, on="SID", how="left")
        .join(excl_redir, on="SID", how="left")
        .join(notes, on="SID", how="left")
        .select(
            "code",
            "abbrev",
            "label",
            "type",
            "ofs_type",
            "depth",
            "left",
            "right",
            "path",
            "synonymes",
            "inclusions",
            "exclusions_text",
            "exclusions_redirect",
            "notes_editorial",
        )
        .sort("left")
    )

    OfsCodesSchema.validate(df)
    return df


def load_dagger_asterisk(ofs_dir: Path) -> pl.DataFrame:
    master = _read(ofs_dir / "MASTER.txt").filter(pl.col("valid") == 1)
    dagstar = _read(ofs_dir / "DAGSTAR.txt")
    sid_to_code = master.select(["SID", "code"])

    df: pl.DataFrame = (
        dagstar.join(
            sid_to_code.rename({"SID": "SID_start", "code": "start_code"}),
            left_on="SID",
            right_on="SID_start",
        )
        .join(
            sid_to_code.rename({"SID": "SID_end", "code": "end_code"}),
            left_on="assoc",
            right_on="SID_end",
        )
        .with_columns(
            pl.col("plus").cast(pl.Boolean),
            pl.lit("OFS").alias("source"),
        )
        .select("start_code", "end_code", "daget", "plus", "source")
        .sort(["start_code", "end_code"])
    )

    OfsDaggerAsteriskSchema.validate(df)
    return df


def to_parquet(ofs_dir: Path, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "terminology": TERMINOLOGY_NAME,
        "version": _read_version(ofs_dir),
        "source_dir": str(ofs_dir),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    codes_path = output_dir / "ofs_codes.parquet"
    pairs_path = output_dir / "ofs_dagger_asterisk.parquet"
    core.write_parquet_with_metadata(load_codes(ofs_dir), codes_path, metadata)
    core.write_parquet_with_metadata(
        load_dagger_asterisk(ofs_dir), pairs_path, metadata
    )
    return codes_path, pairs_path
