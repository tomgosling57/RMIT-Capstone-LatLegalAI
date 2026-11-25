"""
Multilingual integration tests for WordParser.

Verifies correct extraction of Hindi (Devanagari), French, Spanish, German,
and mixed English+Hindi text from .docx files.
"""

from pathlib import Path

import pytest

from services.parsers.word_parser import WordParser
from tests.conftest import assert_text_accuracy

pytestmark = pytest.mark.slow

# ---------------------------------------------------------------------------
# Constants — asset paths
# ---------------------------------------------------------------------------

ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
MULTILINGUAL_DIR = ASSETS_DIR / "multilingual"

# Word document asset files (single-column layout)
HINDI_DOCX = MULTILINGUAL_DIR / "docx/single/hindi_single.docx"
FRENCH_DOCX = MULTILINGUAL_DIR / "docx/single/french_single.docx"
SPANISH_DOCX = MULTILINGUAL_DIR / "docx/single/spanish_single.docx"
GERMAN_DOCX = MULTILINGUAL_DIR / "docx/single/german_single.docx"
MIXED_EN_HI_DOCX = MULTILINGUAL_DIR / "docx/single/mixed_en_hi_single.docx"

# Ground-truth text loaded from source .txt files
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
def parser() -> WordParser:
    """Return a WordParser instance."""
    return WordParser()


def _join_pages(pages: list[str]) -> str:
    """Join extracted pages into a single string."""
    return "\n".join(pages)


# ---------------------------------------------------------------------------
# Hindi (Devanagari) — WordParser
# ---------------------------------------------------------------------------


@integration
class TestWordParserMultilingualHindi:
    """Multi-language text extraction from .docx — Hindi (Devanagari)."""

    @requires_asset(HINDI_DOCX)
    @pytest.mark.asyncio
    async def test_hindi_docx_returns_non_empty(self, parser: WordParser):
        """Extracted Hindi text should be non-empty."""
        result = await parser.parse(HINDI_DOCX)
        assert isinstance(result, list)
        concatenated = " ".join(result)
        assert len(concatenated) > 0

    @requires_asset(HINDI_DOCX)
    @pytest.mark.asyncio
    async def test_hindi_docx_contains_devanagari(self, parser: WordParser):
        """Verify that Devanagari characters appear in extracted text."""
        result = await parser.parse(HINDI_DOCX)
        concatenated = " ".join(result)
        assert any(
            0x0900 <= ord(ch) <= 0x097F for ch in concatenated
        ), "No Devanagari characters found in extracted text"

    @requires_asset(HINDI_DOCX)
    @pytest.mark.asyncio
    async def test_hindi_docx_contains_key_phrases(self, parser: WordParser):
        """Verify key Hindi legal phrases survive extraction."""
        result = await parser.parse(HINDI_DOCX)
        concatenated = " ".join(result)
        key_phrases = [
            "करार",  # Agreement
            "पक्षकार",  # Parties
            "भुगतान",  # Payment
            "गोपनीयता",  # Confidentiality
        ]
        for phrase in key_phrases:
            assert (
                phrase in concatenated
            ), f"Expected Hindi phrase '{phrase}' missing from extracted text"

    @requires_asset(HINDI_DOCX)
    @pytest.mark.asyncio
    async def test_hindi_docx_accuracy(self, parser: WordParser):
        """WER should be low for Hindi text extraction from .docx.

        The docx layout files include a title header that is not present in
        the ground-truth source, so a small threshold accounts for that.
        """
        result = await parser.parse(HINDI_DOCX)
        extracted = _join_pages(result)
        assert_text_accuracy(HINDI_GROUND_TRUTH, extracted, threshold=0.05)


# ---------------------------------------------------------------------------
# French (accented characters) — WordParser
# ---------------------------------------------------------------------------


