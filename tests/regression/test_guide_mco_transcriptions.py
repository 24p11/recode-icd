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

import pytest

from recode_icd.recommendations.transcription import (
    BRUTS_DIR,
    CURES_DIR,
    articles_cures,
    verifie_article,
)

pytestmark = pytest.mark.regression

_ARTICLES = articles_cures()


@pytest.mark.skipif(not _ARTICLES, reason="Aucune transcription curée (chantier B non commencé).")
@pytest.mark.parametrize("article", _ARTICLES or ["—"])
def test_transcription_fidele_a_son_brut(article: str) -> None:
    """Le flux de mots du curé égale celui du brut, aux suppressions déclarées près.

    Si ce test casse, **ne pas élargir `suppressions.yaml` pour le faire
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
    assert (CURES_DIR / "suppressions.yaml").is_file()


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
