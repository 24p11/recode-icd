"""Chaque transcription curée est fidèle à son extrait brut.

Ce test est **l'étape 1 du circuit de curation** du chantier B :

    brut  →  curé (ce test vert)  →  relecture RF  →  committé et figé
                                  ↑
                          on ne soumet pas à relecture
                          un curé qui échoue ici

Il se découvre tout seul : tout `.md` déposé dans
`data/guide_mco/extraits/` est vérifié. Rien à déclarer, donc rien à
oublier de déclarer.

Tant que le chantier B n'a produit aucun curé, le test **skippe** — et
c'est un état normal, pas un trou de couverture : `test_transcription.py`
couvre la logique sur données synthétiques.
"""

from __future__ import annotations

import hashlib
import re

import polars as pl
import pytest

from recode_icd.recommendations.transcription import (
    BRUTS_DIR,
    CURES_DIR,
    articles_cures,
    charge_curation,
    partitionne_cure,
    verifie_article,
)

pytestmark = pytest.mark.regression

_EXTRACTION = BRUTS_DIR.parent / "extraction"

_ARTICLES = articles_cures()


@pytest.mark.skipif(not _ARTICLES, reason="Aucune transcription curée (chantier B non commencé).")
@pytest.mark.parametrize("article", _ARTICLES or ["—"])
def test_transcription_fidele_a_son_brut(article: str) -> None:
    """Le flux de mots du curé égale celui du brut, aux suppressions déclarées près.

    Si ce test casse, **ne pas élargir `curation.yaml` pour le faire
    passer** : le message dit précisément quels mots ont été perdus ou
    ajoutés. Une suppression ne s'ajoute que si elle est justifiée en
    tant que telle — un artefact de pagination, pas un paragraphe gênant.
    """
    rapport = verifie_article(article)
    assert rapport.conforme, rapport.message()


@pytest.mark.skipif(not _ARTICLES, reason="Aucune transcription curée (chantier B non commencé).")
@pytest.mark.parametrize("article", _ARTICLES or ["—"])
def test_chaque_cure_a_son_brut(article: str) -> None:
    """Un curé sans brut n'est pas vérifiable, donc pas recevable.

    Le cas se produirait si un article était curé à la main sans passer
    par `scripts/extraire_guide_mco.sh` — auquel cas plus rien ne
    garantit que la transcription vient bien du PDF.
    """
    assert (BRUTS_DIR / f"{article}.txt").is_file(), (
        f"« {article} » a un curé sans extrait brut. Régénérer le brut avec "
        f"scripts/extraire_guide_mco.sh avant toute relecture."
    )


def test_le_repertoire_des_cures_existe() -> None:
    """Le répertoire et sa déclaration de suppressions sont versionnés.

    Ils sont créés vides à l'ouverture du pattern : le chantier B dépose
    ses curés dedans sans avoir à inventer l'emplacement ni le format de
    déclaration.
    """
    assert CURES_DIR.is_dir()
    assert (CURES_DIR / "curation.yaml").is_file()


def test_les_bruts_du_pilote_sont_toujours_la() -> None:
    """Le pilote reste ancré sur les bruts — on ne réancre rien.

    Ses citations ont été contre-lues et validées ligne à ligne contre
    ces fichiers. Les déplacer ou les régénérer autrement invaliderait
    la vérification déjà faite ; les numéros de ligne des candidates y
    renvoient directement.
    """
    for article in (
        "avc",
        "anemie_posthemorragique_d62",
        "chapitre_xxi",
        "malnutrition_denutrition",
    ):
        assert (BRUTS_DIR / f"{article}.txt").is_file(), (
            f"L'extrait brut « {article} » a disparu : les citations du pilote "
            f"y renvoient par numéro de ligne."
        )


# -- verrous ajoutés après une corruption réelle des bruts --------------


