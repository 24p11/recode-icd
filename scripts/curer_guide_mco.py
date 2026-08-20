"""Produit un premier jet de transcription curée à partir d'un extrait brut.

**Un jet, pas un livrable.** Le résultat passe par le test d'intégrité,
puis par une relecture humaine — c'est elle qui juge de ce qu'aucune
machine ne voit : structure des tableaux, ancrage des notes, contenu que
`pdftotext` a perdu (cf. le §4.1 de l'article dénutrition).

Ce que le script fait mécaniquement :

- découpe l'article selon les bornes déclarées dans `curation.yaml` ;
- écarte les lignes réduites à un nombre — numéro de page, numéro de
  définition de note, appel hissé seul sur sa ligne par le rendu ;
- recolle les lignes qu'une mise en page en colonnes a coupées ;
- replie chaque note à son point d'appel, sous la forme `[^n: texte]`,
  le marqueur venant APRÈS le mot complet, ponctuation comprise ;
- balise les titres de section.

Ce qu'il ne fait pas, et ne peut pas faire : reconstruire un tableau
absent du brut. Les restitutions se déclarent à la main dans
`curation.yaml`, avec leur page PDF.

    uv run python scripts/curer_guide_mco.py avc
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from recode_icd.recommendations.transcription import (
    BRUTS_DIR,
    CURES_DIR,
    charge_curation,
    verifie_article,
)

#: Titre de section : « 1. », « 4.1 », « 3.2. », ou le titre d'article.
_RE_TITRE_NUMEROTE = re.compile(r"^\d+(\.\d+)*\.?\s+\S")

#: Règle numérotée à la mode du guide : « 1°) », « 6°) ».
_RE_REGLE_NUMEROTEE = re.compile(r"^\d+°\)")

#: Sous-titre centré : le guide ne les numérote pas, il les INDENTE.
#: C'est le seul signal disponible, et il disparaît au recollage — on
#: le capte donc à la découpe, avec une sentinelle que `balise` consomme.
_SENTINELLE_TITRE = "\x00"
_INDENT_TITRE = 8


def decoupe(article: str) -> tuple[list[str], dict[str, str]]:
    """`(lignes du corps, notes par numéro)` de l'article borné."""
    curation = charge_curation().get(article)
    if curation is None or curation.bornes is None:
        raise SystemExit(
            f"Aucune borne déclarée pour « {article} » dans curation.yaml. "
            f"Les déclarer avant de curer : sans elles, le jet embarquerait "
            f"le débordement de pages sur l'article voisin."
        )
    b = curation.bornes
    brutes = (BRUTS_DIR / f"{article}.txt").read_text(encoding="utf-8").split("\n")
    lignes = brutes[b.premiere_ligne - 1 : b.derniere_ligne]
    appels = {str(a) for a in curation.appels_notes}

    notes: dict[str, str] = {}
    corps: list[str] = []
    i = 0
    while i < len(lignes):
        ligne = lignes[i]
        # Définition de note : le numéro seul, en colonne 0.
        if ligne in appels:
            j, buf = i + 1, []
            while j < len(lignes) and lignes[j].strip() and not re.fullmatch(r"\d{1,3}", lignes[j]):
                if not re.fullmatch(r"\s*\d{1,3}\s*", lignes[j]):
                    buf.append(lignes[j].strip())
                j += 1
            notes[ligne] = " ".join(buf)
            i = j
            continue
        # Numéro de page, ou appel hissé seul sur sa ligne : pure mise
        # en page, aucun texte.
        if re.fullmatch(r"\s+\d{1,3}\s*", ligne):
            i += 1
            continue
        # Sous-titre centré : indenté, seul entre deux lignes vides, sans
        # ponctuation finale.
        nu = ligne.strip()
        isole = (i == 0 or not lignes[i - 1].strip()) and (
            i + 1 >= len(lignes) or not lignes[i + 1].strip()
        )
        if (
            nu
            and isole
            and len(ligne) - len(ligne.lstrip()) >= _INDENT_TITRE
            and not nu.endswith((".", ";", ":"))
            and not nu.startswith(("-", "•", "*"))
            and len(nu) < 100
        ):
            corps.append(_SENTINELLE_TITRE + nu)
            i += 1
            continue
        corps.append(ligne)
        i += 1
    return corps, notes


