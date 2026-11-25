"""Tests for WordParser."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from services.parsers.word_parser import WordParser
from tests.conftest import assert_text_accuracy

pytestmark = pytest.mark.slow

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"
SAMPLE_DOCX = ASSETS_DIR / "sample.docx"

# Markers for test organization
integration = pytest.mark.integration


def requires_asset(path: Path):
    """Skip test if asset file is missing."""
    return pytest.mark.skipif(
        not path.exists(),
        reason=f"Asset not found: {path} — populate tests/assets/ to run this test",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def parser() -> WordParser:
    """Return a WordParser instance."""
    return WordParser()


# ---------------------------------------------------------------------------
# Helper functions (factory functions for creating mocks)
# ---------------------------------------------------------------------------


def make_mock_run(text: str = "", bold: bool = False, italic: bool = False):
    """Create a mock Run object from python-docx."""
    run = Mock()
    run.text = text
    run.bold = bold
    run.italic = italic
    return run


def make_mock_paragraph(text: str = "Sample paragraph", style_name: str = "Normal"):
    """Create a mock Paragraph object from python-docx."""
    para = Mock()
    para.text = text

    # Create a mock run for the paragraph
    run = Mock()
    run.text = text
    run.bold = False
    run.italic = False
    para.runs = [run]

    # Create a mock style
    style = Mock()
    style.name = style_name
    para.style = style

    return para


def make_mock_heading(text: str = "Heading 1", level: int = 1):
    """Create a mock Heading paragraph."""
    para = Mock()
    para.text = text

    run = Mock()
    run.text = text
    run.bold = False
    run.italic = False
    para.runs = [run]

    style = Mock()
    style.name = f"Heading {level}"
    para.style = style

    return para


def make_mock_table(rows_data: list[list[str]] = None):
    """Create a mock Table object from python-docx."""
    if rows_data is None:
        rows_data = [["Header 1", "Header 2"], ["Cell 1", "Cell 2"]]

    table = Mock()
    rows = []

    for row_data in rows_data:
        row = Mock()
        cells = []

        for cell_text in row_data:
            cell = Mock()
            para = Mock()
            para_run = Mock()
            para_run.text = cell_text
            para_run.bold = False
            para_run.italic = False
            para.runs = [para_run]
            cell.paragraphs = [para]
            cells.append(cell)

        row.cells = cells
        rows.append(row)

    table.rows = rows
    return table


def make_mock_document(
    paragraphs: list = None,
    tables: list = None,
):
    """Create a mock Document object from python-docx."""
    doc = Mock()
    doc.paragraphs = paragraphs or []
    doc.tables = tables or []
    return doc


# ---------------------------------------------------------------------------
# Test supports_format
# ---------------------------------------------------------------------------


class TestSupportsFormat:
    """Test the supports_format() class method."""

    @pytest.mark.parametrize("ext", [".doc", ".docx", ".DOC", ".DOCX"])
    def test_supported_extensions(self, parser, ext):
        """Test that .doc and .docx files are recognized."""
        file_path = Path(f"document{ext}")
        assert parser.supports_format(file_path) is True

    @pytest.mark.parametrize(
        "ext", [".pdf", ".txt", ".xls", ".ppt", ".md", ".html", ".json"]
    )
    def test_unsupported_extensions(self, parser, ext):
        """Test that non-Word files are rejected."""
        file_path = Path(f"document{ext}")
        assert parser.supports_format(file_path) is False

    def test_case_insensitive_check(self, parser):
        """Test that extension check is case-insensitive."""
        assert parser.supports_format(Path("Document.DOCX")) is True
        assert parser.supports_format(Path("document.dOc")) is True


# ---------------------------------------------------------------------------
# Test parse() - Basic functionality
# ---------------------------------------------------------------------------


class TestParseBasic:
    """Test basic parse() functionality."""

    @pytest.mark.asyncio
    async def test_parse_simple_paragraph(self, parser, tmp_path):
        """Test parsing a document with a single paragraph."""
        doc = make_mock_document(paragraphs=[make_mock_paragraph("Hello, World!")])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "Hello, World!" in text
        assert text.strip() != ""

    @pytest.mark.asyncio
    async def test_parse_multiple_paragraphs(self, parser, tmp_path):
        """Test parsing multiple paragraphs."""
        paragraphs = [
            make_mock_paragraph(text="First paragraph"),
            make_mock_paragraph(text="Second paragraph"),
            make_mock_paragraph(text="Third paragraph"),
        ]
        doc = make_mock_document(paragraphs=paragraphs)

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "First paragraph" in text
        assert "Second paragraph" in text
        assert "Third paragraph" in text

    @pytest.mark.asyncio
    async def test_parse_empty_document(self, parser, tmp_path):
        """Test parsing an empty document."""
        doc = make_mock_document()

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert text == ""

    @pytest.mark.asyncio
    async def test_parse_skips_empty_paragraphs(self, parser, tmp_path):
        """Test that empty paragraphs are skipped."""
        paragraphs = [
            make_mock_paragraph(text="Real content"),
            make_mock_paragraph(text=""),
            make_mock_paragraph(text="   "),
            make_mock_paragraph(text="More content"),
        ]
        doc = make_mock_document(paragraphs=paragraphs)

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        lines = [line for line in text.split("\n") if line.strip()]
        assert len(lines) == 2
        assert "Real content" in text
        assert "More content" in text


# ---------------------------------------------------------------------------
# Test parse() — accuracy metrics
# ---------------------------------------------------------------------------


class TestParseAccuracy:
    """Word Error Rate accuracy tests for WordParser.parse()."""

    @pytest.mark.asyncio
    async def test_parse_simple_paragraph_accuracy(self, parser, tmp_path):
        """WER should be 0.0 for a single paragraph."""
        doc = make_mock_document(
            paragraphs=[make_mock_paragraph("This is a simple paragraph for testing.")]
        )
        file_path = tmp_path / "test.docx"
        file_path.touch()
        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)
        # parse() returns a list; join all pages into a single string
        actual_text = "\n".join(result) if isinstance(result, list) else result
        assert_text_accuracy(
            expected="This is a simple paragraph for testing.",
            actual=actual_text,
            threshold=0.0,
        )

    @pytest.mark.asyncio
    async def test_parse_multiple_paragraphs_accuracy(self, parser, tmp_path):
        """WER should be 0.0 for multiple paragraphs."""
        paragraphs = [
            make_mock_paragraph(text="First paragraph of the document."),
            make_mock_paragraph(text="Second paragraph with more details."),
            make_mock_paragraph(text="Third and final paragraph."),
        ]
        doc = make_mock_document(paragraphs=paragraphs)
        file_path = tmp_path / "test.docx"
        file_path.touch()
        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)
        actual_text = "\n".join(result) if isinstance(result, list) else result
        expected = (
            "First paragraph of the document.\n"
            "Second paragraph with more details.\n"
            "Third and final paragraph."
        )
        assert_text_accuracy(expected=expected, actual=actual_text, threshold=0.0)

    @pytest.mark.asyncio
    async def test_parse_with_numbers_and_symbols_accuracy(self, parser, tmp_path):
        """WER should be 0.0 for text with numbers and special characters."""
        para = Mock()
        run = Mock()
        run.text = "Invoice #12345: Total $1,250.00 (inc. GST) due 2024-01-15."
        run.bold = False
        run.italic = False
        para.runs = [run]
        style = Mock()
        style.name = "Normal"
        para.style = style

        doc = make_mock_document(paragraphs=[para])
        file_path = tmp_path / "test.docx"
        file_path.touch()
        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)
        actual_text = "\n".join(result) if isinstance(result, list) else result
        assert_text_accuracy(
            expected="Invoice #12345: Total $1,250.00 (inc. GST) due 2024-01-15.",
            actual=actual_text,
            threshold=0.0,
        )

    @pytest.mark.asyncio
    async def test_parse_heading_and_paragraph_accuracy(self, parser, tmp_path):
        """WER should be 0.0 for document with headings and body text."""
        paragraphs = [
            make_mock_heading(text="Introduction", level=1),
            make_mock_paragraph(
                text="This document outlines the terms and conditions."
            ),
            make_mock_heading(text="Clause 1: Payment", level=2),
            make_mock_paragraph(text="All payments shall be made within 30 days."),
        ]
        doc = make_mock_document(paragraphs=paragraphs)
        file_path = tmp_path / "test.docx"
        file_path.touch()
        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)
        actual_text = "\n".join(result) if isinstance(result, list) else result
        expected = (
            "# Introduction\n"
            "This document outlines the terms and conditions.\n"
            "## Clause 1: Payment\n"
            "All payments shall be made within 30 days."
        )
        assert_text_accuracy(expected=expected, actual=actual_text, threshold=0.0)

    @pytest.mark.asyncio
    async def test_parse_table_content_accuracy(self, parser, tmp_path):
        """WER should be 0.0 for table content."""
        table = make_mock_table(
            rows_data=[
                ["Item", "Description", "Amount"],
                ["Service A", "Consulting", "$1,000"],
                ["Service B", "Development", "$2,500"],
            ]
        )
        doc = make_mock_document(tables=[table])
        file_path = tmp_path / "test.docx"
        file_path.touch()
        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)
        actual_text = "\n".join(result) if isinstance(result, list) else result
        # WordParser formats tables with pipe separators between columns
        assert_text_accuracy(
            expected=(
                "Item | Description | Amount\n"
                "Service A | Consulting | $1,000\n"
                "Service B | Development | $2,500"
            ),
            actual=actual_text,
            threshold=0.0,
        )


# ---------------------------------------------------------------------------
# Test parse() - Formatting preservation
# ---------------------------------------------------------------------------


class TestParseFormatting:
    """Test formatting preservation."""

    @pytest.mark.asyncio
    async def test_parse_bold_text(self, parser, tmp_path):
        """Test that bold text is marked with ** delimiters."""
        para = Mock()
        run = Mock()
        run.text = "Bold text"
        run.bold = True
        run.italic = False
        para.runs = [run]
        style = Mock()
        style.name = "Normal"
        para.style = style

        doc = make_mock_document(paragraphs=[para])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "**Bold text**" in text

    @pytest.mark.asyncio
    async def test_parse_italic_text(self, parser, tmp_path):
        """Test that italic text is marked with * delimiters."""
        para = Mock()
        run = Mock()
        run.text = "Italic text"
        run.bold = False
        run.italic = True
        para.runs = [run]
        style = Mock()
        style.name = "Normal"
        para.style = style

        doc = make_mock_document(paragraphs=[para])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "*Italic text*" in text

    @pytest.mark.asyncio
    async def test_parse_bold_and_italic_text(self, parser, tmp_path):
        """Test text with both bold and italic formatting."""
        para = Mock()
        run = Mock()
        run.text = "Bold italic text"
        run.bold = True
        run.italic = True
        para.runs = [run]
        style = Mock()
        style.name = "Normal"
        para.style = style

        doc = make_mock_document(paragraphs=[para])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "***Bold italic text***" in text

    @pytest.mark.asyncio
    async def test_parse_mixed_formatting_in_paragraph(self, parser, tmp_path):
        """Test paragraph with multiple runs with different formatting."""
        para = Mock()

        run1 = Mock()
        run1.text = "Normal "
        run1.bold = False
        run1.italic = False

        run2 = Mock()
        run2.text = "bold"
        run2.bold = True
        run2.italic = False

        run3 = Mock()
        run3.text = " and "
        run3.bold = False
        run3.italic = False

        run4 = Mock()
        run4.text = "italic"
        run4.bold = False
        run4.italic = True

        para.runs = [run1, run2, run3, run4]
        style = Mock()
        style.name = "Normal"
        para.style = style

        doc = make_mock_document(paragraphs=[para])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "Normal " in text
        assert "**bold**" in text
        assert "*italic*" in text


# ---------------------------------------------------------------------------
# Test parse() - Headings
# ---------------------------------------------------------------------------


class TestParseHeadings:
    """Test heading extraction and formatting."""

    @pytest.mark.asyncio
    async def test_parse_heading_1(self, parser, tmp_path):
        """Test Heading 1 is formatted with # symbol."""
        heading = make_mock_heading(text="Main Heading", level=1)
        doc = make_mock_document(paragraphs=[heading])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "# Main Heading" in text

    @pytest.mark.asyncio
    async def test_parse_heading_2(self, parser, tmp_path):
        """Test Heading 2 is formatted with ## symbol."""
        heading = make_mock_heading(text="Subheading", level=2)
        doc = make_mock_document(paragraphs=[heading])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "## Subheading" in text

    @pytest.mark.asyncio
    async def test_parse_multiple_heading_levels(self, parser, tmp_path):
        """Test document with multiple heading levels."""
        paragraphs = [
            make_mock_heading(text="Title", level=1),
            make_mock_heading(text="Section", level=2),
            make_mock_paragraph(text="Content"),
            make_mock_heading(text="Subsection", level=3),
        ]
        doc = make_mock_document(paragraphs=paragraphs)

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "# Title" in text
        assert "## Section" in text
        assert "### Subsection" in text

    @pytest.mark.asyncio
    async def test_parse_invalid_heading_style_defaults_to_h1(self, parser, tmp_path):
        """Test that invalid heading style defaults to Heading 1."""
        para = Mock()
        run = Mock()
        run.text = "Unknown"
        run.bold = False
        run.italic = False
        para.runs = [run]

        style = Mock()
        style.name = "InvalidHeading"
        para.style = style

        doc = make_mock_document(paragraphs=[para])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        # Invalid heading should not be formatted as heading
        assert "Unknown" in text


