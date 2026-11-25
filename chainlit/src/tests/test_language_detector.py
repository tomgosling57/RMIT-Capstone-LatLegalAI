"""
Unit tests for language detection utility (migrated from backend).

Tests the language detection functionality used for OCR document processing,
including the ``UnsupportedLanguageError`` exception and factory integration.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.tools.language_detector import (
    TESSERACT_LANGUAGE_MAP,
    SUPPORTED_TESSERACT_LANGUAGES,
    UnsupportedLanguageError,
    detect_language,
    is_language_supported,
    get_supported_languages,
)

# ===========================================================================
# TestDetectLanguage
# ===========================================================================


class TestDetectLanguage:
    """Tests for the :func:`detect_language` function."""

    def test_detect_english(self) -> None:
        """Test detection of English text."""
        text = (
            "The quick brown fox jumps over the lazy dog. "
            "This is a sample English text for language detection."
        )
        result = detect_language(text)
        assert result == "eng", f"Expected 'eng', got {result}"

    def test_detect_french(self) -> None:
        """Test detection of French text."""
        text = (
            "Bonjour, ceci est un texte en français. "
            "La détection de langue est très importante pour le traitement OCR."
        )
        result = detect_language(text)
        assert result == "fra", f"Expected 'fra', got {result}"

    def test_detect_spanish(self) -> None:
        """Test detection of Spanish text."""
        text = (
            "Hola, este es un texto en español. "
            "La detección de idioma es importante para el procesamiento OCR."
        )
        result = detect_language(text)
        assert result == "spa", f"Expected 'spa', got {result}"

    def test_detect_german(self) -> None:
        """Test detection of German text."""
        text = (
            "Hallo, dies ist ein deutscher Text. "
            "Die Spracherkennung ist wichtig für die OCR-Verarbeitung."
        )
        result = detect_language(text)
        assert result == "deu", f"Expected 'deu', got {result}"

    def test_detect_hindi(self) -> None:
        """Test detection of Hindi text."""
        text = "नमस्ते, यह एक हिंदी पाठ है। " "भाषा पहचान"  # noqa: E501
        result = detect_language(text)
        assert result == "hin", f"Expected 'hin', got {result}"

    def test_detect_portuguese(self) -> None:
        """Test detection of Portuguese text."""
        text = (
            "Olá, este é um texto em português. "
            "A detecção de idioma é importante para o processamento OCR."
        )
        result = detect_language(text)
        assert result == "por", f"Expected 'por', got {result}"

    def test_empty_text_raises_error(self) -> None:
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            detect_language("")

    def test_whitespace_only_raises_error(self) -> None:
        """Test that whitespace-only text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            detect_language("   \n\t  ")

    def test_very_short_text_returns_none(self) -> None:
        """Test that very short text may return None due to low confidence."""
        text = "a"
        result = detect_language(text)
        assert result is None or isinstance(result, str)

    def test_confidence_threshold(self) -> None:
        """Test that confidence threshold is respected."""
        text = (
            "The quick brown fox jumps over the lazy dog. "
            "This is a sample English text for language detection."
        )
        result_low = detect_language(text, confidence_threshold=0.1)
        result_high = detect_language(text, confidence_threshold=0.95)

        assert result_low is not None, "Low threshold should detect language"
        assert result_high is None or isinstance(
            result_high, str
        ), "High threshold may or may not detect depending on confidence"

    def test_mixed_language_text(self) -> None:
        """Test detection of mixed language text (should detect dominant language)."""
        text = (
            "Hello world. This is English text. "
            "Bonjour le monde. Ceci est du texte français."
        )
        result = detect_language(text)
        assert result in ["eng", "fra"], f"Expected 'eng' or 'fra', got {result}"


# ===========================================================================
# TestIsLanguageSupported
# ===========================================================================


