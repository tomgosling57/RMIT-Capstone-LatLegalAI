"""
Pytest configuration for Chainlit parser unit tests.

Provides:
  - assert_text_accuracy helper (Word Error Rate assertion)
  - --run-slow CLI option for skipping slow tests by default
"""

import sys
from pathlib import Path

import pytest

# Ensure chainlit/src/tests/ is on the Python path so that
# ``from conftest import assert_text_accuracy`` works.
# Add chainlit/ (the src package parent) so that
# ``from src.tools.pdf_parser import PDFParser`` resolves correctly,
# with ``src`` as a proper package (preserving relative imports within src/).
# Also add the project root so that ``from shared.file_validation import ...`` resolves.
_tests_dir = str(Path(__file__).parent)
_chainlit_dir = str(Path(__file__).parent.parent.parent)  # chainlit/src/tests -> chainlit/
_project_root = str(Path(__file__).parent.parent.parent.parent)  # chainlit/src/tests -> project root
for _p in (_tests_dir, _chainlit_dir, _project_root):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    """
    Normalise text for WER comparison.

    - Lowercases
    - Standardises curly quotes to straight quotes
    - Collapses whitespace (including newlines) to single spaces
    - Strips leading/trailing whitespace
    """
    import re

    text = text.lower()
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Calculate Word Error Rate between *reference* and *hypothesis* strings.

    Uses Levenshtein distance at the word level.

    Returns a float between 0.0 (perfect) and 1.0 (completely wrong).
    """
    ref_words = reference.split()
    hyp_words = hypothesis.split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    # Levenshtein distance on word lists
    n, m = len(ref_words), len(hyp_words)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # deletion
                dp[i][j - 1] + 1,  # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )

    return dp[n][m] / n


def assert_text_accuracy(expected: str, actual: str, threshold: float = 0.05) -> None:
    """
    Assert that the Word Error Rate between *expected* and *actual* text
    does not exceed *threshold*.

    Both strings are normalised before comparison so that minor differences
    in casing, whitespace, and curly-quote characters do not inflate the WER.

    Parameters
    ----------
    expected : str
        The reference (ground-truth) text.
    actual : str
        The text produced by the system under test.
    threshold : float
        Maximum acceptable Word Error Rate (default 0.05 = 5 %).

    Raises
    ------
    AssertionError
        If the calculated WER exceeds *threshold*.
    """
    norm_expected: str = normalize_text(expected)
    norm_actual: str = normalize_text(actual)

    wer: float = calculate_wer(norm_expected, norm_actual)

    assert wer <= threshold, (
        f"Text accuracy assertion failed\n"
        f"  Normalised expected : {norm_expected!r}\n"
        f"  Normalised actual   : {norm_actual!r}\n"
        f"  Word Error Rate     : {wer:.4f}  (threshold: {threshold})"
    )


# ---------------------------------------------------------------------------
# Pytest configuration
# ---------------------------------------------------------------------------


def pytest_addoption(parser):
    """Add command-line option for running slow tests."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests (by default, slow tests are skipped)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip slow tests by default unless --run-slow is passed."""
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="slow test - use --run-slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
