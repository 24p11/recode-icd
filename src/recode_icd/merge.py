from __future__ import annotations

from pathlib import Path

import polars as pl

from recode_icd._normalize import normalize_column
from recode_icd.loaders.schemas import MergedCodesSchema

# Sources possibles dans la colonne `*_source` du Parquet mergé.
# Quand OFS et OWL contribuent tous deux des notes différentes au même
# (code, type), on annote `"OFS+OWL_ANS"` pour signaler la mixité — la
# traçabilité fine est dans `note_merges.csv`.
_SOURCE_NONE = "none"
_SOURCE_OFS = "OFS"
_SOURCE_OWL = "OWL_ANS"
_SOURCE_MIXED = "OFS+OWL_ANS"


def _normalize_ofs(ofs_codes: pl.DataFrame) -> pl.DataFrame:
    """Strip parens du code OFS pour matcher le format OWL (`A00-A09`).

    Cas particulier : OFS encode parfois des "blocs mono-code" `(F99)` au
    niveau bloc + `F99` au niveau catégorie. Strip parens les fait
    collisionner. On dédoublonne en gardant la ligne la plus spécifique
    (catégorie > bloc > chapitre).
    """
    type_priority = pl.col("ofs_type").replace_strict(
        {"D": 0, "S": 1, "K": 2, "U": 3, "G": 4, "C": 5},
        default=99,
    )
    return (
        ofs_codes.with_columns(
            pl.col("code").str.strip_chars("()").alias("code_norm"),
            type_priority.alias("_priority"),
        )
        .sort("_priority")
        .unique(subset="code_norm", keep="first")
        .drop("_priority")
    )


def _explode_ofs_notes(
    ofs: pl.DataFrame, col: str, note_type: str
) -> pl.DataFrame:
    """OFS notes (list[str]) → long format avec (code, type, texte, source='OFS')."""
    return (
        ofs.select(
            pl.col("code"),
            pl.col(col).alias("texte"),
        )
        .filter(pl.col("texte").list.len() > 0)
        .explode("texte")
        .filter(pl.col("texte").is_not_null())
        .with_columns(
            pl.lit(note_type).alias("type"),
            pl.lit(_SOURCE_OFS).alias("source"),
        )
        .select("code", "type", "texte", "source")
    )


def _explode_owl_singleton(
    owl: pl.DataFrame, col: str, note_type: str
) -> pl.DataFrame:
    """OWL singleton string (ex. inclusion_note) → long format."""
    return (
        owl.select(pl.col("code"), pl.col(col).alias("texte"))
        .filter(pl.col("texte").is_not_null())
        .with_columns(
            pl.lit(note_type).alias("type"),
            pl.lit(_SOURCE_OWL).alias("source"),
        )
        .select("code", "type", "texte", "source")
    )


def _explode_owl_list(
    owl: pl.DataFrame, col: str, note_type: str
) -> pl.DataFrame:
    """OWL list (ex. exclusion_notes) → long format."""
    return (
        owl.select(pl.col("code"), pl.col(col).alias("texte"))
        .filter(pl.col("texte").list.len() > 0)
        .explode("texte")
        .filter(pl.col("texte").is_not_null())
        .with_columns(
            pl.lit(note_type).alias("type"),
            pl.lit(_SOURCE_OWL).alias("source"),
        )
        .select("code", "type", "texte", "source")
    )


def _build_notes_long(
    owl_codes: pl.DataFrame, ofs_normalized: pl.DataFrame
) -> pl.DataFrame:
    """Long format toutes notes (inclusions + exclusions), des deux sources, dédoublonnées.

    Dédup OFS-prio sur le texte normalisé : si OFS et OWL ont une note dont
    le texte normalisé est identique, on garde la version OFS.
    """
    all_notes = pl.concat(
        [
            _explode_ofs_notes(ofs_normalized, "ofs_inclusions", "inclusion"),
            _explode_ofs_notes(ofs_normalized, "ofs_exclusions", "exclusion"),
            _explode_owl_singleton(owl_codes, "inclusion_note", "inclusion"),
            _explode_owl_list(owl_codes, "exclusion_notes", "exclusion"),
        ]
    )

    return (
        all_notes.with_columns(
            normalize_column("texte").alias("_norm"),
            (pl.col("source") == _SOURCE_OFS).alias("_is_ofs"),
        )
        .sort(["_is_ofs", "texte"], descending=[True, False])
        .unique(subset=["code", "type", "_norm"], keep="first")
        .drop("_is_ofs", "_norm")
        .sort(["code", "type", "texte"])
    )


