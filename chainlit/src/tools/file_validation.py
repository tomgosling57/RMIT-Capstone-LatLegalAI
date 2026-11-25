"""
Chainlit tool for file validation using magic number detection.

Re-exports from the shared ``shared.file_validation`` module and wraps
the detection functions as Chainlit tools so LLM agents can validate
file types before parsing.

The ``validate_file_type`` function is defined at module level so it is
importable for testing even when Chainlit is not running.
The ``@cl.tool`` decorator is applied inside ``_register_tools()`` below.
"""

from pathlib import Path
from typing import Optional

__all__ = [
    "detect_file_type_bytes",
    "detect_file_type_from_path",
    "extension_matches",
    "is_pdf",
    "is_docx",
    "is_txt",
    "is_png",
    "is_jpg",
    "is_supported",
    "validate_file_type",
]


def detect_file_type_bytes(file_bytes: bytes) -> Optional[str]:
    """Lazy wrapper for detect_file_type_bytes."""
    from shared.file_validation import detect_file_type_bytes as _detect

    return _detect(file_bytes)


def detect_file_type_from_path(file_path: str) -> Optional[str]:
    """Lazy wrapper for detect_file_type_from_path."""
    from shared.file_validation import detect_file_type_from_path as _detect

    return _detect(file_path)


def extension_matches(file_name: str, detected_type: str) -> bool:
    """Lazy wrapper for extension_matches."""
    from shared.file_validation import extension_matches as _matches

    return _matches(file_name, detected_type)


def is_pdf(file_bytes: bytes) -> bool:
    """Lazy wrapper for is_pdf."""
    from shared.file_validation import is_pdf as _is_pdf

    return _is_pdf(file_bytes)


def is_docx(file_bytes: bytes) -> bool:
    """Lazy wrapper for is_docx."""
    from shared.file_validation import is_docx as _is_docx

    return _is_docx(file_bytes)


def is_txt(file_bytes: bytes) -> bool:
    """Lazy wrapper for is_txt."""
    from shared.file_validation import is_txt as _is_txt

    return _is_txt(file_bytes)


def is_png(file_bytes: bytes) -> bool:
    """Lazy wrapper for is_png."""
    from shared.file_validation import is_png as _is_png

    return _is_png(file_bytes)


def is_jpg(file_bytes: bytes) -> bool:
    """Lazy wrapper for is_jpg."""
    from shared.file_validation import is_jpg as _is_jpg

    return _is_jpg(file_bytes)


def is_supported(file_bytes: bytes) -> bool:
    """Lazy wrapper for is_supported."""
    from shared.file_validation import is_supported as _is_supported

    return _is_supported(file_bytes)


async def validate_file_type(file_bytes: bytes, file_name: str) -> str:
    """
    Validate a file's type using magic number (libmagic) detection.

    Reads the file header bytes and checks whether the content matches
    the expected extension.  Helps prevent extension-spoofing attacks.

    Args:
        file_bytes: Raw file content as bytes (first few KB are sufficient).
        file_name: Original file name (used for extension comparison).

    Returns:
        A string describing the validation result, e.g.:
        ``"Valid PDF file (contract.pdf)"`` or
        ``"Type mismatch: extension suggests .pdf but content is image/png"``.
    """
    detected = detect_file_type_bytes(file_bytes)
    if detected is None:
        return (
            f"Unsupported or unrecognised file type for '{file_name}'. "
            f"Supported types: PDF, Word (.docx), Text (.txt), PNG, JPEG."
        )

    if extension_matches(file_name, detected):
        return f"Valid {detected.upper()} file ({file_name})"
    else:
        ext = Path(file_name).suffix.lower().lstrip(".")
        return (
            f"Type mismatch: extension suggests .{ext} but "
            f"content is {detected.upper()}"
        )


# ---------------------------------------------------------------------------
# Chainlit tool registration — deferred to avoid import-time errors
# when Chainlit is not running (e.g. during pytest collection).
# ---------------------------------------------------------------------------


def _register_tools() -> None:
    """Register ``@cl.tool``-decorated functions for file validation."""
    import chainlit as cl

    cl.tool(name="validate_file_type")(validate_file_type)


try:
    _register_tools()
except (ImportError, KeyError, RuntimeError):
    pass