def en_blocs(corps: list[str]) -> list[str]:
    """Recolle les lignes coupées ; titres et puces gardent leur ligne."""
    blocs: list[str] = []
    tampon: list[str] = []
    for ligne in corps:
        nu = ligne.strip()
        if not nu:
            if tampon:
                blocs.append(" ".join(tampon))
                tampon = []
            continue
        if (
            _RE_TITRE_NUMEROTE.match(nu)
            or _RE_REGLE_NUMEROTEE.match(nu)
            or nu.startswith((_SENTINELLE_TITRE, "-", "•", "*"))
        ):
            if tampon:
                blocs.append(" ".join(tampon))
                tampon = []
            blocs.append(nu)
            continue
        tampon.append(nu)
    if tampon:
        blocs.append(" ".join(tampon))
    return blocs


def replie_notes(texte: str, notes: dict[str, str]) -> tuple[str, list[str]]:
    """Insère `[^n: …]` après le mot portant l'appel. Retourne les orphelines.

    L'appel est cherché **en fin de token** : c'est un exposant, il se
    place après le mot (« précision58. », « kg/m261; »). Une note dont
    l'appel reste introuvable est signalée plutôt que placée au hasard.
    """
    orphelines: list[str] = []
    for numero in sorted(notes, key=int):
        motif = re.compile(rf"(\S*?{numero}[;:.,!?»)]*)(?=\s|$)")
        trouve = motif.search(texte)
        if trouve is None:
            orphelines.append(numero)
            continue
        texte = texte[: trouve.end()] + f" [^{numero}: {notes[numero]}]" + texte[trouve.end() :]
    return texte, orphelines


def balise(blocs: list[str], titre_article: str) -> list[str]:
    sortie: list[str] = []
    for bloc in blocs:
        nu = bloc.strip()
        if nu.startswith(_SENTINELLE_TITRE):
            sortie.append(f"### {nu.lstrip(_SENTINELLE_TITRE)}")
        elif nu == titre_article:
            sortie.append(f"## {nu}")
        elif _RE_REGLE_NUMEROTEE.match(nu) or re.match(r"^\d+\.\s", nu):
            sortie.append(f"### {nu}")
        elif re.match(r"^\d+\.\d+", nu):
            sortie.append(f"#### {nu}")
        else:
            sortie.append(nu)
    return sortie


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("article")
    args = parser.parse_args()

    curation = charge_curation()[args.article]
    corps, notes = decoupe(args.article)
    texte, orphelines = replie_notes("\n\n".join(en_blocs(corps)), notes)
    titre = (curation.bornes.titre if curation.bornes else "").strip()
    contenu = "\n\n".join(balise(texte.split("\n\n"), titre))

    entete = (
        f"<!-- Transcription curée — {titre}\n"
        f"     Premier jet produit par scripts/curer_guide_mco.py, À RELIRE.\n"
        f"     Brut : extraits_bruts/{args.article}.txt, "
        f"lignes {curation.bornes.premiere_ligne}-{curation.bornes.derniere_ligne}.\n"
        f"     Curation déclarée : extraits/curation.yaml.\n"
        f"     Le test garantit qu'aucun mot n'a bougé ; il ne dit rien des\n"
        f"     tableaux, de l'ancrage des notes, ni de ce que pdftotext a perdu. -->\n\n"
    )
    cible = CURES_DIR / f"{args.article}.md"
    cible.write_text(entete + contenu + "\n", encoding="utf-8")
    print(f"Écrit : {cible.relative_to(Path.cwd())}")
    if orphelines:
        print(f"⚠ notes sans appel trouvé : {orphelines} — à placer à la main")
    print(verifie_article(args.article).message())


if __name__ == "__main__":
    main()
