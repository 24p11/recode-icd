"""Intégration des sources externes (ORPHANET, Index CIM-10 vol3,
AP-HP HECTOR) au pipeline de merge OFS/OWL.

Cf `docs/source_mapping.md` §"Sources externes : politique
d'intégration".

Workflow Phase 2 :

1. `build_dedup_index(propagated, owl, ofs, siblings)` construit un
   `DataFrame (code, libelle_norm, libelle_orig, source, note_type)`
   à partir de toutes les notes/synonymes déjà présents dans
   OFS/ANS/synthétisés. C'est l'index contre lequel chaque entrée
   externe est testée pour absorption.

2. `merge_external_sources(...)` itère sur les sources externes dans
   l'ordre conventionnel (ORPHANET → INDEX_CIM10_VOL3 → APHP_*
   alphabétique). Pour chaque entrée :

   - **Code orphan** (absent de `merged_codes`) → loggué dans
     `external_orphans`, ignoré.
   - **Match dans `dedup_index`** → loggué dans `external_overlaps`,
     ignoré.
   - **Pas de match** → ajouté à `to_add` ET à `dedup_index` (pour la
     dédup inter-externes des sources suivantes).

3. Les entrées dont le code n'est pas terminal (`leaves`) tombent
   silencieusement au join final dans `flat_csv.build()`. Un
   compteur `entries_dropped_non_terminal` les comptabilise dans le
   summary pour audit (cohérent avec backlog
   `inclure_codes_intermediaires.md`).
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

from recode_icd._normalize import normalize_column

log = logging.getLogger(__name__)


# Ordre conventionnel de traitement des sources externes. Le premier
# arrivé sur une paire `(code, libelle_norm)` gagne (cf
# `docs/source_mapping.md` §"Politique de fusion avec OFS/ANS").
_EXTERNAL_ORDER: tuple[str, ...] = (
    "ORPHANET",
    "INDEX_CIM10_VOL3",
    "APHP_DERMATOLOGIE",
    "APHP_ENDOCRINOLOGIE",
    "APHP_GERMES",
    "APHP_GRONES",
    "APHP_METABOLISME",
    "APHP_NEPHROLOGIE",
    "APHP_OPHTALMOLOGIE",
    "APHP_RHUMATOLOGIE",
    "APHP_SRLF",
    # CepiDc en dernier : formulations télégraphiques (médiane 26 chars,
    # 3 mots) — moins riches que les libellés AP-HP/ORPHANET/Index.
    # Les ~0,5 % de matches tolérants sont donc absorbés en faveur des
    # sources plus expertes qui précèdent.
    "CEPIDC_2015",
)


# ----------------------------------------------------------------------
# 1. Construction de l'index de dédup
# ----------------------------------------------------------------------


def _explode_synonymes(codes_df: pl.DataFrame, source: str) -> pl.DataFrame:
    """Pour `owl_codes.parquet` ou `ofs_codes.parquet` : retourne
    `(code, libelle_orig, source, note_type=synonyme)`."""
    return (
        codes_df.select(
            pl.col("code"),
            pl.col("synonymes").alias("libelle_orig"),
        )
        .explode("libelle_orig")
        .filter(pl.col("libelle_orig").is_not_null())
        .with_columns(
            pl.lit(source).alias("source"),
            pl.lit("synonyme").alias("note_type"),
        )
        .select("code", "libelle_orig", "source", "note_type")
    )


def build_dedup_index(
    propagated: pl.DataFrame,
    owl: pl.DataFrame,
    ofs: pl.DataFrame,
    siblings: pl.DataFrame,
) -> pl.DataFrame:
    """Concatène toutes les notes/synonymes OFS+ANS+synthétisés
    indexables. Une ligne par (code, libellé original) avec sa
    `source` (enum Python) et son `note_type`.

    Émet aussi `libelle_norm` (NFKD + lowercase + ponctuation
    collapsée) qui sert de clé de dédup tolérante avec les sources
    externes.

    Pas de garantie d'unicité — un même `(code, libelle_norm)` peut
    apparaître plusieurs fois (OFS et ANS donnent le même libellé).
    Pour le lookup on prend la première occurrence (`unique(keep=first)`).
    """
    # Inclusions et exclusions propagées (héritées + propres). On
    # exclut explicitement `note_editorial` qui ne va pas dans le CSV
    # final.
    prop_notes = propagated.filter(
        pl.col("note_type").is_in(["inclusion", "exclusion"])
    ).select(
        pl.col("code"),
        pl.col("texte").alias("libelle_orig"),
        pl.col("source"),
        pl.col("note_type"),
    )

    # Exclusions synthétisées sur les codes .8.
    sib_notes = siblings.select(
        pl.col("code"),
        pl.col("texte").alias("libelle_orig"),
        pl.col("source"),
        pl.col("note_type"),
    )

    syn_owl = _explode_synonymes(owl, "OWL_ANS")
    # OFS code peut être entouré de parenthèses (cf flat_csv:103).
    ofs_clean = ofs.with_columns(pl.col("code").str.strip_chars("()").alias("code"))
    syn_ofs = _explode_synonymes(ofs_clean, "OFS")

    combined = pl.concat([prop_notes, sib_notes, syn_owl, syn_ofs])
    return (
        combined.with_columns(
            normalize_column("libelle_orig").alias("libelle_norm")
        )
        .filter(pl.col("libelle_norm").is_not_null())
        .filter(pl.col("libelle_norm").str.len_chars() > 0)
        .unique(subset=["code", "libelle_norm"], keep="first")
        .select("code", "libelle_norm", "libelle_orig", "source", "note_type")
    )


# ----------------------------------------------------------------------
# 2. Merge externe
# ----------------------------------------------------------------------


def _classify_codes(
    external_df: pl.DataFrame,
    valid_codes: pl.DataFrame,
    ofs_codes: pl.DataFrame,
    rdf_codes: set[str] | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Sépare `external_df` en (`present`, `orphan`) selon présence
    dans `valid_codes` (= `merged_codes`). Pour les orphans, attribue
    une `categorie_orphan` selon le diagnostic Phase 2.5
    (cf `docs/sessions/phase2_5_diagnostic.md` §4) :

    - `pre_2006_dropped_by_atih` : code présent en OFS mais pas dans
      `merged_codes`. La CIM-10 ANS 2025 ne contient plus ce code
      (refonte ATIH). Cas dominant (~89 %).
    - `truly_absent` : code absent de toutes les sources OFS/ANS.
      Faute de transcription dans la source externe (~11 %).
    - `loader_dropped` : code dans le RDF ANS brut mais perdu par
      le loader OWL. Détectable seulement si `rdf_codes` est passé
      (set des codes présents dans le RDF). Sans ce paramètre, on
      ne distingue pas ce cas de `pre_2006_dropped_by_atih` /
      `truly_absent` — il faudrait que le code soit présent dans le
      RDF tout en étant absent du Parquet OWL (= absent de
      `valid_codes` car merged_codes vient d'OWL). 0 cas observé.
    - `unknown_pattern` : filet de sécurité pour des combinaisons
      non prévues (typiquement aucun cas en pratique).

    Le code "non_parseable" est filtré en amont par les loaders Phase 1.
    """
    present = external_df.join(valid_codes, on="code", how="inner")
    orphans = external_df.join(valid_codes, on="code", how="anti")
    if orphans.is_empty():
        empty_with_cat = orphans.with_columns(
            pl.lit(None, dtype=pl.String).alias("categorie_orphan")
        )
        return present, empty_with_cat

    ofs_set = set(ofs_codes["code"].str.strip_chars("()").to_list())
    rdf_set = rdf_codes if rdf_codes is not None else set()

    def _classify_one(code: str) -> str:
        in_ofs = code in ofs_set
        in_rdf = code in rdf_set
        if in_rdf:
            # Présent RDF mais absent merged_codes → le loader OWL l'a
            # perdu. Filet de sécurité, 0 cas observé en pratique.
            return "loader_dropped"
        if in_ofs:
            return "pre_2006_dropped_by_atih"
        # Absent OFS et absent RDF (si fourni) ou détection RDF
        # désactivée : on classe `truly_absent` par défaut. Un futur
        # cas où ce raisonnement deviendrait faux serait capturé par
        # `unknown_pattern` côté tests.
        return "truly_absent"

    orphans = orphans.with_columns(
        pl.col("code")
        .map_elements(_classify_one, return_dtype=pl.String)
        .alias("categorie_orphan")
    )
    return present, orphans


