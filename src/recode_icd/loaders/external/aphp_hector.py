"""Loader pour les feuilles AP-HP du fichier HECTOR.

Le classeur `data/CIM_APHP_2019/Dictionnaire_Hector_MAJ062019.xlsx`
contient 13 feuilles. 9 d'entre elles sont des thésaurus métiers
(Dermatologie, Endocrinologie, ...) — elles partagent strictement
le même schéma 4 colonnes que la feuille "Cim Alphabétique" (Index
CIM-10 vol3). Cf `docs/source_mapping.md` §"Schéma uniforme des
feuilles HECTOR".

Toutes les entrées sont émises avec `type=synonyme` et un `source`
distinct par spécialité (cf `APHP_SHEET_TO_SOURCE` dans
`_constants.py`). Les feuilles "Cim Analytique", "Orphanet" et
"Thesam" sont exclues par choix de design (cf
`docs/external_sources_inventory.md`).
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
from recode_icd.loaders.external._constants import APHP_SHEET_TO_SOURCE
from recode_icd.loaders.external._schemas import ExternalSourceSchema

log = logging.getLogger(__name__)


def _load_hector_sheet(
    xlsx_path: Path,
    sheet_name: str,
    source_label: str,
    note_type: str = "synonyme",
) -> pl.DataFrame:
    """Charge une feuille du classeur HECTOR et la transforme en
    DataFrame uniforme aux 5 colonnes
    `(code, libelle, type, source, metadata)`.

    Helper utilisé à la fois par `load_aphp_hector` (chaque
    spécialité) et par `load_index_cim10` (feuille "Cim Alphabétique").

    Args :
        xlsx_path : chemin vers le classeur HECTOR.
        sheet_name : nom EXACT de la feuille (clé canonique).
        source_label : valeur d'enum NoteSource à affecter à toutes
            les lignes.
        note_type : "synonyme" (défaut) ou "inclusion".

    Returns :
        DataFrame validé par `ExternalSourceSchema`. Le `metadata` est
        un Struct `{sheet_name, sheet_label}` où `sheet_label` est la
        valeur observée en colonne 2 du fichier (peut diverger du
        nom de feuille — cf cas Endocrinologie).
    """
    df = pl.read_excel(xlsx_path, sheet_name=sheet_name)
    cols = df.columns
    if len(cols) < 4:
        raise ValueError(
            f"Feuille HECTOR '{sheet_name}' inattendue : {len(cols)} "
            f"colonnes au lieu de 4. Colonnes : {cols}"
        )

    df = df.rename(
        {cols[0]: "libelle", cols[1]: "_sheet_label", cols[2]: "code_raw",
         cols[3]: "_flag"}
    )

    # `sheet_label` constant par feuille — on prend la 1re valeur
    # rencontrée pour la trace metadata. Si la colonne est entièrement
    # null (cas dégénéré), on utilise le nom de la feuille en fallback.
    sheet_label_values = df["_sheet_label"].drop_nulls().to_list()
    sheet_label = sheet_label_values[0] if sheet_label_values else sheet_name

    df = df.with_columns(
        pl.col("code_raw")
        .map_elements(normalize_compact_code, return_dtype=pl.String)
        .alias("code"),
    )

    n_unparseable = df.filter(pl.col("code").is_null()).height
    if n_unparseable:
        log.info(
            "%s : %d lignes au code non parseable (filtrées) — "
            "majoritairement 'nocode' (renvois index)",
            sheet_name,
            n_unparseable,
        )

    df = (
        df.filter(pl.col("code").is_not_null())
        .filter(pl.col("libelle").is_not_null())
        .filter(pl.col("libelle").str.strip_chars().str.len_chars() > 0)
        # Validation finale du format standard (un compact à 7+ chiffres
        # ne devrait pas exister, mais on garantit).
        .filter(pl.col("code").str.contains(_STANDARD_CODE_RE.pattern))
    )

    # Déduplication tolérante intra-feuille sur (code, libellé norm).
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
        pl.lit(note_type).alias("type"),
        pl.lit(source_label).alias("source"),
        pl.struct(
            pl.lit(sheet_name).alias("sheet_name"),
            pl.lit(sheet_label).alias("sheet_label"),
        ).alias("metadata"),
    ).sort(["code", "libelle"])

    ExternalSourceSchema.validate(df)
    return df


def load_aphp_hector(xlsx_path: Path | str) -> pl.DataFrame:
    """Charge les 9 feuilles métier AP-HP du classeur HECTOR et les
    concatène en un seul DataFrame au schéma uniforme.

    Chaque ligne porte un `source` distinct par spécialité (ex
    `APHP_DERMATOLOGIE`, `APHP_NEPHROLOGIE`, ...). La feuille "Cim
    Alphabétique" du même fichier n'est PAS chargée ici (cf
    `loaders.external.index_cim10.load_index_cim10`).

    Args :
        xlsx_path : chemin du fichier
            `Dictionnaire_Hector_MAJ062019.xlsx`.

    Returns :
        DataFrame `(code, libelle, type, source, metadata)` validé,
        avec une ligne par paire (code, libellé) unique au sein de
        chaque feuille. `type` est toujours "synonyme".
    """
    xlsx_path = Path(xlsx_path)
    frames = [
        _load_hector_sheet(xlsx_path, sheet, source_label)
        for sheet, source_label in APHP_SHEET_TO_SOURCE.items()
    ]
    result = pl.concat(frames)
    ExternalSourceSchema.validate(result)
    return result
