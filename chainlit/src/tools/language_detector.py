"""
Language detection utility for OCR document processing.

Detects the language of text samples and maps them to Tesseract-compatible
language codes for OCR processing.

This module is a shared copy of backend/src/utilities/language_detector.py,
enriched with an UnsupportedLanguageError exception class.
"""

import logging
from typing import Any, Dict, List, Optional

from langdetect import detect_langs, LangDetectException

logger = logging.getLogger(__name__)

TESSERACT_LANGUAGE_MAP: dict[str, str] = {
    "en": "eng",
    "hi": "hin",
    "fr": "fra",
    "es": "spa",
    "de": "deu",
    "pt": "por",
    "ru": "rus",
    "ja": "jpn",
    "zh-cn": "chi_sim",
    "zh-tw": "chi_tra",
    "ar": "ara",
    "th": "tha",
    "vi": "vie",
    "ko": "kor",
    "it": "ita",
    "nl": "nld",
    "pl": "pol",
    "tr": "tur",
    "el": "ell",
    "hu": "hun",
    "cs": "ces",
    "ro": "ron",
    "sv": "swe",
    "da": "dan",
    "fi": "fin",
    "no": "nor",
}

SUPPORTED_TESSERACT_LANGUAGES: set[str] = set(TESSERACT_LANGUAGE_MAP.values())


class UnsupportedLanguageError(Exception):
    """Raised when a detected language is not supported by OCR."""

    error_code: str = "UNSUPPORTED_LANGUAGE"
    message: str = "The detected language is not supported for OCR processing"
    status_code: int = 400

    def __init__(
        self,
        message: Optional[str] = None,
        detected_language: Optional[str] = None,
        supported_languages: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize unsupported language error.

        Args:
            message: Override the default message
            detected_language: The detected language code or name
            supported_languages: List of supported language codes
            details: Additional context information
        """
        error_details: Dict[str, Any] = details or {}
        if detected_language:
            error_details["detected_language"] = detected_language
        if supported_languages:
            error_details["supported_languages"] = supported_languages

        if not message:
            message = f"Language '{detected_language}' is not supported for OCR"
            if supported_languages:
                message += f". Supported languages: {', '.join(supported_languages)}"

        self.message = message
        self.error_code = "UNSUPPORTED_LANGUAGE"
        self.status_code = 400
        self.details = error_details
        # Backward-compatible direct attribute access for downstream handlers
        # (e.g. document_processor.py accesses e.detected_language directly).
        self._detected_language = detected_language
        self._supported_languages = supported_languages
        super().__init__(self.message)

    @property
    def detected_language(self) -> Optional[str]:
        """Backward-compatible accessor — returns detected language."""
        return self._detected_language or self.details.get("detected_language")

    @property
    def supported_languages(self) -> List[str]:
        """Backward-compatible accessor — returns supported languages."""
        return self._supported_languages or self.details.get("supported_languages", [])

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to structured response format.

        Returns:
            Dictionary with success=false and error details
        """
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            },
        }


def detect_language(
    text_sample: str, confidence_threshold: float = 0.5
) -> Optional[str]:
    """
    Detect the language of a text sample and return a Tesseract language code.

    Uses langdetect to identify the language, then maps it to a Tesseract-compatible
    code. If detection fails or confidence is below the threshold, returns None.

    Args:
        text_sample: Text to analyze for language detection
        confidence_threshold: Minimum confidence score (0.0-1.0) to accept detection.
                            Default 0.5 requires at least 50% confidence.

    Returns:
        Tesseract language code (e.g., "eng", "fra", "hin") or None if detection fails
        or confidence is too low.

    Raises:
        ValueError: If text_sample is empty or contains only whitespace
    """
    if not text_sample or not text_sample.strip():
        raise ValueError("text_sample cannot be empty or whitespace-only")

    try:
        detected_langs = detect_langs(text_sample)
        if not detected_langs:
            logger.warning("Language detection returned empty result")
            return None

        best_match = detected_langs[0]
        if best_match.prob < confidence_threshold:
            logger.warning(
                "Language detection confidence below threshold — "
                "lang=%s, confidence=%.2f, threshold=%.2f",
                best_match.lang,
                best_match.prob,
                confidence_threshold,
            )
            return None

        lang_code = best_match.lang
        tesseract_code = TESSERACT_LANGUAGE_MAP.get(lang_code)

        if tesseract_code:
            logger.info(
                "Language detected — detected_lang=%s, tesseract_code=%s, "
                "confidence=%.2f",
                lang_code,
                tesseract_code,
                best_match.prob,
            )
            return tesseract_code

        logger.warning(
            "Detected language not in Tesseract map — lang=%s, confidence=%.2f",
            lang_code,
            best_match.prob,
        )
        return None

    except LangDetectException as e:
        logger.warning("Language detection failed — error=%s", str(e))
        return None
    except Exception as e:
        logger.error(
            "Unexpected error during language detection — error=%s",
            str(e),
            exc_info=True,
        )
        return None


def is_language_supported(tesseract_code: str) -> bool:
    """
    Check if a Tesseract language code is supported.

    Args:
        tesseract_code: Tesseract language code (e.g., "eng", "fra")

    Returns:
        True if the language is in the supported set, False otherwise
    """
    return tesseract_code in SUPPORTED_TESSERACT_LANGUAGES


def get_supported_languages() -> list[str]:
    """
    Get a list of all supported Tesseract language codes.

    Returns:
        Sorted list of supported language codes
    """
    return sorted(SUPPORTED_TESSERACT_LANGUAGES)


__all__: list[str] = [
    "TESSERACT_LANGUAGE_MAP",
    "SUPPORTED_TESSERACT_LANGUAGES",
    "UnsupportedLanguageError",
    "detect_language",
    "is_language_supported",
    "get_supported_languages",
]
