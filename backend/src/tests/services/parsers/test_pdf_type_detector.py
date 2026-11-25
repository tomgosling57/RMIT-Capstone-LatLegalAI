"""
Unit tests for ``detect_pdf_type()`` in ``pdf_type_detector``.

All ``pdfplumber`` interactions and file-system operations are fully mocked
so that no real PDF files are required.
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.parsers.pdf_type_detector import (
    PDFType,
    detect_pdf_type,
)


# ============================================================================
# Helpers
# ============================================================================


def _make_mock_page(
    xobjects: list[dict] | None = None,
    text: str = "",
) -> MagicMock:
    """Build a mock ``pdfplumber.page.Page`` with optional XObjects and text."""
    page = MagicMock()
    page.xobjects = xobjects or []
    page.extract_text.return_value = text
    return page


def _make_mock_pdf(
    pages: list[MagicMock] | None = None,
) -> MagicMock:
    """Build a mock ``pdfplumber.PDF`` with the given pages."""
    pdf = MagicMock()
    pages = pages or []
    pdf.pages = pages
    pdf.__enter__.return_value = pdf
    pdf.__exit__.return_value = None
    return pdf


def _make_mock_pdf_side_effect(
    pages: list[MagicMock],
    num_opens: int = 2,
) -> list[MagicMock]:
    """
    Build a list of mock PDFs to use as a ``side_effect`` for
    ``pdfplumber.open``.

    ``detect_pdf_type`` opens the PDF at most twice:
      - Stage 1 calls ``pdfplumber.open``
      - Stage 2 calls ``pdfplumber.open`` again (if Stage 1 was inconclusive)

    ``_has_significant_images`` no longer reopens the PDF; it consumes
    cached ``_ImageStats`` from Stage 1.

    Args:
        pages: The mock pages to attach to each PDF instance.
        num_opens: Number of separate PDF opens to mock (default 2).

    Each call should return a separate mock so that the context managers
    don't interfere with each other.
    """
    return [_make_mock_pdf(pages) for _ in range(num_opens)]


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def fake_path(tmp_path: Path) -> Path:
    """Return a temporary file path that *exists* on disk (zero bytes)."""
    p = tmp_path / "test.pdf"
    p.write_bytes(b"")
    return p


# ============================================================================
# TestDetectPDFType
# ============================================================================


class TestDetectPDFType:
    """Core classification scenarios for ``detect_pdf_type()``."""

    # ------------------------------------------------------------------
    # 1. Digital PDF — no images, all pages have text
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_digital_pdf_no_images_with_text(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF with zero images and abundant text on every page should
        be classified as DIGITAL."""
        pages = [
            _make_mock_page(xobjects=[], text="A" * 100),
            _make_mock_page(xobjects=[], text="B" * 100),
            _make_mock_page(xobjects=[], text="C" * 100),
        ]
        # Stage 1 opens the PDF once and returns DIGITAL early
        mock_pdfplumber_open.return_value = _make_mock_pdf(pages)

        result = detect_pdf_type(fake_path)

        assert result == PDFType.DIGITAL

    # ------------------------------------------------------------------
    # 2. Scanned PDF — many images, no text
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_scanned_pdf_many_images_no_text(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF with a high image density (>= 1.5 images/page) and no
        extractable text should be classified as SCANNED."""
        pages = [
            _make_mock_page(
                xobjects=[{"subtype": "Image"}, {"subtype": "Image"}],
                text="",
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}, {"subtype": "Image"}],
                text="",
            ),
        ]
        mock_pdfplumber_open.return_value = _make_mock_pdf(pages)

        result = detect_pdf_type(fake_path)

        assert result == PDFType.SCANNED

    # ------------------------------------------------------------------
    # 3. Scanned PDF — few images, no text (falls through to Stage 3)
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    @patch("services.parsers.pdf_type_detector.Path.is_file")
    @patch("services.parsers.pdf_type_detector.Path.stat")
    def test_scanned_pdf_few_images_no_text(
        self,
        mock_stat: MagicMock,
        mock_is_file: MagicMock,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF with a moderate image density (between thresholds) and no
        text should fall through to Stage 3 and be classified as SCANNED
        when the file is large."""
        mock_is_file.return_value = True
        # 2 pages, 1 image each → 0.5 images/page → inconclusive in Stage 1
        pages = [
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="",
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="",
            ),
        ]
        # Stage 1 opens PDF, Stage 2 opens PDF, _has_significant_images opens PDF
        mock_pdfplumber_open.side_effect = _make_mock_pdf_side_effect(pages)
        # Stage 3: large file → SCANNED
        mock_stat.return_value.st_size = 500_000

        result = detect_pdf_type(fake_path)

        assert result == PDFType.SCANNED

    # ------------------------------------------------------------------
    # 4. Hybrid PDF — some text, some images
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_hybrid_pdf_some_text_some_images(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF with both images and text on most pages should be
        classified as HYBRID."""
        # Stage 1: 5 pages, 1 image each → 1.0 images/page → inconclusive
        # Stage 2: text ratio >= 0.6 → then _has_significant_images returns True
        pages = [
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="A" * 100,
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="B" * 100,
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="C" * 100,
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="D" * 100,
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="E" * 100,
            ),
        ]
        # Stage 1 opens PDF, Stage 2 opens PDF, _has_significant_images opens PDF
        mock_pdfplumber_open.side_effect = _make_mock_pdf_side_effect(pages)

        result = detect_pdf_type(fake_path)

        assert result == PDFType.HYBRID

    # ------------------------------------------------------------------
    # 5. Hybrid PDF — no images, partial text (Stage 1 decisive → DIGITAL)
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_hybrid_pdf_no_images_partial_text(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF with no images but partial text coverage — Stage 1 returns
        DIGITAL (0 images/page <= 0.1), so the function returns DIGITAL
        early.  This scenario tests that when Stage 1 is decisive, Stage 2
        is never reached."""
        pages = [
            _make_mock_page(xobjects=[], text="A" * 100),
            _make_mock_page(xobjects=[], text="B" * 100),
        ]
        mock_pdfplumber_open.return_value = _make_mock_pdf(pages)

        result = detect_pdf_type(fake_path)

        # 0 images across 2 pages → 0.0 images/page → DIGITAL
        assert result == PDFType.DIGITAL

    # ------------------------------------------------------------------
    # 6. Unknown type — fallback to size heuristic (ambiguous size)
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    @patch("services.parsers.pdf_type_detector.Path.is_file")
    @patch("services.parsers.pdf_type_detector.Path.stat")
    def test_unknown_type_fallback_size(
        self,
        mock_stat: MagicMock,
        mock_is_file: MagicMock,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """When Stages 1 and 2 are inconclusive and the file size falls in
        the ambiguous middle range, the result should be UNKNOWN."""
        mock_is_file.return_value = True
        # Stage 1: 2 pages, 1 image each → 0.5 images/page → inconclusive
        pages = [
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="",
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="",
            ),
        ]
        mock_pdfplumber_open.side_effect = _make_mock_pdf_side_effect(pages)
        # Stage 3: ambiguous size (between 50k and 200k)
        mock_stat.return_value.st_size = 100_000

        result = detect_pdf_type(fake_path)

        assert result == PDFType.UNKNOWN

    # ------------------------------------------------------------------
    # 7. Digital by size heuristic
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    @patch("services.parsers.pdf_type_detector.Path.is_file")
    @patch("services.parsers.pdf_type_detector.Path.stat")
    def test_digital_by_size_heuristic(
        self,
        mock_stat: MagicMock,
        mock_is_file: MagicMock,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """When Stages 1 and 2 are inconclusive and the file is small
        (<= 50k), the result should be DIGITAL."""
        mock_is_file.return_value = True
        pages = [
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="",
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="",
            ),
        ]
        mock_pdfplumber_open.side_effect = _make_mock_pdf_side_effect(pages)
        mock_stat.return_value.st_size = 10_000

        result = detect_pdf_type(fake_path)

        assert result == PDFType.DIGITAL

    # ------------------------------------------------------------------
    # 8. Scanned by size heuristic
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    @patch("services.parsers.pdf_type_detector.Path.is_file")
    @patch("services.parsers.pdf_type_detector.Path.stat")
    def test_scanned_by_size_heuristic(
        self,
        mock_stat: MagicMock,
        mock_is_file: MagicMock,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """When Stages 1 and 2 are inconclusive and the file is large
        (>= 200k), the result should be SCANNED."""
        mock_is_file.return_value = True
        pages = [
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="",
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="",
            ),
        ]
        mock_pdfplumber_open.side_effect = _make_mock_pdf_side_effect(pages)
        mock_stat.return_value.st_size = 500_000

        result = detect_pdf_type(fake_path)

        assert result == PDFType.SCANNED

    # ------------------------------------------------------------------
    # 9. Single-page digital
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_single_page_digital(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A single-page PDF with no images and text should be DIGITAL."""
        page = _make_mock_page(xobjects=[], text="A" * 100)
        mock_pdfplumber_open.return_value = _make_mock_pdf([page])

        result = detect_pdf_type(fake_path)

        assert result == PDFType.DIGITAL

    # ------------------------------------------------------------------
    # 10. Single-page scanned
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_single_page_scanned(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A single-page PDF with many images and no text should be
        SCANNED."""
        page = _make_mock_page(
            xobjects=[
                {"subtype": "Image"},
                {"subtype": "Image"},
            ],
            text="",
        )
        mock_pdfplumber_open.return_value = _make_mock_pdf([page])

        result = detect_pdf_type(fake_path)

        assert result == PDFType.SCANNED

    # ------------------------------------------------------------------
    # 11. Empty PDF (zero pages)
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    @patch("services.parsers.pdf_type_detector.Path.is_file")
    @patch("services.parsers.pdf_type_detector.Path.stat")
    def test_empty_pdf(
        self,
        mock_stat: MagicMock,
        mock_is_file: MagicMock,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF with zero pages should fall through all stages and
        return UNKNOWN."""
        mock_is_file.return_value = True
        # Stage 1: 0 pages → inconclusive (returns None)
        # Stage 2: 0 pages → inconclusive (returns None)
        # _has_significant_images is never called because Stage 2 returns None
        mock_pdfplumber_open.side_effect = _make_mock_pdf_side_effect([])
        mock_stat.return_value.st_size = 100_000

        result = detect_pdf_type(fake_path)

        assert result == PDFType.UNKNOWN

    # ------------------------------------------------------------------
    # 12. Corrupted PDF — raises warning, returns UNKNOWN
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.Path.exists")
    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    @patch("services.parsers.pdf_type_detector.Path.is_file")
    @patch("services.parsers.pdf_type_detector.Path.stat")
    def test_corrupted_pdf_raises_warning(
        self,
        mock_stat: MagicMock,
        mock_is_file: MagicMock,
        mock_pdfplumber_open: MagicMock,
        mock_exists: MagicMock,
        fake_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When pdfplumber raises an exception in every stage, the
        function should log a warning and return UNKNOWN."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_pdfplumber_open.side_effect = Exception("Corrupted PDF")
        mock_stat.side_effect = Exception("Cannot stat")

        caplog.set_level(logging.WARNING)

        result = detect_pdf_type(fake_path)

        assert result == PDFType.UNKNOWN
        assert "All detection stages failed" in caplog.text

    # ------------------------------------------------------------------
    # 13. Digital PDF with a logo (few images, abundant text)
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_digital_pdf_with_logo(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF with a single logo image (low image density) and
        abundant text should be classified as HYBRID by the current
        heuristic (the image density exceeds LOW_IMAGE_DENSITY)."""
        pages = [
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],  # 1 logo
                text="A" * 200,
            ),
            _make_mock_page(
                xobjects=[],  # no images on subsequent pages
                text="B" * 200,
            ),
            _make_mock_page(
                xobjects=[],
                text="C" * 200,
            ),
        ]
        # Stage 1: 1 image across 3 pages → 0.33 images/page → > 0.1
        # → inconclusive. Stage 2 opens PDF again, _has_significant_images
        # opens PDF a third time.
        mock_pdfplumber_open.side_effect = _make_mock_pdf_side_effect(pages)

        result = detect_pdf_type(fake_path)

        # Stage 2: 3/3 pages have text → text_ratio = 1.0
        # → _has_significant_images returns True (0.33 > 0.1) → HYBRID
        assert result == PDFType.HYBRID


# ============================================================================
# TestDetectPDFTypeEdgeCases
# ============================================================================


class TestDetectPDFTypeEdgeCases:
    """Edge-case and boundary-condition scenarios."""

    # ------------------------------------------------------------------
    # 14. Very large PDF — sampling behaviour
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_very_large_pdf_sampling(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF with many pages (more than SAMPLE_SIZE) should only
        sample the first SAMPLE_SIZE pages for text extraction."""
        # 20 pages, no images, first 5 have text, remaining 15 have none
        pages = []
        for i in range(20):
            text = "A" * 100 if i < 5 else ""
            pages.append(_make_mock_page(xobjects=[], text=text))

        mock_pdfplumber_open.return_value = _make_mock_pdf(pages)

        result = detect_pdf_type(fake_path)

        # Stage 1: 0 images across 20 pages → 0.0 images/page → DIGITAL
        # (returns early, never reaches Stage 2)
        assert result == PDFType.DIGITAL

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    @patch("services.parsers.pdf_type_detector.Path.is_file")
    @patch("services.parsers.pdf_type_detector.Path.stat")
    def test_very_large_pdf_sampling_inconclusive_stage1(
        self,
        mock_stat: MagicMock,
        mock_is_file: MagicMock,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF with many pages where Stage 1 is inconclusive — Stage 2
        should sample only the first SAMPLE_SIZE pages."""
        mock_is_file.return_value = True
        # 20 pages, 1 image each → 1.0 images/page → inconclusive
        pages = []
        for i in range(20):
            # First 3 pages have text, rest don't
            text = "A" * 100 if i < 3 else ""
            pages.append(_make_mock_page(xobjects=[{"subtype": "Image"}], text=text))

        mock_pdfplumber_open.side_effect = _make_mock_pdf_side_effect(pages)
        # Stage 3: ambiguous size
        mock_stat.return_value.st_size = 100_000

        result = detect_pdf_type(fake_path)

        # Stage 2 samples 5 pages: pages 0-4 → 3 have text → 3/5 = 0.6
        # → text_ratio >= 0.6 → _has_significant_images returns True
        # → HYBRID
        assert result == PDFType.HYBRID

    # ------------------------------------------------------------------
    # 15. PDF with mixed page types
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    @patch("services.parsers.pdf_type_detector.Path.is_file")
    @patch("services.parsers.pdf_type_detector.Path.stat")
    def test_pdf_with_mixed_page_types(
        self,
        mock_stat: MagicMock,
        mock_is_file: MagicMock,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF where some pages are image-based and others are
        text-based should be classified as DIGITAL via the size heuristic."""
        mock_is_file.return_value = True
        pages = [
            # Page 0: image-only (scanned)
            _make_mock_page(
                xobjects=[{"subtype": "Image"}, {"subtype": "Image"}],
                text="",
            ),
            # Page 1: text-only (digital)
            _make_mock_page(
                xobjects=[],
                text="A" * 100,
            ),
            # Page 2: image-only
            _make_mock_page(
                xobjects=[{"subtype": "Image"}, {"subtype": "Image"}],
                text="",
            ),
            # Page 3: text-only
            _make_mock_page(
                xobjects=[],
                text="B" * 100,
            ),
            # Page 4: image-only
            _make_mock_page(
                xobjects=[{"subtype": "Image"}, {"subtype": "Image"}],
                text="",
            ),
        ]
        mock_pdfplumber_open.side_effect = _make_mock_pdf_side_effect(pages)
        # Stage 3: small file size -> DIGITAL
        mock_stat.return_value.st_size = 10_000

        result = detect_pdf_type(fake_path)

        # Stage 1: 6 images across 5 pages -> 1.2 images/page -> inconclusive
        # Stage 2: 5 pages sampled, 2 have text -> 2/5 = 0.4 < 0.6 -> inconclusive
        # Stage 3: file size <= 50k -> DIGITAL
        assert result == PDFType.DIGITAL

    # ------------------------------------------------------------------
    # 16. PDF with embedded fonts, no images
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_pdf_with_embedded_fonts_no_images(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF with embedded fonts but no images and full text should
        be DIGITAL."""
        pages = [
            _make_mock_page(xobjects=[], text="A" * 100),
            _make_mock_page(xobjects=[], text="B" * 100),
            _make_mock_page(xobjects=[], text="C" * 100),
        ]
        mock_pdfplumber_open.return_value = _make_mock_pdf(pages)

        result = detect_pdf_type(fake_path)

        # Stage 1: 0 images across 3 pages → 0.0 images/page → DIGITAL
        assert result == PDFType.DIGITAL

    # ------------------------------------------------------------------
    # 17. PDF with form fields (AcroForm) — no images, some text
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_pdf_with_form_fields(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
    ) -> None:
        """A PDF with form fields (AcroForm) but no images and partial
        text should be classified based on the text extraction stage."""
        # 5 pages, no images, only 2 pages have meaningful text
        pages = [
            _make_mock_page(xobjects=[], text="A" * 100),
            _make_mock_page(xobjects=[], text="B" * 100),
            _make_mock_page(xobjects=[], text=""),
            _make_mock_page(xobjects=[], text=""),
            _make_mock_page(xobjects=[], text=""),
        ]
        mock_pdfplumber_open.return_value = _make_mock_pdf(pages)

        result = detect_pdf_type(fake_path)

        # Stage 1: 0 images across 5 pages → 0.0 images/page → DIGITAL
        assert result == PDFType.DIGITAL

    # ------------------------------------------------------------------
    # Log message verification helpers
    # ------------------------------------------------------------------

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_digital_log_message(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify that a DIGITAL classification logs an info message with
        the correct PDF type."""
        page = _make_mock_page(xobjects=[], text="A" * 100)
        mock_pdfplumber_open.return_value = _make_mock_pdf([page])

        caplog.set_level(logging.INFO)
        detect_pdf_type(fake_path)

        # The log message contains the lowercase enum value
        assert "digital" in caplog.text

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_scanned_log_message(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify that a SCANNED classification logs an info message with
        the correct PDF type."""
        page = _make_mock_page(
            xobjects=[{"subtype": "Image"}, {"subtype": "Image"}],
            text="",
        )
        mock_pdfplumber_open.return_value = _make_mock_pdf([page])

        caplog.set_level(logging.INFO)
        detect_pdf_type(fake_path)

        assert "scanned" in caplog.text

    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    def test_hybrid_log_message(
        self,
        mock_pdfplumber_open: MagicMock,
        fake_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify that a HYBRID classification logs an info message with
        the correct PDF type."""
        pages = [
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="A" * 100,
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="B" * 100,
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="C" * 100,
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="D" * 100,
            ),
            _make_mock_page(
                xobjects=[{"subtype": "Image"}],
                text="E" * 100,
            ),
        ]
        mock_pdfplumber_open.side_effect = _make_mock_pdf_side_effect(pages)

        caplog.set_level(logging.INFO)
        detect_pdf_type(fake_path)

        assert "hybrid" in caplog.text

    @patch("services.parsers.pdf_type_detector.Path.exists")
    @patch("services.parsers.pdf_type_detector.pdfplumber.open")
    @patch("services.parsers.pdf_type_detector.Path.is_file")
    @patch("services.parsers.pdf_type_detector.Path.stat")
    def test_unknown_log_message(
        self,
        mock_stat: MagicMock,
        mock_is_file: MagicMock,
        mock_pdfplumber_open: MagicMock,
        mock_exists: MagicMock,
        fake_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify that an UNKNOWN classification logs a warning message."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_pdfplumber_open.side_effect = _make_mock_pdf_side_effect([])
        mock_stat.return_value.st_size = 100_000

        caplog.set_level(logging.INFO)
        detect_pdf_type(fake_path)

        # The log message contains the lowercase enum value "unknown"
        assert "unknown" in caplog.text
