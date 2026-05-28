# ruff: noqa
"""Walkthrough pédagogique du pipeline complet recode-icd.

Format : fichier `.py` avec cellules `# %%` (jupytext percent),
exécutable cellule par cellule dans VSCode ou Jupyter Lab. Le `.ipynb`
correspondant est généré via nbformat (cf bas de
`scripts/explore/_convert_to_ipynb.py`).

Fil rouge : on suit le code A18.1 (Tuberculose de l'appareil
génito-urinaire) à travers TOUTES les étapes du pipeline, des sources
brutes jusqu'au CSV maître à 11 colonnes.

Convention recode-icd : ce notebook ne réécrit AUCUNE logique métier.
Toutes les données viennent des Parquets/CSV déjà produits par le
pipeline et chargés via `load_exploration_context`. Les transformations
vivent dans `src/recode_icd/`.

Pour exécuter avec sorties : ce `.py` se lance cellule par cellule, ou
le `.ipynb` généré peut être exécuté via
`uv run --with jupyter --with fastexcel jupyter nbconvert --to notebook
--execute --inplace scripts/explore/01_walkthrough_pipeline.ipynb`.
"""

# %% [markdown]
# # Walkthrough du pipeline `recode-icd`
#
# Ce notebook explique pas à pas le pipeline qui produit le fichier
# maître `inclusions_exclusions_synonymes.csv` (11 colonnes) à partir
# des sources CIM-10, en vue d'enrichir des prompts LLM.
#
# ## Schéma global
#
# ```
#   SOURCES BRUTES                TRANSFORMATIONS               LIVRABLES
#   ──────────────                ───────────────               ─────────
#   OFS suisse 2006   ─┐
#   (relationnel,      │   merge.py (OFS ⊕ ANS)
#    latin-1)          ├─► propagation.py (héritage) ─┐
#   ANS FR 2025       ─┘   sibling_exclusions.py (.8) ─┤
#   (RDF/OWL)              dagger_asterisk.py (†/*)    ├─► flat_csv.py ─► inclusions_
#                          merge_external.py (externes)─┘   (11 colonnes)   exclusions_
#   ORPHANET ─┐                                                             synonymes.csv
#   Index vol3├─► loaders/external/                              + dagger_asterisk.parquet
#   AP-HP    ─┘                                                  + reports/*.csv
# ```
#
# ## Étapes et modules responsables
#
# | Étape | Module | Livrable |
# |-------|--------|----------|
# | Chargement OFS / ANS | `loaders/ofs.py`, `loaders/owl.py` | `ofs_codes.parquet`, `owl_codes.parquet` |
# | Fusion OFS ⊕ ANS | `merge.py` | `merged_codes.parquet` |
# | Propagation hiérarchique | `propagation.py` | `propagated_notes.parquet` |
# | Exclusions de frères .8 | `relations/sibling_exclusions.py` | `sibling_exclusions.parquet` |
# | Couples dague/astérisque | `relations/dagger_asterisk.py` | `dagger_asterisk.parquet` |
# | Sources externes | `merge_external.py` + `loaders/external/` | `external_to_add.parquet` |
# | CSV maître | `exporters/flat_csv.py` | `inclusions_exclusions_synonymes.csv` |
#
# ## Fil rouge
#
# Tout au long de ce notebook, nous suivrons le code **A18.1
# (Tuberculose de l'appareil génito-urinaire)** pour voir comment il est
# traité à chaque étape. C'est un excellent témoin : il a des
# descripteurs OFS, des notes ANS, des associations dague/astérisque, et
# il est référencé par les trois sources externes.

# %% Init — chargement du contexte
from __future__ import annotations

import polars as pl

from recode_icd.utils.loaders_dev import inspect_code, load_exploration_context

pl.Config.set_fmt_str_lengths(70)
pl.Config.set_tbl_rows(20)

# with_external=True charge aussi les sources externes brutes (ORPHANET,
# Index CIM-10 vol3, AP-HP) — nécessaire à la section 6. Coût ~5 s.
ctx = load_exploration_context(with_external=True)

FIL_ROUGE = "A18.1"


def cell(df: pl.DataFrame, col: str):
    """Valeur de `col` sur la 1re ligne de `df` (liste ou scalaire),
    ou [] / '' si df est vide. Helper d'affichage — pas de logique
    métier."""
    if df.is_empty():
        return []
    return df[col].to_list()[0]

# Identité de base depuis merged_codes.
ident = ctx.merged.filter(pl.col("code") == FIL_ROUGE).select(
    "code", "label", "type", "path"
)
print(ident.to_dicts()[0])

