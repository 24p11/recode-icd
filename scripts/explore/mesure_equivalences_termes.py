"""Mesures d'ouverture du chantier « dictionnaire d'équivalences » (2026-10-22).

`codeur` demande des correspondances entre MOTS (abréviations, variantes
morphologiques et savantes), indépendantes des codes, pour élargir sa
recherche. Ce script mesure, sans rien modifier, ce que les 110 000
formulations livrées contiennent déjà :

A. les abréviations distinctes (tokens tout-majuscules) et leur
   fréquence, par source — CepiDc étant du langage réel de certificat ;
B. les expansions candidates par co-occurrence sur le MÊME code
   (heuristique des initiales : « IDM » ↔ « Infarctus Du Myocarde ») —
   le rendement mesure ce que l'auto-extraction peut donner ;
C. les familles morphologiques du vocabulaire (tumeur/tumoral,
   rénal/rénale…) par préfixe commun — l'ordre de grandeur du besoin
   en variantes ;
D. ce que les mesures NE couvrent PAS : variantes savantes
   (rein/rénal, cœur/cardiaque) indétectables mécaniquement, et la
   fréquence en CRH réels (corpus hors dépôt — les journaux de
   recherche de codeur seront la source d'usage).

Usage
-----
    uv run python scripts/explore/mesure_equivalences_termes.py
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict

import polars as pl

from recode_icd.utils.loaders_dev import load_exploration_context

#: Mots-outils ignorés par l'heuristique des initiales.
_STOP = {
    "de",
    "du",
    "des",
    "la",
    "le",
    "les",
    "l",
    "d",
    "au",
    "aux",
    "et",
    "a",
    "à",
    "en",
    "sans",
    "avec",
    "par",
    "sur",
    "non",
}

RE_ABREV = re.compile(r"\b[A-Z]{2,6}\b")
RE_MOT = re.compile(r"[a-zà-ÿ]{3,}", re.IGNORECASE)


def _plie(texte: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texte.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _initiales(texte: str) -> str:
    mots = [m for m in re.split(r"[\s\-']+", _plie(texte)) if m and m not in _STOP]
    return "".join(m[0] for m in mots).upper()


def main() -> None:
    ctx = load_exploration_context()
    flat = ctx.flat.collect() if isinstance(ctx.flat, pl.LazyFrame) else ctx.flat
    formulations = flat.filter(
        (pl.col("type") == "synonyme")
        & (
            pl.col("source").is_in(["CIM-10 index", "CepiDc 2015"])
            | pl.col("source").str.starts_with("AP-HP")
        )
    ).select("code", "source", "texte")
    libelles = flat.select("code", "libelle").unique()
    print(f"Vivier : {formulations.height} formulations, {formulations['code'].n_unique()} codes")

    # ---- A. Abréviations distinctes et fréquence ---------------------------
    freq: Counter[str] = Counter()
    par_source: dict[str, Counter[str]] = defaultdict(Counter)
    abrev_codes: dict[str, set[str]] = defaultdict(set)
    for r in formulations.iter_rows(named=True):
        for a in set(RE_ABREV.findall(r["texte"] or "")):
            if a in ("SAI", "NCA"):  # méta-termes de classification, pas des abréviations cliniques
                continue
            freq[a] += 1
            par_source[r["source"]][a] += 1
            abrev_codes[a].add(r["code"])
    print(f"\n== A. {len(freq)} abréviations distinctes (tokens MAJ 2-6 lettres, hors SAI/NCA)")
    print("  les 25 plus fréquentes :")
    for a, n in freq.most_common(25):
        print(f"    {a:<6} {n:>5} occ. | {len(abrev_codes[a]):>4} codes")
    cepidc = par_source.get("CepiDc 2015", Counter())
    print(f"  distinctes dans CepiDc (langage réel) : {len(cepidc)}")

    # ---- B. Expansions candidates par co-occurrence même code --------------
    print("\n== B. Expansions candidates (initiales, même code)")
    textes_par_code: dict[str, list[str]] = defaultdict(list)
    for r in formulations.iter_rows(named=True):
        if r["texte"]:
            textes_par_code[r["code"]].append(r["texte"])
    for r in libelles.iter_rows(named=True):
        if r["libelle"]:
            textes_par_code[r["code"]].append(r["libelle"])

    candidats: Counter[tuple[str, str]] = Counter()
    for a, codes in abrev_codes.items():
        if freq[a] < 2:
            continue
        for code in codes:
            for texte in textes_par_code.get(code, []):
                if a in texte:
                    continue  # le texte EST porteur de l'abréviation
                if _initiales(texte) == a and len(texte.split()) >= 2:
                    candidats[(a, _plie(texte))] += 1
    print(f"  paires (abréviation, expansion) candidates : {len(candidats)}")
    print("  exemples (co-occurrence la plus forte) :")
    for (a, exp), n in candidats.most_common(20):
        print(f"    {a:<6} ↔ {exp[:55]:<57} ({n} codes)")

    # ---- C. Familles morphologiques ----------------------------------------
    print("\n== C. Familles morphologiques du vocabulaire")
    vocab: Counter[str] = Counter()
    for r in formulations.iter_rows(named=True):
        for m in RE_MOT.findall(_plie(r["texte"] or "")):
            if len(m) >= 6:
                vocab[m] += 1
    familles: dict[str, set[str]] = defaultdict(set)
    for mot in vocab:
        familles[mot[:6]].add(mot)
    multi = {p: mots for p, mots in familles.items() if len(mots) > 1}
    print(
        f"  vocabulaire (mots ≥ 6 lettres) : {len(vocab)} ; familles par préfixe-6 : {len(familles)}"
    )
    print(f"  familles à plusieurs formes : {len(multi)}")
    for p in ("tumeur", "cardia", "renale", "fractu", "pulmon"):
        if p in familles:
            print(f"    {p}* → {sorted(familles[p])[:6]}")

    # ---- D. Limites déclarées ----------------------------------------------
    print("\n== D. Hors de portée mécanique (à déclarer, jamais deviné)")
    print(
        "  - variantes savantes (rein↔rénal, cœur↔cardiaque, foie↔hépatique) : liste manuelle relue"
    )
    print("  - fréquences en CRH réels : corpus hors dépôt — source = journaux de recherche codeur")
    print("  - ambiguïtés (IRC, IC, PR) : seul un humain tranche les équivalents multiples")


if __name__ == "__main__":
    main()
