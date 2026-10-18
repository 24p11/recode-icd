# %% [markdown]
# # Explorer le kit ATIH (`LIBCIM10MULTI.TXT`)
#
# Notebook de consultation du fichier officiel ATIH — la source unique
# de l'autorisation de codage en MCO (`build atih` → `atih_codes.parquet`).
# Format : `CODE  |type|SMR|psy|LIBELLÉ COURT|Libellé long` (cp1252,
# 42 897 lignes, cf. `cim.pdf` du kit). Type 3 = père interdit ou
# supprimé ; codable = type ≠ 3 et non supprimé.
#
# Exécution : cellules `# %%` dans VSCode, ou
# `uv run python scripts/explore/_convert_to_ipynb.py` pour un .ipynb
# (`uv sync --extra notebook` au préalable).

# %%
from pathlib import Path

import polars as pl

from recode_icd.utils.loaders_dev import load_atih_libcim10, load_exploration_context

pl.Config.set_tbl_rows(40)
pl.Config.set_fmt_str_lengths(70)

ctx = load_exploration_context()
merged = ctx.merged.collect() if isinstance(ctx.merged, pl.LazyFrame) else ctx.merged

KIT_TXT = Path("data/CIM_ATIH_2025/LIBCIM10MULTI.TXT")
kit_brut = load_atih_libcim10(KIT_TXT)  # le TXT tel quel, une ligne par code
atih = pl.read_parquet("referentials/processed/atih_codes.parquet")  # décodé par build atih
print(f"TXT : {kit_brut.height} lignes | parquet : {atih.height} codes")
atih.head(5)


# %% [markdown]
# ## Chercher une famille de codes dans le kit
# Changer `FAMILLE` et relancer la cellule — c'est le fichier ATIH
# qu'on regarde, en forme compacte (`M142`, `Z992+0`).

# %%
FAMILLE = "M142"

atih.filter(pl.col("code_atih").str.starts_with(FAMILLE)).select(
    "code_atih", "type_mco", "statut_mco", "codable_mco", "libelle_long"
)

# %% [markdown]
# ## Le cas M14 : le kit s'arrête au 4ᵉ caractère
# Le kit porte `M14` (type 3) et `M140`…`M148` (type 0, codables) —
# AUCUN `M142x`. Les localisations à 5ᵉ caractère (`M14.20`…`M14.27`)
# viennent du maître (héritage OFS, chapitre XIII) : elles sont
# `inconnu_atih`, donc non codables en MCO.

# %%
atih.filter(pl.col("code_atih").str.starts_with("M14")).select(
    "code_atih", "type_mco", "statut_mco", "codable_mco", "libelle_court"
)

# %%
# Le même périmètre vu du MAÎTRE : les M14.2x existent, mais inconnus du kit.
merged.filter(pl.col("code").str.starts_with("M14.2")).select(
    "code", "type", "statut_mco", "codable_mco"
)

# %% [markdown]
# ## Les `inconnu_atih` en masse : qui sont-ils ?
# Codes du maître sans ligne au kit — par chapitre, puis par motif de
# forme (5ᵉ caractère du chapitre XIII en tête).

# %%
inconnus = merged.filter(pl.col("statut_mco") == "inconnu_atih")
print(f"{inconnus.height} codes du maître inconnus du kit")
inconnus.with_columns(pl.col("code").str.slice(0, 1).alias("lettre")).group_by("lettre").len().sort(
    "len", descending=True
).head(10)

# %%
# Échantillon à lire : ce sont presque tous des 5e caractères du
# chapitre XIII (M) et quelques Z37.xx — cf. chantier couverture ATIH.
inconnus.select("code", "label").head(20)

# %% [markdown]
# ## Vérification croisée avec le résolveur
# `resoudre` est le point d'entrée officiel : toute écriture → fiche ou
# raison motivée.

# %%
from recode_icd.couverture import charge_contexte, resoudre_code

ctx_res = charge_contexte()
for saisie in ("M142", "M1427", "Z992", "Z992+0", "E11"):
    r = resoudre_code(saisie, ctx_res)
    print(f"{saisie:<8} → {r.statut:<14} {r.raison[:80]}")

# %% [markdown]
# ## Répartition générale du kit

# %%
atih.group_by("type_mco", "statut_mco").len().sort("len", descending=True)
