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
import rdflib

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
    "guide_mco_associations_ensemble.csv",
)

# Chemins par défaut des sources externes brutes (chargées seulement
# si `with_external=True`). Relatifs à la racine du projet.
_ORPHANET_XML_REL = "data/Orphanet_Nomenclature_Pack_FR_2025/ORPHA_ICD10_mapping_fr_2025.xml"
_HECTOR_XLSX_REL = "data/CIM_APHP_2019/Dictionnaire_Hector_MAJ062019.xlsx"
_CEPIDC_CSV_REL = "data/CIM_CEPIDC_2015/CepiDc_Dictionnaire2015.csv"

# Chemins candidats du RDF ANS (chargé seulement si `load_rdf=True`).
_RDF_PATH_CANDIDATES: tuple[str, ...] = (
    "data/CIM_ANS_2026/dat/terminologie-cim-10-2025-01-01.rdf",
    "referentials/raw/terminologie-cim-10-2025-01-01.rdf",
)

# Cache module-level du graphe RDF (3,5 s de parse à éviter de payer
# plusieurs fois quand `load_exploration_context(load_rdf=True)` est
# rappelé dans un notebook).
_ANS_GRAPH_CACHE: dict[Path, rdflib.Graph] = {}


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
    - `ofs_dagger_asterisk` : `ofs_dagger_asterisk.parquet` (paires
      dérivées de DAGSTAR OFS, avant audit ANS) ou `None`.
    - `owl_dagger_asterisk` : `owl_dagger_asterisk.parquet` (paires
      dérivées des relations `atih-cim10:hasCausality` /
      `hasManifestation` côté ANS, pour audit de cohérence) ou `None`.
    - `recommendations` : `recommendations.parquet` (consignes du guide
      méthodologique MCO, une ligne par consigne) ou `None`.
    - `recommendation_codes` : `recommendation_codes.parquet` (cibles
      des consignes résolues aux codes feuilles, avec `role`,
      `centralite`, `type_expr` et `specificite`) ou `None`.
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
    ofs_dagger_asterisk: Frame | None = None
    owl_dagger_asterisk: Frame | None = None
    recommendations: Frame | None = None
    recommendation_codes: Frame | None = None
    external: dict[str, pl.DataFrame] = field(default_factory=dict)
    reports: dict[str, Frame] = field(default_factory=dict)
    # Graphe RDF ANS chargé via rdflib (opt-in via `load_rdf=True`).
    # Utilisé par `inspect_code_extended` pour exposer toutes les
    # propriétés RDF d'un code, y compris celles non extraites par
    # smt2parquet (xkos:exclusionNote, atih-cim10:hasCausality, etc.).
    ans_graph: rdflib.Graph | None = None


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


def _find_rdf_path(root: Path) -> Path | None:
    """Premier des _RDF_PATH_CANDIDATES qui existe sous root."""
    for candidate in _RDF_PATH_CANDIDATES:
        path = root / candidate
        if path.is_file():
            return path
    return None


def _load_ans_graph(rdf_path: Path) -> rdflib.Graph | None:
    """Charge le RDF ANS avec cache module-level.

    Coût : ~3,5 s la première fois pour 151 647 triplets. Les appels
    suivants sont instantanés (même processus Python).
    """
    cached = _ANS_GRAPH_CACHE.get(rdf_path)
    if cached is not None:
        return cached
    try:
        import rdflib
    except ImportError:
        log.warning("rdflib non installé — ans_graph restera None.")
        return None
    g = rdflib.Graph()
    try:
        g.parse(rdf_path.as_posix())
    except Exception as exc:
        log.warning("Échec parse RDF %s : %s", rdf_path, exc)
        return None
    _ANS_GRAPH_CACHE[rdf_path] = g
    return g


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
            "Sources externes introuvables (orphanet=%s, hector=%s) — ctx.external restera vide.",
            orphanet_xml.is_file(),
            hector_xlsx.is_file(),
        )
        return {}
    # CepiDc est optionnel côté `load_external_frames` : on ne le passe
    # que si le CSV est présent, sinon le chargement se poursuit sans lui
    # (mêmes conditions que `recode-icd build external`).
    cepidc_path = root / _CEPIDC_CSV_REL
    cepidc_csv: Path | None = cepidc_path if cepidc_path.is_file() else None
    if cepidc_csv is None:
        log.warning("CSV CepiDc introuvable (%s) — ctx.external sera sans CepiDc.", cepidc_path)
    try:
        return load_external_frames(orphanet_xml, hector_xlsx, cepidc_csv)
    except Exception as exc:
        log.warning("Échec chargement sources externes : %s", exc)
        return {}


