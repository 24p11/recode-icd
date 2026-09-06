"""Loader du kit ATIH (`loaders/atih.py`) sur un kit synthétique.

Cas exercés : format (ISO-8859-1, CR LF, 6 champs, bourrage), écriture
du maître via la table de notation (famille inversée, `+` ponctué ou
non), statut et règles positionnelles dérivées du type, décodage du
marqueur de suppression, schéma, métadonnées Parquet, rapport.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pyarrow.parquet as pq
import pytest

from recode_icd.loaders.atih import (
    LIBELLES_STATUT,
    STATUTS_MCO,
    build_atih_codes,
    load_atih_kit,
    resume_kit,
    statut_mco,
    to_parquet,
)
from recode_icd.loaders.schemas import AtihCodesSchema
from recode_icd.notations import charge_notations

pytestmark = pytest.mark.unit

_KIT = (
    "A00   |3|NNN|3|CHOLERA|Chol\xe9ra\r\n"
    "A000  |0|ONO|0|CHOLERA A VIBRIO|Chol\xe9ra \xe0 Vibrio cholerae 01\r\n"
    "B24+0 |0|OOO|0|PRE-SIDA|Pr\xe9-SIDA (A.R.C.) sans pr\xe9cision\r\n"
    "T08+1 |1|NNO|1|FRACT. RACHIS OUV.|Fracture du rachis, niveau non pr\xe9cis\xe9, ouverte\r\n"
    "C169+0|0|OOO|0|TM ESTOMAC CDH1|Tumeur maligne de l'estomac, familiale li\xe9e au g\xe8ne CDH 1\r\n"
    "O0490 |0|OOO|0|IVG SANS COMPLIC.|Interruption m\xe9dicale volontaire de grossesse, complet, sans complication\r\n"
    "M62810|0|OOO|0|RHABDOMYOLYSE SCAP.|Rhabdomyolyse - R\xe9gion scapulaire\r\n"
    "W00   |3|NNN|3|CHUTE GLACE|Chute de plain-pied due \xe0 la glace et la neige\r\n"
    + "".join(
        f"W00{i}  |2|NNO|1|CHUTE GLACE LIEU {i}|Chute de plain-pied due \xe0 la glace et la neige, {lieu}\r\n"
        for i, lieu in enumerate(
            (
                "domicile",
                "\xe9tablissement collectif",
                "\xe9cole et lieu public",
                "lieu de sport",
                "rue ou route",
                "zone de commerce",
                "local industriel et chantier",
                "exploitation agricole",
                "autres lieux pr\xe9cis\xe9s",
                "lieu sans pr\xe9cision",
            )
        )
    )
    + "".join(
        f"W000{a} |2|NNO|1|CHUTE GLACE DOM. {a}|Chute de plain-pied due \xe0 la glace et la neige, domicile, {lib}\r\n"
        for a, lib in (
            ("0", "en pratiquant un sport"),
            ("1", "en participant \xe0 un jeu et \xe0 des activit\xe9s de loisirs"),
            ("2", "en exer\xe7ant un travail \xe0 des fins lucratives"),
            ("3", "en exer\xe7ant d'autres formes de travail"),
            (
                "4",
                "en se reposant, en dormant, en mangeant ou en participant \xe0 d'autres activit\xe9s essentielles",
            ),
            ("8", "en participant \xe0 d'autres activit\xe9s pr\xe9cis\xe9es"),
            ("9", "en participant \xe0 une activit\xe9 non pr\xe9cis\xe9e"),
        )
    )
    + "M0720 |3|NNN|3|SPONDYLITE PSO. SM|*** SU09 *** Spondylite psoriasique (L40.5) - Si\xe8ges multiples\r\n"
    "Z514  |4|NOO|1|SOINS PREPAR.|Soins pr\xe9paratoires \xe0 un traitement ult\xe9rieur\r\n"
)


@pytest.fixture
def kit_path(tmp_path: Path) -> Path:
    chemin = tmp_path / "LIBCIM10MULTI.TXT"
    chemin.write_bytes(_KIT.encode("iso-8859-1"))
    return chemin


@pytest.fixture(scope="module")
def notations():  # type: ignore[no-untyped-def]
    return charge_notations()


def test_load_atih_kit_lit_le_format(kit_path: Path) -> None:
    df = load_atih_kit(kit_path)
    assert df.columns == [
        "code",
        "type_mco",
        "profil_smr",
        "type_psy",
        "libelle_court",
        "libelle_long",
    ]
    assert df["code"].to_list()[:3] == ["A00", "A000", "B24+0"]
    assert df.height == len(_KIT.splitlines())
    assert df.filter(pl.col("code").str.starts_with("W00"))["type_mco"].to_list() == [3] + [2] * 17
    assert df["libelle_long"][0] == "Choléra"


def test_load_atih_kit_refuse_un_enregistrement_mal_forme(tmp_path: Path) -> None:
    chemin = tmp_path / "LIBCIM10MULTI.TXT"
    chemin.write_bytes(b"A00   |3|NNN|3|CHOLERA|Chol|era\r\n")
    with pytest.raises(ValueError, match="6 champs"):
        load_atih_kit(chemin)


def test_build_atih_codes_ecrit_le_maitre_et_derive_le_statut(kit_path: Path, notations) -> None:  # type: ignore[no-untyped-def]
    codes = build_atih_codes(load_atih_kit(kit_path), notations)
    AtihCodesSchema.validate(codes)
    par = {r["code_atih"]: r for r in codes.iter_rows(named=True)}

    # Écriture du maître : table de notation, pas de règle en dur.
    assert par["A000"]["code"] == "A00.0"
    assert par["B24+0"]["code"] == "B24.+0"
    assert par["T08+1"]["code"] == "T08+1"
    assert par["C169+0"]["code"] == "C16.9+0"
    assert par["O0490"]["code"] == "O04.-0.9"
    assert par["M62810"]["code"] == "M62.8-01"
    assert par["W0004"]["code"] == "W00.04"

    # Statut et règles positionnelles dérivées du type.
    assert par["A000"]["statut_mco"] == "codable" and par["A000"]["codable_mco"]
    assert not par["A000"]["interdit_dp"] and not par["A000"]["interdit_dr"]
    assert par["T08+1"]["statut_mco"] == "interdit_dp_dr"
    assert (
        par["T08+1"]["interdit_dp"]
        and par["T08+1"]["interdit_dr"]
        and not par["T08+1"]["interdit_das"]
    )
    assert par["W0004"]["statut_mco"] == "cause_externe" and par["W0004"]["codable_mco"]
    assert par["Z514"]["statut_mco"] == "interdit_dp"
    assert par["Z514"]["interdit_dp"] and not par["Z514"]["interdit_dr"]
    assert par["A00"]["statut_mco"] == "pere_interdit" and not par["A00"]["codable_mco"]
    assert par["A00"]["interdit_das"]

    # Code supprimé : marqueur décodé, libellé restitué sans le marqueur.
    assert par["M0720"]["supprime"] and par["M0720"]["supprime_millesime"] == "09"
    assert par["M0720"]["statut_mco"] == "supprime" and not par["M0720"]["codable_mco"]
    assert par["M0720"]["libelle_long"].startswith("Spondylite psoriasique")
    assert not par["A000"]["supprime"] and par["A000"]["supprime_millesime"] is None

    # Profil SMR décomposé.
    assert (par["A000"]["smr_mmp"], par["A000"]["smr_ae"], par["A000"]["smr_das"]) == (
        True,
        False,
        True,
    )
    assert par["A000"]["millesime"] == "2025"


def test_statut_mco_couvre_les_cinq_types() -> None:
    assert [statut_mco(t, False) for t in (0, 1, 2, 4, 3)] == list(STATUTS_MCO[:5])
    assert statut_mco(3, True) == "supprime"
    assert statut_mco(0, True) == "supprime", "un code supprimé l'est quel que soit son type"
    assert set(LIBELLES_STATUT) >= set(STATUTS_MCO)
    with pytest.raises(ValueError, match="0-4"):
        statut_mco(7, False)


def test_to_parquet_ecrit_metadonnees_et_rapport(kit_path: Path, tmp_path: Path) -> None:
    paths = to_parquet(kit_path, tmp_path / "processed", tmp_path / "reports", millesime="2025")
    table = pq.read_table(paths["atih_codes"])
    metadata = {k.decode(): v.decode() for k, v in (table.schema.metadata or {}).items()}
    assert metadata["atih_kit_version"] == "2025"
    assert metadata["terminology"] == "cim10_atih"
    assert metadata["source_file"] == "LIBCIM10MULTI.TXT"
    rapport = pl.read_csv(paths["summary"])
    n_codes = len(_KIT.splitlines())
    n_codables = sum(1 for ligne in _KIT.splitlines() if ligne.split("|")[1] != "3")
    assert rapport.filter(pl.col("valeur") == "codes")["count"][0] == n_codes
    assert rapport.filter(pl.col("valeur") == "codables_mco")["count"][0] == n_codables
    assert paths["chapitre_xx_troncs"].is_file() and paths["chapitre_xx_composition"].is_file()
    troncs = pl.read_parquet(paths["chapitre_xx_troncs"])
    assert troncs.select("tronc", "classe").rows() == [("W00", "tronc_composition")]
    assert rapport.filter(pl.col("dimension") == "supprime_millesime")["valeur"].to_list() == ["09"]


def test_resume_kit_est_deterministe(kit_path: Path, notations) -> None:  # type: ignore[no-untyped-def]
    codes = build_atih_codes(load_atih_kit(kit_path), notations)
    assert resume_kit(codes).equals(resume_kit(codes.reverse().sort("code_atih")))