class TestIsLanguageSupported:
    """Tests for the :func:`is_language_supported` function."""

    def test_supported_languages(self) -> None:
        """Test that known supported languages return True."""
        supported = ["eng", "fra", "spa", "deu", "hin", "por"]
        for lang in supported:
            assert is_language_supported(lang), f"Language {lang} should be supported"

    def test_unsupported_language(self) -> None:
        """Test that unsupported language returns False."""
        assert not is_language_supported(
            "xyz"
        ), "Unsupported language should return False"

    def test_all_tesseract_codes_supported(self) -> None:
        """Test that all Tesseract codes in the map are in the supported set."""
        for code in TESSERACT_LANGUAGE_MAP.values():
            assert is_language_supported(
                code
            ), f"Tesseract code {code} should be supported"


# ===========================================================================
# TestGetSupportedLanguages
# ===========================================================================


class TestGetSupportedLanguages:
    """Tests for the :func:`get_supported_languages` function."""

    def test_returns_list(self) -> None:
        """Test that function returns a list."""
        result = get_supported_languages()
        assert isinstance(result, list), "Should return a list"

    def test_returns_sorted_list(self) -> None:
        """Test that returned list is sorted."""
        result = get_supported_languages()
        assert result == sorted(result), "List should be sorted"

    def test_contains_common_languages(self) -> None:
        """Test that common languages are in the list."""
        result = get_supported_languages()
        common = ["eng", "fra", "spa", "deu", "hin"]
        for lang in common:
            assert lang in result, f"Language {lang} should be in supported list"

    def test_matches_supported_set(self) -> None:
        """Test that returned list matches the supported set."""
        result = get_supported_languages()
        assert set(result) == SUPPORTED_TESSERACT_LANGUAGES


# ===========================================================================
# TestLanguageMap
# ===========================================================================


class TestLanguageMap:
    """Tests for the language mapping constants."""

    def test_tesseract_language_map_not_empty(self) -> None:
        """Test that the language map is not empty."""
        assert len(TESSERACT_LANGUAGE_MAP) > 0, "Language map should not be empty"

    def test_supported_set_not_empty(self) -> None:
        """Test that supported languages set is not empty."""
        assert (
            len(SUPPORTED_TESSERACT_LANGUAGES) > 0
        ), "Supported languages should not be empty"

    def test_map_values_in_supported_set(self) -> None:
        """Test that all map values are in the supported set."""
        for code in TESSERACT_LANGUAGE_MAP.values():
            assert (
                code in SUPPORTED_TESSERACT_LANGUAGES
            ), f"Language code {code} should be in supported set"

    def test_common_codes_present(self) -> None:
        """Test that common language codes are in the map."""
        common_codes = ["eng", "fra", "spa", "deu", "hin"]
        for code in common_codes:
            assert (
                code in TESSERACT_LANGUAGE_MAP.values()
            ), f"Language code {code} should be in the map"


# ===========================================================================
# TestUnsupportedLanguageError
# ===========================================================================


class TestUnsupportedLanguageError:
    """Tests for the :class:`UnsupportedLanguageError` exception."""

    def test_error_message_format(self) -> None:
        """Test that the error message includes detected language and supported list."""
        supported = ["eng", "fra", "spa"]
        err = UnsupportedLanguageError(
            detected_language="xyz",
            supported_languages=supported,
        )
        assert "xyz" in str(err), "Error message should contain detected language"
        assert "eng" in str(err), "Error message should contain supported languages"
        assert "fra" in str(err), "Error message should contain supported languages"

    def test_error_code_value(self) -> None:
        """Test that ``error_code`` is ``\"UNSUPPORTED_LANGUAGE\"``."""
        err = UnsupportedLanguageError()
        assert err.error_code == "UNSUPPORTED_LANGUAGE"

    def test_to_dict_structure(self) -> None:
        """Test that ``to_dict()`` returns the expected structure."""
        err = UnsupportedLanguageError(
            detected_language="xyz",
            supported_languages=["eng", "fra"],
        )
        result = err.to_dict()

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["code"] == "UNSUPPORTED_LANGUAGE"
        assert isinstance(result["error"]["message"], str)
        assert isinstance(result["error"]["details"], dict)

    def test_with_details(self) -> None:
        """Test that a details dict is included in the error."""
        details = {"file": "/path/to/doc.pdf", "detected_language": "xyz"}
        err = UnsupportedLanguageError(
            detected_language="xyz",
            details=details,
        )
        assert err.details["file"] == "/path/to/doc.pdf"
        assert err.details["detected_language"] == "xyz"

        result = err.to_dict()
        assert result["error"]["details"]["file"] == "/path/to/doc.pdf"

    def test_default_message(self) -> None:
        """Test that a default message is used when not provided."""
        err = UnsupportedLanguageError()
        assert err.message is not None
        assert isinstance(err.message, str)
        assert len(err.message) > 0


