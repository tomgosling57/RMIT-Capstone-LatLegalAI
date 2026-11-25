"""
Integration tests for ``detect_pdf_type()`` and ``DocumentParserFactory`` routing.

Uses real PDF assets from the ``tests/assets/`` directory tree to verify that:

* ``detect_pdf_type()`` correctly classifies digital vs. scanned PDFs.
* ``DocumentParserFactory.get_parser()`` routes each PDF type to the correct
  parser (``PDFParser`` for digital/hybrid/unknown, ``OCRPDFParser`` for scanned).
* Parsing produces non-empty text (and for OCR, page markers).

Asset groups exercised:
  - ``golden/``         — digital PDFs, scanned PDFs, and multi-layout documents
  - ``OCR_test/``       — native PDFs, scanned PDFs, and image files
  - ``multilingual/``   — digital and scanned PDFs in French, German, Spanish,
                          Hindi, and mixed English-Hindi
"""

from __future__ import annotations

from pathlib import Path

import pytest

from services.parsers.ocr_pdf_parser import OCRPDFParser
from services.parsers.pdf_parser import PDFParser
from services.parsers.pdf_type_detector import PDFType, detect_pdf_type

# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

integration = pytest.mark.integration


def requires_asset(path: Path):
    """Skip test if the asset file is missing."""
    return pytest.mark.skipif(
        not path.exists(),
        reason=f"Asset not found: {path} — populate tests/assets/ to run this test",
    )


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
GOLDEN_DIR = ASSETS_DIR / "golden"
OCR_TEST_DIR = ASSETS_DIR / "OCR_test"
MULTILINGUAL_DIR = ASSETS_DIR / "multilingual"

# ── golden/ digital PDFs (single layout) ─────────────────────────────────
GOLDEN_DIGITAL_SINGLE = sorted((GOLDEN_DIR / "pdf/single").glob("*.pdf"))

# ── golden/ scanned PDFs (single layout) ─────────────────────────────────
GOLDEN_SCANNED_SINGLE = sorted(
    (GOLDEN_DIR / "scanned_pdf/single").glob("*_scanned.pdf")
)

# ── golden/ all three documents (digital) across all layouts ─────────────
GOLDEN_DIGITAL_ALL = sorted(
    list((GOLDEN_DIR / "pdf/single").glob("*.pdf"))
    + list((GOLDEN_DIR / "pdf/double").glob("*.pdf"))
    + list((GOLDEN_DIR / "pdf/multi").glob("*.pdf"))
)

# ── golden/ all three documents (scanned) across all layouts ─────────────
GOLDEN_SCANNED_ALL = sorted(
    list((GOLDEN_DIR / "scanned_pdf/single").glob("*_scanned.pdf"))
    + list((GOLDEN_DIR / "scanned_pdf/double").glob("*_scanned.pdf"))
    + list((GOLDEN_DIR / "scanned_pdf/multi").glob("*_scanned.pdf"))
)

# ── golden/ multi-layout digital PDFs ────────────────────────────────────
GOLDEN_MULTI_DIGITAL = sorted((GOLDEN_DIR / "pdf/multi").glob("*.pdf"))

# ── golden/ multi-layout scanned PDFs ────────────────────────────────────
GOLDEN_MULTI_SCANNED = sorted((GOLDEN_DIR / "scanned_pdf/multi").glob("*_scanned.pdf"))

# ── OCR_test/ assets ─────────────────────────────────────────────────────
OCR_NATIVE_PDF = OCR_TEST_DIR / "native_pdfs/sample-standard_contract.pdf"
OCR_NATIVE_PDF_2 = OCR_TEST_DIR / "native_pdfs/sample-limited-by-guarantee.pdf"
OCR_SCANNED_PDF = OCR_TEST_DIR / "scanned_pdfs/image_doc.pdf"
OCR_IMAGE_FILE = OCR_TEST_DIR / "images/test_document.png"

# ── multilingual/ digital PDFs (single layout) ───────────────────────────
MULTILINGUAL_DIGITAL = sorted((MULTILINGUAL_DIR / "pdf/single").glob("*.pdf"))

# ── multilingual/ scanned PDFs (single layout) ───────────────────────────
MULTILINGUAL_SCANNED = sorted(
    (MULTILINGUAL_DIR / "scanned_pdf/single").glob("*_scanned.pdf")
)


# ===================================================================
# Golden asset integration tests
# ===================================================================


