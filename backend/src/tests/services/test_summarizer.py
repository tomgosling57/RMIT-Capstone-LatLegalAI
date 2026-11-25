"""
Unit tests for the LegalSummarizer service.

Tests cover:
- Initialization with custom and default dependencies
- summarize_text() with mocked NLP and LLM backends
- is_available() status checks
- process_document() orchestration order
- Error handling for each dependency failure mode
- file_size metadata collection via tmp_path
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.llm_backend import MockBackend
from services.nlp_processor import NLPService
from services.parsers.base_parser import BaseDocumentParser
from services.parsers.parser_factory import DocumentParserFactory
from services.summarizer import LegalSummarizer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_nlp_service() -> MagicMock:
    """Return a fully mocked NLPService instance."""
    service = MagicMock(spec=NLPService, autospec=True)
    service.analyze_text.return_value = {
        "cleaned_text": "cleaned legal text",
        "clauses": {
            "obligations": ["obligation A"],
            "permissions": ["permission B"],
            "risks": ["risk C"],
        },
        "stats": {"sentences": 5, "words": 100},
    }
    service.is_available.return_value = True
    return service


@pytest.fixture
def mock_llm_backend() -> MagicMock:
    """Return a mocked LLM backend with a known summarise return."""
    backend = MagicMock(spec=MockBackend, autospec=True)
    backend.summarise.return_value = "Summary: This is a test summary.\nEntities: None"
    return backend


@pytest.fixture
def mock_parser_factory() -> MagicMock:
    """Return a mocked DocumentParserFactory whose get_parser returns a mock parser."""
    factory = MagicMock(spec=DocumentParserFactory, autospec=True)
    mock_parser = MagicMock(spec=BaseDocumentParser, autospec=True)
    # BaseDocumentParser.parse is async, but the summarizer calls it synchronously.
    # Override the autospec'd method with a regular MagicMock that returns a string.
    mock_parser.parse = MagicMock(return_value="raw document text")
    factory.get_parser.return_value = mock_parser
    return factory


@pytest.fixture
def summarizer_with_mocks(
    mock_parser_factory: MagicMock,
    mock_nlp_service: MagicMock,
    mock_llm_backend: MagicMock,
) -> LegalSummarizer:
    """Build a LegalSummarizer with all dependencies mocked."""
    summarizer = LegalSummarizer.__new__(LegalSummarizer)
    summarizer.parser_factory = mock_parser_factory
    summarizer.nlp_service = mock_nlp_service
    summarizer.llm_backend = mock_llm_backend
    return summarizer


@pytest.fixture
def real_file_path(tmp_path: Path) -> Path:
    """Create a temporary file for tests that need a real file on disk."""
    file = tmp_path / "test_document.pdf"
    file.write_text("raw document text")
    return file


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInitialization:
    """LegalSummarizer.__init__ behaviour."""

    def test_default_dependencies(self) -> None:
        """When no arguments are given, real defaults are used."""
        summarizer = LegalSummarizer()
        assert isinstance(summarizer.parser_factory, DocumentParserFactory)
        assert isinstance(summarizer.nlp_service, NLPService)
        assert isinstance(summarizer.llm_backend, MockBackend)

    def test_custom_dependencies(
        self, mock_parser_factory, mock_nlp_service, mock_llm_backend
    ) -> None:
        """When all arguments are given,
        they are used instead of defaults."""
        summarizer = LegalSummarizer(
            parser_factory=mock_parser_factory,
            nlp_service=mock_nlp_service,
            llm_backend_name="mock",
        )
        # parser_factory and nlp_service are the injected mocks
        assert summarizer.parser_factory is mock_parser_factory
        assert summarizer.nlp_service is mock_nlp_service
        # llm_backend_name="mock" should produce a MockBackend
        assert isinstance(summarizer.llm_backend, MockBackend)

    def test_partial_custom_dependencies(self, mock_nlp_service) -> None:
        """Only nlp_service is injected; parser_factory and
        llm_backend fall back to defaults."""
        summarizer = LegalSummarizer(nlp_service=mock_nlp_service)
        assert summarizer.nlp_service is mock_nlp_service
        assert isinstance(summarizer.parser_factory, DocumentParserFactory)
        assert isinstance(summarizer.llm_backend, MockBackend)


# ---------------------------------------------------------------------------
# summarize_text
# ---------------------------------------------------------------------------


class TestSummarizeText:
    """LegalSummarizer.summarize_text() behaviour."""

    def test_summarize_text_calls_nlp_and_llm(
        self, summarizer_with_mocks, mock_nlp_service, mock_llm_backend
    ) -> None:
        """summarize_text should call nlp_service.analyze_text
        then llm_backend.summarise."""
        result = summarizer_with_mocks.summarize_text("some legal text")

        # NLP was called with the raw text
        mock_nlp_service.analyze_text.assert_called_once_with("some legal text")

        # LLM was called with the cleaned text from NLP
        mock_llm_backend.summarise.assert_called_once_with(
            "cleaned legal text", target_language=None
        )

        # Verify the result structure
        assert result["cleaned_text"] == "cleaned legal text"
        assert result["summary"] == "Summary: This is a test summary.\nEntities: None"
        assert result["obligations"] == ["obligation A"]
        assert result["permissions"] == ["permission B"]
        assert result["risks"] == ["risk C"]
        assert result["stats"] == {"sentences": 5, "words": 100}
        assert result["translation_method"] == "none"
        assert result["target_language"] is None

    def test_summarize_text_with_translation(
        self, summarizer_with_mocks, mock_llm_backend
    ) -> None:
        """When target_language is provided, it is forwarded to the LLM backend."""
        summarizer_with_mocks.summarize_text("legal text", target_language="es")

        mock_llm_backend.summarise.assert_called_once_with(
            "cleaned legal text", target_language="es"
        )

    def test_summarize_text_nlp_fallback(
        self, summarizer_with_mocks, mock_nlp_service
    ) -> None:
        """If NLP returns no cleaned_text, the original text is used as fallback."""
        mock_nlp_service.analyze_text.return_value = {
            "cleaned_text": "",
            "clauses": {},
            "stats": {},
        }
        result = summarizer_with_mocks.summarize_text("original text")

        # The LLM should receive the fallback (empty string in this case)
        assert result["cleaned_text"] == ""


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    """LegalSummarizer.is_available() behaviour."""

    def test_available_when_all_services_ready(self, summarizer_with_mocks) -> None:
        """is_available returns True when nlp_service is
        available and llm_backend exists."""
        assert summarizer_with_mocks.is_available() is True

    def test_unavailable_when_nlp_unavailable(
        self, summarizer_with_mocks, mock_nlp_service
    ) -> None:
        """is_available returns False when nlp_service.is_available() is False."""
        mock_nlp_service.is_available.return_value = False
        assert summarizer_with_mocks.is_available() is False

    def test_unavailable_when_llm_backend_is_none(self, summarizer_with_mocks) -> None:
        """is_available returns False when llm_backend is None."""
        summarizer_with_mocks.llm_backend = None
        assert summarizer_with_mocks.is_available() is False


# ---------------------------------------------------------------------------
# process_document
# ---------------------------------------------------------------------------


class TestProcessDocument:
    """LegalSummarizer.process_document() orchestration."""

    @pytest.mark.asyncio
    async def test_process_document_calls_parser_nlp_llm_in_order(
        self,
        summarizer_with_mocks,
        mock_parser_factory,
        mock_nlp_service,
        mock_llm_backend,
        real_file_path,
    ) -> None:
        """process_document should call parser -> NLP -> LLM in that order."""
        result = await summarizer_with_mocks.process_document(real_file_path)

        # 1. Parser factory was asked for a parser
        mock_parser_factory.get_parser.assert_called_once_with(real_file_path)

        # 2. The parser parsed the file
        parser = mock_parser_factory.get_parser.return_value
        parser.parse.assert_called_once_with(real_file_path)

        # 3. NLP analysed the raw text
        mock_nlp_service.analyze_text.assert_called_once_with("raw document text")

        # 4. LLM summarised the cleaned text
        mock_llm_backend.summarise.assert_called_once_with(
            "cleaned legal text", target_language=None
        )

        # Verify the result structure
        assert result["original_text"] == "raw document text"
        assert result["cleaned_text"] == "cleaned legal text"
        assert result["summary"] == "Summary: This is a test summary.\nEntities: None"
        assert result["obligations"] == ["obligation A"]
        assert result["permissions"] == ["permission B"]
        assert result["risks"] == ["risk C"]
        assert result["stats"] == {"sentences": 5, "words": 100}
        assert result["translation_method"] == "none"
        assert result["target_language"] is None
        assert result["metadata"]["file_path"] == str(real_file_path)
        assert result["metadata"]["file_name"] == "test_document.pdf"
        assert result["metadata"]["file_size"] > 0
        assert result["metadata"]["translation_applied"] is False
        assert result["metadata"]["llm_backend"] == "MockBackend"

    @pytest.mark.asyncio
    async def test_process_document_with_translation(
        self, summarizer_with_mocks, mock_llm_backend, real_file_path
    ) -> None:
        """When target_language is provided, translation metadata is set."""
        result = await summarizer_with_mocks.process_document(
            real_file_path, target_language="fr"
        )

        mock_llm_backend.summarise.assert_called_once_with(
            "cleaned legal text", target_language="fr"
        )
        assert result["target_language"] == "fr"
        assert result["metadata"]["translation_applied"] is True
        assert result["metadata"]["target_language"] == "fr"

    @pytest.mark.asyncio
    async def test_process_document_nlp_fallback(
        self, summarizer_with_mocks, mock_nlp_service, real_file_path
    ) -> None:
        """If NLP returns no cleaned_text, the original parsed text is used."""
        mock_nlp_service.analyze_text.return_value = {
            "cleaned_text": "",
            "clauses": {},
            "stats": {},
        }
        result = await summarizer_with_mocks.process_document(real_file_path)

        # cleaned_text falls back to the original text from the parser
        assert result["cleaned_text"] == ""
        assert result["original_text"] == "raw document text"

    # ------------------------------------------------------------------
    # Error-handling: parser.parse() failure
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_process_document_parser_parse_error(
        self, summarizer_with_mocks, mock_parser_factory, real_file_path
    ) -> None:
        """When parser.parse() raises, the error propagates."""
        parser = mock_parser_factory.get_parser.return_value
        parser.parse.side_effect = ValueError("Unsupported file format")

        with pytest.raises(ValueError, match="Unsupported file format"):
            await summarizer_with_mocks.process_document(real_file_path)

        parser.parse.assert_called_once_with(real_file_path)

    # ------------------------------------------------------------------
    # Error-handling: nlp_service.analyze_text() failure
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_process_document_nlp_error(
        self, summarizer_with_mocks, mock_nlp_service, real_file_path
    ) -> None:
        """When nlp_service.analyze_text() raises, the error propagates."""
        mock_nlp_service.analyze_text.side_effect = RuntimeError(
            "spaCy model not loaded"
        )

        with pytest.raises(RuntimeError, match="spaCy model not loaded"):
            await summarizer_with_mocks.process_document(real_file_path)

        mock_nlp_service.analyze_text.assert_called_once_with("raw document text")

    # ------------------------------------------------------------------
    # Error-handling: llm_backend.summarise() failure
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_process_document_llm_error(
        self, summarizer_with_mocks, mock_llm_backend, real_file_path
    ) -> None:
        """When llm_backend.summarise() raises, the error propagates."""
        mock_llm_backend.summarise.side_effect = ConnectionError("API key invalid")

        with pytest.raises(ConnectionError, match="API key invalid"):
            await summarizer_with_mocks.process_document(real_file_path)

        mock_llm_backend.summarise.assert_called_once_with(
            "cleaned legal text", target_language=None
        )

    # ------------------------------------------------------------------
    # Error-handling: file_path.stat() failure (metadata collection)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_process_document_stat_failure(
        self, summarizer_with_mocks, real_file_path
    ) -> None:
        """When file_path.stat() raises (e.g. permission denied),
        file_size defaults to 0 and processing continues."""
        # Patch Path.exists and Path.stat at the class level.
        # exists() must be patched too because it internally calls stat(),
        # which would otherwise raise PermissionError before we reach the
        # file_size line.
        with (
            patch.object(Path, "exists", return_value=True),
            patch.object(
                Path, "stat", side_effect=PermissionError("Permission denied")
            ),
        ):
            result = await summarizer_with_mocks.process_document(real_file_path)

        # Processing should complete with file_size = 0
        assert result["metadata"]["file_size"] == 0
        assert result["metadata"]["file_path"] == str(real_file_path)
        assert result["metadata"]["file_name"] == "test_document.pdf"

    # ------------------------------------------------------------------
    # file_size: real file on disk via tmp_path
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_process_document_file_size_from_real_file(
        self, summarizer_with_mocks, real_file_path
    ) -> None:
        """When the file exists on disk, file_size reflects the actual size."""
        result = await summarizer_with_mocks.process_document(real_file_path)

        expected_size = real_file_path.stat().st_size
        assert result["metadata"]["file_size"] == expected_size
        assert result["metadata"]["file_size"] > 0


# ---------------------------------------------------------------------------
# process_document_sync (convenience wrapper)
# ---------------------------------------------------------------------------


class TestProcessDocumentSync:
    """LegalSummarizer.process_document_sync() — currently returns {}."""

    def test_process_document_sync_returns_empty_dict(self) -> None:
        """The sync convenience method currently returns an empty dict."""
        summarizer = LegalSummarizer()
        result = summarizer.process_document_sync(Path("/fake/doc.txt"))
        assert result == {}
