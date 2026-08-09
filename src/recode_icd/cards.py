"""Génération de fiches markdown descriptives par code CIM-10.

Ce module factorise la logique historique du prototype
`scripts/explore/2026-06-01_card_prototype.py`. Il expose deux entrées
publiques :

- `build_card(code, ctx, rng)` : produit le markdown d'une fiche pour
  un code donné. Sortie déterministe pour un seed donné.
- `build_cards_library(...)` : génère la bibliothèque complète sous
  `output_dir/<chapitre_romain>/<code>.md` avec un fichier
  `_index.csv` récapitulatif.

Couplage à `ExplorationContext` (module dev-only) : assumé pour
limiter l'invasivité. Si la fonction doit un jour être utilisée hors
contexte exploratoire, sa signature pourra évoluer pour accepter les
DataFrames bruts.
"""

from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from recode_icd._normalize import normalize_for_match
from recode_icd.utils.loaders_dev import ExplorationContext, load_exploration_context

log = logging.getLogger(__name__)


def _eager(frame: pl.DataFrame | pl.LazyFrame | None) -> pl.DataFrame:
    """Collecte un LazyFrame en DataFrame ; assert que ce n'est pas None.

    Les helpers de ce module attendent un DataFrame eager. Cet adaptateur
    masque le type union exposé par ExplorationContext et fait remonter
    une erreur claire si le frame est absent.
    """
    assert frame is not None, "frame requis (None passé)"
    if isinstance(frame, pl.LazyFrame):
        return frame.collect()
    return frame


# ----------------------------------------------------------------------
# Constantes publiques
# ----------------------------------------------------------------------

DEFAULT_SEED = 42
INDEX_SAMPLE_SIZE = 10

# ----------------------------------------------------------------------
# Sources alimentant la section « Formulations cliniques alternatives »
# ----------------------------------------------------------------------
# Ces valeurs sont des **libellés CSV** (colonne `source` du fichier
# maître), pas des noms d'enum : elles doivent rester synchronisées avec
# `_SOURCE_CSV_MAP` de `exporters/flat_csv.py`. Le filtrage se fait par
# égalité stricte, donc un renommage de libellé non répercuté ici ferait
# disparaître la source de la section **en silence**, sans exception ni
# test rouge. C'est exactement ce qui a failli arriver lors du renommage
# `CepiDc_2015` → `CepiDc 2015` (2026-08-09).
#
# Verrou : `tests/regression/test_cards_formulations_sources.py` vérifie
# que tout libellé du mapping est explicitement soit inclus ci-dessous,
# soit listé dans FORMULATION_SOURCES_EXCLUDED. Ajouter une source sans
# trancher son sort fait échouer ce test.

FORMULATION_SOURCE_INDEX = "CIM-10 index"
FORMULATION_SOURCE_CEPIDC = "CepiDc 2015"
FORMULATION_SOURCE_APHP_PREFIX = "AP-HP"

#: Libellés retenus par égalité stricte, et plafonnés à INDEX_SAMPLE_SIZE
#: sur les fiches feuilles.
FORMULATION_SOURCES_EXACT: tuple[str, ...] = (
    FORMULATION_SOURCE_INDEX,
    FORMULATION_SOURCE_CEPIDC,
)

#: Préfixes retenus (toutes les spécialités AP-HP, non plafonnées).
FORMULATION_SOURCE_PREFIXES: tuple[str, ...] = (FORMULATION_SOURCE_APHP_PREFIX,)

#: Sources délibérément hors de la section Formulations : elles
#: alimentent les sections « Périmètre clinique » / « À ne pas décrire »
#: (OFS, ANS, frères synthétisés) ou sont jugées non pertinentes comme
#: formulation de CRH (ORPHANET, libellés de maladies rares).
FORMULATION_SOURCES_EXCLUDED: tuple[str, ...] = (
    "CIM-10",
    "ANS",
    "CIM-10 frères",
    "ORPHANET",
)

# Ordre d'affichage des groupes dans les sections "Périmètre clinique"
# et "À ne pas décrire" : du plus large (chapitre) au plus spécifique
# (code feuille). Cohérent entre les deux sections.
_LEVEL_ORDER = ("chapter", "block", "category", "code")

# Amorces narratives par niveau d'héritage pour "À ne pas décrire".
_AMORCE_CODE_LEVEL = "Affections relevant d'autres codes :"
_AMORCE_HERITAGE_BY_LEVEL = {
    "category": "Affections relevant d'autres codes (hérité de la catégorie {parent}) :",
    "block": "Affections relevant d'autres codes (hérité du bloc {parent}) :",
    "chapter": "Affections relevant d'autres codes (hérité du chapitre {parent}) :",
}

# Amorces pour la section "Périmètre clinique du code".
_AMORCE_PERIMETRE_HERITAGE = {
    "chapter": "Inclusions héritées du chapitre {parent} :",
    "block": "Inclusions héritées du bloc {parent} :",
    "category": "Inclusions héritées de la catégorie {parent} :",
}
_AMORCE_PERIMETRE_CODE = "Au niveau du code :"

# Regex pour extraire le code frère à la fin d'un texte d'exclusion
# synthétisée (CIM-10 frères).
_SIBLING_CODE_RE = re.compile(r"\s*\(([A-Z]\d{2}(?:\.\d+)?)\)\s*$")

