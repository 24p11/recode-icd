"""Rendu des consignes du guide MCO dans les fiches — démonstration

Notebook d'exploration **interactif**. Démonstration du rendu de la
section « Consignes de codage » des fiches, à partir des deux tables du
chantier A (`recommendations.parquet` / `recommendation_codes.parquet`).
Six codes de démonstration l'exercent, chacun choisi pour un cas précis.

Document de référence figé :
`docs/analyses/2026-08-09_conception_base_recommandations_guide_methodo.md`
(§4.2 catalogue des rôles, §4.3 résolution, §6 esquisse d'usage). Le
`.md` fait foi pour le modèle.

**L'implémentation vit dans `src/`** —
`recode_icd.recommendations.rendu` (sélection et forme de la section),
branchée dans les fiches par `cards._section_consignes` (chantier du
2026-09-03). Ce notebook l'importe et la démontre : le prototype local
a été supprimé le jour où le chantier a atterri, comme l'annonçait son
avertissement — deux implémentations coexistantes divergeraient en
silence. **C'est `src/` qui fait foi.** Les cellules pédagogiques et
les six démonstrations verrouillées restent, à l'identique.

Le CSV maître n'est jamais modifié : les consignes vivent dans leur
livrable séparé, c'est l'invariant du chantier.

Régénération du notebook :
    uv run --extra notebook python scripts/explore/_convert_to_ipynb.py \\
        scripts/explore/rendu_recommandations_fiches.py
"""

# ruff: noqa: E402

# %% [markdown]
# ## Mode d'emploi
#
# Le `.py` est la **source de vérité** : diffable, lintable, exécutable
# directement (`uv run python scripts/explore/rendu_recommandations_fiches.py`).
# Le `.ipynb` en est un rendu régénéré — ne pas l'éditer à la main.
#
# Les règles de rendu démontrées ici (implémentées dans
# `recode_icd/recommendations/rendu.py`) :
#
# 1. **Filtre `centralite = sujet`** par défaut. Les codes cités en
#    illustration (`exemple`) n'entrent pas dans la fiche — c'est la
#    raison d'être du champ (la fiche de F32 ne doit pas recevoir la
#    consigne AVC au motif que F32 y illustre une manifestation).
# 2. **Exclusion du rôle `contexte`** — cf. ⚠ Piège ci-dessous.
# 3. **Tri par spécificité décroissante** : `CODE > CATEGORIE > PLAGE >
#    CHAPITRE`, dérivée de l'**expression parsée** de la table curée,
#    jamais du référentiel (`merged.type` ne distingue pas `Z86.70` de
#    `I69`). Le tri réutilise `cle_de_tri` de la résolution de
#    production — pas de réimplémentation locale qui pourrait diverger.
# 4. **Les consignes de niveau chapitre sont regroupées en fin de
#    section** sous « Règles générales du chapitre ». C'est la maîtrise
#    du bruit actée à la question ouverte n°1 de la note de conception :
#    la résolution descend tout jusqu'aux feuilles, le rendu regroupe.
#    Chacune est précédée de sa **`situation` entre parenthèses** —
#    c'est elle qui borne la portée et transforme une règle apparemment
#    hors sujet en information de non-application (cas Z23.0).
# 5. **Chaque consigne est préfixée de son `rec_id` entre crochets** —
#    traçabilité vers le guide, principe « jamais d'agrégation
#    silencieuse ».
# 6. **Les `centralite = exemple` sont rendus en bloc cité `>`**,
#    introduits par « À titre d'exemple dans le guide : », après les
#    consignes sujet et avant les règles générales — signal structurel
#    « ceci illustre, ceci ne norme pas ». À la déduplication, `sujet`
#    prime sur `exemple` (Z20.1 : GM2026-V-XXI-16 l'atteint en exemple
#    au code ET en sujet via Z20 → une seule ligne, dans la liste
#    principale). Aucun des six codes de démonstration ne porte
#    d'exemple : ce chemin est verrouillé par les tests de régression
#    (`tests/regression/test_cards_consignes.py`, témoins Z20.1 et
#    F01.000).
#
# Une règle de plus est appliquée **en amont, par construction** : une
# association de portée `ensemble` (l'expression est le domaine d'un
# choix, ex. AVC-14 « le DP appartient au chapitre XXI ») n'est jamais
# résolue — elle n'existe pas dans le Parquet, donc aucun rendu ne peut
# la faire fuir sur les fiches des membres. Cf. note de conception §4.2
# (amendement du 2026-09-02) ; la trace vit au rapport de build
# `guide_mco_associations_ensemble.csv`.