def _aggregate_notes(notes_long: pl.DataFrame) -> pl.DataFrame:
    """Agrège long → wide par (code, type).

    Retourne 3 colonnes par (code, type) :
    - `texts` : `list[str]`, les textes des notes retenues (post-dédup OFS-prio)
    - `per_source` : `list[str]` parallèle, la source de chaque note (OFS|OWL_ANS)
    - `source` : `str` agrégé pour audit rapide (`OFS`, `OWL_ANS`, ou `OFS+OWL_ANS`)
    """
    return (
        notes_long.group_by(["code", "type"])
        .agg(
            pl.col("texte").alias("texts"),
            pl.col("source").alias("per_source"),
        )
        .with_columns(
            pl.col("per_source").list.unique().list.sort().list.join("+").alias("source"),
        )
        .sort(["code", "type"])
    )


def merge_codes(owl_codes: pl.DataFrame, ofs_codes: pl.DataFrame) -> pl.DataFrame:
    """Fusion OFS ⊕ OWL conforme à `docs/source_mapping.md`.

    OWL = univers (left join). Pour chaque (code, type_de_note), matching
    élément-par-élément des notes OFS et OWL sur leur texte normalisé.
    Priorité OFS : une note OWL textuellement équivalente (après
    normalisation) à une note OFS est dropée du résultat (mais logguée
    dans `note_merges.csv` par `find_note_merges`).
    """
    ofs = _normalize_ofs(ofs_codes).select(
        pl.col("code_norm").alias("code"),
        pl.col("label").alias("ofs_label"),
        pl.col("synonymes").alias("ofs_synonymes"),
        pl.col("inclusions").alias("ofs_inclusions"),
        pl.col("exclusions_text").alias("ofs_exclusions"),
        pl.col("exclusions_redirect"),
        pl.col("notes_editorial"),
    )

    notes_long = _build_notes_long(owl_codes, ofs)
    notes_wide = _aggregate_notes(notes_long)

    inclusions_wide = notes_wide.filter(pl.col("type") == "inclusion").select(
        "code",
        pl.col("texts").alias("inclusions"),
        pl.col("per_source").alias("inclusions_per_source"),
        pl.col("source").alias("inclusions_source"),
    )
    exclusions_wide = notes_wide.filter(pl.col("type") == "exclusion").select(
        "code",
        pl.col("texts").alias("exclusions"),
        pl.col("per_source").alias("exclusions_per_source"),
        pl.col("source").alias("exclusions_source"),
    )

    empty_list = pl.lit([], dtype=pl.List(pl.String))

    # Synonymes : union OFS ∪ OWL dédupliquée (la priorité OFS s'applique à
    # l'EXPORT par flat_csv.py ; ici on conserve juste l'union triée).
    merged = owl_codes.join(ofs, on="code", how="left")
    synonymes_expr = (
        pl.col("synonymes")
        .fill_null(empty_list)
        .list.concat(pl.col("ofs_synonymes").fill_null(empty_list))
        .list.unique()
        .list.sort()
        .alias("synonymes_merged")
    )

    out: pl.DataFrame = (
        merged.with_columns(
            synonymes_expr,
            pl.col("ofs_label").is_not_null().alias("has_ofs_match"),
        )
        .with_columns(pl.col("synonymes_merged").alias("synonymes"))
        .join(inclusions_wide, on="code", how="left")
        .join(exclusions_wide, on="code", how="left")
        .with_columns(
            pl.col("inclusions").fill_null(empty_list),
            pl.col("inclusions_per_source").fill_null(empty_list),
            pl.col("inclusions_source").fill_null(_SOURCE_NONE),
            pl.col("exclusions").fill_null(empty_list),
            pl.col("exclusions_per_source").fill_null(empty_list),
            pl.col("exclusions_source").fill_null(_SOURCE_NONE),
        )
        .select(
            "code",
            "label",
            "type",
            "depth",
            "left",
            "right",
            "path",
            "inclusions",
            "inclusions_per_source",
            "inclusions_source",
            "exclusions",
            "exclusions_per_source",
            "exclusions_source",
            "exclusions_redirect",
            "structured_exclusions",
            "notes_editorial",
            "definitions",
            "scope_notes",
            "synonymes",
            "has_ofs_match",
        )
        .sort("left")
    )

    MergedCodesSchema.validate(out)
    return out


