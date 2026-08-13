"""Les trois lexiques dérivés du corpus, et leurs trois périmètres.

⚠ **PITFALL CENTRAL — ne jamais fusionner ces trois lexiques.**

Ils sont construits sur des sous-ensembles *différents* du CSV, et chaque
exclusion répond à une propriété linguistique distincte de la source
écartée. Les unifier « par simplification » casse une garantie
différente à chaque fois.

| Lexique | Périmètre | Pourquoi |
|---|---|---|
| **Rections** — `du X`, `de la X` | **Index inclus** | La syntaxe *interne* des entrées d'index est du français naturel (« hypertrophie adénofibromateuse **de la** prostate ») : elle témoigne valablement du genre. |
| **Casse** — mots vus en minuscule | **Index exclu** | L'Index capitalise **toute tête d'entrée** par convention éditoriale. Il ne peut donc pas dire si un mot est un nom commun — c'est précisément le test qu'on lui demande. |
| **Juxtaposition** — mot suivant un mot sans article | **CepiDc exclu**, virgules et parenthèses en **frontières dures** | CepiDc est **télégraphique** : il supprime les articles, donc tout nom y paraît adjectival. Et sans frontières, « Hypoplasie (de), cerveau » se compterait lui-même en juxtaposition — **l'Index se contaminerait**. |

Mesuré : sans exclure CepiDc, « cerveau » ressort adjectival (A/J = 0,46)
et « hypoplasie du cerveau » serait cassé. Sans frontières, même effet.
Avec les deux corrections : cerveau 78/1, estomac 79/1, médullaire 1/72.

Les trois artefacts sont **déterministes** : tri explicite, aucun
horodatage. Ils sont reconstruits par `recode-icd build lexicons` et
versionnés dans `referentials/processed/`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from recode_icd.loaders.schemas import (
    LexiqueCasseSchema,
    LexiqueJuxtapositionSchema,
    LexiqueRectionsSchema,
)
from recode_icd.policy import ChapterPolicy

#: Deux motifs sont nécessaires : les formes élidées s'attachent au mot
#: suivant (« de l'estomac »), les autres en sont séparées par une
#: espace. Un motif unique en `\s+` ne verrait **jamais** les élisions —
#: le lexique serait silencieusement amputé de toute une famille.
RE_RECTION_ESPACE = re.compile(r"\b(du|de la|des|de|au|à la|aux|à)\s+([a-zà-ÿ][\wà-ÿ-]{2,})")
RE_RECTION_ELIDEE = re.compile(r"\b(de l'|à l')\s*([a-zà-ÿ][\wà-ÿ-]{2,})")

#: Familles `de` et `à`, de la forme la plus contractée à la forme nue.
#: L'ordre est porteur de sens : la contractée porte le genre, la nue
#: n'est qu'un repli.
FAMILLE_DE = ("du", "de la", "de l'", "des", "de")
FAMILLE_A = ("au", "à la", "à l'", "aux", "à")

#: Mots outils : un mot qui en suit un n'est pas en juxtaposition nue.
MOTS_OUTILS = frozenset(
    {
        "le",
        "la",
        "les",
        "l",
        "un",
        "une",
        "des",
        "du",
        "de",
        "d",
        "au",
        "aux",
        "à",
        "en",
        "avec",
        "sans",
        "par",
        "pour",
        "sur",
        "dans",
        "sous",
        "chez",
        "vers",
        "entre",
        "après",
        "avant",
        "depuis",
        "dû",
        "due",
        "dus",
        "dues",
        "et",
        "ou",
        "son",
        "sa",
        "ses",
    }
)

RE_MOT = re.compile(r"[a-zà-ÿ][\wà-ÿ-]*")
#: Virgules et parenthèses coupent la juxtaposition — sans quoi
#: « Hypoplasie (de), cerveau » compterait « cerveau » comme juxtaposé.
RE_FRONTIERE = re.compile(r"[(),;:/]")

RECTIONS_FILENAME = "lexique_rections.parquet"
CASSE_FILENAME = "lexique_casse.parquet"
JUXTAPOSITION_FILENAME = "lexique_juxtaposition.parquet"


@dataclass(frozen=True)
class Lexiques:
    """Les trois lexiques, sous la forme attendue par `normalize_index`."""

    rections: dict[str, dict[str, int]]
    casse: frozenset[str]
    juxtaposition: dict[str, int]

    def attestations_avec_joint(self, mot: str) -> int:
        """`A` — nombre total d'attestations avec article ou joint."""
        return sum(self.rections.get(mot.lower(), {}).values())

    def attestations_juxtaposees(self, mot: str) -> int:
        """`J` — nombre d'attestations en juxtaposition adjectivale nue."""
        return self.juxtaposition.get(mot.lower(), 0)

    def est_minuscule_attestee(self, mot: str) -> bool:
        """Le mot est-il attesté en minuscule **hors Index** ?"""
        return mot.lower() in self.casse


def _normalise_apostrophes(texte: str) -> str:
    return texte.replace("l'", "l' ").replace("d'", "d' ")


