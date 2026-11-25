"""
Parameterized golden file integration tests for document parsers.

Tests every combination of parser × file format × layout × source document,
comparing extracted text against the golden source texts.

Directory layout expected:
    backend/src/tests/assets/golden/
    ├── source/          *.txt  (golden standard)
    ├── pdf/             single/ double/ multi/  *.pdf
    ├── docx/            single/ double/ multi/  *.docx
    ├── txt/             single/ double/ multi/  *.txt
    └── scanned_pdf/     single/ double/ multi/  *_scanned.pdf
"""

from __future__ import annotations

import difflib
import re
import textwrap
from pathlib import Path
from typing import Any

import pytest

from services.parsers.ocr_pdf_parser import OCRPDFParser
from services.parsers.pdf_parser import PDFParser
from services.parsers.text_parser import TextParser
from services.parsers.word_parser import WordParser

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

GOLDEN_ROOT = Path(__file__).parents[2] / "assets" / "golden"
SOURCE_DIR = GOLDEN_ROOT / "source"

LAYOUTS = ("single", "double", "multi")

# Map each format directory name → (parser class, glob pattern)
FORMAT_CONFIG: dict[str, tuple[Any, str]] = {
    "pdf": (PDFParser, "*.pdf"),
    "docx": (WordParser, "*.docx"),
    "txt": (TextParser, "*.txt"),
    "scanned_pdf": (OCRPDFParser, "*_scanned.pdf"),
}