def find_note_merges(
    owl_codes: pl.DataFrame, ofs_codes: pl.DataFrame
) -> pl.DataFrame:
    """Pour chaque note OFS retenue, logger la version ANS alternative.

    Schéma (cf `docs/source_mapping.md` précision sur la dimension
    textuelle) :
    - code, type
    - texte_retenu : version OFS
    - texte_alternatif_ans : version ANS si différente après normalisation,
      sinon null
    - libelles_identiques_apres_normalisation : bool
    - difference_significative : bool (True si après normalisation les
      textes restent différents)

    Pour chaque (code, type) où OFS et OWL ont chacun au moins une note,
    on émet une ligne par note OFS retenue avec la meilleure alternative
    OWL : version normalisée-identique en priorité, sinon une version OWL
    textuellement différente (premier candidat). Les notes OWL sans
    alternative OFS et les notes OFS sans alternative OWL ne génèrent pas
    de ligne.
    """
    ofs = _normalize_ofs(ofs_codes).select(
        pl.col("code_norm").alias("code"),
        pl.col("inclusions").alias("ofs_inclusions"),
        pl.col("exclusions_text").alias("ofs_exclusions"),
    )

    ofs_long = pl.concat(
        [
            _explode_ofs_notes(ofs, "ofs_inclusions", "inclusion"),
            _explode_ofs_notes(ofs, "ofs_exclusions", "exclusion"),
        ]
    ).with_columns(normalize_column("texte").alias("_norm"))

    owl_long = pl.concat(
        [
            _explode_owl_singleton(owl_codes, "inclusion_note", "inclusion"),
            _explode_owl_list(owl_codes, "exclusion_notes", "exclusion"),
        ]
    ).with_columns(normalize_column("texte").alias("_norm"))

    # Jointure 1 : normalisation match (texte_retenu_ofs ↔ texte_owl identique)
    matched = (
        ofs_long.select(
            "code",
            "type",
            pl.col("texte").alias("texte_retenu"),
            pl.col("_norm"),
        )
        .join(
            owl_long.select(
                "code",
                "type",
                pl.col("texte").alias("texte_owl_match"),
                pl.col("_norm"),
            ),
            on=["code", "type", "_norm"],
            how="left",
        )
    )

    # Pour les OFS sans match normalisation : trouver un OWL "fallback"
    # = n'importe quelle note OWL du même (code, type) avec un _norm différent.
    owl_per_code_type = (
        owl_long.group_by(["code", "type"])
        .agg(pl.col("texte").first().alias("texte_owl_alt"))
    )

    enriched = matched.join(owl_per_code_type, on=["code", "type"], how="left")

    rows = enriched.with_columns(
        pl.col("texte_owl_match").is_not_null().alias("libelles_identiques_apres_normalisation"),
        pl.when(pl.col("texte_owl_match").is_not_null())
        .then(pl.lit(None, dtype=pl.String))
        .otherwise(pl.col("texte_owl_alt"))
        .alias("texte_alternatif_ans"),
    ).with_columns(
        (
            ~pl.col("libelles_identiques_apres_normalisation")
            & pl.col("texte_alternatif_ans").is_not_null()
        ).alias("difference_significative")
    )

    # Filtrer : ne garder que les lignes où il y a une alternative ANS (matchée ou différente)
    return (
        rows.filter(
            pl.col("libelles_identiques_apres_normalisation")
            | pl.col("texte_alternatif_ans").is_not_null()
        )
        .select(
            "code",
            "type",
            "texte_retenu",
            "texte_alternatif_ans",
            "libelles_identiques_apres_normalisation",
            "difference_significative",
        )
        .sort(["code", "type", "texte_retenu"])
    )


