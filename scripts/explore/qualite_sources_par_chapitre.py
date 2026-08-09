"""Qualité des sources de synonymes par chapitre CIM-10.

Trace reproductible de l'analyse du 2026-08-09. Document de référence :
`docs/analyses/2026-08-09_qualite_sources_par_chapitre.md`.

Objectif triple :

1. rejouer et affiner l'analyse de qualité des sources par chapitre ;
2. formuler explicitement les règles de filtrage R1 (filtrage par plage
   de codes × source) et R2 (plafonnement par source des fiches
   catégories) ;
3. les prototyper et mesurer leur effet, pour documenter la procédure.

> **Avertissement — prototype.** Les règles R1/R2 sont implémentées ici
> en configuration Python locale. La source de vérité finale sera le
> YAML du chantier `chapter_policy`, implémenté dans `src/`. **Le jour
> où ce chantier atterrit, la section (d) doit importer l'implémentation
> réelle au lieu du prototype**, sinon les deux divergeront en silence.
> Rien de ce fichier ne doit être importé par du code de production.

Le CSV maître n'est jamais modifié : ces règles s'appliquent à
l'assemblage des fiches uniquement.

Conversion en notebook :
    uv run --extra notebook python scripts/explore/_convert_to_ipynb.py \\
        scripts/explore/qualite_sources_par_chapitre.py
"""

# ruff: noqa: E402

# %% Chargement du contexte
from recode_icd.utils.loaders_dev import load_exploration_context

ctx = load_exploration_context(with_external=True)

import random
import re
from dataclasses import dataclass, field

import polars as pl

# Graine fixée partout : toute cellule d'échantillonnage doit être
# rejouable à l'identique.
SEED = 42
rng = random.Random(SEED)

pl.Config.set_tbl_rows(30)
pl.Config.set_fmt_str_lengths(90)

flat = ctx.flat if isinstance(ctx.flat, pl.DataFrame) else ctx.flat.collect()
merged = ctx.merged if isinstance(ctx.merged, pl.DataFrame) else ctx.merged.collect()
print(f"CSV maître : {flat.height:,} lignes".replace(",", " "))
print(f"merged_codes : {merged.height:,} codes".replace(",", " "))

# %% Helpers — chapitre, bloc, familles de sources
# Le mapping romain → numérique vit déjà dans `loaders_dev` (donnée pure,
# pas de la logique métier) : on le réutilise pour ordonner les chapitres
# plutôt que d'en dupliquer une copie ici.
from recode_icd.utils.loaders_dev import _ROMAN_TO_NUM_CHAPTER

CHAPITRES = sorted(_ROMAN_TO_NUM_CHAPTER, key=lambda r: _ROMAN_TO_NUM_CHAPTER[r])

# `path` vaut par exemple "I/A00-A09/A00/A00.0" → chapitre / bloc /
# catégorie / code.
#
# Deux pièges, tous deux rencontrés :
#
# - **Blocs imbriqués.** Le chapitre II a deux niveaux de bloc
#   ("II/C00-C97/C00-C75/C50/C50.8"), donc la position dans le `path`
#   ne désigne pas le même niveau selon le chapitre. On retient le bloc
#   le plus *interne* (dernier segment de forme « A00-B99 »), seul
#   niveau pertinent pour une règle de bloc type T36-T50.
# - **Catégorie.** `cards.py` définit une catégorie comme le code à 3
#   caractères (`_category_leaf_codes`), pas comme un segment du path :
#   on la dérive du code lui-même, partie avant le point.
_RE_BLOC = r"^[A-Z]\d{2}-[A-Z]?\d{2}$"
_hier = merged.select(
    pl.col("code"),
    pl.col("path").str.split("/").list.get(0, null_on_oob=True).alias("chapitre"),
    pl.col("path")
    .str.split("/")
    .list.eval(pl.element().filter(pl.element().str.contains(_RE_BLOC)))
    .alias("blocs"),
    pl.col("code").str.split(".").list.first().alias("categorie"),
)

# Familles de sources, exprimées en **libellés CSV** (colonne `source`).
# On réutilise les constantes de `cards.py` pour les trois sources qui
# alimentent réellement la section Formulations : si un libellé est
# renommé, ce notebook suit automatiquement.
from recode_icd import cards

