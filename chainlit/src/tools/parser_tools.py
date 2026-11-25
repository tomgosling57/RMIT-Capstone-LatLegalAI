"""
Parser tools for Chainlit document processing.

Provides functions to parse documents locally within Chainlit using
the local parser implementations, eliminating the need for HTTP
calls to the FastAPI backend.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from .language_detector import UnsupportedLanguageError
from .ocr_pdf_parser import OCRPDFParser
from ..config import SUPPORTED_OCR_LANGUAGES
from .parser_factory import DocumentParserFactory

try:
    from ..config import SUPPORTED_OCR_LANGUAGES
except ImportError:
    # Fallback when imported as a top-level package (e.g., during testing)
    try:
        from config import SUPPORTED_OCR_LANGUAGES
    except ImportError:
        SUPPORTED_OCR_LANGUAGES = {
            "english": "eng",
            "french": "fra",
            "german": "deu",
            "spanish": "spa",
            "hindi": "hin",
        }
from .base_parser import BaseDocumentParser

logger = logging.getLogger(__name__)


class ParserToolError(Exception):
    """Raised when document parsing fails."""

    pass


def get_supported_ocr_languages() -> dict[str, str]:
    """
    Get the mapping of supported OCR language names to Tesseract codes.

    Returns:
        Dictionary mapping language names (lowercase) to Tesseract
        language codes (e.g. ``{"english": "eng", "french": "fra"}``).
    """
    return dict(SUPPORTED_OCR_LANGUAGES)


def validate_ocr_language(
    detected_language: str,
) -> None:
    """
    Validate that a detected language is supported for OCR processing.

    Checks the detected language (as a Tesseract language code or full
    language name) against the configured ``SUPPORTED_OCR_LANGUAGES``.
    Raises ``UnsupportedLanguageError`` if the language is not supported.

    Args:
        detected_language: Tesseract language code (e.g. ``"eng"``,
            ``"hin"``) or full language name (e.g. ``"english"``,
            ``"hindi"``).

    Raises:
        UnsupportedLanguageError: If the detected language is not in the
            supported set.
    """
    normalized = detected_language.strip().lower()

    # Build a set of all valid identifiers (both names and codes)
    supported_names = set(SUPPORTED_OCR_LANGUAGES.keys())
    supported_codes = set(SUPPORTED_OCR_LANGUAGES.values())
    all_supported = supported_names | supported_codes

    # Handle compound language codes (e.g. "eng+hin")
    parts = normalized.split("+")
    for part in parts:
        part = part.strip()
        if part and part not in all_supported:
            raise UnsupportedLanguageError(
                detected_language=detected_language,
            )


async def parse_document(
    file_path: str,
    use_ocr_fallback: bool = True,
    ocr_language: str | None = None,
) -> Tuple[List[str], int, int]:
    """
    Parse a document and extract text using the appropriate parser.

    This function uses the DocumentParserFactory to select the correct
    parser based on file type and content, then extracts text from the
    document.

    When the selected parser is OCRPDFParser:
    - If ``lang`` is provided, it is used as the OCR language (overrides
      auto-detection).
    - If ``lang`` is ``None``, the language is auto-detected from a sample
      image of the document. If detection fails, ``"eng"`` is used as default.

    Non-OCR parsers ignore the ``lang`` parameter entirely.

    Args:
        file_path: Path to the document file to parse
        use_ocr_fallback: Whether to use OCR as fallback for PDFs
        ocr_language: Optional Tesseract language code(s) for OCR
            (e.g. ``"eng"``, ``"hin"``, ``"fra"``, ``"eng+hin"``).
            When provided, the language is validated against the
            configured supported languages before parsing. When
            ``None``, no language validation is performed and the
            OCR parser uses its default (English).

    Returns:
        Tuple of (extracted_pages, page_count, character_count, detected_lang)
        - extracted_pages: List of text strings, one per page
        - page_count: Number of pages extracted
        - character_count: Total character count across all pages
        - detected_lang: Detected or used language code (``None`` for non-OCR
          parsers or when detection fails)

    Raises:
        ParserToolError: If parsing fails or file format is unsupported
        FileNotFoundError: If the file does not exist
        UnsupportedLanguageError: If ``ocr_language`` is provided and
            is not in the configured supported languages
    """
    try:
        file_path_obj = Path(file_path)

        # Validate file exists
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path_obj.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Validate OCR language if provided
        if ocr_language is not None:
            validate_ocr_language(ocr_language)

        # Get the appropriate parser.
        # Pass detect_lang=True so the factory runs language detection once
        # (via _validate_ocr_language) and stores the result on the returned
        # parser as ``parser._detected_lang``.  This avoids a redundant second
        # OCR sample pass in this function.
        factory = DocumentParserFactory(use_ocr_fallback=use_ocr_fallback)
        parser: BaseDocumentParser = factory.get_parser(file_path_obj, detect_lang=True)

        logger.info(
            f"Parsing document with {parser.__class__.__name__}",
            extra={
                "file_path": str(file_path),
                "parser": parser.__class__.__name__,
                "ocr_language": ocr_language,
            },
        )

        # Read the language that the factory already detected (if any).
        # Priority order:
        #   1. User-specified ocr_language (from session / UI)
        #   2. Auto-detected language from factory's sample OCR pass
        #   3. Default (English) — handled by the parser itself
        detected_lang: Optional[str] = None
        if isinstance(parser, OCRPDFParser):
            detected_lang = getattr(parser, "_detected_lang", None)

        # Parse the document asynchronously
        # Pass the resolved language to OCRPDFParser so it doesn't
        # default to English-only OCR for non-English documents.
        if isinstance(parser, OCRPDFParser):
            # User-specified language takes highest priority
            if ocr_language is not None:
                ocr_lang = ocr_language
                detected_lang = ocr_language
                logger.info(
                    "Using user-specified OCR language — lang=%s",
                    ocr_lang,
                )
            elif detected_lang is not None:
                ocr_lang = detected_lang
                logger.info(
                    "Using auto-detected OCR language — lang=%s",
                    ocr_lang,
                )
            else:
                # Explicitly pass "eng" rather than None for consistency.
                # OCRPDFParser.resolve_lang(None) also returns "eng"
                # (DEFAULT_OCR_LANG), so both values are functionally
                # equivalent — but passing "eng" explicitly makes the
                # fallback behaviour visible in a single code path.
                ocr_lang = "eng"
                logger.info(
                    "No language detected or specified, falling back to English"
                )

            extracted_pages = await parser.parse(file_path_obj, lang=ocr_lang)
        else:
            extracted_pages = await parser.parse(file_path_obj)

        # Calculate statistics
        page_count = len(extracted_pages)
        character_count = sum(len(page) for page in extracted_pages)

        logger.info(
            "Document parsed successfully",
            extra={
                "file_path": str(file_path),
                "pages": page_count,
                "characters": character_count,
                "detected_lang": detected_lang,
            },
        )

        return extracted_pages, page_count, character_count, detected_lang

    except FileNotFoundError:
        raise
    except UnsupportedLanguageError as e:
        logger.warning(
            "Unsupported language detected",
            extra={
                "file_path": str(file_path),
                "detected_language": e.detected_language or "unknown",
            },
        )
        raise
    except ValueError as e:
        if "No parser available" in str(e):
            raise ParserToolError(
                f"Unsupported file format: {Path(file_path).suffix}. "
                f"Supported formats: PDF, DOCX, TXT"
            ) from e
        raise ParserToolError(f"Invalid file: {str(e)}") from e
    except Exception as e:
        logger.error(
            "Document parsing failed",
            extra={"file_path": str(file_path), "error": str(e)},
            exc_info=True,
        )
        raise ParserToolError(f"Failed to parse document: {str(e)}") from e


def get_supported_formats() -> List[str]:
    """
    Get list of supported document formats.

    Returns:
        List of supported file extensions (e.g., ['.pdf', '.docx', '.txt'])
    """
    return [".pdf", ".docx", ".doc", ".txt", ".md"]


def format_extracted_text(
    extracted_pages: List[str], max_preview_chars: int = 500
) -> str:
    """
    Format extracted text for display in Chainlit.

    Joins pages with clear separators and optionally truncates
    for preview purposes.

    Args:
        extracted_pages: List of text strings from parser
        max_preview_chars: Maximum characters to show in preview (0 = no limit)

    Returns:
        Formatted text string suitable for Chainlit display
    """
    if not extracted_pages:
        return ""

    # Join pages with clear separator
    full_text = "\n\n---\n\n".join(extracted_pages)

    # Truncate if needed
    if max_preview_chars > 0 and len(full_text) > max_preview_chars:
        return full_text[:max_preview_chars] + "\n\n... (truncated)"

    return full_text