# Regex de détection des sections présentes dans un markdown généré
# (utilisé par `build_cards_library` pour remplir _index.csv).
_SECTION_TITLES = {
    "has_perimetre": "Périmètre clinique du code",
    "has_localisations": "Localisations anatomiques",
    "has_exclusions": "À ne pas décrire",
    "has_formulations": "Formulations cliniques alternatives",
}


# ----------------------------------------------------------------------
# Section 1 — Position dans la classification
# ----------------------------------------------------------------------


def _section_hierarchy(code: str, ctx: ExplorationContext) -> str | None:
    """Construit la section 1 via nested set sur ctx.ans.

    Pour un code de type=category (3 caractères, ex R51), on omet la
    ligne "Catégorie" pour éviter la redondance avec le titre.
    """
    ans = _eager(ctx.ans)
    assert ans is not None
    row = ans.filter(pl.col("code") == code)
    if row.is_empty():
        return None
    r = row.row(0, named=True)
    left_v, right_v = r["left"], r["right"]
    self_type = r["type"]

    parents = (
        ans.filter((pl.col("left") < left_v) & (pl.col("right") > right_v))
        .sort("depth")
        .select(["code", "label", "type"])
    )

    lines = ["## Position dans la classification"]
    for p in parents.iter_rows(named=True):
        ptype, pcode, plabel = p["type"], p["code"], p["label"]
        if ptype == "chapter":
            lines.append(f"- Chapitre {pcode} : {plabel}")
        elif ptype == "block":
            lines.append(f"- Bloc {pcode} : {plabel}")
        elif ptype == "category":
            if self_type == "category":
                continue
            lines.append(f"- Catégorie {pcode} : {plabel}")
    if len(lines) == 1:
        return None
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Section 1bis — Localisations anatomiques (codes type=D chap XIII)
# ----------------------------------------------------------------------


def _is_type_d_code(code: str, ctx: ExplorationContext) -> bool:
    """Code 5e position du chapitre XIII (ofs_type=='D' AND depth==5).

    Critère strictement identique à celui du retypage dans
    `merge.py::retype_chap13_altlabels`.
    """
    ofs_codes = _eager(ctx.ofs_codes)
    assert ofs_codes is not None
    row = ofs_codes.filter(pl.col("code").str.strip_chars("()") == code)
    if row.is_empty():
        return False
    r = row.row(0, named=True)
    return r.get("ofs_type") == "D" and r.get("depth") == 5


def _section_localisations(code: str, ctx: ExplorationContext) -> str | None:
    """Section 'Localisations anatomiques' — codes type=D chap XIII uniquement.

    Source : `type=inclusion, source=ANS, source_level=code` (les
    ex-altLabel ANS retypés par le chantier 2026-06-06). Dichotomie
    atomiques vs bloc multi-ligne via la présence de `\\n`.
    """
    if not _is_type_d_code(code, ctx):
        return None

    csv = _eager(ctx.flat)
    assert csv is not None
    sub = csv.filter(
        (pl.col("code") == code)
        & (pl.col("type") == "inclusion")
        & (pl.col("source") == "ANS")
        & (pl.col("source_level") == "code")
    )
    if sub.is_empty():
        return None

    atomiques: list[str] = []
    blocs: list[str] = []
    for t in sub["texte"].drop_nulls().to_list():
        if "\n" in t:
            blocs.append(t.rstrip())
        else:
            atomiques.append(t)
    atomiques.sort(key=lambda s: normalize_for_match(s) or "")

    if not atomiques and not blocs:
        return None

    lines = ["## Localisations anatomiques"]
    for a in atomiques:
        lines.append(f"- {a}")
    if blocs:
        lines.append("")
        lines.append("Bloc d'inclusion :")
        lines.append("\n\n".join(blocs))
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Section 2 — Périmètre clinique du code
# ----------------------------------------------------------------------


def _dedup_tolerant_preserve_order(texts: list[str]) -> list[str]:
    """Dédup tolérante : conserve la première occurrence par clé normalisée."""
    seen: set[str] = set()
    out: list[str] = []
    for t in texts:
        norm = normalize_for_match(t) or ""
        if norm in seen:
            continue
        seen.add(norm)
        out.append(t)
    return out


def _perimeter_heritage_block(sub: pl.DataFrame, level: str) -> str | None:
    """Bloc d'inclusions héritées d'un niveau (chapter/block/category)."""
    rows = sub.filter((pl.col("type") == "inclusion") & (pl.col("source_level") == level))
    if rows.is_empty():
        return None
    parents = rows["inherited_from_code"].drop_nulls().to_list()
    parent = parents[0] if parents else "?"
    # Certains textes (notamment ANS) finissent par un \n qui casse
    # l'espacement déterministe ; on rstripe avant toute manipulation.
    texts = _dedup_tolerant_preserve_order([t.rstrip() for t in rows["texte"].to_list() if t])
    texts.sort(key=lambda t: normalize_for_match(t) or "")
    amorce = _AMORCE_PERIMETRE_HERITAGE[level].format(parent=parent)
    return amorce + "\n" + "\n".join(f"- {t}" for t in texts)