FAMILLE_PAR_LIBELLE: dict[str, str] = {
    "CIM-10": "OFS",
    "ANS": "ANS",
    "CIM-10 frères": "OFS",
    cards.FORMULATION_SOURCE_INDEX: "INDEX",
    "ORPHANET": "ORPHANET",
    cards.FORMULATION_SOURCE_CEPIDC: "CEPIDC",
}


def _famille(libelle: str) -> str:
    if libelle.startswith(cards.FORMULATION_SOURCE_APHP_PREFIX):
        return "APHP"
    return FAMILLE_PAR_LIBELLE.get(libelle, "AUTRE")


_familles = pl.DataFrame(
    {
        "source": sorted(flat["source"].unique().to_list()),
    }
).with_columns(
    pl.col("source").map_elements(_famille, return_dtype=pl.String).alias("famille")
)

# Table de travail : CSV maître enrichi de chapitre / bloc / catégorie /
# famille de source. C'est le socle de toutes les cellules suivantes.
work = flat.join(_hier, on="code", how="left").join(_familles, on="source", how="left")

# Les sections des fiches ne consomment pas les mêmes lignes :
#   - Formulations       ← Index + AP-HP + CepiDc (cf cards.py)
#   - Périmètre clinique ← inclusions (OFS/ANS)
#   - À ne pas décrire   ← exclusions
FAMILLES_FORMULATIONS = ("INDEX", "APHP", "CEPIDC")
candidates_formulations = work.filter(pl.col("famille").is_in(FAMILLES_FORMULATIONS))

print(f"Lignes candidates à la section Formulations : {candidates_formulations.height:,}".replace(",", " "))
print(f"Chapitre non résolu : {work['chapitre'].null_count()} lignes")

# %% (a) Volumétrie — synonymes par source × chapitre
croise = (
    work.filter(pl.col("type") == "synonyme")
    .group_by("chapitre", "source")
    .len()
    .pivot(on="chapitre", index="source", values="len")
    .fill_null(0)
)
colonnes = ["source"] + [c for c in CHAPITRES if c in croise.columns]
print("Synonymes par source × chapitre (CSV courant)")
print(croise.select(colonnes).sort("source"))

# %% (a) Volumétrie — focus XVIII à XXI
FOCUS = ["XVIII", "XIX", "XX", "XXI"]
focus_tbl = (
    work.filter((pl.col("type") == "synonyme") & pl.col("chapitre").is_in(FOCUS))
    .group_by("chapitre", "famille")
    .len()
    .pivot(on="chapitre", index="famille", values="len")
    .fill_null(0)
)
print("Synonymes par famille de sources sur les chapitres à politique spéciale")
print(focus_tbl.select(["famille"] + [c for c in FOCUS if c in focus_tbl.columns]).sort("famille"))

# %% (a) Volumétrie — codes distincts couverts par famille
couverture = (
    work.group_by("famille")
    .agg(
        pl.col("code").n_unique().alias("codes_couverts"),
        pl.len().alias("lignes"),
    )
    .sort("lignes", descending=True)
)
print("Couverture par famille de sources (toutes lignes, tous types)")
print(couverture)

# %% (a) Écarts avec les chiffres de référence pré-merge
# Les chiffres de référence de l'analyse initiale (2026-08-09) portaient
# sur le CSV **pré-merge CepiDc** (199 970 lignes). Ils sont figés dans
# le document de trace ; on mesure ici l'écart plutôt que de les
# réécrire.
REFERENCE_PRE_MERGE = {
    ("APHP", "XVIII"): 112,
    ("APHP", "XIX"): 235,
    ("APHP", "XX"): 49,
    ("APHP", "XXI"): 39,
    ("INDEX", "XIX"): 3935,
    ("INDEX", "XXI"): 1695,
    ("INDEX", "XX"): 0,
}
courant = {
    (r["famille"], r["chapitre"]): r["len"]
    for r in work.filter(pl.col("type") == "synonyme")
    .group_by("famille", "chapitre")
    .len()
    .iter_rows(named=True)
}
lignes_ecart = [
    {
        "famille": fam,
        "chapitre": chap,
        "reference_pre_merge": ref,
        "csv_courant": courant.get((fam, chap), 0),
        "ecart": courant.get((fam, chap), 0) - ref,
    }
    for (fam, chap), ref in REFERENCE_PRE_MERGE.items()
]
print("Écarts référence pré-merge → CSV courant")
print(pl.DataFrame(lignes_ecart).sort("famille", "chapitre"))

