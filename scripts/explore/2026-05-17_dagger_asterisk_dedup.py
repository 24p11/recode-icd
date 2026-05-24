# ruff: noqa
"""Exploration empirique de la règle de filtrage des doublons dague/astérisque.

Format : fichier `.py` avec cellules `# %%` (jupytext percent),
exécutable cellule par cellule.

Hypothèse à tester :
    "Pour les codes ayant une association dague/astérisque, on ne
    garde les synonymes/descripteurs (table DESCR) que côté
    manifestation (astérisque). Donc on exclut les descripteurs dont
    le SID OFS apparaît dans DAGSTAR avec daget ∈ {S, T, U}."

Sortie : pour chaque table candidate (DESCR / INCLUDE / EXCLUDE),
mesurer le périmètre du filtrage et le taux de doublons textuels
réels entre côté dague et côté astérisque, puis conclure.

Convention recode-icd : inspection PURE, aucune logique métier
réutilisable n'est introduite dans ce fichier.
"""

# %% Init
from __future__ import annotations

import re
import unicodedata
from collections import Counter

import polars as pl

from recode_icd.utils.loaders_dev import load_exploration_context

ctx = load_exploration_context()

pl.Config.set_fmt_str_lengths(300)
pl.Config.set_tbl_rows(30)
pl.Config.set_tbl_width_chars(200)

master = ctx.ofs["master"].filter(pl.col("valid") == 1)
libelle = ctx.ofs["libelle"].filter(pl.col("valid") == 1)
descr = ctx.ofs["descr"]
include = ctx.ofs["include"]
exclude = ctx.ofs["exclude"]
dagstar = ctx.ofs["dagstar"]
system = ctx.ofs["system"]

# Maps utilitaires (locaux, à usage strict du notebook).
_code_of_sid = dict(zip(master["SID"].to_list(), master["code"].to_list(), strict=True))


def _code(sid: int) -> str:
    return _code_of_sid.get(sid, f"?(SID={sid})")


_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+")


def _normalize(text: str | None) -> str:
    """Normalisation tolérante : NFKD + lowercase + suppression
    ponctuation + collapse whitespace. Conforme à la déduplication
    cible décrite dans docs/source_mapping.md."""
    if text is None:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    # Retirer combining marks (accents).
    no_accent = "".join(c for c in decomposed if not unicodedata.combining(c))
    lower = no_accent.lower()
    no_punct = _PUNCT_RE.sub(" ", lower)
    return _WS_RE.sub(" ", no_punct).strip()


# %% === Section 1 : Volumétrie DAGSTAR par daget ===
print("=" * 78)
print("SECTION 1 — Volumétrie DAGSTAR par daget")
print("=" * 78)

print("\nDistribution brute des valeurs de daget :")
print(dagstar.group_by("daget").len().sort("len", descending=True))

# SID uniques touchés par valeur daget (côté SID source).
print("\nNombre de SID 'source' uniques par daget :")
print(
    dagstar.group_by("daget")
    .agg(pl.col("SID").n_unique().alias("nb_sid_uniques"))
    .sort("nb_sid_uniques", descending=True)
)

# Pour chaque daget, taux de présence du SID dans : SYSTEM, DESCR,
# INCLUDE — on inspecte large, sans présupposer le mapping.
print("\nPour chaque daget, présence du LID dans LIBELLE par source :")
ds_with_lib = dagstar.join(
    libelle.select(["LID", "source"]).rename({"source": "lib_source"}),
    on="LID",
    how="left",
)
print(
    ds_with_lib.group_by(["daget", "lib_source"])
    .len()
    .sort(["daget", "len"], descending=[False, True])
)

# Pour info : sur les daget S/T/U (départ dague selon hypothèse),
# combien d'entrées avec assoc=0 vs assoc≠0 ?
print("\nDaget S/T/U — répartition assoc=0 vs assoc≠0 :")
print(
    dagstar.filter(pl.col("daget").is_in(["S", "T", "U"]))
    .with_columns((pl.col("assoc") == 0).alias("assoc_nul"))
    .group_by(["daget", "assoc_nul"])
    .len()
    .sort(["daget", "assoc_nul"])
)