# ===========================================================================
# TestFactoryLanguageValidation
# ===========================================================================


class TestFactoryLanguageValidation:
    """Integration tests for language validation in :class:`DocumentParserFactory`."""

    @pytest.fixture
    def pdf_path(self, tmp_path: Path) -> Path:
        """Return a temporary ``.pdf`` file path (file is not created on disk)."""
        return tmp_path / "test.pdf"

    def test_detect_lang_true_triggers_validation(self, pdf_path: Path) -> None:
        """
        When ``detect_lang=True``, ``get_parser()`` calls
        ``_validate_ocr_language`` for scanned PDFs.
        """
        from src.tools.parser_factory import DocumentParserFactory
        from src.tools.pdf_type_detector import PDFType

        with (
            patch(
                "src.tools.parser_factory.detect_pdf_type",
                return_value=PDFType.SCANNED,
            ),
            patch.object(
                DocumentParserFactory, "_validate_ocr_language"
            ) as mock_validate,
        ):
            factory = DocumentParserFactory()
            factory.get_parser(pdf_path, detect_lang=True)

        mock_validate.assert_called_once()

    def test_detect_lang_false_skips_validation(self, pdf_path: Path) -> None:
        """
        When ``detect_lang=False``, ``get_parser()`` skips
        ``_validate_ocr_language`` for scanned PDFs.
        """
        from src.tools.parser_factory import DocumentParserFactory
        from src.tools.pdf_type_detector import PDFType

        with (
            patch(
                "src.tools.parser_factory.detect_pdf_type",
                return_value=PDFType.SCANNED,
            ),
            patch.object(
                DocumentParserFactory, "_validate_ocr_language"
            ) as mock_validate,
        ):
            factory = DocumentParserFactory()
            factory.get_parser(pdf_path, detect_lang=False)

        mock_validate.assert_not_called()

    def test_validate_ocr_language_raises_on_unsupported(self, pdf_path: Path) -> None:
        """
        ``_validate_ocr_language`` raises ``UnsupportedLanguageError``
        when the detected language is not supported.
        """
        from src.tools.parser_factory import DocumentParserFactory

        factory = DocumentParserFactory()

        with patch(
            "src.tools.parser_factory.OCRPDFParser.detect_language_from_sample",
            return_value="xyz",
        ):
            with pytest.raises(UnsupportedLanguageError) as excinfo:
                factory._validate_ocr_language(pdf_path)

        assert excinfo.value.error_code == "UNSUPPORTED_LANGUAGE"
        assert "xyz" in str(excinfo.value)

    def test_validate_ocr_language_passes_for_supported(self, pdf_path: Path) -> None:
        """
        ``_validate_ocr_language`` does not raise when the detected language
        is supported.
        """
        from src.tools.parser_factory import DocumentParserFactory

        factory = DocumentParserFactory()

        with patch(
            "src.tools.parser_factory.OCRPDFParser.detect_language_from_sample",
            return_value="eng",
        ):
            # Should not raise
            factory._validate_ocr_language(pdf_path)

    def test_validate_ocr_language_handles_none_detection(self, pdf_path: Path) -> None:
        """
        ``_validate_ocr_language`` does not raise when language detection
        returns ``None`` (e.g., low confidence).
        """
        from src.tools.parser_factory import DocumentParserFactory

        factory = DocumentParserFactory()

        with patch(
            "src.tools.parser_factory.OCRPDFParser.detect_language_from_sample",
            return_value=None,
        ):
            # Should not raise
            factory._validate_ocr_language(pdf_path)
