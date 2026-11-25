"""
Unit tests for ``DocumentParserFactory`` PDF routing logic.

Tests verify that ``get_parser()`` correctly routes PDF files based on
the ``PDFType`` returned by ``detect_pdf_type()``, and that non-PDF files
are unaffected by the PDF detection machinery.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from services.parsers.ocr_pdf_parser import OCRPDFParser
from services.parsers.pdf_parser import PDFParser
from services.parsers.word_parser import WordParser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pdf_path(tmp_path: Path) -> Path:
    """Return a temporary ``.pdf`` file path (file is not created on disk)."""
    return tmp_path / "test.pdf"


@pytest.fixture
def docx_path(tmp_path: Path) -> Path:
    """Return a temporary ``.docx`` file path (file is not created on disk)."""
    return tmp_path / "test.docx"


# ---------------------------------------------------------------------------
# PDF routing — each PDFType value
# ---------------------------------------------------------------------------


def test_get_parser_digital_pdf_returns_pdfparser(pdf_path: Path) -> None:
    """
    When ``detect_pdf_type()`` returns ``PDFType.DIGITAL``,
    ``DocumentParserFactory.get_parser()`` must return a ``PDFParser`` instance.
    """
    from services.parsers.parser_factory import DocumentParserFactory
    from services.parsers.pdf_type_detector import PDFType

    with patch(
        "services.parsers.parser_factory.detect_pdf_type",
        return_value=PDFType.DIGITAL,
    ):
        factory = DocumentParserFactory()
        parser = factory.get_parser(pdf_path)

    assert isinstance(
        parser, PDFParser
    ), f"Expected PDFParser for DIGITAL PDF, got {type(parser).__name__}"


def test_get_parser_scanned_pdf_returns_ocrpdfparser(pdf_path: Path) -> None:
    """
    When ``detect_pdf_type()`` returns ``PDFType.SCANNED``,
    ``DocumentParserFactory.get_parser()`` must return an ``OCRPDFParser`` instance.
    """
    from services.parsers.parser_factory import DocumentParserFactory
    from services.parsers.pdf_type_detector import PDFType

    with patch(
        "services.parsers.parser_factory.detect_pdf_type",
        return_value=PDFType.SCANNED,
    ):
        factory = DocumentParserFactory()
        parser = factory.get_parser(pdf_path)

    assert isinstance(
        parser, OCRPDFParser
    ), f"Expected OCRPDFParser for SCANNED PDF, got {type(parser).__name__}"


def test_get_parser_hybrid_pdf_returns_pdfparser(pdf_path: Path) -> None:
    """
    When ``detect_pdf_type()`` returns ``PDFType.HYBRID``,
    ``DocumentParserFactory.get_parser()`` must return a ``PDFParser`` instance.
    """
    from services.parsers.parser_factory import DocumentParserFactory
    from services.parsers.pdf_type_detector import PDFType

    with patch(
        "services.parsers.parser_factory.detect_pdf_type",
        return_value=PDFType.HYBRID,
    ):
        factory = DocumentParserFactory()
        parser = factory.get_parser(pdf_path)

    assert isinstance(
        parser, PDFParser
    ), f"Expected PDFParser for HYBRID PDF, got {type(parser).__name__}"


def test_get_parser_unknown_pdf_returns_pdfparser(pdf_path: Path) -> None:
    """
    When ``detect_pdf_type()`` returns ``PDFType.UNKNOWN``,
    ``DocumentParserFactory.get_parser()`` must return a ``PDFParser`` instance.
    """
    from services.parsers.parser_factory import DocumentParserFactory
    from services.parsers.pdf_type_detector import PDFType

    with patch(
        "services.parsers.parser_factory.detect_pdf_type",
        return_value=PDFType.UNKNOWN,
    ):
        factory = DocumentParserFactory()
        parser = factory.get_parser(pdf_path)

    assert isinstance(
        parser, PDFParser
    ), f"Expected PDFParser for UNKNOWN PDF, got {type(parser).__name__}"


# ---------------------------------------------------------------------------
# Non-PDF routing (unaffected by PDF type detection)
# ---------------------------------------------------------------------------


def test_get_parser_non_pdf_unaffected(docx_path: Path) -> None:
    """
    Non-PDF files (e.g. ``.docx``) must be routed by extension-based logic
    regardless of ``detect_pdf_type()``.  The factory should return a
    ``WordParser`` for a ``.docx`` file.
    """
    from services.parsers.parser_factory import DocumentParserFactory

    with patch("services.parsers.parser_factory.detect_pdf_type") as mock_detect:
        factory = DocumentParserFactory()
        parser = factory.get_parser(docx_path)

    assert isinstance(
        parser, WordParser
    ), f"Expected WordParser for .docx file, got {type(parser).__name__}"
    mock_detect.assert_not_called()


# ---------------------------------------------------------------------------
# OCR fallback flag
# ---------------------------------------------------------------------------


def test_get_parser_ocr_fallback_disabled() -> None:
    """
    When ``use_ocr_fallback=False``, the factory must not include
    ``OCRPDFParser`` in its parser list (``self._parsers``).
    """
    from services.parsers.parser_factory import DocumentParserFactory

    factory = DocumentParserFactory(use_ocr_fallback=False)

    assert not any(
        isinstance(p, OCRPDFParser) for p in factory._parsers
    ), "OCRPDFParser should not be in the parser list when use_ocr_fallback=False"
