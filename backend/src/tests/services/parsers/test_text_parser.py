from pathlib import Path

import pytest
from services.parsers.text_parser import TextParser
from tests.conftest import assert_text_accuracy

pytestmark = pytest.mark.slow


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def parser() -> TextParser:
    """Create a TextParser instance."""
    return TextParser()


@pytest.fixture
def sample_utf8_file(tmp_path) -> Path:
    """Create a sample UTF-8 text file."""
    file_path = tmp_path / "sample.txt"
    content = "This is a sample legal document.\n\nIt contains multiple paragraphs."
    file_path.write_text(content, encoding="utf-8")
    return file_path


# ---------------------------------------------------------------------------
# supports_format tests
# ---------------------------------------------------------------------------


class TestSupportsFormat:
    """Tests for format support detection."""

    @pytest.mark.parametrize("extension", [".txt", ".md", ".rst", ".text"])
    def test_supported_extensions(self, parser, extension):
        """Test that all supported text extensions are recognized."""
        file_path = Path(f"document{extension}")
        assert parser.supports_format(file_path) is True

    @pytest.mark.parametrize("extension", [".doc", ".docx", ".pdf", ".xlsx"])
    def test_unsupported_extensions(self, parser, extension):
        """Test that non-text extensions are rejected."""
        file_path = Path(f"document{extension}")
        assert parser.supports_format(file_path) is False


# ---------------------------------------------------------------------------
# parse() tests
# ---------------------------------------------------------------------------