def _perimeter_code_level_block(sub: pl.DataFrame) -> str | None:
    """Bloc niveau code de "Périmètre clinique"."""
    primary = sub.filter(
        ((pl.col("type") == "synonyme") | (pl.col("type") == "inclusion"))
        & (pl.col("source") == "CIM-10")
        & (pl.col("source_level") == "code")
    )
    texts = primary["texte"].drop_nulls().to_list()

    if not texts:
        fallback = sub.filter(
            (pl.col("type") == "synonyme")
            & (pl.col("source") == "ANS")
            & (pl.col("source_level") == "code")
        )
        texts = fallback["texte"].drop_nulls().to_list()

    if not texts:
        return None

    texts = _dedup_tolerant_preserve_order(texts)
    texts.sort(key=lambda t: normalize_for_match(t) or "")
    return _AMORCE_PERIMETRE_CODE + "\n" + "\n".join(f"- {t}" for t in texts)


def _section_perimeter(code: str, ctx: ExplorationContext) -> str | None:
    """Périmètre clinique du code : inclusions héritées + niveau code.

    Ordre des sous-sections : général → spécifique
    (chapter > block > category > code).
    """
    csv = _eager(ctx.flat)
    assert csv is not None
    sub = csv.filter(pl.col("code") == code)

    if sub.is_empty():
        return _section_perimeter_from_ans(code, ctx)

    parts: list[str] = []
    for level in ("chapter", "block", "category"):
        block = _perimeter_heritage_block(sub, level)
        if block:
            parts.append(block)
    code_block = _perimeter_code_level_block(sub)
    if code_block:
        parts.append(code_block)

    if not parts:
        return None
    return "## Périmètre clinique du code\n\n" + "\n\n".join(parts)


def _section_perimeter_from_ans(code: str, ctx: ExplorationContext) -> str | None:
    """Fallback pour les codes absents du CSV (ex : U07.1)."""
    ans = _eager(ctx.ans)
    assert ans is not None
    row = ans.filter(pl.col("code") == code)
    if row.is_empty():
        return None
    r = row.row(0, named=True)
    texts: list[str] = []
    if r["synonymes"]:
        texts.extend(s for s in r["synonymes"] if s)
    if r["inclusion_note"]:
        texts.append(r["inclusion_note"])
    if not texts:
        return None
    texts = _dedup_tolerant_preserve_order(texts)
    texts.sort(key=lambda t: normalize_for_match(t) or "")
    lines = ["## Périmètre clinique du code"]
    lines.extend(f"- {t}" for t in texts)
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Section 3 — À ne pas décrire
# ----------------------------------------------------------------------


def _amorce_for(level: str, parent: str | None) -> str:
    if level == "code":
        return _AMORCE_CODE_LEVEL
    return _AMORCE_HERITAGE_BY_LEVEL[level].format(parent=parent or "?")


def _block_for_level(group: pl.DataFrame, level: str) -> str | None:
    """Rend l'amorce + les blocs textuels d'un même niveau d'héritage."""
    rows = list(group.iter_rows(named=True))
    if not rows:
        return None
    parent = rows[0]["inherited_from_code"]
    amorce = _amorce_for(level, parent)
    texts = [(r["texte"] or "").rstrip() for r in rows]
    texts = [t for t in texts if t]
    if not texts:
        return None
    return f"{amorce}\n\n" + "\n".join(texts)


def _sibling_label(text: str) -> str:
    """Retire `(Jxx.x)` final du libellé d'un frère synthétisé."""
    return _SIBLING_CODE_RE.sub("", text)


def _siblings_block(siblings: pl.DataFrame, parent_category: str) -> str:
    """Sous-section des frères (en fin de "À ne pas décrire")."""
    rows = list(siblings.iter_rows(named=True))
    rows.sort(key=lambda r: normalize_for_match(_sibling_label(r["texte"])) or "")
    lines = [f"Formes spécifiées de la catégorie {parent_category} :"]
    for r in rows:
        text = r["texte"] or ""
        m = _SIBLING_CODE_RE.search(text)
        sibling_code = m.group(1) if m else "?"
        label = _sibling_label(text)
        lines.append(f"- {label} [→ {sibling_code}]")
    return "\n".join(lines)


def _section_exclusions(code: str, ctx: ExplorationContext) -> str | None:
    """Section 3 — "À ne pas décrire".

    Stratégie : ANS primaire (les blocs ANS contiennent les exclusions
    OFS atomiques + des entrées absentes d'OFS), fallback OFS si ANS
    vide. Format narratif par niveau d'héritage + frères en fin si
    code en `.8`.
    """
    csv = _eager(ctx.flat)
    assert csv is not None

    sub = csv.filter(pl.col("code") == code)
    if sub.is_empty():
        return _section_exclusions_from_ans(code, ctx)

    excl = sub.filter(pl.col("type") == "exclusion")
    if excl.is_empty():
        return None

    ans_excl = excl.filter(pl.col("source") == "ANS")
    siblings = excl.filter(pl.col("source") == "CIM-10 frères")

    primary = excl.filter(pl.col("source") == "CIM-10") if ans_excl.is_empty() else ans_excl

    if primary.is_empty() and siblings.is_empty():
        return None

    parts: list[str] = []
    for level in _LEVEL_ORDER:
        group = primary.filter(pl.col("source_level") == level)
        block = _block_for_level(group, level)
        if block:
            parts.append(block)

    if not siblings.is_empty():
        parent_category = code.split(".")[0]
        parts.append(_siblings_block(siblings, parent_category))

    if not parts:
        return None
    return "## À ne pas décrire\n\n" + "\n\n".join(parts)


