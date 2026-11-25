"""
Pydantic schemas for request/response validation in the LatMatrix API.

These models define the structured data contracts for all API endpoints,
ensuring type safety and consistent serialisation across the application.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Request Schemas ────────────────────────────────────────────────────────


class SummarizeRequest(BaseModel):
    """
    Request body for the ``POST /api/documents/summarize`` endpoint.

    Accepts either a ``file_id`` (to re-read a previously saved file) or
    direct ``text`` content.  At least one of the two must be provided.
    """

    file_id: Optional[str] = Field(
        None,
        description="UUID-based file identifier returned by the extract endpoint",
    )
    text: Optional[str] = Field(
        None,
        description="Full cleaned text to summarise (alternative to file_id)",
    )
    entities: Optional[Dict[str, Any]] = Field(
        None,
        description="Pre-extracted entities to pass as context to the LLM",
    )
    max_tokens: int = Field(
        4096,
        description="Maximum number of tokens for the generated summary",
        ge=256,
        le=16384,
    )


# ── Response Schemas ───────────────────────────────────────────────────────


class EntityItem(BaseModel):
    """A single extracted entity with metadata."""

    text: str = Field(..., description="The entity text")
    type: str = Field(
        ..., description="Entity type label (e.g. ORG, PERSON, DATE, GPE)"
    )
    confidence: float = Field(
        ..., description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0
    )
    source: str = Field(
        ..., description="Source of the entity (e.g. 'spacy', 'pattern')"
    )


class EntityCollection(BaseModel):
    """Grouped entities returned by the NLP pipeline."""

    names: List[EntityItem] = Field(
        default_factory=list, description="Person and organisation names"
    )
    dates: List[EntityItem] = Field(
        default_factory=list, description="Dates found in the document"
    )
    locations: List[EntityItem] = Field(
        default_factory=list, description="Locations (GPE and LOC)"
    )
    all_entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Raw list of all entities with label, start, and end positions",
    )


class ClauseLabel(BaseModel):
    """Classification labels for a single clause."""

    obligation: bool = Field(
        False, description="Whether the clause imposes an obligation"
    )
    permission: bool = Field(False, description="Whether the clause grants permission")
    risk: bool = Field(False, description="Whether the clause indicates risk")


class ClauseItem(BaseModel):
    """A single classified clause from the document."""

    sentence: str = Field(..., description="The clause sentence text")
    labels: ClauseLabel = Field(
        ..., description="Classification labels for this clause"
    )


class ExtractDocumentResponse(BaseModel):
    """
    Response model for the ``POST /api/documents/extract`` endpoint.

    Contains the extracted text, NLP entities, clause classifications, and
    file metadata.  No LLM summary is included — that is handled by the
    separate ``/api/documents/summarize`` endpoint.
    """

    success: bool = Field(True, description="Indicates whether the request succeeded")
    content: List[str] = Field(
        ..., description="List of extracted text strings, one per page"
    )
    cleaned_text: str = Field(
        ..., description="Full cleaned and squashed text ready for NLP"
    )
    entities: EntityCollection = Field(
        ..., description="Extracted NLP entities (names, dates, locations)"
    )
    clauses: List[ClauseItem] = Field(
        default_factory=list,
        description="Classified clauses (obligations, permissions, risks)",
    )
    filename: str = Field(..., description="Original uploaded filename")
    file_id: str = Field(
        ..., description="UUID-based file identifier for subsequent requests"
    )
    upload_timestamp: str = Field(..., description="ISO 8601 timestamp of the upload")
    pdf_type: str = Field(..., description="PDF type: TEXT_BASED, SCANNED, or UNKNOWN")


class SummarizeResponse(BaseModel):
    """
    Response model for the ``POST /api/documents/summarize`` endpoint.

    Contains the LLM-generated summary, extracted entities, file metadata,
    and processing time.
    """

    success: bool = Field(True, description="Indicates whether the request succeeded")
    summary: str = Field(
        ..., description="LLM-generated summary of the document in plain English"
    )
    llm_entities: str = Field(
        ...,
        description="Key entities extracted by the LLM (parties, dates, locations)",
    )
    file_id: str = Field(
        ..., description="UUID-based file identifier for the source document"
    )
    processing_time_ms: float = Field(
        ..., description="Time taken to generate the summary, in milliseconds"
    )
