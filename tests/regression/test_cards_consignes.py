"""Section « Consignes de codage » des fiches — régression sur données réelles.

Les six témoins du prototype (`scripts/explore/rendu_recommandations_fiches.py`)
plus deux témoins des raffinements (dédup sujet/exemple, bloc cité des
exemples), sur le contenu de la section extraite de `build_card`.

Verrouille aussi les deux décisions d'intégration : fiches
constructibles sans les tables du guide (section omise + avertissement
au rapport de build), et indépendance vis-à-vis de la chapter_policy
(R1/R2/R3 gouvernent les Formulations, pas les consignes).
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import polars as pl
import pytest
import yaml

from recode_icd import cards
from recode_icd.cards import (
    DEFAULT_SEED,
    build_card,
    build_cards_library,
    charge_politique,
    rng_pour_code,
)
from recode_icd.policy import DEFAULT_POLICY_PATH
from recode_icd.utils.loaders_dev import ExplorationContext, load_exploration_context

_RACINE_REPORTS = Path(__file__).resolve().parents[2] / "reports"

pytestmark = pytest.mark.regression


@pytest.fixture(scope="module")
def ctx() -> ExplorationContext:
    c = load_exploration_context(with_external=True)
    if c.flat is None or c.merged is None or c.ans is None or c.ofs_codes is None:
        pytest.skip("Artefacts pipeline absents.")
    if c.recommendations is None or c.recommendation_codes is None:
        pytest.skip("Tables du guide MCO absentes — lancer `recode-icd build guide-mco`.")
    return c


@pytest.fixture(scope="module")
def outils(ctx: ExplorationContext):  # type: ignore[no-untyped-def]
    return charge_politique(cards._eager(ctx.merged))


@pytest.fixture(scope="module")
def ctx_sans_guide(ctx: ExplorationContext) -> ExplorationContext:
    """Le même contexte, amputé des deux tables du guide MCO."""
    return dataclasses.replace(ctx, recommendations=None, recommendation_codes=None)


def _fiche(code: str, ctx: ExplorationContext, outils) -> str:  # type: ignore[no-untyped-def]
    return build_card(code, ctx, rng_pour_code(DEFAULT_SEED, code), outils)


def _section_consignes(card: str) -> str:
    """Extrait la section Consignes du markdown (chaîne vide si absente)."""
    m = re.search(
        r"^## Consignes de codage \(guide méthodologique [^)]+\)$"
        r".*?(?=^## |^</fiche_code>|\Z)",
        card,
        re.MULTILINE | re.DOTALL,
    )
    return m.group(0).rstrip() if m else ""


def _liste_principale(section: str) -> str:
    """La partie de la section avant le bloc exemples et les règles générales."""
    coupe = re.split(r"^> À titre d'exemple|^### Règles générales", section, flags=re.MULTILINE)
    return coupe[0]


# ----------------------------------------------------------------------
# Les six témoins du prototype
# ----------------------------------------------------------------------


def test_i64_le_filtre_contexte(ctx: ExplorationContext, outils) -> None:  # type: ignore[no-untyped-def]
    """AVC-03 et AVC-08 ne citent I60-I64 qu'en `contexte` : elles ne
    doivent pas apparaître sur la fiche de I64 (piège n°3 du modèle)."""
    section = _section_consignes(_fiche("I64", ctx, outils))
    assert "[GM2026-V-AVC-02]" in section
    assert "GM2026-V-AVC-03" not in section, "contexte rendu — piège n°3 violé"
    assert "GM2026-V-AVC-08" not in section, "contexte rendu — piège n°3 violé"


def test_z86_70_tri_et_regles_generales(ctx: ExplorationContext, outils) -> None:  # type: ignore[no-untyped-def]
    """Les trois étages : consignes au code, puis à la plage, puis les
    règles générales du chapitre XXI en fin de section — chacune avec sa
    situation entre parenthèses."""
    section = _section_consignes(_fiche("Z86.70", ctx, outils))
    positions = [
        section.find("[GM2026-V-AVC-05]"),
        section.find("[GM2026-V-AVC-11]"),
        section.find("[GM2026-V-XXI-49]"),
        section.find("### Règles générales du chapitre XXI"),
        section.find("[GM2026-V-XXI-01]"),
    ]
    assert all(p >= 0 for p in positions), f"éléments manquants dans :\n{section}"
    assert positions == sorted(positions), "tri par spécificité ou regroupement violé"
    assert "[GM2026-V-XXI-01] (Emploi général des codes du chapitre XXI)" in section


def test_d62_article_historique(ctx: ExplorationContext, outils) -> None:  # type: ignore[no-untyped-def]
    """D62 (chapitre III) : les trois consignes de son article, pas de
    sous-section Règles générales — ANT-01, qui atteignait tout le
    chapitre au lot 1, est `rendu_fiche=non` depuis l'arbitrage n° 10."""
    section = _section_consignes(_fiche("D62", ctx, outils))
    rendus = set(re.findall(r"\[(\S+)\]", section))
    assert rendus == {"GM2026-V-D62-01", "GM2026-V-D62-02", "GM2026-V-D62-03"}
    assert "### Règles générales" not in section


