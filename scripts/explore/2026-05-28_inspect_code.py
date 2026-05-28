# ruff: noqa
"""Notebook d'inspection multi-source d'un code CIM-10.

Format : fichier `.py` avec cellules `# %%` (jupytext percent),
exécutable cellule par cellule dans VSCode ou Jupyter Lab. Le `.ipynb`
correspondant est généré via `nbformat` (cf bas de
`scripts/explore/_convert_to_ipynb.py`).

But : pour un code CIM-10 donné, afficher côte à côte ce que livre
chaque source (OFS, ANS, ORPHANET, Index CIM-10 vol3, AP-HP), les
relations dague/astérisque, et le résultat final dans le CSV maître
à 11 colonnes.

Convention recode-icd : inspection PURE. `inspect_code` vit dans
`recode_icd.utils.loaders_dev` (dev only) — aucune logique métier,
juste du chargement et de l'affichage.
"""

# %% Init
from __future__ import annotations

from recode_icd.utils.loaders_dev import inspect_code, load_exploration_context

# Charge le contexte AVEC les sources externes brutes (nécessaire au
# BLOC 2). Coût ~5 s (parse XML ORPHANET + xlsx HECTOR). Réutilisable
# pour tous les appels inspect_code(..., ctx=ctx) ci-dessous.
ctx = load_exploration_context(with_external=True)

# %% [markdown]
# # inspect_code — mode d'emploi
#
# `inspect_code(codes, ctx=None)` affiche un rapport texte en 4 blocs
# pour un ou plusieurs codes CIM-10 :
#
# - **BLOC 1 — Identité** : libellés OFS/ANS, position hiérarchique
#   (chapitre / bloc / catégorie), type.
# - **BLOC 2 — Sources brutes** : ce que dit chaque source avant fusion
#   (OFS, ANS, ORPHANET avec relation E/NTBT, Index CIM-10 vol3, AP-HP
#   par spécialité).
# - **BLOC 3 — Dague/astérisque** : les associations de la table DAGSTAR
#   enrichie (partenaire, redundancy_level, niveaux présents).
# - **BLOC 4 — Résultat final** : les lignes du CSV maître pour ce code,
#   réparties par (type, source), avec source_level / inherited_from_code.
#
# **Résolution des codes** :
# - `"A18.1"` → le code exact (s'il existe dans le CSV).
# - `"A18"` → préfixe : tous les codes du CSV commençant par `A18`.
# - `["A18.1", "N33.0"]` → liste de codes/préfixes.
#
# `ctx=None` recharge automatiquement le contexte avec les sources
# externes. Ici on passe `ctx=ctx` pour réutiliser le contexte déjà
# chargé (plus rapide).

# %% A18.1 — code dague/astérisque riche
inspect_code("A18.1", ctx=ctx)

# %% E84.8 — code avec synonyme ORPHANET (mucoviscidose)
inspect_code("E84.8", ctx=ctx)

# %% A52.7 — code-fourre-tout avec beaucoup d'entrées Index CIM-10 vol3
inspect_code("A52.7", ctx=ctx)

# %% Liste — un couple dague/astérisque
inspect_code(["A18.1", "N33.0"], ctx=ctx)

# %% Préfixe — toute la catégorie A18
inspect_code("A18", ctx=ctx)

# %% Cellule libre — tape ton propre code ici
# inspect_code("E10.2", ctx=ctx)
