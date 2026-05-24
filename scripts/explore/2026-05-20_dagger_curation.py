# ruff: noqa
"""Outil d'aide à la curation manuelle de `docs/dagger_subordinate_pairs.yaml`.

Trois modes (cf. brief de session) :
  1. Inspection (défaut)         — lecture seule, dump formaté des paires.
  2. `--generate-workbook`       — produit un YAML éditable pré-rempli.
  3. `--merge-workbook`          — fusionne le workbook édité dans le YAML cible.

Le script n'embarque AUCUNE logique métier réutilisable : c'est de
l'I/O + édition. Cf. `docs/source_mapping.md` §"Couples dague/astérisque"
pour la sémantique des champs.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import polars as pl
import yaml

_ROOT = Path(__file__).resolve().parents[2]
TABLE_PATH = _ROOT / "referentials" / "processed" / "dagger_asterisk.parquet"
YAML_PATH = _ROOT / "docs" / "dagger_subordinate_pairs.yaml"
DEFAULT_WORKBOOK = _ROOT / "scripts" / "explore" / "curation_workbook.yaml"

VALID_REDUNDANCY = frozenset({"subordinate", "independent", "undecided", ""})


# --------------------------------------------------------------------------- #
# Chargement / sauvegarde
# --------------------------------------------------------------------------- #
def load_table(path: Path = TABLE_PATH) -> pl.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Table dague/astérisque introuvable : {path}")
    return pl.read_parquet(path)


def load_curated_yaml(path: Path = YAML_PATH) -> dict[str, list[dict]]:
    """Lit le YAML cible. Fichier ou clés absents → listes vides."""
    if not path.is_file():
        return {"subordinate_pairs": [], "independent_pairs": []}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        "subordinate_pairs": list(raw.get("subordinate_pairs") or []),
        "independent_pairs": list(raw.get("independent_pairs") or []),
    }


def save_curated_yaml(path: Path, data: dict[str, list[dict]]) -> None:
    """Écrit le YAML cible avec en-tête de commentaires, tri stable par
    (dagger, asterisk) au sein de chaque liste."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sub = sorted(
        data.get("subordinate_pairs") or [],
        key=lambda p: (p.get("dagger") or "", p.get("asterisk") or ""),
    )
    indep = sorted(
        data.get("independent_pairs") or [],
        key=lambda p: (p.get("dagger") or "", p.get("asterisk") or ""),
    )
    header = (
        "# Couples dague/astérisque curés manuellement.\n"
        "# Voir docs/source_mapping.md §\"Couples dague/astérisque\".\n"
        "#\n"
        "# Deux listes en miroir :\n"
        "#   - subordinate_pairs : le code dague est sémantiquement subordonné\n"
        "#                          à la combinaison (cas typique des maladies\n"
        "#                          infectieuses). Le merger appliquera\n"
        "#                          is_redundant_dagger=True sur la ligne dague.\n"
        "#   - independent_pairs : revus explicitement, gardent independent\n"
        "#                          (trace de la décision, optionnel).\n"
        "# Tout couple absent des deux listes hérite du défaut 'independent'.\n"
        "\n"
    )
    body = yaml.safe_dump(
        {"subordinate_pairs": sub, "independent_pairs": indep},
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )
    path.write_text(header + body, encoding="utf-8")


def curated_lookup(curated: dict[str, list[dict]]) -> dict[tuple[str, str], str]:
    """Map (dagger, asterisk) → 'subordinate' | 'independent'."""
    out: dict[tuple[str, str], str] = {}
    for p in curated.get("subordinate_pairs", []):
        out[(p["dagger"], p["asterisk"])] = "subordinate"
    for p in curated.get("independent_pairs", []):
        out[(p["dagger"], p["asterisk"])] = "independent"
    return out


