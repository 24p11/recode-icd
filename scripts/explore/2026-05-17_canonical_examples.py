# ruff: noqa
"""Inspection brute des 7 codes canoniques pour `docs/canonical_examples.md`.

Format : fichier `.py` avec cellules `# %%` (jupytext percent),
exécutable cellule par cellule dans VSCode ou Jupyter Lab.

But : pour chaque code canonique, dumper côte à côte ce que livre OFS,
ce que livre ANS, ce qui finit dans le CSV final, ce qui apparaît dans
`note_merges.csv` et — si pertinent — les associations dague/astérisque.

Convention recode-icd :
  Inspection PURE — aucune logique métier réutilisable. Si une requête
  semble réutilisable, elle doit migrer dans `src/recode_icd/`, pas
  rester ici.
"""

# %% Init
from __future__ import annotations

from pathlib import Path

import polars as pl

from recode_icd.utils.loaders_dev import load_exploration_context

ctx = load_exploration_context()

# Configuration polars : on ne tronque pas, on veut voir tout le texte.
pl.Config.set_fmt_str_lengths(500)
pl.Config.set_tbl_rows(50)
pl.Config.set_tbl_width_chars(200)
pl.Config.set_fmt_table_cell_list_len(20)

# Sources brutes OFS (raccourcis locaux).
master = ctx.ofs["master"].filter(pl.col("valid") == 1)
libelle = ctx.ofs["libelle"].filter(pl.col("valid") == 1)
system = ctx.ofs["system"]
include = ctx.ofs["include"]
exclude = ctx.ofs["exclude"]
descr = ctx.ofs["descr"]
indir = ctx.ofs["indir"]
dagstar = ctx.ofs["dagstar"]
note = ctx.ofs["note"]
memo = ctx.ofs["memo"].filter(pl.col("valid") == "Yes")

# Tables d'associations dague/astérisque dérivées (post-loader).
_PROCESSED = Path(__file__).resolve().parents[2] / "referentials" / "processed"
ofs_dagstar_pairs = (
    pl.read_parquet(_PROCESSED / "ofs_dagger_asterisk.parquet")
    if (_PROCESSED / "ofs_dagger_asterisk.parquet").is_file()
    else None
)
owl_dagstar_pairs = (
    pl.read_parquet(_PROCESSED / "owl_dagger_asterisk.parquet")
    if (_PROCESSED / "owl_dagger_asterisk.parquet").is_file()
    else None
)

ans = ctx.ans
flat = ctx.flat
note_merges = ctx.reports.get("note_merges")

# Map code → SID (premier hit, valid=1).
_code_to_sid = dict(
    zip(master["code"].to_list(), master["SID"].to_list(), strict=True)
)


# %% Helper d'inspection
def _sid_of(code: str) -> int | None:
    return _code_to_sid.get(code)


def _print_section(title: str) -> None:
    print(f"\n--- {title} ---")


def _print_block(text: str | None) -> None:
    if text is None:
        print("  ABSENT")
        return
    for line in text.splitlines() or [""]:
        print(f"  {line}")


def _print_list(items: list[str] | None, *, empty_msg: str = "ABSENT") -> None:
    if items is None or len(items) == 0:
        print(f"  {empty_msg}")
        return
    for item in items:
        if item is None:
            continue
        for i, line in enumerate(str(item).splitlines() or [""]):
            prefix = "  - " if i == 0 else "    "
            print(f"{prefix}{line}")


def _libelle_for(sid: int, source: str) -> pl.DataFrame:
    """Renvoie les libellés OFS d'une source donnée pour un SID."""
    return libelle.filter(
        (pl.col("SID") == sid) & (pl.col("source") == source)
    ).select("LID", "libelle")