# %% (b) Échantillonneur qualitatif
def echantillon(
    prefixes: tuple[str, ...] | str,
    famille: str | None = None,
    type_note: str | None = "synonyme",
    n: int = 12,
    seed: int = SEED,
) -> pl.DataFrame:
    """Échantillon reproductible de lignes du CSV.

    `prefixes` : préfixes de code (« S », « T4 », « Z ») ou chapitre
    romain si la chaîne y ressemble. Graine fixée → rejouable.
    """
    if isinstance(prefixes, str):
        prefixes = (prefixes,)
    sub = work
    if prefixes and prefixes[0] in CHAPITRES:
        sub = sub.filter(pl.col("chapitre").is_in(list(prefixes)))
    else:
        sub = sub.filter(
            pl.any_horizontal([pl.col("code").str.starts_with(p) for p in prefixes])
        )
    if famille:
        sub = sub.filter(pl.col("famille") == famille)
    if type_note:
        sub = sub.filter(pl.col("type") == type_note)
    if sub.is_empty():
        return sub.select("code", "source", "texte")
    return sub.select("code", "source", "texte").sample(
        n=min(n, sub.height), seed=seed, shuffle=True
    )


print("Index CIM-10 vol3 sur le chapitre XIX (S00-T98) — format « chemin d'index »")
print(echantillon("XIX", famille="INDEX"))

# %% (b) Rejeu — Index CIM-10 vol3 sur le chapitre XXI (Z)
print("Index CIM-10 vol3 sur le chapitre XXI (Z00-Z99) — qualité mélangée")
print(echantillon("XXI", famille="INDEX"))

# %% (b) Rejeu — CepiDc sur le bloc T36-T50 (intoxications médicamenteuses)
print("CepiDc sur T36-T50 — noms de médicaments nus, logique du certificat de décès")
print(echantillon(tuple(f"T{n}" for n in range(36, 51)), famille="CEPIDC", n=15))

# %% (b) Rejeu — CepiDc sur les chapitres diagnostiques (contre-exemple)
print("CepiDc sur les chapitres X (respiratoire) et II (tumeurs) — excellentes formulations")
print(echantillon("X", famille="CEPIDC", n=10))
print(echantillon("II", famille="CEPIDC", n=10))

# %% (c) Détecteur de motifs parasites
# Deux heuristiques issues de l'analyse. Elles sont **indicatives** :
# la seconde est fortement dépendante du chapitre (cf cellule suivante).
_PREFIXES_PARASITES = (
    "prise",
    "traitement",
    "sous",
    "injection",
    "perfusion",
)
_RE_PREFIXE = re.compile(
    r"^\s*(" + "|".join(_PREFIXES_PARASITES) + r")\b", flags=re.IGNORECASE
)
_RE_MOT_UNIQUE_CAPITALISE = re.compile(r"^\s*[A-ZÀ-Ý][\wÀ-ÿ'-]*\s*$")


def motif_parasite(texte: str | None) -> str | None:
    """Renvoie le nom du motif détecté, ou None."""
    if not texte:
        return None
    if _RE_PREFIXE.match(texte):
        return "prefixe_prise_traitement"
    if _RE_MOT_UNIQUE_CAPITALISE.match(texte):
        return "mot_unique_capitalise"
    return None


cepidc = work.filter(pl.col("famille") == "CEPIDC").with_columns(
    pl.col("texte").map_elements(motif_parasite, return_dtype=pl.String).alias("motif")
)

taux = (
    cepidc.group_by("chapitre")
    .agg(
        pl.len().alias("n_formulations"),
        pl.col("motif").is_not_null().sum().alias("n_parasites"),
    )
    .with_columns((pl.col("n_parasites") / pl.col("n_formulations")).alias("taux"))
    .sort("taux", descending=True)
)
print("Taux de motifs parasites CepiDc par chapitre")
print(taux)

# %% (c) Taux par motif sur les chapitres à risque
print("Détail par motif, chapitres XIX (S-T), XX (V-Y), XXI (Z)")
print(
    cepidc.filter(pl.col("chapitre").is_in(["XIX", "XX", "XXI"]))
    .filter(pl.col("motif").is_not_null())
    .group_by("chapitre", "motif")
    .len()
    .sort("chapitre", "motif")
)