@integration
class TestWordParserMultilingualFrench:
    """Multi-language text extraction from .docx — French accented characters."""

    FRENCH_ACCENTED_CHARS = frozenset("éèêëàâùûüôöîïç")

    @requires_asset(FRENCH_DOCX)
    @pytest.mark.asyncio
    async def test_french_docx_returns_non_empty(self, parser: WordParser):
        """Extracted French text should be non-empty."""
        result = await parser.parse(FRENCH_DOCX)
        assert isinstance(result, list)
        concatenated = " ".join(result)
        assert len(concatenated) > 0

    @requires_asset(FRENCH_DOCX)
    @pytest.mark.asyncio
    async def test_french_docx_contains_accented_chars(self, parser: WordParser):
        """Verify that accented French characters are preserved."""
        result = await parser.parse(FRENCH_DOCX)
        concatenated = " ".join(result)
        found = {ch for ch in concatenated if ch in self.FRENCH_ACCENTED_CHARS}
        assert len(found) >= 3, (
            f"Expected at least 3 distinct accented characters, "
            f"found {len(found)}: {found}"
        )

    @requires_asset(FRENCH_DOCX)
    @pytest.mark.asyncio
    async def test_french_docx_contains_key_phrases(self, parser: WordParser):
        """Verify key French phrases with accents survive extraction."""
        result = await parser.parse(FRENCH_DOCX)
        concatenated = " ".join(result)
        assert "société" in concatenated, "Expected 'société' (with accent) in output"
        assert "dénommée" in concatenated, "Expected 'dénommée' (with accent) in output"
        assert "siège" in concatenated, "Expected 'siège' (with accent) in output"
        assert (
            "confidentialité" in concatenated
        ), "Expected 'confidentialité' (with accent) in output"

    @requires_asset(FRENCH_DOCX)
    @pytest.mark.asyncio
    async def test_french_docx_accuracy(self, parser: WordParser):
        """WER should be low for French text extraction from .docx."""
        result = await parser.parse(FRENCH_DOCX)
        extracted = _join_pages(result)
        assert_text_accuracy(FRENCH_GROUND_TRUTH, extracted, threshold=0.05)


# ---------------------------------------------------------------------------
# Spanish (special characters) — WordParser
# ---------------------------------------------------------------------------


@integration
class TestWordParserMultilingualSpanish:
    """Multi-language text extraction from .docx — Spanish characters."""

    SPANISH_SPECIAL_CHARS = frozenset("ñÑüÜ¿¡")

    @requires_asset(SPANISH_DOCX)
    @pytest.mark.asyncio
    async def test_spanish_docx_returns_non_empty(self, parser: WordParser):
        """Extracted Spanish text should be non-empty."""
        result = await parser.parse(SPANISH_DOCX)
        assert isinstance(result, list)
        concatenated = " ".join(result)
        assert len(concatenated) > 0

    @requires_asset(SPANISH_DOCX)
    @pytest.mark.asyncio
    async def test_spanish_docx_contains_special_chars(self, parser: WordParser):
        """Verify that Spanish-specific characters are preserved."""
        result = await parser.parse(SPANISH_DOCX)
        concatenated = " ".join(result)
        found = {ch for ch in concatenated if ch in self.SPANISH_SPECIAL_CHARS}
        assert len(found) >= 1, (
            f"Expected at least 1 distinct Spanish special character, "
            f"found {len(found)}: {found}"
        )

    @requires_asset(SPANISH_DOCX)
    @pytest.mark.asyncio
    async def test_spanish_docx_contains_key_phrases(self, parser: WordParser):
        """Verify key Spanish phrases with special chars survive extraction."""
        result = await parser.parse(SPANISH_DOCX)
        concatenated = " ".join(result)
        assert (
            "PRESTACIÓN" in concatenated
        ), "Expected 'PRESTACIÓN' (with accent) in output"
        assert (
            "confidencialidad" in concatenated
        ), "Expected 'confidencialidad' in output"

    @requires_asset(SPANISH_DOCX)
    @pytest.mark.asyncio
    async def test_spanish_docx_accuracy(self, parser: WordParser):
        """WER should be low for Spanish text extraction from .docx."""
        result = await parser.parse(SPANISH_DOCX)
        extracted = _join_pages(result)
        assert_text_accuracy(SPANISH_GROUND_TRUTH, extracted, threshold=0.05)


# ---------------------------------------------------------------------------
# German (umlauts, eszett) — WordParser
# ---------------------------------------------------------------------------


