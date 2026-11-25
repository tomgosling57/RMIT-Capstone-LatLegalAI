"""
Parser factory for creating appropriate document parsers.
Detects document format and returns the correct parser instance.
"""

import logging
from pathlib import Path
from typing import List, Optional
from .base_parser import BaseDocumentParser
from .pdf_parser import PDFParser
from .ocr_pdf_parser import OCRPDFParser
from .word_parser import WordParser
from .text_parser import TextParser
from .pdf_type_detector import PDFType, detect_pdf_type
from exceptions import UnsupportedLanguageError
from utilities.language_detector import (
    is_language_supported,
    get_supported_languages,
)

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
        Tesseract's supported languages. If detection fails or the language is
        unsupported, an ``UnsupportedLanguageError`` is raised.

        Non-PDF files are handled by the existing extension-based logic.

        When ``pdf_type`` is provided (e.g. from a pre-computed detection),
        the factory skips calling ``detect_pdf_type()``, avoiding redundant
        I/O on the PDF file.

        Args:
            file_path: Path to the document file
            pdf_type: Optional pre-computed PDF type classification.
                       When provided, skips the detection pipeline to avoid
                       redundant file I/O.
            detect_lang: Whether to auto-detect language for OCR documents
                        (default: True). When True, raises UnsupportedLanguageError
                        if the detected language is not supported.

        Returns:
            Parser instance that supports the file format

        Raises:
            ValueError: If no parser supports the file format
            UnsupportedLanguageError: If detect_lang=True and the detected
                                     language is not supported by Tesseract
        """
        suffix = file_path.suffix.lower()

        # ── PDF handling with type detection ───────────────────────────────
        if suffix == ".pdf":
            if pdf_type is None:
                pdf_type = detect_pdf_type(file_path)
                logger.info(
                    "PDF type detection result — file_path=%s, pdf_type=%s",
                    file_path,
                    pdf_type.value,
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
                    self._validate_ocr_language(file_path)

                return OCRPDFParser()

            # DIGITAL, HYBRID, and UNKNOWN all route to PDFParser
            logger.info(
                "Routing PDF to PDFParser — file_path=%s,"
                "pdf_type=%s, parser=PDFParser",
                file_path,
                pdf_type.value,
            )
            return PDFParser()

        # ── Non-PDF: use extension-based matching ──────────────────────────
        for parser in self._parsers:
            if parser.supports_format(file_path):
                return parser

        raise ValueError(
            f"No parser available for file: {file_path}. "
            f"Supported formats: PDF, Word (.doc/.docx), Text (.txt/.md)"
        )

    def _validate_ocr_language(self, file_path: Path) -> None:
        """
        Validate that the detected language is supported by Tesseract.

        Detects the language of the document and raises UnsupportedLanguageError
        if the detected language is not in Tesseract's supported set.

        Args:
            file_path: Path to the document file

        Raises:
            UnsupportedLanguageError: If the detected language is not supported
        """
        ocr_parser = OCRPDFParser()
        detected_lang = ocr_parser._detect_language_from_sample(file_path)

        if detected_lang is None:
            logger.warning(
                "Language detection returned None for file — file=%s, "
                "will proceed with default language",
                file_path,
            )
            return

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