# %% [markdown]
# ### ⚠ Piège — `contexte` n'est pas « une consigne qui parle du code »
#
# Un rendu qui veut « les consignes qui parlent de ce code » filtre sur
# `regi` et les positions (`DP`, `DR`, `DAS`, `interdit*`), **jamais**
# sur `contexte` : ce rôle dit que le code délimite la situation, pas
# que la consigne régit son emploi. L'inclure ferait recevoir à la
# fiche de I63 toutes les consignes qui mentionnent l'infarctus sans
# rien prescrire à son sujet. La démonstration I64 ci-dessous exerce ce
# filtre : GM2026-V-AVC-03 et GM2026-V-AVC-08 (où I60-I64 n'est que le
# contexte) ne doivent pas apparaître.

# %% Chargement du contexte d'exploration
from recode_icd.utils.loaders_dev import load_exploration_context

ctx = load_exploration_context()

import polars as pl

from recode_icd.recommendations import rendu

pl.Config.set_tbl_rows(25)
pl.Config.set_fmt_str_lengths(90)

recs = ctx.recommendations if isinstance(ctx.recommendations, pl.DataFrame) else None
rec_codes = ctx.recommendation_codes if isinstance(ctx.recommendation_codes, pl.DataFrame) else None
merged = ctx.merged if isinstance(ctx.merged, pl.DataFrame) else ctx.merged.collect()
assert recs is not None and rec_codes is not None, (
    "Tables du guide MCO absentes — lancer `uv run recode-icd build guide-mco`."
)

# %% [markdown]
# ## 1. Volumétrie de la base versée
#
# État après l'amendement `portee` (2026-09-02) : **94 consignes**,
# **187 associations curées** dont **1 de portée `ensemble`** jamais
# résolue (AVC-14/XXI, au rapport de build), soit **186 associations
# résolues** en **2 056 couples (consigne, code feuille)** sur **1 018
# codes**. Les associations résolues se recomptent depuis le Parquet
# par `(rec_id, code_expr, role)` — la résolution ne fait qu'étendre
# chaque expression à ses feuilles, elle n'en crée ni n'en perd.

# %% Volumétrie
volumetrie = {
    "consignes": recs.height,
    "associations résolues": rec_codes.unique(["rec_id", "code_expr", "role"]).height,
    "couples (consigne, code feuille)": rec_codes.height,
    "codes feuilles distincts": rec_codes["code"].n_unique(),
}
for etiquette, valeur in volumetrie.items():
    print(f"{etiquette:32s}: {valeur}")

assert volumetrie["consignes"] == 94
assert volumetrie["associations résolues"] == 186
assert volumetrie["couples (consigne, code feuille)"] == 2056
assert volumetrie["codes feuilles distincts"] == 1018

# L'association `ensemble` n'est pas dans le Parquet — c'est le rapport
# de build qui l'atteste, avec la taille du domaine non produit.
ensemble = ctx.reports.get("guide_mco_associations_ensemble")
assert isinstance(ensemble, pl.DataFrame) and ensemble.height == 1
print()
print(ensemble.select("rec_id", "code_expr", "role", "n_codes_domaine"))

print()
print(rec_codes.group_by("type_expr", "specificite").len().sort("specificite", descending=True))

# %% [markdown]
# ## 2. Sélection des consignes d'une fiche
#
# `rendu.consignes_pour` (production) matérialise les règles 1 à 3 et
# la dédup de la règle 6. Deux subtilités :
#
# - **une consigne peut atteindre le même code par plusieurs
#   expressions** (30 couples mesurés : GM2026-V-XXI-38 atteint Z51.31
#   par la catégorie `Z51` ET par le code `Z51.31`, par exemple). Elle
#   ne doit se rendre qu'une fois, au niveau le plus spécifique — d'où
#   la déduplication par `rec_id` après tri sur `specificite` ;
# - **le filtre des rôles s'applique avant la déduplication** : si une
#   consigne cite le code en `contexte` ET le couvre par ailleurs au
#   niveau chapitre en `regi`, c'est l'association chapitre qui reste.
#
# Les wrappers ci-dessous lient les deux tables du contexte — la
# signature des démonstrations reste celle du prototype historique.

# %% Fonctions de sélection


