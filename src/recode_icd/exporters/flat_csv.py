from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl

from recode_icd._normalize import normalize_column

_SOURCE_CSV_MAP: dict[str, str] = {
    "OFS": "CIM-10",
    "OWL_ANS": "ANS",
    "SYNTHESIZED_SIBLING": "CIM-10 frères",
    "INDEX_CIM10_VOL3": "CIM-10 index",
    "ORPHANET": "ORPHANET",
    "APHP_DERMATOLOGIE": "AP-HP Dermatologie",
    "APHP_ENDOCRINOLOGIE": "AP-HP Endocrinologie",
    "APHP_GRONES": "AP-HP GRONES",
    "APHP_METABOLISME": "AP-HP Troubles métaboliques",
    "APHP_NEPHROLOGIE": "AP-HP Néphrologie",
    "APHP_OPHTALMOLOGIE": "AP-HP Ophtalmologie",
    "APHP_RHUMATOLOGIE": "AP-HP Rhumatologie",
    "APHP_GERMES": "AP-HP Germes (SPILF)",
    "APHP_SRLF": "AP-HP SRLF",
}

_TYPE_ORDER: dict[str, int] = {"inclusion": 0, "exclusion": 1, "synonyme": 2}

# Colonnes finales du CSV maître (cf docs/source_mapping.md §"Schéma
# final du CSV principal"). Une ligne par (code, type, source, texte)
# par association dague/astérisque ; les codes sans association émettent
# une seule ligne avec dagger_code/asterisk_code à NULL et
# redundancy_level="none".
_FINAL_COLUMNS: tuple[str, ...] = (
    "code",
    "libelle",
    "type",
    "source",
    "texte",
    "dagger_code",
    "asterisk_code",
    "redundancy_level",
    "is_redundant_dagger",
)


@dataclass(frozen=True)
class FlatCsvStats:
    """Compteurs renvoyés par `build()` pour alimentation du rapport
    `reports/curation_applied.csv`."""

    n_dagger_lines_redundant: int
    n_synonyms_filtered_as_duplicates: int

    def as_long_rows(self) -> list[dict[str, object]]:
        return [
            {
                "dimension": "flat_csv",
                "value": "dagger_lines_marked_redundant",
                "count": self.n_dagger_lines_redundant,
            },
            {
                "dimension": "flat_csv",
                "value": "synonyms_filtered_as_duplicates",
                "count": self.n_synonyms_filtered_as_duplicates,
            },
        ]


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


def _filter_redundant_dagger_synonyms(
    synonymes: pl.DataFrame,
    dagger_asterisk: pl.DataFrame,
    leaves: pl.DataFrame,
) -> tuple[pl.DataFrame, int]:
    """Filtre les synonymes côté dague identiques (normalisation
    tolérante) à un synonyme OU au libellé systématique côté astérisque
    pour la même paire dague/astérisque.

    Règle validée empiriquement à ~15.8% sur DESCR (cf source_mapping.md
    §"Filtrage des synonymes redondants"). Limité aux synonymes — INCLUDE
    et EXCLUDE : 0 doublon observé, on ne touche pas.

    Args:
        synonymes : long format `(code, type=synonyme, source, texte)`.
        dagger_asterisk : table enrichie (paires complètes consommées).
        leaves : `(code, libelle)` pour récupérer le libellé systématique
            des codes astérisque.

    Returns:
        `(synonymes_filtrés, nb_filtrés)`.
    """
    pairs = dagger_asterisk.filter(
        pl.col("dagger_code").is_not_null() & pl.col("asterisk_code").is_not_null()
    ).select(["dagger_code", "asterisk_code"])

    if pairs.is_empty():
        return synonymes, 0

    # Référentiel "à ne pas répéter" côté dague : pour chaque paire
    # (D, A), tout texte normalisé présent comme synonyme de A OU comme
    # libellé systématique de A. On marque chaque (D, _norm) comme à
    # filtrer.
    aster_syn = (
        synonymes.join(
            pairs.rename({"asterisk_code": "code"}),
            on="code",
            how="inner",
        )
        .with_columns(normalize_column("texte").alias("_norm"))
        .select(pl.col("dagger_code"), pl.col("_norm"))
    )
    aster_label = (
        leaves.join(
            pairs.rename({"asterisk_code": "code"}),
            on="code",
            how="inner",
        )
        .with_columns(normalize_column("libelle").alias("_norm"))
        .select(pl.col("dagger_code"), pl.col("_norm"))
    )
    forbidden = (
        pl.concat([aster_syn, aster_label])
        .filter(pl.col("_norm").is_not_null())
        .unique()
    )

    annotated = synonymes.with_columns(
        normalize_column("texte").alias("_norm")
    ).join(
        forbidden.rename({"dagger_code": "code"}).with_columns(
            pl.lit(True).alias("_redundant")
        ),
        on=["code", "_norm"],
        how="left",
    )
    n_filtered = annotated.filter(pl.col("_redundant")).height
    kept = (
        annotated.filter(pl.col("_redundant").is_null())
        .drop("_norm", "_redundant")
    )
    return kept, n_filtered


