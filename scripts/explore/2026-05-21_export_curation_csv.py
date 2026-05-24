# ruff: noqa
"""Export CSV de curation pour les couples dague/astérisque.

Le CSV produit sert simultanément :
  - de support de curation manuelle (édité dans Excel) ;
  - de source de vérité consommée par le merger pour appliquer
    redundancy_level=subordinate et is_redundant_dagger=True.

Comportement :
  - 1er run    : crée le CSV avec les 4 colonnes de curation vides.
  - Runs N+1   : merge intelligent.
      * Paires de la table déjà dans le CSV → curation existante préservée.
      * Paires nouvelles                    → ajoutées, curation vide.
      * Paires plus en table mais dans CSV  → conservées, _orphan=True.

Voir docs/source_mapping.md §"Couples dague/astérisque".
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TABLE_PATH = _ROOT / "referentials" / "processed" / "dagger_asterisk.parquet"
DEFAULT_CSV_PATH = _ROOT / "referentials" / "curation" / "dagger_curation.csv"

KEY_COLS = ("dagger_code", "asterisk_code")
CURATION_COLS = ("redundancy_level", "rationale", "curated_by", "curated_date")

# Valeurs par défaut appliquées aux paires nouvelles (jamais vues dans le
# CSV). Modifier ici si la convention de curation évolue.
DEFAULT_REDUNDANCY_LEVEL = "independent"
DEFAULT_RATIONALE = ""
DEFAULT_CURATED_BY = "RF"
DEFAULT_CURATED_DATE = "21/05/2026"
EXPORT_COLS = (
    "dagger_code",
    "dagger_label",
    "asterisk_code",
    "asterisk_label",
    "combination_labels",
    "levels_present",
    "redundancy_level",
    "rationale",
    "curated_by",
    "curated_date",
    "_orphan",
)


# --------------------------------------------------------------------------- #
# Chargement / préparation
# --------------------------------------------------------------------------- #
def load_table(path: Path) -> pl.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Table dague/astérisque introuvable : {path}")
    return pl.read_parquet(path)


def _join_list_col(name: str, sep: str) -> pl.Expr:
    return (
        pl.col(name)
        .list.eval(pl.element().cast(pl.Utf8))
        .list.join(sep)
        .fill_null("")
        .alias(name)
    )


def prepare_from_table(df: pl.DataFrame) -> pl.DataFrame:
    """Sélectionne les paires complètes, formate les colonnes liste,
    initialise les colonnes de curation à vide. Tri stable par (dagger, ast)."""
    complete = df.filter(
        pl.col("dagger_code").is_not_null()
        & pl.col("asterisk_code").is_not_null()
    )
    return complete.select(
        pl.col("dagger_code").cast(pl.Utf8),
        pl.col("dagger_label").cast(pl.Utf8).fill_null(""),
        pl.col("asterisk_code").cast(pl.Utf8),
        pl.col("asterisk_label").cast(pl.Utf8).fill_null(""),
        _join_list_col("combination_labels", " | "),
        _join_list_col("levels_present", ", "),
        pl.lit(DEFAULT_REDUNDANCY_LEVEL, dtype=pl.Utf8).alias("redundancy_level"),
        pl.lit(DEFAULT_RATIONALE, dtype=pl.Utf8).alias("rationale"),
        pl.lit(DEFAULT_CURATED_BY, dtype=pl.Utf8).alias("curated_by"),
        pl.lit(DEFAULT_CURATED_DATE, dtype=pl.Utf8).alias("curated_date"),
        pl.lit(False, dtype=pl.Boolean).alias("_orphan"),
    ).sort(list(KEY_COLS))


def load_existing_csv(path: Path) -> pl.DataFrame:
    """Lit le CSV de curation, normalise les colonnes, cast `_orphan` en bool.

    Toutes les colonnes sont lues en str (infer_schema_length=0) pour rester
    tolérant aux variantes de typage Excel (TRUE/True/true, 1/0, etc.)."""
    df = pl.read_csv(path, infer_schema_length=0)
    for col in EXPORT_COLS:
        if col not in df.columns:
            default = "False" if col == "_orphan" else ""
            df = df.with_columns(pl.lit(default).alias(col))
    str_cols = [c for c in EXPORT_COLS if c != "_orphan"]
    df = df.with_columns([pl.col(c).fill_null("") for c in str_cols])
    df = df.with_columns(
        pl.col("_orphan")
        .fill_null("False")
        .str.to_lowercase()
        .is_in(["true", "1"])
        .alias("_orphan")
    )
    return df.select(list(EXPORT_COLS))


# --------------------------------------------------------------------------- #
# Merge
# --------------------------------------------------------------------------- #
def merge_with_existing(
    fresh: pl.DataFrame, existing: pl.DataFrame
) -> pl.DataFrame:
    """Fusionne fresh (depuis le parquet) et existing (depuis le CSV).

    Règles :
      - paire dans fresh ∩ existing : libellés depuis fresh, curation
        depuis existing ;
      - paire dans fresh seulement  : ajoutée, curation vide ;
      - paire dans existing seulement : conservée, _orphan=True.
    """
    key = list(KEY_COLS)
    existing_cur = existing.select(
        *key,
        *(pl.col(c).alias(f"__{c}") for c in CURATION_COLS),
    )
    enriched = (
        fresh.join(existing_cur, on=key, how="left")
        .with_columns(
            [
                # `__c` est null ssi la paire est nouvelle (absente du CSV
                # existant). Dans ce cas on garde le défaut porté par fresh.
                # Sinon on prend la valeur du CSV existant (y compris "")
                # pour respecter une éventuelle remise à blanc manuelle.
                pl.coalesce([pl.col(f"__{c}"), pl.col(c)]).alias(c)
                for c in CURATION_COLS
            ]
        )
        .drop(*(f"__{c}" for c in CURATION_COLS))
        .with_columns(pl.lit(False, dtype=pl.Boolean).alias("_orphan"))
        .select(list(EXPORT_COLS))
    )

    fresh_keys = fresh.select(key)
    orphans = existing.join(fresh_keys, on=key, how="anti")
    if orphans.height > 0:
        orphans = orphans.with_columns(
            pl.lit(True, dtype=pl.Boolean).alias("_orphan")
        ).select(list(EXPORT_COLS))
        out = pl.concat([enriched, orphans])
    else:
        out = enriched
    return out.sort(key)


# --------------------------------------------------------------------------- #
# Sortie
# --------------------------------------------------------------------------- #
def write_csv(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(path)


def print_stats(df: pl.DataFrame) -> None:
    total = df.height
    n_orphans = df.filter(pl.col("_orphan")).height
    dist = (
        df.filter(~pl.col("_orphan"))
        .group_by("redundancy_level")
        .len()
        .sort("redundancy_level")
    )
    print(f"  Total paires       : {total}")
    print("  Distribution redundancy_level (hors orphelines) :")
    for row in dist.iter_rows(named=True):
        label = row["redundancy_level"] or "(vide)"
        print(f"    - {label:<12s}: {row['len']}")
    if n_orphans > 0:
        print(
            f"  ⚠ Orphelines       : {n_orphans} "
            "(présentes dans le CSV mais plus dans la table DAGSTAR)"
        )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Export CSV de curation des couples dague/astérisque."
    )
    p.add_argument(
        "--table",
        type=Path,
        default=DEFAULT_TABLE_PATH,
        help="Chemin du parquet DAGSTAR enrichi.",
    )
    p.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help="Chemin du CSV de curation (créé ou merged).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        table = load_table(args.table)
    except FileNotFoundError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 2

    fresh = prepare_from_table(table)
    if args.csv.is_file():
        existing = load_existing_csv(args.csv)
        out = merge_with_existing(fresh, existing)
        action = "Merge"
    else:
        out = fresh
        action = "Création"

    write_csv(out, args.csv)
    print(f"{action} : {args.csv}")
    print_stats(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
