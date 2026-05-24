from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.loaders.schemas import EnrichedDaggerAsteriskSchema
from recode_icd.relations import dagger_asterisk

pytestmark = pytest.mark.unit


def _master(rows: list[dict[str, object]]) -> pl.DataFrame:
    """Mini MASTER avec seulement les colonnes consommées."""
    return pl.DataFrame(
        [{"SID": r["SID"], "code": r["code"], "valid": r.get("valid", 1)} for r in rows],
        schema={"SID": pl.Int64, "code": pl.String, "valid": pl.Int64},
    )


def _libelle(rows: list[dict[str, object]]) -> pl.DataFrame:
    """Mini LIBELLE — colonnes : LID, SID, source, valid, libelle."""
    return pl.DataFrame(
        [
            {
                "LID": r["LID"],
                "SID": r["SID"],
                "source": r["source"],
                "valid": r.get("valid", 1),
                "libelle": r["libelle"],
            }
            for r in rows
        ],
        schema={
            "LID": pl.Int64,
            "SID": pl.Int64,
            "source": pl.String,
            "valid": pl.Int64,
            "libelle": pl.String,
        },
    )


def _dagstar(rows: list[dict[str, object]]) -> pl.DataFrame:
    """Mini DAGSTAR — colonnes : SID, LID, assoc, daget, plus."""
    return pl.DataFrame(
        [
            {
                "SID": r["SID"],
                "LID": r["LID"],
                "assoc": r["assoc"],
                "daget": r["daget"],
                "plus": r.get("plus", 0),
            }
            for r in rows
        ],
        schema={
            "SID": pl.Int64,
            "LID": pl.Int64,
            "assoc": pl.Int64,
            "daget": pl.String,
            "plus": pl.Int64,
        },
    )


def test_paire_simple_daget_U() -> None:
    """Une seule ligne DAGSTAR daget='U' : SID=dague, assoc=astérisque."""
    master = _master(
        [
            {"SID": 100, "code": "A18.1"},
            {"SID": 6250, "code": "N33.0"},
        ]
    )
    libelle = _libelle(
        [
            {"LID": 1, "SID": 100, "source": "S", "libelle": "Tuberculose génito-urinaire"},
            {"LID": 2, "SID": 6250, "source": "S", "libelle": "Cystite tuberculeuse"},
            {"LID": 99, "SID": 100, "source": "D", "libelle": "tuberculose (de) vessie"},
        ]
    )
    dagstar = _dagstar([{"SID": 100, "LID": 99, "assoc": 6250, "daget": "U"}])

    out = dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)

    assert len(out) == 1
    row = out.row(0, named=True)
    assert row["dagger_code"] == "A18.1"
    assert row["asterisk_code"] == "N33.0"
    assert row["dagger_label"] == "Tuberculose génito-urinaire"
    assert row["asterisk_label"] == "Cystite tuberculeuse"
    assert list(row["levels_present"]) == ["U"]
    assert list(row["source_lids"]) == [99]
    assert list(row["combination_labels"]) == ["tuberculose (de) vessie"]
    assert row["redundancy_level"] == "independent"


def test_paire_symetrique_U_et_G_fusionnees() -> None:
    """Même paire vue daget='U' (côté dague) + daget='G' (côté astérisque)
    → 1 seule ligne, levels_present cumulé, source_lids cumulés."""
    master = _master(
        [
            {"SID": 100, "code": "A18.1"},
            {"SID": 6250, "code": "N33.0"},
        ]
    )
    libelle = _libelle(
        [
            {"LID": 1, "SID": 100, "source": "S", "libelle": "Tuberculose génito-urinaire"},
            {"LID": 2, "SID": 6250, "source": "S", "libelle": "Cystite tuberculeuse"},
            {"LID": 99, "SID": 100, "source": "D", "libelle": "tuberculose (de) vessie"},
        ]
    )
    dagstar = _dagstar(
        [
            {"SID": 100, "LID": 99, "assoc": 6250, "daget": "U"},
            # Vu depuis l'astérisque : SID=N33.0, assoc=A18.1, daget=G
            # avec LID pointant le libellé systématique de N33.0.
            {"SID": 6250, "LID": 2, "assoc": 100, "daget": "G"},
        ]
    )

    out = dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)

    assert len(out) == 1
    row = out.row(0, named=True)
    assert row["dagger_code"] == "A18.1"
    assert row["asterisk_code"] == "N33.0"
    assert sorted(row["levels_present"]) == ["G", "U"]
    assert sorted(row["source_lids"]) == [2, 99]
    # Deux libellés distincts post-dédup tolérante.
    assert set(row["combination_labels"]) == {
        "tuberculose (de) vessie",
        "Cystite tuberculeuse",
    }