def _attach_dagger_asterisk_columns(
    long: pl.DataFrame,
    dagger_asterisk: pl.DataFrame,
) -> tuple[pl.DataFrame, int]:
    """Expansion : pour chaque ligne de `long` (code, type, source, texte),
    produire N lignes selon les associations dague/astérisque de `code`.

    - Si `code` apparaît comme `dagger_code` d'une paire : `asterisk_code`
      rempli, `dagger_code` NULL.
    - Si `code` apparaît comme `asterisk_code` d'une paire : `dagger_code`
      rempli, `asterisk_code` NULL.
    - Si `code` n'apparaît dans aucune paire complète : 1 ligne, deux
      colonnes NULL, redundancy_level='none'.

    `is_redundant_dagger=True` ssi la ligne correspond à un côté dague
    d'une paire subordinate. `False` sinon.

    Returns:
        `(expanded, n_lignes_redundant)`.
    """
    complete = dagger_asterisk.filter(
        pl.col("dagger_code").is_not_null() & pl.col("asterisk_code").is_not_null()
    ).select(["dagger_code", "asterisk_code", "redundancy_level"])

    # Côté dague : pour les codes qui apparaissent comme dagger_code.
    as_dagger = (
        long.join(
            complete.rename({"dagger_code": "code"}),
            on="code",
            how="inner",
        )
        .with_columns(
            pl.lit(None, dtype=pl.String).alias("dagger_code"),
            pl.col("asterisk_code"),
            pl.col("redundancy_level"),
            (pl.col("redundancy_level") == "subordinate").alias("is_redundant_dagger"),
        )
        .select("code", "type", "source", "texte", "dagger_code", "asterisk_code", "redundancy_level", "is_redundant_dagger")
    )

    # Côté astérisque : pour les codes qui apparaissent comme asterisk_code.
    as_asterisk = (
        long.join(
            complete.rename({"asterisk_code": "code"}),
            on="code",
            how="inner",
        )
        .with_columns(
            pl.col("dagger_code"),
            pl.lit(None, dtype=pl.String).alias("asterisk_code"),
            pl.col("redundancy_level"),
            pl.lit(False).alias("is_redundant_dagger"),
        )
        .select("code", "type", "source", "texte", "dagger_code", "asterisk_code", "redundancy_level", "is_redundant_dagger")
    )

    # Codes hors paires : anti-join sur l'union des codes mentionnés
    # côté dague OU côté astérisque.
    involved = (
        pl.concat(
            [
                complete.select(pl.col("dagger_code").alias("code")),
                complete.select(pl.col("asterisk_code").alias("code")),
            ]
        )
        .unique()
    )
    none_side = (
        long.join(involved, on="code", how="anti")
        .with_columns(
            pl.lit(None, dtype=pl.String).alias("dagger_code"),
            pl.lit(None, dtype=pl.String).alias("asterisk_code"),
            pl.lit("none", dtype=pl.String).alias("redundancy_level"),
            pl.lit(False).alias("is_redundant_dagger"),
        )
        .select("code", "type", "source", "texte", "dagger_code", "asterisk_code", "redundancy_level", "is_redundant_dagger")
    )

    expanded = pl.concat([as_dagger, as_asterisk, none_side])
    n_redundant = expanded.filter(pl.col("is_redundant_dagger")).height
    return expanded, n_redundant


