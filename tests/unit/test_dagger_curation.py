from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path
from types import ModuleType

import polars as pl
import pytest
import yaml

pytestmark = pytest.mark.unit


@pytest.fixture
def mod() -> ModuleType:
    """Charge le script `2026-05-20_dagger_curation.py` comme module
    (nom commençant par un chiffre → import classique impossible)."""
    script_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "explore"
        / "2026-05-20_dagger_curation.py"
    )
    spec = importlib.util.spec_from_file_location("dagger_curation", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Enregistrer dans sys.modules AVANT exec — sinon @dataclass tente
    # de résoudre les annotations via sys.modules[__module__].__dict__
    # et lève AttributeError sur Python 3.14.
    sys.modules["dagger_curation"] = module
    spec.loader.exec_module(module)
    return module


def _mini_table() -> pl.DataFrame:
    """4 paires : 2 chap A (A17.8, A18.1), 1 chap E, 1 incomplète (dagger NULL)."""
    return pl.DataFrame(
        {
            "association_id": [0, 1, 2, 3],
            "dagger_code": ["A17.8", "A18.1", "E10.2", None],
            "dagger_label": [
                "Tuberculose système nerveux",
                "Tuberculose génito-urinaire",
                "Diabète type 1 rénal",
                None,
            ],
            "asterisk_code": ["G05.0", "N33.0", "N08.3", "M50.0"],
            "asterisk_label": [
                "Encéphalite tuberculeuse",
                "Cystite tuberculeuse",
                "Glomérulopathie diabétique",
                "Manif. M50.0",
            ],
            "combination_labels": [
                ["encéphalite tuberculeuse"],
                ["tuberculose vessie", "Cystite tuberculeuse"],
                ["glomérulopathie diabétique"],
                ["manif"],
            ],
            "levels_present": [["G"], ["G", "U"], ["T"], ["F"]],
            "redundancy_level": [
                "independent",
                "independent",
                "independent",
                "none",
            ],
            "source_lids": [[1], [2, 3], [4], [5]],
        }
    )


def _write_table(tmp_path: Path) -> Path:
    table_path = tmp_path / "table.parquet"
    _mini_table().write_parquet(table_path)
    return table_path


# --------------------------------------------------------------------------- #
# Mode 1 — inspection
# --------------------------------------------------------------------------- #
def test_inspection_mode_with_prefix(
    mod: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--prefix A17` ne doit garder que la paire A17.8/G05.0."""
    table_path = _write_table(tmp_path)
    yaml_path = tmp_path / "curated.yaml"  # absent → vide
    rc = mod.main(
        [
            "--prefix",
            "A17",
            "--table-path",
            str(table_path),
            "--yaml-path",
            str(yaml_path),
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "A17.8" in out
    assert "G05.0" in out
    # Les autres paires doivent être absentes.
    assert "A18.1" not in out
    assert "E10.2" not in out
    assert "[non curé]" in out
    assert "1 paire(s) affichée(s)" in out


# --------------------------------------------------------------------------- #
# Mode 2 — génération du workbook
# --------------------------------------------------------------------------- #
def test_generate_workbook_creates_correct_structure(
    mod: ModuleType, tmp_path: Path
) -> None:
    table_path = _write_table(tmp_path)
    workbook_path = tmp_path / "wb.yaml"
    yaml_path = tmp_path / "curated.yaml"
    rc = mod.main(
        [
            "--generate-workbook",
            "--prefix",
            "A",
            "--workbook-path",
            str(workbook_path),
            "--table-path",
            str(table_path),
            "--yaml-path",
            str(yaml_path),
            "--curator",
            "Test",
        ]
    )
    assert rc == 0
    assert workbook_path.is_file()
    pairs = mod.read_workbook(workbook_path)
    assert len(pairs) == 2
    assert pairs[0]["dagger"] == "A17.8"
    assert pairs[0]["asterisk"] == "G05.0"
    assert pairs[0]["redundancy_level"] == ""
    assert pairs[0]["curated_by"] == "Test"
    assert pairs[0]["curated_date"] == date.today().isoformat()
    # Les commentaires d'aide sont présents dans le texte brut.
    raw = workbook_path.read_text(encoding="utf-8")
    assert "# dagger_label:" in raw
    assert "# combination_labels:" in raw
    assert "# levels_present:" in raw


def test_generate_workbook_refuses_to_overwrite(
    mod: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    table_path = _write_table(tmp_path)
    workbook_path = tmp_path / "wb.yaml"
    workbook_path.write_text("contenu_existant", encoding="utf-8")
    yaml_path = tmp_path / "curated.yaml"
    rc = mod.main(
        [
            "--generate-workbook",
            "--workbook-path",
            str(workbook_path),
            "--table-path",
            str(table_path),
            "--yaml-path",
            str(yaml_path),
        ]
    )
    assert rc == 1
    assert workbook_path.read_text(encoding="utf-8") == "contenu_existant"
    err = capsys.readouterr().err
    assert "existe déjà" in err


def test_generate_workbook_filters_already_curated(
    mod: ModuleType, tmp_path: Path
) -> None:
    """`--uncurated-only` doit exclure les paires déjà dans le YAML cible."""
    table_path = _write_table(tmp_path)
    yaml_path = tmp_path / "curated.yaml"
    yaml_path.write_text(
        "subordinate_pairs:\n"
        "  - dagger: A17.8\n"
        "    asterisk: G05.0\n"
        "    rationale: x\n"
        "independent_pairs: []\n",
        encoding="utf-8",
    )
    workbook_path = tmp_path / "wb.yaml"
    rc = mod.main(
        [
            "--generate-workbook",
            "--prefix",
            "A",
            "--uncurated-only",
            "--workbook-path",
            str(workbook_path),
            "--table-path",
            str(table_path),
            "--yaml-path",
            str(yaml_path),
        ]
    )
    assert rc == 0
    pairs = mod.read_workbook(workbook_path)
    assert len(pairs) == 1
    assert pairs[0]["dagger"] == "A18.1"


# --------------------------------------------------------------------------- #
# Mode 3 — merge
# --------------------------------------------------------------------------- #
def test_merge_workbook_appends_new_pairs(
    mod: ModuleType, tmp_path: Path
) -> None:
    yaml_path = tmp_path / "curated.yaml"  # absent → créé
    workbook_path = tmp_path / "wb.yaml"
    workbook_path.write_text(
        "pairs:\n"
        "  - dagger: A17.8\n"
        "    asterisk: G05.0\n"
        "    redundancy_level: subordinate\n"
        "    rationale: tuberculose système nerveux\n"
        "    curated_by: Test\n"
        '    curated_date: "2026-05-20"\n'
        "  - dagger: E10.2\n"
        "    asterisk: N08.3\n"
        "    redundancy_level: independent\n"
        "    rationale: deux réalités distinctes\n"
        "    curated_by: Test\n"
        '    curated_date: "2026-05-20"\n',
        encoding="utf-8",
    )
    rc = mod.main(
        [
            "--merge-workbook",
            "--workbook-path",
            str(workbook_path),
            "--yaml-path",
            str(yaml_path),
        ]
    )
    assert rc == 0
    final = mod.load_curated_yaml(yaml_path)
    assert len(final["subordinate_pairs"]) == 1
    assert final["subordinate_pairs"][0]["dagger"] == "A17.8"
    assert final["subordinate_pairs"][0]["rationale"] == "tuberculose système nerveux"
    assert len(final["independent_pairs"]) == 1
    assert final["independent_pairs"][0]["dagger"] == "E10.2"


def test_merge_workbook_detects_conflict(
    mod: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A17.8/G05.0 déjà 'subordinate' dans le YAML, workbook propose
    'independent' → conflit, YAML non modifié."""
    yaml_path = tmp_path / "curated.yaml"
    yaml_path.write_text(
        "subordinate_pairs:\n"
        "  - dagger: A17.8\n"
        "    asterisk: G05.0\n"
        "    rationale: original\n"
        "independent_pairs: []\n",
        encoding="utf-8",
    )
    original_text = yaml_path.read_text(encoding="utf-8")
    workbook_path = tmp_path / "wb.yaml"
    workbook_path.write_text(
        "pairs:\n"
        "  - dagger: A17.8\n"
        "    asterisk: G05.0\n"
        "    redundancy_level: independent\n",
        encoding="utf-8",
    )
    rc = mod.main(
        [
            "--merge-workbook",
            "--workbook-path",
            str(workbook_path),
            "--yaml-path",
            str(yaml_path),
        ]
    )
    assert rc == 1
    err = capsys.readouterr().err
    assert "Conflits" in err
    assert "A17.8" in err
    # YAML cible byte-equivalent à l'original.
    assert yaml_path.read_text(encoding="utf-8") == original_text


def test_merge_workbook_ignores_empty_and_undecided(mod: ModuleType) -> None:
    pairs = [
        {"dagger": "A17.8", "asterisk": "G05.0", "redundancy_level": ""},
        {"dagger": "A18.1", "asterisk": "N33.0", "redundancy_level": "undecided"},
    ]
    new_curated, report = mod.merge_into_curated(
        pairs,
        {"subordinate_pairs": [], "independent_pairs": []},
    )
    assert len(report.ignored) == 2
    assert len(new_curated["subordinate_pairs"]) == 0
    assert len(new_curated["independent_pairs"]) == 0


def test_merge_workbook_idempotent_on_same_value(mod: ModuleType) -> None:
    """Re-merger une paire déjà au même niveau → no-op (pas de duplication
    de l'entrée existante, rationale du YAML préservé)."""
    curated = {
        "subordinate_pairs": [
            {
                "dagger": "A17.8",
                "asterisk": "G05.0",
                "rationale": "original",
            }
        ],
        "independent_pairs": [],
    }
    pairs = [
        {
            "dagger": "A17.8",
            "asterisk": "G05.0",
            "redundancy_level": "subordinate",
            "rationale": "tentative-de-réécriture",
        }
    ]
    new_curated, report = mod.merge_into_curated(pairs, curated)
    assert len(report.identical) == 1
    assert len(report.added_subordinate) == 0
    assert len(new_curated["subordinate_pairs"]) == 1
    # L'entrée originale est préservée telle quelle (pas de réécriture du rationale).
    assert new_curated["subordinate_pairs"][0]["rationale"] == "original"


def test_merge_workbook_validates_redundancy_level(mod: ModuleType) -> None:
    with pytest.raises(ValueError, match="redundancy_level"):
        mod.merge_into_curated(
            [{"dagger": "A", "asterisk": "B", "redundancy_level": "garbage"}],
            {"subordinate_pairs": [], "independent_pairs": []},
        )


# --------------------------------------------------------------------------- #
# Sanity helpers
# --------------------------------------------------------------------------- #
def test_save_curated_yaml_is_human_readable(
    mod: ModuleType, tmp_path: Path
) -> None:
    """save_curated_yaml produit un YAML trié + commenté + round-trippable."""
    yaml_path = tmp_path / "out.yaml"
    data = {
        "subordinate_pairs": [
            {"dagger": "B", "asterisk": "Z", "rationale": "b"},
            {"dagger": "A", "asterisk": "Z", "rationale": "a"},
        ],
        "independent_pairs": [],
    }
    mod.save_curated_yaml(yaml_path, data)
    text = yaml_path.read_text(encoding="utf-8")
    # En-tête commenté présent.
    assert text.startswith("# Couples dague/astérisque")
    # Tri appliqué : A avant B.
    assert text.index("dagger: A") < text.index("dagger: B")
    # Round-trip.
    parsed = yaml.safe_load(text)
    assert len(parsed["subordinate_pairs"]) == 2
    assert parsed["independent_pairs"] == []
