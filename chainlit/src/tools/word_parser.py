"""
Word document parser for .doc and .docx files.
Uses python-docx to extract text from Word documents.
Asynchronous implementation using asyncio.to_thread for non-blocking I/O.
"""

import asyncio
from pathlib import Path
from typing import List
from docx import Document
from .base_parser import BaseDocumentParser


class WordParser(BaseDocumentParser):
    """Parser for Microsoft Word documents."""

    async def parse(self, file_path: Path, extraction_mode: str = "flow") -> List[str]:
        """
        Extract text from Word document asynchronously.

        Args:
            file_path: Path to Word file
            extraction_mode: Extraction mode - "flow" (default) or
            other format-specific modes

        Returns:
            Extracted text as a list with one element (single page)
        """
        self._validate_file_exists(file_path)

        doc = await asyncio.to_thread(Document, str(file_path))
        text_parts = []

        for para in doc.paragraphs:
            para_text = self._extract_paragraph_text(para)
            if para_text.strip():
                if para.style and para.style.name.startswith("Heading"):
                    level = self._get_heading_level(para.style.name)
                    para_text = "#" * level + " " + para_text
                text_parts.append(para_text)

        for table in doc.tables:
            table_text = self._extract_table_text(table)
            text_parts.extend(table_text)

        return ["\n".join(text_parts)]

    def _extract_paragraph_text(self, para) -> str:
        """Extract text from a paragraph with formatting markers."""
        text = ""
        for run in para.runs:
            run_text = run.text
            if run.bold:
                run_text = f"**{run_text}**"
            if run.italic:
                run_text = f"*{run_text}*"
            text += run_text
        return text

    def _get_heading_level(self, style_name: str) -> int:
        """Get heading level from style name."""
        try:
            level = int(style_name.split()[-1])
            return level
        except (ValueError, IndexError):
            return 1

    def _extract_table_text(self, table) -> list[str]:
        """Extract text from a table as rows."""
        table_rows = []
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                cell_text = ""
                for para in cell.paragraphs:
                    cell_text += self._extract_paragraph_text(para) + " "
                row_text.append(cell_text.strip())
            table_rows.append(" | ".join(row_text))
        return table_rows

    @classmethod
    def supports_format(cls, file_path: Path) -> bool:
        """
        Check if file is a Word document.

        Args:
            file_path: Path to check

        Returns:
            True if file has .doc or .docx extension
        """
        suffix = file_path.suffix.lower()
        return suffix in [".doc", ".docx"]