def inspect_code(code: str, label: str) -> None:
    """Dump structuré de tout ce que les sources disent sur `code`."""
    print("=" * 78)
    print(f"CODE : {code}  —  {label}")
    print("=" * 78)

    sid = _sid_of(code)

    # 1. Position dans la hiérarchie OFS (MASTER).
    _print_section("Hiérarchie OFS (MASTER)")
    if sid is None:
        print("  ABSENT dans OFS (code post-2006 ou code inconnu)")
    else:
        row = master.filter(pl.col("SID") == sid).row(0, named=True)
        print(f"  SID      = {row['SID']}")
        print(f"  code     = {row['code']}")
        print(f"  level    = {row['level']}")
        print(f"  type OFS = {row['type']}  (C=chapter G/U=block K/S/D=category)")
        parents = [row[f"id{i}"] for i in range(1, 8) if row[f"id{i}"] != 0]
        parents_codes = []
        for pid in parents:
            match = master.filter(pl.col("SID") == pid)
            if not match.is_empty():
                parents_codes.append(
                    f"{match['code'][0]}(SID={pid})"
                )
            else:
                parents_codes.append(f"?(SID={pid})")
        print(f"  parents  = {' → '.join(parents_codes) if parents_codes else 'racine'}")

    # 2. Libellé systématique.
    _print_section("Libellé systématique")
    if sid is None:
        print("  OFS : ABSENT")
    else:
        ofs_label = _libelle_for(sid, "S")
        if ofs_label.is_empty():
            print("  OFS : ABSENT (pas de LIBELLE source='S')")
        else:
            for lbl in ofs_label["libelle"].to_list():
                print(f"  OFS : {lbl}")
    if ans is not None:
        ans_row = ans.filter(pl.col("code") == code)
        if ans_row.is_empty():
            print("  ANS : ABSENT")
        else:
            print(f"  ANS : {ans_row['label'][0]}")
    else:
        print("  ANS : (Parquet ANS non chargé)")

    # 3. Inclusions.
    _print_section("Inclusions")
    if sid is None:
        print("  OFS : ABSENT")
    else:
        inc_lids = include.filter(pl.col("SID") == sid)["LID"].to_list()
        if not inc_lids:
            print("  OFS : ABSENT (pas de ligne INCLUDE)")
        else:
            ofs_inc = (
                libelle.filter(
                    (pl.col("LID").is_in(inc_lids)) & (pl.col("source") == "I")
                )["libelle"]
                .to_list()
            )
            _print_list(ofs_inc, empty_msg="ABSENT (LID INCLUDE sans LIBELLE source='I')")
    if ans is not None:
        ans_row = ans.filter(pl.col("code") == code)
        if ans_row.is_empty():
            print("  ANS : ABSENT")
        else:
            inc_note = ans_row["inclusion_note"][0]
            if inc_note is None:
                print("  ANS : ABSENT (pas de xkos:inclusionNote)")
            else:
                print("  ANS (bloc unique xkos:inclusionNote) :")
                _print_block(inc_note)

    # 4. Descripteurs OFS (synonymes implicites, source='D').
    _print_section("Descripteurs OFS (synonymes implicites, LIBELLE source='D')")
    if sid is None:
        print("  ABSENT")
    else:
        descr_lids = descr.filter(pl.col("SID") == sid)["LID"].to_list()
        if not descr_lids:
            print("  ABSENT (pas de ligne DESCR)")
        else:
            ofs_descr_rows = libelle.filter(
                (pl.col("LID").is_in(descr_lids)) & (pl.col("source") == "D")
            ).select("SID", "LID", "libelle")
            if ofs_descr_rows.is_empty():
                print("  ABSENT (LID DESCR sans LIBELLE source='D')")
            else:
                ofs_descr = [
                    f"{r['libelle']} (SID={r['SID']}, LID={r['LID']})"
                    for r in ofs_descr_rows.iter_rows(named=True)
                ]
                _print_list(ofs_descr)

    # 5. Synonymes ANS (skos:altLabel).
    _print_section("Synonymes ANS (skos:altLabel)")
    if ans is None:
        print("  (Parquet ANS non chargé)")
    else:
        ans_row = ans.filter(pl.col("code") == code)
        if ans_row.is_empty():
            print("  ABSENT")
        else:
            syns = ans_row["synonymes"][0]
            if syns is None or len(syns) == 0:
                print("  ABSENT (pas d'altLabel)")
            else:
                _print_list(list(syns))

    # 6. Exclusions typées.
    _print_section("Exclusions typées")
    if sid is None:
        print("  OFS : ABSENT")
    else:
        excl_rows = exclude.filter(pl.col("SID") == sid)
        if excl_rows.is_empty():
            print("  OFS : ABSENT (pas de ligne EXCLUDE)")
        else:
            for excl_row in excl_rows.iter_rows(named=True):
                lid = excl_row["LID"]
                excl_sid = excl_row["excl"]
                daget = excl_row["daget"]
                plus = excl_row["plus"]
                text_row = libelle.filter(
                    (pl.col("LID") == lid) & (pl.col("source") == "E")
                )
                text = text_row["libelle"][0] if not text_row.is_empty() else "(libellé absent)"
                redir = master.filter(pl.col("SID") == excl_sid)
                redir_code = redir["code"][0] if not redir.is_empty() else "(aucun)"
                print(f"  - texte    : {text}")
                print(f"    redirige : {redir_code}  (excl SID={excl_sid})")
                print(f"    daget    : {daget!r}  plus : {plus!r}")
    if ans is not None:
        ans_row = ans.filter(pl.col("code") == code)
        if ans_row.is_empty():
            print("  ANS : ABSENT")
        else:
            exc_notes = ans_row["exclusion_notes"][0]
            if exc_notes is None or len(exc_notes) == 0:
                print("  ANS : ABSENT (pas de xkos:exclusionNote)")
            else:
                print("  ANS (blocs xkos:exclusionNote, parfois multi-éléments) :")
                for n in exc_notes:
                    print("  ┈┈")
                    _print_block(n)
            struct_exc = ans_row["structured_exclusions"][0]
            if struct_exc is not None and len(struct_exc) > 0:
                print("  ANS (atih-cim10:exclusion structurées) :")
                _print_list(list(struct_exc))

    # 7. Exclusions indirectes (INDIR).
    _print_section("Exclusions indirectes (INDIR, LIBELLE source='N')")
    if sid is None:
        print("  ABSENT")
    else:
        indir_lids = indir.filter(pl.col("SID") == sid)["LID"].to_list()
        if not indir_lids:
            print("  ABSENT (pas de ligne INDIR)")
        else:
            ofs_indir = (
                libelle.filter(
                    (pl.col("LID").is_in(indir_lids)) & (pl.col("source") == "N")
                )["libelle"]
                .to_list()
            )
            _print_list(ofs_indir, empty_msg="ABSENT (LID INDIR sans LIBELLE source='N')")

    # 8. Notes éditoriales (NOTE + MEMO).
    _print_section("Notes éditoriales (NOTE → MEMO)")
    if sid is None:
        print("  OFS : ABSENT")
    else:
        mids = note.filter(pl.col("SID") == sid)["MID"].to_list()
        if not mids:
            print("  OFS : ABSENT (pas de ligne NOTE)")
        else:
            ofs_memos = (
                memo.filter(pl.col("MID").is_in(mids))["memo"].to_list()
            )
            if not ofs_memos:
                print("  OFS : ABSENT (MID sans MEMO valid='Yes')")
            else:
                for m in ofs_memos:
                    print("  ┈┈")
                    _print_block(m)
    if ans is not None:
        ans_row = ans.filter(pl.col("code") == code)
        if not ans_row.is_empty():
            scope_notes = ans_row["scope_notes"][0]
            definitions = ans_row["definitions"][0]
            if scope_notes is not None and len(scope_notes) > 0:
                print("  ANS (skos:scopeNote) :")
                for n in scope_notes:
                    print("  ┈┈")
                    _print_block(n)
            if definitions is not None and len(definitions) > 0:
                print("  ANS (skos:definition) :")
                for n in definitions:
                    print("  ┈┈")
                    _print_block(n)

    # 9. Appariements dague / astérisque.
    _print_section("Appariements dague/astérisque (DAGSTAR)")
    if sid is None:
        print("  OFS DAGSTAR (brut) : ABSENT")
    else:
        # DAGSTAR brut : SID=ancrage, assoc=SID du code apparié.
        # Cas 1 : ce code est l'ancrage (SID source).
        src_rows = dagstar.filter(pl.col("SID") == sid)
        if not src_rows.is_empty():
            print("  OFS DAGSTAR (ce code comme SID source) :")
            for r in src_rows.iter_rows(named=True):
                assoc_code = master.filter(pl.col("SID") == r["assoc"])
                assoc_str = assoc_code["code"][0] if not assoc_code.is_empty() else "?"
                print(
                    f"  - assoc={assoc_str} (SID={r['assoc']})  "
                    f"daget={r['daget']!r}  plus={r['plus']!r}  LID={r['LID']}"
                )
        # Cas 2 : ce code apparaît comme assoc (destination).
        dst_rows = dagstar.filter(pl.col("assoc") == sid)
        if not dst_rows.is_empty():
            print("  OFS DAGSTAR (ce code comme destination assoc) :")
            for r in dst_rows.iter_rows(named=True):
                src_code = master.filter(pl.col("SID") == r["SID"])
                src_str = src_code["code"][0] if not src_code.is_empty() else "?"
                print(
                    f"  - source={src_str} (SID={r['SID']})  "
                    f"daget={r['daget']!r}  plus={r['plus']!r}  LID={r['LID']}"
                )
        if src_rows.is_empty() and dst_rows.is_empty():
            print("  OFS DAGSTAR (brut) : ABSENT")

    if ofs_dagstar_pairs is not None:
        pairs = ofs_dagstar_pairs.filter(
            (pl.col("start_code") == code) | (pl.col("end_code") == code)
        )
        if pairs.is_empty():
            print("  ofs_dagger_asterisk.parquet : ABSENT")
        else:
            print("  ofs_dagger_asterisk.parquet :")
            for r in pairs.iter_rows(named=True):
                print(
                    f"  - {r['start_code']} ↔ {r['end_code']}  "
                    f"daget={r['daget']!r}  plus={r['plus']!r}"
                )
    if owl_dagstar_pairs is not None:
        pairs = owl_dagstar_pairs.filter(
            (pl.col("dagger_code") == code) | (pl.col("asterisk_code") == code)
        )
        if pairs.is_empty():
            print("  owl_dagger_asterisk.parquet (ANS) : ABSENT")
        else:
            print("  owl_dagger_asterisk.parquet (ANS) :")
            for r in pairs.iter_rows(named=True):
                print(
                    f"  - dagger={r['dagger_code']} * asterisk={r['asterisk_code']}  "
                    f"evidence={list(r['evidence'])}"
                )

    # 10. Dans le CSV final.
    _print_section("Dans le CSV final (inclusions_exclusions_synonymes.csv)")
    if flat is None:
        print("  (CSV final non chargé)")
    else:
        rows = flat.filter(pl.col("code") == code)
        if rows.is_empty():
            print("  ABSENT")
        else:
            print(f"  {len(rows)} lignes :")
            for r in rows.iter_rows(named=True):
                print(
                    f"  - type={r['type']:<10}  source={r['source']:<14}  "
                    f"libelle={r['libelle']!r}"
                )
                _print_block(f"    texte : {r['texte']}")

    # 11. Dans note_merges.
    _print_section("Dans note_merges.csv")
    if note_merges is None:
        print("  (rapport non chargé)")
    else:
        rows = note_merges.filter(pl.col("code") == code)
        if rows.is_empty():
            print("  ABSENT (pas de note OFS/ANS à réconcilier pour ce code)")
        else:
            for r in rows.iter_rows(named=True):
                marker = (
                    "IDENT" if r["libelles_identiques_apres_normalisation"] else "    "
                )
                marker_div = "DIV" if r["difference_significative"] else "   "
                print(
                    f"  - type={r['type']:<10}  [{marker}|{marker_div}]"
                )
                print(f"    OFS retenu : {r['texte_retenu']}")
                print(f"    ANS altern : {r['texte_alternatif_ans']}")

    print()