def test_les_bruts_sont_intacts() -> None:
    """Les extraits bruts n'ont pas bougé d'un octet.

    **Pourquoi ce test existe** : le 2026-08-17, les quatre bruts ont été
    silencieusement mutilés — numéros de page, titres de section et
    lignes vides supprimés — et la corruption a été committée puis
    poussée. `test_les_bruts_du_pilote_sont_toujours_la` ne vérifiait que
    l'existence des fichiers, pas leur contenu : elle est passée au vert
    sur des fichiers abîmés.

    Or les citations du pilote renvoient à ces fichiers **par numéro de
    ligne**. Toute modification décale les ancres et invalide une
    contre-lecture déjà faite.

    Si ce test casse après une régénération légitime (nouvelle version de
    poppler, nouveau millésime du guide), régénérer le manifeste —
    `cd data/guide_mco/extraits_bruts && shasum -a 256 *.txt > SHA256SUMS`
    — **et revérifier les plages de lignes des citations**, que
    `test_les_citations_retombent_dans_leur_plage` contrôle.
    """
    manifeste = BRUTS_DIR / "SHA256SUMS"
    assert manifeste.is_file(), f"Manifeste absent : {manifeste}"

    attendus = {}
    for ligne in manifeste.read_text(encoding="utf-8").splitlines():
        empreinte, nom = ligne.split(maxsplit=1)
        attendus[nom.strip()] = empreinte

    for nom, empreinte in sorted(attendus.items()):
        chemin = BRUTS_DIR / nom
        assert chemin.is_file(), f"{nom} a disparu des extraits bruts."
        obtenue = hashlib.sha256(chemin.read_bytes()).hexdigest()
        assert obtenue == empreinte, (
            f"{nom} a été modifié. Les citations du pilote y renvoient par "
            f"numéro de ligne : toute modification décale les ancres. "
            f"Restaurer le fichier plutôt que le manifeste."
        )


def test_les_citations_retombent_dans_leur_plage() -> None:
    """Chaque citation de candidate se trouve bien aux lignes déclarées.

    **Pourquoi ce test existe** : deux citations portaient une plage
    décalée d'une ligne (`GM2026-V-D62-03`, `GM2026-V-DEN-16`). Le texte
    cité était exact — c'est la coordonnée qui était fausse, et rien ne
    le signalait. Une citation dont on ne peut plus retrouver la source
    n'est plus une citation.

    Le contrôle porte sur les **cinq premiers mots** de chaque fragment :
    les citations élident les puces et les incises avec « […] », donc
    exiger la chaîne entière produirait des faux positifs. Les
    apostrophes sont normalisées, le guide employant `’`.

    ⚠ Ne pas élargir une plage pour faire passer ce test : c'est la
    citation qu'on corrige, pas la mesure.
    """
    csv = _EXTRACTION / "candidates_recommendations.csv"
    if not csv.is_file():
        pytest.skip("Candidates absentes.")

    def _normalise(texte: str) -> str:
        return " ".join(texte.replace("'", "’").split())

    hors_plage: list[str] = []
    for ligne in pl.read_csv(csv).iter_rows(named=True):
        # `citation_fichier` porte l'ancrage : un `.txt` renvoie au brut,
        # un `.md` à la transcription curée. Les deux coexistent — le
        # pilote reste ancré sur les bruts (ses citations sont validées),
        # les candidates issues d'un curé s'ancrent sur lui.
        nom = str(ligne["citation_fichier"])
        racine = CURES_DIR if nom.endswith(".md") else BRUTS_DIR
        source = (racine / nom).read_text(encoding="utf-8")
        # `split("\n")` et NON `splitlines()` : pdftotext insère des sauts
        # de page \f, que `splitlines()` compte comme des fins de ligne —
        # les numéros seraient décalés par rapport à un éditeur ou à grep.
        lignes_source = source.split("\n")
        zone = _normalise(
            " ".join(
                " ".join(lignes_source[int(debut) - 1 : int(fin or debut)])
                for debut, fin in re.findall(r"L(\d+)(?:-(\d+))?", str(ligne["citation_lignes"]))
            )
        )
        for fragment in str(ligne["citation"]).split(" — "):
            debut_frag = _normalise(" ".join(re.sub(r"\[…\]", " ", fragment).split()[:5]))
            if debut_frag and debut_frag not in zone:
                hors_plage.append(
                    f"{ligne['rec_id']} ({ligne['citation_lignes']}) : « {debut_frag}… »"
                )
                break

    assert not hors_plage, "Citations introuvables aux lignes déclarées :\n  " + "\n  ".join(
        hors_plage
    )


