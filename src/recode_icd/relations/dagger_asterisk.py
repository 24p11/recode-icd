"""Table d'associations dague/astérisque enrichie — objectif 2 du projet.

Construit, à partir des tables brutes OFS (MASTER, DAGSTAR, LIBELLE),
une table relationnelle où chaque ligne représente une **paire
sémantique unique** `(dagger_sid, asterisk_sid)`. Les multiples
lignes DAGSTAR.txt qui pointent sur la même paire (vue depuis le
côté dague ou astérisque, à des niveaux daget différents) sont
regroupées via `association_id`.

Spec : `docs/source_mapping.md` §"Table DAGSTAR enrichie".
Schéma : `loaders.schemas.EnrichedDaggerAsteriskSchema`.

Phase 1 du séquencement : `redundancy_level` reste à `independent`
pour toutes les paires complètes et `none` pour les paires
incomplètes. Le YAML de curation sera consommé en phase 3.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from recode_icd.loaders.ofs import _read as _read_ofs_table
from recode_icd.loaders.schemas import EnrichedDaggerAsteriskSchema

# Sémantique des valeurs daget (cf. docs/source_mapping.md §"Les trois
# niveaux d'association") : le SID est dague pour S/T/U, astérisque
# pour F/G/H. Le champ `assoc` pointe le code opposé.
_DAGUE_SIDE: frozenset[str] = frozenset({"S", "T", "U"})
_ASTER_SIDE: frozenset[str] = frozenset({"F", "G", "H"})

_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+")

_VALID_CURATION_LEVELS: frozenset[str] = frozenset(
    {"independent", "subordinate", "undecided", ""}
)


def _normalize_label(text: str | None) -> str:
    """Normalisation tolérante : NFKD + lowercase + suppression
    ponctuation + collapse whitespace. Sert de clé de bucket pour la
    déduplication des `combination_labels`."""
    if text is None:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    no_accent = "".join(c for c in decomposed if not unicodedata.combining(c))
    no_punct = _PUNCT_RE.sub(" ", no_accent.lower())
    return _WS_RE.sub(" ", no_punct).strip()


def _dedup_tolerant(texts: list[str | None]) -> list[str]:
    """Garde la première occurrence (ordre d'entrée) par bucket de
    normalisation. Skippe les None et les chaînes vides."""
    seen: set[str] = set()
    out: list[str] = []
    for t in texts:
        if t is None:
            continue
        bucket = _normalize_label(t)
        if not bucket or bucket in seen:
            continue
        seen.add(bucket)
        out.append(t)
    return out


def build_dagger_asterisk_table(
    ofs_master: pl.DataFrame,
    ofs_dagstar: pl.DataFrame,
    ofs_libelle: pl.DataFrame,
) -> pl.DataFrame:
    """Construit la table dague/astérisque enrichie.

    Args :
        ofs_master : MASTER brut (lu par `loaders.ofs._read`). Filtré
            sur `valid==1` ici.
        ofs_dagstar : DAGSTAR brut. Toutes les lignes sont consommées.
        ofs_libelle : LIBELLE brut. Filtré sur `valid==1` ici. Sert à
            résoudre `combination_labels` (toutes sources) et
            `*_label` (source='S').

    Returns :
        DataFrame conforme à `EnrichedDaggerAsteriskSchema`.
    """
    master_valid = ofs_master.filter(pl.col("valid") == 1).select(
        ["SID", "code"]
    )
    libelle_valid = ofs_libelle.filter(pl.col("valid") == 1)
    sys_labels = (
        libelle_valid.filter(pl.col("source") == "S")
        .group_by("SID")
        .agg(pl.col("libelle").first().alias("sys_label"))
    )
    libelle_by_lid = libelle_valid.select(["LID", "libelle"])

    # Étape 1 : pour chaque ligne DAGSTAR, identifier les SID dague et
    # astérisque selon `daget`. `assoc==0` signifie absence du code
    # opposé (cas non pointé S/F) — on convertit en None pour
    # alimenter proprement le NULL groupable de polars.
    normalized = (
        ofs_dagstar.with_columns(
            pl.when(pl.col("daget").is_in(list(_DAGUE_SIDE)))
            .then(pl.col("SID"))
            .otherwise(pl.col("assoc"))
            .alias("dagger_sid"),
            pl.when(pl.col("daget").is_in(list(_ASTER_SIDE)))
            .then(pl.col("SID"))
            .otherwise(pl.col("assoc"))
            .alias("asterisk_sid"),
        )
        .with_columns(
            pl.when(pl.col("dagger_sid") == 0)
            .then(None)
            .otherwise(pl.col("dagger_sid"))
            .alias("dagger_sid"),
            pl.when(pl.col("asterisk_sid") == 0)
            .then(None)
            .otherwise(pl.col("asterisk_sid"))
            .alias("asterisk_sid"),
        )
        .join(libelle_by_lid, on="LID", how="left")
        .select(["dagger_sid", "asterisk_sid", "daget", "LID", "libelle"])
    )

    # Étape 2 : grouper par paire. `sort_by("LID")` à l'intérieur de
    # l'agg garantit que les libellés sortent dans un ordre stable
    # avant la dédup tolérante (déterminisme).
    grouped = normalized.group_by(["dagger_sid", "asterisk_sid"]).agg(
        pl.col("daget").unique().sort().alias("levels_present"),
        pl.col("LID").unique().sort().alias("source_lids"),
        pl.col("libelle").sort_by("LID").alias("_raw_labels"),
    )

    grouped = grouped.with_columns(
        pl.col("_raw_labels")
        .map_elements(
            lambda lst: _dedup_tolerant(list(lst)),
            return_dtype=pl.List(pl.String),
        )
        .alias("combination_labels")
    ).drop("_raw_labels")

    # Étape 3 : résoudre les codes (MASTER) et libellés systématiques
    # (LIBELLE source='S'). Le left-join préserve les NULL côtés.
    grouped = (
        grouped.join(
            master_valid.rename({"SID": "dagger_sid", "code": "dagger_code"}),
            on="dagger_sid",
            how="left",
        )
        .join(
            master_valid.rename({"SID": "asterisk_sid", "code": "asterisk_code"}),
            on="asterisk_sid",
            how="left",
        )
        .join(
            sys_labels.rename({"SID": "dagger_sid", "sys_label": "dagger_label"}),
            on="dagger_sid",
            how="left",
        )
        .join(
            sys_labels.rename({"SID": "asterisk_sid", "sys_label": "asterisk_label"}),
            on="asterisk_sid",
            how="left",
        )
    )

    # Étape 4 : redundancy_level. `none` dès qu'une face manque ; les
    # paires complètes sortent `independent` (la curation YAML qui
    # peut les promouvoir à `subordinate` est faite en phase 3).
    grouped = grouped.with_columns(
        pl.when(pl.col("dagger_code").is_null() | pl.col("asterisk_code").is_null())
        .then(pl.lit("none"))
        .otherwise(pl.lit("independent"))
        .alias("redundancy_level")
    )

    # Étape 5 : tri déterministe (NULL en queue) puis association_id.
    grouped = (
        grouped.sort(["dagger_code", "asterisk_code"], nulls_last=True)
        .with_row_index("association_id")
        .with_columns(pl.col("association_id").cast(pl.Int64))
    )

    out = grouped.select(
        "association_id",
        "dagger_code",
        "dagger_label",
        "asterisk_code",
        "asterisk_label",
        "combination_labels",
        "levels_present",
        "redundancy_level",
        "source_lids",
    )

    EnrichedDaggerAsteriskSchema.validate(out)
    return out


@dataclass(frozen=True)
class CurationReport:
    """Compte-rendu de l'application du CSV de curation à la table DAGSTAR.

    Champs :
        n_subordinate_applied : paires curées 'subordinate' réellement
            propagées dans la table enrichie (présentes des deux côtés).
        n_independent_in_csv  : paires curées 'independent' lues dans
            le CSV (n'altèrent pas la table — c'est déjà la valeur par
            défaut — mais comptées pour audit).
        n_undecided           : paires en attente de décision
            (`redundancy_level` vide ou "undecided").
        n_orphan_in_csv       : paires dans le CSV mais absentes de la
            table enrichie. Warning, ignorées au merge.
        n_pairs_in_table_absent_from_csv : paires complètes de la table
            non couvertes par le CSV (gardent leur défaut 'independent').
    """

    n_subordinate_applied: int
    n_independent_in_csv: int
    n_undecided: int
    n_orphan_in_csv: int
    n_pairs_in_table_absent_from_csv: int

    def as_long_rows(self) -> list[dict[str, object]]:
        """Sérialisation long-format pour `reports/curation_applied.csv`."""
        return [
            {"dimension": "curation", "value": "subordinate_applied", "count": self.n_subordinate_applied},
            {"dimension": "curation", "value": "independent_in_csv", "count": self.n_independent_in_csv},
            {"dimension": "curation", "value": "undecided", "count": self.n_undecided},
            {"dimension": "coherence", "value": "csv_pairs_absent_from_table", "count": self.n_orphan_in_csv},
            {"dimension": "coherence", "value": "table_pairs_absent_from_csv", "count": self.n_pairs_in_table_absent_from_csv},
        ]


def _detect_csv_separator(path: Path) -> str:
    """Sniff léger sur la 1re ligne : `;` si dominant, sinon `,`.

    Excel FR sauvegarde les CSV avec `;` ; on tolère sans forcer
    l'utilisateur à reconvertir le fichier."""
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    return ";" if first_line.count(";") > first_line.count(",") else ","


def _read_curation_csv(path: Path) -> pl.DataFrame:
    """Lit le CSV de curation en tolérant le séparateur, valide les
    valeurs de `redundancy_level`.

    Lève `ValueError` si une valeur de `redundancy_level` sort de
    {'', 'independent', 'subordinate', 'undecided'}.
    """
    sep = _detect_csv_separator(path)
    df = pl.read_csv(path, infer_schema_length=0, separator=sep)
    for col in ("dagger_code", "asterisk_code", "redundancy_level"):
        if col not in df.columns:
            raise ValueError(
                f"CSV de curation invalide : colonne '{col}' manquante. "
                f"Colonnes lues : {df.columns}"
            )
    levels = df.get_column("redundancy_level").fill_null("").unique().to_list()
    invalid = [v for v in levels if v not in _VALID_CURATION_LEVELS]
    if invalid:
        raise ValueError(
            f"CSV de curation : valeurs invalides dans 'redundancy_level' : "
            f"{sorted(invalid)}. Admises : {sorted(_VALID_CURATION_LEVELS)}."
        )
    return df


def apply_curation(
    table: pl.DataFrame,
    curation_path: Path,
) -> tuple[pl.DataFrame, CurationReport]:
    """Applique le CSV de curation à la table DAGSTAR enrichie.

    - Les paires avec `redundancy_level=subordinate` dans le CSV
      voient leur valeur propagée dans la table.
    - Les paires `independent` (défaut), `undecided` ou vides
      n'altèrent pas la table.
    - Les paires du CSV absentes de la table sont logguées comme
      orphelines puis ignorées (cf. flag `_orphan` côté CSV).
    - Les paires `_orphan=True` côté CSV sont systématiquement
      ignorées (la curation référence un état révolu).

    Returns:
        (table_curée, rapport).
    """
    curation = _read_curation_csv(curation_path)

    # Exclure les lignes orphelines (le _orphan côté CSV signale une
    # paire absente d'une version précédente de la table — la curation
    # ne s'y applique plus).
    if "_orphan" in curation.columns:
        curation = curation.filter(
            ~pl.col("_orphan").fill_null("False").str.to_lowercase().is_in(["true", "1"])
        )

    sub = curation.filter(pl.col("redundancy_level") == "subordinate")
    indep = curation.filter(pl.col("redundancy_level") == "independent")
    undecided = curation.filter(
        pl.col("redundancy_level").fill_null("").is_in(["", "undecided"])
    )

    # Détection des paires orphelines : présentes dans le CSV (côté
    # subordinate ou independent — celles à effet) mais absentes de la table.
    table_keys = table.select(["dagger_code", "asterisk_code"])
    csv_with_decision = pl.concat([sub, indep], how="diagonal").select(
        ["dagger_code", "asterisk_code"]
    )
    orphans = csv_with_decision.join(
        table_keys, on=["dagger_code", "asterisk_code"], how="anti"
    )

    # Application : left join table ↔ subordinate, override redundancy_level.
    sub_keys = sub.select(
        pl.col("dagger_code"),
        pl.col("asterisk_code"),
        pl.lit("subordinate").alias("_curated_level"),
    )
    curated = (
        table.join(sub_keys, on=["dagger_code", "asterisk_code"], how="left")
        .with_columns(
            pl.coalesce([pl.col("_curated_level"), pl.col("redundancy_level")])
            .alias("redundancy_level")
        )
        .drop("_curated_level")
        .select(table.columns)
    )

    # Combien de paires complètes de la table ne sont pas couvertes par le CSV ?
    csv_keys_all = curation.select(["dagger_code", "asterisk_code"])
    complete_table = table.filter(
        pl.col("dagger_code").is_not_null() & pl.col("asterisk_code").is_not_null()
    )
    table_uncovered = complete_table.join(
        csv_keys_all, on=["dagger_code", "asterisk_code"], how="anti"
    )

    # Nombre effectivement appliqué = lignes sub jointes à la table
    # (orphans exclus). On le mesure via l'anti-join inverse.
    sub_applied = sub.join(table_keys, on=["dagger_code", "asterisk_code"], how="inner")

    report = CurationReport(
        n_subordinate_applied=sub_applied.height,
        n_independent_in_csv=indep.height,
        n_undecided=undecided.height,
        n_orphan_in_csv=orphans.height,
        n_pairs_in_table_absent_from_csv=table_uncovered.height,
    )

    EnrichedDaggerAsteriskSchema.validate(curated)
    return curated, report


def _build_summary(table: pl.DataFrame) -> pl.DataFrame:
    """Rapport long-format (dimension, value, count) pour faciliter la
    curation manuelle de la phase 2."""
    n = len(table)
    rows: list[dict[str, object]] = [
        {"dimension": "total", "value": "pairs", "count": n},
    ]

    # Complétude.
    both = int(
        (table["dagger_code"].is_not_null() & table["asterisk_code"].is_not_null()).sum()
    )
    dagger_only = int(
        (table["dagger_code"].is_not_null() & table["asterisk_code"].is_null()).sum()
    )
    asterisk_only = int(
        (table["dagger_code"].is_null() & table["asterisk_code"].is_not_null()).sum()
    )
    rows.extend(
        [
            {"dimension": "completeness", "value": "both_sides", "count": both},
            {"dimension": "completeness", "value": "dagger_only", "count": dagger_only},
            {"dimension": "completeness", "value": "asterisk_only", "count": asterisk_only},
        ]
    )

    # Distribution par lettre de chapitre du code dague (approximation
    # cheap : ne reconstruit pas le mapping bloc → chapitre rom ; sert
    # uniquement à orienter la curation).
    letter_counts = (
        table.with_columns(
            pl.col("dagger_code").str.slice(0, 1).alias("letter")
        )
        .group_by("letter")
        .len()
        .sort("letter", nulls_last=True)
    )
    for r in letter_counts.iter_rows(named=True):
        rows.append(
            {
                "dimension": "dagger_letter",
                "value": r["letter"] if r["letter"] is not None else "NULL",
                "count": int(r["len"]),
            }
        )

    # Distribution par levels_present (la liste triée sert de clé).
    levels_counts = (
        table.with_columns(
            pl.col("levels_present")
            .map_elements(lambda lst: ",".join(lst), return_dtype=pl.String)
            .alias("levels_key")
        )
        .group_by("levels_key")
        .len()
        .sort("len", descending=True)
    )
    for r in levels_counts.iter_rows(named=True):
        rows.append(
            {
                "dimension": "levels_present",
                "value": r["levels_key"],
                "count": int(r["len"]),
            }
        )

    # Distribution du nombre de combination_labels par paire (bucket).
    nlabels = table.with_columns(
        pl.col("combination_labels").list.len().alias("nb_labels")
    )
    for label, expr in [
        ("0", pl.col("nb_labels") == 0),
        ("1", pl.col("nb_labels") == 1),
        ("2_5", (pl.col("nb_labels") >= 2) & (pl.col("nb_labels") <= 5)),
        ("6_plus", pl.col("nb_labels") >= 6),
    ]:
        rows.append(
            {
                "dimension": "nb_combination_labels",
                "value": label,
                "count": int(nlabels.filter(expr).height),
            }
        )

    return pl.DataFrame(rows, schema={"dimension": pl.String, "value": pl.String, "count": pl.Int64})


def to_parquet_and_csv_and_report(
    ofs_dir: Path,
    processed_dir: Path,
    report_path: Path,
    curation_path: Path | None = None,
    curation_report_path: Path | None = None,
) -> tuple[Path, Path, Path]:
    """Lit les tables OFS brutes, construit la table enrichie,
    applique optionnellement la curation, écrit Parquet + CSV + rapports.

    Args:
        ofs_dir : répertoire OFS contenant MASTER/DAGSTAR/LIBELLE.txt.
        processed_dir : sortie des Parquet + CSV de la table.
        report_path : `reports/dagger_asterisk_summary.csv` (synthèse).
        curation_path : chemin du CSV de curation (optionnel).
        curation_report_path : `reports/curation_applied.csv`. Écrit
            uniquement si `curation_path` fourni.

    Returns:
        `(parquet_path, csv_path, report_path)`.
    """
    master = _read_ofs_table(ofs_dir / "MASTER.txt")
    dagstar = _read_ofs_table(ofs_dir / "DAGSTAR.txt")
    libelle = _read_ofs_table(ofs_dir / "LIBELLE.txt")

    table = build_dagger_asterisk_table(master, dagstar, libelle)

    if curation_path is not None:
        table, curation_report = apply_curation(table, curation_path)
        if curation_report_path is not None:
            curation_report_path.parent.mkdir(parents=True, exist_ok=True)
            pl.DataFrame(
                curation_report.as_long_rows(),
                schema={"dimension": pl.String, "value": pl.String, "count": pl.Int64},
            ).write_csv(curation_report_path)

    processed_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    parquet_path = processed_dir / "dagger_asterisk.parquet"
    csv_path = processed_dir / "dagger_asterisk.csv"
    table.write_parquet(parquet_path)
    # CSV ne supporte pas les colonnes List → sérialisation avec
    # séparateur ` | ` pour rester lisible. Le Parquet conserve les
    # types riches pour les consommateurs Python.
    table.with_columns(
        pl.col("combination_labels").list.join(" | "),
        pl.col("levels_present").list.join(","),
        pl.col("source_lids").cast(pl.List(pl.String)).list.join(","),
    ).write_csv(csv_path)
    _build_summary(table).write_csv(report_path)

    return parquet_path, csv_path, report_path