class TestGoldenDigitalPDFDetection:
    """``detect_pdf_type()`` classifies golden digital PDFs as DIGITAL."""

    @integration
    @requires_asset(GOLDEN_DIGITAL_SINGLE[0])
    def test_golden_digital_pdf_detected(self) -> None:
        """A golden digital PDF should be classified as DIGITAL."""
        for pdf_path in GOLDEN_DIGITAL_SINGLE:
            pdf_type = detect_pdf_type(pdf_path)
            assert (
                pdf_type == PDFType.DIGITAL
            ), f"Expected DIGITAL for {pdf_path.name}, got {pdf_type.value}"


class TestGoldenScannedPDFDetection:
    """``detect_pdf_type()`` classifies golden scanned PDFs as SCANNED."""

    @integration
    @requires_asset(GOLDEN_SCANNED_SINGLE[0])
    def test_golden_scanned_pdf_detected(self) -> None:
        """A golden scanned PDF should be classified as SCANNED."""
        for pdf_path in GOLDEN_SCANNED_SINGLE:
            pdf_type = detect_pdf_type(pdf_path)
            assert (
                pdf_type == PDFType.SCANNED
            ), f"Expected SCANNED for {pdf_path.name}, got {pdf_type.value}"


class TestGoldenDigitalRouting:
    """``DocumentParserFactory`` routes golden digital PDFs to ``PDFParser``."""

    @integration
    @requires_asset(GOLDEN_DIGITAL_SINGLE[0])
    def test_golden_digital_routed_correctly(self) -> None:
        """A golden digital PDF should be routed to PDFParser."""
        from services.parsers.parser_factory import DocumentParserFactory

        factory = DocumentParserFactory()
        for pdf_path in GOLDEN_DIGITAL_SINGLE:
            parser = factory.get_parser(pdf_path)
            assert isinstance(parser, PDFParser), (
                f"Expected PDFParser for {pdf_path.name}, "
                f"got {type(parser).__name__}"
            )


class TestGoldenScannedRouting:
    """``DocumentParserFactory`` routes golden scanned PDFs to ``OCRPDFParser``."""

    @integration
    @requires_asset(GOLDEN_SCANNED_SINGLE[0])
    def test_golden_scanned_routed_correctly(self) -> None:
        """A golden scanned PDF should be routed to OCRPDFParser."""
        from services.parsers.parser_factory import DocumentParserFactory

        factory = DocumentParserFactory()
        for pdf_path in GOLDEN_SCANNED_SINGLE:
            parser = factory.get_parser(pdf_path)
            assert isinstance(parser, OCRPDFParser), (
                f"Expected OCRPDFParser for {pdf_path.name}, "
                f"got {type(parser).__name__}"
            )


class TestGoldenDigitalParsing:
    """Golden digital PDFs produce non-empty text via ``PDFParser``."""

    @integration
    @requires_asset(GOLDEN_DIGITAL_SINGLE[0])
    @pytest.mark.asyncio
    async def test_golden_digital_parses_successfully(self) -> None:
        """A golden digital PDF should yield non-empty text from PDFParser."""
        parser = PDFParser()
        for pdf_path in GOLDEN_DIGITAL_SINGLE:
            pages = await parser.parse(pdf_path)
            assert pages, f"PDFParser returned empty list for {pdf_path.name}"
            combined = " ".join(pages)
            assert (
                combined.strip()
            ), f"PDFParser returned only whitespace for {pdf_path.name}"
            # Verify meaningful content — at least a few words
            word_count = len(combined.split())
            assert word_count >= 10, (
                f"PDFParser extracted only {word_count} words from "
                f"{pdf_path.name}; expected at least 10"
            )


class TestGoldenScannedParsing:
    """Golden scanned PDFs produce non-empty text via ``OCRPDFParser``."""

    @integration
    @requires_asset(GOLDEN_SCANNED_SINGLE[0])
    @pytest.mark.asyncio
    async def test_golden_scanned_parses_via_ocr(self) -> None:
        """A golden scanned PDF should yield non-empty text from OCRPDFParser."""
        parser = OCRPDFParser()
        for pdf_path in GOLDEN_SCANNED_SINGLE:
            pages = await parser.parse(pdf_path)
            assert pages, f"OCRPDFParser returned empty list for {pdf_path.name}"
            combined = " ".join(pages)
            assert (
                combined.strip()
            ), f"OCRPDFParser returned only whitespace for {pdf_path.name}"
            # Verify page markers are present for scanned PDFs
            assert any(
                "--- Page" in page for page in pages
            ), f"No page markers found in OCR output for {pdf_path.name}"