def test_z51_5_au_carrefour_de_deux_articles(ctx: ExplorationContext, outils) -> None:  # type: ignore[no-untyped-def]
    """Z51.5 est régi par l'article AVC ET par l'article du chapitre
    XXI : les consignes des deux articles se côtoient dans la fiche."""
    section = _section_consignes(_fiche("Z51.5", ctx, outils))
    rendus = set(re.findall(r"\[(\S+)\]", section))
    assert rendus == {
        "GM2026-V-AVC-06",
        "GM2026-V-XXI-38",
        "GM2026-V-XXI-39",
        "GM2026-V-XXI-40",
        "GM2026-V-XXI-01",
    }


def test_e43_les_definitions_de_seuils(ctx: ExplorationContext, outils) -> None:  # type: ignore[no-untyped-def]
    """E43 reçoit les consignes de l'article dénutrition, dont les
    `definition` à seuils chiffrés qui bornent ce que le générateur a le
    droit d'écrire."""
    section = _section_consignes(_fiche("E43", ctx, outils))
    rendus = set(re.findall(r"\[(\S+)\]", section))
    # ANT-01 (chapitre IV au lot 1) est `rendu_fiche=non` — arbitrage n° 10.
    assert rendus == {f"GM2026-V-DEN-{n:02d}" for n in (1, 2, 3, 4, 6, 7, 8, 11, 13, 15, 16, 17)}


def test_z23_0_liste_principale_vide_regles_generales_seules(
    ctx: ExplorationContext,
    outils,  # type: ignore[no-untyped-def]
) -> None:
    """Z23.0 n'est cité par aucune consigne : sa fiche ne porte QUE les
    règles générales du chapitre XXI (complétude + maîtrise du bruit,
    question ouverte n°1 de la note de conception). La situation rendue
    entre parenthèses borne la portée de la règle — c'est elle qui
    transforme une règle apparemment hors sujet en information de
    non-application."""
    section = _section_consignes(_fiche("Z23.0", ctx, outils))
    assert section, "complétude violée — les consignes de chapitre ne descendent pas"
    rendus = set(re.findall(r"\[(\S+)\]", section))
    assert rendus == {"GM2026-V-XXI-01"}, (
        "maîtrise du bruit violée — soit une consigne non chapitre atteint un code "
        "non cité, soit une association `ensemble` a été résolue"
    )
    assert "- [" not in _liste_principale(section), "la liste principale doit être vide"
    assert "### Règles générales du chapitre XXI" in section
    assert "(Emploi général des codes du chapitre XXI)" in section


# ----------------------------------------------------------------------
# Les deux témoins des raffinements
# ----------------------------------------------------------------------


def test_z20_1_dedup_sujet_prime_sur_exemple(ctx: ExplorationContext, outils) -> None:  # type: ignore[no-untyped-def]
    """GM2026-V-XXI-16 atteint Z20.1 en `exemple` (au code) ET en `sujet`
    (via Z20) : la consigne norme le code, elle se rend une seule fois,
    dans la liste principale — jamais dans le bloc cité."""
    section = _section_consignes(_fiche("Z20.1", ctx, outils))
    assert section.count("[GM2026-V-XXI-16]") == 1
    assert "[GM2026-V-XXI-16]" in _liste_principale(section)
    assert "À titre d'exemple" not in section


