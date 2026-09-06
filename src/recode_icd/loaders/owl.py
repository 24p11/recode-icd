from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
from smt2parquet import core

from recode_icd._normalize import normalize_ans_brackets_column
from recode_icd.loaders.queries import load_query
from recode_icd.loaders.schemas import DaggerAsteriskSchema, OwlCodesSchema

# Colonnes textuelles ANS sujettes à la convention de crochets de
# redirection. Normalisées en parenthèses au chargement (cf
# `docs/source_mapping.md` section "Conventions d'export ANS").
# Ce sont les 7 colonnes textuelles extraites par `owl_attrs.rq`, hors
# `code` et `type` qui ne portent pas de texte libre.
_ANS_TEXT_COLUMNS = (
    "label",
    "synonyme",
    "inclusion_note",
    "exclusion_note",
    "definition",
    "scope_note",
    "structured_exclusion",
)

BASE_URI = "http://data.esante.gouv.fr/atih/cim10"
RDF_FILENAME_PREFIX = "terminologie-cim-10-"
TERMINOLOGY_NAME = "cim10_ans"
#: Préfixe des URI synthétiques des codes injectés depuis le kit ATIH.
ATIH_URI_PREFIX = f"{BASE_URI}/kit-atih/"

_RE_CHAPITRE_XX = re.compile(r"^[VWXY]\d{2}")


def parent_au_maitre(code: str, codes: set[str]) -> str | None:
    """L'ancêtre le plus proche d'un code, par troncature de son écriture.

    `I70.00` → `I70.0` ; `J96.100` → `J96.10` ; `M45+0` → `M45` ;
    `M62.80` → `M62.8` (nœud). Un point ou un `+` terminal ne fait pas un
    code : on le saute. `None` si même la catégorie manque.
    """
    for n in range(len(code) - 1, 2, -1):
        candidat = code[:n].rstrip(".+")
        if candidat in codes:
            return candidat
    return None


def codes_atih_a_injecter(atih: pl.DataFrame, codes_presents: set[str]) -> pl.DataFrame:
    """Les codes du kit ATIH à créer dans le nested set (D3).

    Codables en MCO, absents du référentiel ANS, **hors chapitre XX** —
    dont les extensions lieu/activité relèvent d'une composition (D5),
    pas d'une injection. Un code type 3 absent (`O04.0`, niveau
    intermédiaire du kit sur une famille inversée) n'est jamais injecté :
    il ferait un nœud parallèle. Colonnes : `code`, `code_atih`,
    `libelle`, `parent` — un code sans parent au maître est une erreur,
    pas un orphelin silencieux.
    """
    absents = atih.filter(
        pl.col("codable_mco")
        & ~pl.col("code").is_in(sorted(codes_presents))
        & ~pl.col("code").str.contains(_RE_CHAPITRE_XX.pattern)
    ).sort("code")
    parents = [parent_au_maitre(c, codes_presents) for c in absents["code"]]
    sans_parent = [c for c, p in zip(absents["code"], parents, strict=True) if p is None]
    if sans_parent:
        raise ValueError(
            f"Codes ATIH sans ancêtre au référentiel : {sans_parent[:5]} — impossible de "
            f"les rattacher au nested set."
        )
    return absents.select(
        "code",
        "code_atih",
        pl.col("libelle_long").alias("libelle"),
        pl.col("type_mco"),
    ).with_columns(pl.Series("parent", parents, dtype=pl.String))


