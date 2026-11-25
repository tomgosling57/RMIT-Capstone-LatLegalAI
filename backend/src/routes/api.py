"""
Consolidated API routes for the LatMatrix backend.

All routes are registered under the ``/api/`` prefix and are defined in a
single module for clarity and maintainability.

- **Endpoint:** ``/api/documents/extract-text``
  **Purpose:** Pure text extraction, dev-only (conditional registration)

- **Endpoint:** ``/api/documents/extract-entities``
  **Purpose:** Text + spaCy NER entities

- **Endpoint:** ``/api/documents/extract``
  **Purpose:** Text + spaCy NER entities + clause classification (no LLM)

- **Endpoint:** ``/api/documents/summarize``
  **Purpose:** LLM summarisation from a previously extracted file_id or direct text

- **Endpoint:** ``/api/documents/analyze``
  **Purpose:** Full pipeline: text + entities + LLM summary

- **Endpoint:** ``/api/documents/analyze/stream``
  **Purpose:** Streaming LLM summary via SSE

- **Endpoint:** ``/api/chat/process``
  **Purpose:** Future: combined file upload + chat prompt
"""

import json
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from controllers.document import DocumentController
from services.file_handler import file_to_string
from services.llm_backend import get_llm_backend
from services.nlp_processor import NLPService
from services.text_utils import clean_and_squash_text
from services.file_saver import FileSaver
from services.parsers.pdf_type_detector import detect_pdf_type
from schemas import SummarizeRequest

logger = logging.getLogger(__name__)

fs = FileSaver()

# Module-level NLPService instance (spaCy model loaded once, reused across requests)
_nlp_service: NLPService | None = None


def _get_nlp_service() -> NLPService:
    """Return a shared NLPService singleton, loading it on first call."""
    global _nlp_service
    if _nlp_service is None:
        _nlp_service = NLPService()
    return _nlp_service


def controller_factory():
    """
    Factory function to create controller with necessary
    database dependencies.
    Any objects with database dependent code should be
    initialized here with a shared database session.
    """
    return DocumentController(fs)


# ---------------------------------------------------------------------------
# Main router -- always registered
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api")


@router.post("/documents/extract-entities")
async def extract_text_and_entities(
    file: UploadFile = File(), extraction_mode: str = Form("flow")
):
    """
    Extract text and spaCy NER entities from an uploaded document.

    Replaces the legacy ``/upload`` and ``/extract-text-entities`` endpoints.
    """
    controller = controller_factory()
    return await controller.upload_file(file, extraction_mode)


@router.post("/documents/extract")
async def extract_document(
    file: UploadFile = File(), extraction_mode: str = Form("flow")
):
    """
    Upload a file, extract text, run NLP pipeline (entities + clauses),
    and return immediately without LLM summarisation.

    This is the backend for the "Extracted Text" tab in the frontend.
    The response includes extracted text, NLP entities, clause classifications,
    and file metadata — everything needed to populate the tab without waiting
    for an LLM summary.

    **Request:** ``multipart/form-data`` with a ``file`` field and optional
    ``extraction_mode`` (``"flow"``, ``"column"``, or ``"ocr"``).

    **Success Response (200):** See ``ExtractDocumentResponse`` schema.
    **Error Responses:** 400 (file parsing), 413 (file too large),
    500 (entity extraction failure — text still returned).
    """
    controller = controller_factory()
    return await controller.extract_document(file, extraction_mode)


@router.post("/documents/summarize")
async def summarize_document(
    request: SummarizeRequest,
):
    """
    Generate an LLM summary from a previously extracted document.

    Accepts a JSON body with either a ``file_id`` (to re-read a previously
    saved file) or direct ``text`` content.  The LLM backend generates a
    comprehensive plain-English summary and extracts key entities.

    **Request (JSON):**

    .. code-block:: json

        {
            "file_id": "abc123def456.pdf",
            "max_tokens": 4096
        }

    Or with direct text:

    .. code-block:: json

        {
            "text": "Full cleaned document text...",
            "entities": {"names": [...], "dates": [...], "locations": [...]},
            "max_tokens": 4096
        }

    **Success Response (200):**

    .. code-block:: json

        {
            "success": true,
            "summary": "This agreement between...",
            "llm_entities": "Parties: ACME Corp, Beta Ltd\\nDates: January 1, 2024",
            "file_id": "abc123def456.pdf",
            "processing_time_ms": 4523.12
        }

    **Error Responses:**
    - 404 — ``FILE_NOT_FOUND`` (file_id doesn't exist or was cleaned up)
    - 422 — ``VALIDATION_ERROR`` (neither file_id nor text provided)
    - 503 — ``LLM_BACKEND_ERROR`` (LLM unavailable)
    - 500 — ``INTERNAL_ERROR`` (unexpected failure)
    """
    controller = controller_factory()
    return await controller.summarize_document(request)


