"""Qualité des sources de synonymes par chapitre CIM-10

Notebook d'exploration **interactif**. Chaque étape est expliquée, chaque
fonction est courte, nommée et paramétrable : le lecteur est invité à
relancer les cellules avec ses propres plages de codes, sources, plafonds
et graines.

Document de référence figé :
`docs/analyses/2026-08-09_qualite_sources_par_chapitre.md`. Le `.md` fait
foi pour les constats et les décisions ; ce notebook sert à les rejouer,
à les affiner et à instrumenter ce qui n'est pas encore tranché.

**Avertissement — prototype.** Les règles R1, R2 et R3 sont implémentées
ici en configuration Python locale. La source de vérité finale sera le
YAML du chantier `chapter_policy`, dans `src/`. **Le jour où ce chantier
atterrit, les sections (d) et (e) doivent importer l'implémentation
réelle au lieu du prototype**, sinon les deux divergeront en silence.
Rien de ce fichier ne doit être importé par du code de production.

Le CSV maître n'est jamais modifié : ces règles ne portent que sur
l'assemblage des fiches.

Régénération du notebook :
    uv run --extra notebook python scripts/explore/_convert_to_ipynb.py \\
        scripts/explore/qualite_sources_par_chapitre.py
"""

# ruff: noqa: E402

# %% [markdown]
# ## Mode d'emploi
#
# Le `.py` est la **source de vérité** : diffable, lintable, exécutable
# directement (`uv run python scripts/explore/qualite_sources_par_chapitre.py`).
# Le `.ipynb` en est un rendu régénéré — ne pas l'éditer à la main.
#
# Le notebook se lit dans l'ordre mais chaque section est autonome une
# fois la table de travail construite (sections 1 à 3). Les fonctions
# sont regroupées dans leurs propres cellules, séparées des cellules
# d'appel : pour explorer, il suffit de rejouer une cellule d'appel avec
# d'autres arguments.
#
# Trois pièges de modélisation sont documentés au fil de l'eau
# (encadrés « ⚠ Piège »). Ils ont tous les trois produit des résultats
# **plausibles mais faux** dans une première version, et n'ont été
# détectés que par confrontation à des chiffres de référence indépendants.
# Ils valent d'être lus pour eux-mêmes.

# %% Chargement du contexte d'exploration
from recode_icd.utils.loaders_dev import load_exploration_context

ctx = load_exploration_context(with_external=True)

import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import polars as pl

# Graine unique pour tout le notebook. La changer et tout rejouer est un
# bon test de robustesse des conclusions.
SEED = 42
rng = random.Random(SEED)

pl.Config.set_tbl_rows(25)
pl.Config.set_fmt_str_lengths(90)

flat = ctx.flat if isinstance(ctx.flat, pl.DataFrame) else ctx.flat.collect()
merged = ctx.merged if isinstance(ctx.merged, pl.DataFrame) else ctx.merged.collect()

print(f"CSV maître   : {flat.height:,} lignes".replace(",", " "))
print(f"merged_codes : {merged.height:,} codes".replace(",", " "))
print(f"Sources externes chargées : {len(ctx.external)}")

# %% [markdown]
# ## 2. Situer chaque ligne dans la hiérarchie
#
# Le CSV maître ne porte que le code. Pour raisonner par chapitre et par
# bloc, il faut le joindre à `merged_codes`, dont la colonne `path` vaut
# par exemple `I/A00-A09/A00/A00.0`.
#
# ### ⚠ Piège n°1 — la catégorie ne se lit pas dans le `path`
#
# Prendre le segment d'indice 2 du `path` semble donner la catégorie. Ça
# marche sur la plupart des chapitres… mais pas sur ceux qui **imbriquent
# les blocs**. `C50.8` vit sous :
#
# ```
# II / C00-C97 / C00-C75 / C50-C50 / C50 / C50.8
# ```
#
# L'indice 2 y vaut `C00-C75`, un bloc. Une première version comptait
# donc « C00-C75 » comme une catégorie de 13 978 formulations, ce qui
# faussait toute la mesure du déséquilibre.
#
# La bonne définition est celle de `cards.py` (`_category_leaf_codes`) :
# **une catégorie est le code à 3 caractères**. On la dérive du code
# lui-même, pas du chemin.
#
# Même logique pour les blocs : plutôt qu'une position, on retient
# **tous** les segments de forme `A00-B99`, du plus large au plus étroit.
# La résolution des règles les testera du plus interne au plus large.

# %% Hiérarchie — chapitre, blocs englobants, catégorie
_RE_BLOC = r"^[A-Z]\d{2}-[A-Z]?\d{2}$"

hierarchie = merged.select(
    pl.col("code"),
    pl.col("path").str.split("/").list.get(0, null_on_oob=True).alias("chapitre"),
    pl.col("path")
    .str.split("/")
    .list.eval(pl.element().filter(pl.element().str.contains(_RE_BLOC)))
    .alias("blocs"),
    pl.col("code").str.split(".").list.first().alias("categorie"),
)

print(hierarchie.filter(pl.col("code").is_in(["C50.8", "T39.1", "R51"])))

# %% [markdown]
# ## 3. Familles de sources
#
# Le CSV porte des **libellés** de source (`CepiDc 2015`, `AP-HP
# Néphrologie`…). Pour raisonner, on les regroupe en familles.
#
# Les libellés des trois sources qui alimentent la section Formulations
# sont importés depuis `cards.py` plutôt que recopiés : si l'un est
# renommé, ce notebook suit automatiquement — c'est précisément le
# couplage que le renommage `CepiDc_2015` → `CepiDc 2015` avait failli
# casser en silence.

# %% Familles de sources
from recode_icd import cards

FAMILLE_PAR_LIBELLE: dict[str, str] = {
    "CIM-10": "OFS",
    "CIM-10 frères": "OFS",
    "ANS": "ANS",
    cards.FORMULATION_SOURCE_INDEX: "INDEX",
    "ORPHANET": "ORPHANET",
    cards.FORMULATION_SOURCE_CEPIDC: "CEPIDC",
}

#: Familles effectivement consommées par la section « Formulations
#: cliniques alternatives » (cf `cards.py`). Les autres alimentent
#: « Périmètre clinique » ou « À ne pas décrire ».
FAMILLES_FORMULATIONS = ("INDEX", "APHP", "CEPIDC")


def famille_de(libelle: str) -> str:
    """Famille d'un libellé de source CSV."""
    if libelle.startswith(cards.FORMULATION_SOURCE_APHP_PREFIX):
        return "APHP"
    return FAMILLE_PAR_LIBELLE.get(libelle, "AUTRE")


# %% Table de travail
_familles = pl.DataFrame({"source": sorted(flat["source"].unique().to_list())}).with_columns(
    pl.col("source").map_elements(famille_de, return_dtype=pl.String).alias("famille")
)

work = flat.join(hierarchie, on="code", how="left").join(_familles, on="source", how="left")
candidates = work.filter(pl.col("famille").is_in(FAMILLES_FORMULATIONS))

from recode_icd.utils.loaders_dev import _ROMAN_TO_NUM_CHAPTER

CHAPITRES = sorted(_ROMAN_TO_NUM_CHAPTER, key=lambda r: _ROMAN_TO_NUM_CHAPTER[r])

print(f"Lignes du CSV situées   : {work.height:,}".replace(",", " "))
print(f"Chapitre non résolu     : {work['chapitre'].null_count()}")
print(f"Candidates Formulations : {candidates.height:,}".replace(",", " "))

# %% [markdown]
# ## (a) Volumétrie
#
# Combien chaque source apporte-t-elle, et où ? C'est ce qui détermine
# le coût d'une exclusion : écarter une source qui n'apporte que
# quelques dizaines d'entrées sur un chapitre ne coûte presque rien.

# %% (a) Synonymes par source × chapitre
croise = (
    work.filter(pl.col("type") == "synonyme")
    .group_by("chapitre", "source")
    .len()
    .pivot(on="chapitre", index="source", values="len")
    .fill_null(0)
)
croise.select(["source"] + [c for c in CHAPITRES if c in croise.columns]).sort("source")

# %% (a) Focus sur les chapitres à politique spéciale
FOCUS = ["XVIII", "XIX", "XX", "XXI"]
focus = (
    work.filter((pl.col("type") == "synonyme") & pl.col("chapitre").is_in(FOCUS))
    .group_by("chapitre", "famille")
    .len()
    .pivot(on="chapitre", index="famille", values="len")
    .fill_null(0)
)
focus.select(["famille"] + [c for c in FOCUS if c in focus.columns]).sort("famille")

# %% (a) Couverture par famille
(
    work.group_by("famille")
    .agg(pl.col("code").n_unique().alias("codes_couverts"), pl.len().alias("lignes"))
    .sort("lignes", descending=True)
)

# %% [markdown]
# ### Écarts avec les chiffres de référence
#
# L'analyse initiale portait sur le CSV **pré-merge CepiDc** (199 970
# lignes). Ces chiffres sont figés dans le document de trace ; ici on
# mesure l'écart plutôt que de les réécrire.

# %% (a) Écart référence pré-merge → CSV courant
REFERENCE_PRE_MERGE = {
    ("APHP", "XVIII"): 112,
    ("APHP", "XIX"): 235,
    ("APHP", "XX"): 49,
    ("APHP", "XXI"): 39,
    ("INDEX", "XIX"): 3935,
    ("INDEX", "XX"): 0,
    ("INDEX", "XXI"): 1695,
}
_courant = {
    (r["famille"], r["chapitre"]): r["len"]
    for r in work.filter(pl.col("type") == "synonyme")
    .group_by("famille", "chapitre")
    .len()
    .iter_rows(named=True)
}
pl.DataFrame(
    [
        {
            "famille": f,
            "chapitre": c,
            "reference": ref,
            "courant": _courant.get((f, c), 0),
            "ecart": _courant.get((f, c), 0) - ref,
        }
        for (f, c), ref in REFERENCE_PRE_MERGE.items()
    ]
).sort("famille", "chapitre")

# %% [markdown]
# ## (b) Échantillonneur qualitatif
#
# La volumétrie ne dit rien de la qualité. La fonction ci-dessous tire
# un échantillon reproductible pour aller lire les libellés.
#
# **À vous de jouer** : changez `plage`, `famille`, `n` ou `graine` et
# rejouez la cellule d'appel. `plage` accepte soit un chapitre romain
# (`"XIX"`), soit des préfixes de code (`("T36", "T37")`).

