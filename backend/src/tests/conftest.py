"""
Pytest configuration for Golden Engine integration tests.
Reads document schemas from docs/document_schemas/ and generates
assets in tests/assets/ before tests run.
"""

import sys
from pathlib import Path

import pytest

from services.accuracy_calc import calculate_wer
from services.text_utils import normalize_text


# Add backend/src to path for importing DocumentTransformer
sys.path.insert(0, str(Path(__file__).parent))

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ASSETS_DIR = Path(__file__).parent / "assets"


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
        Maximum acceptable Word Error Rate (default 0.05 = 5 %).

    Raises
    ------
    AssertionError
        If the calculated WER exceeds *threshold*.  The message includes the
        normalised versions of both strings and the actual WER.
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