def test_f01_000_exemple_seul_en_bloc_cite(ctx: ExplorationContext, outils) -> None:  # type: ignore[no-untyped-def]
    """F01.000 n'est cité qu'en illustration (DP d'exemple de AVC-13) :
    sa section se réduit au bloc cité — signal structurel « ceci
    illustre, ceci ne norme pas ». ANT-01 (chapitre V au lot 1) est
    `rendu_fiche=non` — arbitrage n° 10."""
    section = _section_consignes(_fiche("F01.000", ctx, outils))
    assert "> À titre d'exemple dans le guide :" in section
    assert "> - [GM2026-V-AVC-13]" in section
    assert "- [" not in _liste_principale(section), "aucune consigne sujet attendue"
    assert "### Règles générales" not in section
    assert "GM2026-V-ANT-01" not in section


# ----------------------------------------------------------------------
# Décisions d'intégration
# ----------------------------------------------------------------------


def test_fiche_sans_consigne_strictement_inchangee(
    ctx: ExplorationContext,
    ctx_sans_guide: ExplorationContext,
    outils,  # type: ignore[no-untyped-def]
) -> None:
    """W65 (chapitre XX) n'est visé par aucune consigne : sa fiche est
    byte-identique avec et sans les tables du guide — le chantier ne
    touche pas les fiches hors périmètre.

    Témoin changé au lot 1 du chantier B : R51 (chapitre XVIII) a gagné
    la règle générale ANT-01, qui descend sur tous les chapitres I à
    XIX. Le témoin doit vivre hors de ces chapitres — W65 (noyade dans
    une baignoire) n'est dans le périmètre d'aucun article de la file."""
    rec_codes = cards._eager(ctx.recommendation_codes)
    assert rec_codes.filter(pl.col("code") == "W65").is_empty(), (
        "prérequis invalidé : W65 est désormais cité par le guide, choisir un autre témoin"
    )
    avec = _fiche("W65", ctx, outils)
    sans = _fiche("W65", ctx_sans_guide, outils)
    assert avec == sans
    assert "Consignes de codage" not in avec


def test_parquets_absents_section_omise_et_avertissement(
    ctx_sans_guide: ExplorationContext,
    tmp_path: Path,
) -> None:
    """Sans les tables du guide, les fiches restent constructibles :
    section omise partout, avertissement porté par le rapport de build."""
    summary = build_cards_library(
        ctx=ctx_sans_guide, output_dir=tmp_path / "lib", limit=3, progress=False
    )
    assert summary.n_written == 3
    assert summary.n_consignes == 0
    assert summary.avertissements, "l'absence du guide doit être signalée au rapport"
    assert "guide MCO" in summary.avertissements[0]


def test_parquets_presents_rapport_compte_par_chapitre(
    ctx: ExplorationContext,
    tmp_path: Path,
) -> None:
    """Chapitre III : un seul code cité rendu (D62) — ANT-01, qui
    couvrait tout le chapitre au lot 1, est `rendu_fiche=non`
    (arbitrage n° 10). Le rapport de build compte les fiches gagnant la
    section, par chapitre, sans avertissement."""
    summary = build_cards_library(
        ctx=ctx, output_dir=tmp_path / "lib", chapter_filter="III", progress=False
    )
    assert summary.avertissements == ()
    assert summary.n_consignes == 1
    assert summary.consignes_par_chapitre == (("III", 1),)
    index = pl.read_csv(summary.index_path)
    assert index.filter(pl.col("code") == "D62")["has_consignes"].to_list() == [True]
    assert index.filter(pl.col("has_consignes"))["code"].to_list() == ["D62"]