def _section_exclusions_from_ans(code: str, ctx: ExplorationContext) -> str | None:
    """Fallback pour les codes absents du CSV (ex : U07.1)."""
    ans = _eager(ctx.ans)
    assert ans is not None
    row = ans.filter(pl.col("code") == code)
    if row.is_empty():
        return None
    r = row.row(0, named=True)
    items = [s.rstrip() for s in (r["exclusion_notes"] or []) if s]
    items = [t for t in items if t]
    if not items:
        return None
    body = "\n".join(items)
    return f"## À ne pas décrire\n\n{_AMORCE_CODE_LEVEL}\n\n{body}"


# ----------------------------------------------------------------------
# Section 4 — Formulations cliniques alternatives
# ----------------------------------------------------------------------


def _section_formulations(code: str, ctx: ExplorationContext, rng: random.Random) -> str | None:
    """Index CIM-10 vol3 (échantillon ≤10) + AP-HP toutes feuilles (tout)
    + CepiDc 2015 (échantillon ≤10)."""
    csv = _eager(ctx.flat)
    assert csv is not None

    sub = csv.filter(pl.col("code") == code)
    if sub.is_empty():
        return None

    index_entries = (
        sub.filter(pl.col("source") == FORMULATION_SOURCE_INDEX)["texte"].drop_nulls().to_list()
    )
    aphp_entries = (
        sub.filter(pl.col("source").str.starts_with(FORMULATION_SOURCE_APHP_PREFIX))["texte"]
        .drop_nulls()
        .to_list()
    )
    cepidc_entries = (
        sub.filter(pl.col("source") == FORMULATION_SOURCE_CEPIDC)["texte"].drop_nulls().to_list()
    )

    if len(index_entries) > INDEX_SAMPLE_SIZE:
        index_entries = rng.sample(index_entries, INDEX_SAMPLE_SIZE)
    # Échantillonnage symétrique pour CepiDc : certains codes ont
    # jusqu'à 988 formulations (AVC) — on limite à INDEX_SAMPLE_SIZE.
    if len(cepidc_entries) > INDEX_SAMPLE_SIZE:
        cepidc_entries = rng.sample(cepidc_entries, INDEX_SAMPLE_SIZE)

    merged = index_entries + aphp_entries + cepidc_entries
    if not merged:
        return None

    merged = _dedup_tolerant_preserve_order(merged)
    merged.sort(key=lambda t: normalize_for_match(t) or "")

    lines = ["## Formulations cliniques alternatives"]
    lines.extend(f"- {t}" for t in merged)
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Orchestrateur — fonction publique build_card
# ----------------------------------------------------------------------


def _title(code: str, ctx: ExplorationContext) -> str:
    """Titre de la fiche (libellé : CSV en priorité, fallback ANS)."""
    csv = _eager(ctx.flat)
    assert csv is not None
    sub = csv.filter(pl.col("code") == code)
    if not sub.is_empty():
        lib = sub.row(0, named=True)["libelle"]
        if lib:
            return f"# {code} — {lib}"
    ans = _eager(ctx.ans)
    assert ans is not None
    row = ans.filter(pl.col("code") == code)
    if not row.is_empty():
        return f"# {code} — {row.row(0, named=True)['label']}"
    return f"# {code}"


def build_card(code: str, ctx: ExplorationContext, rng: random.Random) -> str:
    """Construit la fiche markdown descriptive d'un code CIM-10.

    Args:
        code : code CIM-10 (ex. "A18.1", "M01.08").
        ctx : contexte d'exploration chargé avec `with_external=True`
            (sources externes nécessaires à la section "Formulations
            cliniques alternatives"). Doit avoir `flat`, `merged`,
            `ans`, `ofs_codes` non-None.
        rng : générateur aléatoire pour l'échantillonnage déterministe
            des entrées Index CIM-10 vol3 (cf `INDEX_SAMPLE_SIZE`).
            Même seed → même fiche.

    Returns:
        Markdown sous forme `<fiche_code code="X">\\n\\n# X — ...
        \\n...\\n</fiche_code>\\n`. Les sections vides sont omises.

    Sections produites (dans l'ordre) :
        1. Titre + libellé
        2. Position dans la classification
        3. Localisations anatomiques (codes type=D chap XIII uniquement)
        4. Périmètre clinique du code (héritages + niveau code)
        5. À ne pas décrire (exclusions héritées + frères pour .8)
        6. Formulations cliniques alternatives (Index + AP-HP)
    """
    sections = [
        _title(code, ctx),
        _section_hierarchy(code, ctx),
        _section_localisations(code, ctx),
        _section_perimeter(code, ctx),
        _section_exclusions(code, ctx),
        _section_formulations(code, ctx, rng),
    ]
    body = "\n\n".join(s for s in sections if s)
    return f'<fiche_code code="{code}">\n\n{body}\n\n</fiche_code>\n'


# ----------------------------------------------------------------------
# Bibliothèque complète — build_cards_library
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class BuildSummary:
    """Résumé d'une génération de bibliothèque."""

    n_codes_total: int
    n_written: int
    n_errors: int
    elapsed_seconds: float
    output_dir: Path
    index_path: Path
    errors: tuple[tuple[str, str], ...]


def _detect_sections(card: str) -> dict[str, bool]:
    """Detection par regex des 4 sections principales dans le markdown."""
    return {
        key: bool(re.search(rf"^## {re.escape(title)}$", card, re.MULTILINE))
        for key, title in _SECTION_TITLES.items()
    }