def _process_one_source(
    source_label: str,
    source_df: pl.DataFrame,
    dedup_index: pl.DataFrame,
    valid_codes: pl.DataFrame,
    ofs_codes: pl.DataFrame,
    leaves: pl.DataFrame,
    rdf_codes: set[str] | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, dict[str, int]]:
    """Traite une source externe. Retourne :

    - `to_add` : `(code, libelle_orig, libelle_norm, type, source)` à
      injecter dans le pipeline.
    - `overlaps` : entrées absorbées (matches OFS/ANS/inter-externes).
    - `orphans` : entrées au code absent de `valid_codes`.
    - `counters` : dict des stats pour le summary.
    """
    # Pré-traitement : normaliser le libellé, garder seulement les
    # colonnes utiles.
    src = source_df.select(
        pl.col("code"),
        pl.col("libelle").alias("libelle_orig"),
        pl.col("type"),
    ).with_columns(
        pl.lit(source_label).alias("source"),
        normalize_column("libelle_orig").alias("libelle_norm"),
    )

    entries_loaded = src.height

    # 1. Séparer code-present / code-orphan.
    present, orphans = _classify_codes(src, valid_codes, ofs_codes, rdf_codes)
    entries_orphan = orphans.height

    # 2. Dédup tolérante sur les codes présents.
    matched = present.join(
        dedup_index.rename({"source": "source_ofs_ans",
                            "note_type": "type_ofs_ans",
                            "libelle_orig": "libelle_ofs_ans"})
        .select("code", "libelle_norm", "libelle_ofs_ans",
                "source_ofs_ans", "type_ofs_ans"),
        on=["code", "libelle_norm"],
        how="inner",
    )
    entries_absorbed = matched.height

    unmatched = present.join(
        dedup_index.select("code", "libelle_norm"),
        on=["code", "libelle_norm"],
        how="anti",
    )

    # 3. Pour le summary : codes non-terminaux qui seront silencieusement
    # filtrés par flat_csv.build() à l'inner-join avec leaves.
    leaf_codes = leaves.select("code")
    non_terminal = unmatched.join(leaf_codes, on="code", how="anti")
    entries_dropped_non_terminal = non_terminal.height

    entries_added_to_csv = unmatched.height - entries_dropped_non_terminal

    # 4. Construire le rapport overlaps.
    overlaps = matched.with_columns(
        pl.lit(source_label).alias("source_externe"),
        (pl.col("type") != pl.col("type_ofs_ans")).alias("type_divergence"),
        pl.lit(None, dtype=pl.Int64).alias("lid_ofs"),  # cf docstring
    ).select(
        pl.col("code"),
        pl.col("libelle_orig").alias("libelle_externe"),
        pl.col("libelle_ofs_ans"),
        pl.col("source_externe"),
        pl.col("source_ofs_ans"),
        pl.col("type").alias("type_externe"),
        pl.col("type_ofs_ans"),
        pl.col("type_divergence"),
        pl.col("lid_ofs"),
    )

    # 5. Construire le rapport orphans.
    orphans_report = orphans.select(
        pl.col("code"),
        pl.col("libelle_orig").alias("libelle"),
        pl.col("source").alias("source_externe"),
        pl.col("categorie_orphan"),
    )

    # 6. `to_add` (à concaténer dans `long` côté flat_csv).
    to_add = unmatched.select(
        pl.col("code"),
        pl.col("libelle_orig"),
        pl.col("libelle_norm"),
        pl.col("type"),
        pl.col("source"),
    )

    counters = {
        "entries_loaded": entries_loaded,
        "entries_absorbed": entries_absorbed,
        "entries_orphan": entries_orphan,
        "entries_dropped_non_terminal": entries_dropped_non_terminal,
        "entries_added_to_csv": entries_added_to_csv,
    }
    return to_add, overlaps, orphans_report, counters