print(
    "\n→ Résumé section 1 : DAGSTAR contient 6 valeurs daget "
    "(F/G/H/S/T/U). À vue : S/T/U semblent côté 'départ' (dague), "
    "F/G/H côté arrivée (astérisque). Voir le mapping LIBELLE.source "
    "ci-dessus pour valider."
)


# %% === Section 2 : Inspection DESCR sur les codes dague (daget='U') ===
print("\n" + "=" * 78)
print("SECTION 2 — DESCR côté dague (DAGSTAR daget='U')")
print("=" * 78)

dagstar_u = dagstar.filter(pl.col("daget") == "U")
print(f"\nNombre d'entrées DAGSTAR daget='U' : {len(dagstar_u)}")
print(f"  SID dague uniques        : {dagstar_u['SID'].n_unique()}")
print(f"  LID descripteurs uniques : {dagstar_u['LID'].n_unique()}")
print(f"  assoc astérisque uniques : {dagstar_u['assoc'].n_unique()}")

# Total des descripteurs dans DESCR (référence) :
print(f"\nTotal lignes DESCR : {len(descr)}")
print(f"  SID couverts par DESCR : {descr['SID'].n_unique()}")

# Combien de lignes DESCR seraient filtrées si on retire les SID
# qui apparaissent dans DAGSTAR avec daget ∈ {S,T,U} ?
dague_sids = (
    dagstar.filter(pl.col("daget").is_in(["S", "T", "U"]))["SID"].unique().to_list()
)
descr_filtered_out = descr.filter(pl.col("SID").is_in(dague_sids))
print(
    f"\nLignes DESCR avec SID 'dague' (daget S/T/U) : {len(descr_filtered_out)} "
    f"/ {len(descr)} ({len(descr_filtered_out) / max(len(descr), 1) * 100:.1f} %)"
)
print(f"  SID dague uniques filtrés : {descr_filtered_out['SID'].n_unique()}")

# 10 exemples concrets : dague (libellé descripteur) ↔ astérisque.
print("\n10 exemples (dague → assoc astérisque) :")
sample = dagstar_u.head(10)
for r in sample.iter_rows(named=True):
    dague_code = _code(r["SID"])
    aster_code = _code(r["assoc"])
    lib_row = libelle.filter(pl.col("LID") == r["LID"])
    lib_text = lib_row["libelle"][0] if not lib_row.is_empty() else "(LIBELLE absent)"
    lib_source = lib_row["source"][0] if not lib_row.is_empty() else "?"
    # Côté astérisque, les descripteurs présents dans DESCR.
    aster_descr_lids = descr.filter(pl.col("SID") == r["assoc"])["LID"].to_list()
    aster_descr_texts = (
        libelle.filter(pl.col("LID").is_in(aster_descr_lids) & (pl.col("source") == "D"))
        ["libelle"].to_list()
    )
    print(f"  • dague {dague_code} (SID={r['SID']})")
    print(f"    LID={r['LID']} src={lib_source!r} : {lib_text!r}")
    print(f"    → astérisque {aster_code} (SID={r['assoc']})")
    if aster_descr_texts:
        for t in aster_descr_texts:
            mark = "  ⇆ doublon ?" if _normalize(t) == _normalize(lib_text) else ""
            print(f"      DESCR astérisque : {t!r}{mark}")
    else:
        print("      DESCR astérisque : (aucun)")

print(
    "\n→ Résumé section 2 : sur les 10 premiers exemples, regarder "
    "si le libellé descripteur côté dague est répliqué textuellement "
    "(ou via normalisation) dans DESCR côté astérisque."
)


# %% === Section 3 : Doublons sémantiques DESCR dague ↔ astérisque ===
print("\n" + "=" * 78)
print("SECTION 3 — Doublons sémantiques DESCR (dague ↔ astérisque)")
print("=" * 78)

