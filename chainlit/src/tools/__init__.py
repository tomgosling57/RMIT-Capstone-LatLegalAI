"""
LatMatrix Chainlit Tools – Document Parser Tool Registration

This module registers Chainlit tools (@cl.tool) for document parsing and analysis.
The actual parser implementations live in sibling modules
(pdf_parser.py, word_parser.py, etc.).
Each tool accepts file bytes and returns extracted text or classification results.
"""

import tempfile
from pathlib import Path
from typing import Optional

from .base_parser import BaseDocumentParser
from .language_detector import (
    detect_language,
    is_language_supported,
    get_supported_languages,
    UnsupportedLanguageError,
)
from .pdf_parser import PDFParser
from .ocr_pdf_parser import OCRPDFParser
from .word_parser import WordParser
from .text_parser import TextParser
from .pdf_type_detector import PDFType, detect_pdf_type
from .parser_factory import DocumentParserFactory
from .nlp_processor import NLPService, nlp_service
from .entity_extractor import EntityExtractorService, entity_extractor

__all__ = [
    "BaseDocumentParser",
    "PDFParser",
    "OCRPDFParser",
    "WordParser",
    "TextParser",
    "PDFType",
    "detect_pdf_type",
    "DocumentParserFactory",
    "NLPService",
    "nlp_service",
    "EntityExtractorService",
    "entity_extractor",
    "detect_language",
    "is_language_supported",
    "get_supported_languages",
    "UnsupportedLanguageError",
    "detect_ocr_language",
    # Chainlit tool functions (importable for testing)
    "parse_pdf",
    "parse_word_document",
    "parse_text_file",
    "detect_pdf_format",
    "get_pdf_metadata",
    "parse_document_auto",
    # Internal helpers
    "_parse_document",
]


async def _parse_document(
    file_bytes: bytes,
    file_name: str,
    lang: Optional[str] = None,
) -> str:
    """
    Internal helper to parse a document from bytes.

    Pre-computes the PDF type (for PDF files) so that the factory's
    ``get_parser()`` can skip its own ``detect_pdf_type()`` call,
    avoiding redundant file I/O.

    When the selected parser is OCRPDFParser and ``lang`` is provided,
    the language is forwarded to the parser for OCR extraction.

    Args:
        file_bytes: Raw file content as bytes
        file_name: Original file name (used for extension detection)
        lang: Optional language code for OCR (e.g. ``"eng"``, ``"hin"``).
              Passed through to the parser when it is an OCRPDFParser.

    Returns:
        Extracted text from the document

    Raises:
        ValueError: If the file format is not supported or parsing fails
    """
    with tempfile.NamedTemporaryFile(
        suffix=Path(file_name).suffix, delete=False
    ) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)

    try:
        # Pre-compute PDF type so the factory doesn't re-open the file.
        pdf_type: Optional[PDFType] = None
        if tmp_path.suffix.lower() == ".pdf":
            pdf_type = detect_pdf_type(tmp_path)

        factory = DocumentParserFactory(use_ocr_fallback=True)
        # Pass detect_lang=False since we handle lang ourselves
        parser = factory.get_parser(tmp_path, pdf_type=pdf_type, detect_lang=False)

        if isinstance(parser, OCRPDFParser) and lang is not None:
            ocr_lang = parser.resolve_lang(lang)
            pages = await parser.parse(tmp_path, lang=ocr_lang)
        else:
            pages = await parser.parse(tmp_path)

        return "\n\n".join(pages)
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Chainlit tool functions — defined at module level so they are importable
# for testing even when Chainlit is not running.
# The @cl.tool decorator is applied inside _register_tools() below.
# ---------------------------------------------------------------------------


async def parse_pdf(file_bytes: bytes, file_name: str) -> str:
    """Parse a PDF document (digital or scanned)."""
    return await _parse_document(file_bytes, file_name)


async def parse_word_document(file_bytes: bytes, file_name: str) -> str:
    """Parse a Microsoft Word document (.docx or .doc)."""
    return await _parse_document(file_bytes, file_name)


async def parse_text_file(file_bytes: bytes, file_name: str) -> str:
    """Parse a plain text file (.txt, .md, .rst, etc.)."""
    return await _parse_document(file_bytes, file_name)


async def detect_pdf_format(file_bytes: bytes, file_name: str) -> str:
    """Detect whether a PDF is digital-native, scanned, hybrid, or unknown."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)
    try:
        pdf_type = detect_pdf_type(tmp_path)
        return f"PDF Type: {pdf_type.value}"
    finally:
        tmp_path.unlink(missing_ok=True)


async def get_pdf_metadata(file_bytes: bytes, file_name: str) -> str:
    """Extract metadata from a PDF document."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)
    try:
        parser = PDFParser()
        metadata = await parser.get_metadata_async(tmp_path)
        lines = [
            f"**Title:** {metadata.get('title', 'Unknown')}",
            f"**Author:** {metadata.get('author', 'Unknown')}",
            f"**Subject:** {metadata.get('subject', 'N/A')}",
            f"**Pages:** {metadata.get('pages', 'N/A')}",
            f"**Created:** {metadata.get('creation_date', 'N/A')}",
            f"**Modified:** {metadata.get('modification_date', 'N/A')}",
            f"**Producer:** {metadata.get('producer', 'N/A')}",
            f"**Creator:** {metadata.get('creator', 'N/A')}",
        ]
        return "\n".join(lines)
    finally:
        tmp_path.unlink(missing_ok=True)


async def parse_document_auto(file_bytes: bytes, file_name: str) -> str:
    """Automatically parse any supported document format."""
    return await _parse_document(file_bytes, file_name)


async def detect_ocr_language(file_bytes: bytes, file_name: str) -> str:
    """Detect the language of an OCR document and return Tesseract language code."""
    with tempfile.NamedTemporaryFile(
        suffix=Path(file_name).suffix, delete=False
    ) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)
    try:
        parser = OCRPDFParser()
        detected = parser.detect_language_from_sample(tmp_path)
        if detected:
            return f"Detected language: {detected}"
        return "Language detection failed — will use English (eng) as default"
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Chainlit tool registration — deferred to avoid import-time errors
# when Chainlit is not running (e.g. during pytest collection).
# ---------------------------------------------------------------------------


def _register_tools() -> None:
    """Register all ``@cl.tool``-decorated functions.

    Called once at import time when Chainlit is available.
    """
    import chainlit as cl

    cl.tool(name="parse_pdf")(parse_pdf)
    cl.tool(name="parse_word_document")(parse_word_document)
    cl.tool(name="parse_text_file")(parse_text_file)
    cl.tool(name="detect_pdf_format")(detect_pdf_format)
    cl.tool(name="get_pdf_metadata")(get_pdf_metadata)
    cl.tool(name="parse_document_auto")(parse_document_auto)
    cl.tool(name="detect_ocr_language")(detect_ocr_language)


# Register tools at import time when Chainlit is available.
# The try/except allows the parser classes to be imported for testing
# without requiring a running Chainlit app context.
try:
    _register_tools()
except (ImportError, KeyError, RuntimeError):
    pass