# Fuzzy-match threshold for OCR (Jaccard on word sets, 0–1)
OCR_SIMILARITY_THRESHOLD = 0.80

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    """Collapse whitespace and lowercase for deterministic comparison."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _to_sentences(text: str) -> list[str]:
    """
    Split normalised text into sentence-like chunks on '.', '!', '?'
    so that diffs are readable rather than one giant wall of text.
    """
    parts = re.split(r"(?<=[.!?])\s+", normalize_text(text))
    return [p.strip() for p in parts if p.strip()]


def word_set_similarity(a: str, b: str) -> float:
    """Jaccard similarity between the word sets of two strings."""
    set_a = set(normalize_text(a).split())
    set_b = set(normalize_text(b).split())
    if not set_a and not set_b:
        return 1.0
    return len(set_a & set_b) / len(set_a | set_b)


# --- missing-content helpers ------------------------------------------------


def _missing_words(extracted: str, source: str) -> list[str]:
    """Words present in *source* but absent from *extracted* (normalised)."""
    src_words = set(normalize_text(source).split())
    ext_words = set(normalize_text(extracted).split())
    return sorted(src_words - ext_words)


def _extra_words(extracted: str, source: str) -> list[str]:
    """Words present in *extracted* but absent from *source* (normalised)."""
    src_words = set(normalize_text(source).split())
    ext_words = set(normalize_text(extracted).split())
    return sorted(ext_words - src_words)


# --- ordering helper --------------------------------------------------------


def _order_problems(extracted: str, source: str, n: int = 8) -> list[str]:
    """
    Return a human-readable list of the first *n* sequence-order violations.

    Strategy: use SequenceMatcher to find matching blocks, then report any
    block whose position in the extracted stream is out of order relative to
    the previous matched block in the source stream.
    """
    ext_sentences = _to_sentences(extracted)
    src_sentences = _to_sentences(source)

    matcher = difflib.SequenceMatcher(
        None, src_sentences, ext_sentences, autojunk=False
    )
    blocks = [b for b in matcher.get_matching_blocks() if b.size > 0]

    problems: list[str] = []
    prev_src_end = 0

    for block in blocks:
        src_start = block.a
        if src_start < prev_src_end:
            # This block appears earlier in source than the previous match —
            # the extracted text reordered content.
            fragment = " ".join(src_sentences[block.a : block.a + block.size])
            problems.append(
                f"  • Out-of-order: {fragment[:120]!r} "
                f"(source pos {src_start}, expected after {prev_src_end})"
            )
            if len(problems) >= n:
                break
        prev_src_end = block.a + block.size

    return problems


# --- unified diff helper ----------------------------------------------------


def _unified_diff_excerpt(extracted: str, source: str, context: int = 3) -> str:
    """
    Return a short unified diff (sentence-level) between source and extracted,
    capped at 60 lines so failures stay readable.
    """
    src_lines = _to_sentences(source)
    ext_lines = _to_sentences(extracted)
    diff = list(
        difflib.unified_diff(
            src_lines,
            ext_lines,
            fromfile="source",
            tofile="extracted",
            lineterm="",
            n=context,
        )
    )
    cap = 60
    truncation_note = (
        [f"  … diff truncated to {cap} lines …"] if len(diff) > cap else []
    )
    return "\n".join(diff[:cap] + truncation_note)


# --- master diagnostic ------------------------------------------------------


def _build_failure_message(
    file_path: Path,
    extracted: str,
    source: str,
    *,
    is_ocr: bool = False,
    ocr_similarity: float | None = None,
) -> str:
    """
    Compose a structured failure message covering:
      1. High-level stats (char/word counts)
      2. Missing content (words in source but not extracted)
      3. Extra content  (words in extracted but not source)
      4. Ordering problems
      5. Unified diff excerpt
    """
    norm_ext = normalize_text(extracted)
    norm_src = normalize_text(source)

    ext_words = norm_ext.split()
    src_words = norm_src.split()

    missing = _missing_words(extracted, source)
    extra = _extra_words(extracted, source)
    order = _order_problems(extracted, source)

    def _word_list(words: list[str], cap: int = 20) -> str:
        shown = words[:cap]
        suffix = f" … and {len(words) - cap} more" if len(words) > cap else ""
        return ", ".join(shown) + suffix

    lines: list[str] = [
        "",
        f"{'=' * 70}",
        f"PARSER FAILURE: {file_path}",
        f"{'=' * 70}",
    ]

    # --- stats ---
    lines += [
        "",
        "── Stats ──────────────────────────────────────────────────────────",
        f"  source   : {len(src_words):>6} words  |  {len(norm_src):>7} chars",
        f"  extracted: {len(ext_words):>6} words  |  {len(norm_ext):>7} chars",
        f"  word delta: {len(ext_words) - len(src_words):+d}",
    ]
    if is_ocr and ocr_similarity is not None:
        lines.append(
            f"  OCR Jaccard similarity: {ocr_similarity:.2%}  "
            f"(threshold {OCR_SIMILARITY_THRESHOLD:.0%})"
        )

    # --- missing content ---
    if missing:
        lines += [
            "",
            f"── Missing content ({len(missing)} words in "
            f"source but NOT in extracted) ─",
            f"  {_word_list(missing)}",
        ]
    else:
        lines += ["", "── Missing content: none ✓"]

    # --- extra content ---
    if extra:
        lines += [
            "",
            f"── Extra content ({len(extra)} words in extracted "
            f"but NOT in source) ────",
            f"  {_word_list(extra)}",
        ]
    else:
        lines += ["", "── Extra content: none ✓"]

    # --- ordering ---
    if order:
        lines += [
            "",
            f"── Ordering problems ({len(order)} out-of-sequence blocks detected) ────",
        ]
        lines += order
    else:
        lines += ["", "── Ordering: correct ✓"]

    # --- diff ---
    diff_text = _unified_diff_excerpt(extracted, source)
    if diff_text:
        lines += [
            "",
            "── Sentence-level unified diff (source → extracted) ───────────────",
            textwrap.indent(diff_text, "  "),
        ]

    lines.append("")
    return "\n".join(lines)


def load_source_texts() -> dict[str, str]:
    """Return {stem: text} for every file in the source directory."""
    texts: dict[str, str] = {}
    for path in SOURCE_DIR.glob("*.txt"):
        texts[path.stem] = path.read_text(encoding="utf-8")
    return texts


def _stem_to_source_key(file_stem: str, source_texts: dict[str, str]) -> str | None:
    """
    Map a golden-file stem such as ``ai_ethics_australia_single``
    to the matching source key ``ai_ethics_australia``.
    """
    for source_key in source_texts:
        if file_stem.startswith(source_key):
            return source_key
    return None


# ---------------------------------------------------------------------------
# Build parametrize matrix
# ---------------------------------------------------------------------------


def _build_test_matrix() -> list[tuple]:
    """
    Returns a flat list of tuples:
        (parser_class, file_path, source_text, test_id)
    one entry per (format × layout × document).
    """
    source_texts = load_source_texts()
    matrix: list[tuple] = []

    for fmt, (parser_cls, glob) in FORMAT_CONFIG.items():
        fmt_dir = GOLDEN_ROOT / fmt
        if not fmt_dir.exists():
            continue

        for layout in LAYOUTS:
            layout_dir = fmt_dir / layout
            if not layout_dir.exists():
                continue

            for file_path in sorted(layout_dir.glob(glob)):
                source_key = _stem_to_source_key(file_path.stem, source_texts)
                if source_key is None:
                    # No matching source text — skip silently
                    continue

                test_id = f"{fmt}/{layout}/{file_path.stem}"
                matrix.append(
                    (parser_cls, file_path, source_texts[source_key], test_id)
                )

    return matrix


_MATRIX = _build_test_matrix()


def _is_ocr(parser_cls: Any) -> bool:
    return parser_cls is OCRPDFParser


# ---------------------------------------------------------------------------
# Core extraction test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "parser_cls, file_path, source_text",
    [(m[0], m[1], m[2]) for m in _MATRIX],
    ids=[m[3] for m in _MATRIX],
)
async def test_parser_extracts_golden_text(
    parser_cls: Any,
    file_path: Path,
    source_text: str,
) -> None:
    """
    Each parser must reproduce the source text from the corresponding
    golden file.  OCR results are validated with a fuzzy Jaccard threshold;
    all other parsers require exact (normalised) equality.
    """
    parser = parser_cls()
    extracted: str = await parser.parse(file_path)

    assert extracted, f"Parser returned empty string for {file_path}"

    if _is_ocr(parser_cls):
        similarity = word_set_similarity(extracted, source_text)
        assert similarity >= OCR_SIMILARITY_THRESHOLD, (
            f"OCR similarity {similarity:.2%} < {OCR_SIMILARITY_THRESHOLD:.0%} "
            f"for {file_path}"
        )
    else:
        assert normalize_text(extracted) == normalize_text(source_text), (
            f"Text mismatch for {file_path}\n"
            f"  extracted[:200] = {normalize_text(extracted)[:200]!r}\n"
            f"  source[:200]    = {normalize_text(source_text)[:200]!r}"
        )


# ---------------------------------------------------------------------------
# Supports-format contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parser_cls, file_path",
    [(m[0], m[1]) for m in _MATRIX],
    ids=[m[3] for m in _MATRIX],
)
def test_parser_supports_format(parser_cls: Any, file_path: Path) -> None:
    """
    ``supports_format()`` must return True for every file in the matrix
    that was matched to this parser.
    """
    parser = parser_cls()
    assert parser.supports_format(
        file_path
    ), f"{parser_cls.__name__}.supports_format() returned False for {file_path}"


# ---------------------------------------------------------------------------
# OCR-specific: page markers
# ---------------------------------------------------------------------------


def _scanned_pdf_paths() -> list[tuple[str, Path]]:
    """Return (layout, path) pairs for every scanned PDF golden file."""
    results: list[tuple[str, Path]] = []
    scanned_dir = GOLDEN_ROOT / "scanned_pdf"
    if not scanned_dir.exists():
        return results
    for layout in LAYOUTS:
        layout_dir = scanned_dir / layout
        if layout_dir.exists():
            for p in sorted(layout_dir.glob("*_scanned.pdf")):
                results.append((layout, p))
    return results


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "layout, file_path",
    _scanned_pdf_paths(),
    ids=[f"scanned_pdf/{t[0]}/{t[1].stem}" for t in _scanned_pdf_paths()],
)
async def test_ocr_page_markers_present(layout: str, file_path: Path) -> None:
    """
    OCRPDFParser must insert ``--- Page N ---`` markers for multi-page
    scanned PDFs.
    """
    parser = OCRPDFParser()
    result: str = await parser.parse(file_path)
    assert (
        "--- Page 1 ---" in result
    ), f"No page marker found in OCR output for {file_path}"


# ---------------------------------------------------------------------------
# Missing-file error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "parser_cls", [PDFParser, WordParser, TextParser, OCRPDFParser]
)
async def test_parser_raises_on_missing_file(parser_cls: Any) -> None:
    """Every parser must raise FileNotFoundError for a non-existent path."""
    parser = parser_cls()
    with pytest.raises(FileNotFoundError):
        await parser.parse(Path("/nonexistent/path/file.pdf"))


# ---------------------------------------------------------------------------
# Factory integration smoke test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "file_path, expected_parser_cls",
    [
        (GOLDEN_ROOT / "pdf" / "single", PDFParser),
        (GOLDEN_ROOT / "docx" / "single", WordParser),
        (GOLDEN_ROOT / "txt" / "single", TextParser),
        (GOLDEN_ROOT / "scanned_pdf" / "single", OCRPDFParser),
    ],
)
async def test_factory_returns_correct_parser(
    file_path: Path,
    expected_parser_cls: Any,
) -> None:
    """
    DocumentParserFactory.get_parser() should resolve to the right parser
    for each format directory's first golden file.
    """
    # Import here to avoid hard failure if factory isn't on path yet
    from services.parsers.parser_factory import DocumentParserFactory

    candidates = sorted(file_path.glob("*")) if file_path.is_dir() else []
    if not candidates:
        pytest.skip(f"No files found under {file_path}")

    factory = DocumentParserFactory()
    parser = factory.get_parser(candidates[0])
    assert isinstance(parser, expected_parser_cls), (
        f"Expected {expected_parser_cls.__name__}, got {type(parser).__name__} "
        f"for {candidates[0]}"
    )