def consignes_pour(code: str, **selection) -> list[dict]:
    """Consignes à rendre sur la fiche de `code` — délègue à `src/`."""
    return rendu.consignes_pour(rec_codes, recs, code, **selection)


def libelle_de(code: str) -> str:
    ligne = merged.filter(pl.col("code") == code)
    return (ligne["label"][0] or "") if ligne.height else "(libellé inconnu)"


# %% [markdown]
# ## 3. Rendu de la section
#
# `rendu.rendre_section_consignes` (production) matérialise les règles
# 4 à 6 : liste principale par spécificité décroissante, bloc cité des
# exemples, puis « Règles générales du chapitre » avec leur situation.
# Le millésime du titre vient de la table, pas d'une constante — le
# jour où la base porte le guide définitif, le titre suit. C'est la
# même fonction que `cards._section_consignes` appelle au build des
# fiches.

# %% Fonction de rendu


def rendre_section(code: str) -> str:
    """Section « Consignes de codage » de la fiche de `code` — délègue à `src/`."""
    return rendu.rendre_section_consignes(rec_codes, recs, code) or ""


def demo(code: str) -> None:
    print(f"════ Fiche {code} — {libelle_de(code)}")
    print()
    section = rendre_section(code)
    print(section if section else "(aucune consigne)")


# %% [markdown]
# ## 4. Six démonstrations
#
# Chaque code est choisi pour exercer un cas précis. Les assertions en
# fin de cellule verrouillent le comportement démontré — une
# démonstration qui n'exerce pas ce qu'elle annonce ne prouve rien.

# %% [markdown]
# ### 4.1 I64 — le filtre `contexte` à l'œuvre
#
# I64 (AVC non précisé) est cité par 7 consignes de l'article AVC, dont
# 2 où I60-I64 n'est que le **contexte** d'une interdiction visant
# d'autres codes (GM2026-V-AVC-03 et GM2026-V-AVC-08). Elles ne doivent
# pas apparaître : la fiche montre les 5 consignes qui régissent ou
# positionnent I64 — condition d'emploi (pas de neuro-imagerie),
# récidive, DR des soins palliatifs, interdiction d'association et DP.

# %% Démonstration I64
demo("I64")

rendus = {r["rec_id"] for r in consignes_pour("I64")}
assert "GM2026-V-AVC-03" not in rendus, "contexte rendu — piège n°3 violé"
assert "GM2026-V-AVC-08" not in rendus, "contexte rendu — piège n°3 violé"
assert "GM2026-V-AVC-02" in rendus

# %% [markdown]
# ### 4.2 Z86.70 — du code précis aux règles générales
#
# Z86.70 (antécédents d'AVC) est le cas d'école de la note de
# conception. Sa fiche étage les trois niveaux : consignes au **code**
# (DP de la surveillance négative, condition d'emploi), une consigne de
# **plage** (interdit_DR : un antécédent ne justifie jamais de DR),
# puis les règles générales du chapitre XXI en fin de section.

# %% Démonstration Z86.70
demo("Z86.70")

specificites = [r["specificite"] for r in consignes_pour("Z86.70")]
assert specificites == sorted(specificites, reverse=True), "tri par spécificité violé"

# %% [markdown]
# ### 4.3 D62 — l'article historique
#
# D62 (anémie posthémorragique aigüe) est le cas d'école du bénéfice
# attendu pour la génération (§5.2 de la note) : la fiche apprend au
# générateur qu'une transfusion peropératoire banale ne justifie pas de
# décrire une anémie posthémorragique — la mention codable parasite
# type qui corrompt un corpus annoté.

# %% Démonstration D62
demo("D62")

# %% [markdown]
# ### 4.4 Z51.5 — un code au carrefour de deux articles
#
# Z51.5 (soins palliatifs) est régi à la fois par l'article AVC (DP
# avec l'AVC en DR) et par l'article du chapitre XXI (DP, motif de
# séjour, interdit_DAS en sus d'un acte CCAM). Les consignes des deux
# articles se côtoient dans la même fiche, triées par spécificité —
# c'est la définition unique en base qui rend ce croisement possible
# sans duplication.

# %% Démonstration Z51.5
demo("Z51.5")

# %% [markdown]
# ### 4.5 E43 — les définitions de seuils de la dénutrition
#
# E43 (malnutrition protéino-énergétique grave, sans précision) reçoit
# les consignes de sévérité de l'article dénutrition, dont les
# `definition` à seuils chiffrés (IMC, perte de poids, albuminémie…)
# par classe d'âge. C'est le type de consigne qui borne ce que le
# générateur a le droit d'écrire : une « dénutrition sévère » sans
# critère phénotypique n'est pas codable E43.