def test_section_hors_chapter_policy(
    ctx: ExplorationContext,
    outils,  # type: ignore[no-untyped-def]
    tmp_path: Path,
) -> None:
    """R1/R2/R3 gouvernent les Formulations, pas les consignes : une
    politique restrictive change la fiche de E43 (prérequis — un test
    qui n'exerce rien ne prouve rien) mais sa section Consignes reste
    byte-identique."""
    data = yaml.safe_load(DEFAULT_POLICY_PATH.read_text(encoding="utf-8"))
    data["defaut"] = {"sources_externes": False, "generation_llm": False}
    data["chapitres"] = {}
    data["blocs"] = {}
    yaml_restrictif = tmp_path / "policy_restrictive.yaml"
    yaml_restrictif.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    outils_restrictifs = charge_politique(cards._eager(ctx.merged), policy_path=yaml_restrictif)

    fiche_defaut = _fiche("E43", ctx, outils)
    fiche_restrictive = _fiche("E43", ctx, outils_restrictifs)
    assert fiche_defaut != fiche_restrictive, (
        "prérequis invalidé : la politique restrictive ne change pas la fiche de E43, "
        "le test n'exerce plus l'indépendance"
    )
    assert _section_consignes(fiche_defaut) == _section_consignes(fiche_restrictive)
    assert _section_consignes(fiche_defaut)


def test_determinisme_double_rendu(ctx: ExplorationContext, outils) -> None:  # type: ignore[no-untyped-def]
    """Double build → byte-equal, sur les huit témoins."""
    temoins = ("I64", "Z86.70", "D62", "Z51.5", "E43", "Z23.0", "Z20.1", "F01.000")
    for code in temoins:
        assert _fiche(code, ctx, outils) == _fiche(code, ctx, outils), code


# ----------------------------------------------------------------------
# rendu_fiche (arbitrage n° 10) — sur données réelles
# ----------------------------------------------------------------------


def test_ant01_non_rendue_r51_sans_section(ctx: ExplorationContext, outils) -> None:  # type: ignore[no-untyped-def]
    """R51 n'est visé que par ANT-01 (règle du chapitre XVIII), basculée
    `rendu_fiche=non` : sa fiche reste SANS section Consignes après
    rebuild — le bruit de génération que l'arbitrage n° 10 retire.

    Témoin demandé « hors codes cités » : J18.9 ne convient pas, il est
    cité par COMP-02 (pneumonie postopératoire, exemple) — couvert par
    `test_j18_9_garde_son_exemple_sans_ant01`. R51 est l'ancien témoin
    sans-consigne, redevenu représentatif par la bascule.
    """
    rec_codes = cards._eager(ctx.recommendation_codes)
    vises = rec_codes.filter(pl.col("code") == "R51")["rec_id"].unique().to_list()
    assert vises == ["GM2026-V-ANT-01"], (
        f"prérequis invalidé : R51 est visé par {vises}, choisir un autre témoin"
    )
    fiche = _fiche("R51", ctx, outils)
    assert "Consignes de codage" not in fiche


def test_j18_9_garde_son_exemple_sans_ant01(ctx: ExplorationContext, outils) -> None:  # type: ignore[no-untyped-def]
    """J18.9 (chapitre X) est cité en exemple par COMP-02 : sa section
    garde le bloc cité, mais perd la règle générale ANT-01 non rendue."""
    section = _section_consignes(_fiche("J18.9", ctx, outils))
    assert "> - [GM2026-V-COMP-02]" in section
    assert "GM2026-V-ANT-01" not in section
    assert "### Règles générales" not in section


def test_rapport_de_build_liste_les_consignes_non_rendues() -> None:
    """La bascule `rendu_fiche=non` n'est jamais silencieuse : le
    rapport de build committé la liste, avec sa justification."""
    rapport = pl.read_csv(_RACINE_REPORTS / "guide_mco_consignes_non_rendues.csv")
    assert rapport["rec_id"].to_list() == ["GM2026-V-ANT-01"]
    assert "2026-09-03" in rapport["justification"][0]


def test_expression_non_resolue_au_rapport_jamais_silencieuse() -> None:
    """Invariant de l'arbitrage n° 9 (plage à borne absente, cas
    OMS-01/U00-U49) : l'expression reste déclarée dans la table curée
    ET apparaît au rapport de build committé — jamais avalée."""
    rapport = pl.read_csv(_RACINE_REPORTS / "guide_mco_expressions_non_resolues.csv")
    lignes = rapport.filter(
        (pl.col("rec_id") == "GM2026-V-OMS-01") & (pl.col("code_expr") == "U00-U49")
    )
    assert lignes.height == 1, "OMS-01/U00-U49 doit être au rapport des non-résolues"
    assert "U00" in lignes["erreur"][0]