# %% [markdown]
# ## Section 1 — Les loaders (OFS + ANS)
#
# Le pipeline part de **deux formats sources radicalement différents** :
#
# - **OFS** (Office Fédéral de la Statistique suisse, 2006) : une base
#   **relationnelle plate** (fichiers `.txt`, séparateur `¦`, encodage
#   latin-1). Figée en 2006 mais **structurée** : des tables séparées
#   `INCLUDE`, `EXCLUDE`, `DESCR`, `INDIR` portent la sémantique fine
#   (on sait si une note est une inclusion, un descripteur, etc.).
# - **ANS** (Agence du Numérique en Santé, FR 2025) : RDF/OWL enrichi
#   (~19 000 concepts). À jour (codes COVID, refontes ATIH) mais
#   **aplatit** parfois inclusions et synonymes dans une même propriété.
#
# `loaders/owl.py` **surcharge localement `smt2parquet`** : il réutilise
# la mécanique générique (parsing rdflib, nested set) et redéfinit les
# requêtes SPARQL pour récupérer les prédicats non extraits en amont.
#
# **Pourquoi deux sources** : OFS apporte la structure et l'atomicité
# (cf `docs/source_mapping.md`), ANS apporte l'actualité. La fusion
# combine le meilleur des deux.

# %% Section 1 — ce que chaque source dit de A18.1
ofs_row = ctx.ofs_codes.filter(
    pl.col("code").str.strip_chars("()") == FIL_ROUGE
)
print("[OFS] descripteurs (table DESCR) :")
for d in (cell(ofs_row, "synonymes") or []):
    print(f"   - {d}")

ans_row = ctx.ans.filter(pl.col("code") == FIL_ROUGE)
print("\n[ANS] synonymes (skos:altLabel) :")
for s in (cell(ans_row, "synonymes") or []):
    print(f"   - {s}")
print("\n[ANS] inclusion_note (bloc textuel, non atomisé) :")
print("  ", (cell(ans_row, "inclusion_note") or "")[:200])

# %% [markdown]
# **Observation** : OFS livre 6 descripteurs **atomiques** (un par
# affection : uretère, vessie, col de l'utérus...). ANS livre les mêmes
# informations mais sous forme d'un **bloc textuel** dans
# `inclusion_note` (avec puces et codes entre crochets) + des synonymes
# dédupliqués. C'est exactement la différence structurelle que la fusion
# doit réconcilier.

# %% [markdown]
# ## Section 2 — Le merge OFS ⊕ ANS
#
# `merge.py` applique une **politique par champ** (cf
# `docs/source_mapping.md` §"Politique de fusion") :
#
# | Champ | Source primaire | Fallback |
# |-------|-----------------|----------|
# | Libellé du code | ANS (à jour) | OFS |
# | Existence du code | ANS | — |
# | Inclusions / exclusions typées | OFS (atomique) | ANS |
# | Synonymes | OFS | ANS (union) |
# | Associations †/* | OFS + audit ANS | ANS |
#
# **Codes post-2006** : un code présent en ANS mais absent d'OFS (ex
# U07.1 COVID) est créé avec `source=ANS`. À l'inverse, un code OFS
# retiré par l'ATIH (ex A90 Dengue) n'entre pas dans `merged_codes`
# (politique « ANS prime pour l'existence »).

# %% Section 2 — A18.1 après fusion
merged_row = ctx.merged.filter(pl.col("code") == FIL_ROUGE)
print(merged_row.select(
    "code", "label", "type", "has_ofs_match",
    "inclusions_source", "exclusions_source",
).to_dicts()[0])
print("\nSynonymes fusionnés (union OFS ∪ ANS, dédup tolérante) :")
for s in (cell(merged_row, "synonymes") or []):
    print(f"   - {s}")

# %% [markdown]
# **Observation** : `has_ofs_match=True` (A18.1 existe dans les deux
# sources). Le libellé retenu vient d'ANS ; les inclusions/exclusions
# d'OFS quand il en a. Les synonymes sont l'union dédupliquée des deux
# sources.

# %% [markdown]
# ## Section 3 — La propagation hiérarchique
#
# La CIM-10 est hiérarchique : **chapitre → bloc → catégorie → code**.
# Les notes attachées à un ancêtre s'appliquent à TOUS ses descendants.
# Une exclusion au bloc A15-A19 (Tuberculose) concerne donc A18.1.
#
# `propagation.py` **propage** ces notes vers les codes feuilles, en
# traçant l'origine via `inherited_from` (code parent) et
# `inherited_from_type` (chapter/block/category). Sans cette propagation,
# le LLM consommateur ne verrait pas, au niveau du code feuille, les
# notes pertinentes définies plus haut.
#
# Dans le CSV final, cette traçabilité devient les colonnes
# **`source_level`** et **`inherited_from_code`** (chantier A).

