"""Résolution de la politique de composition des fiches.

Ce fichier verrouille trois choses distinctes :

1. **La résolution par remplacement.** C'est le piège central du
   chantier : une règle de bloc REMPLACE la règle de chapitre, elle
   n'en hérite pas les champs absents. Un repreneur qui « simplifie »
   en fusionnant rouvrirait des sources en silence.
2. **La couverture bidirectionnelle YAML ↔ `_SOURCE_CSV_MAP`.** Le YAML
   énumère les libellés de sources une seconde fois, en parallèle du
   mapping enum↔libellé : c'est un risque de dérive jumeau de celui que
   le verrou de `test_cards_formulations_sources.py` a fermé. Une source
   ajoutée sans être rangée doit faire échouer la suite.
3. **La dérivation des blocs**, qui n'est pas positionnelle : la CIM-10
   imbrique jusqu'à trois niveaux de bloc.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.exporters.flat_csv import _SOURCE_CSV_MAP
from recode_icd.hierarchie import chapitre_et_blocs
from recode_icd.policy import (
    DEFAULT_POLICY_PATH,
    FAMILLE_INCONNUE,
    PolicyError,
    load_policy,
)

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def policy():  # type: ignore[no-untyped-def]
    return load_policy()


# ----------------------------------------------------------------------
# 1. Résolution par remplacement
# ----------------------------------------------------------------------


def test_defaut_admet_tout(policy) -> None:  # type: ignore[no-untyped-def]
    """Hors plage déclarée, aucune famille n'est retirée."""
    regle = policy.regle_pour("IX", ["I20-I25"])
    assert regle.sources_externes is True
    assert regle.generation_llm is True


def test_chapitre_xviii_garde_les_sources_mais_pas_le_llm(policy) -> None:  # type: ignore[no-untyped-def]
    """XVIII est le seul chapitre à dissocier les deux flags."""
    regle = policy.regle_pour("XVIII", ["R50-R69"])
    assert regle.sources_externes is True
    assert regle.generation_llm is False
    admises = policy.familles_admises("XVIII", ["R50-R69"])
    assert "CEPIDC" in admises, "les sources réelles restent sur XVIII"
    assert "LLM" not in admises, "la génération LLM est interdite sur XVIII"


@pytest.mark.parametrize("chapitre", ["XIX", "XX", "XXI"])
def test_chapitres_excluent_les_sources_externes(policy, chapitre: str) -> None:  # type: ignore[no-untyped-def]
    admises = policy.familles_admises(chapitre, [])
    assert not (admises & policy.familles_externes)
    assert "INDEX" in admises, "l'Index reste : son filtrage relève de R3, pas de R1"


def test_bloc_t36_t50_resolu_avant_le_chapitre(policy) -> None:  # type: ignore[no-untyped-def]
    """T39.1 vit sous XIX ET sous T36-T50 : c'est le bloc qui décide."""
    assert "T36-T50" in policy.blocs
    admises = policy.familles_admises("XIX", ["T36-T50"])
    assert "CEPIDC" not in admises


def test_resolution_du_plus_interne_au_plus_large(policy) -> None:  # type: ignore[no-untyped-def]
    """C50.8 a trois blocs englobants ; le plus interne doit primer."""
    blocs = ["C00-C97", "C00-C75", "C50-C50"]
    # Aucun n'est déclaré : on retombe sur le chapitre, puis le défaut.
    assert policy.regle_pour("II", blocs) == policy.defaut


def test_remplacement_et_non_fusion(tmp_path: Path) -> None:
    """**Le verrou central.** Un bloc qui ne redéclare pas un champ ne
    l'hérite PAS du chapitre : il retombe sur le défaut du schéma.

    Ici le chapitre interdit tout ; le bloc ne redéclare que
    `sources_externes`. Si la résolution fusionnait, `generation_llm`
    resterait à False. En remplacement, il revient à True.
    """
    yaml_test = tmp_path / "p.yaml"
    yaml_test.write_text(
        "familles: [LLM, CEPIDC]\n"
        "familles_formulations: [LLM, CEPIDC]\n"
        "familles_externes: [CEPIDC, LLM]\n"
        "familles_llm: [LLM]\n"
        "defaut: {sources_externes: true, generation_llm: true}\n"
        "chapitres:\n"
        "  XIX: {sources_externes: false, generation_llm: false}\n"
        "blocs:\n"
        "  T36-T50: {sources_externes: false}\n",
        encoding="utf-8",
    )
    pol = load_policy(yaml_test)
    chapitre = pol.regle_pour("XIX", [])
    bloc = pol.regle_pour("XIX", ["T36-T50"])

    assert chapitre.generation_llm is False
    assert bloc.sources_externes is False, "le champ redéclaré s'applique"
    assert bloc.generation_llm is True, (
        "REMPLACEMENT, PAS FUSION : le bloc n'hérite pas de `generation_llm` "
        "du chapitre. Si cette assertion casse, la résolution a été changée en "
        "fusion — relire le pitfall du CLAUDE.md avant de « corriger » le test."
    )