def load_codes(rdf_path: Path, atih: pl.DataFrame | None = None) -> pl.DataFrame:
    """Nested set ANS, éventuellement complété des codes du kit ATIH (D3).

    `atih` : `atih_codes.parquet`. Les codes codables absents de l'ANS
    (hors chapitre XX) sont rattachés à leur ancêtre le plus proche avec
    le libellé du kit, `source_existence="ATIH"` ; tous les autres nœuds
    portent `source_existence="OWL_ANS"`. Politique de fusion : existence
    du code — OWL_ANS, fallback ATIH (`docs/source_mapping.md`).
    """
    graph = core.load_graph(rdf_path)
    attrs = core.dataframe_from_sparql(graph, load_query("owl_attrs"))
    edges = core.dataframe_from_sparql(graph, load_query("owl_edges"))

    # Normalisation crochets ANS → parenthèses (avant agrégation : toutes
    # les colonnes textuelles sont encore scalaires à ce stade).
    attrs = attrs.with_columns(*(normalize_ans_brackets_column(col) for col in _ANS_TEXT_COLUMNS))

    attrs_agg = attrs.group_by("concept").agg(
        pl.col("code").first(),
        pl.col("label").first(),
        pl.col("type").first(),
        pl.col("synonyme").drop_nulls().unique().alias("synonymes"),
        pl.col("inclusion_note").first(),
        pl.col("exclusion_note").drop_nulls().unique().alias("exclusion_notes"),
        pl.col("definition").drop_nulls().unique().alias("definitions"),
        pl.col("scope_note").drop_nulls().unique().alias("scope_notes"),
        pl.col("structured_exclusion").drop_nulls().unique().alias("structured_exclusions"),
    )

    code_of = dict(zip(attrs_agg["concept"].to_list(), attrs_agg["code"].to_list(), strict=True))
    attrs_agg = attrs_agg.with_columns(pl.lit("OWL_ANS").alias("source_existence"))

    liste_edges: list[tuple[str, ...]] = list(edges.iter_rows())
    if atih is not None:
        injectes = codes_atih_a_injecter(atih, set(code_of.values()))
        uri_of = {c: u for u, c in code_of.items()}
        for r in injectes.iter_rows(named=True):
            uri = f"{ATIH_URI_PREFIX}{r['code']}"
            code_of[uri] = str(r["code"])
            liste_edges.append((uri_of[str(r["parent"])], uri))
        vide = pl.lit([], dtype=pl.List(pl.String))
        attrs_agg = pl.concat(
            [
                attrs_agg,
                injectes.select(
                    (pl.lit(ATIH_URI_PREFIX) + pl.col("code")).alias("concept"),
                    pl.col("code"),
                    pl.col("libelle").alias("label"),
                    pl.lit("category").alias("type"),
                    vide.alias("synonymes"),
                    pl.lit(None, dtype=pl.String).alias("inclusion_note"),
                    vide.alias("exclusion_notes"),
                    vide.alias("definitions"),
                    vide.alias("scope_notes"),
                    vide.alias("structured_exclusions"),
                    pl.lit("ATIH").alias("source_existence"),
                ),
            ],
            how="vertical_relaxed",
        )

    nested = core.build_nested_set(liste_edges, root=BASE_URI, code_of=code_of)

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
            "source_existence",
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


def to_parquet(
    rdf_path: Path,
    output_dir: Path,
    atih_path: Path | None = None,
    reports_dir: Path | None = None,
) -> tuple[Path, Path]:
    """owl_codes + owl_dagger_asterisk ; avec `atih_path`, injection D3 et
    rapport `reports/atih_only_codes.csv` (patron `post_2006_codes.csv`)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "terminology": TERMINOLOGY_NAME,
        "version": core.extract_version(rdf_path, RDF_FILENAME_PREFIX),
        "source_file": rdf_path.name,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    atih = pl.read_parquet(atih_path) if atih_path is not None else None
    if atih is not None:
        metadata["atih_kit_version"] = str(atih["millesime"][0]) if atih.height else ""

    codes_path = output_dir / "owl_codes.parquet"
    pairs_path = output_dir / "owl_dagger_asterisk.parquet"
    codes = load_codes(rdf_path, atih)
    core.write_parquet_with_metadata(codes, codes_path, metadata)
    core.write_parquet_with_metadata(load_dagger_asterisk(rdf_path), pairs_path, metadata)
    if atih is not None:
        dossier = reports_dir if reports_dir is not None else output_dir.parent.parent / "reports"
        dossier.mkdir(parents=True, exist_ok=True)
        injectes = codes.filter(pl.col("source_existence") == "ATIH").select(
            "code", "label", "path", "depth"
        )
        injectes.join(
            atih.select("code", "code_atih", "type_mco", "statut_mco"), on="code", how="left"
        ).sort("code").write_csv(dossier / "atih_only_codes.csv")
    return codes_path, pairs_path
