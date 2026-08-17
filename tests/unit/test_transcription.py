"""Intégrité des transcriptions curées du guide méthodologique.

Ce que ces tests protègent
--------------------------
La règle de curation — « reformatage sans réécriture » — est une
consigne. Une consigne qu'aucun test ne contrôle dérive en trois
articles, et la dérive est invisible : un curé paraphrasé se lit très
bien, il ne cesse simplement plus d'être une transcription.

Chaque test ci-dessous correspond à une manière précise de violer la
règle. S'il en manque une, c'est une porte ouverte.
"""

from __future__ import annotations

import pytest

from recode_icd.recommendations.transcription import (
    Suppressions,
    charge_suppressions,
    partitionne_cure,
    verifie_integrite,
)

pytestmark = pytest.mark.unit

BRUT = """# Guide méthodologique MCO 2026 — ARTICLE TÉMOIN
# Commande : pdftotext -layout -f 1 -l 2 …
# ---------------------------------------------------------------------

                                                      78

ARTICLE TÉMOIN

Le codage des AVC constitués fait appel, à la phase aigüe, aux
                                      4
catégories I60 à I63 .

4
    Note de bas de page du guide.
"""

CURE = """<!-- transcription curée de extraits_bruts/temoin.txt -->

## ARTICLE TÉMOIN

Le codage des AVC constitués fait appel, à la phase aigüe, aux
catégories I60 à I63[^4].

## Notes de bas de page

[^4] Note de bas de page du guide.
"""

SUPPRESSIONS = Suppressions((r"\s*\d{1,3}\s*", r"\s*"))


def _verifie(cure: str):
    return verifie_integrite(BRUT, cure, SUPPRESSIONS, "temoin")


def test_transcription_fidele_est_conforme() -> None:
    """Le cas nominal : lignes recollées, note relocalisée, titre balisé."""
    rapport = _verifie(CURE)
    assert rapport.conforme, rapport.message()
    assert rapport.n_mots_notes > 0, "la note doit être partitionnée à part"


def test_paraphrase_detectee() -> None:
    """« fait appel » → « recourt » : un mot changé casse le test.

    C'est la violation la plus dangereuse parce que la plus lisible :
    rien dans le curé ne signale qu'il ne dit plus ce que dit le guide.
    """
    rapport = _verifie(CURE.replace("fait appel, à", "recourt, à"))
    assert not rapport.conforme
    assert "fait" in rapport.manquants and "appel," in rapport.manquants
    assert "recourt," in rapport.ajoutes


def test_condensation_detectee() -> None:
    """Une phrase raccourcie perd des mots — le compte le voit."""
    rapport = _verifie(CURE.replace("fait appel, à la phase aigüe, aux", "fait appel aux"))
    assert not rapport.conforme
    assert rapport.manquants


def test_ajout_de_texte_detecte() -> None:
    """La curation reformate, elle ne rédige pas.

    Une remarque de curation a sa place — en commentaire HTML, pas dans
    le texte. Le test doit refuser la seconde forme.
    """
    rapport = _verifie(CURE.replace("catégories I60 à I63", "catégories I60 à I63 (sic)"))
    assert not rapport.conforme
    assert "(sic)" in rapport.ajoutes


def test_annotation_en_commentaire_est_invisible() -> None:
    """La forme AUTORISÉE de signalement d'une erreur du guide.

    « Les erreurs de l'original se signalent en marge, ne se réparent
    pas » : le commentaire HTML est cette marge, et il ne doit pas
    compter dans le flux de mots.
    """
    annote = CURE.replace(
        "catégories I60 à I63[^4].",
        "catégories I60 à I63[^4]. <!-- le guide écrit I63, la table dit I64 -->",
    )
    assert _verifie(annote).conforme


def test_correction_du_texte_du_guide_detectee() -> None:
    """Réparer une coquille du guide est une violation, pas un service.

    Un guide dont on a corrigé le texte ne prouve plus rien sur ce que
    le guide dit — et c'est précisément ce que la base de recommandations
    doit pouvoir attester.
    """
    rapport = _verifie(CURE.replace("aigüe", "aiguë"))
    assert not rapport.conforme, (
        "corriger « aigüe » en « aiguë » doit échouer : la graphie du guide "
        "fait partie de ce qu'on transcrit"
    )


def test_reordonnancement_du_corps_detecte() -> None:
    """Deux phrases permutées conservent le multiensemble de mots.

    Seul le contrôle d'ordre les attrape : c'est la raison d'être du
    test de sous-séquence, que le comptage seul ne remplace pas.
    """
    permute = CURE.replace("à la phase aigüe, aux", "aux à la phase aigüe,")
    rapport = _verifie(permute)
    assert not rapport.conforme
    assert rapport.desordre_corps is not None
    assert not rapport.manquants and not rapport.ajoutes, (
        "le multiensemble est intact — c'est bien l'ordre, et lui seul, qui a bougé"
    )


def test_note_relocalisee_ne_compte_pas_comme_desordre() -> None:
    """Le déplacement des notes vers la fin est AUTORISÉ.

    C'est pourquoi l'ordre est contrôlé séparément sur le corps et sur
    les notes, et jamais sur le fichier entier — un contrôle global
    refuserait la seule réorganisation qu'on permet.
    """
    rapport = _verifie(CURE)
    assert rapport.desordre_corps is None
    assert rapport.desordre_notes is None


def test_suppression_non_declaree_echoue() -> None:
    """Sans la déclaration, le numéro de page fait échouer le test.

    Le sens de `suppressions.yaml` : rien ne disparaît en silence. Une
    heuristique compréhensive avalerait aussi les vraies pertes.
    """
    rapport = verifie_integrite(BRUT, CURE, Suppressions(), "temoin")
    assert not rapport.conforme
    assert "78" in rapport.manquants


def test_partition_corps_notes() -> None:
    corps, notes = partitionne_cure(CURE)
    assert "Note" in notes and "Note" not in corps
    assert "codage" in corps and "codage" not in notes


def test_balisage_markdown_ne_retire_aucun_mot() -> None:
    """Titres et filets de tableau disparaissent, leurs mots restent.

    Un tableau reconstruit doit rendre exactement les mots que le rendu
    en colonnes avait dispersés — sinon toute reconstruction de tableau
    ferait échouer le test, et la consigne serait inapplicable.
    """
    corps, _ = partitionne_cure("## Titre\n\n| a | b |\n|---|---|\n| c | d |\n")
    assert corps == ["Titre", "a", "b", "c", "d"]


def test_suppressions_commun_fusionne_dans_chaque_article(tmp_path) -> None:
    chemin = tmp_path / "suppressions.yaml"
    chemin.write_text(
        "commun:\n  lignes_regex: ['A']\narticles:\n  avc:\n    lignes_regex: ['B']\n",
        encoding="utf-8",
    )
    charge = charge_suppressions(chemin)
    assert charge["avc"].lignes_regex == ("A", "B")
    assert charge[""].lignes_regex == ("A",)


def test_suppressions_absentes_ne_cassent_pas(tmp_path) -> None:
    """Tant que le chantier B n'a rien curé, le fichier peut manquer."""
    assert charge_suppressions(tmp_path / "inexistant.yaml")[""].lignes_regex == ()