# %% Section 3 — notes de A18.1 héritées d'un niveau supérieur
prop = ctx.propagated.filter(
    (pl.col("code") == FIL_ROUGE) & pl.col("inherited_from").is_not_null()
)
print("Notes de A18.1 PROPAGÉES depuis un ancêtre :")
print(prop.select("note_type", "inherited_from", "inherited_from_type", "texte").head(6))

# Ampleur du phénomène sur tout le CSV final.
print("\nDistribution source_level sur le CSV final :")
dist = ctx.flat.group_by("source_level").len().sort("len", descending=True)
total = ctx.flat.height
for r in dist.iter_rows(named=True):
    print(f"   {r['source_level']:9s} : {r['len']:7d}  ({100*r['len']/total:.1f} %)")

# %% [markdown]
# **Observation** : A18.1 hérite de notes du bloc **A15-A19** et du
# chapitre **I**. À l'échelle du CSV, ~49 % des lignes sont propagées
# (block 21 % + category 20 % + chapter 7,5 %) — la propagation n'est
# pas un détail, c'est la moitié du contenu.

# %% [markdown]
# ## Section 4 — Les exclusions de frères (.8)
#
# Pour les codes `XYZ.8` ("Autres ..."), le pipeline **synthétise** des
# notes d'exclusion qui listent les frères `XYZ.0`–`XYZ.7`. Objectif :
# aider le LLM à comprendre que `.8` couvre les affections
# **résiduelles** — celles qui n'ont pas leur propre sous-catégorie.
#
# Ces notes ont `source = SYNTHESIZED_SIBLING` (libellé CSV :
# **« CIM-10 frères »**). Cas particulier : pour C00-C75 (tumeurs
# malignes), `.8` a une sémantique différente ("lésion à localisations
# contiguës") → pas de synthèse.
#
# On illustre avec **A18.8**, le frère `.8` de notre catégorie A18.

# %% Section 4 — exclusions synthétisées de A18.8
freres = (
    ctx.flat.filter(
        (pl.col("code") == "A18.8") & (pl.col("source") == "CIM-10 frères")
    )
    .select("texte")
    .unique()
    .sort("texte")
)
print(f"A18.8 — {freres.height} frères synthétisés (.0 à .7) :")
for t in freres.to_series().to_list():
    print(f"   - {t}")

# %% [markdown]
# **Observation** : A18.8 ("Tuberculose d'autres organes") exclut
# explicitement ses frères A18.0 (os/articulations), A18.1
# (génito-urinaire, notre fil rouge), A18.2 (adénopathie)... Le LLM sait
# ainsi que ces affections-là ont leur propre code.

# %% [markdown]
# ## Section 5 — Les couples dague/astérisque
#
# La CIM-10 utilise la convention **dague (†) / astérisque (*)** pour les
# diagnostics à double codage : le code **dague** porte l'étiologie
# (maladie initiale), le code **astérisque** la manifestation localisée.
# Ex : A18.1† (tuberculose, étiologie) / N33.0* (cystite tuberculeuse).
#
# La table DAGSTAR de l'OFS distingue **6 niveaux** d'association
# (`daget` ∈ F/G/H/S/T/U). Une curation manuelle marque certaines paires
# `redundancy_level=subordinate` (le code dague se "résume" dans la
# combinaison) ; le flag `is_redundant_dagger` permet de filtrer le code
# dague à l'usage, **sans le supprimer** (réversibilité).

# %% Section 5 — les associations dague/astérisque de A18.1
dag = ctx.dagger_asterisk.filter(
    (pl.col("dagger_code") == FIL_ROUGE) | (pl.col("asterisk_code") == FIL_ROUGE)
)
print(f"A18.1 — {dag.height} associations dague/astérisque :")
print(dag.select(
    "dagger_code", "asterisk_code", "asterisk_label",
    "redundancy_level", "levels_present",
))

# %% [markdown]
# **Observation** : A18.1 est le **dague** (étiologie) de ~10
# associations. La plupart sont `subordinate` (ex N33.0 cystite
# tuberculeuse — la tuberculose se résume dans la manifestation), mais
# N74.1 (affection pelvienne tuberculeuse) est `independent`. La curation
# manuelle (`referentials/curation/dagger_curation.csv`) tranche ces cas.

# %% [markdown]
# ## Section 6 — Les sources externes
#
# Trois familles enrichissent le CSV en synonymes/inclusions :
#
# - **ORPHANET** (maladies rares) : relation `E` (exact) → synonyme,
#   relation `NTBT` (ORPHA plus spécifique) → inclusion.
# - **Index CIM-10 vol3** (index alphabétique officiel) : richesse
#   lexicale historique → synonymes.
# - **AP-HP HECTOR** (9 thésaurus métiers) : synonymes spécialisés.
#
# Chaque entrée externe subit une **dédup tolérante** contre OFS/ANS : si
# le libellé existe déjà pour ce code, elle est **absorbée** (loggée dans
# `reports/external_overlaps.csv`) ; sinon ajoutée avec sa source propre.
#
# A18.1 illustre à lui seul les trois sources.