# %% (c) Faux positifs typiques du motif « mot unique capitalisé »
# Hors chapitres à risque, ce motif capture surtout des acronymes et des
# éponymes — d'excellents synonymes. C'est la limite de l'heuristique,
# et la raison pour laquelle on fait une politique par chapitre plutôt
# qu'une curation textuelle générale.
faux_positifs = (
    cepidc.filter(
        (pl.col("motif") == "mot_unique_capitalise")
        & ~pl.col("chapitre").is_in(["XIX", "XX", "XXI"])
    )
    .select("code", "chapitre", "texte")
    .sample(n=20, seed=SEED, shuffle=True)
)
print("Faux positifs du motif « mot unique capitalisé » hors chapitres à risque")
print(faux_positifs)

# %% (d) PROTOTYPE — configuration déclarative R1
@dataclass(frozen=True)
class Politique:
    """Politique applicable à une plage de codes.

    `familles_exclues` : familles de sources retirées de la section
    Formulations. `generation_llm` : autorise ou non l'ajout de
    formulations générées par LLM (flag distinct — une source LLM peut
    être exclue là où les sources réelles sont conservées).
    """

    familles_exclues: frozenset[str] = field(default_factory=frozenset)
    generation_llm: bool = True


# ATTENTION — sémantique de résolution : **la règle la plus spécifique
# REMPLACE** la moins spécifique (bloc > chapitre > défaut), elle ne s'y
# ajoute pas. Une entrée de bloc doit donc **redéclarer** les exclusions
# du chapitre qu'elle veut conserver. Ce choix est délibéré : c'est le
# seul qui permette, plus tard, de *ré-admettre* une source au niveau
# bloc (cas prévu pour T36-T50, cf document de trace).
POLITIQUE_DEFAUT = Politique()

POLITIQUE_CHAPITRE: dict[str, Politique] = {
    # XVIII (R00-R99) — les codes R ont de vraies variantes d'usage
    # courant (« mal de tête » pour R51). Sources réelles conservées,
    # génération LLM exclue.
    "XVIII": Politique(familles_exclues=frozenset(), generation_llm=False),
    # XIX (S00-T98) — lésions traumatiques, combinatoires par site et
    # nature. L'Index y est du chemin d'index inversé, pas des
    # formulations.
    "XIX": Politique(
        familles_exclues=frozenset({"INDEX", "APHP", "ORPHANET", "CEPIDC", "LLM"}),
        generation_llm=False,
    ),
    # XX (V01-Y98) — causes externes : se codent sur les circonstances
    # décrites, pas sur un terme médical substituable. (L'Index y est
    # déjà absent.)
    "XX": Politique(
        familles_exclues=frozenset({"APHP", "ORPHANET", "CEPIDC", "LLM"}),
        generation_llm=False,
    ),
    # XXI (Z00-Z99) — circonstances administratives ou de prise en
    # charge.
    "XXI": Politique(
        familles_exclues=frozenset({"INDEX", "APHP", "ORPHANET", "CEPIDC", "LLM"}),
        generation_llm=False,
    ),
}

POLITIQUE_BLOC: dict[str, Politique] = {
    # T36-T50 (intoxications médicamenteuses) se comporte plus comme des
    # diagnostics classiques que comme des lésions par site. L'entrée
    # existe pour préparer un assouplissement futur du chapitre XIX sur
    # ce bloc — mais CepiDc doit y rester exclu dans tous les cas : le
    # dictionnaire y contient des noms de médicaments nus
    # (« Furosémide » → T50.1), inutilisables comme formulation de CRH.
    # Aujourd'hui l'entrée reprend à l'identique la politique XIX.
    "T36-T50": Politique(
        familles_exclues=frozenset({"INDEX", "APHP", "ORPHANET", "CEPIDC", "LLM"}),
        generation_llm=False,
    ),
}

# Motif des renvois ANS à écarter. **Amendement du 2026-08-09** :
# l'analyse initiale situait ces renvois dans la section Formulations.
# Vérification faite, ANS n'alimente pas cette section (cf `cards.py`,
# FORMULATION_SOURCES_EXCLUDED) — ces lignes remontent comme
# *inclusions* dans « Périmètre clinique du code ». La règle porte donc
# sur cette section.
# Le drapeau `(?i)` est **inline** et non passé à `re.compile` : polars
# ne reçoit que `.pattern`, il perdrait un flag Python. Sans cela le
# motif ne matche pas « États mentionnés… » (É majuscule).
RE_RENVOI_ANS = re.compile(r"(?i)^\s*états?\s+mentionn")