def _code_to_chapter_map(merged: pl.DataFrame) -> dict[str, str]:
    """Construit le map `code → chapitre romain` via merged.path."""
    rows = merged.with_columns(pl.col("path").str.split("/").list.get(0).alias("chap")).select(
        "code", "chap"
    )
    return {r["code"]: r["chap"] for r in rows.iter_rows(named=True)}


def _libelle_of(csv: pl.DataFrame, code: str) -> str:
    """Libellé d'un code via la colonne `libelle` du CSV (1ère ligne)."""
    row = csv.filter(pl.col("code") == code)
    if row.is_empty():
        return ""
    val = row["libelle"][0]
    return val or ""


def build_cards_library(
    *,
    ctx: ExplorationContext | None = None,
    output_dir: Path = Path("outputs/cards_library"),
    chapter_filter: str | None = None,
    limit: int | None = None,
    seed: int = DEFAULT_SEED,
    progress: bool = True,
) -> BuildSummary:
    """Génère la bibliothèque complète de fiches CIM-10.

    Args:
        ctx : contexte d'exploration ; chargé automatiquement avec
            `with_external=True` si None.
        output_dir : dossier racine de sortie (sous-dossiers
            `<chapitre_romain>/<code>.md` créés à l'intérieur).
        chapter_filter : ne génère que les codes d'un chapitre donné
            (notation romaine, ex. "XIII"). None → tous.
        limit : limite à N codes (utile pour tests). None → tous.
        seed : seed du `random.Random` partagé entre toutes les fiches.
        progress : si True, log un message tous les 1 000 codes.

    Returns:
        BuildSummary avec compteurs et chemin du `_index.csv`.

    Fichiers produits :
        - `output_dir/<chapter>/<code>.md` pour chaque code feuille
        - `output_dir/_index.csv` avec métadonnées de chaque fiche

    Comportement en cas d'erreur sur une fiche : log warning, skip,
    continue. Les codes en échec sont listés dans `BuildSummary.errors`.
    """
    if ctx is None:
        ctx = load_exploration_context(with_external=True)
    csv = _eager(ctx.flat)
    merged = _eager(ctx.merged)
    code_to_chap = _code_to_chapter_map(merged)

    # Liste des codes uniques du CSV, dans l'ordre lexicographique
    # déterministe.
    codes_all = sorted(csv["code"].unique().to_list())
    codes = [c for c in codes_all if code_to_chap.get(c) is not None]
    if chapter_filter is not None:
        codes = [c for c in codes if code_to_chap.get(c) == chapter_filter]
    if limit is not None:
        codes = codes[:limit]

    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    index_rows: list[dict[str, object]] = []
    errors: list[tuple[str, str]] = []
    t0 = time.perf_counter()
    n_written = 0

    for i, code in enumerate(codes, 1):
        try:
            card = build_card(code, ctx, rng)
            chapter = code_to_chap[code]
            chap_dir = output_dir / chapter
            chap_dir.mkdir(parents=True, exist_ok=True)
            fname = f"{code}.md"
            (chap_dir / fname).write_text(card, encoding="utf-8")
            sections = _detect_sections(card)
            index_rows.append(
                {
                    "code": code,
                    "chapter": chapter,
                    "filepath": f"{chapter}/{fname}",
                    "libelle": _libelle_of(csv, code),
                    "nb_chars": len(card),
                    **sections,
                }
            )
            n_written += 1
        except Exception as exc:
            errors.append((code, str(exc)))
            log.warning("Échec build_card(%s) : %s", code, exc)
            continue

        if progress and i % 1000 == 0:
            log.info(
                "Progression : %d / %d codes (%.1fs écoulées)",
                i,
                len(codes),
                time.perf_counter() - t0,
            )

    # Écriture _index.csv (colonnes ordonnées explicitement).
    index_path = output_dir / "_index.csv"
    if index_rows:
        ordered_cols = [
            "code",
            "chapter",
            "filepath",
            "libelle",
            "has_perimetre",
            "has_localisations",
            "has_exclusions",
            "has_formulations",
            "nb_chars",
        ]
        pl.DataFrame(index_rows).select(ordered_cols).write_csv(index_path)

    elapsed = time.perf_counter() - t0
    return BuildSummary(
        n_codes_total=len(codes),
        n_written=n_written,
        n_errors=len(errors),
        elapsed_seconds=elapsed,
        output_dir=output_dir,
        index_path=index_path,
        errors=tuple(errors),
    )


# ======================================================================
# Bibliothèque de fiches catégories 3-car
# ======================================================================
#
# Architecture parallèle à `build_card` / `build_cards_library` mais au
# niveau des catégories 3-caractères (A18, M01, J18, R51…). Une fiche
# catégorie agrège les contenus de ses feuilles descendantes depuis le
# CSV maître, avec des règles spécifiques :
# - inclusions héritées dédupliquées sans mention de source
# - inclusions / formulations niveau code agrégées avec mention `(code)`
# - exclusions toutes sans mention de source
# - pas de section "Localisations anatomiques" (cf chap XIII : ces
#   inclusions ANS sont au niveau 5-car, hors scope catégorie)
# - section "Codes enfants directs" omise pour les catégories qui sont
#   elles-mêmes des feuilles (R51, J22…)


_AMORCE_CATEGORY_CODE_LEVEL = "Au niveau des codes :"
_CATEGORY_SECTION_TITLES = {
    "has_perimetre": "Périmètre clinique",
    "has_exclusions": "À ne pas décrire",
    "has_formulations": "Formulations cliniques alternatives",
}

