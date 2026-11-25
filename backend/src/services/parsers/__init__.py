"""
Document parsers module.
Contains parsers for different document formats (PDF, Word, text, OCR).
"""

from .base_parser import BaseDocumentParser
from .pdf_parser import PDFParser
from .ocr_pdf_parser import OCRPDFParser
from .word_parser import WordParser
from .text_parser import TextParser
from .parser_factory import DocumentParserFactory

__all__ = [
    "BaseDocumentParser",
    "PDFParser",
    "OCRPDFParser",
    "WordParser",
    "TextParser",
    "DocumentParserFactory",
]
