"""
PDF parser for digital-native PDF documents.
Uses pdfplumber to extract text from PDF text layer.
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

from .base_parser import BaseDocumentParser
import pdfplumber


CID_TO_UNICODE_MAP: Dict[int, str] = {
    127: "\u2022",
    149: "\u2022",
    181: "\u2022",
    166: "\u2014",
    150: "\u2013",
    188: "\u2026",
    147: "\u201c",
    148: "\u201d",
    145: "\u2018",
    146: "\u2019",
    161: "\u00A1",
    191: "\u00BF",
    209: "\u00D1",
    241: "\u00F1",
    220: "\u00DC",
    252: "\u00FC",
}


class PDFParser(BaseDocumentParser):
    """Parser for digital PDF documents with text layer."""

    @staticmethod
    def _normalize_cid_characters(text: str) -> str:
        """
        Normalize CID (Character ID) references in extracted text.

        CID references appear as (cid:XXX) when pdfplumber encounters
        embedded fonts it cannot decode. This method maps common CID codes
        to their proper Unicode equivalents.

        Args:
            text: Text containing potential CID references

        Returns:
            Text with CID references replaced by proper Unicode characters
        """

        def replace_cid(match: re.Match[str]) -> str:
            """Replace a single CID reference with its Unicode equivalent."""
            cid_num = int(match.group(1))
            return CID_TO_UNICODE_MAP.get(cid_num, match.group(0))

        return re.sub(r"\(cid:(\d+)\)", replace_cid, text)

    @staticmethod
    def _reconstruct_devanagari_conjuncts(text: str) -> str:
        """
        Reconstruct Devanagari text that has been split by pdfplumber's text
        extraction into individual characters separated by whitespace.

        pdfplumber extracts Devanagari text from WeasyPrint-generated PDFs as
        individual glyphs separated by multiple spaces. For example,
        'निम्नलिखित' may appear as 'निम्नि  लि  खित' with 2+ spaces between
        each character, while legitimate word boundaries use single spaces.

        This method performs two levels of reconstruction:

        1. **Virama-based conjuncts**: Recombines consonant + virama (्, U+094D)
           + consonant patterns that were split (e.g., 'क  ् त' → 'क्त').

        2. **General Devanagari spacing**: Removes 2+ whitespace characters
           between adjacent Devanagari characters (including consonants, vowel
           signs, diacritics, and digits) to reconstruct words that pdfplumber
           fragmented. Single spaces between Devanagari characters are preserved
           as legitimate word boundaries.

        Args:
            text: Text that may contain split Devanagari characters

        Returns:
            Text with Devanagari characters properly reconstructed
        """
        CONSONANT_RANGE = "[\u0915-\u0939\u0958-\u095F]"
        VIRAMA = "\u094D"
        conjunct_pattern = re.compile(
            f"({CONSONANT_RANGE})\\s*{re.escape(VIRAMA)}\\s*({CONSONANT_RANGE})"
        )

        prev = ""
        while prev != text:
            prev = text
            text = conjunct_pattern.sub(r"\1" + VIRAMA + r"\2", text)

        DEVANAGARI_CHAR = "[\u0900-\u097F]"
        space_pattern = re.compile(f"({DEVANAGARI_CHAR})\\s{{2,}}({DEVANAGARI_CHAR})")

        prev = ""
        while prev != text:
            prev = text
            text = space_pattern.sub(r"\1 \2", text)

        return text

    def _parse_sync(self, file_path: Path, extraction_mode: str = "flow") -> List[str]:
        """
        Synchronous helper to extract text from PDF using pdfplumber.

        Args:
            file_path: Path to PDF file
            extraction_mode: Extraction mode - "flow" (default), "column", or "ocr"

        Returns:
            Extracted text as a list of strings, one per page

        Raises:
            ValueError: If PDF has no text layer (may be scanned)
            ValueError: If extraction_mode is invalid
            FileNotFoundError: If file does not exist
        """
        self._validate_file_exists(file_path)

        if extraction_mode not in ("flow", "column", "ocr"):
            raise ValueError(
                f"Invalid extraction_mode '{extraction_mode}'. "
                f"Must be 'flow', 'column', or 'ocr'."
            )

        try:
            with pdfplumber.open(file_path) as pdf:
                if not pdf.pages:
                    raise ValueError(f"PDF has no pages: {file_path}")

                text_pages = []
                for page in pdf.pages:
                    if extraction_mode == "flow":
                        page_text = page.extract_text()
                    else:
                        page_text = self._extract_column_text(page)

                    if page_text:
                        page_text = self._normalize_cid_characters(page_text)
                        page_text = self._reconstruct_devanagari_conjuncts(page_text)
                        text_pages.append(page_text)

                if not text_pages:
                    raise ValueError(
                        f"No text extracted from PDF "
                        f"(may be scanned/image-based): {file_path}"
                    )

                return text_pages

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to parse PDF {file_path}: {e}") from e

    def _extract_column_text(self, page) -> str:
        """
        Extract text in a column-aware manner using extract_words.

        Words are grouped by x-coordinate (column) and
        sorted by y-coordinate (reading order).

        Args:
            page: pdfplumber page object

        Returns:
            Text reconstructed in column order
        """
        words = page.extract_words(
            x_tolerance=2,
            y_tolerance=2,
            keep_blank_chars=False,
            use_text_flow=False,
        )

        if not words:
            return ""

        column_tolerance = 10

        sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))

        columns = []
        for word in sorted_words:
            x0 = word["x0"]
            found_column = False
            for column in columns:
                col_x0 = column[0]["x0"]
                if abs(x0 - col_x0) < column_tolerance:
                    column.append(word)
                    found_column = True
                    break
            if not found_column:
                columns.append([word])

        columns.sort(key=lambda c: c[0]["x0"])

        for column in columns:
            column.sort(key=lambda w: w["top"])

        lines = []
        for column in columns:
            column_lines = {}
            for word in column:
                top = word["top"]
                if top not in column_lines:
                    column_lines[top] = []
                column_lines[top].append(word)

            sorted_line_keys = sorted(column_lines.keys())
            for line_key in sorted_line_keys:
                line_words = column_lines[line_key]
                line_words.sort(key=lambda w: w["x0"])
                line_text = " ".join(w["text"] for w in line_words)
                lines.append(line_text)

        result = "\n".join(lines)
        result = self._normalize_cid_characters(result)
        result = self._reconstruct_devanagari_conjuncts(result)
        return result

    async def parse(self, file_path: Path, extraction_mode: str = "flow") -> List[str]:
        """
        Asynchronously extract text from PDF using pdfplumber.

        Runs the blocking I/O in a thread pool to avoid blocking the event loop.

        Args:
            file_path: Path to PDF file
            extraction_mode: Extraction mode - "flow" (default) or "column"

        Returns:
            Extracted text as a list of strings, one per page

        Raises:
            ValueError: If PDF has no text layer (may be scanned)
            ValueError: If extraction_mode is invalid
            FileNotFoundError: If file does not exist
        """
        return await asyncio.to_thread(self._parse_sync, file_path, extraction_mode)

    def get_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from PDF including author, title, and creation date.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with keys: author, title, creation_date, modification_date,
                                  subject, pages, producer, creator

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If PDF cannot be read
        """
        self._validate_file_exists(file_path)

        try:
            with pdfplumber.open(file_path) as pdf:
                metadata = pdf.metadata or {}

                creation_date = self._parse_pdf_date(metadata.get("CreationDate"))
                modification_date = self._parse_pdf_date(metadata.get("ModDate"))

                return {
                    "author": metadata.get("Author") or "Unknown",
                    "title": metadata.get("Title") or file_path.stem,
                    "creation_date": creation_date,
                    "modification_date": modification_date,
                    "subject": metadata.get("Subject") or None,
                    "pages": len(pdf.pages),
                    "producer": metadata.get("Producer") or None,
                    "creator": metadata.get("Creator") or None,
                }

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"Failed to read PDF metadata from {file_path}: {e}"
            ) from e

    async def get_metadata_async(self, file_path: Path) -> Dict[str, Any]:
        """
        Asynchronously extract metadata from PDF.

        Runs the blocking I/O in a thread pool to avoid blocking the event loop.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with metadata

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If PDF cannot be read
        """
        return await asyncio.to_thread(self.get_metadata, file_path)

    @staticmethod
    def _parse_pdf_date(pdf_date: Optional[str]) -> Optional[str]:
        """
        Parse PDF date format (D:YYYYMMDDHHmmSS) to ISO 8601 format.

        Args:
            pdf_date: Date string in PDF format or None

        Returns:
            ISO 8601 formatted date string or None
        """
        if not pdf_date:
            return None

        try:
            date_str = pdf_date.lstrip("D:")

            if len(date_str) < 8:
                return None

            year = int(date_str[0:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            hour = int(date_str[8:10]) if len(date_str) >= 10 else 0
            minute = int(date_str[10:12]) if len(date_str) >= 12 else 0
            second = int(date_str[12:14]) if len(date_str) >= 14 else 0

            dt = datetime(year, month, day, hour, minute, second)
            return dt.isoformat()

        except (ValueError, IndexError):
            return None

    @classmethod
    def supports_format(cls, file_path: Path) -> bool:
        """
        Check if file is a PDF.

        Args:
            file_path: Path to check

        Returns:
            True if file has .pdf extension
        """
        return file_path.suffix.lower() == ".pdf"