def test_yaml_incoherent_rejete(tmp_path: Path) -> None:
    """Une famille citée sans être déclarée doit lever, pas passer."""
    yaml_test = tmp_path / "p.yaml"
    yaml_test.write_text(
        "familles: [INDEX]\nfamilles_formulations: [INDEX, FANTOME]\n", encoding="utf-8"
    )
    with pytest.raises(PolicyError, match="FANTOME"):
        load_policy(yaml_test)


# ----------------------------------------------------------------------
# 2. Couverture bidirectionnelle YAML ↔ mapping des sources
# ----------------------------------------------------------------------


def test_tout_libelle_du_mapping_est_range_dans_une_famille(policy) -> None:  # type: ignore[no-untyped-def]
    """Sens 1 : aucune source du CSV ne reste sans famille.

    Une source ajoutée à `_SOURCE_CSV_MAP` sans être rangée dans le YAML
    tomberait silencieusement en `AUTRE` et disparaîtrait des fiches.
    """
    orphelins = sorted(
        lib for lib in _SOURCE_CSV_MAP.values() if policy.famille_de(lib) == FAMILLE_INCONNUE
    )
    assert not orphelins, (
        f"Libellés du mapping sans famille : {orphelins}. Les ranger dans "
        f"`familles_sources` ou `prefixes_familles` de {DEFAULT_POLICY_PATH}."
    )


def test_toute_famille_citee_est_declaree(policy) -> None:  # type: ignore[no-untyped-def]
    """Sens 2 : les listes du YAML ne citent que des familles connues."""
    citees = (
        set(policy.familles_sources.values())
        | set(policy.prefixes_familles.values())
        | set(policy.familles_formulations)
        | set(policy.familles_externes)
        | set(policy.familles_llm)
    )
    assert citees <= policy.familles, (
        f"Familles citées mais non déclarées : {sorted(citees - policy.familles)}"
    )


def test_famille_llm_declaree_sans_libelle(policy) -> None:  # type: ignore[no-untyped-def]
    """LLM est déclarée mais n'a pas encore de source : c'est voulu.

    Le point d'application du flag doit exister **avant** l'intégration
    des synonymes Mistral, sinon la garantie arriverait après le besoin.
    """
    assert "LLM" in policy.familles
    assert "LLM" not in set(policy.familles_sources.values())


def test_prefixe_aphp_capture_les_specialites(policy) -> None:  # type: ignore[no-untyped-def]
    captures = [lib for lib in _SOURCE_CSV_MAP.values() if policy.famille_de(lib) == "APHP"]
    assert len(captures) >= 9, f"9 feuilles AP-HP attendues, {len(captures)} capturées"


# ----------------------------------------------------------------------
# 3. Dérivation de la hiérarchie
# ----------------------------------------------------------------------


def test_blocs_non_positionnels() -> None:
    """Les blocs se lisent par forme, pas par position dans le `path`."""
    merged = pl.DataFrame(
        {
            "code": ["C50.8", "T39.1", "R51"],
            "path": [
                "II/C00-C97/C00-C75/C50-C50/C50/C50.8",
                "XIX/T36-T50/T39/T39.1",
                "XVIII/R50-R69/R51",
            ],
        }
    )
    out = chapitre_et_blocs(merged)
    lignes = {r["code"]: r for r in out.iter_rows(named=True)}

    assert list(lignes["C50.8"]["blocs"]) == ["C00-C97", "C00-C75", "C50-C50"]
    assert list(lignes["T39.1"]["blocs"]) == ["T36-T50"]
    assert lignes["C50.8"]["chapitre"] == "II"
    assert lignes["C50.8"]["categorie"] == "C50", "la catégorie vient du code, pas du path"
    assert lignes["R51"]["categorie"] == "R51"


# ----------------------------------------------------------------------
# Profils de bibliothèque (chantier couverture ATIH, D4)
# ----------------------------------------------------------------------


def test_les_deux_profils_sont_declares(policy) -> None:  # type: ignore[no-untyped-def]
    assert policy.profil("generation").codables_seulement
    assert not policy.profil("controle").codables_seulement


def test_profil_inconnu_leve(policy) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(PolicyError, match="inconnu"):
        policy.profil("verification")


def test_sans_section_profils_les_implicites_sappliquent(tmp_path: Path) -> None:
    """Une politique antérieure à D4 garde le défaut : génération = codables."""
    yaml_test = tmp_path / "p.yaml"
    yaml_test.write_text("familles: [OFS]\n", encoding="utf-8")
    pol = load_policy(yaml_test)
    assert pol.profil("generation").codes == "codables_mco"
    assert pol.profil("controle").codes == "tous"


def test_selection_de_codes_inconnue_rejetee(tmp_path: Path) -> None:
    yaml_test = tmp_path / "p.yaml"
    yaml_test.write_text(
        "familles: [OFS]\nprofils:\n  generation: {codes: codables}\n", encoding="utf-8"
    )
    with pytest.raises(PolicyError, match="codes"):
        load_policy(yaml_test)


def test_le_profil_par_defaut_doit_exister(tmp_path: Path) -> None:
    yaml_test = tmp_path / "p.yaml"
    yaml_test.write_text("familles: [OFS]\nprofils:\n  controle: {codes: tous}\n", encoding="utf-8")
    with pytest.raises(PolicyError, match="generation"):
        load_policy(yaml_test)