# Toutes les paires (dague, astérisque) issues de DAGSTAR daget=U.
# Pour chaque paire, on récupère :
#   - le texte du descripteur dague (LIBELLE via DAGSTAR.LID)
#   - les textes des descripteurs astérisque (DESCR.SID = assoc → LIBELLE source='D')
pairs = dagstar_u.select(["SID", "LID", "assoc"]).rename(
    {"SID": "dague_sid", "LID": "dague_lid", "assoc": "aster_sid"}
)
pairs = pairs.join(
    libelle.select(["LID", "libelle"]).rename(
        {"LID": "dague_lid", "libelle": "dague_text"}
    ),
    on="dague_lid",
    how="left",
)

aster_descr = (
    descr.join(
        libelle.filter(pl.col("source") == "D").select(["LID", "libelle"]),
        on="LID",
    )
    .group_by("SID")
    .agg(pl.col("libelle").alias("aster_texts"))
)

pairs = pairs.join(
    aster_descr.rename({"SID": "aster_sid"}),
    on="aster_sid",
    how="left",
)

# Normalisation pour comparer.
def _is_dup(row: dict) -> bool:
    dague_norm = _normalize(row["dague_text"])
    aster_texts = row["aster_texts"] or []
    aster_norms = {_normalize(t) for t in aster_texts}
    return dague_norm in aster_norms and dague_norm != ""


pairs = pairs.with_columns(
    pl.struct(["dague_text", "aster_texts"])
    .map_elements(_is_dup, return_dtype=pl.Boolean)
    .alias("is_textual_duplicate")
)

n_total = len(pairs)
n_dup = int(pairs["is_textual_duplicate"].sum())
n_aster_with_descr = int(pairs.filter(pl.col("aster_texts").is_not_null()).height)

print(f"\nNombre total de paires DAGSTAR daget='U' analysées : {n_total}")
print(f"  → dont astérisque a au moins un DESCR  : {n_aster_with_descr}")
print(f"  → dont libellé dague = un DESCR aster  : {n_dup}  ({n_dup / max(n_total, 1) * 100:.1f} %)")
print(f"  → faux doublons (texte différent)      : {n_total - n_dup}")

# Échantillon des "vrais doublons" et des "faux doublons" pour audit.
print("\n10 'vrais doublons' (descr dague ≡ descr astérisque après normalisation) :")
for r in pairs.filter(pl.col("is_textual_duplicate")).head(10).iter_rows(named=True):
    print(f"  • {_code(r['dague_sid'])} (dague) → {_code(r['aster_sid'])} (aster)")
    print(f"    dague   : {r['dague_text']!r}")
    print(f"    astérisque DESCR : {r['aster_texts']}")

print("\n10 'faux doublons' (descr dague absent côté astérisque) :")
for r in pairs.filter(~pl.col("is_textual_duplicate")).head(10).iter_rows(named=True):
    print(f"  • {_code(r['dague_sid'])} (dague) → {_code(r['aster_sid'])} (aster)")
    print(f"    dague   : {r['dague_text']!r}")
    print(f"    astérisque DESCR : {r['aster_texts']}")

print(
    f"\n→ Résumé section 3 : {n_dup}/{n_total} paires ({n_dup / max(n_total, 1) * 100:.1f} %) "
    "présentent un doublon textuel après normalisation. Le complément "
    "représente des descripteurs spécifiques à un côté."
)


# %% === Section 4 : Même analyse pour INCLUDE ===
print("\n" + "=" * 78)
print("SECTION 4 — INCLUDE côté dague vs astérisque")
print("=" * 78)

print(f"\nTotal lignes INCLUDE : {len(include)}")
include_filtered = include.filter(pl.col("SID").is_in(dague_sids))
print(
    f"Lignes INCLUDE avec SID dague (daget S/T/U) : {len(include_filtered)} "
    f"/ {len(include)} ({len(include_filtered) / max(len(include), 1) * 100:.1f} %)"
)

