"""
OCR PDF parser for scanned PDF documents and images.
Uses OCR (pytesseract) to extract text from image-based PDFs and image files.
"""

import asyncio
import logging
from pathlib import Path
from typing import Generator, List, Optional

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

from services.parsers.base_parser import BaseDocumentParser
from utilities.language_detector import detect_language

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = frozenset(
    {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif"}
)

# Default OCR language (Tesseract language code)
DEFAULT_OCR_LANG: str = "eng"

# DPI used when converting PDF pages to images for OCR.
# The scanned test PDFs are generated at 150 DPI, so converting at 300 DPI
# gives Tesseract 4× the pixel data (2× in each dimension) to work with,
# which significantly improves recognition of fine Devanagari conjuncts.
OCR_PDF_DPI: int = 300

# Languages used in the sample OCR pass for language detection.
# A broad set ensures non-Latin scripts (e.g. Devanagari) are recognised.
LANGUAGE_DETECTION_SAMPLE_LANGS: str = "eng+hin+fra+spa+deu"

# Mapping from common language names to Tesseract language codes.
# Tesseract uses ISO 639-3 (three-letter) codes.
LANGUAGE_MAP: dict[str, str] = {
    "eng": "eng",
    "english": "eng",
    "hin": "hin",
    "hindi": "hin",
    "fra": "fra",
    "fre": "fra",
    "french": "fra",
    "spa": "spa",
    "spanish": "spa",
    "deu": "deu",
    "ger": "deu",
    "german": "deu",
}


class OCRPDFParser(BaseDocumentParser):
    """Parser for scanned PDF documents and images using OCR."""

    SUPPORTED_EXTENSIONS = SUPPORTED_EXTENSIONS

    @staticmethod
    def _resolve_lang(lang: Optional[str]) -> str:
        """
        Resolve a language name or code to a valid Tesseract language code.

        Accepts full language names (e.g. ``"hindi"``, ``"french"``) or
        ISO 639-3 three-letter codes (e.g. ``"hin"``, ``"fra"``).
        Also supports Tesseract's multi-language ``+`` notation
        (e.g. ``"eng+hin"``, ``"english+hindi"``), resolving each
        component individually before re-joining with ``+``.
        Falls back to ``DEFAULT_OCR_LANG`` (``"eng"``) when the input is
        ``None``, empty, or not recognised.

        Args:
            lang: Language name, Tesseract code, or ``+``-separated
                combination (e.g. ``"eng+hin"``), or ``None``.

        Returns:
            A valid Tesseract language code or ``+``-joined combination
            (e.g. ``"eng"``, ``"hin"``, ``"eng+hin"``).
        """
        if not lang:
            return DEFAULT_OCR_LANG
        normalized = lang.strip().lower()
        # Handle Tesseract's multi-language "+" notation
        parts = normalized.split("+")
        resolved_parts: list[str] = []
        for part in parts:
            resolved = LANGUAGE_MAP.get(part.strip())
            if resolved is not None:
                resolved_parts.append(resolved)
            else:
                # If not found in the map, check if it looks like a valid
                # Tesseract code (three-letter ISO 639-3) to pass through,
                # otherwise fall back to the default.
                if len(part.strip()) == 3 and part.strip().isalpha():
                    resolved_parts.append(part.strip())
                else:
                    resolved_parts.append(DEFAULT_OCR_LANG)
        return "+".join(resolved_parts)

    async def parse(
        self,
        file_path: Path,
        extraction_mode: str = "flow",
        lang: Optional[str] = None,
    ) -> List[str]:
        """
        Asynchronously extract text from scanned PDF or image using OCR.

        Runs OCR processing in a thread pool to avoid blocking the event loop.

        Args:
            file_path: Path to PDF or image file
            extraction_mode: Extraction mode - "flow" (default) or
            other format-specific modes
            lang: Tesseract language code(s) for OCR (e.g. "eng", "hin",
                "fra", "spa", "deu", or "eng+hin" for multiple languages).
                Defaults to "eng" if not provided.

        Returns:
            Extracted text as a list of strings, one per page

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file cannot be read or processed
            RuntimeError: If OCR processing fails
        """
        ocr_lang = self._resolve_lang(lang)

        # For OCR PDF parser, extraction_mode is currently ignored as OCR
        # processes the entire document differently regardless of mode
        if extraction_mode != "flow":
            logger.warning(
                "extraction_mode '%s' not supported by OCRPDFParser, "
                "defaulting to 'flow'. File: %s",
                extraction_mode,
                file_path,
            )

        result = await asyncio.to_thread(
            self._parse_sync, file_path, extraction_mode, ocr_lang
        )
        return result

    def _parse_sync(
        self,
        file_path: Path,
        extraction_mode: str = "flow",
        lang: str = DEFAULT_OCR_LANG,
    ) -> List[str]:
        """
        Synchronous helper to extract text from scanned PDF or image using OCR.

        Args:
            file_path: Path to PDF or image file
            extraction_mode: Extraction mode - "flow" (default)
            or other format-specific modes
            lang: Tesseract language code(s) for OCR

        Returns:
            Extracted text as a list of strings, one per page

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file cannot be read or processed
            RuntimeError: If OCR processing fails
        """
        self._validate_file_exists(file_path)

        try:
            if file_path.suffix.lower() == ".pdf":
                return self._parse_pdf(file_path, lang=lang)
            else:
                return self._parse_image(file_path, lang=lang)
        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            raise RuntimeError(
                f"Failed to process {file_path.suffix} with OCR: {e}"
            ) from e

    @staticmethod
    def _get_tesseract_config(lang: str) -> str:
        """Build Tesseract configuration string optimised for the target language.

        For Devanagari scripts (Hindi), applies:
        - OEM 1 (LSTM-only engine) — better Devanagari recognition
        - PSM 6 (single uniform text block) — avoids border/decoration being OCR'd
        - Character whitelist restricted to Devanagari Unicode range (U+0900-U+097F)
          plus common Latin, digits, and basic punctuation for mixed-script docs

        For other scripts, uses default PSM 3 with OEM 1.

        Args:
            lang: Tesseract language code(s) (e.g. ``"hin"``, ``"eng"``, ``"eng+hin"``).

        Returns:
            A Tesseract ``--oem`` / ``--psm`` / ``-c`` config string.
        """
        if "hin" in lang:
            # Devanagari Unicode range U+0900-U+097F
            devanagari_chars = "".join(chr(c) for c in range(0x0900, 0x0980))
            # Include Devanagari numerals (U+0966-U+096F)
            devanagari_numerals = "".join(chr(c) for c in range(0x0966, 0x0970))
            whitelist = (
                devanagari_chars
                + devanagari_numerals
                + "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                + "0123456789.,!?;:()-–— \n\t"
            )
            return f"--oem 1 --psm 6 -c tessedit_char_whitelist={whitelist}"
        return "--oem 1 --psm 3"  # LSTM-only, auto layout for non-Hindi

    def _parse_pdf(self, file_path: Path, lang: str = DEFAULT_OCR_LANG) -> List[str]:
        """Convert each PDF page to an image and run OCR."""
        pages = []
        custom_config = self._get_tesseract_config(lang)
        for i, image in enumerate(self._pdf_to_images(file_path), start=1):
            preprocessed = self._preprocess(image)
            page_text = pytesseract.image_to_string(
                preprocessed, lang=lang, config=custom_config
            )
            page_text = self._cleanup_text(page_text)
            pages.append(f"--- Page {i} ---\n{page_text}")
        return pages

    def _parse_image(self, file_path: Path, lang: str = DEFAULT_OCR_LANG) -> List[str]:
        """Run OCR on a single image file."""
        image = cv2.imread(str(file_path))
        if image is None:
            raise ValueError(f"Could not read image file: {file_path}")
        preprocessed = self._preprocess(image)
        custom_config = self._get_tesseract_config(lang)
        page_text = pytesseract.image_to_string(
            preprocessed, lang=lang, config=custom_config
        )
        page_text = self._cleanup_text(page_text)
        return [str(page_text.strip())]

    def _pdf_to_images(self, file_path: Path) -> Generator[np.ndarray, None, None]:
        """
        Convert PDF pages to grayscale OpenCV images without touching disk.

        Uses a higher DPI (300) than the default (200) to give Tesseract more
        pixel data for recognising fine Devanagari conjuncts and other complex
        script details.  The scanned test PDFs are generated at 150 DPI, so
        300 DPI provides 4× the pixel area.

        Yields one grayscale ndarray per page.
        """
        pil_pages = convert_from_path(
            str(file_path), dpi=OCR_PDF_DPI, grayscale=True
        )
        for pil_image in pil_pages:
            yield np.array(pil_image)

    @staticmethod
    def _preprocess(image: np.ndarray) -> np.ndarray:
        """
        Apply contrast enhancement and light denoising to improve OCR accuracy.

        1. CLAHE contrast enhancement — improves stroke/background separation
           without binarisation, preserving Devanagari conjunct continuity.
        2. Light denoising to reduce scanner grain.

        Previous versions used OpenCV adaptive thresholding or Otsu
        binarisation followed by morphological closing.  These approaches
        tend to break apart the fine connecting strokes (shirorekha /
        matras) of Devanagari script, producing garbled OCR output such as
        ``द्वाय`` instead of ``द्वारा`` or ``0000 0000077 0`` noise from
        broken title text.  CLAHE operates on grayscale values, not a binary
        threshold, so it enhances contrast without breaking stroke continuity.
        """
        # 1. CLAHE contrast enhancement — improves stroke/background separation
        #    without binarisation, preserving Devanagari conjunct continuity
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        # 2. Light denoising to reduce scanner grain
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
        return denoised

    @staticmethod
    def _cleanup_text(text: str) -> str:
        """Remove common OCR noise patterns from extracted text.

        Strips lines that are predominantly non-text characters (e.g.,
        danda characters from misread borders, hallucinated punctuation).

        Args:
            text: Raw OCR-extracted text.

        Returns:
            Cleaned text with noise lines removed.
        """
        lines = text.splitlines()
        cleaned: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                cleaned.append(line)
                continue
            # Skip lines where >60% of characters are non-text noise
            # (danda, pipe, digits used as noise, etc.)
            noise_chars = sum(
                1
                for c in stripped
                if c in "॥|"
                or (
                    c.isascii()
                    and not c.isalnum()
                    and not c.isspace()
                    and c not in ".,!?;:()-–—'\""
                )
            )
            if (noise_chars / len(stripped)) > 0.6:
                continue
            cleaned.append(line)
        return "\n".join(cleaned)

    def _detect_language_from_sample(
        self, file_path: Path, sample_size: int = 1
    ) -> Optional[str]:
        """
        Detect the language of a document by OCR-ing a sample page/image.

        Extracts text from the first page (or the image itself) using a
        temporary OCR pass with a broad set of languages (English, Hindi,
        French, Spanish, German), then runs language detection on the
        extracted text. Using a multi-language sample pass ensures that
        non-Latin scripts such as Devanagari are recognised during the
        language-detection phase, rather than producing garbled output
        from an English-only OCR pass.

        Args:
            file_path: Path to PDF or image file
            sample_size: Number of pages to sample for language detection
                        (default: 1, the first page)

        Returns:
            Tesseract language code (e.g., "eng", "fra") or None if detection fails
        """
        try:
            if file_path.suffix.lower() == ".pdf":
                images = list(self._pdf_to_images(file_path))
                sample_images = images[:sample_size]
            else:
                image = cv2.imread(str(file_path))
                if image is None:
                    logger.warning(
                        "Could not read image for language detection — file=%s",
                        file_path,
                    )
                    return None
                sample_images = [image]

            # Use a broad set of languages for the sample OCR pass so that
            # non-Latin scripts (e.g. Devanagari) are recognised, enabling
            # accurate language detection downstream.
            sample_lang = LANGUAGE_DETECTION_SAMPLE_LANGS
            sample_text_parts: list[str] = []
            for image in sample_images:
                preprocessed = self._preprocess(image)
                text = pytesseract.image_to_string(preprocessed, lang=sample_lang)
                if text.strip():
                    sample_text_parts.append(text)

            if not sample_text_parts:
                logger.warning(
                    "No text extracted from sample for language detection — file=%s",
                    file_path,
                )
                return None

            sample_text = " ".join(sample_text_parts)
            detected_lang = detect_language(sample_text)

            if detected_lang:
                logger.info(
                    "Language detected from sample — file=%s, detected_lang=%s",
                    file_path,
                    detected_lang,
                )
            else:
                logger.info(
                    "Language detection returned None — file=%s, "
                    "will use default language",
                    file_path,
                )

            return detected_lang

        except Exception as e:
            logger.warning(
                "Language detection failed, will use default — file=%s, error=%s",
                file_path,
                str(e),
            )
            return None

    @classmethod
    def supports_format(cls, file_path: Path) -> bool:
        """
        Check if file is a PDF or common image format.
        Note: This parser should be used as a fallback when other parsers fail.

        Args:
            file_path: Path to check

        Returns:
            True if file has a PDF or common image extension
        """
        return file_path.suffix.lower() in cls.SUPPORTED_EXTENSIONS
