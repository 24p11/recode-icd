"""Test minimal du helper d'exploration.

Vérifie que `load_exploration_context()` charge sans erreur les sources
principales présentes dans le repo. Marker `unit` mais I/O réelle (les
fichiers sont petits sauf LIBELLE ~11 MB / quelques centaines de ms).
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.utils.loaders_dev import (
    ExplorationContext,
    load_exploration_context,
)

pytestmark = pytest.mark.unit


def test_context_loads_main_sources() -> None:
    ctx = load_exploration_context()
    assert isinstance(ctx, ExplorationContext)

    # Tables OFS principales doivent être présentes.
    required_ofs = {"master", "libelle", "include", "exclude", "dagstar", "memo"}
    missing = required_ofs - set(ctx.ofs.keys())
    assert not missing, f"Tables OFS manquantes : {missing}"

    # ANS Parquet doit être chargé.
    assert ctx.ans is not None, "ctx.ans est None — owl_codes.parquet manquant ?"
    assert isinstance(ctx.ans, pl.DataFrame)

    # Artefacts pipeline présents.
    assert ctx.merged is not None
    assert ctx.propagated is not None
    assert ctx.flat is not None

    # Tables du guide MCO présentes (versées au chantier A).
    assert ctx.recommendations is not None
    assert ctx.recommendation_codes is not None
    assert isinstance(ctx.recommendation_codes, pl.DataFrame)
    assert "specificite" in ctx.recommendation_codes.columns

    # Au moins un rapport présent (note_merges produit après chaque build merged).
    assert "note_merges" in ctx.reports


def test_context_lazy_returns_lazyframes() -> None:
    ctx = load_exploration_context(lazy=True)
    assert isinstance(ctx.ofs["master"], pl.LazyFrame)
    assert isinstance(ctx.ans, pl.LazyFrame)
    assert isinstance(ctx.merged, pl.LazyFrame)


def test_context_graceful_on_missing_paths(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Quand tous les chemins overrides pointent vers du vide, on a un ctx vide sans exception."""
    ctx = load_exploration_context(
        root=tmp_path,
        ofs_dir=tmp_path / "nope_ofs",
        processed_dir=tmp_path / "nope_processed",
        reports_dir=tmp_path / "nope_reports",
    )
    assert ctx.ofs == {}
    assert ctx.ans is None
    assert ctx.merged is None
    assert ctx.propagated is None
    assert ctx.flat is None
    assert ctx.reports == {}


# ----------------------------------------------------------------------
# Kit de nomenclature ATIH (chantier couverture ATIH)
# ----------------------------------------------------------------------


def test_load_atih_libcim10_lit_le_format_du_kit(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """ISO-8859-1, CR LF, 6 champs `|`, code sur 6 caractères bourré d'espaces.

    Cas exercés : accent latin-1 décodé, bourrage retiré, `+` conservé en
    4e position, types convertis en entiers.
    """
    from recode_icd.utils.loaders_dev import load_atih_libcim10

    contenu = (
        "A00   |3|NNN|3|CHOLERA|Chol\xe9ra\r\n"
        "A000  |0|OOO|0|CHOLERA A VIBRIO|Chol\xe9ra \xe0 Vibrio cholerae 01\r\n"
        "B24+0 |0|OOO|0|PRE-SIDA|Pr\xe9-SIDA (A.R.C.) sans pr\xe9cision\r\n"
    )
    chemin = tmp_path / "LIBCIM10MULTI.TXT"
    chemin.write_bytes(contenu.encode("iso-8859-1"))

    df = load_atih_libcim10(chemin)
    assert df.columns == [
        "code",
        "type_mco",
        "profil_smr",
        "type_psy",
        "libelle_court",
        "libelle_long",
    ]
    assert df["code"].to_list() == ["A00", "A000", "B24+0"]
    assert df["type_mco"].to_list() == [3, 0, 0]
    assert df["profil_smr"].to_list() == ["NNN", "OOO", "OOO"]
    assert df["libelle_long"][0] == "Choléra"
    assert df["libelle_long"][2] == "Pré-SIDA (A.R.C.) sans précision"


def test_load_atih_libcim10_refuse_un_enregistrement_mal_forme(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Un `|` dans un libellé casserait le découpage : le chargeur le dit."""
    from recode_icd.utils.loaders_dev import load_atih_libcim10

    chemin = tmp_path / "LIBCIM10MULTI.TXT"
    chemin.write_bytes(b"A00   |3|NNN|3|CHOLERA|Chol|era\r\n")
    with pytest.raises(ValueError, match="6 champs"):
        load_atih_libcim10(chemin)


def test_le_kit_atih_2025_charge_entierement() -> None:
    """Le fichier réel : 42 897 enregistrements, cinq valeurs de type MCO."""
    from recode_icd.utils.loaders_dev import _ATIH_LIBCIM10_REL, load_atih_libcim10

    chemin = Path(__file__).resolve().parents[2] / _ATIH_LIBCIM10_REL
    if not chemin.is_file():
        pytest.skip(f"{chemin} absent.")
    df = load_atih_libcim10(chemin)
    assert df.height == 42_897
    assert set(df["type_mco"].unique().to_list()) == {0, 1, 2, 3, 4}
    assert df["code"].n_unique() == df.height, "un code ATIH par enregistrement"