def politique_pour(chapitre: str | None, blocs: list[str] | None) -> Politique:
    """Résolution bloc > chapitre > défaut (remplacement, pas union).

    `blocs` est la liste des blocs englobants du plus large au plus
    étroit — la CIM-10 en imbrique jusqu'à trois niveaux (C50.8 vit sous
    « C00-C97 / C00-C75 / C50-C50 »). On les teste du plus **interne**
    au plus large : la règle la plus spécifique gagne.
    """
    for bloc in reversed(blocs or []):
        if bloc in POLITIQUE_BLOC:
            return POLITIQUE_BLOC[bloc]
    if chapitre and chapitre in POLITIQUE_CHAPITRE:
        return POLITIQUE_CHAPITRE[chapitre]
    return POLITIQUE_DEFAUT


# %% (d) PROTOTYPE — fonctions d'application
def applique_r1_formulations(df: pl.DataFrame) -> pl.DataFrame:
    """Retire les lignes dont la famille est exclue sur leur plage.

    Entrée : lignes candidates à la section Formulations, colonnes
    `chapitre`, `bloc`, `famille`. Fonction pure.
    """
    combinaisons = (
        df.select("chapitre", "blocs", "famille")
        .with_columns(pl.col("blocs").list.join("|").alias("_cle_blocs"))
        .unique(subset=["chapitre", "_cle_blocs", "famille"])
    )
    exclues = [
        (chap, cle, fam)
        for chap, blocs, fam, cle in combinaisons.iter_rows()
        if fam in politique_pour(chap, list(blocs or [])).familles_exclues
    ]
    if not exclues:
        return df
    marque = df.with_columns(pl.col("blocs").list.join("|").alias("_cle_blocs"))
    masque = pl.any_horizontal(
        [
            (pl.col("chapitre") == chap)
            & (pl.col("_cle_blocs") == cle)
            & (pl.col("famille") == fam)
            for chap, cle, fam in exclues
        ]
    )
    return marque.filter(~masque).drop("_cle_blocs")


def applique_r1_perimetre(df: pl.DataFrame) -> pl.DataFrame:
    """Retire les renvois ANS « États mentionnés en … » des inclusions."""
    return df.filter(
        ~(
            (pl.col("famille") == "ANS")
            & (pl.col("type") == "inclusion")
            & pl.col("texte").str.contains(RE_RENVOI_ANS.pattern)
        )
    )


def applique_r2(df: pl.DataFrame, plafond: int) -> pl.DataFrame:
    """Plafonne à `plafond` entrées par (catégorie, **famille**).

    On plafonne par famille et non par libellé de source : la question
    posée est la domination d'un *type* de source, et les neuf feuilles
    AP-HP forment un seul apport métier. `cards.py` plafonne aujourd'hui
    Index et CepiDc individuellement et laisse AP-HP libre — la famille
    unifie les deux régimes.

    L'ordre de troncature est pseudo-aléatoire déterministe (cf
    `_ordre_pseudo_aleatoire`), pour rester fidèle au `rng.sample` de
    `cards.py`.
    """
    return (
        df.with_columns(_ordre_pseudo_aleatoire())
        .sort("categorie", "famille", "_alea")
        .with_columns(pl.int_range(pl.len()).over("categorie", "famille").alias("_rang"))
        .filter(pl.col("_rang") < plafond)
        .drop("_rang", "_alea")
    )


def _ordre_pseudo_aleatoire() -> pl.Expr:
    """Clé de tri pseudo-aléatoire mais reproductible.

    **Pourquoi pas un simple tri alphabétique + tête de liste** :
    `cards.py` tronque avec `rng.sample`, un tirage *uniforme*, qui
    préserve donc en espérance la composition par source du vivier. Une
    troncature sur l'ordre alphabétique des codes biaiserait la
    composition (elle privilégierait les premières feuilles de la
    catégorie) et ferait mesurer un déséquilibre qui n'est pas celui des
    fiches réelles. Le hash à graine fixe reproduit l'uniformité du
    tirage tout en restant déterministe d'un run à l'autre.
    """
    return (pl.col("code") + "|" + pl.col("texte")).hash(seed=SEED).alias("_alea")


