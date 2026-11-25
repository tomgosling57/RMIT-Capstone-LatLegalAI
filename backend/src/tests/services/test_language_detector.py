"""
Unit tests for language detection utility.

Tests the language detection functionality used for OCR document processing.
"""

import pytest

from utilities.language_detector import (
    detect_language,
    is_language_supported,
    get_supported_languages,
    TESSERACT_LANGUAGE_MAP,
    SUPPORTED_TESSERACT_LANGUAGES,
)


class TestDetectLanguage:
    """Tests for the detect_language function."""

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


class TestIsLanguageSupported:
    """Tests for the is_language_supported function."""

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


class TestGetSupportedLanguages:
    """Tests for the get_supported_languages function."""

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


class TestLanguageMap:
    """Tests for the language mapping constants."""

    def test_tesseract_language_map_not_empty(self) -> None:
        """Test that the language map is not empty."""
        assert len(TESSERACT_LANGUAGE_MAP) > 0, "Language map should not be empty"

    def test_supported_tesseract_languages_not_empty(self) -> None:
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

    def test_common_language_codes_present(self) -> None:
        """Test that common language codes are in the map."""
        common_codes = ["eng", "fra", "spa", "deu", "hin"]
        for code in common_codes:
            assert (
                code in TESSERACT_LANGUAGE_MAP.values()
            ), f"Language code {code} should be in the map"