# Pour chaque paire (dague, astérisque) issue de DAGSTAR daget=U,
# comparer les INCLUDE des deux côtés.
dague_inc = (
    include.join(
        libelle.filter(pl.col("source") == "I").select(["LID", "libelle"]),
        on="LID",
    )
    .group_by("SID")
    .agg(pl.col("libelle").alias("dague_inc_texts"))
)
aster_inc = dague_inc.rename({"SID": "aster_sid", "dague_inc_texts": "aster_inc_texts"})
dague_inc = dague_inc.rename({"SID": "dague_sid"})

inc_pairs = (
    dagstar_u.select(["SID", "assoc"])
    .rename({"SID": "dague_sid", "assoc": "aster_sid"})
    .unique()
    .join(dague_inc, on="dague_sid", how="left")
    .join(aster_inc, on="aster_sid", how="left")
)


def _shared_inc(row: dict) -> int:
    a = {_normalize(t) for t in (row["dague_inc_texts"] or [])} - {""}
    b = {_normalize(t) for t in (row["aster_inc_texts"] or [])} - {""}
    return len(a & b)


inc_pairs = inc_pairs.with_columns(
    pl.struct(["dague_inc_texts", "aster_inc_texts"])
    .map_elements(_shared_inc, return_dtype=pl.Int64)
    .alias("nb_shared_inclusions")
)

print(f"\nPaires (dague, astérisque) uniques : {len(inc_pairs)}")
print(f"  paires avec ≥1 inclusion partagée : {int((inc_pairs['nb_shared_inclusions'] > 0).sum())}")
print(f"  inclusions partagées totales      : {int(inc_pairs['nb_shared_inclusions'].sum())}")

print("\n10 paires avec inclusion partagée :")
for r in (
    inc_pairs.filter(pl.col("nb_shared_inclusions") > 0).head(10).iter_rows(named=True)
):
    print(f"  • {_code(r['dague_sid'])} (dague) ↔ {_code(r['aster_sid'])} (aster)")
    print(f"    INCLUDE dague   : {r['dague_inc_texts']}")
    print(f"    INCLUDE aster   : {r['aster_inc_texts']}")
    print(f"    nb partagées    : {r['nb_shared_inclusions']}")

print(
    "\n→ Résumé section 4 : volumétrie + nombre de paires avec INCLUDE "
    "partagés. Si le nombre est proche de 0, la règle de filtrage DESCR "
    "ne se transpose pas mécaniquement à INCLUDE."
)


# %% === Section 5 : EXCLUDE (daget propre, pas via DAGSTAR) ===
print("\n" + "=" * 78)
print("SECTION 5 — EXCLUDE et son champ daget propre")
print("=" * 78)

print(f"\nTotal lignes EXCLUDE : {len(exclude)}")
print("\nDistribution du daget propre dans EXCLUDE :")
print(
    exclude.group_by("daget")
    .len()
    .sort("len", descending=True)
)

# Couples exclusion dague ↔ exclusion astérisque sur le même code.
# Critère : pour chaque SID, regrouper les EXCLUDE et compter ceux
# qui apparaissent sur les deux faces selon daget.
print("\nNombre de SID qui ont à la fois une EXCLUDE daget=T ET daget=U :")
sid_with_T = set(exclude.filter(pl.col("daget") == "T")["SID"].to_list())
sid_with_U = set(exclude.filter(pl.col("daget") == "U")["SID"].to_list())
sid_both = sid_with_T & sid_with_U
print(f"  daget=T : {len(sid_with_T)} SID")
print(f"  daget=U : {len(sid_with_U)} SID")
print(f"  les deux : {len(sid_both)} SID")

# Détection de doublons texte sur le même SID, entre EXCLUDE daget-différents.
def _exclude_text(sid: int, daget: str | None) -> list[str]:
    rows = exclude.filter((pl.col("SID") == sid) & (pl.col("daget") == daget))
    lids = rows["LID"].to_list()
    return (
        libelle.filter(pl.col("LID").is_in(lids) & (pl.col("source") == "E"))["libelle"]
        .to_list()
    )


