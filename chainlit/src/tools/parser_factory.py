"""
Parser factory for creating appropriate document parsers.
Detects document format and returns the correct parser instance.
"""

import logging
from pathlib import Path
from typing import List, Optional

from .base_parser import BaseDocumentParser
from .language_detector import (
    is_language_supported,
    get_supported_languages,
    UnsupportedLanguageError,
)
from .ocr_pdf_parser import OCRPDFParser
from .pdf_parser import PDFParser
from .word_parser import WordParser
from .text_parser import TextParser
from .pdf_type_detector import PDFType, detect_pdf_type

logger = logging.getLogger(__name__)


class DocumentParserFactory:
    """
    Factory for creating document parsers based on file format.

    The factory tries parsers in order and returns the first one that
    supports the file format. For PDFs, it can try digital parsing first,
    then fall back to OCR if needed.
    """

    def __init__(self, use_ocr_fallback: bool = True):
        """
        Initialize the parser factory.

        Args:
            use_ocr_fallback: Whether to include OCR parser as fallback for PDFs
        """
        self.use_ocr_fallback = use_ocr_fallback
        self._parsers = self._create_parser_list()

    def _create_parser_list(self) -> List[BaseDocumentParser]:
        """Create the list of parsers in priority order."""
        parsers: List[BaseDocumentParser] = [
            PDFParser(),
            WordParser(),
            TextParser(),
        ]

        if self.use_ocr_fallback:
            parsers.append(OCRPDFParser())

        return parsers

    def get_parser(
        self,
        file_path: Path,
        pdf_type: Optional[PDFType] = None,
        detect_lang: bool = True,
    ) -> BaseDocumentParser:
        """
        Get the appropriate parser for the given file.

        For PDF files, the factory uses ``detect_pdf_type()`` to classify the
        document and route it to the most suitable parser:

        * ``DIGITAL`` → :class:`PDFParser`
        * ``SCANNED`` → :class:`OCRPDFParser`
        * ``HYBRID`` → :class:`PDFParser` (falls back to OCR if text extraction fails)
        * ``UNKNOWN`` → :class:`PDFParser` (falls back to OCR if text extraction fails)

        When routing to ``OCRPDFParser`` and ``detect_lang=True``, the factory
        automatically detects the document language and validates it against
        supported Tesseract languages. If the language is unsupported, an
        ``UnsupportedLanguageError`` is raised.

        Non-PDF files are handled by the existing extension-based logic.

        When ``pdf_type`` is provided (e.g. from a pre-computed detection),
        the factory skips calling ``detect_pdf_type()``, avoiding redundant
        I/O on the PDF file.

        When ``detect_lang`` is ``True`` (default) and the document is a scanned
        PDF, the factory runs language detection on the document and validates
        that the detected language is supported by Tesseract. If the language
        is not supported, an :class:`UnsupportedLanguageError` is raised.

        Args:
            file_path: Path to the document file
            pdf_type: Optional pre-computed PDF type classification.
                      When provided, skips the detection pipeline to avoid
                      redundant file I/O.
            detect_lang: Whether to auto-detect language for OCR documents
                        (default: True). When True, raises
                        UnsupportedLanguageError if the detected language
                        is not supported.

        Returns:
            Parser instance that supports the file format

        Raises:
            ValueError: If no parser supports the file format
            UnsupportedLanguageError: If detect_lang=True and the detected
                                     language is not supported
        """
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            if pdf_type is None:
                try:
                    pdf_type = detect_pdf_type(file_path)
                    logger.info(
                        "PDF type detection result — file_path=%s, pdf_type=%s",
                        file_path,
                        pdf_type.value,
                    )
                except FileNotFoundError:
                    logger.warning(
                        "PDF file not found — file_path=%s, falling back to"
                        " extension-based PDFParser",
                        file_path,
                    )
            else:
                logger.info(
                    "Using pre-computed PDF type — file_path=%s, pdf_type=%s",
                    file_path,
                    pdf_type.value,
                )

            if pdf_type == PDFType.SCANNED:
                logger.info(
                    "Routing scanned PDF to OCRPDFParser — file_path=%s,"
                    "pdf_type=%s, parser=OCRPDFParser",
                    file_path,
                    pdf_type.value,
                )

                if detect_lang:
                    detected_lang = self._validate_ocr_language(file_path)
                    return OCRPDFParser(detected_lang=detected_lang)

                return OCRPDFParser()

            logger.info(
                "Routing PDF to PDFParser — file_path=%s,"
                "pdf_type=%s, parser=PDFParser",
                file_path,
                pdf_type.value if pdf_type else "unknown",
            )
            return PDFParser()

        for parser in self._parsers:
            if parser.supports_format(file_path):
                return parser

        raise ValueError(
            f"No parser available for file: {file_path}. "
            f"Supported formats: PDF, Word (.doc/.docx), Text (.txt/.md)"
        )

    def get_parser_by_extension(self, file_path: Path) -> Optional[BaseDocumentParser]:
        """
        Get parser based solely on file extension.
        This is a simpler alternative that doesn't try multiple parsers.

        Args:
            file_path: Path to the document file

        Returns:
            Parser instance or None if no matching parser
        """
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return PDFParser()
        elif suffix in [".doc", ".docx"]:
            return WordParser()
        elif suffix in [".txt", ".md", ".rst", ".text"]:
            return TextParser()

        return None

    def _validate_ocr_language(self, file_path: Path) -> Optional[str]:
        """
        Detect and validate the document language for OCR processing.

        Detects the language of the document via a sample OCR pass and
        validates it against supported Tesseract languages.  If the language
        is unsupported, an ``UnsupportedLanguageError`` is raised.

        Args:
            file_path: Path to the document file

        Returns:
            The detected Tesseract language code (e.g. ``\"eng\"``, ``\"hin\"``),
            or ``None`` if detection failed or was unavailable.

        Raises:
            UnsupportedLanguageError: If the detected language is not supported
        """
        ocr_parser = OCRPDFParser()
        detected_lang = ocr_parser.detect_language_from_sample(file_path)

        if detected_lang is None:
            logger.warning(
                "Language detection returned None for file — file=%s, "
                "will proceed with default language",
                file_path,
            )
            return None

        if not is_language_supported(detected_lang):
            supported = get_supported_languages()
            raise UnsupportedLanguageError(
                detected_language=detected_lang,
                supported_languages=supported,
                details={
                    "file": str(file_path),
                    "detected_language": detected_lang,
                    "supported_count": len(supported),
                },
            )

        logger.info(
            "Language validation passed — file=%s, detected_lang=%s",
            file_path,
            detected_lang,
        )
        return detected_lang
