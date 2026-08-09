"""Tests unitaires pour les fonctions de `recode_icd._normalize`.

Couvre principalement `normalize_ans_brackets` (chantier 4 — normalisation
crochets ANS → parenthèses). Les autres fonctions de `_normalize` (matching
tolérant, codes compacts) ont leurs tests ailleurs (`test_loaders_*`,
`test_normalize_compact_code.py`).
"""

from __future__ import annotations

import pytest

from recode_icd._normalize import normalize_ans_brackets

pytestmark = pytest.mark.unit


class TestNormalizeAnsBracketsStandard:
    def test_simple_code_with_decimal(self) -> None:
        assert normalize_ans_brackets("texte [D48.5] texte") == "texte (D48.5) texte"

    def test_simple_code_no_decimal(self) -> None:
        assert normalize_ans_brackets("[J65]") == "(J65)"

    def test_code_with_trailing_dash_decimal(self) -> None:
        assert normalize_ans_brackets("[B90.-]") == "(B90.-)"

    def test_code_with_only_dot(self) -> None:
        # `\.\d*` autorise un point sans chiffres.
        assert normalize_ans_brackets("[F09.]") == "(F09.)"

    def test_multidigit_decimal(self) -> None:
        assert normalize_ans_brackets("[B96.88]") == "(B96.88)"


class TestNormalizeAnsBracketsRanges:
    def test_range_three_digits(self) -> None:
        assert normalize_ans_brackets("[J67-J70]") == "(J67-J70)"

    def test_range_with_decimal(self) -> None:
        assert normalize_ans_brackets("[V01.0-Y59.9]") == "(V01.0-Y59.9)"

    def test_range_short_form(self) -> None:
        assert normalize_ans_brackets("[P00-P96]") == "(P00-P96)"


class TestNormalizeAnsBracketsMultiOccurrence:
    def test_two_codes_in_same_text(self) -> None:
        assert normalize_ans_brackets("voir [A18.1] et [B20.0]") == "voir (A18.1) et (B20.0)"

    def test_codes_separated_by_newline(self) -> None:
        text = "exclusion [D48.5]\npeau anale [D48.5]\npeau périanale [D48.5]"
        expected = "exclusion (D48.5)\npeau anale (D48.5)\npeau périanale (D48.5)"
        assert normalize_ans_brackets(text) == expected


class TestNormalizeAnsBracketsEdgeCases:
    def test_none_passthrough(self) -> None:
        assert normalize_ans_brackets(None) is None

    def test_empty_string(self) -> None:
        assert normalize_ans_brackets("") == ""

    def test_text_without_match(self) -> None:
        assert normalize_ans_brackets("marge anale") == "marge anale"

    def test_aphp_instruction_untouched(self) -> None:
        """[coder d'abord 1141NL] n'est pas un code CIM-10 → intact."""
        text = "tuberculose génito-urinaire [coder d'abord 1141NL à 1144NL]"
        assert normalize_ans_brackets(text) == text

    def test_latin_synonym_untouched(self) -> None:
        """[mal de Pott] n'est pas un code CIM-10 → intact."""
        text = "tuberculose de colonne vertébrale [mal de Pott]"
        assert normalize_ans_brackets(text) == text

    def test_acronym_untouched(self) -> None:
        """[VIH], [SRAS] sont des sigles, pas des codes → intacts."""
        assert normalize_ans_brackets("virus [VIH]") == "virus [VIH]"
        assert normalize_ans_brackets("[SRAS]") == "[SRAS]"

    def test_en_dash_not_captured(self) -> None:
        """Limitation assumée : `[F55.–]` (U+2013) reste intact."""
        text = "trouble [F55.–]"
        assert normalize_ans_brackets(text) == text

    def test_en_dash_range_not_captured(self) -> None:
        """Limitation assumée : `[T36–T50]` (U+2013) reste intact."""
        text = "intoxications [T36–T50]"
        assert normalize_ans_brackets(text) == text

    def test_multi_interval_not_captured(self) -> None:
        """`[V01-Y59,Y85-Y87,Y89.-]` : virgule non gérée → intact."""
        text = "causes externes [V01-Y59,Y85-Y87,Y89.-]"
        assert normalize_ans_brackets(text) == text

    def test_range_with_french_comment_not_captured(self) -> None:
        """`[F10-F19 avec le quatrième caractère .7]` contient du texte
        libre dans les crochets → la regex stricte ne le touche pas."""
        text = "voir [F10-F19 avec le quatrième caractère .7]"
        assert normalize_ans_brackets(text) == text


class TestNormalizeAnsBracketsIdempotence:
    def test_idempotent_simple(self) -> None:
        text = "voir [D48.5] et [J65]"
        once = normalize_ans_brackets(text)
        twice = normalize_ans_brackets(once)
        assert once == twice == "voir (D48.5) et (J65)"

    def test_idempotent_already_normalized(self) -> None:
        text = "voir (D48.5)"
        assert normalize_ans_brackets(text) == text

    def test_idempotent_none(self) -> None:
        assert normalize_ans_brackets(normalize_ans_brackets(None)) is None