def test_non_pointe_daget_S_assoc_zero() -> None:
    """daget='S' avec assoc=0 → paire incomplète, asterisk_code=None,
    redundancy_level='none'."""
    master = _master([{"SID": 100, "code": "A18.1"}])
    libelle = _libelle(
        [
            {"LID": 1, "SID": 100, "source": "S", "libelle": "Tuberculose génito-urinaire"},
        ]
    )
    dagstar = _dagstar([{"SID": 100, "LID": 1, "assoc": 0, "daget": "S"}])

    out = dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)

    assert len(out) == 1
    row = out.row(0, named=True)
    assert row["dagger_code"] == "A18.1"
    assert row["asterisk_code"] is None
    assert row["asterisk_label"] is None
    assert list(row["levels_present"]) == ["S"]
    assert row["redundancy_level"] == "none"


def test_non_pointe_daget_F_assoc_zero() -> None:
    """daget='F' avec assoc=0 → côté dague NULL."""
    master = _master([{"SID": 6250, "code": "N33.0"}])
    libelle = _libelle(
        [{"LID": 2, "SID": 6250, "source": "S", "libelle": "Cystite tuberculeuse"}]
    )
    dagstar = _dagstar([{"SID": 6250, "LID": 2, "assoc": 0, "daget": "F"}])

    out = dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)

    assert len(out) == 1
    row = out.row(0, named=True)
    assert row["dagger_code"] is None
    assert row["asterisk_code"] == "N33.0"
    assert row["redundancy_level"] == "none"


def test_combination_labels_dedup_tolerante() -> None:
    """Deux LID variants typographiques (ligature, casse, ponctuation)
    → 1 seule entrée dans combination_labels."""
    master = _master(
        [
            {"SID": 100, "code": "A18.1"},
            {"SID": 6250, "code": "N33.0"},
        ]
    )
    libelle = _libelle(
        [
            {"LID": 1, "SID": 100, "source": "S", "libelle": "Tuberculose génito-urinaire"},
            {"LID": 2, "SID": 6250, "source": "S", "libelle": "Cystite tuberculeuse"},
            {"LID": 99, "SID": 100, "source": "D", "libelle": "Cystite tuberculeuse"},
            {"LID": 100, "SID": 100, "source": "D", "libelle": "cystite tuberculeuse."},
        ]
    )
    dagstar = _dagstar(
        [
            {"SID": 100, "LID": 99, "assoc": 6250, "daget": "U"},
            {"SID": 100, "LID": 100, "assoc": 6250, "daget": "U"},
        ]
    )

    out = dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)

    row = out.row(0, named=True)
    # Les deux libellés tombent dans le même bucket de normalisation :
    # on ne garde que la première occurrence (par LID croissant).
    assert list(row["combination_labels"]) == ["Cystite tuberculeuse"]
    assert sorted(row["source_lids"]) == [99, 100]


def test_paires_multiples_independantes_recoivent_ids_distincts() -> None:
    """Deux paires différentes → deux lignes avec association_id distincts,
    tri stable par (dagger_code, asterisk_code)."""
    master = _master(
        [
            {"SID": 100, "code": "A18.1"},
            {"SID": 200, "code": "E10.2"},
            {"SID": 6250, "code": "N33.0"},
            {"SID": 7000, "code": "N08.3"},
        ]
    )
    libelle = _libelle(
        [
            {"LID": 1, "SID": 100, "source": "S", "libelle": "Tuberculose génito-urinaire"},
            {"LID": 2, "SID": 200, "source": "S", "libelle": "Diabète type 1 rénal"},
            {"LID": 3, "SID": 6250, "source": "S", "libelle": "Cystite tuberculeuse"},
            {"LID": 4, "SID": 7000, "source": "S", "libelle": "Glomérulopathie diabétique"},
        ]
    )
    dagstar = _dagstar(
        [
            {"SID": 100, "LID": 1, "assoc": 6250, "daget": "T"},
            {"SID": 200, "LID": 2, "assoc": 7000, "daget": "T"},
        ]
    )

    out = dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)

    assert len(out) == 2
    # Tri attendu : A18.1/N33.0 avant E10.2/N08.3.
    assert out["dagger_code"].to_list() == ["A18.1", "E10.2"]
    assert out["asterisk_code"].to_list() == ["N33.0", "N08.3"]
    assert out["association_id"].to_list() == [0, 1]
    assert all(r["redundancy_level"] == "independent" for r in out.iter_rows(named=True))


