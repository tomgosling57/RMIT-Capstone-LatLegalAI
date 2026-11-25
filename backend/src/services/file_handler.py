import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


async def file_to_string(
    file_path: Path, filename: str, extraction_mode: str = "flow"
) -> List[str]:
    """
    DEPRECATED: Document parsing has been migrated to Chainlit.

    This function is kept for backward compatibility but should not be used.
    All document parsing is now handled by Chainlit tools in chainlit/src/tools/.

    The FastAPI backend is now a storage service only. Document parsing
    (PDFParser, OCRPDFParser, WordParser, TextParser) has been moved to Chainlit
    as @cl.Tool functions.

    Args:
        file_path: Path to the file to extract
        filename: Original filename (for detection)
        extraction_mode: Extraction mode - "flow" (default), "column", or "ocr"

    Returns:
        List of extracted text strings, one per page

    Raises:
        NotImplementedError: Always, as parsing is now in Chainlit
    """
    raise NotImplementedError(
        "Document parsing has been migrated to Chainlit. "
        "Use chainlit/src/tools/ parsers instead. "
        "The FastAPI backend is now a storage service only."
    )
