"""
Multilingual integration tests for TextParser (migrated from backend).

Verifies correct extraction of Hindi (Devanagari), French, Spanish, German,
and mixed English+Hindi text from plain text files.
"""

from pathlib import Path

import pytest

from src.tools.text_parser import TextParser
from conftest import assert_text_accuracy

pytestmark = pytest.mark.slow

# ---------------------------------------------------------------------------
# Constants — asset paths
# ---------------------------------------------------------------------------

ASSETS_DIR = Path(__file__).parent / "assets"
MULTILINGUAL_DIR = ASSETS_DIR / "multilingual"

# Plain-text asset files (single-column layout)
HINDI_TXT = MULTILINGUAL_DIR / "txt/single/hindi_single.txt"
FRENCH_TXT = MULTILINGUAL_DIR / "txt/single/french_single.txt"
SPANISH_TXT = MULTILINGUAL_DIR / "txt/single/spanish_single.txt"
GERMAN_TXT = MULTILINGUAL_DIR / "txt/single/german_single.txt"
MIXED_EN_HI_TXT = MULTILINGUAL_DIR / "txt/single/mixed_en_hi_single.txt"

# Ground-truth text loaded from source .txt files (without layout headers)
HINDI_GROUND_TRUTH = (MULTILINGUAL_DIR / "hindi.txt").read_text(encoding="utf-8")
FRENCH_GROUND_TRUTH = (MULTILINGUAL_DIR / "french.txt").read_text(encoding="utf-8")
SPANISH_GROUND_TRUTH = (MULTILINGUAL_DIR / "spanish.txt").read_text(encoding="utf-8")
GERMAN_GROUND_TRUTH = (MULTILINGUAL_DIR / "german.txt").read_text(encoding="utf-8")
MIXED_EN_HI_GROUND_TRUTH = (MULTILINGUAL_DIR / "mixed_en_hi.txt").read_text(
    encoding="utf-8"
)


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

integration = pytest.mark.integration