# %% Fonction — échantillon reproductible
def echantillon(
    plage: str | tuple[str, ...],
    famille: str | None = None,
    type_note: str | None = "synonyme",
    n: int = 12,
    graine: int = SEED,
    table: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Tire `n` lignes au hasard, de façon reproductible.

    `plage` : chapitre romain (« XIX ») ou préfixes de code
    (« S65 », ou le tuple ("T36", "T37")).
    """
    sub = work if table is None else table
    plages = (plage,) if isinstance(plage, str) else plage
    if plages[0] in CHAPITRES:
        sub = sub.filter(pl.col("chapitre").is_in(list(plages)))
    else:
        sub = sub.filter(pl.any_horizontal([pl.col("code").str.starts_with(p) for p in plages]))
    if famille:
        sub = sub.filter(pl.col("famille") == famille)
    if type_note:
        sub = sub.filter(pl.col("type") == type_note)
    if sub.is_empty():
        return sub.select("code", "source", "texte")
    return sub.select("code", "source", "texte").sample(
        n=min(n, sub.height), seed=graine, shuffle=True
    )


# %% (b) Index CIM-10 vol3 sur le chapitre XIX — le format « chemin d'index »
echantillon("XIX", famille="INDEX")

# %% (b) CepiDc sur le bloc T36-T50 — noms de médicaments nus
echantillon(tuple(f"T{n}" for n in range(36, 51)), famille="CEPIDC", n=15)

# %% (b) CepiDc sur un chapitre diagnostique — le contre-exemple
echantillon("X", famille="CEPIDC", n=12)

# %% [markdown]
# ## (c) Motifs parasites du CepiDc
#
# Deux heuristiques repérées à la lecture : un **préfixe** de type
# « prise / traitement / sous / injection / perfusion », et le **mot
# unique capitalisé** (nom de médicament).
#
# ### ⚠ Piège n°2 — le drapeau `re.IGNORECASE` ne traverse pas polars
#
# On compile volontiers un motif avec `re.compile(..., flags=re.IGNORECASE)`,
# puis on passe `.pattern` à `pl.col(...).str.contains(...)`. **Le
# drapeau est perdu** : polars ne reçoit que la chaîne du motif, pas
# l'objet compilé.
#
# Une première version cherchait ainsi `états? mentionn` dans des textes
# commençant par « **É**tats mentionnés » : zéro résultat, sans la
# moindre erreur. Le remède est le drapeau **inline** `(?i)`, qui fait
# partie du motif lui-même et survit donc au passage.
#
# Règle à retenir : dans ce projet, tout motif destiné à polars porte son
# `(?i)` en tête.

# %% Fonction — détection des motifs parasites
_PREFIXES_PARASITES = ("prise", "traitement", "sous", "injection", "perfusion")

#: `(?i)` **inline** — cf piège n°2.
RE_PREFIXE = re.compile(r"(?i)^\s*(" + "|".join(_PREFIXES_PARASITES) + r")\b")
RE_MOT_UNIQUE_CAPITALISE = re.compile(r"^\s*[A-ZÀ-Ý][\wÀ-ÿ'-]*\s*$")


def motif_parasite(texte: str | None) -> str | None:
    """Nom du motif parasite détecté, ou None."""
    if not texte:
        return None
    if RE_PREFIXE.match(texte):
        return "prefixe_prise_traitement"
    if RE_MOT_UNIQUE_CAPITALISE.match(texte):
        return "mot_unique_capitalise"
    return None


# %% (c) Taux de motifs parasites par chapitre
cepidc = work.filter(pl.col("famille") == "CEPIDC").with_columns(
    pl.col("texte").map_elements(motif_parasite, return_dtype=pl.String).alias("motif")
)
(
    cepidc.group_by("chapitre")
    .agg(pl.len().alias("n"), pl.col("motif").is_not_null().sum().alias("n_parasites"))
    .with_columns((pl.col("n_parasites") / pl.col("n")).round(4).alias("taux"))
    .sort("taux", descending=True)
    .head(10)
)

# %% [markdown]
# ### La limite de l'heuristique, et pourquoi elle décide de la politique
#
# Le motif « mot unique capitalisé » n'est parasite **que pour les noms
# de médicaments**. Ailleurs il capture des acronymes et des éponymes
# qui sont d'excellents synonymes. C'est la raison décisive de préférer
# une politique **par plage de codes** à une curation textuelle générale
# du CepiDc : aucune heuristique de texte ne sépare « Gutron » de
# « Hashimoto ».

# %% (c) Faux positifs du motif « mot unique capitalisé »
(
    cepidc.filter(
        (pl.col("motif") == "mot_unique_capitalise")
        & ~pl.col("chapitre").is_in(["XIX", "XX", "XXI"])
    )
    .select("code", "chapitre", "texte")
    .sample(n=20, seed=SEED, shuffle=True)
)

# %% [markdown]
# ## (d) Règles R1 et R2 — prototype
#
# **R1 — filtrage par plage de codes × source.** Certaines familles de
# sources n'ont rien à faire sur certains chapitres : les Z sont des
# circonstances administratives, les V-Y se codent sur les circonstances
# décrites, les S-T sont combinatoires par site et nature de lésion.
#
# R1 **ne porte plus l'exclusion de l'Index** : la mesure de la section
# (e) a montré que le problème de l'Index est son *format*, pas son
# chapitre. C'est l'objet de la règle R3.
#
# **R2 — plafond par source des fiches catégories.** Les fiches feuilles
# plafonnent Index et CepiDc à 10 ; les fiches catégories n'ont aucun
# plafond par source, d'où la domination du CepiDc.
#
# ### ⚠ Le piège de la résolution bloc > chapitre
#
# La règle la plus spécifique **remplace** la moins spécifique, elle ne
# s'y ajoute pas. C'est le seul choix qui permette de *ré-admettre* une
# source au niveau d'un bloc — le cas prévu pour T36-T50, qui pourrait
# un jour être exempté de la politique du chapitre XIX. En contrepartie,
# une entrée de bloc doit **redéclarer** les exclusions du chapitre
# qu'elle veut conserver ; l'oublier rouvre des sources en silence.

# %% Configuration déclarative des politiques (PROTOTYPE)
@dataclass(frozen=True)
class Politique:
    """Politique applicable à une plage de codes.

    `familles_exclues` : familles retirées de la section Formulations.
    `generation_llm` : autorise ou non les formulations générées par LLM
    (flag distinct — une source LLM peut être exclue là où les sources
    réelles sont conservées).
    """

    familles_exclues: frozenset[str] = field(default_factory=frozenset)
    generation_llm: bool = True


POLITIQUE_DEFAUT = Politique()

_EXTERNES = frozenset({"APHP", "ORPHANET", "CEPIDC", "LLM"})

POLITIQUE_CHAPITRE: dict[str, Politique] = {
    # XVIII (R00-R99) : les codes R ont de vraies variantes d'usage
    # (« mal de tête » pour R51). Sources réelles conservées, mais pas
    # de génération LLM, qui élargirait le périmètre de codes déjà peu
    # spécifiques.
    "XVIII": Politique(generation_llm=False),
    "XIX": Politique(familles_exclues=_EXTERNES, generation_llm=False),
    "XX": Politique(familles_exclues=_EXTERNES, generation_llm=False),
    "XXI": Politique(familles_exclues=_EXTERNES, generation_llm=False),
}

POLITIQUE_BLOC: dict[str, Politique] = {
    # T36-T50 se comporte plus comme des diagnostics classiques que
    # comme des lésions par site : il pourrait être exempté un jour de
    # la politique XIX. Mais CepiDc doit y rester exclu quoi qu'il
    # arrive (noms de médicaments nus). L'entrée reprend aujourd'hui la
    # politique XIX à l'identique — cf le piège de résolution ci-dessus.
    "T36-T50": Politique(familles_exclues=_EXTERNES, generation_llm=False),
}


# %% Fonction — résolution de la politique
def politique_pour(chapitre: str | None, blocs: list[str] | None) -> Politique:
    """Résout la politique applicable : bloc > chapitre > défaut.

    `blocs` va du plus large au plus étroit ; on les teste du plus
    **interne** au plus large, la règle la plus spécifique gagnant.
    """
    for bloc in reversed(blocs or []):
        if bloc in POLITIQUE_BLOC:
            return POLITIQUE_BLOC[bloc]
    if chapitre and chapitre in POLITIQUE_CHAPITRE:
        return POLITIQUE_CHAPITRE[chapitre]
    return POLITIQUE_DEFAUT


# Vérification rapide de la résolution.
for _code in ("T39.1", "S52.50", "R51", "J18.9"):
    _r = hierarchie.filter(pl.col("code") == _code)
    _p = politique_pour(_r["chapitre"][0], list(_r["blocs"][0]))
    print(f"{_code:8} → exclut {sorted(_p.familles_exclues) or '∅'}, llm={_p.generation_llm}")


# %% Fonction — application de R1
def applique_r1(df: pl.DataFrame) -> pl.DataFrame:
    """Retire les lignes dont la famille est exclue sur leur plage.

    Fonction pure : mêmes entrées → mêmes sorties.
    """
    combis = (
        df.select("chapitre", "blocs", "famille")
        .with_columns(pl.col("blocs").list.join("|").alias("_cle"))
        .unique(subset=["chapitre", "_cle", "famille"])
    )
    exclues = [
        (chap, cle, fam)
        for chap, blocs, fam, cle in combis.iter_rows()
        if fam in politique_pour(chap, list(blocs or [])).familles_exclues
    ]
    if not exclues:
        return df
    marque = df.with_columns(pl.col("blocs").list.join("|").alias("_cle"))
    masque = pl.any_horizontal(
        [
            (pl.col("chapitre") == c) & (pl.col("_cle") == k) & (pl.col("famille") == f)
            for c, k, f in exclues
        ]
    )
    return marque.filter(~masque).drop("_cle")


# %% (d) Effet de R1
apres_r1 = applique_r1(candidates)
print(f"Candidates : {candidates.height:,} → {apres_r1.height:,}".replace(",", " "))
print(f"Écartées   : {candidates.height - apres_r1.height:,}".replace(",", " "))

(
    candidates.group_by("chapitre", "famille")
    .len()
    .rename({"len": "avant"})
    .join(
        apres_r1.group_by("chapitre", "famille").len().rename({"len": "apres"}),
        on=["chapitre", "famille"],
        how="left",
    )
    .with_columns(pl.col("apres").fill_null(0))
    .with_columns((pl.col("avant") - pl.col("apres")).alias("ecartees"))
    .filter(pl.col("ecartees") > 0)
    .sort("ecartees", descending=True)
)

# %% (d) Fiches dont la section Formulations devient vide
_avant_codes = set(candidates["code"].unique().to_list())
_apres_codes = set(apres_r1["code"].unique().to_list())
_vides = _avant_codes - _apres_codes
print(f"Codes avec une section Formulations : {len(_avant_codes):,}".replace(",", " "))
print(f"Codes dont elle devient vide        : {len(_vides):,}".replace(",", " "))
(
    pl.DataFrame({"code": sorted(_vides)})
    .join(hierarchie, on="code", how="left")
    .group_by("chapitre")
    .len()
    .sort("len", descending=True)
)

# %% [markdown]
# ### ⚠ Piège n°3 — tronquer n'est pas échantillonner
#
# Pour mesurer la composition d'une fiche catégorie, il faut modéliser
# la troncature au plafond global (`CATEGORY_FORMULATIONS_MAX = 50`).
#
# La tentation est de trier puis de prendre la tête de liste : c'est
# déterministe, donc reproductible. **Mais `cards.py` tronque avec
# `rng.sample`**, un tirage *uniforme*, qui préserve en espérance la
# composition par source du vivier. Une troncature sur l'ordre
# alphabétique privilégie au contraire les premières feuilles de la
# catégorie et **biaise la composition**.
#
# Concrètement : la part médiane de CepiDc mesurée tombait à 0,50 au
# lieu de 0,76. Le chiffre était crédible, et faux.
#
# Le remède : ordonner par un **hash à graine fixe**, qui reproduit
# l'uniformité du tirage tout en restant déterministe d'un run à l'autre.

# %% Fonctions — plafonnement (R2) et troncature globale
def ordre_pseudo_aleatoire(graine: int = SEED) -> pl.Expr:
    """Clé de tri uniforme et reproductible — cf piège n°3."""
    return (pl.col("code") + "|" + pl.col("texte")).hash(seed=graine).alias("_alea")


def applique_r2(df: pl.DataFrame, plafond: int, graine: int = SEED) -> pl.DataFrame:
    """Plafonne à `plafond` entrées par (catégorie, **famille**).

    Par famille et non par libellé : la question posée est la domination
    d'un *type* d'apport, et les neuf feuilles AP-HP forment un seul
    apport métier.
    """
    return (
        df.with_columns(ordre_pseudo_aleatoire(graine))
        .sort("categorie", "famille", "_alea")
        .with_columns(pl.int_range(pl.len()).over("categorie", "famille").alias("_rang"))
        .filter(pl.col("_rang") < plafond)
        .drop("_rang", "_alea")
    )


def tronque_global(df: pl.DataFrame, plafond: int, graine: int = SEED) -> pl.DataFrame:
    """Plafond global par catégorie, tel que `cards.py` l'applique."""
    return (
        df.with_columns(ordre_pseudo_aleatoire(graine))
        .sort("categorie", "_alea")
        .with_columns(pl.int_range(pl.len()).over("categorie").alias("_rang"))
        .filter(pl.col("_rang") < plafond)
        .drop("_rang", "_alea")
    )


def part_cepidc(df: pl.DataFrame) -> pl.DataFrame:
    """Part du CepiDc dans chaque catégorie de `df`."""
    total = df.group_by("categorie").len().rename({"len": "total"})
    return (
        df.filter(pl.col("famille") == "CEPIDC")
        .group_by("categorie")
        .len()
        .rename({"len": "n_cepidc"})
        .join(total, on="categorie", how="right")
        .with_columns(pl.col("n_cepidc").fill_null(0))
        .with_columns((pl.col("n_cepidc") / pl.col("total")).alias("part_cepidc"))
    )


# %% [markdown]
# ### Calibration du plafond R2
#
# Le jeu de catégories évalué doit être **figé une fois** — celles dont
# le vivier dépasse le plafond global, donc celles où l'échantillonnage
# mord. Le recalculer après chaque plafond mesurerait une population
# différente à chaque ligne, c'est-à-dire rien.
#
# `PLAFONDS` est modifiable : ajoutez vos valeurs et rejouez.

# %% Fonction — calibration
PLAFOND_GLOBAL = cards.CATEGORY_FORMULATIONS_MAX  # 50
PLAFOND_FEUILLES = cards.INDEX_SAMPLE_SIZE  # 10


def calibre(df: pl.DataFrame, plafonds: tuple[int | None, ...]) -> pl.DataFrame:
    """Compare l'effet de plusieurs plafonds par source.

    Rapporte, pour chaque plafond : le volume rendu, le volume perdu
    face à la situation actuelle, la part médiane de CepiDc et le nombre
    de catégories au-delà de 80 %.
    """
    base = df.filter(pl.col("categorie").is_not_null())
    vivier = base.group_by("categorie").len().rename({"len": "vivier"})
    ref = vivier.filter(pl.col("vivier") > PLAFOND_GLOBAL).select("categorie")
    restreint = base.join(ref, on="categorie", how="inner")
    reference = tronque_global(restreint, PLAFOND_GLOBAL).height

    lignes = []
    for plafond in plafonds:
        sous = restreint if plafond is None else applique_r2(restreint, plafond)
        rendu = tronque_global(sous, PLAFOND_GLOBAL)
        prof = part_cepidc(rendu)
        lignes.append(
            {
                "plafond": "aucun (actuel)" if plafond is None else str(plafond),
                "rendues": rendu.height,
                "perdues": reference - rendu.height,
                "part_cepidc_mediane": round(prof["part_cepidc"].median(), 3),
                "categories_sup_80pct": prof.filter(pl.col("part_cepidc") > 0.8).height,
            }
        )
    return pl.DataFrame(lignes)


# %% (d) Calibration — R2 retenu à 20
PLAFONDS = (None, 5, 10, 15, 20, 30)
_cal = calibre(apres_r1, PLAFONDS)
print(f"Plafond des fiches feuilles : {PLAFOND_FEUILLES} | plafond global : {PLAFOND_GLOBAL}")
_cal

# %% [markdown]
# **Lecture.** L'essentiel du bénéfice vient d'avoir un plafond, quel
# qu'il soit : les catégories au-delà de 80 % s'effondrent, et la part
# médiane chute d'un coup. Entre 5 et 20 les métriques d'équilibre ne
# bougent presque plus, alors que le volume conservé triple.
#
# **Décision : R2 = 20.** Deux plafonds distincts coexistent donc — 10
# sur les fiches feuilles, 20 sur les fiches catégories — et c'est
# justifié : les viviers ne sont pas comparables. Une fiche feuille tire
# d'un seul code ; une fiche catégorie agrège toutes ses feuilles, avec
# un vivier d'un ordre de grandeur supérieur. Le même plafond y serait
# beaucoup plus mordant.

# %% (d) Effet de R2=20 sur trois catégories très déséquilibrées
R2_RETENU = 20

_base = apres_r1.filter(pl.col("categorie").is_not_null())
_prof = part_cepidc(_base)
_pires = (
    _prof.filter((pl.col("total") > PLAFOND_GLOBAL) & (pl.col("part_cepidc") > 0.8))
    .sort("total", descending=True)
    .head(3)
)
_apres_r2 = applique_r2(_base, R2_RETENU)
for _cat in _pires["categorie"].to_list():
    _av = _base.filter(pl.col("categorie") == _cat)
    _ap = tronque_global(_apres_r2.filter(pl.col("categorie") == _cat), PLAFOND_GLOBAL)
    print(f"\n=== {_cat} ===")
    print(f"  avant : {_av.height:5} formulations — {_av.group_by('famille').len().sort('len', descending=True).to_dicts()}")
    print(f"  après : {_ap.height:5} formulations — {_ap.group_by('famille').len().sort('len', descending=True).to_dicts()}")

# %% [markdown]
# ## (e) R3 — le format de l'entrée, pas le chapitre
#
# R1 excluait initialement l'Index CIM-10 vol3 des chapitres XIX et XXI,
# au motif de son format « chemin d'index inversé ». La mesure ci-dessous
# montre que ce format **domine presque partout**, et davantage sur des
# chapitres qui n'étaient pas exclus.
#
# D'où **R3** : le critère d'exclusion des entrées Index est leur
# **format**, transversalement à tout le référentiel. Cette section
# instrumente le détecteur ; il sera figé après lecture des sorties.
#
# Trois motifs sont testés séparément puis combinés :
#
# | Motif | Ce qu'il attrape |
# |---|---|
# | `voir` | renvois « voir aussi », « - voir » |
# | `parentheses_index` | parenthèses grammaticales `(de)`, `(à)`, `(acquise)`… |
# | `virgules_multiples` | structure inversée à deux virgules ou plus |

# %% Fonctions — détecteur de format « chemin d'index »
RE_VOIR = r"(?i)voir\s"
RE_PAREN_INDEX = (
    r"\((?i:de|du|des|d'|à|au|aux|en|le|la|les|un|une|par|pour|avec|sans"
    r"|dûe?s? à|due?s? à|sur|acquise?|congénitale?)\)"
)
RE_VIRGULES_MULTIPLES = r",[^,]*,"

MOTIFS_INDEX = {
    "voir": RE_VOIR,
    "parentheses_index": RE_PAREN_INDEX,
    "virgules_multiples": RE_VIRGULES_MULTIPLES,
}


def marque_motifs_index(df: pl.DataFrame) -> pl.DataFrame:
    """Ajoute une colonne booléenne par motif, plus `chemin_index`."""
    out = df.with_columns(
        [pl.col("texte").str.contains(pat).alias(nom) for nom, pat in MOTIFS_INDEX.items()]
    )
    return out.with_columns(
        pl.any_horizontal([pl.col(nom) for nom in MOTIFS_INDEX]).alias("chemin_index")
    )


def detecte_strict(df: pl.DataFrame) -> pl.DataFrame:
    """Variante plus large : toute virgule, toute parenthèse, tout « voir ».

    Autrement dit : ne garde que les entrées d'un seul tenant, sans
    ponctuation d'index.
    """
    return df.with_columns(
        (pl.col("texte").str.contains(r"[,()]") | pl.col("texte").str.contains(RE_VOIR)).alias(
            "chemin_index_strict"
        )
    )


# %% (e) Taux de détection par chapitre
index_lignes = detecte_strict(marque_motifs_index(work.filter(pl.col("famille") == "INDEX")))
(
    index_lignes.group_by("chapitre")
    .agg(
        pl.len().alias("n_index"),
        pl.col("chemin_index").sum().alias("n_3motifs"),
        pl.col("chemin_index_strict").sum().alias("n_strict"),
    )
    .with_columns(
        (pl.col("n_3motifs") / pl.col("n_index")).round(3).alias("part_3motifs"),
        (pl.col("n_strict") / pl.col("n_index")).round(3).alias("part_strict"),
    )
    .sort("n_index", descending=True)
)

# %% (e) Ce que le détecteur à 3 motifs ÉCARTE
index_lignes.filter(pl.col("chemin_index")).select("code", "texte").sample(
    n=12, seed=SEED, shuffle=True
).sort("code")

# %% (e) Ce que le détecteur à 3 motifs GARDE
index_lignes.filter(~pl.col("chemin_index")).select("code", "texte").sample(
    n=15, seed=SEED, shuffle=True
).sort("code")

# %% [markdown]
# ### Relecture manuelle de 30 entrées
#
# Les étiquettes ci-dessous ont été posées **à la lecture**, entrée par
# entrée, sur un tirage à graine fixe. Critère retenu : *un clinicien
# écrirait-il cette chaîne telle quelle dans un compte rendu ?* Si non,
# l'entrée est un chemin d'index.
#
# Ce sont des étiquettes d'une seule relecture : elles sont à revalider
# avant de figer le détecteur. Le tirage étant reproductible, une
# seconde relecture peut porter sur exactement les mêmes entrées.

# %% (e) Échantillon relu à la main
ECHANTILLON_RELU_GRAINE = 1234

#: Les deux seules entrées du tirage jugées directement utilisables.
NATURELLES_RELUES = {"Trachéomalacie", "Dysbarisme"}

relu = (
    work.filter(pl.col("famille") == "INDEX")
    .select("code", "texte")
    .sample(n=30, seed=ECHANTILLON_RELU_GRAINE, shuffle=True)
    .sort("code")
    .with_columns((~pl.col("texte").is_in(list(NATURELLES_RELUES))).alias("est_chemin"))
)
relu = detecte_strict(marque_motifs_index(relu))
print(f"Entrées relues : {relu.height} — dont chemins d'index : {relu['est_chemin'].sum()}")
relu.select("code", "texte", "est_chemin")


# %% Fonction — matrice de confusion
def confusion(df: pl.DataFrame, colonne: str, verite: str = "est_chemin") -> dict[str, int]:
    """Compte VP / FN / FP / VN d'un détecteur face aux étiquettes."""
    return {
        "VP": df.filter(pl.col(verite) & pl.col(colonne)).height,
        "FN": df.filter(pl.col(verite) & ~pl.col(colonne)).height,
        "FP": df.filter(~pl.col(verite) & pl.col(colonne)).height,
        "VN": df.filter(~pl.col(verite) & ~pl.col(colonne)).height,
    }


# %% (e) Performance des deux variantes
_perf = []
for _col, _nom in (("chemin_index", "3 motifs"), ("chemin_index_strict", "strict")):
    _c = confusion(relu, _col)
    _n_ecarte = index_lignes.filter(pl.col(_col)).height
    _tot = index_lignes.height
    _perf.append(
        {
            "detecteur": _nom,
            **_c,
            "rappel": round(_c["VP"] / max(_c["VP"] + _c["FN"], 1), 3),
            "precision": round(_c["VP"] / max(_c["VP"] + _c["FP"], 1), 3),
            "index_ecarte": _n_ecarte,
            "index_garde": _tot - _n_ecarte,
            "part_ecartee": round(_n_ecarte / _tot, 3),
        }
    )
pl.DataFrame(_perf)

# %% (e) Les désaccords, à lire avant de figer le détecteur
print("Faux négatifs du détecteur à 3 motifs (chemins non détectés) :")
print(relu.filter(pl.col("est_chemin") & ~pl.col("chemin_index")).select("code", "texte"))
print("\nFaux positifs (entrées utilisables écartées à tort) :")
print(relu.filter(~pl.col("est_chemin") & pl.col("chemin_index")).select("code", "texte"))

# %% (e) Ce que « 3 motifs » garde mais que « strict » écarte
_zone_grise = index_lignes.filter(~pl.col("chemin_index") & pl.col("chemin_index_strict"))
print(f"Zone grise entre les deux variantes : {_zone_grise.height:,} entrées".replace(",", " "))
_zone_grise.select("code", "texte").sample(n=15, seed=SEED, shuffle=True).sort("code")

# %% [markdown]
# ### Ce que la zone grise dit du choix
#
# La variante stricte est parfaite sur l'échantillon relu mais écarte
# ~97 % de l'Index ; le détecteur à trois motifs en écarte ~85 %. La
# différence est faite d'entrées comme « Rectite (à), amibienne » : le
# **contenu** est bon (« rectite amibienne »), seul le **formatage** est
# de l'index.
#
# Cela ouvre une troisième voie, à instruire séparément : **normaliser**
# ces entrées (retirer les parenthèses grammaticales, remettre les
# segments dans l'ordre) plutôt que les écarter. Elle récupérerait une
# information réelle, au prix d'un travail de réécriture — donc hors du
# périmètre d'un simple détecteur.

# %% [markdown]
# ## (f) Normaliser plutôt qu'écarter — instruction de la troisième voie
#
# La section (e) a laissé une question ouverte : 4 231 entrées séparent
# les deux variantes du détecteur, du type « Rectite (à), amibienne » —
# **contenu bon, formatage d'index**. Les écarter perd de l'information
# réelle. Cette section instruit la troisième voie : les **normaliser**.
#
# ### ⚠ Traçabilité — une transformation de *rendu*, pas de données
#
# La normalisation est appliquée par `cards.py` **au moment de
# l'assemblage de la fiche**. Elle ne touche **jamais** le CSV maître :
#
# - la colonne `texte` du CSV conserve la **forme source**, qui reste la
#   référence et la seule chose auditable ;
# - la forme normalisée n'existe qu'en sortie, dans le markdown de la
#   fiche ;
# - aucune ligne n'est fusionnée, supprimée ni réétiquetée dans les
#   données.
#
# C'est la condition pour rester conforme au principe du CLAUDE.md
# « la source de toute information est tracée ; jamais d'agrégation
# silencieuse ». Une normalisation appliquée en amont, dans le CSV,
# violerait ce principe : on ne pourrait plus remonter au libellé
# officiel de l'Index vol3.

# %% [markdown]
# ### Typologie des entrées de l'Index
#
# Avant de normaliser, il faut savoir ce qu'on manipule. On classe la
# source entière par **forme** :
#
# - nombre de **segments** (séparés par des virgules) ;
# - présence de **connecteurs parenthésés** de liaison — `(à)`, `(de)`,
#   `(avec)`… — par opposition aux parenthèses *qualifiantes*
#   (`(chronique)`, `(aigu)`) qui portent du sens ;
# - présence d'un **renvoi** « voir » / « voir aussi ».

# %% Fonctions — typologie des formes
#: Parenthèses de **liaison** : leur contenu entier est un mot outil.
#: À distinguer des parenthèses qualifiantes, qui portent du sens.
CONNECTEURS_LIAISON = (
    "de", "du", "des", "d'", "à", "au", "aux", "en", "le", "la", "les",
    "par", "pour", "avec", "sans", "sur", "dû à", "due à", "dues à", "dus à",
)
RE_CONNECTEUR = re.compile(
    r"\s*\((?:" + "|".join(re.escape(c) for c in CONNECTEURS_LIAISON) + r")\)",
    re.IGNORECASE,
)
RE_RENVOI = re.compile(r"(?i)\bvoir\b")


def forme_index(texte: str) -> str:
    """Classe une entrée Index par forme : renvoi, 1/2/3+ segments."""
    if RE_RENVOI.search(texte):
        return "renvoi"
    n = texte.count(",") + 1
    if n == 1:
        return "1_segment"
    if n == 2:
        return "2_segments"
    return "3+_segments"


# %% (f) Volumétrie par forme
index_formes = work.filter(pl.col("famille") == "INDEX").with_columns(
    pl.col("texte").map_elements(forme_index, return_dtype=pl.String).alias("forme"),
    pl.col("texte").str.contains(RE_CONNECTEUR.pattern).alias("connecteur_liaison"),
)
(
    index_formes.group_by("forme", "connecteur_liaison")
    .len()
    .sort("len", descending=True)
)

# %% (f) Volumétrie par forme × chapitre
_ORDRE_FORMES = ("1_segment", "2_segments", "3+_segments", "renvoi")
_par_chapitre = (
    index_formes.group_by("chapitre", "forme")
    .len()
    .pivot(on="forme", index="chapitre", values="len")
    .fill_null(0)
)
_colonnes_presentes = [c for c in _ORDRE_FORMES if c in _par_chapitre.columns]
(
    _par_chapitre.select(["chapitre", *_colonnes_presentes])
    .with_columns(pl.sum_horizontal(_colonnes_presentes).alias("total"))
    .sort("total", descending=True)
)

# %% [markdown]
# ### Le normalisateur prototype
#
# Périmètre volontairement étroit : **formes à 1 ou 2 segments, sans
# renvoi**. Trois opérations, toutes déterministes, **sans LLM** :
#
# 1. suppression des connecteurs parenthésés de liaison ;
# 2. recollement `segment + qualifiant` pour les formes à deux segments ;
# 3. minuscule initiale.
#
# Aucun réordonnancement au-delà du recollement à deux segments. Les
# formes à trois segments ou plus, et toutes celles portant un renvoi,
# **restent écartées** — elles relèvent du détecteur de la section (e).

# %% Fonction — normalisateur déterministe
def normalise_entree_index(texte: str | None) -> str | None:
    """Forme normalisée d'une entrée Index, ou None si hors périmètre.

    Hors périmètre : renvois « voir », et formes à 3 segments ou plus.
    """
    if not texte or RE_RENVOI.search(texte):
        return None
    segments = [s.strip() for s in texte.split(",")]
    if len(segments) > 2:
        return None
    segments = [RE_CONNECTEUR.sub("", s).strip() for s in segments]
    segments = [s for s in segments if s]
    if not segments:
        return None
    sortie = re.sub(r"\s+", " ", " ".join(segments)).strip()
    return sortie[0].lower() + sortie[1:] if sortie else None


# Démonstration sur l'exemple canonique.
for _ex in ("Rectite (à), amibienne", "Anémie (à) (de), ferriprive", "Dysurie"):
    print(f"{_ex!r:45} → {normalise_entree_index(_ex)!r}")

# %% (f) Périmètre couvert par le normalisateur
index_norm = index_formes.with_columns(
    pl.col("texte")
    .map_elements(normalise_entree_index, return_dtype=pl.String)
    .alias("normalise")
)
_n_norm = index_norm.filter(pl.col("normalise").is_not_null()).height
print(f"Entrées Index          : {index_norm.height:,}".replace(",", " "))
print(f"Normalisables          : {_n_norm:,} ({_n_norm / index_norm.height:.1%})".replace(",", " "))
print(f"Hors périmètre         : {index_norm.height - _n_norm:,}".replace(",", " "))

# %% [markdown]
# ### Relecture manuelle de 50 normalisations
#
# Échantillon reproductible (`seed=99`), relu entrée par entrée avec
# trois étiquettes :
#
# | Étiquette | Critère |
# |---|---|
# | `correcte` | utilisable telle quelle, aucun artefact résiduel |
# | `degradee` | artefact résiduel ou mot de liaison perdu, **sens non ambigu** |
# | `fautive` | sens changé, inversé, ou chaîne inintelligible |
#
# Comme pour le détecteur, ces étiquettes viennent d'**une seule
# relecture** : le tirage est reproductible pour permettre un second avis.

# %% (f) Échantillon relu — étiquettes
ECHANTILLON_NORM_GRAINE = 99

#: Étiquettes posées à la relecture. Tout code absent est `degradee`,
#: la classe majoritaire.
RELECTURE_NORMALISATION: dict[str, str] = {
    # Utilisables telles quelles.
    "D50.9": "correcte",   # anémie ferriprive
    "F60.6": "correcte",   # personnalité évitante
    "G83.0": "correcte",   # diplégie supérieure
    "H11.1": "correcte",   # calcification conjonctive
    "H35.5": "correcte",   # dégénérescence vitréo-rétinienne
    "I73.9": "correcte",   # maladie vasospastique
    "K62.3": "correcte",   # proctoptose
    "N40": "correcte",     # hypertrophie adénofibromateuse de la prostate
    "R10.4": "correcte",   # crampe abdominale
    "R20.1": "correcte",   # hémihypoesthésie
    "R30.0": "correcte",   # dysurie
    # Sens changé ou chaîne inintelligible.
    "E20.9": "fautive",    # deux synonymes recollés : « hypoparathyroïdie hypoparathyroïdisme »
    "E80.2": "fautive",    # deux types alternatifs recollés, suggère qu'ils coexistent
    "H53.1": "fautive",    # annotation d'index recollée : « signifiant cécité diurne (canada) »
    "N76.6": "fautive",    # éponyme inversé : « lipschütz ulcère de »
    "O00.1": "fautive",    # « grossesse (unique) (utérine) tubaire » — contradictoire
    "Q87.1": "fautive",    # éponyme inversé : « prader-willi syndrome de »
}

echantillon_norm = (
    index_norm.filter(pl.col("normalise").is_not_null())
    .select("code", "texte", "normalise")
    .sample(n=50, seed=ECHANTILLON_NORM_GRAINE, shuffle=True)
    .sort("code")
    .with_columns(
        pl.col("code")
        .replace_strict(RELECTURE_NORMALISATION, default="degradee")
        .alias("etiquette")
    )
)
echantillon_norm.group_by("etiquette").len().sort("len", descending=True)

# %% (f) Le détail, pour relecture
echantillon_norm.select("code", "texte", "normalise", "etiquette")

# %% [markdown]
# ### Ce que la relecture apprend
#
# Deux causes dominent, et **toutes deux sont détectables par motif** —
# donc corrigeables sans LLM :
#
# 1. **Parenthèses qualifiantes résiduelles** (cause de la quasi-totalité
#    des `degradee`). Le normalisateur ne retire que les connecteurs de
#    liaison, laissant `(chronique) (aigu) (sénile)…`. C'est le premier
#    levier d'amélioration.
# 2. **Inversions d'éponymes** (`« Lipschütz, ulcère de »`,
#    `« Prader-Willi, syndrome de »`) et **énumérations de synonymes**
#    (`« Hypoparathyroïdie, hypoparathyroïdisme »`), qui produisent les
#    `fautive`. Le second segment y est une tête, pas un qualifiant.
#
# Les cellules suivantes chiffrent ces deux motifs sur toute la source.

# %% (f) Poids des deux causes sur l'ensemble des normalisables
_normalisables = index_norm.filter(pl.col("normalise").is_not_null())

#: Second segment de forme « syndrome de », « maladie de »… : le
#: recollement dans l'ordre y produit une inversion fautive.
RE_EPONYME_INVERSE = (
    r"(?i),\s*(syndrome|maladie|ulcère|signe|opération|réaction|test"
    r"|épreuve|phénomène|loi|bacille|corps)\s+(de|d')\b"
)

_avec_parentheses = _normalisables.filter(pl.col("normalise").str.contains(r"\("))
_eponymes = _normalisables.filter(pl.col("texte").str.contains(RE_EPONYME_INVERSE))
print(f"Normalisables                       : {_normalisables.height:,}".replace(",", " "))
print(
    f"  → parenthèses résiduelles         : {_avec_parentheses.height:,}"
    f" ({_avec_parentheses.height / _normalisables.height:.1%})".replace(",", " ")
)
print(
    f"  → inversion d'éponyme détectable  : {_eponymes.height:,}"
    f" ({_eponymes.height / _normalisables.height:.1%})".replace(",", " ")
)
_eponymes.select("code", "texte", "normalise").head(8)

# %% [markdown]
# ### Bilan chiffré de la R3 révisée
#
# La R3 révisée combine les deux mécanismes : **normaliser** ce qui est
# récupérable, **écarter** le reste. Trois issues possibles par entrée :
#
# - `normalisee` : forme à 1-2 segments sans renvoi → réécrite au rendu ;
# - `ecartee` : renvoi ou 3+ segments → hors de la section Formulations ;
# - `conservee_telle_quelle` : n'existe pas dans cette variante, toute
#   entrée normalisable étant réécrite (même quand la normalisation est
#   l'identité, cas des entrées déjà propres comme « Dysurie »).
#
# On la compare aux deux variantes purement exclusives de la section (e).

# %% (f) Comparaison des trois politiques R3
_total_index = index_norm.height
_n_normalisee = _normalisables.height
_n_ecartee = _total_index - _n_normalisee

# Parmi les normalisées, celles dont la normalisation ne change rien.
_identiques = _normalisables.filter(
    pl.col("normalise") == pl.col("texte").str.to_lowercase()
).height

pl.DataFrame(
    [
        {
            "politique": "détecteur 3 motifs (exclusion seule)",
            "gardees": index_lignes.filter(~pl.col("chemin_index")).height,
            "ecartees": index_lignes.filter(pl.col("chemin_index")).height,
            "normalisees": 0,
        },
        {
            "politique": "détecteur strict (exclusion seule)",
            "gardees": index_lignes.filter(~pl.col("chemin_index_strict")).height,
            "ecartees": index_lignes.filter(pl.col("chemin_index_strict")).height,
            "normalisees": 0,
        },
        {
            "politique": "R3 révisée (normalisation + exclusion)",
            "gardees": _n_normalisee,
            "ecartees": _n_ecartee,
            "normalisees": _n_normalisee - _identiques,
        },
    ]
)

# %% (f) R3 révisée — répartition par chapitre
(
    index_norm.with_columns(
        pl.when(pl.col("normalise").is_null())
        .then(pl.lit("ecartee"))
        .otherwise(pl.lit("normalisee"))
        .alias("issue")
    )
    .group_by("chapitre", "issue")
    .len()
    .pivot(on="issue", index="chapitre", values="len")
    .fill_null(0)
    .with_columns(
        (pl.col("normalisee") / (pl.col("normalisee") + pl.col("ecartee")))
        .round(3)
        .alias("part_normalisee")
    )
    .sort("part_normalisee", descending=True)
)

# %% [markdown]
# ### Ce qu'il reste à trancher
#
# La R3 révisée **récupère 13 220 entrées** que les deux détecteurs
# purement exclusifs jetaient (ils n'en gardaient que 5 424 et 1 193).
# Le gain en information est donc substantiel — mais il n'a de valeur
# que si la qualité suit, et la relecture donne aujourd'hui environ deux
# tiers de formes `degradee`.
#
# Trois décisions, dans l'ordre :
#
# 1. **Étendre le retrait aux parenthèses qualifiantes ?** C'est le
#    levier n°1 : il concerne la moitié des normalisations. Il fait
#    perdre de l'information (`(chronique)`, `(aigu)`) mais produit des
#    formulations réellement utilisables.
# 2. **Exclure les inversions d'éponymes**, détectables par motif
#    (~4 % des normalisables), ou les **inverser** explicitement — le
#    second segment y est la tête.
# 3. **Seuil d'acceptation** : quelle proportion de `degradee` est
#    tolérable pour une section « formulations alternatives » dont le
#    rôle est d'élargir le rappel, pas de fournir un libellé officiel ?
#
# Tant que ces trois points ne sont pas tranchés, **R3 reste non figée**.

# %% [markdown]
# ## (g) Normalisateur v2 — les deux corrections décidées
#
# Décisions du 2026-08-12, appliquées ici.
#
# ### 1. Retrait complet des parenthèses qualifiantes
#
# Ce n'est **pas une approximation** mais l'application de la sémantique
# officielle de l'index. Les conventions du **volume 3 de la CIM-10**
# posent que les termes entre parenthèses sont des **modificateurs non
# essentiels** (*non-essential modifiers*) : leur présence ou leur
# absence **ne change pas l'affectation du code**. Ils servent à faire
# reconnaître l'entrée au codeur qui cherche, pas à la définir.
#
# Les retirer restitue donc le terme d'index dans sa forme minimale
# affectante — ce que le volume 3 considère lui-même comme le noyau de
# l'entrée. Le v1 ne retirait que les connecteurs de liaison, laissant
# « abcès (embolique) (infectieux) (multiple) (pyogène) (septique)
# sous-dural » ; le v2 rend « abcès sous-dural ».
#
# ### 2. Inversion des éponymes, strictement bornée
#
# Restreinte au motif **« second segment se terminant par `de` / `d'` /
# `du` / `des` »**, qui signale sans ambiguïté que la tête du terme est
# dans ce second segment. On recolle alors `segment 2 + segment 1`.
# Tout autre motif d'inversion **reste écarté** — on ne devine pas.
#
# ```
# « Lipschütz, ulcère de »  → « ulcère de Lipschütz »
# « Eberth, maladie d' »    → « maladie d'Eberth »   (élision, pas d'espace)
# ```
#
# ### 3. Minuscule initiale épargnant les noms propres
#
# Le v1 minusculisait systématiquement, ce qui abîmait les noms de genre
# (`Borrelia`, `Stellantchasmus`) et les éponymes non inversés.
#
# Le discriminant retenu est **le corpus lui-même** : on ne minusculise
# le premier mot que s'il apparaît **en minuscule ailleurs dans le CSV,
# hors Index**. La justification est structurelle — l'Index capitalise
# *toute* tête d'entrée par convention éditoriale, il ne peut donc pas
# témoigner de la casse naturelle d'un terme ; les autres sources
# (CepiDc, AP-HP, OFS, ANS) sont du texte médical courant, où les noms
# communs sont en minuscule et les genres et éponymes capitalisés.
#
# Effet : `rectite`, `dysurie` sont minusculisés ; `Borrelia`,
# `Stellantchasmus`, `Lipschütz`, `Eberth` sont préservés. Le coût est
# qu'un terme commun rare, absent des autres sources, garde sa capitale
# initiale (`Dactylite tuberculeuse`) — une casse de phrase, sans gravité.

# %% Fonction — vocabulaire des minuscules attestées hors Index
def vocabulaire_minuscules(df: pl.DataFrame) -> set[str]:
    """Mots attestés en minuscule dans les sources **hors Index**.

    Sert de test de « nom commun » : l'Index capitalise toute tête
    d'entrée, il ne peut donc pas servir de témoin de casse.
    """
    tokens = (
        df.filter(pl.col("source") != cards.FORMULATION_SOURCE_INDEX)
        .select(pl.col("texte").str.split(" ").alias("mot"))
        .explode("mot")
        .select(pl.col("mot").str.strip_chars(",;()\"").alias("mot"))
    )
    return set(
        tokens.filter(pl.col("mot").str.contains(r"^[a-zà-ÿ][\wà-ÿ-]*$"))["mot"].to_list()
    )


VOCAB_MINUSCULES = vocabulaire_minuscules(flat)
print(f"Mots attestés en minuscule hors Index : {len(VOCAB_MINUSCULES):,}".replace(",", " "))

# %% Fonction — normalisateur v2
RE_PARENTHESE = re.compile(r"\s*\([^()]*\)")
#: Second segment se terminant par une préposition : sa tête est le
#: terme, le premier segment est l'éponyme.
RE_EPONYME = re.compile(r"(?i)(?:^|\s)(de|d'|du|des)$")


def minuscule_initiale(texte: str) -> str:
    """Minuscule initiale, sauf si le premier mot n'est pas attesté en
    minuscule hors Index (présomption de nom propre)."""
    if not texte:
        return texte
    premier = texte.split(" ")[0].strip(",;()")
    if premier.lower() in VOCAB_MINUSCULES:
        return texte[0].lower() + texte[1:]
    return texte


def normalise_v2(texte: str | None) -> str | None:
    """Forme normalisée d'une entrée Index, ou None si hors périmètre.

    Hors périmètre : renvois « voir », formes à 3 segments ou plus.
    """
    if not texte or RE_RENVOI.search(texte):
        return None
    segments = [s.strip() for s in texte.split(",")]
    if len(segments) > 2:
        return None
    segments = [re.sub(r"\s+", " ", RE_PARENTHESE.sub("", s)).strip() for s in segments]
    segments = [s for s in segments if s]
    if not segments:
        return None
    if len(segments) == 2 and (m := RE_EPONYME.search(segments[1])):
        # Élision : « maladie d' » + « Eberth » se recolle sans espace.
        separateur = "" if m.group(1).endswith("'") else " "
        sortie = f"{segments[1]}{separateur}{segments[0]}"
    else:
        sortie = " ".join(segments)
    sortie = re.sub(r"\s+", " ", sortie).strip(" ,;")
    return minuscule_initiale(sortie) or None


for _ex in (
    "Rectite (à), amibienne",
    "Abcès (embolique) (infectieux) (septique) (de), sous-dural",
    "Lipschütz, ulcère de",
    "Eberth, maladie d'",
    "Borrelia vincenti, infection (amygdales)",
    "Stellantchasmus falcatus",
):
    print(f"{_ex!r:58} → {normalise_v2(_ex)!r}")

# %% (g) Périmètre et effet du v2
index_v2 = index_formes.with_columns(
    pl.col("texte").map_elements(normalise_v2, return_dtype=pl.String).alias("normalise_v2")
)
_v2 = index_v2.filter(pl.col("normalise_v2").is_not_null())
_resid = _v2.filter(pl.col("normalise_v2").str.contains(r"\(")).height
_inv = _v2.filter(pl.col("texte").str.contains(RE_EPONYME_INVERSE)).height
print(f"Normalisables               : {_v2.height:,}".replace(",", " "))
print(f"  parenthèses résiduelles   : {_resid}")
print(f"  inversions d'éponyme      : {_inv}")

# %% [markdown]
# ### Échantillon de 100 normalisations — graine distincte
#
# Tirage `seed=2025`, **distinct du tirage de la section (f)** pour ne
# pas relire les mêmes entrées. Les étiquettes ci-dessous sont une
# **lecture préliminaire**, à confirmer ou corriger.
#
# Critère d'acceptation fixé : **zéro `fautive`** et **au plus 10 % de
# `degradee`**.

# %% (g) Échantillon de 100 — étiquettes préliminaires
ECHANTILLON_V2_GRAINE = 2025

#: Lecture préliminaire. Défaut = `correcte` ; seuls les écarts sont listés.
RELECTURE_V2: dict[str, str] = {
    # Sens changé, inversé, ou chaîne inintelligible.
    "Q95.5": "fautive",   # « Autosome site fragile » — tête inversée, motif non couvert
    "Q97.1": "fautive",   # « Xxxx syndrome » — idem (caryotype 48,XXXX)
    "Z76.2": "fautive",   # « Nca bien portant » — « Nca » est une abréviation d'index
    # Compréhensible, mais préposition de liaison manquante ou reliquat.
    **dict.fromkeys(
        [
            "A03.9", "A16.8", "A32.7", "A69.1", "A98.2", "B57.3", "B73", "B75",
            "E70.1", "G43.8", "H47.4", "H50.6", "I51.3", "I74.9", "J33.0",
            "K06.1", "K25.5", "K31.8", "K62.8", "L81.4", "N48.6", "O86.4",
            "P25.8", "P96.9", "Q00.0", "Q02", "Q04.0", "Q12.9", "Q25.2",
            "Q25.7", "Q62.4", "Q62.6", "Q70.9", "Q72.5", "R39.1", "S30.1",
            "T74.8", "Z12.4", "Z89.4",
        ],
        "degradee",
    ),
}

echantillon_v2 = (
    _v2.select("code", "texte", "normalise_v2")
    .sample(n=100, seed=ECHANTILLON_V2_GRAINE, shuffle=True)
    .sort("code")
    .with_columns(
        pl.col("code").replace_strict(RELECTURE_V2, default="correcte").alias("etiquette")
    )
)
_bilan = echantillon_v2.group_by("etiquette").len().sort("len", descending=True)
print(_bilan)
_n = echantillon_v2.height
_n_faut = echantillon_v2.filter(pl.col("etiquette") == "fautive").height
_n_deg = echantillon_v2.filter(pl.col("etiquette") == "degradee").height
print(f"\nSeuil « zéro fautive »      : {_n_faut} → {'ATTEINT' if _n_faut == 0 else 'NON ATTEINT'}")
print(f"Seuil « ≤ 10 % dégradées »  : {_n_deg / _n:.0%} → {'ATTEINT' if _n_deg / _n <= 0.10 else 'NON ATTEINT'}")

# %% (g) Le détail, pour relecture
echantillon_v2.select("code", "texte", "normalise_v2", "etiquette")

# %% [markdown]
# ### Diagnostic — pourquoi le seuil n'est pas atteint
#
# Progrès net par rapport au v1 (sur 50 : 22 % correctes, 66 %
# dégradées, 12 % fautives). Mais **les deux seuils restent manqués**,
# et pour des raisons distinctes et toutes deux traitables.
#
# **Les 3 fautives résiduelles relèvent d'un même manque** : le second
# segment est la tête du terme, mais **sans préposition finale**, donc
# hors du motif d'inversion. « Autosome, site fragile » et
# « Xxxx, syndrome » appellent la même inversion que les éponymes.
# La troisième, « Nca, bien portant », a pour premier segment une
# **abréviation d'index** (`nca` = non classé ailleurs) et n'est pas un
# terme du tout. Deux correctifs possibles, conformes à la consigne
# « corrigée par motif ou versée aux exclusions » :
#
# 1. élargir l'inversion aux seconds segments réduits à un **substantif
#    de tête nu** (`syndrome`, `site`, `maladie`…) ;
# 2. **exclure** les entrées dont le premier segment est une abréviation
#    d'index (`nca`, `sai`).
#
# **Les 40 % de dégradées ont une cause unique et très concentrée** : la
# **préposition de liaison manquante**. « Hypoplasie (de), cerveau »
# rend « hypoplasie cerveau » là où le français demande « hypoplasie du
# cerveau ». Or **l'information nécessaire est dans la source** : le
# `(de)` retiré indiquait précisément la liaison à employer.
#
# C'est la limite du choix « retrait complet » appliqué uniformément :
# il est juste pour les modificateurs *qualifiants* (`(chronique)`,
# `(aigu)`), qui sont bien non essentiels au sens du volume 3, mais les
# connecteurs *de liaison* ne sont pas des modificateurs — ce sont des
# marqueurs de rection grammaticale. Les **consommer comme joint** au
# lieu de les supprimer traiterait la quasi-totalité des dégradées :
#
# ```
# « Hypoplasie (de), cerveau »   → « hypoplasie du cerveau »
# « Perforation (de), estomac »  → « perforation de l'estomac »
# « Carence (en), phénylalanine » → « carence en phénylalanine »
# ```
#
# Cela suppose une contraction (`de` + `le` → `du`) et une élision
# (`de` + voyelle → `de l'`), toutes deux déterministes en français.
# **C'est le correctif à instruire au prochain tour** ; il n'est pas
# appliqué ici, la consigne étant le retrait complet.

# %% (g) Bilan global révisé, par chapitre
bilan_r3 = (
    index_v2.with_columns(
        pl.when(pl.col("normalise_v2").is_null())
        .then(pl.lit("ecartee"))
        .when(pl.col("normalise_v2") == pl.col("texte"))
        .then(pl.lit("conservee_telle_quelle"))
        .otherwise(pl.lit("normalisee"))
        .alias("issue")
    )
    .group_by("chapitre", "issue")
    .len()
    .pivot(on="issue", index="chapitre", values="len")
    .fill_null(0)
)
_cols_issue = [
    c for c in ("normalisee", "conservee_telle_quelle", "ecartee") if c in bilan_r3.columns
]
(
    bilan_r3.select(["chapitre", *_cols_issue])
    .with_columns(pl.sum_horizontal(_cols_issue).alias("total"))
    .with_columns(
        (pl.col("normalisee") / pl.col("total")).round(3).alias("part_normalisee")
    )
    .sort("total", descending=True)
)

# %% (g) Bilan global révisé, toutes politiques confondues
pl.DataFrame(
    [
        {
            "politique": "détecteur 3 motifs (exclusion seule)",
            "conservees": index_lignes.filter(~pl.col("chemin_index")).height,
            "normalisees": 0,
            "ecartees": index_lignes.filter(pl.col("chemin_index")).height,
        },
        {
            "politique": "détecteur strict (exclusion seule)",
            "conservees": index_lignes.filter(~pl.col("chemin_index_strict")).height,
            "normalisees": 0,
            "ecartees": index_lignes.filter(pl.col("chemin_index_strict")).height,
        },
        {
            "politique": "R3 v1 (connecteurs de liaison seuls)",
            "conservees": _identiques,
            "normalisees": _n_normalisee - _identiques,
            "ecartees": _n_ecartee,
        },
        {
            "politique": "R3 v2 (parenthèses complètes + éponymes)",
            "conservees": _v2.filter(pl.col("normalise_v2") == pl.col("texte")).height,
            "normalisees": _v2.filter(pl.col("normalise_v2") != pl.col("texte")).height,
            "ecartees": index_v2.height - _v2.height,
        },
    ]
)

# %% [markdown]
# ## (h) Normalisateur v3 — connecteurs consommés comme joints
#
# Amendement du 2026-08-12 à la décision 1, issu du diagnostic du v2.
#
# **Les connecteurs de liaison ne sont pas des modificateurs.** Le
# volume 3 qualifie de non essentiels les termes parenthésés
# *qualifiants* — et ceux-là se retirent. Mais `(de)`, `(à)`, `(en)`
# sont des **marqueurs de rection grammaticale** : ils indiquent
# comment le terme se construit. Les supprimer **détruisait une
# information présente dans la source**, d'où les 40 % de formes
# dégradées du v2 (« hypoplasie cerveau » au lieu de « hypoplasie du
# cerveau »).
#
# Le v3 les **consomme comme joint**, avec contraction (`de + le → du`,
# `de + les → des`) et élision (`de` + voyelle ou h muet → `de l'`).
#
# ### D'où vient le genre ?
#
# `de + le → du` suppose de connaître le genre du nom — que la source ne
# donne pas. On l'obtient **du corpus lui-même** : on relève dans tout
# le CSV les rections attestées (`du cerveau`, `de la rate`,
# `de l'estomac`) et on retient la forme majoritaire.
#
# Ce même mécanisme rend un second service, décisif : **un adjectif
# n'est jamais précédé d'un article**. L'absence d'attestation vaut donc
# signal qu'il ne faut *pas* insérer de joint — c'est ce qui évite
# « rectite à l'amibienne » et « abcès de sous-dural ».

# %% Fonction — lexique des rections attestées
# Deux motifs : les formes élidées s'attachent au mot suivant
# (« de l'estomac »), les autres en sont séparées par une espace. Un
# motif unique en `\s+` ne verrait jamais les élisions.
RE_RECTION_ESPACE = re.compile(r"\b(du|de la|des|de|au|à la|aux|à)\s+([a-zà-ÿ][\wà-ÿ-]{2,})")
RE_RECTION_ELIDEE = re.compile(r"\b(de l'|à l')\s*([a-zà-ÿ][\wà-ÿ-]{2,})")

FAMILLE_DE = ("du", "de la", "de l'", "des", "de")
FAMILLE_A = ("au", "à la", "à l'", "aux", "à")


def lexique_rections(df: pl.DataFrame) -> dict[str, Counter]:
    """Pour chaque nom, les joints attestés dans le corpus et leur compte."""
    lexique: dict[str, Counter] = defaultdict(Counter)
    for texte in df["texte"].drop_nulls().to_list():
        bas = texte.lower()
        for motif in (RE_RECTION_ESPACE, RE_RECTION_ELIDEE):
            for joint, nom in motif.findall(bas):
                lexique[nom][joint] += 1
    return lexique


LEXIQUE_RECTIONS = lexique_rections(flat)
print(f"Noms avec au moins une rection attestée : {len(LEXIQUE_RECTIONS):,}".replace(",", " "))
for _nom in ("cerveau", "rate", "estomac", "amibienne", "sous-dural"):
    print(f"  {_nom:12} → {dict(LEXIQUE_RECTIONS.get(_nom, {}))}")

# %% Fonction — choix du joint
RE_VOYELLE = re.compile(r"^[aàâeéèêëiîïoôuùûyh]", re.IGNORECASE)


def _rection_attestee(nom: str, famille: tuple[str, ...]) -> str | None:
    """Forme majoritaire attestée, ou None. La forme nue (« de », « à »)
    ne concourt pas : c'est le repli, pas un témoignage de rection."""
    compte = LEXIQUE_RECTIONS.get(nom.lower())
    if not compte:
        return None
    candidats = [(n, j) for j, n in compte.items() if j in famille[:-1]]
    if not candidats:
        return None
    n, joint = max(candidats)
    return joint if n >= 2 else None


def joint_pour(connecteur: str, suite: str) -> str | None:
    """Joint à insérer, ou None s'il ne faut pas en insérer."""
    # Un second segment portant déjà sa propre rection (« syndrome du
    # choc toxique ») est un groupe nominal complet : lui ajouter un
    # joint externe produit un non-sens.
    if re.search(r"\s(du|de la|de l'|des|de|au|à la|à l'|aux|à)\s", f" {suite.lower()} "):
        return None
    tete = suite.split(" ")[0].strip("',;")
    cle = connecteur.lower()
    if cle.startswith(("de", "du", "des", "d'", "dû", "due", "dus")):
        return _rection_attestee(tete, FAMILLE_DE)
    if cle in ("à", "au", "aux"):
        return _rection_attestee(tete, FAMILLE_A)
    # Connecteurs littéraux (« avec », « par », « en »…) : on exige la
    # même preuve de nature nominale. Le test rate quelques noms rares
    # (« en disaccharidase »), mais il transforme une fautive
    # potentielle (« problème avec psycho-social ») en simple dégradée —
    # l'asymétrie du critère d'acceptation le commande.
    if _rection_attestee(tete, FAMILLE_DE) or _rection_attestee(tete, FAMILLE_A):
        return cle
    return None


# %% Fonction — normalisateur v3
CONNECTEURS_TOUS = (
    *CONNECTEURS_LIAISON, "dû à", "due à", "dues à", "dus à",
)
RE_PAREN_CAPTURE = re.compile(r"\(([^()]*)\)")

#: Substantifs de tête nus autorisant l'inversion sans préposition
#: finale. Liste **volontairement courte** : tout cas douteux est
#: écarté, jamais normalisé.
TETES_NUES = frozenset({"syndrome", "maladie", "site fragile"})

#: Abréviations d'index en tête d'entrée : ce ne sont pas des termes.
ABREVIATIONS_INDEX = frozenset({"nca", "sai"})

JOINTS_APPLIQUES: Counter = Counter()


def _colle(gauche: str, joint: str, droite: str) -> str:
    """Recolle avec l'espacement correct : les élisions s'attachent."""
    JOINTS_APPLIQUES[joint] += 1
    separateur = "" if joint.endswith("'") else " "
    return f"{gauche} {joint}{separateur}{droite}".strip()


def _nettoie_segment(segment: str) -> tuple[str, str | None]:
    """(texte nettoyé, connecteur laissé en attente pour le recollement)."""
    morceaux: list[str] = []
    attente: str | None = None
    reste = segment
    while m := RE_PAREN_CAPTURE.search(reste):
        avant, contenu, apres = reste[: m.start()], m.group(1).strip(), reste[m.end() :]
        morceaux.append(avant)
        if contenu.lower() in CONNECTEURS_TOUS:
            # Le connecteur n'est « suivi » que par du vrai texte : les
            # parenthèses restantes ne comptent pas.
            suite = RE_PAREN_CAPTURE.sub("", apres).strip(" ,;")
            if suite:
                if joint := joint_pour(contenu, suite):
                    gauche = re.sub(r"\s+", " ", "".join(morceaux)).strip(" ,;")
                    droite = re.sub(r"\s+", " ", apres).strip(" ,;")
                    return _colle(gauche, joint, droite), None
                # Pas de joint pour ce connecteur : on laisse sa chance
                # au suivant plutôt que de renoncer.
            else:
                attente = contenu
        reste = apres
    morceaux.append(reste)
    return re.sub(r"\s+", " ", "".join(morceaux)).strip(" ,;"), attente


def normalise_v3(texte: str | None) -> str | None:
    """Forme normalisée, ou None si l'entrée doit être écartée."""
    if not texte or RE_RENVOI.search(texte):
        return None
    segments = [s.strip() for s in texte.split(",")]
    if len(segments) > 2:
        return None
    if segments[0].strip("()").lower() in ABREVIATIONS_INDEX:
        return None
    nettoyes, attentes = [], []
    for s in segments:
        net, att = _nettoie_segment(s)
        nettoyes.append(net)
        attentes.append(att)
    utiles = [n for n in nettoyes if n]
    if not utiles:
        return None
    if len(utiles) == 1:
        return minuscule_initiale(utiles[0]) or None
    s1, s2 = utiles[0], utiles[1]
    if RE_EPONYME.search(s2):                                   # « …, ulcère de »
        sep = "" if s2.rstrip().endswith("'") else " "
        return minuscule_initiale(f"{s2}{sep}{s1}") or None
    if s2.lower() in TETES_NUES:                                # « …, syndrome »
        return minuscule_initiale(f"{s2} {s1}") or None
    if s1.split(" ")[0].strip(",;()").lower() not in VOCAB_MINUSCULES:
        return None                                             # tête douteuse → écartée
    if attentes[0] and (joint := joint_pour(attentes[0], s2)):
        return minuscule_initiale(_colle(s1, joint, s2)) or None
    return minuscule_initiale(f"{s1} {s2}") or None


for _ex in (
    "Hypoplasie (de), cerveau",
    "Perforation (non traumatique) (de) (due à), estomac",
    "Rectite (à), amibienne",
    "Maladie (à) (de) pancréas",
    "Autosome, site fragile",
    "Xxxx, syndrome",
    "Nca, bien portant",
    "Borrelia vincenti, infection (amygdales)",
    "Problème (avec) (de), psycho-social",
):
    print(f"{_ex!r:56} → {normalise_v3(_ex)!r}")

# %% (h) Périmètre du v3 et distribution des joints
JOINTS_APPLIQUES.clear()
index_v3 = index_formes.with_columns(
    pl.col("texte").map_elements(normalise_v3, return_dtype=pl.String).alias("normalise_v3")
)
_v3 = index_v3.filter(pl.col("normalise_v3").is_not_null())
print(f"Normalisables v3 : {_v3.height:,}  (v2 : 13 220)".replace(",", " "))
print(f"Écartées         : {index_v3.height - _v3.height:,}".replace(",", " "))
print("\nDistribution des joints appliqués — contrôle de vraisemblance :")
pl.DataFrame(
    [{"joint": j, "occurrences": n} for j, n in JOINTS_APPLIQUES.most_common()]
)

# %% [markdown]
# La distribution est un bon test de vraisemblance : `du` et `de la`
# dominent, `de l'` suit, `des` reste minoritaire — c'est la répartition
# attendue des rections nominales en français médical. Un excès de
# `de l'` aurait signalé une élision appliquée à l'aveugle ; un excès de
# `de` nu aurait signalé un lexique de rections trop pauvre.

# %% [markdown]
# ### Échantillon de 100 — troisième tirage
#
# Graine `777`, distincte des deux précédentes. Seuils inchangés :
# **zéro `fautive`**, **au plus 10 % de `degradee`**.

# %% (h) Échantillon v3 — étiquettes préliminaires
ECHANTILLON_V3_GRAINE = 777

#: Lecture préliminaire. Défaut = `correcte` ; seuls les écarts sont listés.
#: Toutes les dégradées relèvent d'une même cause : un joint non inséré
#: faute de rection attestée pour un nom rare, ou un reliquat « nca ».
#: Clé = **texte source**, unique dans le tirage — le code ne l'est pas
#: (une même catégorie peut porter plusieurs entrées d'index).
RELECTURE_V3: dict[str, str] = dict.fromkeys(
    [
        "Abcès (embolique) (infectieux) (multiple) (pyogène) (septique) (de), psoas (évolutif) (tuberculeux)",
        "Septicémie (avec suppuration) (généralisée) (à), syndrome du choc toxique",
        "Infection (à) (de), colibacille nca",
        "Fièvre (de) (des) (due à), volhynie",
        "Fièvre (de) (des) (due à), tahyna",
        "Vaginite (aiguë) (due à), enterobius vermicularis (oxyure)",
        "Infection (à) (de), oesophagostomum (apiostomum)",
        "Dysglobulinémie, associée à dyscrasie lymphoplasmocytaire (m9765/1)",
        "Anémie (à) (de), lederer (hémolytique)",
        "Tétanie, associée à rachitisme",
        "Carence (en), disaccharidase",
        "Ligne(s) (de), stähli",
        "Pneumoconiose (des) (due à), béryllium",
        "Pleurésie (aiguë) (chronique) (double) (fibrineuse) (sèche) (subaiguë) (à), streptocoques",
        "Prolapsus (de), colostomie",
        "Anomalie (congénitale) (type non précisé) (de), vessie nca",
        "Anomalie (congénitale) (type non précisé) (de), albumine",
        "Plaie(s) (coupure) (lacération) (morsure d'animal) (avec corps étranger pénétrant), cuir chevelu",
        "Plaie(s) (coupure) (lacération) (morsure d'animal) (avec corps étranger pénétrant), nasale ou nez (cloison)",
        "Complications (de) (dues à), tuteur urinaire",
    ],
    "degradee",
)

echantillon_v3 = (
    _v3.select("code", "texte", "normalise_v3")
    .sample(n=100, seed=ECHANTILLON_V3_GRAINE, shuffle=True)
    .sort("code")
    .with_columns(
        pl.col("texte").replace_strict(RELECTURE_V3, default="correcte").alias("etiquette")
    )
)
print(echantillon_v3.group_by("etiquette").len().sort("len", descending=True))
_nf = echantillon_v3.filter(pl.col("etiquette") == "fautive").height
_nd = echantillon_v3.filter(pl.col("etiquette") == "degradee").height
print(f"\nSeuil « zéro fautive »     : {_nf} → {'ATTEINT' if _nf == 0 else 'NON ATTEINT'}")
print(f"Seuil « ≤ 10 % dégradées » : {_nd}% → {'ATTEINT' if _nd <= 10 else 'NON ATTEINT'}")

# %% (h) Le détail, pour relecture
echantillon_v3.select("code", "texte", "normalise_v3", "etiquette")

# %% [markdown]
# ### Où l'on en est
#
# | Étiquette | v1 (50) | v2 (100) | **v3 (100)** | Seuil |
# |---|---|---|---|---|
# | `correcte` | 22 % | 57 % | **80 %** | — |
# | `degradee` | 66 % | 40 % | **20 %** | ≤ 10 % |
# | `fautive` | 12 % | 3 % | **0** | 0 ✅ |
#
# **Le seuil « zéro fautive » est atteint.** Les trois correctifs ont
# fonctionné : l'inversion élargie traite « Autosome, site fragile » et
# « Xxxx, syndrome », l'exclusion des abréviations retire
# « Nca, bien portant », et le gardefou sur les groupes nominaux
# complets évite « septicémie au syndrome du choc toxique ».
#
# **Le seuil des dégradées ne l'est pas** (20 % contre ≤ 10 %), et la
# cause est unique et bien identifiée : le **joint non inséré faute de
# rection attestée**. Les noms concernés sont rares ou techniques et
# absents des sources hors Index — `psoas`, `colibacille`, `béryllium`,
# `streptocoques`, `colostomie`, `albumine`, `cuir chevelu`,
# `tuteur urinaire`. S'y ajoute un reliquat mineur, l'abréviation `nca`
# en fin d'entrée.
#
# Deux leviers pour un tour suivant, à arbitrer :
#
# 1. **Élargir le lexique de rections** en y admettant l'Index lui-même.
#    C'est légitime pour la *rection* — « du psoas » y est fiable même si
#    la capitalisation de l'Index ne l'est pas. À ne surtout pas
#    confondre avec le vocabulaire de casse, qui doit rester hors Index.
# 2. **Retirer les abréviations d'index en fin d'entrée** (`nca`, `sai`),
#    et pas seulement en tête.

# %% (h) Bilan global v3, par chapitre
bilan_v3 = (
    index_v3.with_columns(
        pl.when(pl.col("normalise_v3").is_null())
        .then(pl.lit("ecartee"))
        .when(pl.col("normalise_v3") == pl.col("texte"))
        .then(pl.lit("conservee"))
        .otherwise(pl.lit("normalisee"))
        .alias("issue")
    )
    .group_by("chapitre", "issue")
    .len()
    .pivot(on="issue", index="chapitre", values="len")
    .fill_null(0)
)
_c3 = [c for c in ("normalisee", "conservee", "ecartee") if c in bilan_v3.columns]
(
    bilan_v3.select(["chapitre", *_c3])
    .with_columns(pl.sum_horizontal(_c3).alias("total"))
    .with_columns((pl.col("normalisee") / pl.col("total")).round(3).alias("part_normalisee"))
    .sort("total", descending=True)
)

# %% (h) Bilan global v3, toutes politiques
pl.DataFrame(
    [
        {
            "politique": "détecteur 3 motifs (exclusion seule)",
            "conservees": index_lignes.filter(~pl.col("chemin_index")).height,
            "normalisees": 0,
            "ecartees": index_lignes.filter(pl.col("chemin_index")).height,
        },
        {
            "politique": "R3 v2 (parenthèses complètes + éponymes)",
            "conservees": _v2.filter(pl.col("normalise_v2") == pl.col("texte")).height,
            "normalisees": _v2.filter(pl.col("normalise_v2") != pl.col("texte")).height,
            "ecartees": index_v2.height - _v2.height,
        },
        {
            "politique": "R3 v3 (joints + inversion élargie + exclusions)",
            "conservees": _v3.filter(pl.col("normalise_v3") == pl.col("texte")).height,
            "normalisees": _v3.filter(pl.col("normalise_v3") != pl.col("texte")).height,
            "ecartees": index_v3.height - _v3.height,
        },
    ]
)

# %% [markdown]
# ## (i) Normalisateur v4 — et pourquoi un des deux leviers était vide
#
# ### ⚠ Piège n°4 — deux lexiques, à ne jamais fusionner
#
# Le normalisateur s'appuie sur **deux lexiques tirés du corpus, dont
# les périmètres sont volontairement différents**. Un repreneur pressé
# les fusionnera « par simplification ». Il ne faut pas.
#
# | Lexique | Périmètre | Pourquoi |
# |---|---|---|
# | **Rections** (`du X`, `de la X`…) | **Index inclus** | La *syntaxe interne* des entrées d'index est du français naturel : « hypertrophie adénofibromateuse **de la** prostate ». Elle témoigne valablement du genre. |
# | **Casse** (mots vus en minuscule) | **Index exclu** | L'Index capitalise **toute tête d'entrée** par convention éditoriale. Il ne peut donc pas dire si un mot est un nom commun ou un nom propre — c'est exactement le test qu'on lui demande. |
#
# Les fusionner dans un sens (Index partout) fait minusculiser
# `Borrelia` et `Lipschütz` ; dans l'autre (Index nulle part) prive le
# lexique de rections de 265 noms. Les deux périmètres sont chacun
# justifiés par une propriété différente de la même source.
#
# ### Le levier « étendre les rections à l'Index » était déjà en place
#
# Vérification faite avant d'implémenter : `lexique_rections` était
# construit sur `flat`, **toutes sources confondues** — l'Index y était
# donc déjà admis. Le levier n° 1 annoncé au tour précédent était
# **sans objet**, et je le signale plutôt que de le maquiller.
#
# Le contrôle chiffré le confirme : l'Index n'apporte que **265 noms**
# au lexique (5 673 contre 5 408), et **aucune** des têtes qui bloquaient
# — `psoas`, `colibacille`, `volhynie`, `tahyna`, `lederer`,
# `disaccharidase`, `oesophagostomum`, `enterobius` n'ont d'attestation
# nulle part, Index compris.
#
# ### Les deux leviers qui marchent réellement
#
# En cherchant *pourquoi* ces têtes bloquaient, deux causes distinctes
# sont apparues, toutes deux dans la fonction de choix du joint :
#
# 1. **La forme nue (`de`, `à`) était exclue de la compétition.** Elle
#    l'était pour une bonne raison — c'est le repli, pas un témoignage
#    de rection — mais du coup `streptocoques` (`à` attesté 15 fois) ou
#    `stähli` (`de`, 3 fois) n'obtenaient aucun joint. Elle est
#    désormais admise **en dernier recours seulement**, après les formes
#    contractées, et avec un seuil plus exigeant.
# 2. **Le seuil de 2 attestations était trop haut** pour les formes
#    contractées, qui portent le genre : `béryllium` (`du`, 1 fois),
#    `albumine` (`de l'`, 1 fois) tombaient juste en dessous. Seuil
#    ramené à 1 pour elles.
#
# **Contrôle de sûreté** avant d'appliquer : les dix adjectifs testés
# (`amibienne`, `sous-dural`, `psycho-social`, `tuberculeuse`,
# `solaire`, `hypostatique`, `récidivante`, `superficielle`,
# `congénitale`, `fébrile`) n'ont **aucune** attestation, pas même de la
# forme nue. Les deux leviers ne rouvrent donc pas la porte aux joints
# devant adjectif.

# %% Fonction — choix du joint, v4
def _rection_attestee_v4(nom: str, famille: tuple[str, ...]) -> str | None:
    """Forme contractée d'abord (seuil 1), forme nue en dernier (seuil 2).

    L'ordre compte : « cuir » est attesté `du` 36 fois et `de` 98 fois,
    mais c'est `du cuir chevelu` qu'il faut produire. La forme
    contractée porte le genre ; la forme nue n'est qu'un repli.
    """
    compte = LEXIQUE_RECTIONS.get(nom.lower())
    if not compte:
        return None
    contractees = [(n, j) for j, n in compte.items() if j in famille[:-1]]
    if contractees:
        return max(contractees)[1]
    return famille[-1] if compte.get(famille[-1], 0) >= 2 else None


def joint_pour_v4(connecteur: str, suite: str) -> str | None:
    """Identique au v3, mais sur `_rection_attestee_v4`."""
    if re.search(r"\s(du|de la|de l'|des|de|au|à la|à l'|aux|à)\s", f" {suite.lower()} "):
        return None
    tete = suite.split(" ")[0].strip("',;")
    cle = connecteur.lower()
    if cle.startswith(("de", "du", "des", "d'", "dû", "due", "dus")):
        return _rection_attestee_v4(tete, FAMILLE_DE)
    if cle in ("à", "au", "aux"):
        return _rection_attestee_v4(tete, FAMILLE_A)
    if _rection_attestee_v4(tete, FAMILLE_DE) or _rection_attestee_v4(tete, FAMILLE_A):
        return cle
    return None


# %% Fonction — normalisateur v4
#: Abréviations d'index, désormais retirées **en fin d'entrée** aussi,
#: et plus seulement en tête.
RE_ABREV_FIN = re.compile(r"(?i)[\s,]+(nca|sai)\s*$")

JOINTS_V4: Counter = Counter()


def _colle_v4(gauche: str, joint: str, droite: str) -> str:
    JOINTS_V4[joint] += 1
    separateur = "" if joint.endswith("'") else " "
    return f"{gauche} {joint}{separateur}{droite}".strip()


def _nettoie_segment_v4(segment: str) -> tuple[str, str | None]:
    morceaux: list[str] = []
    attente: str | None = None
    reste = segment
    while m := RE_PAREN_CAPTURE.search(reste):
        avant, contenu, apres = reste[: m.start()], m.group(1).strip(), reste[m.end() :]
        morceaux.append(avant)
        if contenu.lower() in CONNECTEURS_TOUS:
            suite = RE_PAREN_CAPTURE.sub("", apres).strip(" ,;")
            if suite:
                if joint := joint_pour_v4(contenu, suite):
                    gauche = re.sub(r"\s+", " ", "".join(morceaux)).strip(" ,;")
                    # Les parenthèses restantes de `apres` doivent être
                    # nettoyées ici aussi : ce retour court-circuite la
                    # boucle et donc le nettoyage habituel.
                    droite = re.sub(
                        r"\s+", " ", RE_PAREN_CAPTURE.sub("", apres)
                    ).strip(" ,;")
                    return _colle_v4(gauche, joint, droite), None
            else:
                attente = contenu
        reste = apres
    morceaux.append(reste)
    return re.sub(r"\s+", " ", "".join(morceaux)).strip(" ,;"), attente


def normalise_v4(texte: str | None) -> str | None:
    """Forme normalisée, ou None si l'entrée doit être écartée."""
    if not texte or RE_RENVOI.search(texte):
        return None
    segments = [s.strip() for s in texte.split(",")]
    if len(segments) > 2:
        return None
    if segments[0].strip("()").lower() in ABREVIATIONS_INDEX:
        return None
    nettoyes, attentes = [], []
    for s in segments:
        net, att = _nettoie_segment_v4(s)
        nettoyes.append(net)
        attentes.append(att)
    utiles = [n for n in nettoyes if n]
    if not utiles:
        return None

    def _fin(sortie: str) -> str | None:
        return minuscule_initiale(RE_ABREV_FIN.sub("", sortie).strip(" ,;")) or None

    if len(utiles) == 1:
        return _fin(utiles[0])
    s1, s2 = utiles[0], utiles[1]
    if RE_EPONYME.search(s2):
        sep = "" if s2.rstrip().endswith("'") else " "
        return _fin(f"{s2}{sep}{s1}")
    if s2.lower() in TETES_NUES:
        return _fin(f"{s2} {s1}")
    if s1.split(" ")[0].strip(",;()").lower() not in VOCAB_MINUSCULES:
        return None
    if attentes[0] and (joint := joint_pour_v4(attentes[0], s2)):
        return _fin(_colle_v4(s1, joint, s2))
    return _fin(f"{s1} {s2}")


for _ex in (
    "Ligne(s) (de), stähli",
    "Pleurésie (aiguë) (à), streptocoques",
    "Pneumoconiose (des) (due à), béryllium",
    "Anomalie (congénitale) (de), albumine",
    "Anomalie (congénitale) (de), vessie nca",
    "Rectite (à), amibienne",
):
    print(f"{_ex!r:48} → {normalise_v4(_ex)!r}")

# %% [markdown]
# ### Contrôle de couverture du levier
#
# Sur les **20 formes dégradées relevées au tour v3**, combien le v4
# résout-il effectivement ?

# %% (i) Couverture — les 20 dégradées du v3 repassées au v4
DEGRADEES_V3 = list(RELECTURE_V3)
_couverture = pl.DataFrame(
    [{"source": d, "v3": normalise_v3(d), "v4": normalise_v4(d)} for d in DEGRADEES_V3]
).with_columns((pl.col("v3") != pl.col("v4")).alias("modifiee_par_v4"))
_n_mod = _couverture.filter(pl.col("modifiee_par_v4")).height
print(f"Dégradées v3 modifiées par le v4 : {_n_mod} / {len(DEGRADEES_V3)}")
_couverture.filter(pl.col("modifiee_par_v4")).select("v3", "v4")

# %% (i) Périmètre v4 et distribution des joints
JOINTS_V4.clear()
index_v4 = index_formes.with_columns(
    pl.col("texte").map_elements(normalise_v4, return_dtype=pl.String).alias("normalise_v4")
)
_v4 = index_v4.filter(pl.col("normalise_v4").is_not_null())
print(f"Normalisables v4 : {_v4.height:,}  (v3 : 12 488)".replace(",", " "))
pl.DataFrame([{"joint": j, "occurrences": n} for j, n in JOINTS_V4.most_common()])

# %% [markdown]
# ### Échantillon de 100 — quatrième tirage
#
# Graine `4242`, distincte des trois précédentes.

# %% (i) Échantillon v4 — étiquettes préliminaires
ECHANTILLON_V4_GRAINE = 4242

#: Clé = texte source. Défaut = `correcte`.
RELECTURE_V4: dict[str, str] = dict.fromkeys(
    [
        "Canaliculite (due à), actinomyces",
        "Herpès (simplex) (de), orchite",
        "Fièvre (de) (des) (due à), arbovirus",
        "Carence (en), sélénium (alimentaire)",
        "Crampe (des) (due à), dactylos",
        "Encéphalite (chronique) (hémorragique) (idiopathique) (non épidémique) (subaiguë) (de) (due à), précisée nca",
        "Grand mal, crise de (avec ou sans petit mal)",
        "Paralysie (de), médullaire",
        "Phlegmon (avec lymphangite aiguë) (à) (de), orbite",
        "Deutéranomalie, deutéranopie",
        "Contusion (sans plaie) (de), hypochondre",
        "Plaie(s) (coupure) (lacération) (morsure d'animal) (avec corps étranger pénétrant), testicule",
        "Entorse (articulation) (ligament), pied",
        "Malposition (de), neurostimulateur électronique (électrode) (cerveau) (moelle épinière) (nerf périphérique)",
        "Atélectasie (complète) (massive) (par compression) (partielle) (postinfectieuse) (pulmonaire), due à anesthésie",
    ],
    "degradee",
)

echantillon_v4 = (
    _v4.select("code", "texte", "normalise_v4")
    .sample(n=100, seed=ECHANTILLON_V4_GRAINE, shuffle=True)
    .sort("code")
    .with_columns(
        pl.col("texte").replace_strict(RELECTURE_V4, default="correcte").alias("etiquette")
    )
)
print(echantillon_v4.group_by("etiquette").len().sort("len", descending=True))
_f4 = echantillon_v4.filter(pl.col("etiquette") == "fautive").height
_d4 = echantillon_v4.filter(pl.col("etiquette") == "degradee").height
print(f"\nSeuil « zéro fautive »     : {_f4} → {'ATTEINT' if _f4 == 0 else 'NON ATTEINT'}")
print(f"Seuil « ≤ 10 % dégradées » : {_d4}% → {'ATTEINT' if _d4 <= 10 else 'NON ATTEINT'}")

# %% (i) Le détail, pour relecture
echantillon_v4.select("code", "texte", "normalise_v4", "etiquette")

# %% [markdown]
# ### Application de la règle d'arrêt — **R3 est figée en v4**
#
# | Étiquette | v1 (50) | v2 (100) | v3 (100) | **v4 (100)** |
# |---|---|---|---|---|
# | `correcte` | 22 % | 57 % | 80 % | **85 %** |
# | `degradee` | 66 % | 40 % | 20 % | **15 %** |
# | `fautive` | 12 % | 3 % | 0 | **0** |
#
# La règle d'arrêt convenue prévoit : zéro fautive, entre 10 et 15 % de
# dégradées, **et pas de cause commune résiduelle corrigeable par
# motif** → on fige.
#
# **Zéro fautive** : atteint pour le second tour consécutif.
# **15 % de dégradées** : au plafond haut de la bande.
#
# **Y a-t-il encore une cause unique et corrigeable ?** Il y a bien une
# cause dominante — **10 des 15 dégradées** sont un joint non inséré
# (`canaliculite actinomyces`, `fièvre arbovirus`, `carence sélénium`,
# `phlegmon orbite`, `plaie testicule`, `entorse pied`…). Mais elle
# n'est **pas corrigeable par motif** : ces têtes n'ont *aucune*
# attestation de rection nulle part dans le corpus. C'est une limite de
# **couverture des données**, pas un défaut de règle. Aucun motif ne
# permettrait de deviner le genre de `dactylos` ou d'`arbovirus`.
#
# Les 5 restantes sont dispersées : une casse (`crise de Grand mal`),
# une énumération de synonymes (`deutéranomalie deutéranopie`), un
# adjectif ayant reçu un article (`paralysie de la médullaire`), un
# reliquat de troncature (`encéphalite précisée`), une élision absente
# du texte source (`atélectasie due à anesthésie`). Pas de motif commun.
#
# Ces formes sont du **télégraphique compréhensible** — un registre qui
# existe dans les CRH réels. **La règle d'arrêt s'applique : R3 est
# figée en l'état v4.** Le chantier `chapter_policy` peut être écrit.

# %% (i) Bilan global v4, par chapitre
bilan_v4 = (
    index_v4.with_columns(
        pl.when(pl.col("normalise_v4").is_null())
        .then(pl.lit("ecartee"))
        .when(pl.col("normalise_v4") == pl.col("texte"))
        .then(pl.lit("conservee"))
        .otherwise(pl.lit("normalisee"))
        .alias("issue")
    )
    .group_by("chapitre", "issue")
    .len()
    .pivot(on="issue", index="chapitre", values="len")
    .fill_null(0)
)
_c4 = [c for c in ("normalisee", "conservee", "ecartee") if c in bilan_v4.columns]
(
    bilan_v4.select(["chapitre", *_c4])
    .with_columns(pl.sum_horizontal(_c4).alias("total"))
    .with_columns((pl.col("normalisee") / pl.col("total")).round(3).alias("part_normalisee"))
    .sort("total", descending=True)
)

# %% (i) Bilan global v4, toutes politiques
pl.DataFrame(
    [
        {
            "politique": "détecteur 3 motifs (exclusion seule)",
            "conservees": index_lignes.filter(~pl.col("chemin_index")).height,
            "normalisees": 0,
            "ecartees": index_lignes.filter(pl.col("chemin_index")).height,
        },
        {
            "politique": "R3 v3",
            "conservees": _v3.filter(pl.col("normalise_v3") == pl.col("texte")).height,
            "normalisees": _v3.filter(pl.col("normalise_v3") != pl.col("texte")).height,
            "ecartees": index_v3.height - _v3.height,
        },
        {
            "politique": "R3 v4 — FIGÉE",
            "conservees": _v4.filter(pl.col("normalise_v4") == pl.col("texte")).height,
            "normalisees": _v4.filter(pl.col("normalise_v4") != pl.col("texte")).height,
            "ecartees": index_v4.height - _v4.height,
        },
    ]
)

# %% [markdown]
# ## (j) Angles morts restants
#
# 1. **Blocs candidats à une politique propre**, au-delà de T36-T50 :
#    `O00-O99` (grossesse — logique d'épisode plutôt que de diagnostic),
#    `P00-P96` (période périnatale), et les codes U du chapitre XXII
#    (usage provisoire, 7 formulations CepiDc seulement).
# 2. **ORPHANET n'alimente pas encore la section Formulations**
#    (`cards.FORMULATION_SOURCES_EXCLUDED`) : son exclusion dans R1 est
#    sans effet mesurable aujourd'hui, elle prépare une ouverture future.
# 3. **L'apport des fiches lui-même est en question** : une évaluation
#    manuelle par médecins DIM ne montre pas d'apport mesurable des
#    fiches dans les prompts de génération de CRH (cf
#    `docs/analyses/2026-08-09_evaluation_fiches_et_contexte_llm.md`).
#    Améliorer la qualité des formulations reste une condition
#    nécessaire, mais la piste « fiche réduite aux formulations seules »
#    y figure parmi les conditions à tester.