def load_exploration_context(
    root: Path | None = None,
    *,
    ofs_dir: Path | None = None,
    processed_dir: Path | None = None,
    reports_dir: Path | None = None,
    rdf_path: Path | None = None,
    lazy: bool = False,
    with_external: bool = False,
    load_rdf: bool = False,
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
        rdf_path : chemin explicite du RDF ANS. Par défaut, premier
            existant parmi `_RDF_PATH_CANDIDATES`. Ignoré si
            `load_rdf=False`.
        load_rdf : si True, charge le graphe RDF ANS dans `ctx.ans_graph`
            via rdflib. Coût ~3,5 s la première fois (cache
            module-level pour les appels suivants). Requis pour
            `inspect_code_extended`. Désactivé par défaut.

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
    flat = _load_csv(actual_processed / "inclusions_exclusions_synonymes.csv", lazy=lazy)
    ofs_codes = _load_parquet(actual_processed / "ofs_codes.parquet", lazy=lazy)
    dagger_asterisk = _load_parquet(actual_processed / "dagger_asterisk.parquet", lazy=lazy)
    ofs_dagger_asterisk = _load_parquet(actual_processed / "ofs_dagger_asterisk.parquet", lazy=lazy)
    owl_dagger_asterisk = _load_parquet(actual_processed / "owl_dagger_asterisk.parquet", lazy=lazy)
    recommendations = _load_parquet(actual_processed / "recommendations.parquet", lazy=lazy)
    recommendation_codes = _load_parquet(
        actual_processed / "recommendation_codes.parquet", lazy=lazy
    )

    reports: dict[str, Frame] = {}
    for fname in _REPORTS:
        path = actual_reports / fname
        frame = _load_csv(path, lazy=lazy)
        if frame is not None:
            reports[fname.removesuffix(".csv")] = frame

    external = _load_external_frames(root) if with_external else {}

    ans_graph: rdflib.Graph | None = None
    if load_rdf:
        actual_rdf = rdf_path or _find_rdf_path(root)
        if actual_rdf is None:
            log.warning(
                "RDF ANS introuvable sous %s (essayé : %s) — ans_graph=None",
                root,
                ", ".join(_RDF_PATH_CANDIDATES),
            )
        else:
            ans_graph = _load_ans_graph(actual_rdf)

    return ExplorationContext(
        ofs=ofs,
        ans=ans,
        merged=merged,
        propagated=propagated,
        flat=flat,
        ofs_codes=ofs_codes,
        dagger_asterisk=dagger_asterisk,
        ofs_dagger_asterisk=ofs_dagger_asterisk,
        owl_dagger_asterisk=owl_dagger_asterisk,
        recommendations=recommendations,
        recommendation_codes=recommendation_codes,
        external=external,
        reports=reports,
        ans_graph=ans_graph,
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
    merged_row = merged.filter(pl.col("code") == code) if merged is not None else None
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
        print(
            "    (sources externes non chargées — relancer avec "
            "load_exploration_context(with_external=True))"
        )
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
    involved = dagger.filter((pl.col("dagger_code") == code) | (pl.col("asterisk_code") == code))
    if involved.is_empty():
        print("    (pas d'association dague/astérisque)")
        return
    for r in involved.iter_rows(named=True):
        role = "dague (†)" if r["dagger_code"] == code else "astérisque (*)"
        partner_code = r["asterisk_code"] if r["dagger_code"] == code else r["dagger_code"]
        partner_label = r["asterisk_label"] if r["dagger_code"] == code else r["dagger_label"]
        print(
            f"  • {code} est {role} ; apparié à {partner_code or '(aucun)'} — {partner_label or ''}"
        )
        print(
            f"      redundancy_level={r['redundancy_level']} ; levels_present={r['levels_present']}"
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
    counts = (
        sub.group_by("type", "source")
        .len()
        .sort(["len", "type", "source"], descending=[True, False, False])
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
                    print(f"  {table_name.upper():7s} : (table absente du contexte)")
                    continue
                if table_name == "dagstar":
                    sub = tbl.filter((pl.col("SID") == sid) | (pl.col("assoc") == sid))
                else:
                    sub = tbl.filter(pl.col("SID") == sid)
                if sub.is_empty():
                    print(f"  {table_name.upper():7s} : 0 ligne (pas de match pour SID={sid})")
                    continue
                # Pour include/exclude/descr/indir : joindre libelle
                # pour afficher le texte associé au LID.
                libelle = _eager(ctx.ofs.get("libelle"))
                if table_name in {"include", "exclude", "descr", "indir"} and libelle is not None:
                    sub = sub.join(libelle.select("LID", "libelle"), on="LID", how="left")
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
    for col in (
        "inclusions",
        "exclusions",
        "synonymes",
        "notes_editorial",
        "definitions",
        "scope_notes",
    ):
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
            f"Δ2 = +{delta_flat} (expansion + synonymes + externes)" if delta_flat else "Δ2 = 0",
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
        prop_counts = pl.DataFrame(schema={"texte": pl.String, "prop_count": pl.UInt32})
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

    flat_codes = set(flat["code"].unique().to_list()) if flat is not None else set()
    known_codes = set(merged["code"].unique().to_list()) if merged is not None else set()

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


# ======================================================================
# inspect_code_extended — variante avec lecture RDF directe
# ======================================================================
#
# Expose toutes les propriétés RDF d'un code (incluant celles non
# extraites par smt2parquet : xkos:exclusionNote, atih:exclusion,
# hasCausality, hasManifestation, skos:definition, scopeNote, note,
# axiomes owl:Axiom réifiés). Permet aussi d'inspecter les codes
# racines (chapitres, blocs, catégories 3-caractères) absents du CSV.

_BASE_URI = "http://data.esante.gouv.fr/atih/cim10"

# Mapping bidirectionnel romain ↔ numérique pour les chapitres.
# - Le RDF source utilise les URIs `01`..`22`.
# - Le pipeline (Parquets) utilise les chiffres romains `I`..`XXII`.
# - L'utilisateur saisit naturellement en romain → on convertit pour
#   l'URI mais on affiche en romain.
_ROMAN_TO_NUM_CHAPTER: dict[str, str] = {
    "I": "01",
    "II": "02",
    "III": "03",
    "IV": "04",
    "V": "05",
    "VI": "06",
    "VII": "07",
    "VIII": "08",
    "IX": "09",
    "X": "10",
    "XI": "11",
    "XII": "12",
    "XIII": "13",
    "XIV": "14",
    "XV": "15",
    "XVI": "16",
    "XVII": "17",
    "XVIII": "18",
    "XIX": "19",
    "XX": "20",
    "XXI": "21",
    "XXII": "22",
}
_NUM_TO_ROMAN_CHAPTER: dict[str, str] = {v: k for k, v in _ROMAN_TO_NUM_CHAPTER.items()}

# Mapping de la notation OFS (plage entre parenthèses) vers l'URI RDF
# numérique. OFS encode les chapitres par leur plage de codes, ex.
# `(A00-B99)` pour le chapitre I, `(M00-M99)` pour XIII. 21 entrées
# seulement : le chapitre XXII (codes U provisoires) n'existait pas
# au gel OFS de novembre 2006.
_OFS_RANGE_TO_NUM_CHAPTER: dict[str, str] = {
    "(A00-B99)": "01",
    "(C00-D48)": "02",
    "(D50-D89)": "03",
    "(E00-E90)": "04",
    "(F00-F99)": "05",
    "(G00-G99)": "06",
    "(H00-H59)": "07",
    "(H60-H95)": "08",
    "(I00-I99)": "09",
    "(J00-J99)": "10",
    "(K00-K93)": "11",
    "(L00-L99)": "12",
    "(M00-M99)": "13",
    "(N00-N99)": "14",
    "(O00-O99)": "15",
    "(P00-P96)": "16",
    "(Q00-Q99)": "17",
    "(R00-R99)": "18",
    "(S00-T98)": "19",
    "(V01-Y98)": "20",
    "(Z00-Z99)": "21",
}
# Inverse : URI RDF numérique → code OFS (avec parenthèses).
_NUM_TO_OFS_RANGE_CHAPTER: dict[str, str] = {v: k for k, v in _OFS_RANGE_TO_NUM_CHAPTER.items()}

# Sections d'affichage du BLOC 2 ANS étendu : (label affiché, prédicat
# en forme préfixée). Ordre = ordre d'affichage. Tout prédicat non
# listé tombe dans "Autres propriétés".
_RDF_BLOC2_SECTIONS: tuple[tuple[str, str], ...] = (
    ("Libellé (rdfs:label)", "rdfs:label"),
    ("Synonymes (skos:altLabel)", "skos:altLabel"),
    ("Inclusions (xkos:inclusionNote)", "xkos:inclusionNote"),
    ("Exclusions (xkos:exclusionNote)", "xkos:exclusionNote"),
    ("Définitions (skos:definition)", "skos:definition"),
    ("Notes de portée (skos:scopeNote)", "skos:scopeNote"),
    ("Notes libres (skos:note)", "skos:note"),
    ("Codes d'exclusion structurés (atih-cim10:exclusion)", "atih-cim10:exclusion"),
    ("Étiologie / dague (atih-cim10:hasCausality)", "atih-cim10:hasCausality"),
    ("Manifestation / astérisque (atih-cim10:hasManifestation)", "atih-cim10:hasManifestation"),
)

# Troncature des valeurs en mode non-verbose pour rester lisible.
_RDF_VALUE_MAX_LEN = 200


def _resolve_user_notation(code: str) -> str:
    """Convertit la notation utilisateur en notation RDF.

    - `I` → `01`, `XIII` → `13` (chapitres romain → 2 chiffres)
    - `(A00-B99)` → `01`, `(M00-M99)` → `13` (chapitres OFS → 2 chiffres).
      Le chapitre XXII (codes U) n'a pas d'équivalent OFS.
    - `M01`, `M01.08`, `A15-A19`, `01` : inchangé
    - Notation inconnue : retournée telle quelle (sera `absent` ensuite)
    """
    if code in _ROMAN_TO_NUM_CHAPTER:
        return _ROMAN_TO_NUM_CHAPTER[code]
    if code in _OFS_RANGE_TO_NUM_CHAPTER:
        return _OFS_RANGE_TO_NUM_CHAPTER[code]
    return code


def _ofs_lookup_candidates(rdf_code: str, disp: str, node_type: str) -> list[str]:
    """Notations à tester pour retrouver un code côté OFS (table ofs_codes).

    OFS encode les chapitres par leur plage entre parenthèses
    (`(M00-M99)` pour XIII), strippée à `M00-M99` après
    `str.strip_chars("()")`. On essaie donc, dans l'ordre :
    1. la notation d'affichage (XIII, M01, M01.08, A15-A19...)
    2. la notation RDF (13, M01, ...)
    3. la plage OFS sans parenthèses pour les chapitres (M00-M99 pour XIII)
    """
    candidates = [disp, rdf_code]
    if node_type == "chapter":
        ofs_range = _NUM_TO_OFS_RANGE_CHAPTER.get(rdf_code)
        if ofs_range is not None:
            # strip_chars("()") sera appliqué côté requête
            candidates.append(ofs_range.strip("()"))
    # Dédup en préservant l'ordre.
    seen: set[str] = set()
    out = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _display_notation(rdf_code: str, node_type: str) -> str:
    """Notation à afficher pour l'utilisateur.

    Pour les chapitres, reconvertit `01`..`22` en `I`..`XXII` car
    c'est la convention familière (et celle du Parquet).
    """
    if node_type == "chapter":
        return _NUM_TO_ROMAN_CHAPTER.get(rdf_code, rdf_code)
    return rdf_code


def _detect_node_type(rdf_code: str, ctx: ExplorationContext) -> str:
    """Renvoie : `chapter`, `block`, `category`, `leaf` ou `absent`.

    Le RDF expose `dc:type` ∈ {chapter, block, category}. La distinction
    `leaf` (sous-catégorie code feuille) vs `category` (catégorie
    3-caractères, source de propagation) se fait par présence du point
    dans la notation — le RDF ne les distingue pas.
    """
    g = ctx.ans_graph
    if g is None:
        return "absent"
    try:
        from rdflib import URIRef
    except ImportError:
        return "absent"
    uri = URIRef(f"{_BASE_URI}/{rdf_code}")
    if (uri, None, None) not in g:
        return "absent"
    from rdflib import Namespace

    dc = Namespace("http://purl.org/dc/elements/1.1/")
    t = g.value(uri, dc.type)
    if t is None:
        return "absent"
    s = str(t)
    if s == "chapter":
        return "chapter"
    if s == "block":
        return "block"
    if s == "category":
        return "leaf" if "." in rdf_code else "category"
    return "absent"


def _uri_for_rdf(rdf_code: str) -> rdflib.term.URIRef:
    from rdflib import URIRef

    return URIRef(f"{_BASE_URI}/{rdf_code}")


def _code_of_uri(uri: object) -> str | None:
    """Extrait la notation d'une URI ANS, ou None si autre."""
    s = str(uri)
    prefix = _BASE_URI + "/"
    return s.removeprefix(prefix) if s.startswith(prefix) else None


def _render_rdf_object(g: rdflib.Graph, o: object, *, max_len: int = _RDF_VALUE_MAX_LEN) -> str:
    """Rend une valeur RDF pour affichage.

    - URI d'un autre code → "Mxx.x — libellé"
    - URI autre → forme préfixée via namespace_manager
    - Littéral → texte rstripé (annotation @fr ignorée : tout l'ANS est en français)
    - Tronqué à `max_len` (avec ellipse) sauf si max_len <= 0
    """
    from rdflib import URIRef

    if isinstance(o, URIRef):
        c = _code_of_uri(o)
        if c is not None:
            from rdflib.namespace import RDFS

            label = g.value(o, RDFS.label)
            disp = _display_notation(c, _detect_node_type_for_uri(g, c))
            return f"{disp} — {label}" if label else disp
        try:
            return str(g.namespace_manager.normalizeUri(o))
        except Exception:
            return str(o)
    text = str(o).rstrip("\n")
    if max_len > 0 and len(text) > max_len:
        text = text[:max_len] + " …"
    return text


def _detect_node_type_for_uri(g: rdflib.Graph, rdf_code: str) -> str:
    """Variante légère de _detect_node_type qui n'a besoin que du graphe.

    Évite de re-passer le ctx complet juste pour résoudre l'affichage
    des références croisées entre codes.
    """
    from rdflib import Namespace

    uri = _uri_for_rdf(rdf_code)
    if (uri, None, None) not in g:
        return "absent"
    dc = Namespace("http://purl.org/dc/elements/1.1/")
    t = g.value(uri, dc.type)
    if t is None:
        return "absent"
    s = str(t)
    if s == "chapter":
        return "chapter"
    if s == "block":
        return "block"
    if s == "category":
        return "leaf" if "." in rdf_code else "category"
    return "absent"


def _props_grouped(g: rdflib.Graph, rdf_code: str) -> dict[str, list[object]]:
    """Tous les triplets sortants, groupés par prédicat (forme préfixée)."""
    out: dict[str, list[object]] = {}
    for p, o in g.predicate_objects(_uri_for_rdf(rdf_code)):
        key = str(g.namespace_manager.normalizeUri(str(p)))
        out.setdefault(key, []).append(o)
    return out


def _reified_axioms_for(g: rdflib.Graph, rdf_code: str) -> list[dict[str, str]]:
    """Axiomes owl:Axiom où le code est annotatedSource OU annotatedTarget."""
    from rdflib import Namespace
    from rdflib.namespace import OWL

    prov = Namespace("http://www.w3.org/ns/prov#")
    uri = _uri_for_rdf(rdf_code)
    out: list[dict[str, str]] = []
    for role, prop in (("source", OWL.annotatedSource), ("cible", OWL.annotatedTarget)):
        for ax in g.subjects(prop, uri):
            src = g.value(ax, OWL.annotatedSource)
            rel = g.value(ax, OWL.annotatedProperty)
            tgt = g.value(ax, OWL.annotatedTarget)
            derived = g.value(ax, prov.wasDerivedFrom)
            out.append(
                {
                    "role_du_code": role,
                    "source": _render_rdf_object(g, src),
                    "relation": str(g.namespace_manager.normalizeUri(str(rel))) if rel else "?",
                    "cible": _render_rdf_object(g, tgt),
                    "libelle_humain": str(derived).rstrip("\n") if derived else "",
                }
            )
    return out


# ----------------------------------------------------------------------
# inspect_code_extended : helpers d'affichage par BLOC
# ----------------------------------------------------------------------


def _print_bloc1_identite_ext(
    rdf_code: str,
    node_type: str,
    ctx: ExplorationContext,
) -> None:
    """BLOC 1 — IDENTITÉ. Adapté pour gérer les nœuds non-feuilles."""
    _section("BLOC 1 : IDENTITÉ")
    g = ctx.ans_graph
    merged = _eager(ctx.merged)
    ofs_codes = _eager(ctx.ofs_codes)

    disp = _display_notation(rdf_code, node_type)
    print(f"Code         : {disp}")
    print(f"Type de nœud : {node_type}")
    if node_type == "absent":
        print("(code absent du RDF ANS)")
        return

    # Libellé OFS — passe par ofs_codes (peut être manquant pour les
    # chapitres/codes post-2006).
    lib_ofs = None
    if ofs_codes is not None:
        # OFS encode les chapitres par plage entre parenthèses (ex.
        # `(M00-M99)` pour XIII), strip_chars("()") la rend `M00-M99`.
        candidates_for_ofs = _ofs_lookup_candidates(rdf_code, disp, node_type)
        for c in candidates_for_ofs:
            row = ofs_codes.filter(pl.col("code").str.strip_chars("()") == c)
            if not row.is_empty():
                lib_ofs = row.select("label").row(0)[0]
                break
    print(f"Libellé OFS  : {lib_ofs or '(absent)'}")

    # Libellé ANS — via rdfs:label sur l'URI RDF.
    if g is not None:
        from rdflib.namespace import RDFS

        lib_ans = g.value(_uri_for_rdf(rdf_code), RDFS.label)
        print(f"Libellé ANS  : {lib_ans or '(absent)'}")
    print(f"URI RDF      : {_BASE_URI}/{rdf_code}")

    # Position dans la hiérarchie (depuis merged_codes via path/parents).
    if merged is not None:
        # Pour les chapitres : pas de parents. Pour les autres : on parse
        # le `path` de merged.
        # merged stocke les chapitres avec la convention romaine — on
        # cherche d'abord via la notation affichée.
        for c in (disp, rdf_code):
            row = merged.filter(pl.col("code") == c)
            if not row.is_empty():
                r = row.row(0, named=True)
                parts = (r.get("path") or "").split("/")
                if len(parts) >= 1 and parts[0] and parts[0] != c:
                    print(f"Chapitre     : {parts[0]} — {_parent_label(merged, parts[0])}")
                if len(parts) >= 2 and parts[1] != c:
                    print(f"Bloc         : {parts[1]} — {_parent_label(merged, parts[1])}")
                if len(parts) >= 3 and parts[2] != c:
                    print(f"Catégorie    : {parts[2]} — {_parent_label(merged, parts[2])}")
                break


def _print_bloc2_sources_ext(
    rdf_code: str,
    node_type: str,
    ctx: ExplorationContext,
) -> None:
    """BLOC 2 — SOURCES BRUTES (avant fusion). Côté ANS lit le RDF."""
    _section("BLOC 2 : SOURCES BRUTES (avant fusion)")

    # --- OFS ---
    # Réutilise la logique existante : on appelle _print_bloc2_sources
    # avec un code "spécial" qui peut ne pas exister côté OFS. Si la
    # notation diffère (chapitre romain), on utilise la version OFS.
    ofs_codes = _eager(ctx.ofs_codes)
    print("[OFS]")
    matched_ofs_code = None
    if ofs_codes is not None:
        disp = _display_notation(rdf_code, node_type)
        for c in _ofs_lookup_candidates(rdf_code, disp, node_type):
            row = ofs_codes.filter(pl.col("code").str.strip_chars("()") == c)
            if not row.is_empty():
                matched_ofs_code = c
                break
    if matched_ofs_code is None or ofs_codes is None:
        print("    (aucune entrée OFS pour ce code)")
    else:
        ofs_row = ofs_codes.filter(pl.col("code").str.strip_chars("()") == matched_ofs_code)
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

    # --- ANS RDF source ---
    print("\n[ANS — RDF source]")
    g = ctx.ans_graph
    if g is None:
        print("    (ctx.ans_graph non chargé — relance avec load_rdf=True)")
        return
    if node_type == "absent":
        print(f"    (code {rdf_code} absent du RDF ANS)")
        return

    props = _props_grouped(g, rdf_code)
    matched_preds: set[str] = set()
    for label, predicate in _RDF_BLOC2_SECTIONS:
        values = props.get(predicate, [])
        matched_preds.add(predicate)
        print(f"  {label} — {len(values)} :")
        if not values:
            print("    (aucune)")
            continue
        for v in values:
            rendered = _render_rdf_object(g, v)
            # Multi-ligne : indenter chaque ligne sous la puce.
            lines = rendered.split("\n")
            print(f"    - {lines[0]}")
            for line in lines[1:]:
                print(f"      {line}")

    # Axiomes réifiés (calculés séparément, pas issus de predicate_objects).
    axioms = _reified_axioms_for(g, rdf_code)
    print(f"  Axiomes réifiés (owl:Axiom) — {len(axioms)} :")
    if not axioms:
        print("    (aucun)")
    else:
        for ax in axioms:
            print(
                f"    - [{ax['role_du_code']}] {ax['source']} --{ax['relation']}--> {ax['cible']}"
            )
            if ax["libelle_humain"]:
                print(f"      libellé : {ax['libelle_humain']}")

    # Autres propriétés (tout ce qui n'a pas été classé).
    other = sorted(set(props.keys()) - matched_preds)
    print(f"  Autres propriétés — {len(other)} :")
    if not other:
        print("    (aucune)")
    else:
        for pred in other:
            for v in props[pred]:
                print(f"    - {pred} → {_render_rdf_object(g, v, max_len=120)}")

    # Sources externes (reprises de l'existant — utile pour les leaves).
    print("\n[SOURCES EXTERNES]")
    if not ctx.external:
        print(
            "    (sources externes non chargées — relancer avec "
            "load_exploration_context(with_external=True, load_rdf=True))"
        )
        return
    any_external = False
    disp = _display_notation(rdf_code, node_type)
    for source_label, df in ctx.external.items():
        sub = df.filter(pl.col("code") == disp)
        if sub.is_empty():
            continue
        any_external = True
        items = [f"{r['libelle']}  [{r['type']}]" for r in sub.iter_rows(named=True)]
        print(f"  {source_label} ({len(items)}) :")
        for line in _fmt_list(items, "    "):
            print(line)
    if not any_external:
        print("    (aucune entrée externe pour ce code)")


def _print_bloc2bis_raw_ext(rdf_code: str, ctx: ExplorationContext) -> None:
    """BLOC 2bis — DONNÉES BRUTES. Tables OFS + tous triplets RDF bruts."""
    _section("BLOC 2bis : DONNÉES BRUTES (DEBUG)")
    # Côté OFS : on délègue à l'existant qui passe par la notation
    # transmise. Si la notation ne match pas MASTER, il affichera son
    # propre message d'absence.
    print("[OFS — Tables brutes liées au SID]")
    master = _eager(ctx.ofs.get("master"))
    if master is None:
        print("    (table MASTER absente du contexte)")
    else:
        # MASTER OFS stocke les chapitres en romain probablement (à
        # confirmer empiriquement). On essaie d'abord la version
        # convertie depuis le rdf_code.
        disp = _display_notation(rdf_code, _detect_node_type(rdf_code, ctx))
        master_row = master.filter((pl.col("code") == disp) | (pl.col("code") == rdf_code))
        if master_row.is_empty():
            print(f"    (code {disp} absent de MASTER OFS)")
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
                    print(f"  {table_name.upper():7s} : (table absente du contexte)")
                    continue
                if table_name == "dagstar":
                    sub = tbl.filter((pl.col("SID") == sid) | (pl.col("assoc") == sid))
                else:
                    sub = tbl.filter(pl.col("SID") == sid)
                if sub.is_empty():
                    print(f"  {table_name.upper():7s} : 0 ligne (pas de match pour SID={sid})")
                    continue
                libelle = _eager(ctx.ofs.get("libelle"))
                if table_name in {"include", "exclude", "descr", "indir"} and libelle is not None:
                    sub = sub.join(libelle.select("LID", "libelle"), on="LID", how="left")
                print(f"  {table_name.upper():7s} : {sub.height} ligne(s)")
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

    # Côté ANS RDF : tous les triplets bruts.
    print("\n[ANS — Triplets RDF bruts]")
    g = ctx.ans_graph
    if g is None:
        print("    (ctx.ans_graph non chargé)")
        return
    node_type = _detect_node_type(rdf_code, ctx)
    if node_type == "absent":
        print(f"    (code {rdf_code} absent du RDF)")
        return
    print(f"  URI : {_BASE_URI}/{rdf_code}")
    props = _props_grouped(g, rdf_code)
    for pred in sorted(props.keys()):
        for v in props[pred]:
            # Mode verbose : pas de troncature
            text = _render_rdf_object(g, v, max_len=0)
            preview = text.replace("\n", "\\n")
            print(f"  {pred:24s} → {preview}")


def _print_bloc3_dagger_ext(rdf_code: str, ctx: ExplorationContext) -> None:
    """BLOC 3 — RELATIONS DAGUE/ASTÉRISQUE. Comparaison OFS DAGSTAR ↔ ANS RDF."""
    _section("BLOC 3 : RELATIONS DAGUE/ASTÉRISQUE")

    # --- Côté OFS ---
    print("[OFS — dagger_asterisk.parquet]")
    dagger = _eager(ctx.dagger_asterisk)
    disp = _display_notation(rdf_code, _detect_node_type(rdf_code, ctx))
    if dagger is None:
        print("    (table dague/astérisque non chargée)")
        ofs_pairs_count = 0
    else:
        involved = dagger.filter(
            (pl.col("dagger_code") == disp) | (pl.col("asterisk_code") == disp)
        )
        if involved.is_empty():
            print("    (pas d'association dague/astérisque)")
            ofs_pairs_count = 0
        else:
            ofs_pairs_count = involved.height
            for r in involved.iter_rows(named=True):
                role = "dague (†)" if r["dagger_code"] == disp else "astérisque (*)"
                partner_code = r["asterisk_code"] if r["dagger_code"] == disp else r["dagger_code"]
                partner_label = (
                    r["asterisk_label"] if r["dagger_code"] == disp else r["dagger_label"]
                )
                print(
                    f"  • {disp} est {role} ; apparié à "
                    f"{partner_code or '(aucun)'} — {partner_label or ''}"
                )

    # --- Côté ANS RDF ---
    print("\n[ANS — RDF (comparaison)]")
    g = ctx.ans_graph
    if g is None:
        print("    (ctx.ans_graph non chargé)")
        return
    from rdflib import Namespace

    atih = Namespace("http://data.esante.gouv.fr/atih-cim10#")
    uri = _uri_for_rdf(rdf_code)
    causalities = list(g.objects(uri, atih.hasCausality))
    manifestations = list(g.objects(uri, atih.hasManifestation))
    print(f"  hasCausality (ce code → étiologie/dague) — {len(causalities)} :")
    if not causalities:
        print("    (aucune)")
    else:
        for o in causalities:
            print(f"    - {_render_rdf_object(g, o)}")
    print(f"  hasManifestation (ce code → manifestation/astérisque) — {len(manifestations)} :")
    if not manifestations:
        print("    (aucune)")
    else:
        for o in manifestations:
            print(f"    - {_render_rdf_object(g, o)}")
    ans_pairs_count = len(causalities) + len(manifestations)

    # --- Synthèse cohérence ---
    print(f"\n  Cohérence : OFS={ofs_pairs_count} paire(s) | ANS={ans_pairs_count} relation(s).")
    if ofs_pairs_count != ans_pairs_count:
        print(
            "    ⚠ Divergence OFS/ANS — peut signaler une différence "
            "de couverture entre DAGSTAR et atih:hasCausality/Manifestation."
        )


def _print_bloc4_final_ext(
    rdf_code: str,
    node_type: str,
    ctx: ExplorationContext,
) -> None:
    """BLOC 4 — CSV final. Pour les non-feuilles, message clair."""
    _section("BLOC 4 : RÉSULTAT FINAL (CSV)")
    flat = _eager(ctx.flat)
    if flat is None:
        print("    (CSV final non chargé)")
        return

    disp = _display_notation(rdf_code, node_type)
    if node_type in ("chapter", "block", "category"):
        print(
            f"    Code absent du CSV final (raison : nœud de type "
            f"{node_type} — le CSV ne contient que les codes feuilles)."
        )
        print("    Pour voir ce qui en est dérivé : inspecter ses descendants directs.")
        return

    sub = flat.filter(pl.col("code") == disp)
    if sub.is_empty():
        orphan_report = _eager(ctx.reports.get("external_orphan_codes"))
        print("    Code absent du CSV final.")
        if orphan_report is not None:
            orph = orphan_report.filter(pl.col("code") == disp)
            if not orph.is_empty():
                cats = sorted(set(orph["categorie_orphan"].to_list()))
                srcs = sorted(set(orph["source_externe"].to_list()))
                print(
                    f"    → présent dans external_orphan_codes.csv : "
                    f"catégorie(s)={cats}, source(s)={srcs}"
                )
        return

    print(f"  {sub.height} ligne(s). Répartition par (type, source) :")
    counts = (
        sub.group_by("type", "source")
        .len()
        .sort(["len", "type", "source"], descending=[True, False, False])
    )
    for r in counts.iter_rows(named=True):
        print(f"    {r['type']:10s} | {r['source']:28s} : {r['len']}")
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


def _print_bloc5_pipeline_ext(
    rdf_code: str,
    node_type: str,
    ctx: ExplorationContext,
) -> None:
    """BLOC 5 — Compteurs pipeline. Pour les non-feuilles, note explicative."""
    _section("BLOC 5 : PARCOURS DANS LE PIPELINE (DEBUG)")
    disp = _display_notation(rdf_code, node_type)

    def _n(df: pl.DataFrame | None) -> int:
        return 0 if df is None else df.filter(pl.col("code") == disp).height

    ofs_codes = _eager(ctx.ofs_codes)
    ans = _eager(ctx.ans)
    merged = _eager(ctx.merged)
    propagated = _eager(ctx.propagated)
    flat = _eager(ctx.flat)

    rows = [
        ("ofs_codes.parquet", str(_n(ofs_codes))),
        ("owl_codes.parquet", str(_n(ans))),
        ("merged_codes.parquet", str(_n(merged))),
        ("propagated_notes.parquet", str(_n(propagated))),
        ("flat_csv (CSV final)", str(_n(flat))),
    ]
    label_w = max(len(r[0]) for r in rows)
    count_w = max(len(r[1]) for r in rows)
    print(f"  {'Étape':<{label_w}} | {'Nb lignes':<{count_w}}")
    print(f"  {'-' * label_w}-|-{'-' * count_w}")
    for label, count in rows:
        print(f"  {label:<{label_w}} | {count:<{count_w}}")

    if node_type in ("chapter", "block", "category"):
        print(
            "\n  → Ce nœud est source de propagation hiérarchique. "
            "Ses notes sont propagées vers les codes feuilles "
            "descendants par propagation.py ; ce nœud lui-même "
            "n'apparaît pas dans propagated_notes / flat_csv."
        )


def inspect_code_extended(
    code: str,
    ctx: ExplorationContext | None = None,
    *,
    verbose: bool = False,
) -> None:
    """Variante de inspect_code avec lecture RDF directe pour l'ANS.

    Affiche les mêmes BLOCs que inspect_code() mais avec :

    - **Côté OFS** : sources identiques (ofs_codes.parquet + tables brutes).
    - **Côté ANS** : lecture du RDF source via `ctx.ans_graph`. Expose
      TOUTES les propriétés RDF (xkos:exclusionNote, skos:definition,
      skos:scopeNote, skos:note, atih-cim10:hasCausality,
      atih-cim10:hasManifestation, atih-cim10:exclusion, axiomes
      owl:Axiom réifiés…), pas seulement les 5 extraites par smt2parquet.
    - **Scope étendu** : accepte les codes feuilles, catégories
      3-caractères, blocs (`A15-A19`), chapitres (en romain `I`-`XXII`
      ou en URI RDF `01`-`22`). Pour les nœuds non-feuilles, le BLOC 4
      affiche un message clair (absence du CSV par construction).

    Args :
        code : notation du code (`M01.08`, `M01`, `A15-A19`, `I`, `XIII`…).
            Un seul code par appel ; pas d'expansion préfixe.
        ctx : contexte d'exploration. Doit avoir été chargé avec
            `load_rdf=True`. Si None, recharge automatiquement avec
            `load_exploration_context(with_external=True, load_rdf=True)`.
        verbose : si True, ajoute BLOC 2bis (triplets RDF bruts +
            tables OFS) et BLOC 5 (compteurs pipeline).

    Outil d'inspection dev only — affichage texte, pas de valeur de retour.
    """
    if ctx is None:
        ctx = load_exploration_context(with_external=True, load_rdf=True)
    if ctx.ans_graph is None:
        raise RuntimeError(
            "ctx.ans_graph manquant — relance avec "
            "load_exploration_context(load_rdf=True) ou passe un ctx "
            "chargé avec cette option."
        )

    rdf_code = _resolve_user_notation(code)
    node_type = _detect_node_type(rdf_code, ctx)
    disp = _display_notation(rdf_code, node_type)

    # Libellé pour l'en-tête (préférence merged > ANS RDF).
    lib = ""
    merged = _eager(ctx.merged)
    if merged is not None:
        row = merged.filter(pl.col("code") == disp)
        if not row.is_empty():
            lib = row.select("label").row(0)[0] or ""
    if not lib and ctx.ans_graph is not None and node_type != "absent":
        from rdflib.namespace import RDFS

        v = ctx.ans_graph.value(_uri_for_rdf(rdf_code), RDFS.label)
        lib = str(v) if v else ""

    print()
    _print_box(f"{disp} — {lib}" if lib else f"{disp} — (libellé inconnu)")
    _print_bloc1_identite_ext(rdf_code, node_type, ctx)
    _print_bloc2_sources_ext(rdf_code, node_type, ctx)
    if verbose:
        _print_bloc2bis_raw_ext(rdf_code, ctx)
    _print_bloc3_dagger_ext(rdf_code, ctx)
    _print_bloc4_final_ext(rdf_code, node_type, ctx)
    if verbose:
        _print_bloc5_pipeline_ext(rdf_code, node_type, ctx)
    print()
