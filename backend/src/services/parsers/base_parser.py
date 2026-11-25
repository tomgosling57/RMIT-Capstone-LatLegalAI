"""
Abstract base class for document parsers.
All document parsers must implement this interface.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from logging_config import get_logger

logger = get_logger(__name__)


class BaseDocumentParser(ABC):
    """
    Abstract base class for document parsers.

    Each parser must implement:
    1. parse() - Extract text from a document
    2. supports_format() - Check if parser supports the file format
    """

    @abstractmethod
    async def parse(self, file_path: Path, extraction_mode: str = "flow") -> List[str]:
        """
        Extract text from the document at the given path (async).

        Args:
            file_path: Path to the document file
            extraction_mode: Extraction mode - "flow" (default) or other
              format-specific modes

        Returns:
            Extracted text as a list of strings, one per page

        Raises:
            ValueError: If the file cannot be parsed
            FileNotFoundError: If the file does not exist
        """
        pass

    @classmethod
    @abstractmethod
    def supports_format(cls, file_path: Path) -> bool:
        """
        Check if this parser supports the given file format.

        Args:
            file_path: Path to check

        Returns:
            True if this parser can handle the file, False otherwise
        """
        pass

    def _validate_file_exists(self, file_path: Path) -> None:
        """
        Helper method to validate file exists.

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the path is not a file
        """
        if not file_path.exists():
            logger.error(
                f"File not found: {file_path}",
                extra={"file_path": str(file_path)},
            )
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            logger.error(
                f"Path is not a file: {file_path}",
                extra={"file_path": str(file_path)},
            )
            raise ValueError(f"Path is not a file: {file_path}")