# Échantillonnage des formulations cliniques au niveau catégorie.
# Sans plafond, une catégorie comme A18 (9 enfants) agrège ~28 KB de
# formulations Index/AP-HP, ce qui produit une fiche >30 KB difficile
# à consommer. Avec une limite haute, on plafonne la section
# Formulations en échantillonnant déterministiquement via `rng` quand
# le nombre d'entrées dépasse `CATEGORY_FORMULATIONS_MAX`.
CATEGORY_FORMULATIONS_MAX = 50


def _category_direct_children(category_code: str, merged: pl.DataFrame) -> list[tuple[str, str]]:
    """Enfants directs de `category_code` : codes de longueur +2 (point + 1 chiffre).

    Pour A18 (3 chars) : retourne A18.0, A18.1, … (5 chars).
    Pour M01 : retourne M01.0..M01.8 (4-car au sens CIM, 5 chars) et
    pas les sous-enfants M01.00..M01.98 (5-car CIM / 6 chars).
    """
    expected_len = len(category_code) + 2
    enfants = (
        merged.filter(
            pl.col("code").str.starts_with(f"{category_code}.")
            & (pl.col("code").str.len_chars() == expected_len)
        )
        .select("code", "label")
        .sort("code")
    )
    return [(r["code"], r["label"] or "") for r in enfants.iter_rows(named=True)]


def _category_leaf_codes(category_code: str, csv: pl.DataFrame) -> list[str]:
    """Feuilles du CSV descendant de la catégorie, plus la catégorie
    elle-même si présente dans le CSV (cas R51).

    Ordre croissant alpha (déterminisme : la dédup tolérante garde le
    premier rencontré, donc le code le plus court / le plus petit).
    """
    sub = csv.filter(
        (pl.col("code") == category_code) | pl.col("code").str.starts_with(f"{category_code}.")
    )
    return sorted(sub["code"].unique().to_list())


def _category_title(code: str, ctx: ExplorationContext) -> str:
    """Titre fiche catégorie : merged en priorité (canonique), fallback ANS."""
    merged = _eager(ctx.merged)
    row = merged.filter(pl.col("code") == code)
    if not row.is_empty():
        lib = row.row(0, named=True)["label"]
        if lib:
            return f"# {code} — {lib}"
    ans = _eager(ctx.ans)
    row_ans = ans.filter(pl.col("code") == code)
    if not row_ans.is_empty():
        return f"# {code} — {row_ans.row(0, named=True)['label']}"
    return f"# {code}"


def _category_section_children(category_code: str, ctx: ExplorationContext) -> str | None:
    """Section "Codes enfants directs". Omise si aucun enfant."""
    merged = _eager(ctx.merged)
    enfants = _category_direct_children(category_code, merged)
    if not enfants:
        return None
    lines = ["## Codes enfants directs"]
    for code, label in enfants:
        lines.append(f"- {code} — {label}")
    return "\n".join(lines)


def _agg_heritage_block(
    sub: pl.DataFrame, level: str, amorce_template: dict[str, str]
) -> str | None:
    """Bloc d'inclusions/exclusions héritées agrégées (dédup tolérante,
    sans mention de source). Format identique à `_perimeter_heritage_block`
    mais sans filtre par type (passé via sub déjà filtré)."""
    rows = sub.filter(pl.col("source_level") == level)
    if rows.is_empty():
        return None
    parents = rows["inherited_from_code"].drop_nulls().to_list()
    parent = parents[0] if parents else "?"
    texts = _dedup_tolerant_preserve_order([t.rstrip() for t in rows["texte"].to_list() if t])
    texts.sort(key=lambda t: normalize_for_match(t) or "")
    amorce = amorce_template[level].format(parent=parent)
    return amorce + "\n" + "\n".join(f"- {t}" for t in texts)


def _category_section_perimeter(category_code: str, ctx: ExplorationContext) -> str | None:
    """Section "Périmètre clinique" agrégée.

    Sous-sections héritées (chapter/block/category) : dédupliquées sans
    mention de source.

    Sous-section "Au niveau des codes" : descripteurs OFS (synonyme
    CIM-10 niveau code) + inclusions ANS niveau code des feuilles,
    avec mention `(code)`, dédupliqués. Pour les codes type=D chap XIII,
    on ignore les inclusions ANS niveau code (couvertes par
    "Localisations anatomiques" des fiches feuilles).
    """
    csv = _eager(ctx.flat)
    leaves = _category_leaf_codes(category_code, csv)
    if not leaves:
        return None
    sub = csv.filter(pl.col("code").is_in(leaves))

    # Inclusions héritées (chapter/block/category) — dédup agressive sans source
    incl = sub.filter(pl.col("type") == "inclusion")
    parts: list[str] = []
    for level in ("chapter", "block", "category"):
        block = _agg_heritage_block(incl, level, _AMORCE_PERIMETRE_HERITAGE)
        if block:
            parts.append(block)

    # Niveau code : descripteurs OFS + inclusions ANS (sauf type=D chap XIII)
    code_entries: list[tuple[str, str]] = []  # (texte, code source)
    # Descripteurs OFS niveau code
    desc_ofs = sub.filter(
        (pl.col("type") == "synonyme")
        & (pl.col("source") == "CIM-10")
        & (pl.col("source_level") == "code")
    )
    for r in desc_ofs.iter_rows(named=True):
        if r["texte"]:
            code_entries.append((r["texte"], r["code"]))
    # Inclusions CIM-10 niveau code
    incl_ofs = sub.filter(
        (pl.col("type") == "inclusion")
        & (pl.col("source") == "CIM-10")
        & (pl.col("source_level") == "code")
    )
    for r in incl_ofs.iter_rows(named=True):
        if r["texte"]:
            code_entries.append((r["texte"], r["code"]))
    # Inclusions ANS niveau code SAUF si code type=D chap XIII
    incl_ans = sub.filter(
        (pl.col("type") == "inclusion")
        & (pl.col("source") == "ANS")
        & (pl.col("source_level") == "code")
    )
    for r in incl_ans.iter_rows(named=True):
        code = r["code"]
        if r["texte"] and not _is_type_d_code(code, ctx):
            code_entries.append((r["texte"], code))

    if code_entries:
        # Tri stable : par code croissant pour que le "premier rencontré"
        # en dédup soit déterministe et le plus court/petit.
        code_entries.sort(key=lambda e: (e[1], normalize_for_match(e[0]) or ""))
        seen: set[str] = set()
        kept: list[tuple[str, str]] = []
        for text, src_code in code_entries:
            norm = normalize_for_match(text) or ""
            if norm in seen:
                continue
            seen.add(norm)
            kept.append((text, src_code))
        kept.sort(key=lambda e: normalize_for_match(e[0]) or "")
        lines = [_AMORCE_CATEGORY_CODE_LEVEL]
        for text, src_code in kept:
            lines.append(f"- {text} ({src_code})")
        parts.append("\n".join(lines))

    if not parts:
        return None
    return "## Périmètre clinique\n\n" + "\n\n".join(parts)