def build(
    merged: pl.DataFrame,
    propagated: pl.DataFrame,
    siblings: pl.DataFrame,
    owl: pl.DataFrame,
    ofs: pl.DataFrame,
    dagger_asterisk: pl.DataFrame,
    external: pl.DataFrame | None = None,
) -> tuple[pl.DataFrame, FlatCsvStats]:
    """Construit le CSV maître à 9 colonnes (cf source_mapping.md
    §"Schéma final du CSV principal").

    Étapes :
      1. Long format inclusions/exclusions/synonymes (priorité OFS).
      2. Filtrage des synonymes redondants côté dague (règle empirique).
      3. Concaténation des entrées externes (ORPHANET/Index/AP-HP)
         déjà dédupliquées et filtrées par `merge_external`.
      4. Restriction aux codes feuilles + traduction des sources.
      5. Expansion par association dague/astérisque (Principe 2 de la
         spec : une ligne par association).
      6. Sort déterministe par (code, type, source, texte, ast, dague).

    Args:
        external : DataFrame `(code, libelle_orig, libelle_norm, type,
            source)` produit par `merge_external.merge_external_sources`.
            Si None, comportement strictement identique à avant Phase 2.

    Returns:
        `(df, stats)`. `stats` est utilisé pour enrichir
        `reports/curation_applied.csv`.
    """
    leaves = _leaf_codes(merged)
    inex = _build_inclusions_exclusions(propagated, siblings)
    syn = _build_synonymes(owl, ofs)
    syn_filtered, n_syn_filtered = _filter_redundant_dagger_synonyms(
        syn, dagger_asterisk, leaves
    )
    parts = [inex, syn_filtered]
    if external is not None and not external.is_empty():
        ext_long = external.select(
            pl.col("code"),
            pl.col("type"),
            pl.col("source"),
            pl.col("libelle_orig").alias("texte"),
        )
        parts.append(ext_long)
    long = pl.concat(parts)

    base = (
        long.join(leaves, on="code", how="inner")
        .with_columns(
            pl.col("source").replace_strict(_SOURCE_CSV_MAP).alias("source"),
        )
        .unique(subset=["code", "type", "source", "texte"])
        .select("code", "libelle", "type", "source", "texte")
    )

    expanded, n_redundant = _attach_dagger_asterisk_columns(
        base.select("code", "type", "source", "texte"),
        dagger_asterisk,
    )

    # Réattacher `libelle` (perdu pendant l'expansion qui ne consomme
    # que les colonnes de note). Stable car (code, libelle) est unique
    # côté `leaves`.
    final = (
        expanded.join(leaves, on="code", how="left")
        .with_columns(pl.col("type").replace_strict(_TYPE_ORDER).alias("_type_order"))
        .sort(["code", "_type_order", "source", "texte", "asterisk_code", "dagger_code"])
        .select(*_FINAL_COLUMNS)
    )

    stats = FlatCsvStats(
        n_dagger_lines_redundant=n_redundant,
        n_synonyms_filtered_as_duplicates=n_syn_filtered,
    )
    return final, stats


def to_csv(
    merged_path: Path,
    propagated_path: Path,
    siblings_path: Path,
    owl_path: Path,
    ofs_path: Path,
    dagger_asterisk_path: Path,
    output_path: Path,
    curation_report_path: Path | None = None,
    external_path: Path | None = None,
) -> Path:
    """Construit le CSV maître à 9 colonnes et l'écrit sur disque.

    Si `curation_report_path` pointe vers un CSV existant (généré par
    `relations.dagger_asterisk.apply_curation`), les stats produites par
    `build()` y sont ajoutées en append. Sinon les stats sont écrites
    seules dans ce chemin si fourni.

    Si `external_path` est fourni et existe, ses lignes sont
    concaténées au pipeline (cf `merge_external.to_parquet_and_reports`).
    """
    merged = pl.read_parquet(merged_path)
    propagated = pl.read_parquet(propagated_path)
    siblings = pl.read_parquet(siblings_path)
    owl = pl.read_parquet(owl_path)
    ofs = pl.read_parquet(ofs_path)
    dag_aster = pl.read_parquet(dagger_asterisk_path)
    external = (
        pl.read_parquet(external_path)
        if external_path is not None and external_path.is_file()
        else None
    )

    csv_df, stats = build(
        merged, propagated, siblings, owl, ofs, dag_aster, external=external
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    csv_df.write_csv(output_path)

    if curation_report_path is not None:
        curation_report_path.parent.mkdir(parents=True, exist_ok=True)
        stats_df = pl.DataFrame(
            stats.as_long_rows(),
            schema={"dimension": pl.String, "value": pl.String, "count": pl.Int64},
        )
        if curation_report_path.is_file():
            existing = pl.read_csv(curation_report_path)
            stats_df = pl.concat([existing, stats_df], how="diagonal_relaxed")
        stats_df.write_csv(curation_report_path)

    return output_path