def merge_external_sources(
    propagated: pl.DataFrame,
    owl: pl.DataFrame,
    ofs: pl.DataFrame,
    siblings: pl.DataFrame,
    leaves: pl.DataFrame,
    valid_codes: pl.DataFrame,
    external_frames: dict[str, pl.DataFrame],
    rdf_codes: set[str] | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Orchestre la dédup tolérante de toutes les sources externes.

    Args :
        propagated, owl, ofs, siblings : DataFrames du pipeline OFS+ANS.
        leaves : `(code, libelle)` des codes terminaux (pour le compteur
            `entries_dropped_non_terminal`).
        valid_codes : codes acceptés par `merged_codes` (DataFrame avec
            au moins la colonne `code`).
        external_frames : dict `{source_label: DataFrame}` avec les
            sorties des loaders Phase 1, déjà séparées par enum source.
            Pour AP-HP, les 9 spécialités doivent figurer séparément.
        rdf_codes : set optionnel des codes présents dans le RDF ANS
            brut. Si fourni, permet de distinguer `loader_dropped`
            dans `categorie_orphan` (cf `_classify_codes` docstring).

    Returns :
        `(to_add, overlaps, orphans, summary)`.
    """
    dedup_index = build_dedup_index(propagated, owl, ofs, siblings)
    log.info(
        "Dedup index initial : %d entrées (notes OFS+ANS+synthétisées)",
        dedup_index.height,
    )

    to_add_parts: list[pl.DataFrame] = []
    overlaps_parts: list[pl.DataFrame] = []
    orphans_parts: list[pl.DataFrame] = []
    summary_rows: list[dict[str, object]] = []

    # `valid_codes` réduit à la colonne `code` pour les joins.
    valid_codes = valid_codes.select("code").unique()

    for source_label in _EXTERNAL_ORDER:
        if source_label not in external_frames:
            continue
        src_df = external_frames[source_label]
        if src_df.is_empty():
            continue

        to_add, overlaps, orphans, counters = _process_one_source(
            source_label=source_label,
            source_df=src_df,
            dedup_index=dedup_index,
            valid_codes=valid_codes,
            ofs_codes=ofs,
            leaves=leaves,
            rdf_codes=rdf_codes,
        )

        # Update du dedup_index avec les unmatched pour les sources suivantes.
        new_index_rows = to_add.with_columns(
            pl.col("type").alias("note_type"),
        ).select("code", "libelle_norm", "libelle_orig", "source", "note_type")
        dedup_index = pl.concat([dedup_index, new_index_rows]).unique(
            subset=["code", "libelle_norm"], keep="first"
        )

        to_add_parts.append(to_add)
        overlaps_parts.append(overlaps)
        orphans_parts.append(orphans)
        pct = (
            counters["entries_absorbed"] / counters["entries_loaded"]
            if counters["entries_loaded"]
            else 0.0
        )
        summary_rows.append(
            {
                "source": source_label,
                **counters,
                "pct_absorbed": round(pct, 4),
            }
        )
        log.info(
            "%s : loaded=%d absorbed=%d orphan=%d non_terminal=%d added=%d",
            source_label,
            counters["entries_loaded"],
            counters["entries_absorbed"],
            counters["entries_orphan"],
            counters["entries_dropped_non_terminal"],
            counters["entries_added_to_csv"],
        )

    to_add_df = (
        pl.concat(to_add_parts) if to_add_parts else _empty_to_add()
    )
    overlaps_df = (
        pl.concat(overlaps_parts) if overlaps_parts else _empty_overlaps()
    )
    orphans_df = (
        pl.concat(orphans_parts) if orphans_parts else _empty_orphans()
    )
    summary_df = pl.DataFrame(summary_rows, schema=_summary_schema())

    return to_add_df, overlaps_df, orphans_df, summary_df


# ----------------------------------------------------------------------
# 3. Schémas (utilisés pour construire des DataFrames vides cohérents)
# ----------------------------------------------------------------------


def _empty_to_add() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "code": pl.String,
            "libelle_orig": pl.String,
            "libelle_norm": pl.String,
            "type": pl.String,
            "source": pl.String,
        }
    )


def _empty_overlaps() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "code": pl.String,
            "libelle_externe": pl.String,
            "libelle_ofs_ans": pl.String,
            "source_externe": pl.String,
            "source_ofs_ans": pl.String,
            "type_externe": pl.String,
            "type_ofs_ans": pl.String,
            "type_divergence": pl.Boolean,
            "lid_ofs": pl.Int64,
        }
    )


def _empty_orphans() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "code": pl.String,
            "libelle": pl.String,
            "source_externe": pl.String,
            "categorie_orphan": pl.String,
        }
    )


def _summary_schema() -> dict[str, type[pl.DataType]]:
    return {
        "source": pl.String,
        "entries_loaded": pl.Int64,
        "entries_absorbed": pl.Int64,
        "entries_orphan": pl.Int64,
        "entries_dropped_non_terminal": pl.Int64,
        "entries_added_to_csv": pl.Int64,
        "pct_absorbed": pl.Float64,
    }


# ----------------------------------------------------------------------
# 4. Orchestration disk-based
# ----------------------------------------------------------------------


def load_external_frames(
    orphanet_xml: Path,
    hector_xlsx: Path,
    cepidc_csv: Path | None = None,
) -> dict[str, pl.DataFrame]:
    """Charge les loaders Phase 1 (ORPHANET, Index, AP-HP, CepiDc) et
    split AP-HP en 9 DataFrames par spécialité. Retourne un dict
    source_label → DataFrame.

    Args :
        orphanet_xml : XML ORPHANET (mapping E/NTBT).
        hector_xlsx : classeur HECTOR (Index CIM-10 vol3 + AP-HP).
        cepidc_csv : CSV CepiDc 2015 (optionnel). Si None, CepiDc n'est
            pas chargé.
    """
    from recode_icd.loaders.external import (
        load_aphp_hector,
        load_cepidc,
        load_index_cim10,
        load_orphanet,
    )

    frames: dict[str, pl.DataFrame] = {
        "ORPHANET": load_orphanet(orphanet_xml),
        "INDEX_CIM10_VOL3": load_index_cim10(hector_xlsx),
    }
    aphp = load_aphp_hector(hector_xlsx)
    for source_label in aphp["source"].unique().to_list():
        frames[source_label] = aphp.filter(pl.col("source") == source_label)
    if cepidc_csv is not None:
        frames["CEPIDC_2015"] = load_cepidc(cepidc_csv)
    return frames


def to_parquet_and_reports(
    merged_path: Path,
    propagated_path: Path,
    siblings_path: Path,
    owl_path: Path,
    ofs_path: Path,
    orphanet_xml: Path,
    hector_xlsx: Path,
    output_path: Path,
    reports_dir: Path,
    cepidc_csv: Path | None = None,
) -> dict[str, Path]:
    """Pipeline complet : loaders → merge → 1 Parquet `to_add` + 3
    rapports CSV.

    Si `cepidc_csv` est fourni, CepiDc 2015 est chargé en plus et un
    rapport dédié `cepidc_ignored.csv` est généré (codes CepiDc absents
    du CSV recode-icd, format `(code_cepidc, n_formulations_perdues,
    exemples_formulations)`).
    """
    merged = pl.read_parquet(merged_path)
    propagated = pl.read_parquet(propagated_path)
    siblings = pl.read_parquet(siblings_path)
    owl = pl.read_parquet(owl_path)
    ofs = pl.read_parquet(ofs_path)

    leaves = merged.filter(
        (pl.col("type") == "category") & ((pl.col("right") - pl.col("left")) == 1)
    ).select("code", pl.col("label").alias("libelle"))
    valid_codes = merged.select("code")

    external_frames = load_external_frames(orphanet_xml, hector_xlsx, cepidc_csv)

    to_add, overlaps, orphans, summary = merge_external_sources(
        propagated=propagated,
        owl=owl,
        ofs=ofs,
        siblings=siblings,
        leaves=leaves,
        valid_codes=valid_codes,
        external_frames=external_frames,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "to_add": output_path,
        "overlaps": reports_dir / "external_overlaps.csv",
        "orphans": reports_dir / "external_orphan_codes.csv",
        "summary": reports_dir / "external_sources_summary.csv",
    }
    to_add.write_parquet(paths["to_add"])
    overlaps.write_csv(paths["overlaps"])
    orphans.write_csv(paths["orphans"])
    summary.write_csv(paths["summary"])

    if cepidc_csv is not None:
        cepidc_ignored = _build_cepidc_ignored_report(orphans)
        paths["cepidc_ignored"] = reports_dir / "cepidc_ignored.csv"
        cepidc_ignored.write_csv(paths["cepidc_ignored"])
    return paths


def _build_cepidc_ignored_report(orphans: pl.DataFrame) -> pl.DataFrame:
    """Agrège les orphelins CepiDc par code pour le rapport dédié.

    Format : `(code_cepidc, n_formulations_perdues,
    exemples_formulations)` — 5 premiers libellés ordre alphabétique,
    concaténés par ` | `.
    """
    cepidc = orphans.filter(pl.col("source_externe") == "CEPIDC_2015")
    if cepidc.is_empty():
        return pl.DataFrame(
            schema={
                "code_cepidc": pl.String,
                "n_formulations_perdues": pl.UInt32,
                "exemples_formulations": pl.String,
            }
        )
    return (
        cepidc.sort("libelle")
        .group_by("code")
        .agg(
            pl.col("libelle").len().alias("n_formulations_perdues"),
            pl.col("libelle").head(5).str.join(" | ").alias(
                "exemples_formulations"
            ),
        )
        .rename({"code": "code_cepidc"})
        .sort("n_formulations_perdues", descending=True)
    )


__all__ = (
    "build_dedup_index",
    "load_external_frames",
    "merge_external_sources",
    "to_parquet_and_reports",
)