print("\nPour chacun des SID avec daget=T ET daget=U, doublons textuels :")
for sid in list(sid_both)[:10]:
    texts_T = _exclude_text(sid, "T")
    texts_U = _exclude_text(sid, "U")
    set_T = {_normalize(t) for t in texts_T}
    set_U = {_normalize(t) for t in texts_U}
    overlap = set_T & set_U
    print(f"  • {_code(sid)} (SID={sid})")
    print(f"    daget=T : {texts_T}")
    print(f"    daget=U : {texts_U}")
    print(f"    overlap (normalisé) : {len(overlap)}")

# Comparatif : EXCLUDE entre les deux côtés d'une paire DAGSTAR.
dague_exc = (
    exclude.join(
        libelle.filter(pl.col("source") == "E").select(["LID", "libelle"]),
        on="LID",
    )
    .group_by("SID")
    .agg(pl.col("libelle").alias("exc_texts"))
)

exc_pairs = (
    dagstar_u.select(["SID", "assoc"])
    .rename({"SID": "dague_sid", "assoc": "aster_sid"})
    .unique()
    .join(dague_exc.rename({"SID": "dague_sid", "exc_texts": "dague_exc"}), on="dague_sid", how="left")
    .join(dague_exc.rename({"SID": "aster_sid", "exc_texts": "aster_exc"}), on="aster_sid", how="left")
)
exc_pairs = exc_pairs.with_columns(
    pl.struct(["dague_exc", "aster_exc"])
    .map_elements(
        lambda r: len(
            ({_normalize(t) for t in (r["dague_exc"] or [])} - {""})
            & ({_normalize(t) for t in (r["aster_exc"] or [])} - {""})
        ),
        return_dtype=pl.Int64,
    )
    .alias("nb_shared_exclusions")
)

print(f"\nPaires DAGSTAR daget='U' avec EXCLUDE partagés : "
      f"{int((exc_pairs['nb_shared_exclusions'] > 0).sum())} / {len(exc_pairs)}")
print(f"  total exclusions partagées : {int(exc_pairs['nb_shared_exclusions'].sum())}")

print(
    "\n→ Résumé section 5 : EXCLUDE a son propre daget — la grande "
    "majorité reste NULL. Les très rares cas daget=T/U mériteront "
    "une analyse manuelle."
)


# %% === Section 6 : Cas A18.1 / N33.0 en détail ===
print("\n" + "=" * 78)
print("SECTION 6 — Couple canonique A18.1 (dague) / N33.0 (astérisque)")
print("=" * 78)