# --------------------------------------------------------------------------- #
# Sélection
# --------------------------------------------------------------------------- #
def select_pairs(
    table: pl.DataFrame,
    *,
    chapter: str | None = None,
    prefix: str | None = None,
    uncurated_only: bool = False,
    curated_lookup_map: dict[tuple[str, str], str] | None = None,
    limit: int | None = None,
) -> pl.DataFrame:
    """Filtre les paires complètes selon les critères. Tri stable
    (dagger_code, asterisk_code). Les paires incomplètes (un côté NULL)
    sont systématiquement exclues — la curation n'a de sens que sur des
    paires complètes."""
    df = table.filter(
        pl.col("dagger_code").is_not_null() & pl.col("asterisk_code").is_not_null()
    )
    if chapter is not None:
        df = df.filter(
            pl.col("dagger_code").str.starts_with(chapter)
            | pl.col("asterisk_code").str.starts_with(chapter)
        )
    if prefix is not None:
        df = df.filter(
            pl.col("dagger_code").str.starts_with(prefix)
            | pl.col("asterisk_code").str.starts_with(prefix)
        )
    if uncurated_only and curated_lookup_map:
        keys = list(curated_lookup_map.keys())
        curated_df = pl.DataFrame(
            {
                "dagger_code": [k[0] for k in keys],
                "asterisk_code": [k[1] for k in keys],
            }
        )
        df = df.join(curated_df, on=["dagger_code", "asterisk_code"], how="anti")
    df = df.sort(["dagger_code", "asterisk_code"])
    if limit is not None:
        df = df.head(limit)
    return df


# --------------------------------------------------------------------------- #
# Mode 1 : inspection
# --------------------------------------------------------------------------- #
def format_pair_for_inspection(
    row: dict,
    idx: int,
    total: int,
    curated_status: str | None,
) -> str:
    sep_wide = "=" * 78
    sep_thin = "-" * 78
    tag = (
        f"  [DÉJÀ CURÉ: {curated_status}]" if curated_status else "  [non curé]"
    )
    dag = row["dagger_code"]
    ast = row["asterisk_code"]
    dag_label = row.get("dagger_label") or "(absent)"
    ast_label = row.get("asterisk_label") or "(absent)"
    combs = list(row.get("combination_labels") or [])
    levels = list(row.get("levels_present") or [])
    lines = [
        sep_wide,
        f"[{idx}/{total}] dague={dag} ↔ astérisque={ast}{tag}",
        sep_thin,
        f"Dague {dag}     : {dag_label!r}",
        f"Astérisque {ast}: {ast_label!r}",
        "Libellés observés (combination_labels) :",
    ]
    if combs:
        for c in combs:
            lines.append(f"  - {c!r}")
    else:
        lines.append("  (aucun)")
    lines.append(f"Niveaux DAGSTAR : {levels}")
    lines.append(sep_wide)
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Mode 2 : génération du workbook
# --------------------------------------------------------------------------- #
def _s(value: object) -> str:
    """JSON-encode une string (JSON ⊂ YAML pour les strings, gère
    l'échappement correctement). None → 'null'."""
    if value is None:
        return "null"
    return json.dumps(value, ensure_ascii=False)