@router.post("/documents/analyze")
async def analyze_document(
    file: UploadFile = File(), extraction_mode: str = Form("flow")
):
    """
    Full pipeline: text extraction + entity extraction + LLM summarization.
    """
    controller = controller_factory()
    return await controller.analyze_document(file, extraction_mode)


@router.post("/documents/analyze/stream")
async def stream_summary(
    file: UploadFile = File(), extraction_mode: str = Form("flow")
):
    """
    Streaming endpoint that analyzes a document and streams the LLM summary
    back to the client via Server-Sent Events (SSE).
    """
    controller = controller_factory()

    # Read file bytes
    file_bytes = await file.read()
    file_path = controller.file_saver.save_file(file_bytes, file.filename)

    # Extract file ID from the file path (UUID portion)
    file_id = file_path.name

    # Get current UTC timestamp in ISO 8601 format
    upload_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    nlp = _get_nlp_service()

    async def generate_stream():
        """Async generator function to stream the LLM summary."""
        try:
            # Extract text
            text_pages = await file_to_string(file_path, file.filename, extraction_mode)
            processed_text = clean_and_squash_text(text_pages)
            cleaned_text = nlp.clean_text(processed_text)

            # Detect PDF type (only meaningful for PDF files; returns UNKNOWN otherwise)
            pdf_type = detect_pdf_type(file_path).value

            # First, send initial metadata
            metadata = {
                "type": "metadata",
                "filename": file.filename,
                "file_id": file_id,
                "upload_timestamp": upload_timestamp,
                "pdf_type": pdf_type,
            }
            yield f"data: {json.dumps(metadata)}\n\n"

            # Stream the summary
            llm_backend = get_llm_backend()
            for chunk in llm_backend.stream_complete(
                f"Please summarize this legal document:\n\n{cleaned_text}"
            ):
                chunk_response = {"type": "chunk", "content": chunk}
                yield f"data: {json.dumps(chunk_response)}\n\n"

            # Send final message with entities
            final_summary = llm_backend.summarise(cleaned_text)

            # Handle both dict and string return formats
            if isinstance(final_summary, dict):
                summary_text = final_summary.get("summary", "")
                entities_text = final_summary.get("entities", "")
            else:
                # Parse string format: "Summary: {summary}\nEntities: {entities}"
                summary_text = ""
                entities_text = ""
                if final_summary:
                    lines = final_summary.split("\n")
                    for line in lines:
                        if line.startswith("Summary:"):
                            summary_text = line[len("Summary:") :].strip()
                        elif line.startswith("Entities:"):
                            entities_text = line[len("Entities:") :].strip()

            final_response = {
                "type": "complete",
                "summary": summary_text,
                "entities": entities_text,
            }
            yield f"data: {json.dumps(final_response)}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/chat/process")
async def chat_process(
    file: UploadFile = File(),
    prompt: str = Form(""),
    extraction_mode: str = Form("flow"),
):
    """
    **Future**: Combined file upload + chat prompt in one request.

    Currently returns a placeholder response indicating this endpoint
    is not yet fully implemented.

    Args:
        file: Uploaded document file
        prompt: User's chat prompt about the document
        extraction_mode: Extraction mode for text extraction
    """
    controller = controller_factory()
    return await controller.chat_process(file, prompt, extraction_mode)


# ---------------------------------------------------------------------------
# Dev-only router -- only registered when DEV_MODE=true
# ---------------------------------------------------------------------------
dev_router = APIRouter(prefix="/api")


@dev_router.post("/documents/extract-text")
async def extract_text(file: UploadFile = File(), extraction_mode: str = Form("flow")):
    """
    Pure text extraction endpoint.

    **Dev-only**: This endpoint is only registered when the ``DEV_MODE``
    environment variable is set to ``"true"``.  It performs text extraction
    **without** entity extraction or LLM summarization.
    """
    controller = controller_factory()
    return await controller.extract_text(file, extraction_mode)


def should_register_dev_routes() -> bool:
    """
    Return ``True`` if dev-only routes should be registered.

    Controlled by the ``DEV_MODE`` environment variable (case-insensitive).
    """
    return os.getenv("DEV_MODE", "").strip().lower() == "true"