def build_lexique_rections(csv: pl.DataFrame) -> pl.DataFrame:
    """`(nom, joint, occurrences)` — **toutes sources, Index inclus**."""
    compte: dict[tuple[str, str], int] = {}
    for texte in csv["texte"].drop_nulls().to_list():
        bas = texte.lower()
        for motif in (RE_RECTION_ESPACE, RE_RECTION_ELIDEE):
            for joint, nom in motif.findall(bas):
                cle = (nom, joint)
                compte[cle] = compte.get(cle, 0) + 1
    out = pl.DataFrame(
        [{"nom": n, "joint": j, "occurrences": c} for (n, j), c in compte.items()],
        schema={"nom": pl.String, "joint": pl.String, "occurrences": pl.Int64},
    ).sort(["nom", "joint"])  # tri explicite : artefact versionné
    LexiqueRectionsSchema.validate(out)
    return out


def build_lexique_casse(csv: pl.DataFrame, policy: ChapterPolicy) -> pl.DataFrame:
    """`(mot)` attestés en minuscule — **Index exclu**.

    L'Index capitalise toute tête d'entrée : il ne peut pas témoigner de
    la casse naturelle d'un terme.
    """
    hors_index = _sans_famille(csv, policy, "INDEX")
    mots = (
        hors_index.select(pl.col("texte").str.split(" ").alias("mot"))
        .explode("mot")
        .select(pl.col("mot").str.strip_chars(',;()"').alias("mot"))
        .filter(pl.col("mot").str.contains(r"^[a-zà-ÿ][\wà-ÿ-]*$"))
        .unique()
        .sort("mot")
    )
    LexiqueCasseSchema.validate(mots)
    return mots


def build_lexique_juxtaposition(csv: pl.DataFrame, policy: ChapterPolicy) -> pl.DataFrame:
    """`(mot, occurrences)` en juxtaposition nue — **CepiDc exclu**.

    CepiDc est télégraphique et supprime les articles : l'y inclure ferait
    passer tout nom pour un adjectif.
    """
    hors_cepidc = _sans_famille(csv, policy, "CEPIDC")
    compte: dict[str, int] = {}
    for texte in hors_cepidc["texte"].drop_nulls().to_list():
        for fragment in RE_FRONTIERE.split(_normalise_apostrophes(texte.lower())):
            mots = RE_MOT.findall(fragment)
            for i in range(1, len(mots)):
                if mots[i - 1] not in MOTS_OUTILS and len(mots[i]) > 2:
                    compte[mots[i]] = compte.get(mots[i], 0) + 1
    out = pl.DataFrame(
        [{"mot": m, "occurrences": c} for m, c in compte.items()],
        schema={"mot": pl.String, "occurrences": pl.Int64},
    ).sort("mot")
    LexiqueJuxtapositionSchema.validate(out)
    return out


def _sans_famille(csv: pl.DataFrame, policy: ChapterPolicy, famille: str) -> pl.DataFrame:
    """Retire les lignes dont la source appartient à `famille`."""
    libelles = [
        lib for lib in csv["source"].unique().to_list() if policy.famille_de(lib) == famille
    ]
    return csv.filter(~pl.col("source").is_in(libelles))


def to_parquet(csv: pl.DataFrame, policy: ChapterPolicy, output_dir: Path) -> dict[str, Path]:
    """Construit et écrit les trois lexiques. Retourne leurs chemins."""
    output_dir.mkdir(parents=True, exist_ok=True)
    chemins = {
        "rections": output_dir / RECTIONS_FILENAME,
        "casse": output_dir / CASSE_FILENAME,
        "juxtaposition": output_dir / JUXTAPOSITION_FILENAME,
    }
    build_lexique_rections(csv).write_parquet(chemins["rections"])
    build_lexique_casse(csv, policy).write_parquet(chemins["casse"])
    build_lexique_juxtaposition(csv, policy).write_parquet(chemins["juxtaposition"])
    return chemins


def load_lexicons(processed_dir: Path) -> Lexiques:
    """Charge les trois artefacts en structures de lookup."""
    rections_df = pl.read_parquet(processed_dir / RECTIONS_FILENAME)
    rections: dict[str, dict[str, int]] = {}
    for nom, joint, n in rections_df.iter_rows():
        rections.setdefault(nom, {})[joint] = n
    casse = frozenset(pl.read_parquet(processed_dir / CASSE_FILENAME)["mot"].to_list())
    jux_df = pl.read_parquet(processed_dir / JUXTAPOSITION_FILENAME)
    juxtaposition = dict(jux_df.iter_rows())
    return Lexiques(rections=rections, casse=casse, juxtaposition=juxtaposition)


__all__ = (
    "CASSE_FILENAME",
    "FAMILLE_A",
    "FAMILLE_DE",
    "JUXTAPOSITION_FILENAME",
    "RECTIONS_FILENAME",
    "Lexiques",
    "build_lexique_casse",
    "build_lexique_juxtaposition",
    "build_lexique_rections",
    "load_lexicons",
    "to_parquet",
)