def applique_plafond_global(df: pl.DataFrame, plafond: int) -> pl.DataFrame:
    """Plafond global par catégorie, tel que `cards.py` l'applique après
    dédup (`CATEGORY_FORMULATIONS_MAX`). Modélisé ici pour mesurer la
    composition **réellement rendue**, pas celle du vivier."""
    return (
        df.with_columns(_ordre_pseudo_aleatoire())
        .sort("categorie", "_alea")
        .with_columns(pl.int_range(pl.len()).over("categorie").alias("_rang"))
        .filter(pl.col("_rang") < plafond)
        .drop("_rang", "_alea")
    )


# %% (d) Mesure d'effet — R1 sur la section Formulations
avant = candidates_formulations
apres = applique_r1_formulations(avant)
print(f"Formulations candidates : {avant.height:,} → {apres.height:,}".replace(",", " "))
print(f"Écartées par R1 : {avant.height - apres.height:,}".replace(",", " "))

effet_r1 = (
    avant.group_by("chapitre", "famille")
    .len()
    .rename({"len": "avant"})
    .join(
        apres.group_by("chapitre", "famille").len().rename({"len": "apres"}),
        on=["chapitre", "famille"],
        how="left",
    )
    .with_columns(pl.col("apres").fill_null(0))
    .with_columns((pl.col("avant") - pl.col("apres")).alias("ecartees"))
    .filter(pl.col("ecartees") > 0)
    .sort("ecartees", descending=True)
)
print("Lignes écartées par R1, par chapitre × famille")
print(effet_r1)

# %% (d) Mesure d'effet — R1 sur le périmètre clinique (renvois ANS)
inclusions = work.filter(pl.col("type") == "inclusion")
inclusions_apres = applique_r1_perimetre(inclusions)
retirees = inclusions.height - inclusions_apres.height
print(f"Inclusions : {inclusions.height:,} → {inclusions_apres.height:,}".replace(",", " "))
print(f"Renvois ANS « États mentionnés en … » retirés : {retirees}")
print(
    inclusions.filter(
        (pl.col("famille") == "ANS")
        & pl.col("texte").str.contains(RE_RENVOI_ANS.pattern)
    )
    .group_by("chapitre")
    .len()
    .sort("len", descending=True)
    .head(8)
)

# %% (d) Mesure d'effet — fiches dont la section Formulations devient vide
codes_avant = set(avant["code"].unique().to_list())
codes_apres = set(apres["code"].unique().to_list())
vidés = codes_avant - codes_apres
print(f"Codes ayant une section Formulations avant R1 : {len(codes_avant):,}".replace(",", " "))
print(f"Codes dont elle devient vide : {len(vidés):,}".replace(",", " "))
print(
    pl.DataFrame({"code": sorted(vidés)})
    .join(_hier, on="code", how="left")
    .group_by("chapitre")
    .len()
    .sort("len", descending=True)
)

# %% (d) Calibration du plafond R2 sur les fiches catégories
# Les fiches catégories agrègent les formulations de leurs feuilles et
# n'ont aujourd'hui **aucun plafond par source** — seulement un plafond
# global CATEGORY_FORMULATIONS_MAX. D'où le déséquilibre mesuré au
# chantier 1. On balaie plusieurs plafonds par source.
base_cat = apres.filter(pl.col("categorie").is_not_null())


def profil_categories(df: pl.DataFrame) -> pl.DataFrame:
    """Part de chaque source dans le vivier de chaque catégorie."""
    par_cat = df.group_by("categorie").len().rename({"len": "total"})
    return (
        df.filter(pl.col("famille") == "CEPIDC")
        .group_by("categorie")
        .len()
        .rename({"len": "n_cepidc"})
        .join(par_cat, on="categorie", how="right")
        .with_columns(pl.col("n_cepidc").fill_null(0))
        .with_columns((pl.col("n_cepidc") / pl.col("total")).alias("part_cepidc"))
    )


PLAFOND_FEUILLES = cards.INDEX_SAMPLE_SIZE  # 10 — convention des fiches feuilles
PLAFOND_GLOBAL = cards.CATEGORY_FORMULATIONS_MAX  # 50


