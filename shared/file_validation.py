"""
File validation utilities using magic number (libmagic) detection.

Provides MIME-based file type detection, extension verification, and
helper predicates for common document formats.  Designed to be shared
across services (backend, Chainlit, etc.) — no service-specific imports.

Dependencies:
    - python-magic (libmagic bindings)
"""

import os
from typing import Optional

import magic


# ── MIME-to-extension mapping ────────────────────────────────────────────────

MIME_TO_EXT: dict[str, Optional[str]] = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "docx",
    "application/vnd.ms-word.document.macroEnabled.12": "docx",
    "text/plain": "txt",
}

SUPPORTED_EXTENSIONS: set[str] = {"pdf", "png", "jpg", "docx", "txt"}


# ── Public API ───────────────────────────────────────────────────────────────


def detect_file_type_bytes(file_bytes: bytes) -> Optional[str]:
    """
    Detect file type from raw bytes using libmagic.

    Args:
        file_bytes: At least the first few bytes of the file (header).

    Returns:
        Extension string (e.g. ``"pdf"``, ``"docx"``) or ``None`` if
        the type is unsupported or detection fails.
    """
    try:
        mime = magic.from_buffer(file_bytes, mime=True)
    except Exception:
        return None
    return MIME_TO_EXT.get(mime)


def detect_file_type_from_path(file_path: str) -> Optional[str]:
    """
    Detect file type from a file path using libmagic.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        Extension string or ``None`` if unsupported.
    """
    try:
        mime = magic.from_file(file_path, mime=True)
    except Exception:
        return None
    return MIME_TO_EXT.get(mime)


def extension_matches(filename: str, detected: str) -> bool:
    """
    Check whether a filename's extension matches a detected type.

    Args:
        filename: Original filename (e.g. ``"contract.pdf"``).
        detected: Detected type extension (e.g. ``"pdf"``).

    Returns:
        ``True`` if the extension matches (case-insensitive).
    """
    ext = os.path.splitext(filename)[1].lower().replace(".", "")
    return ext == detected


def is_pdf(file_bytes: bytes) -> bool:
    """Check whether the given bytes represent a PDF."""
    return detect_file_type_bytes(file_bytes) == "pdf"


def is_docx(file_bytes: bytes) -> bool:
    """Check whether the given bytes represent a Word document."""
    return detect_file_type_bytes(file_bytes) == "docx"


def is_txt(file_bytes: bytes) -> bool:
    """Check whether the given bytes represent a plain text file."""
    return detect_file_type_bytes(file_bytes) == "txt"


def is_png(file_bytes: bytes) -> bool:
    """Check whether the given bytes represent a PNG image."""
    return detect_file_type_bytes(file_bytes) == "png"


def is_jpg(file_bytes: bytes) -> bool:
    """Check whether the given bytes represent a JPEG image."""
    return detect_file_type_bytes(file_bytes) == "jpg"


def is_supported(file_bytes: bytes) -> bool:
    """Check whether the given bytes represent a supported file type."""
    return detect_file_type_bytes(file_bytes) is not None
