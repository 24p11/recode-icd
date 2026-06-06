from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl

from recode_icd._normalize import normalize_column
from recode_icd.loaders.schemas import FlatCsvSchema

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

# Ordre de priorité du niveau de propagation (cf docs/source_mapping.md
# §"Propagation des notes hiérarchiques"). En cas de doublon
# (code, type, source, texte) propre+hérité, on garde la version la
# plus spécifique : code < category < block < chapter.
_SOURCE_LEVEL_ORDER: dict[str, int] = {
    "code": 0,
    "category": 1,
    "block": 2,
    "chapter": 3,
}

# Colonnes finales du CSV maître à 9 colonnes (cf docs/source_mapping.md
# §"Schéma final du CSV principal", §"Couples dague/astérisque :
# politique de représentation" et §"Propagation des notes hiérarchiques").
# Refonte 2026-05-30 : une ligne par (code, type, source, texte) avec
# is_dagger_in_pair / is_asterisk_in_pair signalant la participation à
# la mécanique dague/astérisque au niveau du code, sans expansion.
_FINAL_COLUMNS: tuple[str, ...] = (
    "code",
    "libelle",
    "type",
    "source",
    "texte",
    "source_level",
    "inherited_from_code",
    "is_dagger_in_pair",
    "is_asterisk_in_pair",
)


@dataclass(frozen=True)
class FlatCsvStats:
    """Compteurs renvoyés par `build()` pour alimentation du rapport
    `reports/curation_applied.csv`."""

    n_synonyms_filtered_as_duplicates: int

    def as_long_rows(self) -> list[dict[str, object]]:
        return [
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
        # source_level = type de l'ancêtre si propagé, sinon "code".
        pl.when(pl.col("inherited_from").is_null())
        .then(pl.lit("code"))
        .otherwise(pl.col("inherited_from_type"))
        .cast(pl.String)
        .alias("source_level"),
        # Cast explicite : si propagated a inherited_from tout-null
        # (cas fixtures), polars infère le type Null — on force String
        # pour rester concat-compatible avec les autres parties.
        pl.col("inherited_from").cast(pl.String).alias("inherited_from_code"),
    )
    # Notes synthétisées frères : attachées directement au code .8.
    sib = siblings.select(
        pl.col("code"),
        pl.col("note_type").alias("type"),
        pl.col("source"),
        pl.col("texte"),
        pl.lit("code").alias("source_level"),
        pl.lit(None, dtype=pl.String).alias("inherited_from_code"),
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
        .with_columns(
            pl.lit("synonyme").alias("type"),
            # Les descripteurs/synonymes sont attachés au code feuille.
            pl.lit("code").alias("source_level"),
            pl.lit(None, dtype=pl.String).alias("inherited_from_code"),
        )
        .select("code", "type", "source", "texte", "source_level", "inherited_from_code")
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


def _compute_dagger_flags(
    dagger_asterisk: pl.DataFrame,
) -> tuple[set[str], set[str]]:
    """Calcule depuis la table DAGSTAR enrichie les deux sets de codes
    impliqués dans des paires (cf docs/source_mapping.md §"Couples
    dague/astérisque : politique de représentation").

    Construction (cf section "Table DAGSTAR enrichie") :
    - daget ∈ {S, T, U} → SID = dague (stocké en `dagger_code`).
    - daget ∈ {F, G, H} → SID = astérisque (stocké en `asterisk_code`).

    Donc l'apparition d'un code en `dagger_code` (non-null) est
    exactement l'équivalent d'`is_dagger_in_pair=True`, et idem
    pour `asterisk_code` (non-null) ⇔ `is_asterisk_in_pair=True`.
    Les cas non pointés (assoc=0) y figurent avec l'autre côté NULL.

    Returns:
        `(dagger_codes, asterisk_codes)` : deux sets de codes.
    """
    dagger_codes = set(
        dagger_asterisk["dagger_code"].drop_nulls().to_list()
    )
    asterisk_codes = set(
        dagger_asterisk["asterisk_code"].drop_nulls().to_list()
    )
    return dagger_codes, asterisk_codes


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
    §"Schéma final du CSV principal", §"Couples dague/astérisque :
    politique de représentation" et §"Propagation des notes
    hiérarchiques").

    Étapes :
      1. Long format inclusions/exclusions/synonymes (priorité OFS),
         avec source_level/inherited_from_code tracés.
      2. Filtrage des synonymes redondants côté dague (règle empirique
         des 15,8 %).
      3. Concaténation des entrées externes (ORPHANET/Index/AP-HP)
         déjà dédupliquées et filtrées par `merge_external`
         (source_level=code, inherited_from_code=null).
      4. Restriction aux codes feuilles + traduction des sources.
         Dédup (code, type, source, texte) priorisant la version la
         plus spécifique (source_level=code).
      5. Calcul des flags is_dagger_in_pair / is_asterisk_in_pair via
         la table DAGSTAR enrichie (sans expansion).
      6. Sort déterministe par (code, type, source, texte).

    Refonte 2026-05-30 : suppression de l'expansion par paire
    dague/astérisque. Chaque note du code apparaît une seule fois ;
    le détail des paires reste dans `dagger_asterisk.parquet`.

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
    # Retypage altLabel ANS → inclusion pour codes type=D du chapitre
    # XIII : `_build_synonymes` lit `owl` directement (pas `merged`), il
    # faut donc vider les altLabel concernés ici aussi pour qu'ils ne
    # ré-apparaissent pas comme `synonyme`. Idempotent avec le retypage
    # déjà appliqué dans `merge.py::merge_codes` (les inclusions ANS
    # retypées arrivent via `propagated_notes`, indépendamment).
    # Cf docs/sessions/2026-06-06_localisations_chap13_ofs.md.
    from recode_icd.merge import retype_chap13_altlabels
    owl_filtered, _ = retype_chap13_altlabels(owl, ofs)
    syn = _build_synonymes(owl_filtered, ofs)
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
            pl.lit("code").alias("source_level"),
            pl.lit(None, dtype=pl.String).alias("inherited_from_code"),
        )
        parts.append(ext_long)
    long = pl.concat(parts)

    base = (
        long.join(leaves, on="code", how="inner")
        .with_columns(
            pl.col("source").replace_strict(_SOURCE_CSV_MAP).alias("source"),
            pl.col("source_level")
            .replace_strict(_SOURCE_LEVEL_ORDER, default=0)
            .alias("_level_order"),
        )
        # Dédup priorisant la version la plus spécifique : si une note
        # (code, type, source, texte) existe à la fois propre (code) et
        # héritée (category/block/chapter), on garde la version `code`.
        .sort("_level_order")
        .unique(subset=["code", "type", "source", "texte"], keep="first")
        .select(
            "code", "libelle", "type", "source", "texte",
            "source_level", "inherited_from_code",
        )
    )

    dagger_codes, asterisk_codes = _compute_dagger_flags(dagger_asterisk)

    final = (
        base.with_columns(
            pl.col("code").is_in(list(dagger_codes)).alias("is_dagger_in_pair"),
            pl.col("code").is_in(list(asterisk_codes)).alias("is_asterisk_in_pair"),
            pl.col("type").replace_strict(_TYPE_ORDER).alias("_type_order"),
        )
        .sort(["code", "_type_order", "source", "texte"])
        .select(*_FINAL_COLUMNS)
    )

    FlatCsvSchema.validate(final)
    stats = FlatCsvStats(
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