@integration
class TestWordParserMultilingualGerman:
    """Multi-language text extraction from .docx — German characters."""

    GERMAN_SPECIAL_CHARS = frozenset("äöüßÄÖÜ")

    @requires_asset(GERMAN_DOCX)
    @pytest.mark.asyncio
    async def test_german_docx_returns_non_empty(self, parser: WordParser):
        """Extracted German text should be non-empty."""
        result = await parser.parse(GERMAN_DOCX)
        assert isinstance(result, list)
        concatenated = " ".join(result)
        assert len(concatenated) > 0

    @requires_asset(GERMAN_DOCX)
    @pytest.mark.asyncio
    async def test_german_docx_contains_special_chars(self, parser: WordParser):
        """Verify that German-specific characters are preserved."""
        result = await parser.parse(GERMAN_DOCX)
        concatenated = " ".join(result)
        found = {ch for ch in concatenated if ch in self.GERMAN_SPECIAL_CHARS}
        assert len(found) >= 2, (
            f"Expected at least 2 distinct German special characters, "
            f"found {len(found)}: {found}"
        )

    @requires_asset(GERMAN_DOCX)
    @pytest.mark.asyncio
    async def test_german_docx_contains_key_phrases(self, parser: WordParser):
        """Verify key German phrases with umlauts/eszett survive extraction."""
        result = await parser.parse(GERMAN_DOCX)
        concatenated = " ".join(result)
        assert "Müller" in concatenated, "Expected 'Müller' (with umlaut) in output"
        assert "Schmidt" in concatenated, "Expected 'Schmidt' in output"
        assert "Vertrag" in concatenated, "Expected 'Vertrag' in output"
        assert "Geheimhaltung" in concatenated, "Expected 'Geheimhaltung' in output"
        assert (
            "Gesamtvergütung" in concatenated
        ), "Expected 'Gesamtvergütung' (with umlaut) in output"

    @requires_asset(GERMAN_DOCX)
    @pytest.mark.asyncio
    async def test_german_docx_accuracy(self, parser: WordParser):
        """WER should be low for German text extraction from .docx."""
        result = await parser.parse(GERMAN_DOCX)
        extracted = _join_pages(result)
        assert_text_accuracy(GERMAN_GROUND_TRUTH, extracted, threshold=0.05)


# ---------------------------------------------------------------------------
# Mixed English+Hindi — WordParser
# ---------------------------------------------------------------------------


@integration
class TestWordParserMultilingualMixedEnHi:
    """Multi-language text extraction from .docx — mixed English+Hindi."""

    @requires_asset(MIXED_EN_HI_DOCX)
    @pytest.mark.asyncio
    async def test_mixed_docx_returns_non_empty(self, parser: WordParser):
        """Extracted mixed English+Hindi text should be non-empty."""
        result = await parser.parse(MIXED_EN_HI_DOCX)
        assert isinstance(result, list)
        concatenated = " ".join(result)
        assert len(concatenated) > 0

    @requires_asset(MIXED_EN_HI_DOCX)
    @pytest.mark.asyncio
    async def test_mixed_docx_contains_english(self, parser: WordParser):
        """Verify that English text is extracted from mixed-script .docx."""
        result = await parser.parse(MIXED_EN_HI_DOCX)
        concatenated = " ".join(result)
        assert (
            "SERVICE AGREEMENT" in concatenated
            or "service agreement" in concatenated.lower()
        ), "Expected English text 'SERVICE AGREEMENT' in extracted output"

    @requires_asset(MIXED_EN_HI_DOCX)
    @pytest.mark.asyncio
    async def test_mixed_docx_contains_hindi(self, parser: WordParser):
        """Verify that Devanagari Hindi text is extracted alongside English."""
        result = await parser.parse(MIXED_EN_HI_DOCX)
        concatenated = " ".join(result)
        assert any(
            0x0900 <= ord(ch) <= 0x097F for ch in concatenated
        ), "No Devanagari characters found in mixed English+Hindi extraction"

    @requires_asset(MIXED_EN_HI_DOCX)
    @pytest.mark.asyncio
    async def test_mixed_docx_contains_both_scripts(self, parser: WordParser):
        """Verify both Latin and Devanagari scripts appear in output."""
        result = await parser.parse(MIXED_EN_HI_DOCX)
        concatenated = " ".join(result)
        has_latin = any(ord(ch) < 128 and ch.isalpha() for ch in concatenated)
        has_devanagari = any(0x0900 <= ord(ch) <= 0x097F for ch in concatenated)
        assert has_latin and has_devanagari, (
            f"Expected both Latin and Devanagari scripts in output "
            f"(has_latin={has_latin}, has_devanagari={has_devanagari})"
        )

    @requires_asset(MIXED_EN_HI_DOCX)
    @pytest.mark.asyncio
    async def test_mixed_docx_accuracy(self, parser: WordParser):
        """WER should be low for mixed English+Hindi text extraction from .docx."""
        result = await parser.parse(MIXED_EN_HI_DOCX)
        extracted = _join_pages(result)
        assert_text_accuracy(MIXED_EN_HI_GROUND_TRUTH, extracted, threshold=0.05)