class TestGoldenAllDigital:
    """All three golden documents (across layouts) are detected as DIGITAL."""

    @integration
    @requires_asset(GOLDEN_DIGITAL_ALL[0])
    def test_golden_all_three_documents_digital(self) -> None:
        """Every golden digital PDF across single/double/multi layouts is DIGITAL."""
        for pdf_path in GOLDEN_DIGITAL_ALL:
            pdf_type = detect_pdf_type(pdf_path)
            assert (
                pdf_type == PDFType.DIGITAL
            ), f"Expected DIGITAL for {pdf_path.name}, got {pdf_type.value}"


class TestGoldenAllScanned:
    """All three golden scanned documents (across layouts) are detected as SCANNED."""

    @integration
    @requires_asset(GOLDEN_SCANNED_ALL[0])
    def test_golden_all_three_documents_scanned(self) -> None:
        """Every golden scanned PDF across single/double/multi layouts is SCANNED."""
        for pdf_path in GOLDEN_SCANNED_ALL:
            pdf_type = detect_pdf_type(pdf_path)
            assert (
                pdf_type == PDFType.SCANNED
            ), f"Expected SCANNED for {pdf_path.name}, got {pdf_type.value}"


class TestGoldenMultiLayoutDetection:
    """Multi-layout golden digital PDFs are detected as DIGITAL."""

    @integration
    @requires_asset(GOLDEN_MULTI_DIGITAL[0])
    def test_golden_multi_layout_detection(self) -> None:
        """Multi-column golden digital PDFs should be classified as DIGITAL."""
        for pdf_path in GOLDEN_MULTI_DIGITAL:
            pdf_type = detect_pdf_type(pdf_path)
            assert pdf_type == PDFType.DIGITAL, (
                f"Expected DIGITAL for multi-layout {pdf_path.name}, "
                f"got {pdf_type.value}"
            )


class TestGoldenMultiLayoutScannedDetection:
    """Multi-layout golden scanned PDFs are detected as SCANNED."""

    @integration
    @requires_asset(GOLDEN_MULTI_SCANNED[0])
    def test_golden_multi_layout_scanned_detection(self) -> None:
        """Multi-column golden scanned PDFs should be classified as SCANNED."""
        for pdf_path in GOLDEN_MULTI_SCANNED:
            pdf_type = detect_pdf_type(pdf_path)
            assert pdf_type == PDFType.SCANNED, (
                f"Expected SCANNED for multi-layout scanned {pdf_path.name}, "
                f"got {pdf_type.value}"
            )


# ===================================================================
# OCR_test asset integration tests
# ===================================================================


class TestOCRNativePDFDetection:
    """``detect_pdf_type()`` classifies OCR_test native PDFs as DIGITAL."""

    @integration
    @requires_asset(OCR_NATIVE_PDF)
    def test_ocr_native_pdf_detected_as_digital(self) -> None:
        """A native (digital) PDF from OCR_test should be DIGITAL."""
        pdf_type = detect_pdf_type(OCR_NATIVE_PDF)
        assert (
            pdf_type == PDFType.DIGITAL
        ), f"Expected DIGITAL for {OCR_NATIVE_PDF.name}, got {pdf_type.value}"


class TestOCRScannedPDFDetection:
    """``detect_pdf_type()`` classifies OCR_test scanned PDFs as SCANNED."""

    @integration
    @requires_asset(OCR_SCANNED_PDF)
    def test_ocr_scanned_pdf_detected_as_scanned(self) -> None:
        """A scanned PDF from OCR_test should be SCANNED."""
        pdf_type = detect_pdf_type(OCR_SCANNED_PDF)
        assert (
            pdf_type == PDFType.SCANNED
        ), f"Expected SCANNED for {OCR_SCANNED_PDF.name}, got {pdf_type.value}"


class TestOCRNativePDFRouting:
    """``DocumentParserFactory`` routes OCR_test native PDFs to ``PDFParser``."""

    @integration
    @requires_asset(OCR_NATIVE_PDF)
    def test_ocr_native_pdf_routed_to_pdfparser(self) -> None:
        """A native PDF from OCR_test should be routed to PDFParser."""
        from services.parsers.parser_factory import DocumentParserFactory

        factory = DocumentParserFactory()
        parser = factory.get_parser(OCR_NATIVE_PDF)
        assert isinstance(parser, PDFParser), (
            f"Expected PDFParser for {OCR_NATIVE_PDF.name}, "
            f"got {type(parser).__name__}"
        )


