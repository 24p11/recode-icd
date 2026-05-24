# ruff: noqa
"""Exploration interactive des divergences textuelles ANS ↔ OFS.

Format : fichier `.py` avec cellules `# %%` (jupytext percent),
exécutable cellule par cellule dans VSCode ou Jupyter Lab.

Source canonique des données :
  `reports/note_merges.csv` (produit par `merge.find_note_merges`).

Convention recode-icd :
  Toute logique réutilisable doit migrer dans `src/recode_icd/`.
  Ce fichier est purement descriptif / exploratoire.
"""
# %% Test
print("hello")
1 + 1

# %% Init : chargement du contexte recode-icd
from __future__ import annotations

import random
import re
from textwrap import shorten

import polars as pl

from recode_icd.utils.loaders_dev import load_exploration_context

ctx = load_exploration_context()
note_merges = ctx.reports["note_merges"]

# Sous-ensemble d'intérêt : seulement les VRAIES divergences (texte ANS
# encore différent de OFS après normalisation complète).
divergences = note_merges.filter(pl.col("difference_significative"))

print(f"note_merges totales : {len(note_merges):,}")
print(f"  - identiques après normalisation : "
      f"{note_merges['libelles_identiques_apres_normalisation'].sum():,}")
print(f"  - vraies divergences             : {len(divergences):,}")


# %% Stats globales sur les vraies divergences
print("Par type de note :")
print(divergences.group_by("type").len().sort("len", descending=True))

print("\nNombre de codes uniques touchés :", divergences["code"].n_unique())

# Distribution simple longueur OFS vs longueur ANS
with_lens = divergences.with_columns(
    pl.col("texte_retenu").str.len_chars().alias("len_ofs"),
    pl.col("texte_alternatif_ans").str.len_chars().alias("len_ans"),
).with_columns(
    (pl.col("len_ans") - pl.col("len_ofs")).alias("delta"),
)

print("\nSens du delta (ANS - OFS) :")
print(
    with_lens.select(
        (pl.col("delta") > 0).sum().alias("ans_plus_long"),
        (pl.col("delta") < 0).sum().alias("ofs_plus_long"),
        (pl.col("delta") == 0).sum().alias("egales"),
    )
)


# %% Helper d'affichage d'une divergence donnée (code, type)
def show_divergence(code: str, note_type: str | None = None) -> None:
    """Affiche côté à côte les versions OFS et ANS d'une divergence."""
    q = divergences.filter(pl.col("code") == code)
    if note_type is not None:
        q = q.filter(pl.col("type") == note_type)

    if q.is_empty():
        print(f"Aucune divergence pour code={code!r} type={note_type!r}.")
        return

    for row in q.iter_rows(named=True):
        print(f"━━━ {row['code']} ({row['type']}) ━━━")
        print(f"  OFS ({len(row['texte_retenu'])} car):")
        print(f"    {row['texte_retenu']}")
        print(f"  ANS ({len(row['texte_alternatif_ans'])} car):")
        print(f"    {row['texte_alternatif_ans']}")
        print()


# Quelques codes témoins pour démo : adapter à ce qu'on veut creuser.
show_divergence("F02.00")
show_divergence("A02.1")
show_divergence("J45.0", "exclusion")


# %% Échantillonnage stratifié — 50 cas
SEED = 42
rng = random.Random(SEED)


def _sample(df: pl.DataFrame, n: int) -> list[dict[str, object]]:
    rows = df.to_dicts()
    rng.shuffle(rows)
    return rows[:n]


def _pretty_print_sample(label: str, rows: list[dict[str, object]]) -> None:
    print(f"\n━━━ {label} ({len(rows)} cas) ━━━")
    for r in rows:
        ofs = str(r["texte_retenu"])
        ans = str(r["texte_alternatif_ans"])
        print(f"  {r['code']} ({r['type']}) — OFS={len(ofs)} / ANS={len(ans)}")
        print(f"    OFS : {shorten(ofs, width=120, placeholder='…')}")
        print(f"    ANS : {shorten(ans, width=120, placeholder='…')}")