def _category_section_exclusions(category_code: str, ctx: ExplorationContext) -> str | None:
    """Section "À ne pas décrire" agrégée.

    Toutes les sous-sections sans mention de source. ANS primaire
    (cohérent avec `_section_exclusions` feuille), fallback OFS si ANS
    vide à un niveau donné. Niveau code agrégé en fin avec amorce
    `_AMORCE_CODE_LEVEL`. Pas de frères (notion feuille).
    """
    csv = _eager(ctx.flat)
    leaves = _category_leaf_codes(category_code, csv)
    if not leaves:
        return None
    sub = csv.filter(pl.col("code").is_in(leaves))

    excl = sub.filter(pl.col("type") == "exclusion")
    if excl.is_empty():
        return None

    parts: list[str] = []
    for level in _LEVEL_ORDER:
        # ANS primaire, fallback OFS si vide à ce niveau précis
        ans_at_level = excl.filter((pl.col("source") == "ANS") & (pl.col("source_level") == level))
        if not ans_at_level.is_empty():
            primary_at_level = ans_at_level
        else:
            primary_at_level = excl.filter(
                (pl.col("source") == "CIM-10") & (pl.col("source_level") == level)
            )
        if primary_at_level.is_empty():
            continue
        parents = primary_at_level["inherited_from_code"].drop_nulls().to_list()
        parent = parents[0] if parents else None
        texts = _dedup_tolerant_preserve_order(
            [(t or "").rstrip() for t in primary_at_level["texte"].to_list() if t]
        )
        texts = [t for t in texts if t]
        if not texts:
            continue
        amorce = _amorce_for(level, parent)
        if level == "code":
            # Niveau code : texte agrégé sans tri spécifique (les exclusions
            # niveau code sont souvent des textes courts ; tri alpha).
            texts.sort(key=lambda t: normalize_for_match(t) or "")
            parts.append(f"{amorce}\n\n" + "\n".join(f"- {t}" for t in texts))
        else:
            # Niveaux hérités : bloc multi-ligne ANS rendu tel quel,
            # joint par \n.
            parts.append(f"{amorce}\n\n" + "\n".join(texts))

    if not parts:
        return None
    return "## À ne pas décrire\n\n" + "\n\n".join(parts)


def _category_section_formulations(
    category_code: str, ctx: ExplorationContext, rng: random.Random
) -> str | None:
    """Section "Formulations cliniques alternatives" agrégée.

    Entrées Index CIM-10 vol3 + AP-HP + CepiDc 2015 des feuilles
    descendantes. Mention de source `(code)` pour chaque entrée. Dédup
    tolérante (premier code rencontré en ordre alpha croissant). Si
    après dédup le nombre d'entrées dépasse `CATEGORY_FORMULATIONS_MAX`,
    échantillonnage déterministe via `rng`.
    """
    csv = _eager(ctx.flat)
    leaves = _category_leaf_codes(category_code, csv)
    if not leaves:
        return None
    sub = csv.filter(pl.col("code").is_in(leaves))

    formul = sub.filter(
        (pl.col("source") == FORMULATION_SOURCE_INDEX)
        | pl.col("source").str.starts_with(FORMULATION_SOURCE_APHP_PREFIX)
        | (pl.col("source") == FORMULATION_SOURCE_CEPIDC)
    )
    if formul.is_empty():
        return None

    entries: list[tuple[str, str]] = [
        (r["texte"], r["code"]) for r in formul.iter_rows(named=True) if r["texte"]
    ]
    if not entries:
        return None
    # Tri par (code, texte_norm) pour déterminisme de la dédup.
    entries.sort(key=lambda e: (e[1], normalize_for_match(e[0]) or ""))
    seen: set[str] = set()
    kept: list[tuple[str, str]] = []
    for text, src_code in entries:
        norm = normalize_for_match(text) or ""
        if norm in seen:
            continue
        seen.add(norm)
        kept.append((text, src_code))

    # Échantillonnage déterministe si volume excessif.
    if len(kept) > CATEGORY_FORMULATIONS_MAX:
        kept = rng.sample(kept, CATEGORY_FORMULATIONS_MAX)

    kept.sort(key=lambda e: normalize_for_match(e[0]) or "")

    lines = ["## Formulations cliniques alternatives"]
    for text, src_code in kept:
        lines.append(f"- {text} ({src_code})")
    return "\n".join(lines)