class TestOCRScannedPDFRouting:
    """``DocumentParserFactory`` routes OCR_test scanned PDFs to ``OCRPDFParser``."""

    @integration
    @requires_asset(OCR_SCANNED_PDF)
    def test_ocr_scanned_pdf_routed_to_ocrpdfparser(self) -> None:
        """A scanned PDF from OCR_test should be routed to OCRPDFParser."""
        from services.parsers.parser_factory import DocumentParserFactory

        factory = DocumentParserFactory()
        parser = factory.get_parser(OCR_SCANNED_PDF)
        assert isinstance(parser, OCRPDFParser), (
            f"Expected OCRPDFParser for {OCR_SCANNED_PDF.name}, "
            f"got {type(parser).__name__}"
        )


class TestOCRImageFileUnchanged:
    """``detect_pdf_type()`` raises ``FileNotFoundError`` for non-PDF image files."""

    @integration
    @requires_asset(OCR_IMAGE_FILE)
    def test_ocr_image_file_unchanged(self) -> None:
        """An image file (non-PDF) should not be processed by detect_pdf_type;
        the function should raise FileNotFoundError because it only handles
        PDF files (pdfplumber will fail on a .png)."""
        with pytest.raises((FileNotFoundError, ValueError)):
            detect_pdf_type(OCR_IMAGE_FILE)


# ===================================================================
# Multilingual asset integration tests
# ===================================================================


class TestMultilingualDigitalDetection:
    """Multilingual digital PDFs are detected as DIGITAL."""

    @integration
    @requires_asset(MULTILINGUAL_DIGITAL[0])
    def test_multilingual_digital_detected(self) -> None:
        """Every multilingual digital PDF should be classified as DIGITAL."""
        for pdf_path in MULTILINGUAL_DIGITAL:
            pdf_type = detect_pdf_type(pdf_path)
            assert (
                pdf_type == PDFType.DIGITAL
            ), f"Expected DIGITAL for {pdf_path.name}, got {pdf_type.value}"


class TestMultilingualScannedDetection:
    """Multilingual scanned PDFs are detected as SCANNED."""

    @integration
    @requires_asset(MULTILINGUAL_SCANNED[0])
    def test_multilingual_scanned_detected(self) -> None:
        """Every multilingual scanned PDF should be classified as SCANNED."""
        for pdf_path in MULTILINGUAL_SCANNED:
            pdf_type = detect_pdf_type(pdf_path)
            assert (
                pdf_type == PDFType.SCANNED
            ), f"Expected SCANNED for {pdf_path.name}, got {pdf_type.value}"


class TestMultilingualDigitalParsing:
    """Multilingual digital PDFs produce non-empty text via ``PDFParser``."""

    @integration
    @requires_asset(MULTILINGUAL_DIGITAL[0])
    @pytest.mark.asyncio
    async def test_multilingual_digital_parses_correctly(self) -> None:
        """Every multilingual digital PDF should yield non-empty text
        from PDFParser."""
        parser = PDFParser()
        for pdf_path in MULTILINGUAL_DIGITAL:
            pages = await parser.parse(pdf_path)
            assert pages, f"PDFParser returned empty list for {pdf_path.name}"
            combined = " ".join(pages)
            assert (
                combined.strip()
            ), f"PDFParser returned only whitespace for {pdf_path.name}"
            # Verify meaningful content
            word_count = len(combined.split())
            assert word_count >= 5, (
                f"PDFParser extracted only {word_count} words from "
                f"{pdf_path.name}; expected at least 5"
            )


class TestMultilingualScannedFallback:
    """Multilingual scanned PDFs produce non-empty text via ``OCRPDFParser``."""

    @integration
    @requires_asset(MULTILINGUAL_SCANNED[0])
    @pytest.mark.asyncio
    async def test_multilingual_scanned_fallback_works(self) -> None:
        """Every multilingual scanned PDF should yield non-empty text
        from OCRPDFParser (fallback OCR path)."""
        parser = OCRPDFParser()
        for pdf_path in MULTILINGUAL_SCANNED:
            pages = await parser.parse(pdf_path)
            assert pages, f"OCRPDFParser returned empty list for {pdf_path.name}"
            combined = " ".join(pages)
            assert (
                combined.strip()
            ), f"OCRPDFParser returned only whitespace for {pdf_path.name}"
            # Verify page markers are present
            assert any(
                "--- Page" in page for page in pages
            ), f"No page markers found in OCR output for {pdf_path.name}"
