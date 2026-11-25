"""API controller for uploading, storing and processing documents."""

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import File, UploadFile, Form
from fastapi.responses import JSONResponse

from services.file_handler import file_to_string
from services.nlp_processor import NLPService
from services.entity_extractor import EntityExtractorService
from services.text_utils import clean_and_squash_text
from services.llm_backend import get_llm_backend
from services.parsers.pdf_type_detector import detect_pdf_type
from exceptions import FileParsingError, LLMBackendError
from logging_config import get_logger, get_file_debug_logger, safe_extra
from config import MAX_FILE_SIZE, SPACY_MAX_LENGTH
from schemas import (
    ExtractDocumentResponse,
    EntityCollection,
    ClauseItem,
    SummarizeRequest,
    SummarizeResponse,
)

logger = get_logger(__name__)
debug_logger = get_file_debug_logger("document_debug")
nlp = NLPService()
entity_extractor = EntityExtractorService()
llm_backend = get_llm_backend()


class DocumentController:
    def __init__(self, file_saver):
        self.file_saver = file_saver

    async def upload_file(
        self,
        file: UploadFile = File(),
        extraction_mode: str = Form("flow"),
        min_confidence: float = 0.6,
    ) -> Dict[str, Any]:
        """
        Receives file from user, extracts text,
        cleans it, and extracts entities asynchronously.

        Args:
            file: Uploaded document file
            min_confidence:
            Minimum confidence threshold for extracted entities (default: 0.6)

        Returns:
            Dictionary with cleaned text and extracted entities with confidence scores
        """
        debug_logger.debug(
            "upload_file called",
            extra={
                "file_name": getattr(file, "filename", None),
                "extraction_mode": extraction_mode,
            },
        )
        try:
            debug_logger.debug("Attempting file.read()...")
            file_bytes = await file.read()
            debug_logger.debug(
                f"file.read() succeeded: {len(file_bytes)} bytes "
                f"({len(file_bytes) / (1024 * 1024):.1f}MB)"
            )

            # Check file size before processing
            if len(file_bytes) > MAX_FILE_SIZE:
                debug_logger.debug(
                    f"Size check triggered: {len(file_bytes)} > {MAX_FILE_SIZE} "
                    f"-> returning 413"
                )
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": (
                            f"File too large. Maximum allowed size is "
                            f"{MAX_FILE_SIZE // (1024 * 1024)}MB, "
                            f"but received {len(file_bytes) / (1024 * 1024):.1f}MB."
                        )
                    },
                )

            debug_logger.debug(
                f"Size check passed: {len(file_bytes)} <= {MAX_FILE_SIZE}"
            )

            file_path = self.file_saver.save_file(file_bytes, file.filename)

            # Extract file ID from the file path (UUID portion)
            file_id = file_path.name

            # Get current UTC timestamp in ISO 8601 format
            upload_timestamp = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            # Detect PDF type (only meaningful for PDF files; returns UNKNOWN otherwise)
            pdf_type = detect_pdf_type(file_path).value

            # Await the async file_to_string call to
            # get the extracted text
            text_pages = await file_to_string(file_path, file.filename, extraction_mode)

            # Process text for NLP: squash and remove page markers
            processed_text = clean_and_squash_text(text_pages)

            # Clean the processed text for NLP
            cleaned_text = nlp.clean_text(processed_text)

            # Check text length against spaCy's NLP model limit before
            # attempting entity extraction.  spaCy's default max_length is
            # 1,000,000 characters; texts beyond that raise ValueError.
            if len(cleaned_text) > SPACY_MAX_LENGTH:
                debug_logger.debug(
                    f"Text length ({len(cleaned_text)}) exceeds spaCy limit "
                    f"({SPACY_MAX_LENGTH}) — skipping entity extraction"
                )
                entities = {
                    "names": [],
                    "dates": [],
                    "locations": [],
                    "all_entities": [],
                }
            else:
                # Extract entities (names, dates, locations)
                entities = entity_extractor.extract_entities(
                    cleaned_text, min_confidence
                )

            debug_logger.debug("upload_file completed successfully")
            return JSONResponse(
                content={
                    "content": text_pages,
                    "entities": entities,
                    "filename": file.filename,
                    "file_id": file_id,
                    "upload_timestamp": upload_timestamp,
                    "pdf_type": pdf_type,
                    "status": "success",
                }
            )
        except ValueError as e:
            debug_logger.debug(f"ValueError caught: {e}", exc_info=True)
            # Return 400 for invalid files or unsupported formats
            return JSONResponse(
                status_code=400, content={"detail": f"Invalid file: {str(e)}"}
            )
        except Exception as e:
            debug_logger.debug(
                f"Exception caught (returning 400): {type(e).__name__}: {e}",
                exc_info=True,
            )
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            return JSONResponse(
                status_code=400, content={"detail": f"Error processing file: {str(e)}"}
            )

    async def analyze_document(
        self,
        file: UploadFile = File(),
        extraction_mode: str = Form("flow"),
        min_confidence: float = 0.6,
    ) -> Dict[str, Any]:
        """
        Receives file from user, extracts text, cleans it, extracts entities,
        and generates a summary using LLM.

        Handles errors gracefully:
        - File parsing errors return clear messages
        - LLM failures return partial results with extracted text and entities
        - Entity extraction errors are logged but don't block the response

        Args:
            file: Uploaded document file
            extraction_mode: Extraction mode for text extraction
            min_confidence: Minimum confidence threshold for
            extracted entities (default: 0.6)

        Returns:
            Dictionary with extracted text, entities, and summary

        Raises:
            FileParsingError: If the file cannot be parsed
        """
        try:
            file_bytes = await file.read()
            file_path = self.file_saver.save_file(file_bytes, file.filename)

            # Extract file ID from the file path (UUID portion)
            file_id = file_path.name

            # Get current UTC timestamp in ISO 8601 format
            upload_timestamp = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            # Detect PDF type (only meaningful for PDF files; returns UNKNOWN otherwise)
            pdf_type = detect_pdf_type(file_path).value

            # Await the async file_to_string call to get the extracted text
            try:
                text_pages = await file_to_string(
                    file_path, file.filename, extraction_mode
                )
            except Exception as e:
                logger.error(
                    f"File parsing failed for {file.filename}",
                    exc_info=True,
                    extra={
                        "filename": file.filename,
                        "file_size": len(file_bytes),
                        "extraction_mode": extraction_mode,
                    },
                )
                raise FileParsingError(
                    filename=file.filename,
                    reason=str(e),
                )

            # Process text for NLP: squash and remove page markers
            processed_text = clean_and_squash_text(text_pages)

            # Clean the processed text for NLP
            cleaned_text = nlp.clean_text(processed_text)

            # Extract entities (names, dates, locations)
            try:
                entities = entity_extractor.extract_entities(
                    cleaned_text, min_confidence
                )
            except Exception:
                logger.warning(
                    f"Entity extraction failed for {file.filename}",
                    exc_info=True,
                    extra={
                        "filename": file.filename,
                        "min_confidence": min_confidence,
                    },
                )
                # Continue without entities - don't fail the whole request
                entities = {}

            # Generate summary and extract entities using LLM
            # Pass pre-extracted entities (from spaCy NER) so the LLM can focus
            # on summarization rather than re-discovering entities from scratch
            llm_result = llm_backend.summarise(
                cleaned_text,
                pre_extracted_entities=entities,
            )

            # Parse the LLM response (could be dict or string)
            llm_summary = ""
            llm_entities = ""

            if isinstance(llm_result, dict):
                # If it's a dict (from base class or future implementations)
                llm_summary = llm_result.get("summary", "")
                llm_entities = llm_result.get("entities", "")
            elif isinstance(llm_result, str):
                # Parse the "Summary: ...\nEntities: ..." format.
                # The summarise() method already returns a string in the format:
                #   "Summary: ...\nEntities: ..."
                # (or the raw response if parsing failed).
                # We simply split on the known delimiter rather than re-parsing.
                summary_prefix = "Summary: "
                entities_prefix = "\nEntities: "
                if entities_prefix in llm_result:
                    parts = llm_result.split(entities_prefix, maxsplit=1)
                    summary_part = parts[0]
                    if summary_part.startswith(summary_prefix):
                        llm_summary = summary_part[len(summary_prefix) :]
                    else:
                        llm_summary = summary_part
                    llm_entities = parts[1]
                elif summary_prefix in llm_result:
                    # Only Summary: found, no Entities: delimiter
                    llm_summary = llm_result[len(summary_prefix) :]
                else:
                    # Neither prefix found — use the raw result as summary
                    llm_summary = llm_result

            logger.info(
                f"Document analyzed successfully: {file.filename}",
                extra=safe_extra(
                    filename=file.filename,
                    file_id=file_id,
                    text_length=len(cleaned_text),
                    entities_count=(len(entities) if isinstance(entities, dict) else 0),
                ),
            )

            return JSONResponse(
                content={
                    "success": True,
                    "content": text_pages,
                    "entities": entities,
                    "llm_summary": llm_summary,
                    "llm_entities": llm_entities,
                    "filename": file.filename,
                    "file_id": file_id,
                    "upload_timestamp": upload_timestamp,
                    "pdf_type": pdf_type,
                }
            )

        except FileParsingError:
            # Re-raise custom exceptions - they'll be handled by
            # global exception handlers
            raise
        except Exception:
            # Log any unexpected errors
            logger.error(
                f"Unexpected error during document analysis: {file.filename}",
                exc_info=True,
                extra=safe_extra(filename=file.filename),
            )
            raise

    async def extract_text(
        self, file: UploadFile = File(), extraction_mode: str = Form("flow")
    ) -> Dict[str, Any]:
        """
        Receives file from user, extracts text and
        cleans it.
        Accepts an extraction mode parameter for column
        compatibility or flow preservation.

        # TODO add dev mode conditional registratrion
        #  of this endpoint to prevent accidental use in production

        Args:
            file: Uploaded document file
            extraction_mode: Extraction mode for text extraction

        Returns:
            Dictionary with extracted text,
            filename, file ID, and upload timestamp
        """
        try:
            file_bytes = await file.read()
            file_path = self.file_saver.save_file(file_bytes, file.filename)

            # Extract file ID from the file path (UUID portion)
            file_id = file_path.name

            # Get current UTC timestamp in ISO 8601 format
            upload_timestamp = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            # Await the async file_to_string call to get the extracted text
            text_pages = await file_to_string(file_path, file.filename, extraction_mode)

            return JSONResponse(
                content={
                    "content": text_pages,
                    "filename": file.filename,
                    "file_id": file_id,
                    "upload_timestamp": upload_timestamp,
                    "status": "success",
                }
            )
        except ValueError as e:
            # Return 400 for invalid files or unsupported formats
            return JSONResponse(
                status_code=400, content={"detail": f"Invalid file: {str(e)}"}
            )
        except Exception as e:
            logger.error(f"Error extracting text from file {file.filename}: {str(e)}")
            return JSONResponse(
                status_code=400, content={"detail": f"Error processing file: {str(e)}"}
            )

    async def extract_document(
        self,
        file: UploadFile = File(),
        extraction_mode: str = Form("flow"),
        min_confidence: float = 0.6,
    ) -> JSONResponse:
        """
        Upload a file, extract text, run NLP pipeline (entities + clauses),
        and return immediately without LLM summarisation.

        This is the backend for the ``POST /api/documents/extract`` endpoint
        used by the "Extracted Text" tab in the frontend.

        Args:
            file: Uploaded document file
            extraction_mode: Extraction mode for text parsing ("flow", "column", "ocr")
            min_confidence: Minimum confidence threshold for extracted entities

        Returns:
            JSONResponse with extracted text, NLP entities, clause classifications,
            and file metadata.

        Raises:
            FileParsingError: If the file cannot be parsed
        """
        debug_logger.debug(
            "extract_document called",
            extra={
                "file_name": getattr(file, "filename", None),
                "extraction_mode": extraction_mode,
                "min_confidence": min_confidence,
            },
        )

        try:
            # ── 1. Read file bytes and validate size ──────────────────────
            file_bytes = await file.read()
            debug_logger.debug(
                f"file.read() succeeded: {len(file_bytes)} bytes "
                f"({len(file_bytes) / (1024 * 1024):.1f}MB)"
            )

            if len(file_bytes) > MAX_FILE_SIZE:
                debug_logger.debug(
                    f"Size check triggered: {len(file_bytes)} > {MAX_FILE_SIZE}"
                )
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": (
                            f"File too large. Maximum allowed size is "
                            f"{MAX_FILE_SIZE // (1024 * 1024)}MB, "
                            f"but received {len(file_bytes) / (1024 * 1024):.1f}MB."
                        )
                    },
                )

            # ── 2. Save file and generate file_id ─────────────────────────
            file_path = self.file_saver.save_file(file_bytes, file.filename)
            file_id = file_path.name

            upload_timestamp = datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )

            # Detect PDF type (only meaningful for PDF files; returns UNKNOWN otherwise)
            pdf_type = detect_pdf_type(file_path).value

            # ── 3. Extract text via parser pipeline ───────────────────────
            try:
                text_pages = await file_to_string(
                    file_path, file.filename, extraction_mode
                )
            except Exception as e:
                logger.error(
                    f"File parsing failed for {file.filename}",
                    exc_info=True,
                    extra={
                        "filename": file.filename,
                        "file_size": len(file_bytes),
                        "extraction_mode": extraction_mode,
                    },
                )
                raise FileParsingError(
                    filename=file.filename,
                    reason=str(e),
                )

            # ── 4. Clean and squash text for NLP ──────────────────────────
            processed_text = clean_and_squash_text(text_pages)
            cleaned_text = nlp.clean_text(processed_text)

            # ── 5. Extract entities (names, dates, locations) ─────────────
            entities: Dict[str, Any]
            try:
                if len(cleaned_text) > SPACY_MAX_LENGTH:
                    debug_logger.debug(
                        f"Text length ({len(cleaned_text)}) exceeds spaCy limit "
                        f"({SPACY_MAX_LENGTH}) — skipping entity extraction"
                    )
                    entities = {
                        "names": [],
                        "dates": [],
                        "locations": [],
                        "all_entities": [],
                    }
                else:
                    entities = entity_extractor.extract_entities(
                        cleaned_text, min_confidence
                    )
            except Exception as e:
                logger.warning(
                    f"Entity extraction failed for {file.filename}: {e}",
                    exc_info=True,
                )
                # Graceful degradation: return empty entities, still include text
                entities = {
                    "names": [],
                    "dates": [],
                    "locations": [],
                    "all_entities": [],
                }

            # ── 6. Extract clause classifications ─────────────────────────
            clauses: List[Dict[str, Any]] = []
            try:
                raw_clauses = nlp.extract_clauses(cleaned_text)
                # Convert to serialisable dicts (ClauseItem-compatible)
                clauses = [
                    {
                        "sentence": c["sentence"],
                        "labels": {
                            "obligation": c["labels"]["obligation"],
                            "permission": c["labels"]["permission"],
                            "risk": c["labels"]["risk"],
                        },
                    }
                    for c in raw_clauses
                ]
            except Exception as e:
                logger.warning(
                    f"Clause extraction failed for {file.filename}: {e}",
                    exc_info=True,
                )
                # Graceful degradation: return empty clauses
                clauses = []

            # ── 7. Build and return structured response ───────────────────
            response = ExtractDocumentResponse(
                success=True,
                content=text_pages,
                cleaned_text=cleaned_text,
                entities=EntityCollection(
                    names=entities.get("names", []),
                    dates=entities.get("dates", []),
                    locations=entities.get("locations", []),
                    all_entities=entities.get("all_entities", []),
                ),
                clauses=[ClauseItem(**c) for c in clauses],
                filename=file.filename,
                file_id=file_id,
                upload_timestamp=upload_timestamp,
                pdf_type=pdf_type,
            )

            logger.info(
                f"Document extracted successfully: {file.filename}",
                extra=safe_extra(
                    filename=file.filename,
                    file_id=file_id,
                    text_length=len(cleaned_text),
                    entities_count=len(entities.get("names", [])),
                    clauses_count=len(clauses),
                ),
            )

            return JSONResponse(content=response.model_dump())

        except FileParsingError:
            # Re-raise custom exceptions — handled by global exception handlers
            raise
        except ValueError as e:
            debug_logger.debug(f"ValueError caught: {e}", exc_info=True)
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid file: {str(e)}"},
            )
        except Exception as e:
            debug_logger.debug(
                f"Exception caught: {type(e).__name__}: {e}",
                exc_info=True,
            )
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"detail": f"Error processing file: {str(e)}"},
            )

    async def summarize_document(
        self,
        request: SummarizeRequest,
    ) -> JSONResponse:
        """
        Generate an LLM summary from a previously extracted document.

        Accepts either a ``file_id`` (to re-read a saved file) or direct
        ``text`` content.  When ``file_id`` is provided, the method looks up
        the saved file in the uploads directory, re-extracts the text, and
        passes it to the LLM backend for summarisation.

        Args:
            request: A ``SummarizeRequest`` containing either ``file_id``
                     or ``text``, plus optional ``entities`` and ``max_tokens``.

        Returns:
            JSONResponse with the generated summary, LLM-extracted entities,
            file_id, and processing time.

        Raises:
            LLMBackendError: If the LLM backend is unavailable or returns an
                             error during summarisation.
        """
        start_time = time.time()
        debug_logger.debug(
            "summarize_document called",
            extra={
                "has_file_id": request.file_id is not None,
                "has_text": request.text is not None,
                "max_tokens": request.max_tokens,
            },
        )

        try:
            # ── 1. Resolve the text to summarise ──────────────────────────
            cleaned_text: Optional[str] = None
            resolved_file_id: Optional[str] = None

            if request.file_id:
                # Look up the saved file by file_id
                file_path: Optional[Path] = self.file_saver.get_file_path(
                    request.file_id
                )
                if file_path is None:
                    logger.warning(
                        f"File not found for file_id: {request.file_id}",
                        extra=safe_extra(file_id=request.file_id),
                    )
                    return JSONResponse(
                        status_code=404,
                        content={
                            "success": False,
                            "error": {
                                "code": "FILE_NOT_FOUND",
                                "message": (
                                    "The uploaded file session has expired. "
                                    "Please upload again."
                                ),
                                "details": {"file_id": request.file_id},
                            },
                        },
                    )

                resolved_file_id = request.file_id

                # Re-extract text from the saved file
                # We use the filename from the path to determine the parser
                text_pages = await file_to_string(file_path, file_path.name, "flow")
                processed_text = clean_and_squash_text(text_pages)
                cleaned_text = nlp.clean_text(processed_text)

                debug_logger.debug(
                    f"Text re-extracted from file_id={request.file_id}: "
                    f"{len(cleaned_text)} chars"
                )

            elif request.text:
                # Use the provided text directly
                cleaned_text = request.text
                resolved_file_id = "direct_text"

                debug_logger.debug(
                    f"Using direct text input: {len(cleaned_text)} chars"
                )
            else:
                # Neither file_id nor text provided
                return JSONResponse(
                    status_code=422,
                    content={
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": ("Either 'file_id' or 'text' must be provided."),
                            "details": {},
                        },
                    },
                )

            # ── 2. Call the LLM backend for summarisation ─────────────────
            try:
                llm_result = llm_backend.summarise(
                    cleaned_text,
                    pre_extracted_entities=request.entities,
                )
            except Exception as e:
                logger.error(
                    f"LLM backend error during summarisation: {e}",
                    exc_info=True,
                    extra=safe_extra(
                        file_id=resolved_file_id,
                        text_length=len(cleaned_text),
                    ),
                )
                raise LLMBackendError(
                    provider=llm_backend.__class__.__name__,
                    reason=str(e),
                )

            # ── 3. Parse the LLM response ─────────────────────────────────
            llm_summary: str = ""
            llm_entities: str = ""

            if isinstance(llm_result, dict):
                llm_summary = llm_result.get("summary", "")
                llm_entities = llm_result.get("entities", "")
            elif isinstance(llm_result, str):
                # Parse the "Summary: ...\nEntities: ..." format
                summary_prefix = "Summary: "
                entities_prefix = "\nEntities: "
                if entities_prefix in llm_result:
                    parts = llm_result.split(entities_prefix, maxsplit=1)
                    summary_part = parts[0]
                    if summary_part.startswith(summary_prefix):
                        llm_summary = summary_part[len(summary_prefix) :]
                    else:
                        llm_summary = summary_part
                    llm_entities = parts[1]
                elif summary_prefix in llm_result:
                    llm_summary = llm_result[len(summary_prefix) :]
                else:
                    llm_summary = llm_result

            # ── 4. Calculate processing time ──────────────────────────────
            processing_time_ms = (time.time() - start_time) * 1000

            # ── 5. Build and return structured response ───────────────────
            response = SummarizeResponse(
                success=True,
                summary=llm_summary,
                llm_entities=llm_entities,
                file_id=resolved_file_id,
                processing_time_ms=round(processing_time_ms, 2),
            )

            logger.info(
                "Document summarised successfully",
                extra=safe_extra(
                    file_id=resolved_file_id,
                    text_length=len(cleaned_text),
                    summary_length=len(llm_summary),
                    processing_time_ms=round(processing_time_ms, 2),
                ),
            )

            return JSONResponse(content=response.model_dump())

        except LLMBackendError:
            # Re-raise — handled by global exception handlers
            raise
        except Exception as e:
            debug_logger.debug(
                f"Exception caught in summarize_document: {type(e).__name__}: {e}",
                exc_info=True,
            )
            logger.error(
                f"Unexpected error during summarisation: {e}",
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": (
                            "An unexpected error occurred during summarisation. "
                            "Please try again."
                        ),
                        "details": {},
                    },
                },
            )

    async def chat_process(
        self,
        file: UploadFile = File(),
        prompt: str = Form(""),
        extraction_mode: str = Form("flow"),
    ):
        """
        **Future**: Combined file upload + chat prompt in one request.

        This is a stub method intended to support the ``/api/chat/process``
        endpoint.  The full implementation will accept a file upload together
        with a chat prompt, extract text from the file, and feed both the
        extracted text and the user's prompt to the LLM for a conversational
        response.

        Currently returns a placeholder indicating the feature is not yet
        fully implemented.

        Args:
            file: Uploaded document file
            prompt: User's chat prompt about the document
            extraction_mode: Extraction mode for text extraction

        Returns:
            JSONResponse with a placeholder message
        """
        logger.info(
            "chat_process called (stub) - not yet fully implemented",
            extra=safe_extra(
                filename=getattr(file, "filename", None),
                extraction_mode=extraction_mode,
                prompt_length=len(prompt),
            ),
        )
        return JSONResponse(
            status_code=200,
            content={
                "message": (
                    "The /api/chat/process endpoint is a placeholder "
                    "for future implementation. "
                    "File upload + chat prompt functionality is not yet available."
                ),
                "status": "not_implemented",
            },
        )
