"""Loader pour le dictionnaire CepiDc 2015.

Le CepiDc (Centre d'épidémiologie sur les causes médicales de décès)
maintient un dictionnaire de formulations cliniques utilisées sur les
certificats de décès — source de formulations *vie réelle* rédigées
par des médecins.

Fichier source : `data/CIM_CEPIDC_2015/CepiDc_Dictionnaire2015.csv`
(séparateur `;`, utf-8). Colonnes utiles : `DiagnosisText` et `Icd1`.
Le code Icd1 est au format compact (`A181`, `R51`) — converti en
format standard (`A18.1`, `R51`) via `normalize_compact_code`.

Toutes les entrées sortent en `type=synonyme`, `source=CEPIDC_2015`.
La dédup intra-source (tolérante) élimine les doublons stricts ;
la dédup inter-sources (contre OFS/ANS/autres externes) est gérée
par `merge_external.merge_external_sources`.
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

from recode_icd._normalize import (
    _STANDARD_CODE_RE,
    normalize_compact_code,
    normalize_for_match,
)
from recode_icd.loaders.external._constants import CEPIDC_SOURCE
from recode_icd.loaders.external._schemas import ExternalSourceSchema

log = logging.getLogger(__name__)

_VERSION_YEAR = "2015"


def load_cepidc(csv_path: Path | str) -> pl.DataFrame:
    """Charge le dictionnaire CepiDc 2015.

    Toutes les entrées sortent en `type=synonyme`, `source=CEPIDC_2015`.
    Les entrées au `Icd1` null ou au code non parseable sont filtrées
    avec log info.

    Args :
        csv_path : chemin vers le fichier
            `CepiDc_Dictionnaire2015.csv` (séparateur `;`).

    Returns :
        DataFrame `(code, libelle, type, source, metadata)` validé.
        `metadata` est un Struct `{source_file, version_year}`.
    """
    csv_path = Path(csv_path)
    df = pl.read_csv(
        csv_path,
        separator=";",
        encoding="utf8",
        columns=["DiagnosisText", "Icd1"],
        infer_schema_length=0,
    )

    df = df.rename({"DiagnosisText": "libelle", "Icd1": "code_raw"})

    n_total = df.height
    df = df.filter(pl.col("code_raw").is_not_null())
    n_null_code = n_total - df.height
    if n_null_code:
        log.info(
            "CepiDc : %d lignes au Icd1 null (filtrées)",
            n_null_code,
        )

    df = df.with_columns(
        pl.col("code_raw")
        .map_elements(normalize_compact_code, return_dtype=pl.String)
        .alias("code")
    )

    n_unparseable = df.filter(pl.col("code").is_null()).height
    if n_unparseable:
        log.info(
            "CepiDc : %d lignes au code non parseable (filtrées)",
            n_unparseable,
        )

    df = (
        df.filter(pl.col("code").is_not_null())
        .filter(pl.col("libelle").is_not_null())
        .filter(pl.col("libelle").str.strip_chars().str.len_chars() > 0)
        .filter(pl.col("code").str.contains(_STANDARD_CODE_RE.pattern))
    )

    df = (
        df.with_columns(
            pl.col("libelle")
            .map_elements(normalize_for_match, return_dtype=pl.String)
            .alias("_libelle_norm")
        )
        .unique(subset=["code", "_libelle_norm"], keep="first")
        .drop("_libelle_norm")
    )

    df = df.select(
        pl.col("code"),
        pl.col("libelle").str.strip_chars().alias("libelle"),
        pl.lit("synonyme").alias("type"),
        pl.lit(CEPIDC_SOURCE).alias("source"),
        pl.struct(
            pl.lit(csv_path.name).alias("source_file"),
            pl.lit(_VERSION_YEAR).alias("version_year"),
        ).alias("metadata"),
    ).sort(["code", "libelle"])

    ExternalSourceSchema.validate(df)
    return df
