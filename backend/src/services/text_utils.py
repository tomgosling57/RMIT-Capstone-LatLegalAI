"""
Utility functions for text processing, including squashing paginated text,
removing page markers for NLP processing, and normalizing raw text.
"""

import re
from typing import List


def normalize_text(text: str) -> str:
    """
    Normalize raw text by lowercasing, collapsing whitespace, stripping
    leading/trailing whitespace, and standardizing curly quotes to straight
    quotes.

    Args:
        text: Input string to normalize.

    Returns:
        Normalized string with consistent casing, spacing, and punctuation.
    """
    # Force lowercase
    result: str = text.lower()

    # Standardize curly quotes (left and right double quotes) to straight
    result = result.replace("\u201c", '"').replace("\u201d", '"')

    # Collapse all consecutive whitespace (spaces, tabs, newlines) into a single space
    result = re.sub(r"\s+", " ", result)

    # Strip leading/trailing whitespace
    return result.strip()


def squash_paginated_text(pages: List[str]) -> str:
    """
    Squash paginated text from multiple pages into a single continuous string.

    Args:
        pages: List of strings, each representing a page of text

    Returns:
        Single string with all pages concatenated
    """
    return "\n".join(pages)


def remove_page_markers(text: str) -> str:
    """
    Remove page markers (page numbers, page headers/footers) from text.

    This function removes:
    - Standalone page numbers (1-4 digits)
    - "Page X" style footer text
    - "Page X of Y" style headers/footers
    - "X of Y" style footers
    - Lines with just page number patterns

    Args:
        text: Input text potentially containing page markers

    Returns:
        Text with page markers removed
    """
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        line_content = line.strip()

        # Skip pure page numbers like: "12", "  12  "
        if re.fullmatch(r"\d{1,4}", line_content):
            continue

        # Skip "Page 12" style footers
        if re.fullmatch(r"(?i)page\s*\d{1,4}", line_content):
            continue

        # Skip "Page 1 of 10" style headers/footers
        if re.fullmatch(r"(?i)page\s+\d+\s+of\s+\d+", line_content):
            continue

        # Skip "1 of 10" style footers
        if re.fullmatch(r"\d+\s+of\s+\d+", line_content):
            continue

        # Skip lines consisting only of common separators (e.g. "---", "***", "===")
        if re.fullmatch(r"[-*=_:\s]{3,20}", line_content):
            continue

        # Skip lines that look like page numbers with dash or slash separators
        # (e.g. "12-", "-12-", "3/4") but only when short and purely numeric/symbolic
        if (
            re.fullmatch(r"\d{1,4}[-/\\]?\d{0,4}", line_content)
            and len(line_content) <= 9
        ):
            continue

        cleaned.append(line)

    # Rebuild while preserving paragraph spacing
    return "\n".join(cleaned)


def clean_and_squash_text(pages: List[str]) -> str:
    """
    Combine squash and page marker removal for complete text cleaning.

    Args:
        pages: List of strings, each representing a page of text

    Returns:
        Cleaned, squashed text ready for NLP processing
    """
    # First squash all pages into single text
    text = squash_paginated_text(pages)

    # Then remove page markers
    return remove_page_markers(text)