# ---------------------------------------------------------------------------
# Test parse() - Tables
# ---------------------------------------------------------------------------


class TestParseTables:
    """Test table extraction."""

    @pytest.mark.asyncio
    async def test_parse_simple_table(self, parser, tmp_path):
        """Test parsing a simple table."""
        table = make_mock_table(
            rows_data=[["Header 1", "Header 2"], ["Cell 1", "Cell 2"]]
        )
        doc = make_mock_document(tables=[table])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "Header 1" in text
        assert "Header 2" in text
        assert "Cell 1" in text
        assert "Cell 2" in text
        assert "|" in text  # Table separator

    @pytest.mark.asyncio
    async def test_parse_multiple_tables(self, parser, tmp_path):
        """Test parsing multiple tables."""
        table1 = make_mock_table(rows_data=[["A1", "A2"], ["B1", "B2"]])
        table2 = make_mock_table(rows_data=[["C1", "C2"], ["D1", "D2"]])
        doc = make_mock_document(tables=[table1, table2])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "A1" in text
        assert "B1" in text
        assert "C1" in text
        assert "D1" in text

    @pytest.mark.asyncio
    async def test_parse_table_with_multiple_columns(self, parser, tmp_path):
        """Test parsing table with many columns."""
        table = make_mock_table(
            rows_data=[
                ["Col1", "Col2", "Col3", "Col4"],
                ["Data1", "Data2", "Data3", "Data4"],
            ]
        )
        doc = make_mock_document(tables=[table])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        # Should have pipe separators between columns
        assert "Col1 | Col2 | Col3 | Col4" in text
        assert "Data1 | Data2 | Data3 | Data4" in text

    @pytest.mark.asyncio
    async def test_parse_table_with_empty_cells(self, parser, tmp_path):
        """Test parsing table with empty cells."""
        table = make_mock_table(rows_data=[["Data1", ""], ["", "Data2"]])
        doc = make_mock_document(tables=[table])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "Data1" in text
        assert "Data2" in text