def build_category_card(
    category_code: str,
    ctx: ExplorationContext,
    rng: random.Random,
) -> str:
    """Construit la fiche markdown agrégée d'une catégorie 3-car.

    Args:
        category_code : code catégorie 3-car (ex. "A18", "M01", "R51").
        ctx : contexte d'exploration avec `with_external=True`.
        rng : utilisé pour l'échantillonnage déterministe des
            formulations cliniques quand le volume dépasse
            `CATEGORY_FORMULATIONS_MAX`.

    Returns:
        Markdown `<fiche_category code="X">\\n\\n# X — …\\n…\\n</fiche_category>\\n`.

    Sections produites :
        1. Titre + libellé
        2. Position dans la classification (chapter + block)
        3. Codes enfants directs (omise si catégorie = feuille)
        4. Périmètre clinique (héritages + niveau code agrégé)
        5. À ne pas décrire (héritages + niveau code agrégé)
        6. Formulations cliniques alternatives (agrégées, plafonnées
           à `CATEGORY_FORMULATIONS_MAX`)
    """
    sections = [
        _category_title(category_code, ctx),
        _section_hierarchy(category_code, ctx),
        _category_section_children(category_code, ctx),
        _category_section_perimeter(category_code, ctx),
        _category_section_exclusions(category_code, ctx),
        _category_section_formulations(category_code, ctx, rng),
    ]
    body = "\n\n".join(s for s in sections if s)
    return f'<fiche_category code="{category_code}">\n\n{body}\n\n</fiche_category>\n'


def _detect_category_sections(card: str) -> dict[str, bool]:
    """Détecte les sections principales d'une fiche catégorie."""
    return {
        key: bool(re.search(rf"^## {re.escape(title)}$", card, re.MULTILINE))
        for key, title in _CATEGORY_SECTION_TITLES.items()
    }


def build_categories_library(
    *,
    ctx: ExplorationContext | None = None,
    output_dir: Path = Path("outputs/cards_library_categories"),
    chapter_filter: str | None = None,
    limit: int | None = None,
    seed: int = DEFAULT_SEED,
    progress: bool = True,
) -> BuildSummary:
    """Génère la bibliothèque complète de fiches catégories 3-car.

    Itère sur les ~2 054 catégories 3-car de `merged` (type=category,
    len(code)=3), écrit `<chapter>/<code>.md` et produit `_index.csv`.
    """
    if ctx is None:
        ctx = load_exploration_context(with_external=True)
    merged = _eager(ctx.merged)

    cat_3car = merged.filter(
        (pl.col("type") == "category") & (pl.col("code").str.len_chars() == 3)
    ).with_columns(pl.col("path").str.split("/").list.get(0).alias("chapter"))
    if chapter_filter is not None:
        cat_3car = cat_3car.filter(pl.col("chapter") == chapter_filter)
    cat_3car = cat_3car.sort("code")
    if limit is not None:
        cat_3car = cat_3car.head(limit)

    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    index_rows: list[dict[str, object]] = []
    errors: list[tuple[str, str]] = []
    t0 = time.perf_counter()
    n_written = 0
    n_total = cat_3car.height

    for i, row in enumerate(cat_3car.iter_rows(named=True), 1):
        code = row["code"]
        chapter = row["chapter"]
        libelle = row["label"] or ""
        try:
            card = build_category_card(code, ctx, rng)
            chap_dir = output_dir / chapter
            chap_dir.mkdir(parents=True, exist_ok=True)
            fname = f"{code}.md"
            (chap_dir / fname).write_text(card, encoding="utf-8")
            sections = _detect_category_sections(card)
            n_enfants = len(_category_direct_children(code, merged))
            index_rows.append(
                {
                    "code": code,
                    "chapter": chapter,
                    "filepath": f"{chapter}/{fname}",
                    "libelle": libelle,
                    "n_enfants": n_enfants,
                    "nb_chars": len(card),
                    **sections,
                }
            )
            n_written += 1
        except Exception as exc:
            errors.append((code, str(exc)))
            log.warning("Échec build_category_card(%s) : %s", code, exc)
            continue

        if progress and i % 500 == 0:
            log.info(
                "Progression catégories : %d / %d (%.1fs écoulées)",
                i,
                n_total,
                time.perf_counter() - t0,
            )

    index_path = output_dir / "_index.csv"
    if index_rows:
        ordered_cols = [
            "code",
            "chapter",
            "filepath",
            "libelle",
            "n_enfants",
            "has_perimetre",
            "has_exclusions",
            "has_formulations",
            "nb_chars",
        ]
        pl.DataFrame(index_rows).select(ordered_cols).write_csv(index_path)

    elapsed = time.perf_counter() - t0
    return BuildSummary(
        n_codes_total=n_total,
        n_written=n_written,
        n_errors=len(errors),
        elapsed_seconds=elapsed,
        output_dir=output_dir,
        index_path=index_path,
        errors=tuple(errors),
    )
