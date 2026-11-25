"""
Integration test to verify the CID character decoding bug fix.

This test verifies that the PDF parser correctly decodes the bullet point
character (•) that was previously appearing as (cid:127) in extracted text.
"""

import pytest

from services.parsers.pdf_parser import PDFParser


@pytest.mark.asyncio
async def test_pdf_parser_decodes_bullet_character() -> None:
    """
    Test that PDFParser correctly decodes the bullet character (•).

    This is a regression test for the bug where styled PDF documents
    with embedded fonts would output (cid:127) instead of the bullet point.
    """

    # Test the normalization function directly with the reported issue
    test_text = "of algorithmic bias (cid:127) technical paper th"
    normalized = PDFParser._normalize_cid_characters(test_text)

    # Should replace (cid:127) with bullet point •
    assert "(cid:127)" not in normalized, "CID reference was not replaced"
    assert "•" in normalized, "Bullet point was not found in normalized text"
    assert normalized == "of algorithmic bias • technical paper th"


@pytest.mark.asyncio
async def test_pdf_parser_handles_multiple_cid_variants() -> None:
    """
    Test that the parser handles multiple CID variants for bullet points.

    Different PDF fonts may use different CID codes for the same character.
    """
    test_cases = [
        ("text (cid:127) bullet", "text • bullet"),
        ("text (cid:149) bullet", "text • bullet"),
        ("text (cid:181) bullet", "text • bullet"),
    ]

    for input_text, expected_output in test_cases:
        result = PDFParser._normalize_cid_characters(input_text)
        assert result == expected_output, (
            f"Failed for {input_text}: expected '{expected_output}', " f"got '{result}'"
        )


@pytest.mark.asyncio
async def test_pdf_parser_preserves_non_cid_text() -> None:
    """
    Test that non-CID text is preserved during normalization.
    """
    original = "This is a paragraph with actual bullet • character."
    result = PDFParser._normalize_cid_characters(original)
    assert result == original


def test_cid_normalization_regex_pattern() -> None:
    """
    Test that the regex pattern correctly captures CID references.
    """
    import re

    pattern = r"\(cid:(\d+)\)"

    test_strings = [
        ("text (cid:127) more", True),
        ("multiple (cid:127) and (cid:166)", True),
        ("(cid:123)", True),
        ("text with no CID codes", False),
        ("(cid:) incomplete", False),
    ]

    for text, should_match in test_strings:
        matches = re.findall(pattern, text)
        if should_match:
            assert len(matches) > 0, f"Expected matches in '{text}'"
        else:
            assert len(matches) == 0, f"Unexpected matches in '{text}'"