def requires_asset(path: Path):
    """Skip test if asset file is missing."""
    return pytest.mark.skipif(
        not path.exists(),
        reason=f"Asset not found: {path} — populate tests/assets/ to run this test",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def parser() -> TextParser:
    """Create a TextParser instance."""
    return TextParser()


def _join_pages(pages: list[str]) -> str:
    """Join extracted pages into a single string."""
    return "\n".join(pages)


# ---------------------------------------------------------------------------
# Hindi (Devanagari) — TextParser
# ---------------------------------------------------------------------------


@integration
class TestTextParserMultilingualHindi:
    """Multi-language text extraction from plain text — Hindi (Devanagari)."""

    @requires_asset(HINDI_TXT)
    @pytest.mark.asyncio
    async def test_hindi_txt_returns_non_empty(self, parser: TextParser):
        """Extracted Hindi text should be non-empty."""
        result = await parser.parse(HINDI_TXT)
        assert isinstance(result, list)
        concatenated = " ".join(result)
        assert len(concatenated) > 0

    @requires_asset(HINDI_TXT)
    @pytest.mark.asyncio
    async def test_hindi_txt_contains_devanagari(self, parser: TextParser):
        """Verify that Devanagari characters appear in extracted text."""
        result = await parser.parse(HINDI_TXT)
        concatenated = " ".join(result)
        assert any(
            0x0900 <= ord(ch) <= 0x097F for ch in concatenated
        ), "No Devanagari characters found in extracted text"

    @requires_asset(HINDI_TXT)
    @pytest.mark.asyncio
    async def test_hindi_txt_contains_key_phrases(self, parser: TextParser):
        """Verify key Hindi legal phrases survive extraction."""
        result = await parser.parse(HINDI_TXT)
        concatenated = " ".join(result)
        key_phrases = [
            "समझौता",  # Agreement
            "पक्षकारों",  # Parties
            "भुगतान",  # Payment
            "गोपनीयता",  # Confidentiality
        ]
        for phrase in key_phrases:
            assert (
                phrase in concatenated
            ), f"Expected Hindi phrase '{phrase}' missing from extracted text"

    @requires_asset(HINDI_TXT)
    @pytest.mark.asyncio
    async def test_hindi_txt_accuracy(self, parser: TextParser):
        """WER should be low for Hindi text extraction.

        The txt/single layout files include a title header (e.g. 'Hindi\\n=====')
        that is not present in the ground-truth source, so a small threshold
        accounts for that difference.
        """
        result = await parser.parse(HINDI_TXT)
        extracted = _join_pages(result)
        # The txt/single files have a short title header prepended; a threshold
        # of 0.05 (5% WER) accounts for this while still verifying high accuracy.
        assert_text_accuracy(HINDI_GROUND_TRUTH, extracted, threshold=0.05)


# ---------------------------------------------------------------------------
# French (accented characters) — TextParser
# ---------------------------------------------------------------------------


@integration
class TestTextParserMultilingualFrench:
    """Multi-language text extraction from plain text — French accented characters."""

    FRENCH_ACCENTED_CHARS = frozenset("éèêëàâùûüôöîïç")

    @requires_asset(FRENCH_TXT)
    @pytest.mark.asyncio
    async def test_french_txt_returns_non_empty(self, parser: TextParser):
        """Extracted French text should be non-empty."""
        result = await parser.parse(FRENCH_TXT)
        assert isinstance(result, list)
        concatenated = " ".join(result)
        assert len(concatenated) > 0

    @requires_asset(FRENCH_TXT)
    @pytest.mark.asyncio
    async def test_french_txt_contains_accented_chars(self, parser: TextParser):
        """Verify that accented French characters are preserved."""
        result = await parser.parse(FRENCH_TXT)
        concatenated = " ".join(result)
        found = {ch for ch in concatenated if ch in self.FRENCH_ACCENTED_CHARS}
        assert len(found) >= 3, (
            f"Expected at least 3 distinct accented characters, "
            f"found {len(found)}: {found}"
        )

    @requires_asset(FRENCH_TXT)
    @pytest.mark.asyncio
    async def test_french_txt_contains_key_phrases(self, parser: TextParser):
        """Verify key French phrases with accents survive extraction."""
        result = await parser.parse(FRENCH_TXT)
        concatenated = " ".join(result)
        # Check phrases that include accented characters
        assert "société" in concatenated, "Expected 'société' (with accent) in output"
        assert "dénommée" in concatenated, "Expected 'dénommée' (with accent) in output"
        assert "siège" in concatenated, "Expected 'siège' (with accent) in output"
        assert (
            "confidentialité" in concatenated
        ), "Expected 'confidentialité' (with accent) in output"

    @requires_asset(FRENCH_TXT)
    @pytest.mark.asyncio
    async def test_french_txt_accuracy(self, parser: TextParser):
        """WER should be low for French text extraction."""
        result = await parser.parse(FRENCH_TXT)
        extracted = _join_pages(result)
        assert_text_accuracy(FRENCH_GROUND_TRUTH, extracted, threshold=0.05)


# ---------------------------------------------------------------------------
# Spanish (special characters) — TextParser
# ---------------------------------------------------------------------------


@integration
class TestTextParserMultilingualSpanish:
    """Multi-language text extraction from plain text — Spanish characters."""

    SPANISH_SPECIAL_CHARS = frozenset("ñÑüÜ¿¡")

    @requires_asset(SPANISH_TXT)
    @pytest.mark.asyncio
    async def test_spanish_txt_returns_non_empty(self, parser: TextParser):
        """Extracted Spanish text should be non-empty."""
        result = await parser.parse(SPANISH_TXT)
        assert isinstance(result, list)
        concatenated = " ".join(result)
        assert len(concatenated) > 0

    @requires_asset(SPANISH_TXT)
    @pytest.mark.asyncio
    async def test_spanish_txt_contains_special_chars(self, parser: TextParser):
        """Verify that Spanish-specific characters are preserved."""
        result = await parser.parse(SPANISH_TXT)
        concatenated = " ".join(result)
        found = {ch for ch in concatenated if ch in self.SPANISH_SPECIAL_CHARS}
        assert len(found) >= 1, (
            f"Expected at least 1 distinct Spanish special character, "
            f"found {len(found)}: {found}"
        )

    @requires_asset(SPANISH_TXT)
    @pytest.mark.asyncio
    async def test_spanish_txt_contains_key_phrases(self, parser: TextParser):
        """Verify key Spanish phrases with special chars survive extraction."""
        result = await parser.parse(SPANISH_TXT)
        concatenated = " ".join(result)
        assert (
            "PRESTACIÓN" in concatenated
        ), "Expected 'PRESTACIÓN' (with accent) in output"
        assert (
            "compañía" in concatenated or "mercantil" in concatenated
        ), "Expected Spanish company terminology in output"
        assert (
            "confidencialidad" in concatenated
        ), "Expected 'confidencialidad' in output"

    @requires_asset(SPANISH_TXT)
    @pytest.mark.asyncio
    async def test_spanish_txt_accuracy(self, parser: TextParser):
        """WER should be low for Spanish text extraction."""
        result = await parser.parse(SPANISH_TXT)
        extracted = _join_pages(result)
        assert_text_accuracy(SPANISH_GROUND_TRUTH, extracted, threshold=0.05)


# ---------------------------------------------------------------------------
# German (umlauts, eszett) — TextParser
# ---------------------------------------------------------------------------


@integration
class TestTextParserMultilingualGerman:
    """Multi-language text extraction from plain text — German characters."""

    GERMAN_SPECIAL_CHARS = frozenset("äöüßÄÖÜ")

    @requires_asset(GERMAN_TXT)
    @pytest.mark.asyncio
    async def test_german_txt_returns_non_empty(self, parser: TextParser):
        """Extracted German text should be non-empty."""
        result = await parser.parse(GERMAN_TXT)
        assert isinstance(result, list)
        concatenated = " ".join(result)
        assert len(concatenated) > 0

    @requires_asset(GERMAN_TXT)
    @pytest.mark.asyncio
    async def test_german_txt_contains_special_chars(self, parser: TextParser):
        """Verify that German-specific characters are preserved."""
        result = await parser.parse(GERMAN_TXT)
        concatenated = " ".join(result)
        found = {ch for ch in concatenated if ch in self.GERMAN_SPECIAL_CHARS}
        assert len(found) >= 2, (
            f"Expected at least 2 distinct German special characters, "
            f"found {len(found)}: {found}"
        )

    @requires_asset(GERMAN_TXT)
    @pytest.mark.asyncio
    async def test_german_txt_contains_key_phrases(self, parser: TextParser):
        """Verify key German phrases with umlauts/eszett survive extraction."""
        result = await parser.parse(GERMAN_TXT)
        concatenated = " ".join(result)
        assert "Müller" in concatenated, "Expected 'Müller' (with umlaut) in output"
        assert "Schmidt" in concatenated, "Expected 'Schmidt' in output"
        assert "Vertrag" in concatenated, "Expected 'Vertrag' in output"
        assert "Geheimhaltung" in concatenated, "Expected 'Geheimhaltung' in output"
        assert (
            "Gesamtvergütung" in concatenated
        ), "Expected 'Gesamtvergütung' (with umlaut) in output"

    @requires_asset(GERMAN_TXT)
    @pytest.mark.asyncio
    async def test_german_txt_accuracy(self, parser: TextParser):
        """WER should be low for German text extraction."""
        result = await parser.parse(GERMAN_TXT)
        extracted = _join_pages(result)
        assert_text_accuracy(GERMAN_GROUND_TRUTH, extracted, threshold=0.05)


# ---------------------------------------------------------------------------
# Mixed English+Hindi — TextParser
# ---------------------------------------------------------------------------


@integration
class TestTextParserMultilingualMixedEnHi:
    """Multi-language text extraction from plain text — mixed English+Hindi."""

    @requires_asset(MIXED_EN_HI_TXT)
    @pytest.mark.asyncio
    async def test_mixed_txt_returns_non_empty(self, parser: TextParser):
        """Extracted mixed English+Hindi text should be non-empty."""
        result = await parser.parse(MIXED_EN_HI_TXT)
        assert isinstance(result, list)
        concatenated = " ".join(result)
        assert len(concatenated) > 0

    @requires_asset(MIXED_EN_HI_TXT)
    @pytest.mark.asyncio
    async def test_mixed_txt_contains_english(self, parser: TextParser):
        """Verify that English text is extracted from mixed-script file."""
        result = await parser.parse(MIXED_EN_HI_TXT)
        concatenated = " ".join(result)
        assert (
            "SERVICE AGREEMENT" in concatenated
            or "service agreement" in concatenated.lower()
        ), "Expected English text 'SERVICE AGREEMENT' in extracted output"

    @requires_asset(MIXED_EN_HI_TXT)
    @pytest.mark.asyncio
    async def test_mixed_txt_contains_hindi(self, parser: TextParser):
        """Verify that Devanagari Hindi text is extracted alongside English."""
        result = await parser.parse(MIXED_EN_HI_TXT)
        concatenated = " ".join(result)
        assert any(
            0x0900 <= ord(ch) <= 0x097F for ch in concatenated
        ), "No Devanagari characters found in mixed English+Hindi extraction"

    @requires_asset(MIXED_EN_HI_TXT)
    @pytest.mark.asyncio
    async def test_mixed_txt_contains_both_scripts(self, parser: TextParser):
        """Verify both Latin and Devanagari scripts appear in output."""
        result = await parser.parse(MIXED_EN_HI_TXT)
        concatenated = " ".join(result)
        has_latin = any(ord(ch) < 128 and ch.isalpha() for ch in concatenated)
        has_devanagari = any(0x0900 <= ord(ch) <= 0x097F for ch in concatenated)
        assert has_latin and has_devanagari, (
            f"Expected both Latin and Devanagari scripts in output "
            f"(has_latin={has_latin}, has_devanagari={has_devanagari})"
        )

    @requires_asset(MIXED_EN_HI_TXT)
    @pytest.mark.asyncio
    async def test_mixed_txt_accuracy(self, parser: TextParser):
        """WER should be low for mixed English+Hindi text extraction."""
        result = await parser.parse(MIXED_EN_HI_TXT)
        extracted = _join_pages(result)
        assert_text_accuracy(MIXED_EN_HI_GROUND_TRUTH, extracted, threshold=0.05)
