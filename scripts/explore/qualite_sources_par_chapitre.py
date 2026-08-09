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
# ## (f) Angles morts restants
#
# 1. **Blocs candidats à une politique propre**, au-delà de T36-T50 :
#    `O00-O99` (grossesse — logique d'épisode plutôt que de diagnostic),
#    `P00-P96` (période périnatale), et les codes U du chapitre XXII
#    (usage provisoire, 7 formulations CepiDc seulement).
# 2. **ORPHANET n'alimente pas encore la section Formulations**
#    (`cards.FORMULATION_SOURCES_EXCLUDED`) : son exclusion dans R1 est
#    sans effet mesurable aujourd'hui, elle prépare une ouverture future.
# 3. **Normalisation plutôt qu'exclusion** des entrées Index de la zone
#    grise (cf section e).
# 4. **L'apport des fiches lui-même est en question** : une évaluation
#    manuelle par médecins DIM ne montre pas d'apport mesurable des
#    fiches dans les prompts de génération de CRH (cf
#    `docs/analyses/2026-08-09_evaluation_fiches_et_contexte_llm.md`).
#    Améliorer la qualité des formulations reste une condition
#    nécessaire, mais la piste « fiche réduite aux formulations seules »
#    y figure parmi les conditions à tester.