def find_conflicts(
    owl_codes: pl.DataFrame, ofs_codes: pl.DataFrame
) -> pl.DataFrame:
    """Logge UNIQUEMENT les conflits de libellé (le `label` du code).

    Les conflits sur les notes (inclusions, exclusions) sont désormais
    capturés par `find_note_merges` — plus précis car élément-par-élément.
    """
    ofs = _normalize_ofs(ofs_codes).select(
        pl.col("code_norm").alias("code"),
        pl.col("label").alias("ofs_label"),
    )
    both = owl_codes.join(ofs, on="code", how="inner")

    return (
        both.with_columns(
            normalize_column("label").alias("_owl_n"),
            normalize_column("ofs_label").alias("_ofs_n"),
        )
        .filter(
            pl.col("label").is_not_null()
            & pl.col("ofs_label").is_not_null()
            & (pl.col("_owl_n") != pl.col("_ofs_n"))
        )
        .select(
            pl.col("code"),
            pl.lit("label").alias("field"),
            pl.col("label").alias("owl_value"),
            pl.col("ofs_label").alias("ofs_value"),
            pl.lit("OWL_ANS").alias("resolved_to"),
        )
        .sort("code")
    )


def find_orphans(
    owl_codes: pl.DataFrame, ofs_codes: pl.DataFrame
) -> pl.DataFrame:
    """Codes OFS sans contrepartie OWL après strip parens (dropés du merge)."""
    ofs = _normalize_ofs(ofs_codes)
    owl_set = owl_codes.select("code").rename({"code": "code_norm"})
    return (
        ofs.join(owl_set, on="code_norm", how="anti")
        .select("code", "abbrev", "label", "type")
        .sort("code")
    )


def find_post_2006_codes(
    owl_codes: pl.DataFrame, ofs_codes: pl.DataFrame
) -> pl.DataFrame:
    """Codes ANS sans contrepartie OFS (= codes post-2006, par convention).

    Cf `docs/source_mapping.md` : OFS est gelé au 1er novembre 2006 ; tous
    les codes ajoutés depuis (U07.1 COVID, etc.) ne sont QUE dans l'ANS.
    """
    ofs_codes_norm = _normalize_ofs(ofs_codes).select(pl.col("code_norm").alias("code"))
    return (
        owl_codes.join(ofs_codes_norm, on="code", how="anti")
        .select("code", "label", "type", "depth")
        .sort("code")
    )


def to_parquet_and_reports(
    owl_path: Path,
    ofs_path: Path,
    output_dir: Path,
    reports_dir: Path,
) -> dict[str, Path]:
    owl = pl.read_parquet(owl_path)
    ofs = pl.read_parquet(ofs_path)

    merged = merge_codes(owl, ofs)
    conflicts = find_conflicts(owl, ofs)
    orphans = find_orphans(owl, ofs)
    note_merges = find_note_merges(owl, ofs)
    post_2006 = find_post_2006_codes(owl, ofs)

    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "merged": output_dir / "merged_codes.parquet",
        "conflicts": reports_dir / "merge_conflicts.csv",
        "orphans": reports_dir / "orphan_ofs_codes.csv",
        "note_merges": reports_dir / "note_merges.csv",
        "post_2006": reports_dir / "post_2006_codes.csv",
    }
    merged.write_parquet(paths["merged"])
    conflicts.write_csv(paths["conflicts"])
    orphans.write_csv(paths["orphans"])
    note_merges.write_csv(paths["note_merges"])
    post_2006.write_csv(paths["post_2006"])
    return paths
