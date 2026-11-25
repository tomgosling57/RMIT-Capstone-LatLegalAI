"""
Unit tests for the scanned-PDF visual indicator in the Streamlit chat UI.

Tests cover:
1. ``render_scanned_indicator()`` — verifies the HTML structure of the indicator.
2. The conditional display logic — verifies the indicator is rendered only when
   ``detect_pdf_type()`` returns ``PDFType.SCANNED``, and is *not* rendered for
   ``DIGITAL``, ``HYBRID``, or ``UNKNOWN``.

All Streamlit and pdfplumber interactions are fully mocked so that no real
PDF files or browser sessions are required.
"""

from __future__ import annotations

from unittest.mock import MagicMock


from components.theme import render_scanned_indicator
from utils.pdf_type_detector import PDFType


# ============================================================================
# Tests for render_scanned_indicator()
# ============================================================================


class TestRenderScannedIndicator:
    """Verify the HTML output of ``render_scanned_indicator()``."""

    def test_returns_non_empty_string(self) -> None:
        """The function must return a non-empty string."""
        html = render_scanned_indicator()
        assert isinstance(html, str)
        assert len(html) > 0

    def test_contains_scanned_indicator_css_class(self) -> None:
        """The HTML must include the ``scanned-indicator`` CSS class."""
        html = render_scanned_indicator()
        assert "scanned-indicator" in html

    def test_contains_fade_in_animation_class(self) -> None:
        """The HTML must include the ``fade-in`` animation class."""
        html = render_scanned_indicator()
        assert "fade-in" in html

    def test_contains_role_alert(self) -> None:
        """The HTML must include ``role="alert"`` for accessibility."""
        html = render_scanned_indicator()
        assert 'role="alert"' in html

    def test_contains_aria_live_polite(self) -> None:
        """The HTML must include ``aria-live="polite"`` for accessibility."""
        html = render_scanned_indicator()
        assert 'aria-live="polite"' in html

    def test_contains_warning_icon(self) -> None:
        """The HTML must include the warning emoji icon."""
        html = render_scanned_indicator()
        assert "⚠️" in html

    def test_contains_scanned_document_label(self) -> None:
        """The HTML must include the label text 'Scanned Document'."""
        html = render_scanned_indicator()
        assert "Scanned Document" in html

    def test_contains_ocr_message(self) -> None:
        """The HTML must mention OCR processing in the message."""
        html = render_scanned_indicator()
        assert "OCR" in html or "ocr" in html

    def test_contains_scanned_indicator_icon_class(self) -> None:
        """The HTML must include the BEM icon class."""
        html = render_scanned_indicator()
        assert "scanned-indicator__icon" in html

    def test_contains_scanned_indicator_content_class(self) -> None:
        """The HTML must include the BEM content class."""
        html = render_scanned_indicator()
        assert "scanned-indicator__content" in html

    def test_contains_scanned_indicator_label_class(self) -> None:
        """The HTML must include the BEM label class."""
        html = render_scanned_indicator()
        assert "scanned-indicator__label" in html

    def test_contains_scanned_indicator_message_class(self) -> None:
        """The HTML must include the BEM message class."""
        html = render_scanned_indicator()
        assert "scanned-indicator__message" in html


# ============================================================================
# Tests for the conditional display logic
# ============================================================================