# %% Section 6 — A18.1 dans les trois sources externes (brutes)
for source_label in ("ORPHANET", "INDEX_CIM10_VOL3", "APHP_NEPHROLOGIE"):
    df = ctx.external.get(source_label)
    if df is None:
        continue
    sub = df.filter(pl.col("code") == FIL_ROUGE)
    print(f"[{source_label}] {sub.height} entrée(s) brute(s) :")
    for r in sub.head(3).iter_rows(named=True):
        rel = ""
        if source_label == "ORPHANET" and r.get("metadata"):
            rel = f" (relation {r['metadata'].get('relation', '?')})"
        print(f"   - {r['libelle']}  [{r['type']}]{rel}")
    if sub.height > 3:
        print(f"   … (+{sub.height - 3} de plus)")
    print()

# %% [markdown]
# **Observation** : ORPHANET donne 2 synonymes (relation E :
# "Tuberculose génito-urinaire primaire"), l'Index CIM-10 vol3 en donne
# ~91 (déclinaisons historiques de la tuberculose urogénitale), et AP-HP
# Néphrologie 1 (avec une note de codage métier). C'est la richesse
# lexicale qui aide le LLM à reconnaître toutes les formulations.

# %% [markdown]
# ## Section 7 — Le CSV final + point d'orgue
#
# Le livrable principal `inclusions_exclusions_synonymes.csv` a
# **11 colonnes** :
#
# | # | Colonne | Rôle |
# |---|---------|------|
# | 1-5 | `code`, `libelle`, `type`, `source`, `texte` | la note et son origine |
# | 6-7 | `dagger_code`, `asterisk_code` | association †/* (si applicable) |
# | 8-9 | `redundancy_level`, `is_redundant_dagger` | curation dague/astérisque |
# | 10-11 | `source_level`, `inherited_from_code` | traçabilité de la propagation |
#
# **Régénérer le pipeline complet** :
#
# ```bash
# uv run recode-icd build owl --rdf-path <...>.rdf
# uv run recode-icd build ofs --ofs-dir data/CIM_OFS_SW_2006
# uv run recode-icd build merged
# uv run recode-icd build propagated
# uv run recode-icd build siblings
# uv run recode-icd build dagger-asterisk --ofs-dir data/CIM_OFS_SW_2006
# uv run recode-icd build external
# uv run recode-icd build flat-csv
# ```

# %% Section 7 — POINT D'ORGUE : la synthèse complète via inspect_code
# Tout ce que nous avons vu étape par étape, l'outil inspect_code() le
# rassemble en une seule vue. C'est l'outil à utiliser au quotidien pour
# inspecter n'importe quel code.
inspect_code(FIL_ROUGE, ctx=ctx)

# %% [markdown]
# ## Récapitulatif
#
# Le chemin parcouru par A18.1 :
#
# | Étape | Module | Ce qui arrive à A18.1 |
# |-------|--------|------------------------|
# | 1. Loaders | `loaders/ofs.py` + `owl.py` | 6 descripteurs OFS, synonymes + bloc ANS |
# | 2. Merge | `merge.py` | libellé ANS, synonymes unifiés, `has_ofs_match=True` |
# | 3. Propagation | `propagation.py` | hérite des notes du bloc A15-A19 et du chapitre I |
# | 4. Frères .8 | `sibling_exclusions.py` | (A18.8, son frère, l'exclut explicitement) |
# | 5. Dague/astérisque | `relations/dagger_asterisk.py` | 10 associations (N33.0 subordinate, ...) |
# | 6. Sources externes | `merge_external.py` | +ORPHANET (2), +Index (91), +AP-HP (1) |
# | 7. CSV final | `exporters/flat_csv.py` | 954 lignes, 11 colonnes |
#
# **Pour aller plus loin** :
#
# - `docs/source_mapping.md` — toutes les politiques (fusion,
#   propagation, dague/astérisque, sources externes) : la référence.
# - `CLAUDE.md` — vue d'ensemble, objectifs métier, domain pitfalls.
# - `docs/sessions/` — récaps de chaque chantier (diagnostics, audits).
#
# **Outil quotidien** : `inspect_code("<code>")` (dans
# `recode_icd.utils.loaders_dev`) rassemble en une vue tout ce que ce
# notebook a parcouru, pour n'importe quel code CIM-10.