def test_les_cures_figes_sont_intacts() -> None:
    """Un curé validé ne change que par mise à jour explicite du manifeste.

    Le gel est le dernier étage du procédé : sortie machine tracée,
    relecture humaine, **puis empreinte**. Sans elle, une régénération
    ou une édition distraite défait une validation sans que rien ne le
    signale — c'est déjà arrivé aux extraits bruts le 2026-08-17.

    Régénérer après une mise à jour VOULUE :
    `cd data/guide_mco/extraits && shasum -a 256 *.md > SHA256SUMS`,
    puis mettre à jour `relecteur` et `date` dans `curation.yaml`, et
    revérifier les plages de citation qui pointent vers ce curé.
    """
    manifeste = CURES_DIR / "SHA256SUMS"
    assert manifeste.is_file(), f"Manifeste absent : {manifeste}"
    for ligne in manifeste.read_text(encoding="utf-8").splitlines():
        empreinte, nom = ligne.split(maxsplit=1)
        chemin = CURES_DIR / nom.strip()
        assert chemin.is_file(), f"{nom} a disparu des transcriptions curées."
        assert hashlib.sha256(chemin.read_bytes()).hexdigest() == empreinte, (
            f"{nom} a changé depuis sa validation. Si le changement est voulu, "
            f"régénérer le manifeste ET mettre à jour relecteur/date dans "
            f"curation.yaml — sinon restaurer le fichier."
        )


def test_chaque_cure_fige_porte_son_relecteur() -> None:
    """Le manifeste dit qu'un curé n'a pas bougé, pas qu'il a été relu.

    Les deux vont ensemble : une empreinte sans relecteur fige une
    sortie machine, ce que le procédé refuse — la relecture est une
    étape structurelle, pas transitoire.
    """
    # Le manifeste liste les curés FIGÉS. Un curé fraîchement produit et
    # soumis à relecture n'y figure pas encore, et n'a donc pas de
    # relecteur — c'est un état normal du circuit, pas un manquement.
    manifeste = CURES_DIR / "SHA256SUMS"
    figes = [
        ligne.split(maxsplit=1)[1].strip().removesuffix(".md")
        for ligne in manifeste.read_text(encoding="utf-8").splitlines()
    ]
    curations = charge_curation(CURES_DIR / "curation.yaml")
    for article in figes:
        curation = curations.get(article)
        assert curation is not None and curation.relecteur and curation.date_validation, (
            f"« {article} » est figé sans relecteur ni date. Renseigner "
            f"`validations` dans curation.yaml."
        )


def test_aucun_appel_de_note_ne_subsiste_dans_le_corps() -> None:
    """Aucun nombre isolé de la plage des appels ne reste dans un curé.

    Un appel hissé que le rendu a laissé seul sur sa ligne coupe la
    phrase en deux à la lecture — deux subsistaient dans le chapitre XXI
    (41 et 42) et hachaient le paragraphe Z51. Le curé porte des
    marqueurs `[^n: …]`, jamais des nombres nus.

    Le contrôle d'intégrité ne les voit pas : ils sont dans le brut
    aussi, donc conservés des deux côtés. C'est un invariant de LISIBILITÉ,
    qui ne se déduit d'aucune comparaison.
    """
    curations = charge_curation(CURES_DIR / "curation.yaml")
    for article in articles_cures():
        appels = {str(a) for a in curations[article].appels_notes}
        if not appels:
            continue
        corps, _ = partitionne_cure((CURES_DIR / f"{article}.md").read_text(encoding="utf-8"))
        nus = sorted({mot for mot in corps if mot in appels})
        assert not nus, (
            f"« {article} » : appel(s) de note resté(s) nu(s) dans le corps — "
            f"{nus}. Ils coupent la phrase à la lecture ; leur note doit être "
            f"repliée à leur place par un marqueur."
        )
