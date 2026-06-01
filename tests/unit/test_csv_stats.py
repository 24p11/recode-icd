"""Tests de `reports.csv_stats` — statistiques déterministes du CSV final."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.reports import csv_stats

pytestmark = pytest.mark.unit


def _make_csv(rows: list[dict[str, object]]) -> pl.DataFrame:
    """Mini-CSV final aux 9 colonnes attendues (refonte 2026-05-30)."""
    schema = {
        "code": pl.String,
        "libelle": pl.String,
        "type": pl.String,
        "source": pl.String,
        "texte": pl.String,
        "source_level": pl.String,
        "inherited_from_code": pl.String,
        "is_dagger_in_pair": pl.Boolean,
        "is_asterisk_in_pair": pl.Boolean,
    }
    base = {
        "libelle": "lib",
        "texte": "t",
        "inherited_from_code": None,
        "is_dagger_in_pair": False,
        "is_asterisk_in_pair": False,
    }
    return pl.DataFrame([{**base, **r} for r in rows], schema=schema)


def _sample() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    # A00.0 : 2 notes (1 synonyme CIM-10 code, 1 exclusion ANS block)
    rows.append({"code": "A00.0", "type": "synonyme", "source": "CIM-10",
                 "source_level": "code"})
    rows.append({"code": "A00.0", "type": "exclusion", "source": "ANS",
                 "source_level": "block", "inherited_from_code": "A00-A09"})
    # A00.1 : 1 inclusion ORPHANET code
    rows.append({"code": "A00.1", "type": "inclusion", "source": "ORPHANET",
                 "source_level": "code"})
    return _make_csv(rows)


def test_compute_stats_basic() -> None:
    stats = csv_stats.compute_csv_stats(_sample())
    assert stats["n_total"] == 3
    assert stats["n_codes"] == 2
    assert stats["mean_notes"] == pytest.approx(1.5)
    # distribution par type couvre les 3 types présents
    types = {r["type"]: r["n"] for r in stats["by_type"]}
    assert types == {"synonyme": 1, "exclusion": 1, "inclusion": 1}
    # distribution par source
    sources = {r["source"]: r["n"] for r in stats["by_source"]}
    assert sources == {"CIM-10": 1, "ANS": 1, "ORPHANET": 1}
    # distribution par source_level
    levels = {r["source_level"]: r["n"] for r in stats["by_level"]}
    assert levels == {"code": 2, "block": 1}


def test_quantiles_present() -> None:
    stats = csv_stats.compute_csv_stats(_sample())
    q = stats["quantiles"]
    assert set(q) == {"min", "p25", "median", "p75", "p90", "p95", "p99", "max"}
    assert q["min"] == 1  # A00.1 a 1 note
    assert q["max"] == 2  # A00.0 a 2 notes


def test_render_markdown_has_all_sections() -> None:
    stats = csv_stats.compute_csv_stats(_sample())
    md = csv_stats.render_markdown(stats, generated_at="2026-05-28")
    for section in (
        "# Statistiques du CSV maître",
        "Généré le** : 2026-05-28",
        "## Distribution par source",
        "## Distribution par type",
        "## Croisé source × type",
        "## Distribution par source_level",
        "## Quantiles du nombre de notes par code",
        "## Codes dépassant 100 notes",
    ):
        assert section in md, f"section manquante : {section}"


def test_render_is_deterministic_except_date() -> None:
    """Même données + même date → markdown byte-identique."""
    df = _sample()
    a = csv_stats.render_markdown(csv_stats.compute_csv_stats(df), "2026-01-01")
    b = csv_stats.render_markdown(csv_stats.compute_csv_stats(df), "2026-01-01")
    assert a == b


def test_codes_over_100_listed() -> None:
    """Un code avec >100 notes figure dans la section dédiée."""
    rows = [
        {"code": "FAT.0", "type": "synonyme", "source": "CIM-10 index",
         "source_level": "code", "libelle": "Code fourre-tout"}
        for _ in range(101)
    ]
    rows.append({"code": "THIN.0", "type": "synonyme", "source": "CIM-10",
                 "source_level": "code"})
    stats = csv_stats.compute_csv_stats(_make_csv(rows))
    fat = {r["code"] for r in stats["fat_codes"]}
    assert "FAT.0" in fat
    assert "THIN.0" not in fat
    md = csv_stats.render_markdown(stats, "2026-05-28")
    assert "FAT.0" in md
    assert "Code fourre-tout" in md


def test_generate_writes_file(tmp_path: Path) -> None:
    csv_path = tmp_path / "in.csv"
    _sample().write_csv(csv_path)
    out = tmp_path / "csv_stats.md"
    result = csv_stats.generate_csv_stats(csv_path, out, generated_at="2026-05-28")
    assert result == out
    assert out.is_file()
    content = out.read_text(encoding="utf-8")
    assert "# Statistiques du CSV maître" in content
    assert "## Quantiles" in content