def test_schema_validates() -> None:
    master = _master(
        [{"SID": 100, "code": "A18.1"}, {"SID": 6250, "code": "N33.0"}]
    )
    libelle = _libelle(
        [
            {"LID": 1, "SID": 100, "source": "S", "libelle": "x"},
            {"LID": 2, "SID": 6250, "source": "S", "libelle": "y"},
        ]
    )
    dagstar = _dagstar([{"SID": 100, "LID": 1, "assoc": 6250, "daget": "T"}])

    out = dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)
    EnrichedDaggerAsteriskSchema.validate(out)


def test_deterministe() -> None:
    """Deux appels successifs → résultat byte-equivalent."""
    master = _master(
        [
            {"SID": 100, "code": "A18.1"},
            {"SID": 200, "code": "E10.2"},
            {"SID": 6250, "code": "N33.0"},
            {"SID": 7000, "code": "N08.3"},
        ]
    )
    libelle = _libelle(
        [
            {"LID": 1, "SID": 100, "source": "S", "libelle": "x"},
            {"LID": 2, "SID": 200, "source": "S", "libelle": "y"},
            {"LID": 3, "SID": 6250, "source": "S", "libelle": "z"},
            {"LID": 4, "SID": 7000, "source": "S", "libelle": "w"},
            {"LID": 99, "SID": 100, "source": "D", "libelle": "alt"},
        ]
    )
    dagstar = _dagstar(
        [
            {"SID": 100, "LID": 99, "assoc": 6250, "daget": "U"},
            {"SID": 200, "LID": 2, "assoc": 7000, "daget": "T"},
            {"SID": 6250, "LID": 3, "assoc": 100, "daget": "G"},
        ]
    )

    first = dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)
    second = dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)
    assert first.equals(second)


def test_libelle_invalid_ignore() -> None:
    """Les lignes LIBELLE valid=0 sont ignorées pour combination_labels."""
    master = _master(
        [{"SID": 100, "code": "A18.1"}, {"SID": 6250, "code": "N33.0"}]
    )
    libelle = _libelle(
        [
            {"LID": 1, "SID": 100, "source": "S", "libelle": "Tub."},
            {"LID": 2, "SID": 6250, "source": "S", "libelle": "Cys."},
            {"LID": 99, "SID": 100, "source": "D", "valid": 0, "libelle": "doit_etre_ignore"},
        ]
    )
    dagstar = _dagstar([{"SID": 100, "LID": 99, "assoc": 6250, "daget": "U"}])

    out = dagger_asterisk.build_dagger_asterisk_table(master, dagstar, libelle)

    row = out.row(0, named=True)
    # LID 99 est invalide → pas de libellé récupéré → combination_labels vide.
    assert list(row["combination_labels"]) == []
    assert list(row["source_lids"]) == [99]


def test_to_parquet_and_csv_and_report_writes_three_files(tmp_path: Path) -> None:
    """Vérifie l'écriture des trois artefacts via le wrapper fichier."""
    # On reconstruit un mini-dossier OFS avec les trois fichiers nécessaires.
    src_fixture = (
        Path(__file__).resolve().parents[1] / "fixtures" / "ofs_sample"
    )
    processed = tmp_path / "processed"
    report = tmp_path / "reports" / "dagger_asterisk_summary.csv"

    parquet_path, csv_path, report_path = (
        dagger_asterisk.to_parquet_and_csv_and_report(
            src_fixture, processed, report
        )
    )

    assert parquet_path.exists()
    assert csv_path.exists()
    assert report_path.exists()

    table = pl.read_parquet(parquet_path)
    EnrichedDaggerAsteriskSchema.validate(table)
    # Au moins une ligne (le DAGSTAR fixture en contient une).
    assert len(table) >= 1
