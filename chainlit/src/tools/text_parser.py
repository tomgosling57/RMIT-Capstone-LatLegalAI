"""
Text file parser for plain text documents.
Handles .txt and other plain text formats with automatic encoding detection.
"""

import asyncio
from pathlib import Path
from typing import List
from .base_parser import BaseDocumentParser


class TextParser(BaseDocumentParser):
    """Parser for plain text documents.

    Supports encoding detection for UTF-8, ASCII, Latin-1, and Windows-1252.
    Also handles common text formats like Markdown and reStructuredText.
    """

    ENCODING_PRIORITY: List[str] = [
        "utf-8",
        "ascii",
        "utf-8-sig",
        "windows-1252",
        "iso-8859-1",
    ]

    MAX_FILE_SIZE = 100 * 1024 * 1024

    async def parse(self, file_path: Path, extraction_mode: str = "flow") -> List[str]:
        """
        Read text from plain text file with automatic encoding detection (async).

        Attempts to read the file using encodings in order of priority.
        Falls back to the most permissive encoding if needed.

        Args:
            file_path: Path to text file
            extraction_mode: Extraction mode - "flow" (default)
            or other format-specific modes

        Returns:
            Cleaned text content as a list with one element (single page)

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If file is too large or cannot be read
        """
        self._validate_file_exists(file_path)
        self._validate_file_size(file_path)

        text = await self._read_with_encoding_detection_async(file_path)

        cleaned_text = self._clean_text(text)

        return [cleaned_text]

    def parse_sync(self, file_path: Path) -> List[str]:
        """Synchronous wrapper for backward compatibility."""
        self._validate_file_exists(file_path)
        self._validate_file_size(file_path)
        text = self._read_with_encoding_detection(file_path)
        return [self._clean_text(text)]

    def _read_with_encoding_detection(self, file_path: Path) -> str:
        """
        Attempt to read file with various encodings (sync).

        Args:
            file_path: Path to the file

        Returns:
            File content as string

        Raises:
            ValueError: If all encoding attempts fail
        """
        for encoding in self.ENCODING_PRIORITY:
            try:
                return self._read_with_encoding(file_path, encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise ValueError(
            f"Could not read file {file_path} with any supported encoding. "
            f"Tried: {', '.join(self.ENCODING_PRIORITY)}"
        )

    async def _read_with_encoding_detection_async(self, file_path: Path) -> str:
        """
        Attempt to read file with various encodings using thread executor.
        """
        for encoding in self.ENCODING_PRIORITY:
            try:
                return await asyncio.to_thread(
                    self._read_with_encoding, file_path, encoding
                )
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise ValueError(
            f"Could not read file {file_path} with any supported encoding. "
            f"Tried: {', '.join(self.ENCODING_PRIORITY)}"
        )

    def _read_with_encoding(self, file_path: Path, encoding: str) -> str:
        """
        Sync helper to read file with a specific encoding.
        """
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.

        Removes:
        - Leading/trailing whitespace
        - Multiple consecutive blank lines (collapses to single blank line)
        - Excessive whitespace

        Args:
            text: Raw text content

        Returns:
            Cleaned text content
        """
        lines = [line.rstrip() for line in text.splitlines()]

        cleaned_lines = []
        blank_count = 0

        for line in lines:
            if line.strip() == "":
                blank_count += 1
                if blank_count <= 2:
                    cleaned_lines.append(line)
            else:
                blank_count = 0
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def _validate_file_size(self, file_path: Path) -> None:
        """
        Validate that file size is within acceptable limits.

        Args:
            file_path: Path to the file

        Raises:
            ValueError: If file is too large
        """
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File is too large: {file_size / (1024 * 1024):.1f} MB. "
                f"Maximum allowed size: {self.MAX_FILE_SIZE / (1024 * 1024):.1f} MB"
            )

    @classmethod
    def supports_format(cls, file_path: Path) -> bool:
        """
        Check if file is a plain text document.

        Args:
            file_path: Path to check

        Returns:
            True if file has supported text extension
        """
        suffix = file_path.suffix.lower()
        supported_extensions = [".txt", ".md", ".rst", ".text", ".markdown", ".mdown"]
        return suffix in supported_extensions
