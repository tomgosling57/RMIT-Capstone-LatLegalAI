"""
Tests for ``parser_tools.parse_document()`` language detection integration.

Verifies that language detection, explicit language forwarding, and
backward compatibility work correctly when parsing documents through
the high-level ``parse_document()`` API.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.ocr_pdf_parser import OCRPDFParser
from src.tools.pdf_parser import PDFParser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_pdf_path(tmp_path: Path) -> Path:
    """Return a temporary PDF file path (file is created on disk)."""
    p = tmp_path / "test.pdf"
    p.write_text("%PDF-1.4 mock")
    return p


@pytest.fixture
def temp_txt_path(tmp_path: Path) -> Path:
    """Return a temporary text file path (file is created on disk)."""
    p = tmp_path / "test.txt"
    p.write_text("Hello world")
    return p


# ============================================================================
# Test parse_document language integration
# ============================================================================


class TestParseDocumentLanguageIntegration:
    """Tests for language detection/forwarding in ``parse_document()``."""

    # ------------------------------------------------------------------
    # Helper: build a mock factory that returns a given parser
    # ------------------------------------------------------------------

    def _make_mock_factory(self, parser: MagicMock) -> MagicMock:
        factory = MagicMock()
        factory.get_parser.return_value = parser
        return factory

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    @patch("src.tools.parser_tools.DocumentParserFactory")
    async def test_auto_detects_language_when_not_provided(
        self,
        mock_factory_cls: MagicMock,
        temp_pdf_path: Path,
    ) -> None:
        """When ``lang`` is not provided, language is auto-detected from a sample."""
        from src.tools.parser_tools import parse_document

        mock_parser = MagicMock(spec=OCRPDFParser)
        mock_parser.parse = AsyncMock(return_value=["OCR extracted text"])
        mock_parser.resolve_lang.return_value = "hin"
        # Simulate the factory having stored the detected language on the parser
        mock_parser._detected_lang = "hin"

        mock_factory = self._make_mock_factory(mock_parser)
        mock_factory_cls.return_value = mock_factory

        result: Tuple[List[str], int, int, Optional[str]] = await parse_document(
            str(temp_pdf_path)
        )

        extracted_pages, page_count, char_count, detected_lang = result

        assert extracted_pages == ["OCR extracted text"]
        assert page_count == 1
        assert detected_lang == "hin"
        # Factory should have detect_lang=True (single detection in factory)
        assert mock_factory.get_parser.call_args[1].get("detect_lang") is True
        # Parser should have been called with the auto-detected language
        assert mock_parser.parse.call_args[1].get("lang") == "hin"

    @pytest.mark.asyncio
    @patch("src.tools.parser_tools.DocumentParserFactory")
    async def test_explicit_lang_overrides_auto_detection(
        self,
        mock_factory_cls: MagicMock,
        temp_pdf_path: Path,
    ) -> None:
        """When ``lang`` is explicitly provided, it overrides auto-detection."""
        from src.tools.parser_tools import parse_document

        mock_parser = MagicMock(spec=OCRPDFParser)
        mock_parser.parse = AsyncMock(return_value=["French OCR text"])

        mock_factory = self._make_mock_factory(mock_parser)
        mock_factory_cls.return_value = mock_factory

        result: Tuple[List[str], int, int, Optional[str]] = await parse_document(
            str(temp_pdf_path), ocr_language="fra"
        )

        extracted_pages, page_count, char_count, detected_lang = result

        assert extracted_pages == ["French OCR text"]
        assert detected_lang == "fra"
        # Factory should have been called with detect_lang=True
        assert mock_factory.get_parser.call_args[1].get("detect_lang") is True
        # Parser should have been called with the explicit language
        assert mock_parser.parse.call_args[1].get("lang") == "fra"

    @pytest.mark.asyncio
    @patch("src.tools.parser_tools.DocumentParserFactory")
    async def test_non_ocr_parser_returns_none_lang(
        self,
        mock_factory_cls: MagicMock,
        temp_pdf_path: Path,
    ) -> None:
        """Non-OCR parsers return ``None`` for detected_lang."""
        from src.tools.parser_tools import parse_document

        mock_parser = MagicMock(spec=PDFParser)
        mock_parser.parse = AsyncMock(return_value=["Digital PDF text"])

        mock_factory = self._make_mock_factory(mock_parser)
        mock_factory_cls.return_value = mock_factory

        result: Tuple[List[str], int, int, Optional[str]] = await parse_document(
            str(temp_pdf_path)
        )

        extracted_pages, page_count, char_count, detected_lang = result

        assert extracted_pages == ["Digital PDF text"]
        assert detected_lang is None
        # Non-OCR parser should be called WITHOUT lang keyword
        assert "lang" not in mock_parser.parse.call_args[1]

    @pytest.mark.asyncio
    @patch("src.tools.parser_tools.DocumentParserFactory")
    async def test_auto_detect_falls_back_to_english(
        self,
        mock_factory_cls: MagicMock,
        temp_pdf_path: Path,
    ) -> None:
        """When auto-detection returns ``None``, fall back to ``"eng"``."""
        from src.tools.parser_tools import parse_document

        mock_parser = MagicMock(spec=OCRPDFParser)
        mock_parser.parse = AsyncMock(return_value=["Fallback OCR text"])
        mock_parser.resolve_lang.return_value = "eng"
        # Detection fails — returns None
        mock_parser.detect_language_from_sample.return_value = None

        mock_factory = self._make_mock_factory(mock_parser)
        mock_factory_cls.return_value = mock_factory

        result: Tuple[List[str], int, int, Optional[str]] = await parse_document(
            str(temp_pdf_path)
        )

        extracted_pages, page_count, char_count, detected_lang = result

        assert extracted_pages == ["Fallback OCR text"]
        # When detection fails, detected_lang should be None (not "eng")
        # because the code only sets detected_lang when ocr_lang is truthy
        assert detected_lang is None
        # Parser should have been called with "eng" as the default
        assert mock_parser.parse.call_args[1].get("lang") == "eng"

    @pytest.mark.asyncio
    @patch("src.tools.parser_tools.DocumentParserFactory")
    async def test_backward_compatible_return_type(
        self,
        mock_factory_cls: MagicMock,
        temp_pdf_path: Path,
    ) -> None:
        """``parse_document()`` returns a 4-tuple for backward compatibility."""
        from src.tools.parser_tools import parse_document

        mock_parser = MagicMock(spec=OCRPDFParser)
        mock_parser.parse = AsyncMock(return_value=["Content"])
        mock_parser.resolve_lang.return_value = "eng"
        mock_parser.detect_language_from_sample.return_value = "eng"

        mock_factory = self._make_mock_factory(mock_parser)
        mock_factory_cls.return_value = mock_factory

        result = await parse_document(str(temp_pdf_path))

        # Verify it's a 4-tuple
        assert isinstance(result, tuple)
        assert len(result) == 4
        assert isinstance(result[0], list)
        assert isinstance(result[1], int)
        assert isinstance(result[2], int)
        assert result[3] is None or isinstance(result[3], str)


# ============================================================================
# Test parse_document language logging
# ============================================================================


class TestParseDocumentLanguageLogging:
    """Tests for logging behaviour in ``parse_document()`` language handling."""

    @pytest.mark.asyncio
    @patch("src.tools.parser_tools.DocumentParserFactory")
    async def test_logs_explicit_language(
        self,
        mock_factory_cls: MagicMock,
        temp_pdf_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When explicit lang is provided, a log message should be emitted."""
        from src.tools.parser_tools import parse_document

        mock_parser = MagicMock(spec=OCRPDFParser)
        mock_parser.parse = AsyncMock(return_value=["Content"])
        mock_parser.resolve_lang.return_value = "fra"

        mock_factory = MagicMock()
        mock_factory.get_parser.return_value = mock_parser
        mock_factory_cls.return_value = mock_factory

        with caplog.at_level(logging.INFO):
            await parse_document(str(temp_pdf_path), ocr_language="fra")

        assert any(
            "Using user-specified OCR language" in record.message
            for record in caplog.records
        ), "Expected log message about explicit language not found"

    @pytest.mark.asyncio
    @patch("src.tools.parser_tools.DocumentParserFactory")
    async def test_logs_auto_detected_language(
        self,
        mock_factory_cls: MagicMock,
        temp_pdf_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When language is auto-detected, a log message should be emitted."""
        from src.tools.parser_tools import parse_document

        mock_parser = MagicMock(spec=OCRPDFParser)
        mock_parser.parse = AsyncMock(return_value=["Content"])
        mock_parser.resolve_lang.return_value = "hin"
        # Simulate the factory having stored the detected language on the parser
        mock_parser._detected_lang = "hin"

        mock_factory = MagicMock()
        mock_factory.get_parser.return_value = mock_parser
        mock_factory_cls.return_value = mock_factory

        with caplog.at_level(logging.INFO):
            await parse_document(str(temp_pdf_path))

        assert any(
            "Using auto-detected OCR language" in record.message
            for record in caplog.records
        ), "Expected log message about auto-detected language not found"

    @pytest.mark.asyncio
    @patch("src.tools.parser_tools.DocumentParserFactory")
    async def test_logs_fallback_to_english(
        self,
        mock_factory_cls: MagicMock,
        temp_pdf_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When detection fails and falls back to English, a log should be emitted."""
        from src.tools.parser_tools import parse_document

        mock_parser = MagicMock(spec=OCRPDFParser)
        mock_parser.parse = AsyncMock(return_value=["Content"])
        mock_parser.resolve_lang.return_value = "eng"
        # No _detected_lang set — simulates factory detection returning None

        mock_factory = MagicMock()
        mock_factory.get_parser.return_value = mock_parser
        mock_factory_cls.return_value = mock_factory

        with caplog.at_level(logging.INFO):
            await parse_document(str(temp_pdf_path))

        assert any(
            "No language detected or specified, falling back to English"
            in record.message
            for record in caplog.records
        ), "Expected log message about fallback to English not found"