def write_workbook(
    path: Path,
    pairs: pl.DataFrame,
    *,
    curator: str,
    today: date,
    selector_description: str = "(filtres non spécifiés)",
) -> None:
    """Écrit le workbook éditable. Refuse d'écraser un fichier existant."""
    if path.exists():
        raise FileExistsError(
            f"Workbook existe déjà : {path}. "
            "Supprime-le ou utilise --workbook-path différent."
        )

    lines = [
        f"# Workbook de curation dague/astérisque — généré le {today.isoformat()}",
        f"# Sélection : {selector_description}",
        "# Champs à remplir : redundancy_level (subordinate / independent /",
        "#                   undecided / \"\"), rationale (optionnel mais recommandé).",
        "# Les commentaires d'aide (dagger_label, etc.) ne sont PAS recopiés",
        "# dans le YAML cible.",
        "",
        "pairs:",
    ]

    for r in pairs.iter_rows(named=True):
        lines.append(f"  - dagger: {_s(r['dagger_code'])}")
        lines.append(f"    asterisk: {_s(r['asterisk_code'])}")
        lines.append('    redundancy_level: ""   # subordinate / independent / undecided')
        lines.append('    rationale: ""')
        lines.append(f"    curated_by: {_s(curator)}")
        lines.append(f"    curated_date: {_s(today.isoformat())}")
        lines.append("    # --- Aide à la décision (ignoré au merge) ---")
        lines.append(f"    # dagger_label: {_s(r.get('dagger_label'))}")
        lines.append(f"    # asterisk_label: {_s(r.get('asterisk_label'))}")
        combs = list(r.get("combination_labels") or [])
        if combs:
            lines.append("    # combination_labels:")
            for c in combs:
                lines.append(f"    #   - {_s(c)}")
        else:
            lines.append("    # combination_labels: []")
        levels = list(r.get("levels_present") or [])
        if levels:
            inline = "[" + ", ".join(_s(x) for x in levels) + "]"
        else:
            inline = "[]"
        lines.append(f"    # levels_present: {inline}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Mode 3 : merge
# --------------------------------------------------------------------------- #
def read_workbook(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"Workbook absent : {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    pairs = raw.get("pairs")
    if not isinstance(pairs, list):
        raise ValueError(
            f"Workbook invalide : clé 'pairs' attendue (liste). Reçu : {type(pairs).__name__}."
        )
    for i, p in enumerate(pairs):
        if not isinstance(p, dict):
            raise ValueError(f"Workbook : entrée #{i} n'est pas un dict.")
        if "dagger" not in p or "asterisk" not in p:
            raise ValueError(
                f"Workbook : entrée #{i} doit avoir 'dagger' et 'asterisk'."
            )
    return pairs


@dataclass
class MergeReport:
    added_subordinate: list[tuple[str, str]] = field(default_factory=list)
    added_independent: list[tuple[str, str]] = field(default_factory=list)
    ignored: list[tuple[str, str, str]] = field(default_factory=list)
    conflicts: list[tuple[str, str, str, str]] = field(default_factory=list)
    identical: list[tuple[str, str]] = field(default_factory=list)


def merge_into_curated(
    workbook_pairs: list[dict],
    curated: dict[str, list[dict]],
) -> tuple[dict[str, list[dict]], MergeReport]:
    """Pure. Retourne (nouveau YAML curé, rapport). Ne mute pas
    `curated`. Lève ValueError si une `redundancy_level` est invalide."""
    # Validation pré-merge
    for p in workbook_pairs:
        rl = p.get("redundancy_level", "")
        if rl not in VALID_REDUNDANCY:
            raise ValueError(
                f"redundancy_level invalide : {rl!r} pour "
                f"({p.get('dagger')}, {p.get('asterisk')}). "
                f"Valeurs admises : {sorted(VALID_REDUNDANCY)}."
            )

    new_sub = list(curated.get("subordinate_pairs") or [])
    new_indep = list(curated.get("independent_pairs") or [])
    existing = curated_lookup(curated)
    report = MergeReport()

    for p in workbook_pairs:
        dagger = p["dagger"]
        asterisk = p["asterisk"]
        rl = p.get("redundancy_level", "")
        key = (dagger, asterisk)

        if rl in ("", "undecided"):
            report.ignored.append((dagger, asterisk, rl or "empty"))
            continue

        if key in existing:
            if existing[key] == rl:
                report.identical.append(key)
            else:
                report.conflicts.append((dagger, asterisk, existing[key], rl))
            continue

        entry = {
            "dagger": dagger,
            "asterisk": asterisk,
            "rationale": p.get("rationale", ""),
            "curated_by": p.get("curated_by", ""),
            "curated_date": p.get("curated_date", ""),
        }
        if rl == "subordinate":
            new_sub.append(entry)
            report.added_subordinate.append(key)
        else:
            new_indep.append(entry)
            report.added_independent.append(key)

    return (
        {"subordinate_pairs": new_sub, "independent_pairs": new_indep},
        report,
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Aide à la curation du YAML dague/astérisque (3 modes).",
    )
    p.add_argument("--chapter", default=None, help="Filtre : 1re lettre du code (A, I, …)")
    p.add_argument("--prefix", default=None, help="Filtre : préfixe du code (ex. A17, E10.2)")
    p.add_argument("--uncurated-only", action="store_true", help="Exclut les paires déjà dans le YAML cible.")
    p.add_argument("--limit", type=int, default=None, help="Tronque à N paires.")
    p.add_argument("--generate-workbook", action="store_true", help="Mode 2 : produit un workbook éditable.")
    p.add_argument("--merge-workbook", action="store_true", help="Mode 3 : fusionne le workbook dans le YAML cible.")
    p.add_argument("--workbook-path", type=Path, default=DEFAULT_WORKBOOK)
    p.add_argument("--yaml-path", type=Path, default=YAML_PATH)
    p.add_argument("--table-path", type=Path, default=TABLE_PATH)
    p.add_argument("--curator", default="", help="Nom du curateur pour le workbook (mode 2).")
    return p


def _selector_description(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.chapter:
        parts.append(f"chapter={args.chapter}")
    if args.prefix:
        parts.append(f"prefix={args.prefix}")
    if args.uncurated_only:
        parts.append("uncurated_only")
    if args.limit:
        parts.append(f"limit={args.limit}")
    return ", ".join(parts) if parts else "(aucun filtre)"


def _run_mode_inspect(args: argparse.Namespace) -> int:
    try:
        table = load_table(args.table_path)
    except FileNotFoundError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        print(
            "→ Lance d'abord la Phase 1 pour produire la table dague/astérisque.",
            file=sys.stderr,
        )
        return 2

    curated = load_curated_yaml(args.yaml_path)
    lookup = curated_lookup(curated)
    selected = select_pairs(
        table,
        chapter=args.chapter,
        prefix=args.prefix,
        uncurated_only=args.uncurated_only,
        curated_lookup_map=lookup,
        limit=args.limit,
    )
    total = len(selected)
    n_sub = 0
    n_indep = 0
    for idx, r in enumerate(selected.iter_rows(named=True), start=1):
        key = (r["dagger_code"], r["asterisk_code"])
        status = lookup.get(key)
        if status == "subordinate":
            n_sub += 1
        elif status == "independent":
            n_indep += 1
        print(format_pair_for_inspection(r, idx, total, status))

    n_remaining = total - n_sub - n_indep
    print(
        f"\n{total} paire(s) affichée(s) "
        f"(subordinate déjà curées : {n_sub}, "
        f"independent déjà curées : {n_indep}, "
        f"restant à curer : {n_remaining})"
    )
    return 0


def _run_mode_generate(args: argparse.Namespace) -> int:
    try:
        table = load_table(args.table_path)
    except FileNotFoundError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 2

    curated = load_curated_yaml(args.yaml_path)
    lookup = curated_lookup(curated)
    selected = select_pairs(
        table,
        chapter=args.chapter,
        prefix=args.prefix,
        uncurated_only=args.uncurated_only,
        curated_lookup_map=lookup,
        limit=args.limit,
    )
    try:
        write_workbook(
            args.workbook_path,
            selected,
            curator=args.curator,
            today=date.today(),
            selector_description=_selector_description(args),
        )
    except FileExistsError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1
    print(f"Workbook écrit : {args.workbook_path} ({len(selected)} paire(s))")
    print("À éditer : remplir redundancy_level + rationale, puis --merge-workbook.")
    return 0


def _run_mode_merge(args: argparse.Namespace) -> int:
    try:
        workbook_pairs = read_workbook(args.workbook_path)
    except FileNotFoundError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        print(
            "→ Génère d'abord un workbook avec --generate-workbook.",
            file=sys.stderr,
        )
        return 2
    except (ValueError, yaml.YAMLError) as e:
        print(f"Erreur : workbook invalide → {e}", file=sys.stderr)
        return 1

    curated = load_curated_yaml(args.yaml_path)
    try:
        new_curated, report = merge_into_curated(workbook_pairs, curated)
    except ValueError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1

    if report.conflicts:
        print("Conflits détectés — YAML cible NON modifié :", file=sys.stderr)
        for dag, ast, existing, proposed in report.conflicts:
            print(
                f"  - ({dag}, {ast}) : YAML='{existing}', workbook='{proposed}'",
                file=sys.stderr,
            )
        print(
            "→ Résous les conflits manuellement (édition du YAML ou du workbook).",
            file=sys.stderr,
        )
        return 1

    save_curated_yaml(args.yaml_path, new_curated)

    print("Merge terminé :")
    print(f"  + subordinate : {len(report.added_subordinate)} ajoutée(s)")
    print(f"  + independent : {len(report.added_independent)} ajoutée(s)")
    print(f"  = identiques  : {len(report.identical)} (no-op)")
    print(f"  - ignorées    : {len(report.ignored)} (vide ou undecided)")
    print(f"YAML cible : {args.yaml_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    if args.generate_workbook and args.merge_workbook:
        print(
            "Erreur : --generate-workbook et --merge-workbook sont mutuellement exclusifs.",
            file=sys.stderr,
        )
        return 1

    if args.merge_workbook:
        return _run_mode_merge(args)
    if args.generate_workbook:
        return _run_mode_generate(args)
    return _run_mode_inspect(args)


if __name__ == "__main__":
    sys.exit(main())
