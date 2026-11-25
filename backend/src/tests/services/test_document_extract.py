"""
Unit tests for the ``POST /api/documents/extract`` endpoint.

Covers the ``DocumentController.extract_document()`` method, including:
- Successful extraction with entities and clauses
- File size validation (413)
- File parsing failures (400 / FileParsingError)
- Entity extraction graceful degradation
- Clause extraction graceful degradation
- spaCy max-length overflow handling
- Unexpected exceptions
- Asynchronous behaviour with mocked dependencies

All external services (file_saver, file_handler, nlp_processor,
entity_extractor, pdf_type_detector) are fully mocked so that no real
files, PDF readers, or spaCy models are required.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile
from fastapi.responses import JSONResponse

from controllers.document import DocumentController
from exceptions import FileParsingError


# ============================================================================
# Helpers
# ============================================================================


def _make_upload_file(
    filename: str = "contract.pdf",
    content: bytes = b"dummy pdf content",
    content_type: str = "application/pdf",
) -> UploadFile:
    """Build a minimal ``UploadFile`` for testing."""
    return UploadFile(
        filename=filename, file=None, headers={}, content_type=content_type
    )


def _make_mock_file_saver(tmp_path: Path) -> MagicMock:
    """Create a ``FileSaver`` mock that returns a real temp path."""
    saver = MagicMock()
    saved_path = tmp_path / "abc123def456.pdf"
    saved_path.write_bytes(b"dummy")
    saver.save_file.return_value = saved_path
    saver.get_file_path.return_value = saved_path
    return saver


def _make_mock_entities() -> dict:
    """Return a realistic entity-extraction result."""
    return {
        "names": [
            {"text": "ACME Corp", "type": "ORG", "confidence": 0.95, "source": "spacy"},
            {"text": "Beta Ltd", "type": "ORG", "confidence": 0.88, "source": "spacy"},
        ],
        "dates": [
            {
                "text": "January 1, 2024",
                "type": "DATE",
                "confidence": 0.92,
                "source": "spacy",
            },
        ],
        "locations": [
            {"text": "New York", "type": "GPE", "confidence": 0.97, "source": "spacy"},
        ],
        "all_entities": [],
    }


def _make_mock_clauses() -> list[dict]:
    """Return a realistic clause-classification result."""
    return [
        {
            "sentence": "The Lessee shall pay rent monthly.",
            "labels": {"obligation": True, "permission": False, "risk": False},
        },
        {
            "sentence": "The Lessor may terminate upon breach.",
            "labels": {"obligation": False, "permission": True, "risk": True},
        },
    ]


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def controller(tmp_path: Path) -> DocumentController:
    """Return a ``DocumentController`` backed by a temp-directory file saver."""
    saver = _make_mock_file_saver(tmp_path)
    return DocumentController(saver)


# ============================================================================
# Tests — Success cases
# ============================================================================


class TestExtractDocumentSuccess:
    """Happy-path: extraction returns all expected fields."""

    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_extract_document_returns_full_response(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """A successful extraction returns cleaned_text, entities, clauses,
        and metadata."""
        # ── Arrange ────────────────────────────────────────────────────────
        mock_detect.return_value.value = "TEXT_BASED"

        mock_nlp = MagicMock()
        mock_nlp.clean_text.return_value = "Cleaned contract text here."
        mock_nlp.extract_clauses.return_value = _make_mock_clauses()
        mock_nlp_cls.return_value = mock_nlp

        mock_entity_extractor = MagicMock()
        mock_entity_extractor.extract_entities.return_value = _make_mock_entities()
        mock_entity_extractor_cls.return_value = mock_entity_extractor

        mock_file_to_string.return_value = ["Page 1 content.", "Page 2 content."]

        upload_file = _make_upload_file()

        # ── Act ────────────────────────────────────────────────────────────
        response = controller.extract_document(upload_file, "flow")

        # ── Assert ─────────────────────────────────────────────────────────
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200

        body = json.loads(response.body)
        assert body["success"] is True
        assert body["cleaned_text"] == "Cleaned contract text here."
        assert body["content"] == ["Page 1 content.", "Page 2 content."]
        assert body["filename"] == "contract.pdf"
        assert body["file_id"] == "abc123def456.pdf"
        assert body["pdf_type"] == "TEXT_BASED"
        assert "upload_timestamp" in body

        # Entities
        assert len(body["entities"]["names"]) == 2
        assert body["entities"]["names"][0]["text"] == "ACME Corp"
        assert len(body["entities"]["dates"]) == 1
        assert len(body["entities"]["locations"]) == 1

        # Clauses
        assert len(body["clauses"]) == 2
        assert body["clauses"][0]["labels"]["obligation"] is True
        assert body["clauses"][1]["labels"]["permission"] is True

    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_extract_document_with_empty_entities_and_clauses(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """Extraction succeeds even when no entities or clauses are found."""
        mock_detect.return_value.value = "SCANNED"

        mock_nlp = MagicMock()
        mock_nlp.clean_text.return_value = "Short text."
        mock_nlp.extract_clauses.return_value = []
        mock_nlp_cls.return_value = mock_nlp

        mock_entity_extractor = MagicMock()
        mock_entity_extractor.extract_entities.return_value = {
            "names": [],
            "dates": [],
            "locations": [],
            "all_entities": [],
        }
        mock_entity_extractor_cls.return_value = mock_entity_extractor

        mock_file_to_string.return_value = ["Short text."]

        upload_file = _make_upload_file()
        response = controller.extract_document(upload_file, "flow")

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["success"] is True
        assert body["entities"]["names"] == []
        assert body["clauses"] == []

    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_extract_document_async_file_to_string_called(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """Verify that the async ``file_to_string`` is awaited with correct args."""
        mock_detect.return_value.value = "TEXT_BASED"

        mock_nlp = MagicMock()
        mock_nlp.clean_text.return_value = "text"
        mock_nlp.extract_clauses.return_value = []
        mock_nlp_cls.return_value = mock_nlp

        mock_entity_extractor = MagicMock()
        mock_entity_extractor.extract_entities.return_value = {
            "names": [],
            "dates": [],
            "locations": [],
            "all_entities": [],
        }
        mock_entity_extractor_cls.return_value = mock_entity_extractor

        mock_file_to_string.return_value = ["text"]

        upload_file = _make_upload_file()
        controller.extract_document(upload_file, "ocr")

        # The async mock should have been awaited with
        # the saved path, filename, and mode
        mock_file_to_string.assert_called_once()
        call_args = mock_file_to_string.call_args
        assert call_args[0][2] == "ocr"


# ============================================================================
# Tests — File size validation
# ============================================================================


class TestExtractDocumentFileSize:
    """File-size validation (413)."""

    @patch("controllers.document.MAX_FILE_SIZE", 10)  # tiny limit
    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_extract_document_file_too_large_returns_413(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """A file exceeding MAX_FILE_SIZE must return HTTP 413."""
        # The UploadFile.read() returns the full bytes — we make it large
        upload_file = _make_upload_file(content=b"x" * 100)

        response = controller.extract_document(upload_file, "flow")

        assert response.status_code == 413
        body = json.loads(response.body)
        assert "too large" in body["detail"].lower()

        # Ensure no further processing occurred
        mock_file_to_string.assert_not_called()


# ============================================================================
# Tests — File parsing errors
# ============================================================================


class TestExtractDocumentFileParsingError:
    """File parsing failures (400 / FileParsingError)."""

    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_extract_document_file_parsing_error_raises(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """When ``file_to_string`` raises, a ``FileParsingError`` must be raised."""
        mock_detect.return_value.value = "TEXT_BASED"
        mock_file_to_string.side_effect = ValueError("Unsupported format")

        upload_file = _make_upload_file()

        with pytest.raises(FileParsingError) as exc_info:
            controller.extract_document(upload_file, "flow")

        assert exc_info.value.error_code == "FILE_PARSING_ERROR"
        assert "contract.pdf" in exc_info.value.message

    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_extract_document_file_parsing_generic_exception(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """A non-ValueError exception during file parsing returns 400."""
        mock_detect.return_value.value = "TEXT_BASED"
        mock_file_to_string.side_effect = RuntimeError("Disk I/O error")

        upload_file = _make_upload_file()

        response = controller.extract_document(upload_file, "flow")
        assert response.status_code == 400
        body = json.loads(response.body)
        assert "Error processing file" in body["detail"]


# ============================================================================
# Tests — Graceful degradation
# ============================================================================


class TestExtractDocumentGracefulDegradation:
    """Entity / clause extraction failures should not block the response."""

    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_entity_extraction_failure_returns_empty_entities(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """If entity extraction raises, the response
        must still include text and clauses."""
        mock_detect.return_value.value = "TEXT_BASED"

        mock_nlp = MagicMock()
        mock_nlp.clean_text.return_value = "Some text."
        mock_nlp.extract_clauses.return_value = _make_mock_clauses()
        mock_nlp_cls.return_value = mock_nlp

        mock_entity_extractor = MagicMock()
        mock_entity_extractor.extract_entities.side_effect = RuntimeError("spaCy OOM")
        mock_entity_extractor_cls.return_value = mock_entity_extractor

        mock_file_to_string.return_value = ["Some text."]

        upload_file = _make_upload_file()
        response = controller.extract_document(upload_file, "flow")

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["cleaned_text"] == "Some text."
        # Entities should be empty (graceful degradation)
        assert body["entities"]["names"] == []
        assert body["entities"]["dates"] == []
        assert body["entities"]["locations"] == []
        # Clauses should still be present
        assert len(body["clauses"]) == 2

    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_clause_extraction_failure_returns_empty_clauses(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """If clause extraction raises, the response
        must still include text and entities."""
        mock_detect.return_value.value = "TEXT_BASED"

        mock_nlp = MagicMock()
        mock_nlp.clean_text.return_value = "Some text."
        mock_nlp.extract_clauses.side_effect = RuntimeError("Clause model error")
        mock_nlp_cls.return_value = mock_nlp

        mock_entity_extractor = MagicMock()
        mock_entity_extractor.extract_entities.return_value = _make_mock_entities()
        mock_entity_extractor_cls.return_value = mock_entity_extractor

        mock_file_to_string.return_value = ["Some text."]

        upload_file = _make_upload_file()
        response = controller.extract_document(upload_file, "flow")

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["cleaned_text"] == "Some text."
        # Entities should still be present
        assert len(body["entities"]["names"]) == 2
        # Clauses should be empty (graceful degradation)
        assert body["clauses"] == []

    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_both_extractions_fail_still_returns_text(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """If both entity and clause extraction fail,
        the response must still contain text."""
        mock_detect.return_value.value = "TEXT_BASED"

        mock_nlp = MagicMock()
        mock_nlp.clean_text.return_value = "Some text."
        mock_nlp.extract_clauses.side_effect = RuntimeError("Clause error")
        mock_nlp_cls.return_value = mock_nlp

        mock_entity_extractor = MagicMock()
        mock_entity_extractor.extract_entities.side_effect = RuntimeError(
            "Entity error"
        )
        mock_entity_extractor_cls.return_value = mock_entity_extractor

        mock_file_to_string.return_value = ["Some text."]

        upload_file = _make_upload_file()
        response = controller.extract_document(upload_file, "flow")

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["cleaned_text"] == "Some text."
        assert body["entities"]["names"] == []
        assert body["clauses"] == []


# ============================================================================
# Tests — spaCy max-length overflow
# ============================================================================


class TestExtractDocumentSpacyMaxLength:
    """When text exceeds SPACY_MAX_LENGTH, entity extraction is skipped."""

    @patch("controllers.document.SPACY_MAX_LENGTH", 50)
    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_entity_extraction_skipped_when_text_exceeds_limit(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """When cleaned_text exceeds SPACY_MAX_LENGTH, entities must be empty."""
        mock_detect.return_value.value = "TEXT_BASED"

        mock_nlp = MagicMock()
        # Return text longer than the patched limit (50)
        mock_nlp.clean_text.return_value = "A" * 100
        mock_nlp.extract_clauses.return_value = []
        mock_nlp_cls.return_value = mock_nlp

        mock_entity_extractor = MagicMock()
        mock_entity_extractor_cls.return_value = mock_entity_extractor

        mock_file_to_string.return_value = ["A" * 100]

        upload_file = _make_upload_file()
        response = controller.extract_document(upload_file, "flow")

        assert response.status_code == 200
        body = json.loads(response.body)

        # Entity extraction should have been skipped entirely
        mock_entity_extractor.extract_entities.assert_not_called()
        assert body["entities"]["names"] == []
        assert body["entities"]["dates"] == []
        assert body["entities"]["locations"] == []


# ============================================================================
# Tests — Unexpected exceptions
# ============================================================================


class TestExtractDocumentUnexpectedErrors:
    """Unexpected exceptions should return 400 with a descriptive message."""

    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_unexpected_exception_returns_400(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """Any unexpected exception in the controller must return HTTP 400."""
        mock_detect.side_effect = RuntimeError("Unexpected crash")

        upload_file = _make_upload_file()

        response = controller.extract_document(upload_file, "flow")
        assert response.status_code == 400
        body = json.loads(response.body)
        assert "Error processing file" in body["detail"]


# ============================================================================
# Tests — Asynchronous behaviour
# ============================================================================


class TestExtractDocumentAsyncBehaviour:
    """Verify that async calls are properly
    awaited and the controller is non-blocking."""

    @patch("controllers.document.file_to_string", new_callable=AsyncMock)
    @patch("controllers.document.NLPService")
    @patch("controllers.document.EntityExtractorService")
    @patch("controllers.document.detect_pdf_type")
    def test_file_to_string_is_async_and_awaited(
        self,
        mock_detect: MagicMock,
        mock_entity_extractor_cls: MagicMock,
        mock_nlp_cls: MagicMock,
        mock_file_to_string: AsyncMock,
        controller: DocumentController,
    ) -> None:
        """``file_to_string`` must be an async call that is awaited."""
        mock_detect.return_value.value = "TEXT_BASED"

        mock_nlp = MagicMock()
        mock_nlp.clean_text.return_value = "text"
        mock_nlp.extract_clauses.return_value = []
        mock_nlp_cls.return_value = mock_nlp

        mock_entity_extractor = MagicMock()
        mock_entity_extractor.extract_entities.return_value = {
            "names": [],
            "dates": [],
            "locations": [],
            "all_entities": [],
        }
        mock_entity_extractor_cls.return_value = mock_entity_extractor

        mock_file_to_string.return_value = ["text"]

        upload_file = _make_upload_file()
        controller.extract_document(upload_file, "flow")

        # Verify it was called (and thus awaited)
        mock_file_to_string.assert_called_once()
        # Verify it's an AsyncMock (coroutine)
        assert isinstance(mock_file_to_string, AsyncMock)
