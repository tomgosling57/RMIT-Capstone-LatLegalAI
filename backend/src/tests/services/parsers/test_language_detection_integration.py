"""
Integration tests for language detection in parser factory.

Tests the integration of language detection with the DocumentParserFactory
and OCRPDFParser for scanned document processing.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from services.parsers.parser_factory import DocumentParserFactory
from services.parsers.ocr_pdf_parser import OCRPDFParser
from exceptions import UnsupportedLanguageError


class TestOCRPDFParserLanguageDetection:
    """Tests for language detection in OCRPDFParser."""

    def test_detect_language_from_sample_returns_none_on_empty_text(self) -> None:
        """Test that language detection returns None when no text is extracted."""
        parser = OCRPDFParser()

        with patch.object(parser, "_pdf_to_images", return_value=[]):
            result = parser._detect_language_from_sample(Path("test.pdf"))
            assert result is None

    def test_detect_language_from_sample_handles_exceptions(self) -> None:
        """Test that language detection gracefully handles exceptions."""
        parser = OCRPDFParser()

        with patch.object(
            parser, "_pdf_to_images", side_effect=Exception("Test error")
        ):
            result = parser._detect_language_from_sample(Path("test.pdf"))
            assert result is None

    def test_detect_language_from_sample_with_valid_text(self) -> None:
        """Test language detection with valid English text."""
        parser = OCRPDFParser()

        mock_image = MagicMock()
        with patch.object(parser, "_pdf_to_images", return_value=[mock_image]):
            with patch.object(parser, "_preprocess", return_value=mock_image):
                with patch("pytesseract.image_to_string", return_value="Hello world"):
                    result = parser._detect_language_from_sample(Path("test.pdf"))
                    assert result == "eng"


class TestDocumentParserFactoryLanguageValidation:
    """Tests for language validation in DocumentParserFactory."""

    def test_get_parser_with_detect_lang_false(self) -> None:
        """Test that language detection is skipped when detect_lang=False."""
        factory = DocumentParserFactory()

        with patch("services.parsers.parser_factory.detect_pdf_type") as mock_detect:
            from services.parsers.pdf_type_detector import PDFType

            mock_detect.return_value = PDFType.SCANNED

            with patch.object(factory, "_validate_ocr_language") as mock_validate:
                parser = factory.get_parser(Path("test.pdf"), detect_lang=False)

                assert isinstance(parser, OCRPDFParser)
                mock_validate.assert_not_called()

    def test_get_parser_with_detect_lang_true(self) -> None:
        """Test that language validation is called when detect_lang=True."""
        factory = DocumentParserFactory()

        with patch("services.parsers.parser_factory.detect_pdf_type") as mock_detect:
            from services.parsers.pdf_type_detector import PDFType

            mock_detect.return_value = PDFType.SCANNED

            with patch.object(factory, "_validate_ocr_language") as mock_validate:
                parser = factory.get_parser(Path("test.pdf"), detect_lang=True)

                assert isinstance(parser, OCRPDFParser)
                mock_validate.assert_called_once()

    def test_validate_ocr_language_raises_on_unsupported(self) -> None:
        """Test that UnsupportedLanguageError is raised for unsupported languages."""
        factory = DocumentParserFactory()

        with patch.object(
            OCRPDFParser, "_detect_language_from_sample", return_value="xyz"
        ):
            with patch(
                "services.parsers.parser_factory.is_language_supported",
                return_value=False,
            ):
                with patch(
                    "services.parsers.parser_factory.get_supported_languages",
                    return_value=["eng", "fra"],
                ):
                    with pytest.raises(UnsupportedLanguageError) as exc_info:
                        factory._validate_ocr_language(Path("test.pdf"))

                    assert exc_info.value.error_code == "UNSUPPORTED_LANGUAGE"
                    assert "xyz" in str(exc_info.value)

    def test_validate_ocr_language_passes_for_supported(self) -> None:
        """Test that validation passes for supported languages."""
        factory = DocumentParserFactory()

        with patch.object(
            OCRPDFParser, "_detect_language_from_sample", return_value="eng"
        ):
            with patch(
                "services.parsers.parser_factory.is_language_supported",
                return_value=True,
            ):
                factory._validate_ocr_language(Path("test.pdf"))

    def test_validate_ocr_language_handles_none_detection(self) -> None:
        """Test that validation handles None detection gracefully."""
        factory = DocumentParserFactory()

        with patch.object(
            OCRPDFParser, "_detect_language_from_sample", return_value=None
        ):
            factory._validate_ocr_language(Path("test.pdf"))


class TestUnsupportedLanguageError:
    """Tests for the UnsupportedLanguageError exception."""

    def test_error_initialization(self) -> None:
        """Test that error is initialized correctly."""
        error = UnsupportedLanguageError(
            detected_language="xyz",
            supported_languages=["eng", "fra"],
        )

        assert error.error_code == "UNSUPPORTED_LANGUAGE"
        assert error.status_code == 400
        assert "xyz" in error.message

    def test_error_to_dict(self) -> None:
        """Test that error converts to dict correctly."""
        error = UnsupportedLanguageError(
            detected_language="xyz",
            supported_languages=["eng", "fra"],
        )

        error_dict = error.to_dict()
        assert error_dict["success"] is False
        assert error_dict["error"]["code"] == "UNSUPPORTED_LANGUAGE"
        assert "xyz" in error_dict["error"]["message"]

    def test_error_with_details(self) -> None:
        """Test that error includes details."""
        error = UnsupportedLanguageError(
            detected_language="xyz",
            supported_languages=["eng", "fra"],
            details={"file": "test.pdf"},
        )

        error_dict = error.to_dict()
        assert error_dict["error"]["details"]["file"] == "test.pdf"