def _dump_code(code: str) -> None:
    sid_row = master.filter(pl.col("code") == code)
    if sid_row.is_empty():
        print(f"\n{code} : ABSENT dans MASTER")
        return
    sid = sid_row["SID"][0]
    print(f"\n{code} (SID={sid})")

    # libellé systématique
    sys_label = libelle.filter(
        (pl.col("SID") == sid) & (pl.col("source") == "S")
    )["libelle"].to_list()
    print(f"  systématique (S) : {sys_label or '(absent)'}")

    # inclusions
    inc_lids = include.filter(pl.col("SID") == sid)["LID"].to_list()
    inc_texts = (
        libelle.filter(pl.col("LID").is_in(inc_lids) & (pl.col("source") == "I"))["libelle"]
        .to_list()
    )
    print(f"  inclusions (I)   : {inc_texts or '(aucune)'}")

    # descripteurs
    descr_lids = descr.filter(pl.col("SID") == sid)["LID"].to_list()
    descr_texts = (
        libelle.filter(pl.col("LID").is_in(descr_lids) & (pl.col("source") == "D"))["libelle"]
        .to_list()
    )
    print(f"  descripteurs (D) : {descr_texts or '(aucun)'}")

    # exclusions
    excl_rows = exclude.filter(pl.col("SID") == sid)
    if excl_rows.is_empty():
        print("  exclusions (E)   : (aucune)")
    else:
        print(f"  exclusions (E)   : {len(excl_rows)} ligne(s)")
        for er in excl_rows.iter_rows(named=True):
            lib = libelle.filter(
                (pl.col("LID") == er["LID"]) & (pl.col("source") == "E")
            )
            text = lib["libelle"][0] if not lib.is_empty() else "(libellé absent)"
            redir = _code(er["excl"]) if er["excl"] else "(aucun)"
            print(
                f"    - {text!r}  redir={redir}  daget={er['daget']!r}  "
                f"plus={er['plus']!r}"
            )

    # DAGSTAR
    src_rows = dagstar.filter(pl.col("SID") == sid)
    dst_rows = dagstar.filter(pl.col("assoc") == sid)
    if not src_rows.is_empty():
        print(f"  DAGSTAR (SID=source) : {len(src_rows)} ligne(s)")
        for dr in src_rows.iter_rows(named=True):
            lib = libelle.filter(pl.col("LID") == dr["LID"])
            text = lib["libelle"][0] if not lib.is_empty() else "(absent)"
            src = lib["source"][0] if not lib.is_empty() else "?"
            print(
                f"    - daget={dr['daget']!r} plus={dr['plus']!r}  "
                f"assoc={_code(dr['assoc'])}  LID={dr['LID']} src={src!r}  "
                f"texte={text!r}"
            )
    if not dst_rows.is_empty():
        print(f"  DAGSTAR (SID=assoc) : {len(dst_rows)} ligne(s)")
        for dr in dst_rows.iter_rows(named=True):
            lib = libelle.filter(pl.col("LID") == dr["LID"])
            text = lib["libelle"][0] if not lib.is_empty() else "(absent)"
            src = lib["source"][0] if not lib.is_empty() else "?"
            print(
                f"    - daget={dr['daget']!r} plus={dr['plus']!r}  "
                f"depart={_code(dr['SID'])}  LID={dr['LID']} src={src!r}  "
                f"texte={text!r}"
            )


_dump_code("A18.1")
_dump_code("N33.0")

print(
    "\n→ Résumé section 6 : matériau brut pour rédiger l'exemple "
    "A18.1/N33.0 dans canonical_examples.md."
)


# %% === Section 7 : Synthèse pour décision ===
print("\n" + "=" * 78)
print("SECTION 7 — Synthèse")
print("=" * 78)

n_descr_total = len(descr)
n_descr_dague = len(descr_filtered_out)
n_inc_total = len(include)
n_inc_dague = len(include_filtered)
n_exc_total = len(exclude)
n_exc_with_daget = int(exclude.filter(pl.col("daget").is_not_null()).height)

print(f"""
| Table   | Critère filtrage                     | Nb lignes | Nb impactées | Doublons sémantiques (paires) |
|---------|--------------------------------------|-----------|--------------|-------------------------------|
| DESCR   | SID ∈ DAGSTAR.SID (daget ∈ S/T/U)    | {n_descr_total:>9} | {n_descr_dague:>12} | {n_dup} / {n_total} ({n_dup / max(n_total, 1) * 100:.1f} %) |
| INCLUDE | SID ∈ DAGSTAR.SID (daget ∈ S/T/U)    | {n_inc_total:>9} | {n_inc_dague:>12} | {int((inc_pairs['nb_shared_inclusions'] > 0).sum())} paires partagent ≥1 inclusion |
| EXCLUDE | EXCLUDE.daget non NULL (T/U propres) | {n_exc_total:>9} | {n_exc_with_daget:>12} | {int((exc_pairs['nb_shared_exclusions'] > 0).sum())} paires partagent ≥1 exclusion |
""")

print(
    "Commentaire factuel (à valider à la lecture des chiffres ci-dessus) :\n"
    "  - Si le taux de doublons DESCR est > ~80 %, la règle est solide\n"
    "    pour DESCR.\n"
    "  - Si le taux de partage INCLUDE est marginal, ne pas transposer\n"
    "    la règle aux inclusions.\n"
    "  - EXCLUDE : volume marginal (les daget T/U propres), à traiter\n"
    "    au cas par cas plutôt qu'avec une règle globale.\n"
)

# %%