# ---------------------------------------------------------------------------
# Test parse() - Complex documents
# ---------------------------------------------------------------------------


class TestParseComplexDocuments:
    """Test parsing complex documents with multiple elements."""

    @pytest.mark.asyncio
    async def test_parse_document_with_all_elements(self, parser, tmp_path):
        """Test parsing document with paragraphs, headings, and tables."""
        paragraphs = [
            make_mock_heading(text="Legal Agreement", level=1),
            make_mock_paragraph(text="This is a legal document."),
            make_mock_heading(text="Terms and Conditions", level=2),
            make_mock_paragraph(text="Clause 1: Payment terms"),
        ]

        table = make_mock_table(rows_data=[["Item", "Amount"], ["Service A", "$100"]])

        doc = make_mock_document(paragraphs=paragraphs, tables=[table])

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        assert "# Legal Agreement" in text
        assert "## Terms and Conditions" in text
        assert "This is a legal document." in text
        assert "Item" in text
        assert "Amount" in text

    @pytest.mark.asyncio
    async def test_parse_preserves_document_order(self, parser, tmp_path):
        """Test that elements are extracted in document order."""
        doc = make_mock_document(
            paragraphs=[
                make_mock_paragraph(text="First"),
                make_mock_paragraph(text="Second"),
                make_mock_paragraph(text="Third"),
            ]
        )

        file_path = tmp_path / "test.docx"
        file_path.touch()

        with patch("services.parsers.word_parser.Document", return_value=doc):
            result = await parser.parse(file_path)

        text = "\n".join(result)
        first_pos = text.index("First")
        second_pos = text.index("Second")
        third_pos = text.index("Third")

        assert first_pos < second_pos < third_pos