def _stats_desequilibre(df: pl.DataFrame, etiquette: str) -> dict[str, object]:
    """Déséquilibre CepiDc des fiches catégories effectivement rendues."""
    vivier = df.group_by("categorie").len().rename({"len": "vivier"})
    ref = vivier.filter(pl.col("vivier") > PLAFOND_GLOBAL)
    rendu = applique_plafond_global(
        df.join(ref.select("categorie"), on="categorie", how="inner"), PLAFOND_GLOBAL
    )
    prof = profil_categories(rendu)
    return {
        "etat": etiquette,
        "categories_vivier_sup_50": ref.height,
        "part_cepidc_mediane": round(prof["part_cepidc"].median(), 3) if prof.height else 0.0,
        "categories_sup_80pct": prof.filter(pl.col("part_cepidc") > 0.8).height,
    }


# R1 retire déjà CepiDc des chapitres XIX/XX/XXI, là où sa domination
# était la plus forte. Mesurer R2 sans cette étape surestimerait donc le
# problème : on affiche les deux états.
avant_cat = avant.filter(pl.col("categorie").is_not_null())
print("Déséquilibre CepiDc des fiches catégories — effet de R1 seul")
print(
    pl.DataFrame(
        [
            _stats_desequilibre(avant_cat, "avant R1"),
            _stats_desequilibre(apres.filter(pl.col("categorie").is_not_null()), "après R1"),
        ]
    )
)
print()

# Jeu de référence **figé** : les catégories dont le vivier dépasse le
# plafond global, c'est-à-dire celles où l'échantillonnage mord et où le
# déséquilibre se manifeste. Il doit être calculé une seule fois, sur le
# vivier non plafonné — le recalculer après chaque plafond mesurerait
# une population différente à chaque ligne, donc rien du tout.
_vivier = base_cat.group_by("categorie").len().rename({"len": "vivier"})
CATEGORIES_REF = _vivier.filter(pl.col("vivier") > PLAFOND_GLOBAL)
# Composition de référence : ce que la fiche rend aujourd'hui, soit le
# vivier tronqué au plafond global sans plafond par source.
_baseline_rendu = applique_plafond_global(
    base_cat.join(CATEGORIES_REF.select("categorie"), on="categorie", how="inner"),
    PLAFOND_GLOBAL,
)
print(f"Catégories de référence (vivier > {PLAFOND_GLOBAL}) : {CATEGORIES_REF.height}")
print(f"Formulations rendues aujourd'hui sur ces catégories : {_baseline_rendu.height:,}".replace(",", " "))

lignes_calibration = []
for plafond in (None, 5, 10, 15, 20):
    sous_ensemble = base_cat.join(
        CATEGORIES_REF.select("categorie"), on="categorie", how="inner"
    )
    if plafond is not None:
        sous_ensemble = applique_r2(sous_ensemble, plafond)
    rendu = applique_plafond_global(sous_ensemble, PLAFOND_GLOBAL)
    prof = profil_categories(rendu)
    lignes_calibration.append(
        {
            "plafond": "aucun (actuel)" if plafond is None else str(plafond),
            "reference": plafond == PLAFOND_FEUILLES,
            "formulations_rendues": rendu.height,
            "formulations_perdues": _baseline_rendu.height - rendu.height,
            "part_cepidc_mediane": round(prof["part_cepidc"].median(), 3),
            "categories_sup_80pct": prof.filter(pl.col("part_cepidc") > 0.8).height,
            "categories_a_zero_cepidc": prof.filter(pl.col("part_cepidc") == 0).height,
        }
    )
calibration = pl.DataFrame(lignes_calibration)
print()
print("Calibration du plafond R2 — coût en diversité face au bénéfice en équilibre")
print(f"(mesuré sur les {CATEGORIES_REF.height} catégories de référence, après plafond global {PLAFOND_GLOBAL})")
print("(« reference » marque le plafond des fiches feuilles : convention unique s'il convient)")
print(calibration)

# %% (d) Validation visuelle — rendu avant/après sur codes témoins
# Témoins : un R (conservé intégralement), un S (Index seul, écarté),
# un Z massivement alimenté par CepiDc, et un T36-T50 (double motif :
# règle de chapitre XIX + règle de bloc).
TEMOINS = ["R51", "S52.50", "Z92.4", "T39.1"]


def rendu_formulations(code: str, df: pl.DataFrame, limite: int = 12) -> list[str]:
    sub = df.filter(pl.col("code") == code)
    return sorted(sub["texte"].drop_nulls().unique().to_list())[:limite]


