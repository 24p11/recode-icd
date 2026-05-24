"""Helper de chargement pour exploration interactive — **dev only**.

⚠️  **Ce module est exclusivement réservé aux notebooks d'exploration
dans `scripts/explore/`.** Il ne doit JAMAIS être importé depuis le code
de production (`loaders/`, `merge.py`, `propagation.py`, `exporters/`,
`cli/`). Le code de production a ses propres loaders et schémas pandera ;
ce module-ci les bypasse pour aller plus vite côté exploration.

But : exposer un `ExplorationContext` qui regroupe en mémoire toutes
les sources brutes (tables OFS), le Parquet OWL/ANS, les artefacts du
pipeline (merged, propagated, flat) et les rapports CSV. Permet de
faire une analyse cross-source en une seule cellule, sans re-coder à
chaque fois la lecture des fichiers.

Usage typique dans un notebook ::

    from recode_icd.utils.loaders_dev import load_exploration_context

    ctx = load_exploration_context()
    ctx.ofs["master"].head()
    ctx.ans.filter(pl.col("code") == "A00.0")
    ctx.reports["note_merges"].filter(pl.col("difference_significative"))

En mode `lazy=True`, retourne des `LazyFrame` pour les très gros
fichiers (utile si on n'a besoin que d'un sous-ensemble) ::

    ctx = load_exploration_context(lazy=True)
    ctx.ofs["libelle"].filter(pl.col("source") == "S").collect()

Gestion des fichiers manquants : warning (via `logging`), pas
d'exception. Le champ correspondant vaut `None` ou est absent du dict.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

from recode_icd.loaders.ofs import _read as _read_ofs_table

log = logging.getLogger(__name__)

# Alias type — un slot peut contenir un DataFrame, un LazyFrame ou None.
type Frame = pl.DataFrame | pl.LazyFrame

# Tables OFS demandées par l'utilisateur — toutes en MAJUSCULES, fichier
# `<NAME>.txt` dans le dossier OFS. La clé exposée dans ctx.ofs est en
# minuscules (`master`, `libelle`, etc.).
_OFS_TABLES: tuple[str, ...] = (
    "MASTER",
    "LIBELLE",
    "INCLUDE",
    "EXCLUDE",
    "DESCR",
    "INDIR",
    "DAGSTAR",
    "NOTE",
    "MEMO",
    "SYSTEM",
    "COMMON",
    "CHAPTER",
    "REFER",
    "GLOSSAIRE",
)

# MEMO a une convention de quoting différente du reste de la base OFS
# (apostrophes doublées) — cf `loaders/ofs.py:_read`.
_OFS_TABLES_WITH_APOSTROPHE_QUOTING: frozenset[str] = frozenset({"MEMO"})

# Chemins OFS testés dans l'ordre (le premier qui existe gagne).
_OFS_PATH_CANDIDATES: tuple[str, ...] = (
    "referentials/raw/ofs",
    "referentials/raw/CIM_OFS_SW_2006",
    "data/CIM_OFS_SW_2006",
)

# ANS / Parquet OWL — noms candidats dans `referentials/processed/`.
_ANS_PARQUET_CANDIDATES: tuple[str, ...] = (
    "owl_ans.parquet",
    "owl_codes.parquet",
)

# Rapports CSV à charger si présents.
_REPORTS: tuple[str, ...] = (
    "note_merges.csv",
    "merge_conflicts.csv",
    "post_2006_codes.csv",
    "synthesized_skipped.csv",
    "sibling_exclusions_skipped.csv",
    "orphan_ofs_codes.csv",
)

@dataclass(frozen=True)
class ExplorationContext:
    """Snapshot mémoire des référentiels et artefacts pour exploration.

    Attributs :

    - `ofs` : dict des tables OFS indexé par nom en minuscules
      (`master`, `libelle`, `include`, `exclude`, `descr`, `indir`,
      `dagstar`, `note`, `memo`, `system`, `common`, `chapter`,
      `refer`, `glossaire`). Les tables manquantes sont absentes du dict.
    - `ans` : Parquet OWL/ANS (codes + propriétés enrichies) ou `None`
      si non trouvé.
    - `merged` : `merged_codes.parquet` (sortie de `merge.merge_codes`)
      ou `None`.
    - `propagated` : `propagated_notes.parquet` (sortie de
      `propagation.propagate`) ou `None`.
    - `flat` : `inclusions_exclusions_synonymes.csv` (CSV maître à 5
      colonnes) ou `None`.
    - `reports` : dict des rapports CSV indexé par nom de fichier
      sans extension (`note_merges`, `merge_conflicts`, etc.).

    En mode `lazy=True`, tous les frames sont des `LazyFrame`.
    """

    ofs: dict[str, Frame] = field(default_factory=dict)
    ans: Frame | None = None
    merged: Frame | None = None
    propagated: Frame | None = None
    flat: Frame | None = None
    reports: dict[str, Frame] = field(default_factory=dict)


def _find_ofs_dir(root: Path) -> Path | None:
    """Premier des _OFS_PATH_CANDIDATES qui existe sous root."""
    for candidate in _OFS_PATH_CANDIDATES:
        path = root / candidate
        if path.is_dir() and any(path.glob("*.txt")):
            return path
    return None


def _find_ans_parquet(processed_dir: Path) -> Path | None:
    for name in _ANS_PARQUET_CANDIDATES:
        path = processed_dir / name
        if path.is_file():
            return path
    return None


def _load_parquet(path: Path, lazy: bool) -> Frame | None:
    if not path.is_file():
        log.warning("Parquet absent : %s", path)
        return None
    if lazy:
        return pl.scan_parquet(path)
    return pl.read_parquet(path)


def _load_csv(path: Path, lazy: bool) -> Frame | None:
    if not path.is_file():
        log.warning("CSV absent : %s", path)
        return None
    if lazy:
        return pl.scan_csv(path)
    return pl.read_csv(path)


def _load_ofs_table(path: Path, name: str, lazy: bool) -> Frame | None:
    if not path.is_file():
        log.warning("Table OFS absente : %s", path)
        return None
    quote_char = "'" if name in _OFS_TABLES_WITH_APOSTROPHE_QUOTING else None
    try:
        df = _read_ofs_table(path, quote_char=quote_char)
    except Exception as exc:
        log.warning("Échec lecture %s : %s", path, exc)
        return None
    return df.lazy() if lazy else df


def load_exploration_context(
    root: Path | None = None,
    *,
    ofs_dir: Path | None = None,
    processed_dir: Path | None = None,
    reports_dir: Path | None = None,
    lazy: bool = False,
) -> ExplorationContext:
    """Charge en mémoire toutes les sources et artefacts pour exploration.

    Args :
        root : racine du projet. Par défaut, déduit du fichier actuel
            (`src/recode_icd/utils/loaders_dev.py` → 3 niveaux au-dessus).
        ofs_dir : dossier des fichiers OFS `.txt`. Par défaut, premier
            existant parmi `referentials/raw/ofs`,
            `referentials/raw/CIM_OFS_SW_2006`, `data/CIM_OFS_SW_2006`.
        processed_dir : dossier des Parquets dérivés. Par défaut
            `<root>/referentials/processed`.
        reports_dir : dossier des rapports CSV. Par défaut `<root>/reports`.
        lazy : si True, retourne des `LazyFrame` au lieu de `DataFrame`
            (utile pour les très gros fichiers que tu vas filtrer).

    Returns :
        `ExplorationContext` (dataclass frozen). Les sources manquantes
        sont traitées par un warning + champ vide (`None` ou absent du dict).

    Exemple :
        >>> from recode_icd.utils.loaders_dev import load_exploration_context
        >>> ctx = load_exploration_context()
        >>> ctx.ofs["master"].select(["SID", "code", "type"]).head()
        >>> ctx.reports["note_merges"].filter(pl.col("difference_significative"))
    """
    root = (root or _default_root()).resolve()

    actual_ofs_dir = ofs_dir or _find_ofs_dir(root)
    actual_processed = processed_dir or (root / "referentials" / "processed")
    actual_reports = reports_dir or (root / "reports")

    ofs: dict[str, Frame] = {}
    if actual_ofs_dir is None:
        log.warning(
            "Aucun dossier OFS trouvé sous %s (essayé : %s)",
            root,
            ", ".join(_OFS_PATH_CANDIDATES),
        )
    else:
        for table in _OFS_TABLES:
            path = actual_ofs_dir / f"{table}.txt"
            frame = _load_ofs_table(path, table, lazy=lazy)
            if frame is not None:
                ofs[table.lower()] = frame

    ans_path = _find_ans_parquet(actual_processed)
    ans = _load_parquet(ans_path, lazy=lazy) if ans_path else None
    if ans is None:
        log.warning(
            "ANS Parquet absent : essayé %s sous %s",
            ", ".join(_ANS_PARQUET_CANDIDATES),
            actual_processed,
        )

    merged = _load_parquet(actual_processed / "merged_codes.parquet", lazy=lazy)
    propagated = _load_parquet(actual_processed / "propagated_notes.parquet", lazy=lazy)
    flat = _load_csv(
        actual_processed / "inclusions_exclusions_synonymes.csv", lazy=lazy
    )

    reports: dict[str, Frame] = {}
    for fname in _REPORTS:
        path = actual_reports / fname
        frame = _load_csv(path, lazy=lazy)
        if frame is not None:
            reports[fname.removesuffix(".csv")] = frame

    return ExplorationContext(
        ofs=ofs,
        ans=ans,
        merged=merged,
        propagated=propagated,
        flat=flat,
        reports=reports,
    )


def _default_root() -> Path:
    # Ce fichier : src/recode_icd/utils/loaders_dev.py
    # Racine du projet : remonter 4 niveaux.
    return Path(__file__).resolve().parents[3]
