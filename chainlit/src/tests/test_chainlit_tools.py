"""
Tests for Chainlit tool functions registered in ``tools/__init__.py``.

These tests verify that the ``@cl.tool``-decorated functions work correctly
with mocked file I/O and parser dependencies.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.pdf_type_detector import PDFType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Return minimal valid PDF bytes."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n"
        b"(Hello World) Tj\nET\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \n0000000241 00000 n \n"
        b"0000000349 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n429\n%%EOF\n"
    )


@pytest.fixture
def sample_docx_bytes() -> bytes:
    """Return minimal .docx-like bytes (not a real docx, just for testing)."""
    return b"PK\x03\x04" + b"\x00" * 100  # ZIP header (docx is a ZIP)


@pytest.fixture
def sample_txt_bytes() -> bytes:
    """Return plain text bytes."""
    return b"Hello, this is a text file.\nWith multiple lines."


# ============================================================================
# Test _parse_document helper
# ============================================================================


class TestParseDocumentHelper:
    """Tests for the internal ``_parse_document()`` helper."""

    @pytest.mark.asyncio
    @patch("src.tools.__init__.detect_pdf_type", return_value=PDFType.DIGITAL)
    @patch("src.tools.__init__.DocumentParserFactory")
    async def test_parse_document_pdf(
        self,
        mock_factory_cls: MagicMock,
        mock_detect: MagicMock,
        sample_pdf_bytes: bytes,
    ) -> None:
        """_parse_document should detect PDF type and parse a PDF file."""
        from src.tools.__init__ import _parse_document

        # Set up mock factory
        mock_parser = AsyncMock()
        mock_parser.parse.return_value = ["Page 1 content", "Page 2 content"]
        mock_factory = MagicMock()
        mock_factory.get_parser.return_value = mock_parser
        mock_factory_cls.return_value = mock_factory

        result = await _parse_document(sample_pdf_bytes, "test.pdf")

        assert "Page 1 content" in result
        assert "Page 2 content" in result
        mock_detect.assert_called_once()
        mock_factory.get_parser.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.tools.__init__.detect_pdf_type")
    @patch("src.tools.__init__.DocumentParserFactory")
    async def test_parse_document_non_pdf(
        self,
        mock_factory_cls: MagicMock,
        mock_detect: MagicMock,
        sample_txt_bytes: bytes,
    ) -> None:
        """_parse_document should skip PDF type detection for non-PDF files."""
        from src.tools.__init__ import _parse_document

        mock_parser = AsyncMock()
        mock_parser.parse.return_value = ["Text content"]
        mock_factory = MagicMock()
        mock_factory.get_parser.return_value = mock_parser
        mock_factory_cls.return_value = mock_factory

        result = await _parse_document(sample_txt_bytes, "test.txt")

        assert "Text content" in result
        # detect_pdf_type should NOT be called for non-PDF files
        mock_detect.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.tools.__init__.detect_pdf_type", return_value=PDFType.DIGITAL)
    @patch("src.tools.__init__.DocumentParserFactory")
    async def test_parse_document_cleans_up_temp_file(
        self,
        mock_factory_cls: MagicMock,
        mock_detect: MagicMock,
        sample_pdf_bytes: bytes,
    ) -> None:
        """_parse_document should clean up the temporary file after parsing."""
        from src.tools.__init__ import _parse_document

        mock_parser = AsyncMock()
        mock_parser.parse.return_value = ["Content"]
        mock_factory = MagicMock()
        mock_factory.get_parser.return_value = mock_parser
        mock_factory_cls.return_value = mock_factory

        # Track temp files created
        temp_files_before = set(Path(tempfile.gettempdir()).iterdir())

        await _parse_document(sample_pdf_bytes, "test.pdf")

        temp_files_after = set(Path(tempfile.gettempdir()).iterdir())
        new_files = temp_files_after - temp_files_before
        # Filter out non-temp files that may exist
        temp_new = {f for f in new_files if f.name.startswith("tmp")}
        assert len(temp_new) == 0, f"Temporary file not cleaned up: {temp_new}"

    @pytest.mark.asyncio
    @patch("src.tools.__init__.detect_pdf_type", return_value=PDFType.SCANNED)
    @patch("src.tools.__init__.DocumentParserFactory")
    async def test_parse_document_pdf_with_lang(
        self,
        mock_factory_cls: MagicMock,
        mock_detect: MagicMock,
        sample_pdf_bytes: bytes,
    ) -> None:
        """_parse_document should forward lang to OCRPDFParser when provided."""
        from src.tools.__init__ import _parse_document
        from src.tools.ocr_pdf_parser import OCRPDFParser

        mock_parser = MagicMock(spec=OCRPDFParser)
        mock_parser.parse = AsyncMock(return_value=["OCR content"])
        mock_parser.resolve_lang.return_value = "fra"
        mock_factory = MagicMock()
        mock_factory.get_parser.return_value = mock_parser
        mock_factory_cls.return_value = mock_factory

        result = await _parse_document(sample_pdf_bytes, "test.pdf", lang="fra")

        assert "OCR content" in result
        # Verify detect_lang=False was passed to factory
        assert mock_factory.get_parser.call_args[1].get("detect_lang") is False
        # Verify parse was called with resolved language
        assert mock_parser.parse.call_args[1].get("lang") == "fra"

    @pytest.mark.asyncio
    @patch("src.tools.__init__.detect_pdf_type", return_value=PDFType.DIGITAL)
    @patch("src.tools.__init__.DocumentParserFactory")
    async def test_parse_document_without_lang_backward_compat(
        self,
        mock_factory_cls: MagicMock,
        mock_detect: MagicMock,
        sample_pdf_bytes: bytes,
    ) -> None:
        """_parse_document should work without lang (backward compat)."""
        from src.tools.__init__ import _parse_document

        mock_parser = AsyncMock()
        mock_parser.parse.return_value = ["Page content"]
        mock_factory = MagicMock()
        mock_factory.get_parser.return_value = mock_parser
        mock_factory_cls.return_value = mock_factory

        # Call without lang (backward compat — uses the 2-arg signature)
        result = await _parse_document(sample_pdf_bytes, "test.pdf")

        assert "Page content" in result
        mock_factory.get_parser.assert_called_once()


# ============================================================================
# Test parse_pdf tool
# ============================================================================


class TestParsePdfTool:
    """Tests for the ``parse_pdf`` Chainlit tool."""

    @pytest.mark.asyncio
    @patch("src.tools.__init__._parse_document")
    async def test_parse_pdf_delegates_to_helper(
        self, mock_parse: AsyncMock, sample_pdf_bytes: bytes
    ) -> None:
        """parse_pdf should delegate to _parse_document."""
        from src.tools.__init__ import parse_pdf

        mock_parse.return_value = "Extracted PDF text"

        result = await parse_pdf(sample_pdf_bytes, "test.pdf")

        assert result == "Extracted PDF text"
        mock_parse.assert_called_once_with(sample_pdf_bytes, "test.pdf")


# ============================================================================
# Test parse_word_document tool
# ============================================================================


class TestParseWordDocumentTool:
    """Tests for the ``parse_word_document`` Chainlit tool."""

    @pytest.mark.asyncio
    @patch("src.tools.__init__._parse_document")
    async def test_parse_word_delegates_to_helper(
        self, mock_parse: AsyncMock, sample_docx_bytes: bytes
    ) -> None:
        """parse_word_document should delegate to _parse_document."""
        from src.tools.__init__ import parse_word_document

        mock_parse.return_value = "Extracted Word text"

        result = await parse_word_document(sample_docx_bytes, "test.docx")

        assert result == "Extracted Word text"
        mock_parse.assert_called_once_with(sample_docx_bytes, "test.docx")


# ============================================================================
# Test parse_text_file tool
# ============================================================================


class TestParseTextFileTool:
    """Tests for the ``parse_text_file`` Chainlit tool."""

    @pytest.mark.asyncio
    @patch("src.tools.__init__._parse_document")
    async def test_parse_text_delegates_to_helper(
        self, mock_parse: AsyncMock, sample_txt_bytes: bytes
    ) -> None:
        """parse_text_file should delegate to _parse_document."""
        from src.tools.__init__ import parse_text_file

        mock_parse.return_value = "Extracted text content"

        result = await parse_text_file(sample_txt_bytes, "test.txt")

        assert result == "Extracted text content"
        mock_parse.assert_called_once_with(sample_txt_bytes, "test.txt")


# ============================================================================
# Test detect_pdf_format tool
# ============================================================================


class TestDetectPdfFormatTool:
    """Tests for the ``detect_pdf_format`` Chainlit tool."""

    @pytest.mark.asyncio
    @patch("src.tools.__init__.detect_pdf_type", return_value=PDFType.DIGITAL)
    async def test_detect_pdf_format_digital(
        self, mock_detect: MagicMock, sample_pdf_bytes: bytes
    ) -> None:
        """detect_pdf_format should return the correct PDF type string."""
        from src.tools.__init__ import detect_pdf_format

        result = await detect_pdf_format(sample_pdf_bytes, "test.pdf")

        assert result == "PDF Type: digital"
        mock_detect.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.tools.__init__.detect_pdf_type", return_value=PDFType.SCANNED)
    async def test_detect_pdf_format_scanned(
        self, mock_detect: MagicMock, sample_pdf_bytes: bytes
    ) -> None:
        """detect_pdf_format should return 'scanned' for scanned PDFs."""
        from src.tools.__init__ import detect_pdf_format

        result = await detect_pdf_format(sample_pdf_bytes, "test.pdf")

        assert result == "PDF Type: scanned"

    @pytest.mark.asyncio
    @patch("src.tools.__init__.detect_pdf_type", return_value=PDFType.HYBRID)
    async def test_detect_pdf_format_hybrid(
        self, mock_detect: MagicMock, sample_pdf_bytes: bytes
    ) -> None:
        """detect_pdf_format should return 'hybrid' for hybrid PDFs."""
        from src.tools.__init__ import detect_pdf_format

        result = await detect_pdf_format(sample_pdf_bytes, "test.pdf")

        assert result == "PDF Type: hybrid"

    @pytest.mark.asyncio
    @patch("src.tools.__init__.detect_pdf_type", return_value=PDFType.UNKNOWN)
    async def test_detect_pdf_format_unknown(
        self, mock_detect: MagicMock, sample_pdf_bytes: bytes
    ) -> None:
        """detect_pdf_format should return 'unknown' for unclassifiable PDFs."""
        from src.tools.__init__ import detect_pdf_format

        result = await detect_pdf_format(sample_pdf_bytes, "test.pdf")

        assert result == "PDF Type: unknown"


# ============================================================================
# Test get_pdf_metadata tool
# ============================================================================


class TestGetPdfMetadataTool:
    """Tests for the ``get_pdf_metadata`` Chainlit tool."""

    @pytest.mark.asyncio
    @patch("src.tools.__init__.PDFParser")
    async def test_get_pdf_metadata_returns_formatted_string(
        self, mock_parser_cls: MagicMock, sample_pdf_bytes: bytes
    ) -> None:
        """get_pdf_metadata should return a formatted metadata string."""
        from src.tools.__init__ import get_pdf_metadata

        mock_parser = AsyncMock()
        mock_parser.get_metadata_async.return_value = {
            "title": "Test Document",
            "author": "John Doe",
            "subject": "Testing",
            "pages": 5,
            "creation_date": "2024-01-15",
            "modification_date": "2024-01-20",
            "producer": "Test Producer",
            "creator": "Test Creator",
        }
        mock_parser_cls.return_value = mock_parser

        result = await get_pdf_metadata(sample_pdf_bytes, "test.pdf")

        assert "**Title:** Test Document" in result
        assert "**Author:** John Doe" in result
        assert "**Pages:** 5" in result
        assert "**Created:** 2024-01-15" in result
        mock_parser.get_metadata_async.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.tools.__init__.PDFParser")
    async def test_get_pdf_metadata_handles_missing_fields(
        self, mock_parser_cls: MagicMock, sample_pdf_bytes: bytes
    ) -> None:
        """get_pdf_metadata should handle missing metadata fields gracefully."""
        from src.tools.__init__ import get_pdf_metadata

        mock_parser = AsyncMock()
        mock_parser.get_metadata_async.return_value = {
            "title": "Untitled",
            "pages": 1,
        }
        mock_parser_cls.return_value = mock_parser

        result = await get_pdf_metadata(sample_pdf_bytes, "test.pdf")

        assert "**Title:** Untitled" in result
        assert "**Author:** Unknown" in result  # Missing field defaults
        assert "**Pages:** 1" in result


# ============================================================================
# Test parse_document_auto tool
# ============================================================================


class TestParseDocumentAutoTool:
    """Tests for the ``parse_document_auto`` Chainlit tool."""

    @pytest.mark.asyncio
    @patch("src.tools.__init__._parse_document")
    async def test_parse_document_auto_delegates_to_helper(
        self, mock_parse: AsyncMock, sample_pdf_bytes: bytes
    ) -> None:
        """parse_document_auto should delegate to _parse_document."""
        from src.tools.__init__ import parse_document_auto

        mock_parse.return_value = "Auto-parsed content"

        result = await parse_document_auto(sample_pdf_bytes, "test.pdf")

        assert result == "Auto-parsed content"
        mock_parse.assert_called_once_with(sample_pdf_bytes, "test.pdf")


# ============================================================================
# Test file_validation tool
# ============================================================================


class TestFileValidationTool:
    """Tests for the ``validate_file_type`` Chainlit tool."""

    @pytest.mark.asyncio
    async def test_validate_file_type_valid(
        self,
        sample_pdf_bytes: bytes,
    ) -> None:
        """validate_file_type should return success for matching types."""
        from unittest.mock import patch
        from src.tools.file_validation import validate_file_type

        with (
            patch("src.tools.file_validation.detect_file_type_bytes") as mock_detect,
            patch("src.tools.file_validation.extension_matches") as mock_ext_matches,
        ):
            mock_detect.return_value = "pdf"
            mock_ext_matches.return_value = True

            result = await validate_file_type(sample_pdf_bytes, "document.pdf")

            assert "Valid PDF file" in result

    @pytest.mark.asyncio
    async def test_validate_file_type_mismatch(
        self,
        sample_pdf_bytes: bytes,
    ) -> None:
        """validate_file_type should report type mismatch."""
        from unittest.mock import patch
        from src.tools.file_validation import validate_file_type

        with (
            patch("src.tools.file_validation.detect_file_type_bytes") as mock_detect,
            patch("src.tools.file_validation.extension_matches") as mock_ext_matches,
        ):
            mock_detect.return_value = "pdf"
            mock_ext_matches.return_value = False

            result = await validate_file_type(sample_pdf_bytes, "document.txt")

            assert "Type mismatch" in result

    @pytest.mark.asyncio
    async def test_validate_file_type_unsupported(
        self,
        sample_pdf_bytes: bytes,
    ) -> None:
        """validate_file_type should report unsupported types."""
        from unittest.mock import patch
        from src.tools.file_validation import validate_file_type

        with patch("src.tools.file_validation.detect_file_type_bytes") as mock_detect:
            mock_detect.return_value = None

            result = await validate_file_type(sample_pdf_bytes, "unknown.xyz")

            assert "Unsupported" in result or "unrecognised" in result
