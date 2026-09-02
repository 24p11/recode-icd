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
    Curation,
    Restitution,
    charge_curation,
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
catégories I60 à I63[^4: Note de bas de page du guide.].
"""

SUPPRESSIONS = Curation((r"\s*\d{1,3}\s*", r"\s*"))


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
    # « (sic) » absorbe le point qui suit : la ponctuation détachée est
    # recollée au mot précédent, des deux côtés (cf. `_fusionne_ponctuation`).
    assert any("sic" in mot for mot in rapport.ajoutes), rapport.ajoutes


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
    rapport = verifie_integrite(BRUT, CURE, Curation(), "temoin")
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
        "suppressions_mecaniques:\n"
        "  commun:\n    lignes_regex: ['A']\n"
        "  articles:\n    avc:\n      lignes_regex: ['B']\n",
        encoding="utf-8",
    )
    charge = charge_curation(chemin)
    assert charge["avc"].lignes_regex == ("A", "B")
    assert charge[""].lignes_regex == ("A",)


def test_suppressions_absentes_ne_cassent_pas(tmp_path) -> None:
    """Tant que le chantier B n'a rien curé, le fichier peut manquer."""
    assert charge_curation(tmp_path / "inexistant.yaml")[""].lignes_regex == ()


# -- restitutions : le brut est lossy ----------------------------------


def test_restitution_declaree_est_admise() -> None:
    """Du contenu du PDF absent du brut, déclaré, ne fait pas échouer.

    C'est le mécanisme qui rattrape la perte de `pdftotext` : sur le
    pilote, le tableau du §4.1 de l'article dénutrition sort en quatre
    lignes vides. Sans les restitutions, un curé fidèle au PDF serait
    rejeté pour « ajout de texte ».
    """
    cure = CURE.replace(
        "catégories I60 à I63[^4:",
        "| A | B |\n|---|---|\n| 1 | 2 |\n\ncatégories I60 à I63[^4:",
    )
    curation = Curation(
        lignes_regex=SUPPRESSIONS.lignes_regex,
        restitutions=(
            Restitution(
                texte="| A | B |\n|---|---|\n| 1 | 2 |",
                page_pdf=121,
                motif="tableau en image, perdu par pdftotext",
            ),
        ),
    )
    rapport = verifie_integrite(BRUT, cure, curation, "temoin")
    assert rapport.conforme, rapport.message()
    assert rapport.n_mots_restitues == 4


def test_restitution_non_declaree_est_refusee() -> None:
    """Le même contenu, sans déclaration, échoue.

    La déclaration n'est pas une formalité : c'est ce qui distingue
    « j'ai retrouvé un tableau dans le PDF » de « j'ai inventé un
    tableau ». Aucune machine ne peut faire la différence.
    """
    cure = CURE.replace("catégories", "| A | B |\n\ncatégories")
    assert not verifie_integrite(BRUT, cure, SUPPRESSIONS, "temoin").conforme


def test_restitution_declaree_mais_absente_est_signalee() -> None:
    """Une déclaration qui ne sert plus est une déclaration périmée."""
    curation = Curation(
        lignes_regex=SUPPRESSIONS.lignes_regex,
        restitutions=(Restitution(texte="tableau absent", page_pdf=121, motif="…"),),
    )
    rapport = verifie_integrite(BRUT, CURE, curation, "temoin")
    assert rapport.restitutions_absentes


def test_suppression_editoriale_declaree_est_admise() -> None:
    """Un renvoi de couche 2 retiré avec son motif ne fait pas échouer."""
    curation = Curation(
        lignes_regex=SUPPRESSIONS.lignes_regex,
        suppressions_editoriales=(("Note de bas de page du guide.", "renvoi couche 2"),),
    )
    cure = CURE.replace("[^4: Note de bas de page du guide.]", "[^4]")
    rapport = verifie_integrite(BRUT, cure, curation, "temoin")
    assert rapport.conforme, rapport.message()


def test_suppression_editoriale_introuvable_est_signalee() -> None:
    """Le texte déclaré doit exister dans le brut, sinon la déclaration ment."""
    curation = Curation(
        lignes_regex=SUPPRESSIONS.lignes_regex,
        suppressions_editoriales=(("texte qui n'existe pas", "motif"),),
    )
    assert verifie_integrite(BRUT, CURE, curation, "temoin").suppressions_inutiles


def test_note_repliee_est_extraite_du_corps() -> None:
    """`[^n: …]` sort du corps avant le contrôle d'ordre.

    Replier une note la fait remonter avant sa position d'origine — en
    bas de page dans le brut. Sans extraction, le contrôle de
    sous-séquence la refuserait, et le seul déplacement qu'on autorise
    deviendrait impossible.
    """
    corps, notes = partitionne_cure("Texte[^4: contenu de la note] suite.")
    assert corps == ["Texte", "suite."]
    assert notes == ["contenu", "de", "la", "note"]


# -- balisage de liste et appels de note -------------------------------


