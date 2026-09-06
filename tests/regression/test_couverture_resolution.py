"""Le résolveur sur les artefacts réels : témoins de chaque classe de la phase 1,
tels qu'ils se résolvent APRÈS le palier 2 (D2, D3, D4).

Deux bibliothèques, deux vérités : dans `generation` (défaut), un code non
codable n'a pas de fiche — le résolveur le dit (`pere_interdit`,
`supprime`, `inconnu_atih`) ; dans `controle`, il en a une, avec
`codable_mco=False`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from recode_icd.couverture import charge_contexte, resoudre_code

pytestmark = pytest.mark.regression

_RACINE = Path(__file__).resolve().parents[2]
_INDEX_CONTROLE = _RACINE / "outputs" / "cards_library_controle" / "_index.csv"


@pytest.fixture(scope="module")
def ctx():  # type: ignore[no-untyped-def]
    if not (_RACINE / "referentials/processed/atih_codes.parquet").is_file():
        pytest.skip("atih_codes.parquet absent (`recode-icd build atih`).")
    return charge_contexte()


@pytest.fixture(scope="module")
def ctx_controle():  # type: ignore[no-untyped-def]
    if not _INDEX_CONTROLE.is_file():
        pytest.skip("Bibliothèque `controle` absente (`recode-icd cards build --profil controle`).")
    return charge_contexte(index_path=_INDEX_CONTROLE)


@pytest.mark.parametrize(
    ("saisie", "statut", "code"),
    [
        ("A181", "fiche", "A18.1"),
        ("A18.1", "fiche", "A18.1"),
        ("O0490", "fiche", "O04.-0.9"),  # famille inversée O04
        ("O04.90", "fiche", "O04.-0.9"),
        ("M62810", "fiche", "M62.8-01"),  # famille inversée M62.8
        ("B24+0", "fiche", "B24.+0"),  # + ponctué
        ("T08+0", "fiche", "T08+0"),  # + non ponctué
        ("U0713", "fiche", "U07.13"),
        ("M000", "fiche", "M00.0"),  # intermédiaire codable : fiche par héritage (D2)
        ("F000", "fiche", "F00.0"),
        ("Z3710", "fiche", "Z37.10"),  # codable sans ligne au CSV : fiche quand même (D3)
        ("U822+0", "fiche", "U82.2+0"),
        ("I7000", "fiche", "I70.00"),  # extension ATIH injectée (D3)
        ("U071", "pere_interdit", "U07.1"),  # type 3 : hors génération (D4)
        ("A00", "pere_interdit", "A00"),
        ("M0720", "supprime", "M07.20"),  # supprimé : hors génération (D4)
        ("N069", "inconnu_atih", "N06.9"),  # inconnu du kit : hors génération (D4)
        ("M1600", "inconnu_atih", "M16.00"),  # localisation chap. XIII inconnue du kit
        ("W0004", "compose", "W00.04"),  # chapitre XX composé (D5)
        ("W260+4", "compose", "W26.0+4"),
        ("X49001", "compose", "X49.001"),
        ("W0005", "composition_invalide", "W00.05"),  # activité 5 hors table
        ("X590", "fiche", "X59.0"),  # sous-code OMS codable de l'hybride X59
        ("X591", "compose", "X59.1"),
        ("Z99.99", "inconnu", "Z99.99"),
        ("O04.123", "inconnu", "O04.123"),
        ("XYZ", "notation_invalide", None),
    ],
)
def test_temoins_generation(ctx, saisie: str, statut: str, code: str | None) -> None:  # type: ignore[no-untyped-def]
    r = resoudre_code(saisie, ctx)
    assert r.statut == statut, r
    if code is not None:
        assert r.code == code
    assert r.raison


def test_une_fiche_de_generation_est_toujours_codable(ctx) -> None:  # type: ignore[no-untyped-def]
    """Invariant dual vu du résolveur : `fiche` ⇒ `codable_mco`."""
    for saisie in ("A181", "M000", "Z3710", "I7000", "O0490", "W000"):
        r = resoudre_code(saisie, ctx)
        if r.statut == "fiche":
            assert r.codable_mco is True, r


def test_le_pere_interdit_rend_ses_subdivisions_avec_fiche(ctx) -> None:  # type: ignore[no-untyped-def]
    r = resoudre_code("U071", ctx)
    assert r.codes_avec_fiche == ("U07.10", "U07.11", "U07.12", "U07.13", "U07.14", "U07.15")
    m00 = resoudre_code("M00", ctx)
    assert m00.statut == "pere_interdit"
    assert {"M00.0", "M00.00"} <= set(m00.codes_avec_fiche), "intermédiaires codables ET feuilles"


def test_un_code_compose_pointe_sur_la_fiche_de_son_tronc(ctx) -> None:  # type: ignore[no-untyped-def]
    """Garde-fou 3 : `W0004` → tronc `W00` (fiche de génération par exception)
    + lieu 0 + activité 4, libellés à l'appui."""
    r = resoudre_code("W0004", ctx)
    assert r.statut == "compose" and r.ancetre == "W00" and r.fiche
    assert r.composition["lieu"] == ("0", "domicile")
    assert r.composition["activite"][0] == "4"  # type: ignore[index]
    tronc = resoudre_code("W00", ctx)
    assert tronc.statut == "fiche" and tronc.codable_mco is False, (
        "le tronc a sa fiche, non codable seul"
    )


def test_dans_la_bibliotheque_controle_les_non_codables_ont_une_fiche(ctx_controle) -> None:  # type: ignore[no-untyped-def]
    for saisie, statut_mco in (
        ("M0720", "supprime"),
        ("N069", "inconnu_atih"),
        ("W00", "pere_interdit"),
    ):
        r = resoudre_code(saisie, ctx_controle)
        assert r.statut == "fiche", r
        assert r.codable_mco is False and r.statut_mco == statut_mco
        assert "pas codable" in r.raison