# Stratifications
_lens = with_lens

samples_ans_plus_long = _sample(
    _lens.filter(pl.col("delta") > 5),
    10,
)
samples_ofs_plus_long = _sample(
    _lens.filter(pl.col("delta") < -5),
    10,
)
samples_similar = _sample(
    _lens.filter(pl.col("delta").abs() <= 5),
    10,
)

# Chapitres cliniques très annotés : I/J (cardio-respiratoire) et S/T (lésions) et C/D (tumeurs)
samples_clinical = _sample(
    _lens.filter(
        pl.col("code").str.starts_with("C")
        | pl.col("code").str.starts_with("I")
        | pl.col("code").str.starts_with("S")
    ),
    10,
)

samples_random = _sample(_lens, 10)

_pretty_print_sample("ANS strictement plus long", samples_ans_plus_long)
_pretty_print_sample("OFS strictement plus long", samples_ofs_plus_long)
_pretty_print_sample("Longueurs similaires (|Δ| ≤ 5)", samples_similar)
_pretty_print_sample("Chapitres cliniques (C/I/S)", samples_clinical)
_pretty_print_sample("Random (contrôle)", samples_random)


# %% Détection de patterns automatiques
CODE_REF_RE = re.compile(r"\[[A-Z]\d{2}(?:\.\d+)?\]")

with_patterns = divergences.with_columns(
    pl.col("texte_retenu").map_elements(
        lambda t: bool(CODE_REF_RE.search(t or "")),
        return_dtype=pl.Boolean,
    ).alias("ofs_has_code_ref"),
    pl.col("texte_alternatif_ans").map_elements(
        lambda t: bool(CODE_REF_RE.search(t or "")),
        return_dtype=pl.Boolean,
    ).alias("ans_has_code_ref"),
    pl.struct(["texte_retenu", "texte_alternatif_ans"]).map_elements(
        lambda s: (
            (s["texte_retenu"] or "") in (s["texte_alternatif_ans"] or "")
            and len(s["texte_retenu"] or "") < len(s["texte_alternatif_ans"] or "")
            and len(s["texte_retenu"] or "") > 0
        ),
        return_dtype=pl.Boolean,
    ).alias("ofs_substring_of_ans"),
    pl.struct(["texte_retenu", "texte_alternatif_ans"]).map_elements(
        lambda s: (
            (s["texte_alternatif_ans"] or "") in (s["texte_retenu"] or "")
            and len(s["texte_alternatif_ans"] or "") < len(s["texte_retenu"] or "")
            and len(s["texte_alternatif_ans"] or "") > 0
        ),
        return_dtype=pl.Boolean,
    ).alias("ans_substring_of_ofs"),
)

print("\n=== Patterns détectés ===")
print(
    with_patterns.select(
        pl.col("ofs_has_code_ref").sum().alias("ofs_avec_code_ref"),
        pl.col("ans_has_code_ref").sum().alias("ans_avec_code_ref"),
        pl.col("ofs_substring_of_ans").sum().alias("ofs_substring_ans"),
        pl.col("ans_substring_of_ofs").sum().alias("ans_substring_ofs"),
    )
)


# %% Creuser les cas avec OFS strictement plus long (rares mais intéressants)
# Hypothèse : OFS conserve parfois un qualificatif clinique perdu côté ANS.
ofs_longer_full = _lens.filter(pl.col("delta") < -5).sort("delta")
print(f"\n{len(ofs_longer_full)} cas où OFS > ANS de plus de 5 caractères :\n")
for r in ofs_longer_full.head(10).iter_rows(named=True):
    print(f"  {r['code']} ({r['type']})")
    print(f"    OFS : {r['texte_retenu']}")
    print(f"    ANS : {r['texte_alternatif_ans']}")
    print()


# %% (vide) — creuser un chapitre / un code particulier


# %% (vide) — comparer un sous-ensemble de note_merges avec ctx.merged ou ctx.flat


# %% (vide) — exporter une sélection en CSV pour partage manuel
