"""Rendu des consignes du guide MCO dans les fiches — prototype

Notebook d'exploration **interactif**. Prototype du rendu de la section
« Consignes de codage » des fiches, à partir des deux tables du
chantier A (`recommendations.parquet` / `recommendation_codes.parquet`).
Chaque règle de rendu est une fonction courte et paramétrable ; six
codes de démonstration l'exercent, chacun choisi pour un cas précis.

Document de référence figé :
`docs/analyses/2026-08-09_conception_base_recommandations_guide_methodo.md`
(§4.2 catalogue des rôles, §4.3 résolution, §6 esquisse d'usage). Le
`.md` fait foi pour le modèle ; ce notebook prototype le rendu.

**Avertissement — prototype.** `cards.py` n'est PAS modifié :
l'insertion de la section dans les fiches est un chantier ultérieur
(cf. `docs/backlog/profils_fiches_par_usage.md`). Le jour où ce
chantier atterrit, l'implémentation réelle remplace ce prototype — les
deux ne doivent pas coexister, sinon ils divergeront en silence. Rien
de ce fichier ne doit être importé par du code de production.

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
# Les règles de rendu prototypées ici :
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
# 5. **Chaque consigne est préfixée de son `rec_id` entre crochets** —
#    traçabilité vers le guide, principe « jamais d'agrégation
#    silencieuse ».

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

from recode_icd.recommendations.code_expr import TypeExpr
from recode_icd.recommendations.resolution import cle_de_tri

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
# État attendu à la clôture du chantier A : **94 consignes**, **187
# associations curées**, **2 806 couples (consigne, code feuille)** sur
# **1 018 codes**. Les associations curées se recomptent depuis le
# Parquet par `(rec_id, code_expr, role)` — la résolution ne fait
# qu'étendre chaque expression à ses feuilles, elle n'en crée ni n'en
# perd.

# %% Volumétrie
volumetrie = {
    "consignes": recs.height,
    "associations curées": rec_codes.unique(["rec_id", "code_expr", "role"]).height,
    "couples (consigne, code feuille)": rec_codes.height,
    "codes feuilles distincts": rec_codes["code"].n_unique(),
}
for etiquette, valeur in volumetrie.items():
    print(f"{etiquette:32s}: {valeur}")

assert volumetrie["consignes"] == 94
assert volumetrie["associations curées"] == 187
assert volumetrie["couples (consigne, code feuille)"] == 2806
assert volumetrie["codes feuilles distincts"] == 1018

print()
print(rec_codes.group_by("type_expr", "specificite").len().sort("specificite", descending=True))

# %% [markdown]
# ## 2. Sélection des consignes d'une fiche
#
# `consignes_pour` matérialise les règles 1 à 3. Deux subtilités :
#
# - **une consigne peut atteindre le même code par plusieurs
#   expressions** (30 couples mesurés : GM2026-V-XXI-38 atteint Z51.31
#   par la catégorie `Z51` ET par le code `Z51.31`, par exemple). Elle
#   ne doit se rendre qu'une fois, au niveau le plus spécifique — d'où
#   la déduplication par `rec_id` après tri sur `specificite` ;
# - **le filtre des rôles s'applique avant la déduplication** : si une
#   consigne cite le code en `contexte` ET le couvre par ailleurs au
#   niveau chapitre en `regi`, c'est l'association chapitre qui reste.

# %% Fonctions de sélection


def consignes_pour(
    code: str,
    *,
    avec_exemples: bool = False,
    roles_exclus: tuple[str, ...] = ("contexte",),
) -> list[dict]:
    """Consignes à rendre sur la fiche de `code`, triées.

    Tri : spécificité décroissante, puis `sujet` avant `exemple`, puis
    `rec_id` — la clé de production `cle_de_tri`, qui rend le tri total.
    """
    assoc = rec_codes.filter(pl.col("code") == code)
    if not avec_exemples:
        assoc = assoc.filter(pl.col("centralite") == "sujet")
    assoc = assoc.filter(~pl.col("role").is_in(roles_exclus))
    assoc = assoc.sort("specificite", descending=True).unique(
        subset="rec_id", keep="first", maintain_order=True
    )
    lignes = assoc.join(
        recs.select("rec_id", "texte", "type", "millesime"), on="rec_id", how="left"
    )
    return sorted(
        lignes.iter_rows(named=True),
        key=lambda r: cle_de_tri(TypeExpr(r["specificite"]), r["centralite"], r["rec_id"]),
    )


def libelle_de(code: str) -> str:
    ligne = merged.filter(pl.col("code") == code)
    return (ligne["label"][0] or "") if ligne.height else "(libellé inconnu)"


# %% [markdown]
# ## 3. Rendu de la section
#
# `rendre_section` matérialise les règles 4 et 5 : liste principale par
# spécificité décroissante, puis « Règles générales du chapitre » pour
# les consignes de niveau chapitre. Le millésime du titre vient de la
# table, pas d'une constante — le jour où la base porte le guide
# définitif, le titre suit.

# %% Fonction de rendu


def rendre_section(code: str, **selection) -> str:
    """Section « Consignes de codage » de la fiche de `code`, en markdown."""
    lignes = consignes_pour(code, **selection)
    if not lignes:
        return ""
    millesime = lignes[0]["millesime"]
    specifiques = [r for r in lignes if TypeExpr(r["specificite"]) is not TypeExpr.CHAPITRE]
    generales = [r for r in lignes if TypeExpr(r["specificite"]) is TypeExpr.CHAPITRE]

    rendu = [f"## Consignes de codage (guide méthodologique {millesime})", ""]
    rendu += [f"- [{r['rec_id']}] {r['texte']}" for r in specifiques]
    if generales:
        chapitre = generales[0]["code_expr"]
        rendu += ["", f"### Règles générales du chapitre {chapitre}", ""]
        rendu += [f"- [{r['rec_id']}] {r['texte']}" for r in generales]
    return "\n".join(rendu)


def demo(code: str, **selection) -> None:
    print(f"════ Fiche {code} — {libelle_de(code)}")
    print()
    section = rendre_section(code, **selection)
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
# On y voit aussi la limite assumée du compromis : GM2026-V-AVC-14,
# consigne de chapitre issue de l'article AVC (« s'il n'est pas
# découvert d'affection nouvelle, le DP appartient au chapitre XXI »),
# descend sur toutes les fiches Z — y compris celle-ci. Sa curation en
# `XXI / DP / sujet` est conforme à la doctrine (la consigne régit bien
# le DP au niveau du chapitre) ; le préfixe `[rec_id]` garde le retour
# au guide possible si le chantier fiches veut affiner.

# %% Démonstration Z23.0
demo("Z23.0")

lignes_z230 = consignes_pour("Z23.0")
assert lignes_z230, "complétude violée — les consignes de chapitre ne descendent pas"
assert all(TypeExpr(r["specificite"]) is TypeExpr.CHAPITRE for r in lignes_z230), (
    "maîtrise du bruit violée — une consigne non chapitre atteint un code non cité"
)

# %% [markdown]
# ## 5. Backlog — le rendu des consignes à `centralite = exemple`
#
# Les 152 associations `exemple` sont exclues par défaut (règle 1) et
# aucune démonstration ne les rend. Leur rendu éventuel — et sa forme —
# est une décision du chantier fiches, pas de celui-ci. Elle rejoint le
# backlog déjà ouvert sur les exemples du guide : les blocs cités `>`
# des curés sont une convention de **transcription**, pas encore une
# décision de rendu de fiche (cf. CLAUDE.md, section guide MCO, et
# `docs/backlog/profils_fiches_par_usage.md`). Le jour venu, les deux
# questions se tranchent ensemble : un exemple du guide entre-t-il dans
# la fiche, et sous quelle forme — bloc cité, paraphrase interdite,
# ou exclusion pure.
#
# `consignes_pour(code, avec_exemples=True)` permet dès maintenant
# d'instrumenter cette décision sans toucher aux règles par défaut.

# %% [markdown]
# ## 6. Récapitulatif
#
# Les cinq règles de rendu tiennent en deux fonctions courtes sur les
# deux Parquets, sans toucher ni au CSV maître ni à `cards.py` :
#
# | Règle | Où |
# |---|---|
# | filtre `centralite = sujet` | `consignes_pour` |
# | exclusion du rôle `contexte` | `consignes_pour` |
# | tri par spécificité décroissante (`cle_de_tri` de production) | `consignes_pour` |
# | « Règles générales du chapitre » en fin de section | `rendre_section` |
# | préfixe `[rec_id]` | `rendre_section` |
#
# Reste au chantier fiches : l'insertion dans `cards.py`, le plafond
# par fiche (mécanisme analogue à R2 de la `chapter_policy`), le rendu
# des `exemple` et celui des conditions par code (`condition` de
# l'association, plus fine que celle de la consigne).