# %% Démonstration E43
demo("E43")

types_rendus = {r["type"] for r in consignes_pour("E43")}
assert "definition" in types_rendus, "les définitions de seuils manquent"

# %% [markdown]
# ### 4.6 Z23.0 — un code que le guide ne cite pas
#
# Z23.0 (vaccination antivariolique isolée) n'est cité par **aucune**
# consigne : tout ce qu'il reçoit descend du chapitre XXI. Sa fiche ne
# doit donc contenir QUE les « Règles générales du chapitre » — liste
# principale vide. C'est le double test de la question ouverte n°1 :
# **complétude** (la résolution descend bien les consignes de chapitre
# jusqu'aux feuilles non citées) et **maîtrise du bruit** (elles restent
# cantonnées au groupe de fin de section).
#
# Ce cas est aussi le témoin de l'amendement `portee` (2026-09-02) :
# GM2026-V-AVC-14 (« s'il n'est pas découvert d'affection nouvelle, le
# DP appartient au chapitre XXI ») descendait ici alors que le chapitre
# XXI n'y est que le **domaine d'un choix** fait par le motif de séjour.
# Son association XXI est désormais déclarée `ensemble` à la curation :
# jamais résolue, elle n'existe pas dans le Parquet — la garantie est
# par construction, aucun rendu ne peut la faire fuir. Z23.0 ne reçoit
# plus que XXI-01, la vraie règle « pour tout » du chapitre.

# %% Démonstration Z23.0
demo("Z23.0")

lignes_z230 = consignes_pour("Z23.0")
assert lignes_z230, "complétude violée — les consignes de chapitre ne descendent pas"
assert {r["rec_id"] for r in lignes_z230} == {"GM2026-V-XXI-01"}, (
    "maîtrise du bruit violée — soit une consigne non chapitre atteint un code "
    "non cité, soit une association `ensemble` a été résolue"
)

# %% [markdown]
# ## 5. Le rendu des consignes à `centralite = exemple` — tranché
#
# La décision, ouverte au backlog à la clôture du chantier A, a été
# prise au chantier fiches (2026-09-03) : les 152 associations
# `exemple` **sont rendues**, en bloc cité `>` introduit par « À titre
# d'exemple dans le guide : », entre les consignes sujet et les règles
# générales (règle 6 ci-dessus). Le bloc cité reprend la convention de
# transcription des curés : signal structurel « ceci illustre, ceci ne
# norme pas ».
#
# `consignes_pour(code)` reste sujet-seul par défaut (les assertions
# des démonstrations n'en dépendent pas) ; le rendu de fiche passe
# `avec_exemples=True`. Aucun des six codes de démonstration ne porte
# d'exemple — F01.000 (exemple seul) et Z20.1 (dédup sujet/exemple)
# sont les témoins de ce chemin dans les tests de régression.

# %% [markdown]
# ## 6. Récapitulatif
#
# Les règles de rendu vivent dans `recode_icd/recommendations/rendu.py`
# et sont branchées dans les fiches par `cards._section_consignes`
# (entre « À ne pas décrire » et « Formulations », hors chapter_policy).
# Le CSV maître n'est pas touché :
#
# | Règle | Où |
# |---|---|
# | associations `ensemble` jamais résolues (garantie par construction) | build, en amont du Parquet |
# | filtre `centralite = sujet` (exemples à part) | `rendu.consignes_pour` |
# | exclusion du rôle `contexte` | `rendu.consignes_pour` |
# | dédup : `sujet` prime sur `exemple`, puis plus spécifique | `rendu.consignes_pour` |
# | tri par spécificité décroissante (`cle_de_tri` de production) | `rendu.consignes_pour` |
# | exemples en bloc cité « À titre d'exemple dans le guide : » | `rendu.rendre_section_consignes` |
# | « Règles générales du chapitre » en fin de section, avec situation | `rendu.rendre_section_consignes` |
# | préfixe `[rec_id]` | `rendu.rendre_section_consignes` |
#
# Reste au backlog (`docs/backlog/rendu_consignes_dans_fiches.md`) : le
# plafond par fiche (mécanisme analogue à R2 de la `chapter_policy`) et
# le rendu des conditions par code (`condition` de l'association, plus
# fine que celle de la consigne).