# ---------------------------------------------------------------------------
# Test error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_parse_nonexistent_file(self, parser):
        """Test that FileNotFoundError is raised for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            await parser.parse(Path("/nonexistent/path.docx"))

    @pytest.mark.asyncio
    async def test_parse_directory_instead_of_file(self, parser, tmp_path):
        """Test that ValueError is raised when path is a directory."""
        dir_path = tmp_path / "directory"
        dir_path.mkdir()

        with pytest.raises(ValueError):
            await parser.parse(dir_path)

    @pytest.mark.asyncio
    async def test_file_validation_before_parsing(self, parser, tmp_path):
        """Test that file validation happens before attempting to parse."""
        # Create a file
        file_path = tmp_path / "test.docx"
        file_path.touch()

        # Delete it to simulate race condition
        file_path.unlink()

        with pytest.raises(FileNotFoundError):
            await parser.parse(file_path)


# ---------------------------------------------------------------------------
# Test helper methods
# ---------------------------------------------------------------------------


class TestHelperMethods:
    """Test helper/private methods."""

    def test_extract_paragraph_text_single_run(self, parser):
        """Test _extract_paragraph_text with single run."""
        para = Mock()
        run = Mock()
        run.text = "Hello"
        run.bold = False
        run.italic = False
        para.runs = [run]

        result = parser._extract_paragraph_text(para)
        assert result == "Hello"

    def test_extract_paragraph_text_multiple_runs(self, parser):
        """Test _extract_paragraph_text with multiple runs."""
        para = Mock()

        run1 = Mock()
        run1.text = "Hello"
        run1.bold = False
        run1.italic = False

        run2 = Mock()
        run2.text = " World"
        run2.bold = False
        run2.italic = False

        para.runs = [run1, run2]

        result = parser._extract_paragraph_text(para)
        assert result == "Hello World"

    def test_get_heading_level(self, parser):
        """Test _get_heading_level extracts number correctly."""
        assert parser._get_heading_level("Heading 1") == 1
        assert parser._get_heading_level("Heading 2") == 2
        assert parser._get_heading_level("Heading 9") == 9

    def test_get_heading_level_invalid_format(self, parser):
        """Test _get_heading_level defaults to 1 for invalid format."""
        assert parser._get_heading_level("InvalidHeading") == 1
        assert parser._get_heading_level("Heading X") == 1


# ---------------------------------------------------------------------------
# Integration tests (optional, with real .docx files)
# ---------------------------------------------------------------------------


class TestWordParserIntegration:
    """Integration tests with real Word documents."""

    @requires_asset(SAMPLE_DOCX)
    @integration
    @pytest.mark.asyncio
    async def test_parse_real_docx_file(self, parser):
        """Test parsing a real .docx file."""
        result = await parser.parse(SAMPLE_DOCX)

        # Assert some content was extracted
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(page, str) for page in result)

    @integration
    @pytest.mark.asyncio
    async def test_parse_created_docx(self, parser, tmp_path):
        """Test parsing a .docx file created with python-docx."""
        try:
            from docx import Document as DocxDocument
        except ImportError:
            pytest.skip("python-docx not installed")

        # Create a test document
        doc = DocxDocument()
        doc.add_heading("Test Heading", level=1)
        doc.add_paragraph("Test paragraph content")

        table = doc.add_table(rows=2, cols=2)
        table.rows[0].cells[0].text = "Header 1"
        table.rows[0].cells[1].text = "Header 2"
        table.rows[1].cells[0].text = "Cell 1"
        table.rows[1].cells[1].text = "Cell 2"

        # Save document
        file_path = tmp_path / "test_generated.docx"
        doc.save(str(file_path))

        # Parse it
        result = await parser.parse(file_path)

        # Assert content
        text = "\n".join(result)
        assert "Test Heading" in text
        assert "Test paragraph content" in text
        assert "Header 1" in text
        assert "Cell 1" in text

    @integration
    @pytest.mark.asyncio
    async def test_parse_created_docx_accuracy(self, parser, tmp_path):
        """WER should be 0.0 for a python-docx generated document."""
        try:
            from docx import Document as DocxDocument
        except ImportError:
            pytest.skip("python-docx not installed")

        doc = DocxDocument()
        doc.add_heading("Service Agreement", level=1)
        doc.add_paragraph("This agreement is made on 2024-01-15 between the parties.")
        doc.add_heading("Terms", level=2)
        doc.add_paragraph("Payment shall be made within 30 days of invoice.")

        file_path = tmp_path / "test_accuracy.docx"
        doc.save(str(file_path))

        result = await parser.parse(file_path)
        actual_text = "\n".join(result) if isinstance(result, list) else result

        expected = (
            "# Service Agreement\n"
            "This agreement is made on 2024-01-15 between the parties.\n"
            "## Terms\n"
            "Payment shall be made within 30 days of invoice."
        )
        assert_text_accuracy(expected=expected, actual=actual_text, threshold=0.0)