for code in TEMOINS:
    chap = _hier.filter(pl.col("code") == code)
    if chap.is_empty():
        print(f"\n=== {code} : absent du référentiel ===")
        continue
    print(f"\n=== {code} (chapitre {chap['chapitre'][0]}, blocs {chap['blocs'][0].to_list()}) ===")
    av = rendu_formulations(code, avant)
    ap = rendu_formulations(code, apres)
    print(f"  avant R1 ({len(avant.filter(pl.col('code') == code))} lignes) :")
    for t in av:
        print(f"    - {t[:95]}")
    print(f"  après R1 ({len(apres.filter(pl.col('code') == code))} lignes) :")
    if not ap:
        print("    (section supprimée)")
    for t in ap:
        print(f"    - {t[:95]}")

# %% (d) Validation visuelle — catégories déséquilibrées
prof_avant = profil_categories(base_cat)
desequilibrees = (
    prof_avant.filter(
        (pl.col("total") > cards.CATEGORY_FORMULATIONS_MAX) & (pl.col("part_cepidc") > 0.8)
    )
    .sort("total", descending=True)
    .head(3)
)
print("Trois catégories parmi les plus déséquilibrées")
print(desequilibrees)

apres_r2 = applique_r2(base_cat, PLAFOND_FEUILLES)
for cat in desequilibrees["categorie"].to_list():
    av_n = base_cat.filter(pl.col("categorie") == cat)
    ap_n = apres_r2.filter(pl.col("categorie") == cat)
    print(f"\n=== catégorie {cat} — plafond {PLAFOND_FEUILLES} par source ===")
    print(f"  avant : {av_n.height} formulations, {av_n.group_by('source').len().sort('len', descending=True).to_dicts()}")
    print(f"  après : {ap_n.height} formulations, {ap_n.group_by('source').len().sort('len', descending=True).to_dicts()}")

# %% (e) Angles morts
print(
    """
ANGLES MORTS — à instruire avant d'implémenter chapter_policy
=============================================================

1. Fréquence du format « chemin d'index » sur les chapitres NON exclus.
   R1 ne retire l'Index que sur XIX et XXI. Or le format « Traumatisme(s)
   (de) (voir aussi ...), artère, cubitale ... » n'est pas propre à ces
   chapitres : la cellule ci-dessous en mesure la prévalence ailleurs.
   Si elle est forte, le critère devrait être **le format de l'entrée**,
   pas seulement le chapitre.

2. Autres blocs candidats à une politique spéciale au-delà de T36-T50.
   Pistes : O00-O99 (grossesse — logique d'épisode plutôt que de
   diagnostic), P00-P96 (période périnatale), et les codes U (chapitre
   XXII, usage provisoire).

3. Sémantique de résolution bloc > chapitre. Le prototype implémente le
   REMPLACEMENT, pas l'union : une entrée de bloc doit redéclarer les
   exclusions du chapitre qu'elle conserve. C'est ce qui permettra de
   ré-admettre des sources sur T36-T50, mais c'est un piège si on
   l'oublie. À trancher explicitement dans le YAML de chapter_policy.

4. ORPHANET n'alimente pas la section Formulations aujourd'hui
   (cards.FORMULATION_SOURCES_EXCLUDED). Son exclusion dans R1 est donc
   sans effet mesurable — elle prépare le cas où la section s'ouvrirait
   à cette source.
"""
)

# %% (e) Mesure — prévalence du format « chemin d'index » hors chapitres exclus
# Heuristique : une entrée d'index inversé contient une virgule de
# subordination et/ou un renvoi « voir ».
_RE_CHEMIN_INDEX = re.compile(r"(,\s*\w+.*){2,}|voir\s+aussi|\(voir", flags=re.IGNORECASE)
index_lignes = work.filter(pl.col("famille") == "INDEX").with_columns(
    pl.col("texte").str.contains(_RE_CHEMIN_INDEX.pattern).alias("chemin_index")
)
prevalence = (
    index_lignes.group_by("chapitre")
    .agg(
        pl.len().alias("n_index"),
        pl.col("chemin_index").sum().alias("n_chemin"),
    )
    .with_columns((pl.col("n_chemin") / pl.col("n_index")).round(3).alias("part"))
    .sort("n_index", descending=True)
)
print("Prévalence du format « chemin d'index » par chapitre")
print("(XIX et XXI sont déjà exclus par R1 — regarder les autres)")
print(prevalence)
