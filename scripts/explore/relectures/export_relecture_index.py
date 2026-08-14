"""Export CSV d'un échantillon d'entrées d'Index pour relecture humaine.

Pourquoi ce script existe
-------------------------
R3 a été calibrée par relectures successives (v1 → v5) : à chaque
itération, un échantillon tiré au sort est relu à la main et chaque
entrée étiquetée `correcte` / `degradee` / `fautive`. La règle d'arrêt
— zéro `fautive`, ≤ 15 % `degradee` sans cause corrigeable par motif —
n'a de sens que si l'échantillon est **reproductible** et si la
relecture est **traçable dans le temps**.

Ce script produit le support de cette relecture : un CSV par graine,
avec la colonne `etiquette` laissée **vide**, à remplir à la main.

⚠ **La relecture de forme ne contrôle pas le périmètre.** Une entrée
peut être parfaitement bien formée et pourtant désigner autre chose que
le code (« oculopathie syphilitique » pour une entrée `nca`). Ce sont
deux validations distinctes ; ce CSV ne sert qu'à la première.

La colonne `version_regle` est indispensable : sans elle, deux CSV de
graines identiques mais de versions différentes sont indiscernables, et
comparer les taux d'une version à l'autre devient impossible.

Usage
-----
    uv run python scripts/explore/relectures/export_relecture_index.py \
        --graine 4242 --taille 100
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import polars as pl

from recode_icd.lexicons import load_lexicons
from recode_icd.normalize_index import normalise
from recode_icd.policy import DEFAULT_LEXICONS_DIR, load_policy
from recode_icd.utils.loaders_dev import load_exploration_context

SORTIE = Path(__file__).parent

#: Version de la règle R3. **À incrémenter à chaque changement de
#: comportement du normalisateur**, sinon les relectures de deux
#: versions se mélangent silencieusement.
VERSION_REGLE = "v5"

LIBELLE_INDEX = "CIM-10 index"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graine", type=int, default=4242)
    parser.add_argument("--taille", type=int, default=100)
    parser.add_argument(
        "--inclure-ecartees",
        action="store_true",
        help=(
            "Échantillonner aussi les entrées écartées par R3. Par défaut "
            "on ne relit que les entrées RETENUES : ce sont elles qui "
            "atterrissent dans les fiches. Les écartées se relisent "
            "séparément, avec une autre question — « l'exclusion est-elle "
            "justifiée ? » et non « la forme est-elle correcte ? »."
        ),
    )
    args = parser.parse_args()

    ctx = load_exploration_context()
    policy = load_policy()
    lexiques = load_lexicons(DEFAULT_LEXICONS_DIR)
    config = policy.normalisation_index

    flat = ctx.flat.collect() if isinstance(ctx.flat, pl.LazyFrame) else ctx.flat
    index = flat.filter(pl.col("source") == LIBELLE_INDEX).select("code", "texte").drop_nulls()

    lignes: list[dict[str, object]] = []
    for code, texte in index.iter_rows():
        diag = normalise(texte, lexiques, config)
        retenue = diag.forme is not None
        if retenue or args.inclure_ecartees:
            lignes.append(
                {
                    "code": code,
                    "texte_source": texte,
                    "forme_normalisee": diag.forme or "",
                    "etiquette": "",  # à remplir à la main
                    "motif_exclusion": diag.motif_exclusion or "",
                    "version_regle": VERSION_REGLE,
                }
            )

    # Tirage reproductible : on trie avant d'échantillonner, sinon
    # l'ordre d'itération du DataFrame décide du tirage.
    lignes.sort(key=lambda ligne: (str(ligne["code"]), str(ligne["texte_source"])))
    rng = random.Random(args.graine)
    echantillon = rng.sample(lignes, min(args.taille, len(lignes)))
    echantillon.sort(key=lambda ligne: (str(ligne["code"]), str(ligne["texte_source"])))

    suffixe = "_avec_ecartees" if args.inclure_ecartees else ""
    chemin = SORTIE / f"relecture_index_{VERSION_REGLE}_graine{args.graine}{suffixe}.csv"
    pl.DataFrame(echantillon).write_csv(chemin)
    print(f"{len(echantillon)} entrées sur {len(lignes)} → {chemin}")
    print("Remplir la colonne `etiquette` : correcte | degradee | fautive")


if __name__ == "__main__":
    main()