# %% I78.1 — Atomicité OFS vs bloc ANS
inspect_code("I78.1", "Atomicité OFS vs bloc ANS (exclusions multiples)")

# %% U07.1 — Code post-2006, ANS only (COVID-19)
inspect_code("U07.1", "Code post-2006, ANS only (COVID-19)")

# %% A18.1 — Dague/astérisque systématique (Tuberculose appareil génito-urinaire, daget=T)
inspect_code("A18.1", "Dague/astérisque systématique (daget=T)")

# %% N74.0 — Dague/astérisque systématique (Tuberculose appareil génito-urinaire, daget=T)
inspect_code("N74.0", "Dague/astérisque systématique (daget=T)")

# %% N51.0— Dague/astérisque systématique (Tuberculose appareil génito-urinaire, daget=T)
inspect_code("N51.0", "Dague/astérisque systématique (daget=T)")

# %% C50.8 — Catégorie C00-C75, skip synthèse frère
inspect_code("C50.8", "Catégorie C00-C75 — skip synthèse frère")

# %% M24 — Exclusion indirecte (INDIR)
inspect_code("M24", "Exclusion indirecte (INDIR)")

# %% E84 — Descripteur OFS (DESCR) Mucoviscidose
inspect_code("E84", "Code avec descripteur DESCR distinct des inclusions (Mucoviscidose)")

# %% K35.8 — Code .8 avec synthèse de frères active
inspect_code("K35.8", "Code .8 avec synthèse de frères active (Appendicite)")

# %% E10.3 — dague 
inspect_code("E10.3", "Code dague")


# %%
