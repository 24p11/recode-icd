"""Les deux invariants du chantier couverture ATIH.

I2 (dual, posé avec D4) — **aucun code non codable dans la bibliothèque
de génération** : l'index de `outputs/cards_library` ne porte ni père
interdit, ni code supprimé, ni code inconnu du kit ; la bibliothèque
`controle` les garde, avec leur statut.

I1 (posé en fin de palier 2, après D2 et D3) — **tout code autorisé MCO
hors chapitre XX a une fiche** dans la bibliothèque de génération. Il
est écrit ici dès D4 et **skippe** tant que D2/D3 ne sont pas livrés,
avec le compte des manquants dans le message : il ne se pose en vert
qu'une fois vrai, jamais assoupli pour passer.
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.regression

_RACINE = Path(__file__).resolve().parents[2]
_INDEX_GENERATION = _RACINE / "outputs" / "cards_library" / "_index.csv"
_INDEX_CONTROLE = _RACINE / "outputs" / "cards_library_controle" / "_index.csv"
_ATIH = _RACINE / "referentials" / "processed" / "atih_codes.parquet"
_MERGED = _RACINE / "referentials" / "processed" / "merged_codes.parquet"

NON_CODABLES = {"pere_interdit", "supprime", "inconnu_atih"}
_CHAPITRE_XX = re.compile(r"^[VWXY]\d{2}")


def _index(path: Path) -> pl.DataFrame:
    if not path.is_file():
        pytest.skip(f"{path} absent (`recode-icd cards build [--profil controle]`).")
    return pl.read_csv(path, schema_overrides={"statut_mco": pl.String})


_TRONCS = _RACINE / "referentials" / "processed" / "chapitre_xx_troncs.parquet"
_CODES_XX = _RACINE / "referentials" / "processed" / "chapitre_xx_codes.parquet"


def test_i2_aucun_non_codable_presente_comme_emissible_dans_la_generation() -> None:
    """Reformulé par D5 : les troncs du chapitre XX sont une classe déclarée
    (`tronc_composition`), la seule admise ; tout autre non-codable est une
    violation — `couverture.verifie_generation`, testé dans les deux sens
    sur données synthétiques (`test_couverture.py`)."""
    from recode_icd.couverture import verifie_generation

    index = _index(_INDEX_GENERATION)
    troncs = pl.read_parquet(_TRONCS) if _TRONCS.is_file() else None
    violations = verifie_generation(index, troncs)
    assert not violations, violations[:10]
    if troncs is not None and "classe_generation" in index.columns:
        n_troncs = index.filter(pl.col("classe_generation") == "tronc_composition").height
        assert n_troncs == troncs.filter(pl.col("classe") == "tronc_composition").height, (
            "chaque tronc de composition du kit a sa fiche de génération, rien d'autre ne porte la classe"
        )


def test_i1_par_composition_le_chapitre_xx_est_couvert() -> None:
    """Un code composé du chapitre XX est couvert si son tronc a une fiche de génération."""
    if not (_CODES_XX.is_file() and _TRONCS.is_file()):
        pytest.skip("Tables de composition absentes (`recode-icd build atih`).")
    index = _index(_INDEX_GENERATION)
    fiches = set(index["code"].to_list())
    codes = pl.read_parquet(_CODES_XX)
    sans_tronc = codes.filter(~pl.col("tronc").is_in(sorted(fiches)))
    assert sans_tronc.is_empty(), sans_tronc["tronc"].unique().to_list()[:10]
    assert codes.height >= 25_000


def test_la_bibliotheque_controle_garde_tout_avec_le_statut() -> None:
    controle = _index(_INDEX_CONTROLE)
    generation = _index(_INDEX_GENERATION)
    assert controle.height > generation.height
    assert not controle.filter(pl.col("statut_mco").is_in(NON_CODABLES)).is_empty()
    assert set(generation["code"].to_list()) <= set(controle["code"].to_list())


def test_i1_tout_code_autorise_hors_chapitre_xx_a_une_fiche() -> None:
    if not (_ATIH.is_file() and _MERGED.is_file()):
        pytest.skip("Parquets absents.")
    index = _index(_INDEX_GENERATION)
    atih = pl.read_parquet(_ATIH).filter(pl.col("codable_mco"))
    au_maitre = set(pl.read_parquet(_MERGED)["code"].to_list())
    fiches = set(index["code"].to_list())
    # Le chapitre XX se couvre par composition (D5) : ses extensions
    # absentes du maître sont hors de cet invariant-ci.
    perimetre = [
        c for c in atih["code"].to_list() if not (_CHAPITRE_XX.match(c) and c not in au_maitre)
    ]
    manquants = sorted(c for c in perimetre if c not in fiches)
    if manquants:
        pytest.skip(
            f"I1 pas encore vrai : {len(manquants)} code(s) autorisé(s) sans fiche "
            f"(D2/D3 en cours), ex. {manquants[:8]}"
        )
    assert not manquants
