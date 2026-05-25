"""Tests de la fonction `normalize_compact_code` (cf
`docs/source_mapping.md` §"Format des codes dans les sources externes")."""

from __future__ import annotations

import pytest

from recode_icd._normalize import normalize_compact_code

pytestmark = pytest.mark.unit


class TestStandardForms:
    def test_three_char_code_unchanged(self) -> None:
        assert normalize_compact_code("A00") == "A00"

    def test_standard_with_point_unchanged(self) -> None:
        assert normalize_compact_code("A00.0") == "A00.0"

    def test_standard_with_two_digit_suffix_unchanged(self) -> None:
        assert normalize_compact_code("B96.88") == "B96.88"


class TestCompactForms:
    def test_compact_one_digit_suffix(self) -> None:
        assert normalize_compact_code("A000") == "A00.0"

    def test_compact_two_digit_suffix(self) -> None:
        assert normalize_compact_code("B9688") == "B96.88"

    def test_compact_three_digit_suffix(self) -> None:
        assert normalize_compact_code("Z12345") == "Z12.345"

    def test_compact_too_many_digits_returns_none(self) -> None:
        # Pas de code CIM-10 ATIH connu à 4+ chiffres après le préfixe.
        assert normalize_compact_code("Z1234567") is None


class TestOpenIntervals:
    def test_trailing_dash_root_three_chars(self) -> None:
        assert normalize_compact_code("B65-") == "B65"

    def test_trailing_dash_root_with_point(self) -> None:
        # `D22.-` (notation OMS) → on accepte aussi
        assert normalize_compact_code("D22.-") == "D22"


class TestFiltered:
    def test_nocode_returns_none(self) -> None:
        assert normalize_compact_code("nocode") is None

    def test_uppercase_nocode_returns_none(self) -> None:
        assert normalize_compact_code("NOCODE") is None

    def test_empty_string_returns_none(self) -> None:
        assert normalize_compact_code("") is None

    def test_whitespace_returns_none(self) -> None:
        assert normalize_compact_code("   ") is None

    def test_none_input_returns_none(self) -> None:
        assert normalize_compact_code(None) is None

    def test_dagger_notation_returns_none(self) -> None:
        # `I200+0` est une notation dague exotique observée dans GRONES
        assert normalize_compact_code("I200+0") is None

    def test_lowercase_letter_returns_none(self) -> None:
        # Les codes CIM-10 sont en majuscules ; on accepte le strip+upper
        # pour les codes mais on n'invente pas un code invalide.
        assert normalize_compact_code("a000") == "A00.0"

    def test_random_text_returns_none(self) -> None:
        assert normalize_compact_code("voir typhoïde") is None


class TestRobustness:
    def test_strips_surrounding_whitespace(self) -> None:
        assert normalize_compact_code("  A000  ") == "A00.0"
