"""doc_transformer – document format/layout generator for parser testing."""

from .transformer import (
    DocumentTransformer,
    generate_pdf,
    generate_docx,
    generate_scanned_pdf,
    generate_txt,
)

__all__ = [
    "DocumentTransformer",
    "generate_pdf",
    "generate_docx",
    "generate_scanned_pdf",
    "generate_txt",
]