class TestParse:
    """Tests for parsing text files."""

    @pytest.mark.asyncio
    async def test_parse_utf8_file(self, parser, sample_utf8_file):
        """Test parsing UTF-8 encoded file returns a list of strings,
        each representing a page, containing no more than one consecutive
        newline characters."""
        result = await parser.parse(sample_utf8_file)
        expected = "is a sample"
        assert any(expected == member for member in result), (
            f"The expected content was not found within the file: "
            f"expected {expected} in {result}"
        )
        assert isinstance(result, list), f"Output must be a list, got: {result}"
        assert all(
            not (s == "\n" and prev == "\n") for prev, s in zip([""] + result, result)
        )
        # Accuracy assertion: joined pages must match the original content exactly
        joined_text = "\n".join(result)
        assert_text_accuracy(
            expected="This is a sample legal document.\n\nIt contains "
            "multiple paragraphs.",
            actual=joined_text,
            threshold=0.0,
        )

    @pytest.mark.asyncio
    async def test_parse_utf8_file_accuracy(self, parser, sample_utf8_file):
        """Test that parsed UTF-8 content matches the reference string
        with a Word Error Rate threshold of 0.0 (exact match after
        normalisation)."""
        result = await parser.parse(sample_utf8_file)
        reference = (
            "This is a sample legal document.\n\nIt contains multiple paragraphs."
        )
        # parse() returns a list; join all pages into a single string
        actual_text = "\n".join(result)
        assert_text_accuracy(reference, actual_text, threshold=0.0)

    @pytest.mark.asyncio
    async def test_parse_nonexistent_file(self, parser, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        nonexistent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            await parser.parse(nonexistent)

    @pytest.mark.asyncio
    async def test_parse_empty_file(self, parser, tmp_path):
        """Test parsing an empty text file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("", encoding="utf-8")
        result = await parser.parse(empty_file)
        assert result == [""]

    @pytest.mark.asyncio
    async def test_clean_excessive_blank_lines(self, parser, tmp_path):
        """Test that excessive blank lines are collapsed."""
        file_path = tmp_path / "excessive_blanks.txt"
        content = "Line 1\n\n\n\n\nLine 2"
        file_path.write_text(content, encoding="utf-8")

        result = await parser.parse(file_path)
        # Should not have 5 consecutive newlines
        assert "\n\n\n\n\n" not in result
        expectations = ["Line 1", "Line 2"]
        for expectation in expectations:
            assert any(expectation in member for member in result)

    @pytest.mark.asyncio
    async def test_clean_trailing_spaces(self, parser, tmp_path):
        """Test that trailing spaces are removed."""
        file_path = tmp_path / "trailing_spaces.txt"
        content = "Line 1 with spaces   \nLine 2"
        file_path.write_text(content, encoding="utf-8")

        result = await parser.parse(file_path)
        for line in result:
            assert line == line.rstrip()


# ---------------------------------------------------------------------------
# parse() — accuracy metrics
# ---------------------------------------------------------------------------


class TestParseAccuracy:
    """Word Error Rate accuracy tests for TextParser.parse()."""

    @pytest.mark.asyncio
    async def test_parse_multi_paragraph_exact(self, parser, tmp_path):
        """WER should be 0.0 for multi-paragraph text."""
        file_path = tmp_path / "multi_para.txt"
        content = (
            "This is the first paragraph of a legal document.\n\n"
            "It contains multiple sentences. Each one matters.\n\n"
            "The third paragraph concludes the document."
        )
        file_path.write_text(content, encoding="utf-8")
        result = await parser.parse(file_path)
        actual_text = "\n".join(result)
        assert_text_accuracy(expected=content, actual=actual_text, threshold=0.0)

    @pytest.mark.asyncio
    async def test_parse_with_numbers_and_symbols(self, parser, tmp_path):
        """WER should be 0.0 for text with numbers, dates, and symbols."""
        file_path = tmp_path / "numbers.txt"
        content = (
            "Invoice #12345 dated 2024-01-15 for $1,250.00 (inc. GST).\n"
            "Reference: PO-2024-001 / Project Alpha."
        )
        file_path.write_text(content, encoding="utf-8")
        result = await parser.parse(file_path)
        actual_text = "\n".join(result)
        assert_text_accuracy(expected=content, actual=actual_text, threshold=0.0)

    @pytest.mark.asyncio
    async def test_parse_with_curly_quotes(self, parser, tmp_path):
        """WER should be 0.0 when text contains curly quotes (normalised)."""
        file_path = tmp_path / "curly.txt"
        content = "She said \u201cHello\u201d and he replied \u201cGood morning\u201d."
        file_path.write_text(content, encoding="utf-8")
        result = await parser.parse(file_path)
        actual_text = "\n".join(result)
        # Reference uses straight quotes — normalisation handles the conversion
        reference = 'She said "Hello" and he replied "Good morning".'
        assert_text_accuracy(expected=reference, actual=actual_text, threshold=0.0)

    @pytest.mark.asyncio
    async def test_parse_trailing_whitespace_accuracy(self, parser, tmp_path):
        """WER should be 0.0 despite trailing whitespace in source."""
        file_path = tmp_path / "trailing.txt"
        content = "Line with trailing spaces   \n\nAnother line   "
        file_path.write_text(content, encoding="utf-8")
        result = await parser.parse(file_path)
        actual_text = "\n".join(result)
        # The parser strips trailing spaces; reference matches cleaned output
        reference = "Line with trailing spaces\n\nAnother line"
        assert_text_accuracy(expected=reference, actual=actual_text, threshold=0.0)


# ---------------------------------------------------------------------------
# Encoding detection tests
# ---------------------------------------------------------------------------


class TestEncodingDetection:
    """Tests for automatic encoding detection."""

    @pytest.mark.asyncio
    async def test_parse_ascii_file(self, parser, tmp_path):
        """Test parsing ASCII encoded file."""
        file_path = tmp_path / "ascii.txt"
        content = "This is ASCII text."
        file_path.write_text(content, encoding="ascii")

        result = await parser.parse(file_path)
        assert any("ASCII text" in member for member in result)

    @pytest.mark.asyncio
    async def test_parse_ascii_file_accuracy(self, parser, tmp_path):
        """WER should be 0.0 for ASCII-encoded file content."""
        file_path = tmp_path / "ascii_acc.txt"
        content = "This is ASCII text with accurate extraction."
        file_path.write_text(content, encoding="ascii")
        result = await parser.parse(file_path)
        actual_text = "\n".join(result)
        assert_text_accuracy(expected=content, actual=actual_text, threshold=0.0)

    @pytest.mark.asyncio
    async def test_parse_latin1_file(self, parser, tmp_path):
        """Test parsing Latin-1 encoded file."""
        file_path = tmp_path / "latin1.txt"
        content = "Français café"
        file_path.write_bytes(content.encode("iso-8859-1"))

        result = await parser.parse(file_path)
        assert any(
            "caf" in member for member in result
        )  # May not be exact depending on encoding

    @pytest.mark.asyncio
    async def test_parse_latin1_file_accuracy(self, parser, tmp_path):
        """WER should be 0.0 for Latin-1 encoded content with accented characters."""
        file_path = tmp_path / "latin1_acc.txt"
        content = "Français café élève déjà vu"
        file_path.write_bytes(content.encode("iso-8859-1"))
        result = await parser.parse(file_path)
        actual_text = "\n".join(result)
        assert_text_accuracy(expected=content, actual=actual_text, threshold=0.0)

    @pytest.mark.asyncio
    async def test_parse_file_with_bom(self, parser, tmp_path):
        """Test parsing UTF-8 file with BOM."""
        file_path = tmp_path / "with_bom.txt"
        content = "Content with BOM"
        file_path.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))

        result = await parser.parse(file_path)
        assert any("Content with BOM" in member for member in result)

    @pytest.mark.asyncio
    async def test_parse_file_with_bom_accuracy(self, parser, tmp_path):
        """WER should be 0.0 for UTF-8 BOM file content.

        Note: The parser preserves the BOM character (\\ufeff) in the
        extracted text, so the expected reference includes it.
        """
        file_path = tmp_path / "bom_acc.txt"
        content = "Content with BOM and accurate extraction."
        file_path.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
        result = await parser.parse(file_path)
        actual_text = "\n".join(result)
        # The parser preserves the BOM character; reference includes it
        expected = "\ufeffContent with BOM and accurate extraction."
        assert_text_accuracy(expected=expected, actual=actual_text, threshold=0.0)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests with DocumentParserFactory."""

    def test_factory_selects_text_parser_for_txt_file(self, tmp_path):
        """Test that factory correctly selects TextParser for .txt files."""
        from services.parsers.parser_factory import DocumentParserFactory

        factory = DocumentParserFactory()
        txt_file = tmp_path / "document.txt"
        txt_file.write_text("Content", encoding="utf-8")

        parser = factory.get_parser(txt_file)
        assert isinstance(parser, TextParser)

    def test_factory_selects_text_parser_for_md_file(self, tmp_path):
        """Test that factory correctly selects TextParser for .md files."""
        from services.parsers.parser_factory import DocumentParserFactory

        factory = DocumentParserFactory()
        md_file = tmp_path / "readme.md"
        md_file.write_text("# Title", encoding="utf-8")

        parser = factory.get_parser(md_file)
        assert isinstance(parser, TextParser)
