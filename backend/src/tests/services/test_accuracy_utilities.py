"""
Unit tests for text normalisation and Word Error Rate calculation utilities.

Tests cover:
- ``normalize_text``: exact matches, whitespace handling, curly-quote
  standardisation, and combined formatting issues.
- ``calculate_wer``: exact matches, minor typos, word-order errors,
  formatting-only differences (WER = 0 after normalisation), and
  mixed insertions / deletions / substitutions.
"""

from __future__ import annotations

import pytest

from services.accuracy_calc import calculate_wer
from services.text_utils import normalize_text


# ===========================================================================
# normalize_text
# ===========================================================================


class TestNormalizeText:
    """Tests for :func:`services.text_utils.normalize_text`."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            # --- exact matches (no changes needed) ---------------------------
            pytest.param(
                "hello world",
                "hello world",
                id="exact_match_simple",
            ),
            pytest.param(
                "the quick brown fox",
                "the quick brown fox",
                id="exact_match_sentence",
            ),
            pytest.param(
                "",
                "",
                id="empty_string",
            ),
            pytest.param(
                "a",
                "a",
                id="single_character",
            ),
            # --- inconsistent whitespace ------------------------------------
            pytest.param(
                "hello\tworld",
                "hello world",
                id="tab_replaced_with_space",
            ),
            pytest.param(
                "hello\nworld",
                "hello world",
                id="newline_replaced_with_space",
            ),
            pytest.param(
                "hello\n\n\nworld",
                "hello world",
                id="multiple_newlines_collapsed",
            ),
            pytest.param(
                "hello    world",
                "hello world",
                id="multiple_spaces_collapsed",
            ),
            pytest.param(
                "hello \t\n world",
                "hello world",
                id="mixed_whitespace_collapsed",
            ),
            # --- leading / trailing whitespace ------------------------------
            pytest.param(
                "  hello world",
                "hello world",
                id="leading_spaces_stripped",
            ),
            pytest.param(
                "hello world  ",
                "hello world",
                id="trailing_spaces_stripped",
            ),
            pytest.param(
                "\n\thello world\n\t",
                "hello world",
                id="leading_trailing_tabs_newlines_stripped",
            ),
            # --- curly quotes -----------------------------------------------
            pytest.param(
                "\u201chello\u201d",
                '"hello"',
                id="curly_double_quotes_to_straight",
            ),
            pytest.param(
                "she said \u201chello\u201d",
                'she said "hello"',
                id="curly_quotes_in_sentence",
            ),
            # --- lowercasing ------------------------------------------------
            pytest.param(
                "HELLO WORLD",
                "hello world",
                id="uppercase_to_lowercase",
            ),
            pytest.param(
                "The Quick Brown Fox",
                "the quick brown fox",
                id="mixed_case_to_lowercase",
            ),
            # --- combined formatting issues ---------------------------------
            pytest.param(
                "  \u201cHELLO\u201d\tWORLD\n",
                '"hello" world',
                id="combined_curly_quotes_whitespace_case",
            ),
            pytest.param(
                "\u201cThe\tQuick\nBrown\u201d   FOX  ",
                '"the quick brown" fox',
                id="combined_all_formatting_issues",
            ),
        ],
    )
    def test_normalize(self, raw: str, expected: str) -> None:
        """Verify that *raw* is normalised to *expected*."""
        assert normalize_text(raw) == expected


# ===========================================================================
# calculate_wer
# ===========================================================================


class TestCalculateWer:
    """Tests for :func:`services.accuracy_calc.calculate_wer`."""

    # ------------------------------------------------------------------
    # Exact matches (WER == 0.0)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("expected", "actual"),
        [
            pytest.param("hello world", "hello world", id="exact_match_short"),
            pytest.param(
                "the quick brown fox jumps over the lazy dog",
                "the quick brown fox jumps over the lazy dog",
                id="exact_match_long_sentence",
            ),
            pytest.param("", "", id="both_empty"),
            pytest.param("word", "word", id="single_word_match"),
        ],
    )
    def test_exact_match(self, expected: str, actual: str) -> None:
        """WER should be 0.0 when reference and hypothesis are identical."""
        assert calculate_wer(expected, actual) == 0.0

    # ------------------------------------------------------------------
    # Minor typos (WER > 0.0)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("expected", "actual", "expected_wer"),
        [
            pytest.param(
                "hello world",
                "hallo world",
                0.5,
                id="single_substitution",
            ),
            pytest.param(
                "the cat sat on the mat",
                "the dog sat on the mat",
                1 / 6,
                id="one_word_substituted_in_sentence",
            ),
            pytest.param(
                "hello world",
                "hello wrld",
                0.5,
                id="typo_in_one_word",
            ),
        ],
    )
    def test_minor_typos(self, expected: str, actual: str, expected_wer: float) -> None:
        """WER should be greater than 0.0 for minor typos."""
        wer: float = calculate_wer(expected, actual)
        assert wer > 0.0
        assert wer == pytest.approx(expected_wer, abs=1e-10)

    # ------------------------------------------------------------------
    # Completely wrong word order (WER > 0.0, potentially higher)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("expected", "actual"),
        [
            pytest.param(
                "hello world",
                "world hello",
                id="two_word_reversal",
            ),
            pytest.param(
                "the quick brown fox",
                "fox brown quick the",
                id="full_reversal_four_words",
            ),
        ],
    )
    def test_wrong_word_order(self, expected: str, actual: str) -> None:
        """WER should be greater than 0.0 when word order is scrambled."""
        wer: float = calculate_wer(expected, actual)
        assert wer > 0.0

    # ------------------------------------------------------------------
    # Pure formatting differences (WER == 0.0 after normalisation)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("expected", "actual"),
        [
            pytest.param(
                "hello world",
                "  HELLO\tWORLD\n",
                id="case_and_whitespace_only",
            ),
            pytest.param(
                'she said "hello"',
                "She Said \u201cHello\u201d",
                id="case_and_curly_quotes_only",
            ),
            pytest.param(
                "the quick brown fox",
                "THE\nQUICK\tBROWN   FOX",
                id="whitespace_variations_only",
            ),
            pytest.param(
                "hello world",
                "HELLO WORLD",
                id="case_difference_only",
            ),
        ],
    )
    def test_formatting_differences_only(self, expected: str, actual: str) -> None:
        """WER should be 0.0 when only formatting differs (after normalisation)."""
        norm_expected: str = normalize_text(expected)
        norm_actual: str = normalize_text(actual)
        assert calculate_wer(norm_expected, norm_actual) == 0.0

    # ------------------------------------------------------------------
    # Insertions, deletions, and substitutions
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("expected", "actual", "expected_wer"),
        [
            pytest.param(
                "the cat sat on the mat",
                "the cat sat on the big mat",
                1 / 6,
                id="insertion_one_word",
            ),
            pytest.param(
                "the cat sat on the mat",
                "the cat sat on mat",
                1 / 6,
                id="deletion_one_word",
            ),
            pytest.param(
                "the cat sat on the mat",
                "the dog sat on the big mat",
                2 / 6,
                id="substitution_and_insertion",
            ),
            pytest.param(
                "the cat sat on the mat",
                "the cat on mat",
                2 / 6,
                id="two_deletions",
            ),
            pytest.param(
                "hello world",
                "goodbye cruel world",
                1.0,
                id="substitution_and_insertion_dominant",
            ),
        ],
    )
    def test_insertions_deletions_substitutions(
        self, expected: str, actual: str, expected_wer: float
    ) -> None:
        """WER should correctly reflect insertions, deletions, and substitutions."""
        wer: float = calculate_wer(expected, actual)
        assert wer == pytest.approx(expected_wer, abs=1e-10)

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_empty_reference(self) -> None:
        """WER returns the number of words in hypothesis when reference is empty."""
        wer: float = calculate_wer("", "hello world")
        assert wer == 2.0

    def test_empty_hypothesis(self) -> None:
        """WER should be 1.0 when hypothesis is empty (all words deleted)."""
        assert calculate_wer("hello world", "") == 1.0

    def test_both_same_after_normalisation(self) -> None:
        """WER should be 0.0 when texts differ only in formatting."""
        expected: str = "The quick brown fox"
        actual: str = "the\tquick\nbrown   FOX  "
        norm_expected: str = normalize_text(expected)
        norm_actual: str = normalize_text(actual)
        assert calculate_wer(norm_expected, norm_actual) == 0.0

    def test_wer_bounds(self) -> None:
        """WER can exceed 1.0 when insertions dominate."""
        wer: float = calculate_wer("hello", "hello world goodbye everyone")
        assert wer > 1.0
