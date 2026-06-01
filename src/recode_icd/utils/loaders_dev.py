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
    "external_overlaps.csv",
    "external_orphan_codes.csv",
    "external_sources_summary.csv",
)

# Chemins par défaut des sources externes brutes (chargées seulement
# si `with_external=True`). Relatifs à la racine du projet.
_ORPHANET_XML_REL = (
    "data/Orphanet_Nomenclature_Pack_FR_2025/ORPHA_ICD10_mapping_fr_2025.xml"
)
_HECTOR_XLSX_REL = "data/CIM_APHP_2019/Dictionnaire_Hector_MAJ062019.xlsx"

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
    - `flat` : `inclusions_exclusions_synonymes.csv` (CSV maître à 11
      colonnes) ou `None`.
    - `ofs_codes` : `ofs_codes.parquet` (sortie agrégée du loader OFS,
      une ligne par code avec `inclusions`/`exclusions_text`/
      `synonymes`/`notes_editorial`) ou `None`.
    - `dagger_asterisk` : `dagger_asterisk.parquet` (table enrichie des
      paires dague/astérisque) ou `None`.
    - `external` : dict des sources externes BRUTES (sorties des
      loaders Phase 1), indexé par enum source (`ORPHANET`,
      `INDEX_CIM10_VOL3`, `APHP_*`). Vide sauf si
      `load_exploration_context(with_external=True)`.
    - `reports` : dict des rapports CSV indexé par nom de fichier
      sans extension (`note_merges`, `merge_conflicts`,
      `external_orphan_codes`, etc.).

    En mode `lazy=True`, tous les frames sont des `LazyFrame`
    (sauf `external` qui reste eager — les loaders externes ne sont
    pas lazy).
    """

    ofs: dict[str, Frame] = field(default_factory=dict)
    ans: Frame | None = None
    merged: Frame | None = None
    propagated: Frame | None = None
    flat: Frame | None = None
    ofs_codes: Frame | None = None
    dagger_asterisk: Frame | None = None
    external: dict[str, pl.DataFrame] = field(default_factory=dict)
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


def _load_external_frames(root: Path) -> dict[str, pl.DataFrame]:
    """Charge les sources externes BRUTES via les loaders Phase 1.

    Import local de `merge_external` (production) pour éviter un import
    circulaire au chargement du module et pour ne payer le coût (~5 s
    de parsing XML + xlsx) que si `with_external=True`.
    """
    from recode_icd.merge_external import load_external_frames

    orphanet_xml = root / _ORPHANET_XML_REL
    hector_xlsx = root / _HECTOR_XLSX_REL
    if not orphanet_xml.is_file() or not hector_xlsx.is_file():
        log.warning(
            "Sources externes introuvables (orphanet=%s, hector=%s) — "
            "ctx.external restera vide.",
            orphanet_xml.is_file(),
            hector_xlsx.is_file(),
        )
        return {}
    try:
        return load_external_frames(orphanet_xml, hector_xlsx)
    except Exception as exc:
        log.warning("Échec chargement sources externes : %s", exc)
        return {}


def load_exploration_context(
    root: Path | None = None,
    *,
    ofs_dir: Path | None = None,
    processed_dir: Path | None = None,
    reports_dir: Path | None = None,
    lazy: bool = False,
    with_external: bool = False,
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
        with_external : si True, charge aussi les sources externes
            BRUTES (ORPHANET, Index CIM-10 vol3, AP-HP) dans
            `ctx.external`. Coût ~5 s (parse XML + xlsx) — désactivé
            par défaut pour ne pas ralentir les notebooks usuels.

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
    ofs_codes = _load_parquet(actual_processed / "ofs_codes.parquet", lazy=lazy)
    dagger_asterisk = _load_parquet(
        actual_processed / "dagger_asterisk.parquet", lazy=lazy
    )

    reports: dict[str, Frame] = {}
    for fname in _REPORTS:
        path = actual_reports / fname
        frame = _load_csv(path, lazy=lazy)
        if frame is not None:
            reports[fname.removesuffix(".csv")] = frame

    external = _load_external_frames(root) if with_external else {}

    return ExplorationContext(
        ofs=ofs,
        ans=ans,
        merged=merged,
        propagated=propagated,
        flat=flat,
        ofs_codes=ofs_codes,
        dagger_asterisk=dagger_asterisk,
        external=external,
        reports=reports,
    )


def _default_root() -> Path:
    # Ce fichier : src/recode_icd/utils/loaders_dev.py
    # Racine du projet : remonter 4 niveaux.
    return Path(__file__).resolve().parents[3]


# ======================================================================
# inspect_code — rapport texte multi-source pour un code CIM-10
# ======================================================================
#
# Outil d'exploration interactif (dev only). PURE inspection : filtrage
# polars + formatage texte, AUCUNE transformation métier. Toutes les
# données viennent des Parquets/CSV déjà produits par le pipeline et
# chargés dans `ExplorationContext`.

_BOX_WIDTH = 70
# Au-delà, on tronque l'affichage des longues listes (ex : A52.7 a
# 2478 entrées CSV) pour rester lisible.
_MAX_LIST_DISPLAY = 40


def _eager(frame: Frame | None) -> pl.DataFrame | None:
    """Collecte un LazyFrame si besoin ; passe-plat pour un DataFrame."""
    if frame is None:
        return None
    if isinstance(frame, pl.LazyFrame):
        return frame.collect()
    return frame


def _print_box(title: str) -> None:
    inner = _BOX_WIDTH - 2
    print("╔" + "═" * inner + "╗")
    for chunk_start in range(0, max(len(title), 1), inner - 2):
        chunk = title[chunk_start : chunk_start + (inner - 2)]
        print("║ " + chunk.ljust(inner - 2) + " ║")
    print("╚" + "═" * inner + "╝")


def _section(title: str) -> None:
    bar = "─" * (_BOX_WIDTH - len(title) - 4)
    print(f"\n── {title} {bar}")


def _fmt_list(items: list[str] | None, indent: str = "    ") -> list[str]:
    """Formate une liste de textes pour affichage, avec troncature."""
    if not items:
        return [f"{indent}(aucune entrée)"]
    out = [f"{indent}- {it}" for it in items[:_MAX_LIST_DISPLAY]]
    if len(items) > _MAX_LIST_DISPLAY:
        out.append(f"{indent}… (+{len(items) - _MAX_LIST_DISPLAY} de plus)")
    return out


def _list_col(df: pl.DataFrame, col: str) -> list[str]:
    """Extrait une colonne (scalaire ou list[str]) en liste plate de str,
    en ignorant les nulls. Robuste aux colonnes absentes."""
    if df.is_empty() or col not in df.columns:
        return []
    dtype = df.schema[col]
    if dtype == pl.List(pl.String):
        vals = df.select(pl.col(col).explode()).to_series().drop_nulls().to_list()
    else:
        vals = df.select(pl.col(col)).to_series().drop_nulls().to_list()
    # Aplatit les éventuelles sous-listes restantes + cast str.
    flat: list[str] = []
    for v in vals:
        if v is None:
            continue
        if isinstance(v, list):
            flat.extend(str(x) for x in v if x is not None)
        else:
            flat.append(str(v))
    return flat


def _resolve_codes(raw: str, flat_codes: set[str], known_codes: set[str]) -> list[str]:
    """Résout un token en liste de codes :
    - code exact présent dans le CSV final → [code] seul
    - sinon préfixe : tous les codes du CSV final qui commencent par `raw`
    - sinon, si le code existe ailleurs (merged) → [raw] littéral
    - sinon → [raw] littéral (les blocs afficheront "absent / inconnu")
    """
    if raw in flat_codes:
        return [raw]
    prefixed = sorted(c for c in flat_codes if c.startswith(raw))
    if prefixed:
        return prefixed
    if raw in known_codes:
        return [raw]
    return [raw]


def _parent_label(merged: pl.DataFrame | None, code: str) -> str:
    if merged is None or not code:
        return ""
    row = merged.filter(pl.col("code") == code)
    if row.is_empty():
        return ""
    return row.select("label").row(0)[0] or ""


def _print_bloc1_identite(
    code: str,
    merged: pl.DataFrame | None,
    ofs_codes: pl.DataFrame | None,
    ans: pl.DataFrame | None,
) -> None:
    _section("BLOC 1 : IDENTITÉ")
    merged_row = (
        merged.filter(pl.col("code") == code) if merged is not None else None
    )
    ofs_row = (
        ofs_codes.filter(pl.col("code").str.strip_chars("()") == code)
        if ofs_codes is not None
        else None
    )
    ans_row = ans.filter(pl.col("code") == code) if ans is not None else None

    lib_ofs = (
        ofs_row.select("label").row(0)[0]
        if ofs_row is not None and not ofs_row.is_empty()
        else None
    )
    lib_ans = (
        ans_row.select("label").row(0)[0]
        if ans_row is not None and not ans_row.is_empty()
        else None
    )
    print(f"Code         : {code}")
    print(f"Libellé OFS  : {lib_ofs or '(absent)'}")
    print(f"Libellé ANS  : {lib_ans or '(absent)'}")

    if merged_row is not None and not merged_row.is_empty():
        r = merged_row.row(0, named=True)
        print(f"Type         : {r['type']}")
        # path = "I/A15-A19/A18/A18.1" → chapitre / bloc / catégorie.
        parts = (r.get("path") or "").split("/")
        if len(parts) >= 1 and parts[0]:
            print(f"Chapitre     : {parts[0]} — {_parent_label(merged, parts[0])}")
        if len(parts) >= 2:
            print(f"Bloc         : {parts[1]} — {_parent_label(merged, parts[1])}")
        if len(parts) >= 3:
            print(f"Catégorie    : {parts[2]} — {_parent_label(merged, parts[2])}")
    else:
        print("Type         : (code absent de merged_codes)")


def _print_bloc2_sources(
    code: str,
    ofs_codes: pl.DataFrame | None,
    ans: pl.DataFrame | None,
    external: dict[str, pl.DataFrame],
) -> None:
    _section("BLOC 2 : SOURCES BRUTES (avant fusion)")

    # --- OFS ---
    print("[OFS]")
    ofs_row = (
        ofs_codes.filter(pl.col("code").str.strip_chars("()") == code)
        if ofs_codes is not None
        else None
    )
    if ofs_row is None or ofs_row.is_empty():
        print("    (aucune entrée)")
    else:
        print("  Inclusions :")
        for line in _fmt_list(_list_col(ofs_row, "inclusions"), "    "):
            print(line)
        print("  Exclusions :")
        for line in _fmt_list(_list_col(ofs_row, "exclusions_text"), "    "):
            print(line)
        print("  Descripteurs / synonymes :")
        for line in _fmt_list(_list_col(ofs_row, "synonymes"), "    "):
            print(line)
        print("  Notes éditoriales :")
        for line in _fmt_list(_list_col(ofs_row, "notes_editorial"), "    "):
            print(line)

    # --- ANS ---
    print("\n[ANS]")
    ans_row = ans.filter(pl.col("code") == code) if ans is not None else None
    if ans_row is None or ans_row.is_empty():
        print("    (aucune entrée)")
    else:
        print("  Inclusions :")
        for line in _fmt_list(_list_col(ans_row, "inclusion_note"), "    "):
            print(line)
        print("  Exclusions :")
        for line in _fmt_list(_list_col(ans_row, "exclusion_notes"), "    "):
            print(line)
        print("  Synonymes :")
        for line in _fmt_list(_list_col(ans_row, "synonymes"), "    "):
            print(line)
        notes = _list_col(ans_row, "definitions") + _list_col(ans_row, "scope_notes")
        print("  Notes (définitions / scope) :")
        for line in _fmt_list(notes, "    "):
            print(line)

    # --- Sources externes ---
    print("\n[SOURCES EXTERNES]")
    if not external:
        print("    (sources externes non chargées — relancer avec "
              "load_exploration_context(with_external=True))")
        return
    any_external = False
    for source_label, df in external.items():
        sub = df.filter(pl.col("code") == code)
        if sub.is_empty():
            continue
        any_external = True
        # Pour ORPHANET, on annote la relation (E/NTBT) depuis metadata.
        if source_label == "ORPHANET" and "metadata" in sub.columns:
            items = [
                f"{r['libelle']}  [{r['type']}, "
                f"{r['metadata'].get('relation', '?') if r['metadata'] else '?'}]"
                for r in sub.iter_rows(named=True)
            ]
        else:
            items = [f"{r['libelle']}  [{r['type']}]" for r in sub.iter_rows(named=True)]
        print(f"  {source_label} ({len(items)}) :")
        for line in _fmt_list(items, "    "):
            print(line)
    if not any_external:
        print("    (aucune entrée externe pour ce code)")


def _print_bloc3_dagger(code: str, dagger: pl.DataFrame | None) -> None:
    _section("BLOC 3 : RELATIONS DAGUE/ASTÉRISQUE")
    if dagger is None:
        print("    (table dague/astérisque non chargée)")
        return
    involved = dagger.filter(
        (pl.col("dagger_code") == code) | (pl.col("asterisk_code") == code)
    )
    if involved.is_empty():
        print("    (pas d'association dague/astérisque)")
        return
    for r in involved.iter_rows(named=True):
        role = "dague (†)" if r["dagger_code"] == code else "astérisque (*)"
        partner_code = (
            r["asterisk_code"] if r["dagger_code"] == code else r["dagger_code"]
        )
        partner_label = (
            r["asterisk_label"] if r["dagger_code"] == code else r["dagger_label"]
        )
        print(
            f"  • {code} est {role} ; apparié à "
            f"{partner_code or '(aucun)'} — {partner_label or ''}"
        )
        print(
            f"      redundancy_level={r['redundancy_level']} ; "
            f"levels_present={r['levels_present']}"
        )


def _print_bloc4_final(
    code: str,
    flat: pl.DataFrame | None,
    orphan_report: pl.DataFrame | None,
) -> None:
    _section("BLOC 4 : RÉSULTAT FINAL (CSV)")
    if flat is None:
        print("    (CSV final non chargé)")
        return
    sub = flat.filter(pl.col("code") == code)
    if sub.is_empty():
        print("    Code absent du CSV final.")
        if orphan_report is not None:
            orph = orphan_report.filter(pl.col("code") == code)
            if not orph.is_empty():
                cats = sorted(set(orph["categorie_orphan"].to_list()))
                srcs = sorted(set(orph["source_externe"].to_list()))
                print(
                    f"    → présent dans external_orphan_codes.csv : "
                    f"catégorie(s)={cats}, source(s)={srcs}"
                )
            else:
                print("    → ni dans le CSV, ni dans external_orphan_codes.csv.")
        return

    # Compte par (type, source). Tri secondaire (type, source) pour
    # un ordre déterministe en cas d'égalité de count (group_by polars
    # n'est pas stable).
    print(f"  {sub.height} ligne(s). Répartition par (type, source) :")
    counts = sub.group_by("type", "source").len().sort(
        ["len", "type", "source"], descending=[True, False, False]
    )
    for r in counts.iter_rows(named=True):
        print(f"    {r['type']:10s} | {r['source']:28s} : {r['len']}")

    # Détail des lignes (tronqué).
    print("\n  Détail (type | source | source_level | inherited_from | texte) :")
    shown = sub.head(_MAX_LIST_DISPLAY)
    for r in shown.iter_rows(named=True):
        parent = r["inherited_from_code"] or ""
        texte = (r["texte"] or "")[:50]
        print(
            f"    {r['type']:9s} | {r['source']:22s} | "
            f"{r['source_level']:8s} | {parent:9s} | {texte}"
        )
    if sub.height > _MAX_LIST_DISPLAY:
        print(f"    … (+{sub.height - _MAX_LIST_DISPLAY} lignes de plus)")


# ----------------------------------------------------------------------
# Blocs supplémentaires en mode verbose (debug)
# ----------------------------------------------------------------------


# Tables OFS reliées au SID maître. Pour chaque table on indique les
# colonnes à afficher (clé de filtrage = SID, sauf cas particuliers).
_OFS_TABLES_BY_SID: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("libelle", ("LID", "source", "valid", "libelle")),
    ("include", ("LID",)),
    ("exclude", ("LID", "excl", "plus", "daget")),
    ("descr", ("LID",)),
    ("indir", ("LID",)),
    ("note", ("MID",)),
    ("dagstar", ("SID", "assoc", "daget", "plus")),
)
# Colonnes OWL à inspecter dans le BLOC 2bis ANS (liste vs scalaire).
_OWL_LIST_COLS = (
    "synonymes",
    "exclusion_notes",
    "definitions",
    "scope_notes",
    "structured_exclusions",
)
_OWL_SCALAR_COLS = ("inclusion_note",)


def _print_bloc2bis_raw(code: str, ctx: ExplorationContext) -> None:
    """Affiche les données brutes OFS (tables liées au SID) et ANS
    (propriétés agrégées du Parquet `owl_codes`)."""
    _section("BLOC 2bis : DONNÉES BRUTES (DEBUG)")

    # --- OFS ---
    print("[OFS — Tables brutes liées au SID]")
    master = _eager(ctx.ofs.get("master"))
    if master is None:
        print("    (table MASTER absente du contexte)")
    else:
        master_row = master.filter(pl.col("code") == code)
        if master_row.is_empty():
            print(f"    (code {code} absent de MASTER OFS)")
        else:
            r = master_row.row(0, named=True)
            sid = r.get("SID")
            print(
                f"  MASTER  : 1 ligne — SID={sid}, code={r.get('code')}, "
                f"type={r.get('type')}, level={r.get('level')}, "
                f"abbrev={r.get('abbrev')}"
            )
            for table_name, cols in _OFS_TABLES_BY_SID:
                tbl = _eager(ctx.ofs.get(table_name))
                if tbl is None:
                    continue
                if table_name == "dagstar":
                    sub = tbl.filter(
                        (pl.col("SID") == sid) | (pl.col("assoc") == sid)
                    )
                else:
                    sub = tbl.filter(pl.col("SID") == sid)
                if sub.is_empty():
                    continue
                # Pour include/exclude/descr/indir : joindre libelle
                # pour afficher le texte associé au LID.
                libelle = _eager(ctx.ofs.get("libelle"))
                if (
                    table_name in {"include", "exclude", "descr", "indir"}
                    and libelle is not None
                ):
                    sub = sub.join(
                        libelle.select("LID", "libelle"), on="LID", how="left"
                    )
                print(f"  {table_name.upper():7s} : {sub.height} ligne(s)")
                # Préfixe SID + cols spécifiques + libelle joint (si
                # présent) ; dédup en préservant l'ordre.
                ordered = list(dict.fromkeys(["SID", *cols, "libelle"]))
                display_cols = [c for c in ordered if c in sub.columns]
                for row in sub.head(8).iter_rows(named=True):
                    parts = []
                    for c in display_cols:
                        v = row.get(c)
                        if v is None:
                            continue
                        s = str(v)
                        if len(s) > 70:
                            s = s[:67] + "…"
                        parts.append(f"{c}={s}")
                    print("    " + " | ".join(parts))
                if sub.height > 8:
                    print(f"    … (+{sub.height - 8} ligne(s) de plus)")

    # --- ANS ---
    print("\n[ANS — Propriétés agrégées (owl_codes.parquet)]")
    ans = _eager(ctx.ans)
    if ans is None:
        print("    (Parquet OWL absent du contexte)")
        return
    ans_row = ans.filter(pl.col("code") == code)
    if ans_row.is_empty():
        print(f"    (code {code} absent d'owl_codes.parquet)")
        return
    r = ans_row.row(0, named=True)
    print(f"  rdfs:label          : {r.get('label')}")
    print(f"  dc:type             : {r.get('type')}")
    for col in _OWL_SCALAR_COLS:
        val = r.get(col)
        if val:
            text = str(val).replace("\n", "\n      ")
            print(f"  {col:20s}: {text[:300]}")
    for col in _OWL_LIST_COLS:
        items = r.get(col) or []
        if items:
            print(f"  {col:20s}: ({len(items)} valeur(s))")
            for item in list(items)[:8]:
                print(f"    - {item}")
            if len(items) > 8:
                print(f"    … (+{len(items) - 8} de plus)")


def _count_text_in_owl(code: str, text: str, ans: pl.DataFrame | None) -> int:
    """Compte les occurrences strictes du texte dans owl_codes pour ce
    code (parmi les listes + scalaires). 0 ou 1 typiquement."""
    if ans is None:
        return 0
    row = ans.filter(pl.col("code") == code)
    if row.is_empty():
        return 0
    r = row.row(0, named=True)
    n = 0
    for col in _OWL_LIST_COLS:
        items = r.get(col) or []
        n += sum(1 for v in items if v == text)
    for col in _OWL_SCALAR_COLS:
        val = r.get(col)
        if val and (val == text or text in str(val)):
            n += 1
    return n


def _count_text_in_merged(code: str, text: str, merged: pl.DataFrame | None) -> int:
    """Compte les occurrences strictes du texte dans merged_codes pour
    ce code (colonnes lists inclusions/exclusions/synonymes/etc.)."""
    if merged is None:
        return 0
    row = merged.filter(pl.col("code") == code)
    if row.is_empty():
        return 0
    r = row.row(0, named=True)
    n = 0
    for col in ("inclusions", "exclusions", "synonymes",
                "notes_editorial", "definitions", "scope_notes"):
        items = r.get(col) or []
        n += sum(1 for v in items if v == text)
    return n


def _print_bloc5_pipeline(code: str, ctx: ExplorationContext) -> None:
    """Affiche les compteurs de lignes du code à chaque étape du pipeline,
    plus un sous-tableau de traçage des textes les plus dupliqués dans
    le CSV final."""
    _section("BLOC 5 : PARCOURS DANS LE PIPELINE (DEBUG)")

    ofs_codes = _eager(ctx.ofs_codes)
    ans = _eager(ctx.ans)
    merged = _eager(ctx.merged)
    propagated = _eager(ctx.propagated)
    flat = _eager(ctx.flat)
    dagger = _eager(ctx.dagger_asterisk)

    def _n(df: pl.DataFrame | None) -> int:
        return 0 if df is None else df.filter(pl.col("code") == code).height

    n_ofs = _n(ofs_codes)
    n_owl = _n(ans)
    n_merged = _n(merged)
    n_prop = _n(propagated)
    n_flat = _n(flat)
    delta_prop = n_prop - n_merged
    delta_flat = n_flat - n_prop

    # Nombre de paires dague/astérisque impliquant ce code (pour
    # qualifier l'origine de Δ2).
    n_pairs = 0
    if dagger is not None:
        n_pairs = dagger.filter(
            (pl.col("dagger_code") == code) | (pl.col("asterisk_code") == code)
        ).height

    rows = [
        ("RDF ANS brut (triples)", "(non chargé — coût ~3,5 s)", ""),
        ("ofs_codes.parquet", str(n_ofs), ""),
        ("owl_codes.parquet", str(n_owl), ""),
        ("merged_codes.parquet", str(n_merged), ""),
        (
            "propagated_notes.parquet",
            str(n_prop),
            f"Δ1 = +{delta_prop} (propagation)" if delta_prop else "Δ1 = 0",
        ),
        (
            "flat_csv (CSV final)",
            str(n_flat),
            f"Δ2 = +{delta_flat} (expansion + synonymes + externes)"
            if delta_flat
            else "Δ2 = 0",
        ),
    ]
    label_w = max(len(r[0]) for r in rows)
    count_w = max(len(r[1]) for r in rows)
    print(f"  {'Étape':<{label_w}} | {'Nb lignes':<{count_w}} | Variation")
    print(f"  {'-' * label_w}-|-{'-' * count_w}-|----------")
    for label, count, var in rows:
        print(f"  {label:<{label_w}} | {count:<{count_w}} | {var}")
    print()
    if delta_prop:
        print(f"  → Δ1 = {delta_prop} : héritage hiérarchique détecté.")
    if delta_flat:
        if n_pairs:
            print(
                f"  → Δ2 = {delta_flat} : {n_pairs} paire(s) dague/astérisque "
                f"impliquant {code} → expansion attendue, plus synonymes/externes."
            )
        else:
            print(
                f"  → Δ2 = {delta_flat} : aucune paire dague/astérisque "
                f"pour {code} → Δ2 vient des synonymes et sources externes seuls."
            )

    # Sous-tableau : traçage des textes les plus dupliqués dans flat.
    # Tri prioritaire sur les textes qui transitent par
    # `propagated_notes` — c'est là que le saut 1→N révèle l'expansion
    # dague/astérisque (cas A01.0 "Infection due à Salmonella typhi").
    # Les synonymes Index restant en deuxième position (count=N sans
    # passage par propagated) sont moins diagnostiques.
    if flat is None:
        return
    flat_sub = flat.filter(pl.col("code") == code)
    if flat_sub.is_empty():
        return
    flat_counts = (
        flat_sub.group_by("texte")
        .len()
        .rename({"len": "flat_count"})
        .filter(pl.col("flat_count") > 1)
    )
    if flat_counts.is_empty():
        return
    if propagated is not None:
        prop_counts = (
            propagated.filter(pl.col("code") == code)
            .group_by("texte")
            .len()
            .rename({"len": "prop_count"})
        )
    else:
        prop_counts = pl.DataFrame(
            schema={"texte": pl.String, "prop_count": pl.UInt32}
        )
    joined = (
        flat_counts.join(prop_counts, on="texte", how="left")
        .with_columns(pl.col("prop_count").fill_null(0))
        .with_columns((pl.col("prop_count") > 0).alias("_via_prop"))
        .sort(
            ["_via_prop", "flat_count", "texte"],
            descending=[True, True, False],
        )
        .head(5)
    )
    print()
    print(f"  Traçage des {joined.height} texte(s) dupliqué(s) dans flat_csv")
    print(
        "  (textes transitant par propagated_notes affichés en premier — "
        "le saut N→M y révèle l'expansion) :"
    )
    for r in joined.iter_rows(named=True):
        text = r["texte"] or ""
        n_owl_t = _count_text_in_owl(code, text, ans)
        n_merged_t = _count_text_in_merged(code, text, merged)
        n_prop_t = r["prop_count"]
        n_flat_t = r["flat_count"]
        preview = text.replace("\n", "\\n")[:60]
        print(f'\n    "{preview}"')
        print(
            f"      owl_codes={n_owl_t} | merged_codes={n_merged_t} | "
            f"propagated_notes={n_prop_t} | flat_csv={n_flat_t}"
        )


def inspect_code(
    codes: str | list[str],
    ctx: ExplorationContext | None = None,
    *,
    verbose: bool = False,
) -> None:
    """Affiche un rapport texte complet pour un ou plusieurs codes CIM-10.

    Args :
        codes : un code exact ("A18.1"), un préfixe ("A18" qui matche
            A18.0..A18.9), ou une liste de codes/préfixes.
        ctx : contexte d'exploration. Si None, appelle
            `load_exploration_context(with_external=True)` automatiquement
            (les sources externes brutes sont nécessaires au BLOC 2).
        verbose : si True, ajoute deux blocs de debug : `BLOC 2bis`
            (données brutes OFS table par table + propriétés agrégées
            ANS) et `BLOC 5` (compteurs de lignes du code à chaque
            étape du pipeline + traçage des textes dupliqués). Utile
            pour diagnostiquer des cas comme A01.0 où un texte
            apparaît N fois dans le CSV à cause de l'expansion
            dague/astérisque.

    Outil d'inspection dev only — affichage texte, pas de valeur de
    retour.
    """
    if ctx is None:
        ctx = load_exploration_context(with_external=True)

    flat = _eager(ctx.flat)
    merged = _eager(ctx.merged)
    ofs_codes = _eager(ctx.ofs_codes)
    ans = _eager(ctx.ans)
    dagger = _eager(ctx.dagger_asterisk)
    orphan_report = _eager(ctx.reports.get("external_orphan_codes"))

    flat_codes = (
        set(flat["code"].unique().to_list()) if flat is not None else set()
    )
    known_codes = (
        set(merged["code"].unique().to_list()) if merged is not None else set()
    )

    tokens = [codes] if isinstance(codes, str) else list(codes)
    resolved: list[str] = []
    for tok in tokens:
        for c in _resolve_codes(tok, flat_codes, known_codes):
            if c not in resolved:
                resolved.append(c)

    if not resolved:
        print("Aucun code à inspecter.")
        return

    for code in resolved:
        lib = ""
        if merged is not None:
            row = merged.filter(pl.col("code") == code)
            if not row.is_empty():
                lib = row.select("label").row(0)[0] or ""
        print()
        _print_box(f"{code} — {lib}" if lib else f"{code} — (libellé inconnu)")
        _print_bloc1_identite(code, merged, ofs_codes, ans)
        _print_bloc2_sources(code, ofs_codes, ans, ctx.external)
        if verbose:
            _print_bloc2bis_raw(code, ctx)
        _print_bloc3_dagger(code, dagger)
        _print_bloc4_final(code, flat, orphan_report)
        if verbose:
            _print_bloc5_pipeline(code, ctx)
        print()
