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

#: Titre de section : « 4.1 Outil… », « 4. Consignes générales ».
#:
#: ⚠ Le motif doit exiger une NUMÉROTATION, pas un simple nombre en tête
#: de ligne : « 12 grammes par décilitre chez la femme… » est une phrase
#: coupée par la mise en page, pas un titre. La confondre empêche le
#: recollage et laisse la phrase en deux morceaux — défaut relevé en
#: relecture sur l'article D62.
_RE_TITRE_NUMEROTE = re.compile(r"^\d+(\.\d+)+\.?\s+\S|^\d+\.\s+[A-ZÀ-ÝŒ]")

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
    precedente_vide = True
    for ligne in corps:
        nu = ligne.strip()
        if not nu:
            if tampon:
                blocs.append(" ".join(tampon))
                tampon = []
            precedente_vide = True
            continue
        if (
            _RE_TITRE_NUMEROTE.match(nu)
            or _RE_REGLE_NUMEROTEE.match(nu)
            or nu.startswith((_SENTINELLE_TITRE, "-", "•", "*"))
        ):
            if tampon:
                blocs.append(" ".join(tampon))
                tampon = []
            # Puce du guide (« • ») rendue en markdown : deux notations
            # du même balisage, que le contrôle traite en équivalentes.
            blocs.append("- " + nu[1:].strip() if nu[0] in "•*-" else nu)
            precedente_vide = False
            continue
        # Suite d'une puce coupée par la mise en page : elle appartient à
        # l'item précédent, pas à un paragraphe neuf. Le D62 n'a pas de
        # puce et n'exerçait donc pas ce cas — l'AVC, si.
        # Une continuation SUIT immédiatement son item : une ligne vide
        # la sépare d'un paragraphe neuf. Sans ce signal, tout ce qui
        # suit la liste s'y engouffre.
        if not tampon and not precedente_vide and blocs and blocs[-1].startswith("- "):
            blocs[-1] += " " + nu
            precedente_vide = False
            continue
        tampon.append(nu)
        precedente_vide = False
    if tampon:
        blocs.append(" ".join(tampon))
    return blocs


class NoteOrpheline(SystemExit):
    """Une note dont l'ancre n'est ni univoque ni déclarée."""


def replie_notes(
    texte: str, notes: dict[str, str], ancres: dict[str, str]
) -> tuple[str, dict[str, str]]:
    """Insère `[^n: …]` après l'appel. Retourne `(texte, provenance)`.

    **Aucune recherche de repli.** Une note se place sur un appel
    UNIVOQUE — le numéro apparaît collé en fin d'un seul token de
    l'article — ou sur une ancre DÉCLARÉE dans `curation.yaml`. Tout
    autre cas est une orpheline, et le script refuse de produire.

    C'est la leçon de la note 4 de l'AVC : l'appel « 4 » se retrouve en
    fin de « I64 », de « 24 heures », de « G81.08 »… Une heuristique de
    repli l'avait placée quarante lignes trop haut, en silence. On ne
    devine pas, on déclare.

    `provenance` dit, pour chaque note, « automatique » ou « déclarée » :
    c'est ce que le tableau de relecture doit montrer.
    """
    provenance: dict[str, str] = {}
    orphelines: list[str] = []

    for numero in sorted(notes, key=int):
        ancre = ancres.get(numero)
        if ancre:
            occurrences = texte.count(ancre)
            if occurrences != 1:
                orphelines.append(
                    f"{numero} : l'ancre déclarée « {ancre[:40]} » apparaît "
                    f"{occurrences} fois, il en faut exactement une"
                )
                continue
            fin = texte.index(ancre) + len(ancre)
            texte = texte[:fin] + f" [^{numero}: {notes[numero]}]" + texte[fin:]
            provenance[numero] = "déclarée"
            continue

        motif = re.compile(rf"\S*?{numero}[;:.,!?»)]*(?=\s|$)")
        trouves = [m for m in motif.finditer(texte) if not m.group(0).strip(";:.,!?»)").isdigit()]
        if len(trouves) != 1:
            orphelines.append(f"{numero} : {len(trouves)} appel(s) possible(s) — ancre à déclarer")
            continue
        fin = trouves[0].end()
        texte = texte[:fin] + f" [^{numero}: {notes[numero]}]" + texte[fin:]
        provenance[numero] = "automatique"

    if orphelines:
        raise NoteOrpheline(
            "Notes orphelines — curé NON produit. Déclarer leur ancre dans "
            "extraits/curation.yaml, section `ancres_notes` :\n  " + "\n  ".join(orphelines)
        )
    return texte, provenance


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
    texte = "\n\n".join(en_blocs(corps))

    # Les suppressions éditoriales déclarées valent des DEUX côtés : le
    # test les retire du brut, le jet doit les retirer du curé. Sans
    # cela, le script réintroduit à chaque passe ce qu'une relecture
    # avait écarté — constaté sur la note 5 du D62, qui appartient à
    # l'article voisin.
    for texte_supprime, _motif in curation.suppressions_editoriales:
        avant = texte
        texte = texte.replace(texte_supprime, "", 1)
        if texte == avant:
            print(f"⚠ suppression déclarée introuvable dans le jet : « {texte_supprime[:60]} »")

    # Recoller la ponctuation détachée AVANT de replier les notes : le
    # rendu détache point et virgule là où un exposant s'intercalait
    # (« (G83.5) . »), et une ancre déclarée doit pouvoir viser la forme
    # normale. La typographie française ne détache ni l'un ni l'autre —
    # contrairement à « ; » et « : », laissés tels quels.
    texte = texte.replace(" .", ".").replace(" ,", ",")
    texte, provenance = replie_notes(texte, notes, curation.ancres_notes)
    titre = (curation.bornes.titre if curation.bornes else "").strip()
    # Deux items de liste consécutifs se suivent d'un simple saut : une
    # ligne vide entre eux couperait la liste en markdown.
    blocs_balises = balise(texte.split("\n\n"), titre)
    morceaux: list[str] = []
    for bloc in blocs_balises:
        if morceaux and bloc.startswith("- ") and morceaux[-1].startswith("- "):
            morceaux[-1] += "\n" + bloc
        else:
            morceaux.append(bloc)
    contenu = "\n\n".join(morceaux)
    # Le rendu détache point et virgule là où un exposant s'intercalait
    # (« (G83.5) . »). La typographie française ne les détache jamais —
    # contrairement à « ; » et « : », qu'on laisse tels quels. Le
    # contrôle traite déjà les deux formes en équivalentes.

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
    if provenance:
        auto = sum(1 for v in provenance.values() if v == "automatique")
        print(
            f"{len(provenance)} note(s) : {auto} par appel univoque, "
            f"{len(provenance) - auto} par ancre déclarée"
        )
    print(verifie_article(args.article).message())


if __name__ == "__main__":
    main()