def test_puces_de_liste_sont_du_balisage() -> None:
    """« • » du guide et « * » du markdown sont deux notations du même rien.

    Les retirer d'un seul côté ferait échouer toute reconstruction de
    liste — et une liste reconstruite est précisément ce qu'on demande
    au curé.
    """
    brut = "# en-tête\n\nA :\n•   premier\n•   second\n"
    cure = "A :\n\n- premier\n- second\n"
    assert verifie_integrite(brut, cure, Curation(), "t").conforme


def test_appel_de_note_colle_au_mot_est_retire_des_deux_cotes() -> None:
    """`pdftotext` colle l'exposant : « précision58. », « kg/m261; ».

    Le curé porte un marqueur `[^58: …]` à la place. Sans ce
    dépouillement, tout article à notes serait rejeté.
    """
    brut = "# en-tête\n\nMalnutrition sans précision58.\n\n58\n   Auxquels s’ajoute O25.\n"
    # Convention : le marqueur se place APRÈS le mot COMPLET, ponctuation
    # comprise. L'insérer à l'intérieur (« précision[^58: …]. ») couperait
    # le token en deux et ferait échouer le contrôle, à juste titre.
    cure = "Malnutrition sans précision58. [^58: Auxquels s’ajoute O25.]\n"
    curation = Curation(lignes_regex=(r"\s*\d{1,3}\s*", r"\s*"), appels_notes=(58,))
    assert verifie_integrite(brut, cure, curation, "t").conforme


def test_appel_non_declare_fait_echouer() -> None:
    """Les appels sont déclarés article par article, jamais devinés.

    Deviner reviendrait à supprimer des nombres qui sont de la donnée.
    """
    brut = "# en-tête\n\nMalnutrition sans précision58.\n"
    cure = "Malnutrition sans précision.\n"
    assert not verifie_integrite(brut, cure, Curation(), "t").conforme


def test_nombre_de_donnee_nest_pas_ampute() -> None:
    """« 2061 » n'est pas « 20 » suivi de l'appel 61.

    Garde-fou : un token entièrement numérique et plus long que l'appel
    est de la donnée. Sans lui, déclarer un appel mutilerait les chiffres
    de l'article — or cet article est plein de seuils.
    """
    brut = "# en-tête\n\nvaleur 2061 mesurée\n"
    cure = "valeur 2061 mesurée\n"
    curation = Curation(appels_notes=(61,))
    assert verifie_integrite(brut, cure, curation, "t").conforme


def test_ponctuation_collee_par_lexposant_est_detachee() -> None:
    """« kg/m261; » devient « kg/m2 ; », la typographie du guide.

    L'exposant collait le point-virgule ; le guide écrit « 18,5 ; »
    partout ailleurs. La forme détachée est produite des deux côtés.
    """
    brut = "# en-tête\n\nIMC < 22 kg/m261; sarcopénie\n"
    cure = "IMC < 22 kg/m2 ; sarcopénie\n"
    curation = Curation(appels_notes=(61,))
    assert verifie_integrite(brut, cure, curation, "t").conforme


# -- codes CIM homographes des numéros de note --------------------------


def test_un_code_cim_nest_pas_un_appel_de_note() -> None:
    """Piège permanent des articles riches en codes Z.

    Sur le chapitre XXI, les numéros de note vont de 23 à 48 — et le
    texte est plein de `Z29`, `Z33`, `Z34`, `Z37`, `Z40`, `Z51.30`…
    Le premier examen annonçait 8 appels possibles pour la note 29 et 5
    pour la 43 : **tous étaient des codes**. Après filtrage, 18 des 19
    notes orphelines n'avaient plus aucun candidat, ce qui a mis sur la
    piste des appels hissés.

    Prendre un code pour un appel place la note à un endroit arbitraire
    ET ampute le code dans le flux de mots — deux dégâts pour un.
    """
    from recode_icd.recommendations.transcription import _depouille

    # « Z29 » et « Z51.30 » ne doivent PAS perdre leurs chiffres quand
    # 29 et 30 sont déclarés comme appels de note.
    mots = ["catégorie", "Z29", "code", "Z51.30", "chimiothérapie29"]
    depouille = _depouille(mots, (29, 30))
    assert "Z29" in depouille, depouille
    assert "Z51.30" in depouille, depouille
    assert "chimiothérapie" in depouille, "l'appel réellement collé à un mot doit, lui, être retiré"


def test_un_code_cim_survit_a_toute_passe() -> None:
    """Invariant ABSOLU du garde unique `est_code_cim`.

    Le piège a mordu TROIS fois, à trois endroits : `Z29` amputé en
    « Z » au dépouillement, la note 38 posée sur « Z38.0 » au placement,
    « Z43.– » transformé en « Z.– » au nettoyage du corps. Chaque fois
    le test d'intégrité restait vert, parce qu'il compare deux artefacts
    du même code.

    D'où un garde unique et cet invariant, affirmé sur des entrées
    choisies et non sur l'égalité de deux sorties.
    """
    from recode_icd.recommendations.transcription import _depouille, est_code_cim

    codes = ["Z29", "Z33", "Z37", "Z38.0", "Z40", "Z43.–", "Z51.30", "I63.–", "G46.0"]
    appels = (*range(23, 49), 58, 61, 63)
    for code in codes:
        assert est_code_cim(code), code
        assert _depouille([code], appels) == [code], code
        assert _depouille([code + ","], appels) == [code + ","], code