class TestScannedIndicatorConditionalDisplay:
    """Verify that the scanned indicator is shown only for SCANNED PDFs.

    These tests replicate the conditional logic from ``chat/src/ui.py``
    (lines 85-95) as an isolated helper, avoiding the need to import
    ``ui.py`` (which would pull in ``auth_guard`` and its ``supabase``
    dependency).  All external calls (``st.markdown``, ``detect_pdf_type``)
    are mocked.
    """

    @staticmethod
    def _make_mock_uploaded_file(
        name: str = "test.pdf",
        file_type: str = "application/pdf",
        content: bytes = b"%PDF-1.4 mock content",
    ) -> MagicMock:
        """Create a mock Streamlit ``UploadedFile`` with the given attributes."""
        f = MagicMock()
        f.name = name
        f.type = file_type
        f.size = len(content)
        f.getvalue.return_value = content
        f.seek.return_value = None
        return f

    # ── The isolated logic under test ─────────────────────────────────────

    @staticmethod
    def _run_display_logic(
        uploaded_file: MagicMock,
        pdf_type: PDFType,
        mock_markdown: MagicMock,
        mock_detect: MagicMock,
    ) -> None:
        """Replicate the indicator-display logic from ``ui.py`` lines 85-95.

        This is the exact conditional block that decides whether to render
        the scanned indicator, extracted so we can test it without importing
        the full ``ui`` module.  Includes the try/except wrapper that exists
        in the real ``ui.py`` code.
        """
        if (
            uploaded_file.type == "application/pdf"
            or uploaded_file.name.lower().endswith(".pdf")
        ):
            try:
                uploaded_file.seek(0)
                detected = mock_detect(uploaded_file, filename=uploaded_file.name)
                uploaded_file.seek(0)

                if detected == PDFType.SCANNED:
                    mock_markdown(render_scanned_indicator(), unsafe_allow_html=True)
            except Exception:
                pass

    # ── Tests ─────────────────────────────────────────────────────────────

    def test_indicator_rendered_for_scanned(self) -> None:
        """The indicator MUST be rendered when the PDF is classified as SCANNED."""
        uploaded_file = self._make_mock_uploaded_file()
        mock_markdown = MagicMock()
        mock_detect = MagicMock(return_value=PDFType.SCANNED)

        self._run_display_logic(
            uploaded_file, PDFType.SCANNED, mock_markdown, mock_detect
        )

        mock_markdown.assert_called_once()
        call_args, call_kwargs = mock_markdown.call_args
        assert "scanned-indicator" in call_args[0]
        assert call_kwargs.get("unsafe_allow_html") is True

    def test_indicator_not_rendered_for_digital(self) -> None:
        """The indicator MUST NOT be rendered when the PDF is DIGITAL."""
        uploaded_file = self._make_mock_uploaded_file()
        mock_markdown = MagicMock()
        mock_detect = MagicMock(return_value=PDFType.DIGITAL)

        self._run_display_logic(
            uploaded_file, PDFType.DIGITAL, mock_markdown, mock_detect
        )

        mock_markdown.assert_not_called()

    def test_indicator_not_rendered_for_hybrid(self) -> None:
        """The indicator MUST NOT be rendered when the PDF is HYBRID."""
        uploaded_file = self._make_mock_uploaded_file()
        mock_markdown = MagicMock()
        mock_detect = MagicMock(return_value=PDFType.HYBRID)

        self._run_display_logic(
            uploaded_file, PDFType.HYBRID, mock_markdown, mock_detect
        )

        mock_markdown.assert_not_called()

    def test_indicator_not_rendered_for_unknown(self) -> None:
        """The indicator MUST NOT be rendered when the PDF is UNKNOWN."""
        uploaded_file = self._make_mock_uploaded_file()
        mock_markdown = MagicMock()
        mock_detect = MagicMock(return_value=PDFType.UNKNOWN)

        self._run_display_logic(
            uploaded_file, PDFType.UNKNOWN, mock_markdown, mock_detect
        )

        mock_markdown.assert_not_called()

    def test_detect_pdf_type_called_with_uploaded_file(self) -> None:
        """``detect_pdf_type`` must be invoked with the uploaded file and filename."""
        uploaded_file = self._make_mock_uploaded_file()
        mock_markdown = MagicMock()
        mock_detect = MagicMock(return_value=PDFType.DIGITAL)

        self._run_display_logic(
            uploaded_file, PDFType.DIGITAL, mock_markdown, mock_detect
        )

        mock_detect.assert_called_once_with(uploaded_file, filename=uploaded_file.name)

    def test_indicator_not_rendered_for_non_pdf_files(self) -> None:
        """The indicator MUST NOT be rendered for non-PDF file types."""
        uploaded_file = self._make_mock_uploaded_file(
            name="document.txt", file_type="text/plain"
        )
        mock_markdown = MagicMock()
        mock_detect = MagicMock(return_value=PDFType.SCANNED)

        self._run_display_logic(
            uploaded_file, PDFType.SCANNED, mock_markdown, mock_detect
        )

        # detect_pdf_type should not even be called for non-PDF files
        mock_detect.assert_not_called()
        mock_markdown.assert_not_called()

    def test_indicator_rendered_for_pdf_without_mime_type(self) -> None:
        """The indicator must work when the MIME type is missing but the extension
        is .pdf."""
        uploaded_file = self._make_mock_uploaded_file(name="report.pdf", file_type="")
        mock_markdown = MagicMock()
        mock_detect = MagicMock(return_value=PDFType.SCANNED)

        self._run_display_logic(
            uploaded_file, PDFType.SCANNED, mock_markdown, mock_detect
        )

        mock_markdown.assert_called_once()
        call_args, call_kwargs = mock_markdown.call_args
        assert "scanned-indicator" in call_args[0]

    def test_detect_pdf_type_failure_does_not_crash(self) -> None:
        """If ``detect_pdf_type`` raises an exception, the UI must not crash."""
        uploaded_file = self._make_mock_uploaded_file()
        mock_markdown = MagicMock()
        mock_detect = MagicMock(side_effect=RuntimeError("Unexpected error"))

        # This should not raise — the helper includes the try/except wrapper
        self._run_display_logic(
            uploaded_file, PDFType.SCANNED, mock_markdown, mock_detect
        )

        # markdown should NOT have been called (the exception was caught)
        mock_markdown.assert_not_called()

    def test_file_seek_called_before_and_after_detection(self) -> None:
        """The uploaded file must be rewound before and after detection."""
        uploaded_file = self._make_mock_uploaded_file()
        mock_markdown = MagicMock()
        mock_detect = MagicMock(return_value=PDFType.DIGITAL)

        self._run_display_logic(
            uploaded_file, PDFType.DIGITAL, mock_markdown, mock_detect
        )

        # seek(0) should have been called twice (before and after detection)
        assert uploaded_file.seek.call_count == 2
        uploaded_file.seek.assert_any_call(0)
