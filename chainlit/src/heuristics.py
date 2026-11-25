"""Lightweight heuristic functions for user intent detection.

These functions parse plain-text messages to determine whether the
user is asking for a section summary or a document translation.

They live in a standalone module so they can be imported and tested
without pulling in the full Chainlit application dependency chain
(``chainlit``, ``langchain``, ``langdetect``, etc.).
"""


def is_section_summary_request(text: str) -> bool:
    """Heuristic: detect if the user is asking for a section summary.

    Args:
        text: The user's message text.

    Returns:
        ``True`` if the text contains one of the known section-summary
        keyword phrases (case-insensitive).
    """
    lowered = text.lower().strip()
    keywords = (
        "section summary",
        "summarise sections",
        "summarize sections",
        "list sections",
        "document sections",
        "what are the sections",
        "section breakdown",
        "outline the document",
        "identify sections",
    )
    return any(kw in lowered for kw in keywords)


def is_translation_request(text: str) -> bool:
    """Heuristic: detect if the user is asking for document translation.

    Uses a two-tier approach to avoid false positives:

    *Tier 1* — Direct translation keywords (``translate``,
    ``translation``, ``convert to``) always trigger a match.

    *Tier 2* — ``in {language}`` patterns only match if they appear
    within the first 10 characters of the message, avoiding false
    positives like ``"I'm interested in English literature"`` while
    still catching short queries such as ``"In english please"``.

    Args:
        text: The user's message text.

    Returns:
        ``True`` if the text looks like a translation request.
    """
    lowered = text.lower().strip()

    # Tier 1: Strong signals — directly mention translation
    if any(kw in lowered for kw in ("translate", "translation", "convert to")):
        return True

    # Tier 2: "in {language}" patterns — only match near the start of
    # the message to avoid false positives from general language mentions.
    language_keywords = (
        "in english",
        "in hindi",
        "in french",
        "in spanish",
        "in german",
        "in chinese",
        "in arabic",
        "in portuguese",
        "in urdu",
        "in indonesian",
    )
    for kw in language_keywords:
        idx = lowered.find(kw)
        # Only match if the pattern appears within the first 10 characters.
        # Short queries like "In english please" (idx=0) or "Reply in spanish"
        # (idx=6) match, but longer false positives like "I'm interested in
        # English literature" (idx=15) are rejected.
        if idx != -1 and idx < 10:
            return True

    return False
