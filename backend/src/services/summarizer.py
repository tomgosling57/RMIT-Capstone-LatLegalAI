"""
Legal Document Summarizer Service.
Main service for legal document summarization using LLM backends.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from services.parsers.parser_factory import DocumentParserFactory
from services.nlp_processor import NLPService
from services.llm_backend import get_llm_backend


class LegalSummarizer:
    """
    Main service for legal document summarization.

    Orchestrates the complete summarization pipeline:
    1. Document parsing (PDF, Word, text, OCR)
    2. NLP processing (text cleaning, clause extraction)
    3. LLM-based summarization (with optional integrated translation)

    Uses the NLPService for natural language processing tasks
    and LLM backends for summarization.
    """

    def __init__(
        self,
        parser_factory: Optional[DocumentParserFactory] = None,
        nlp_service: Optional[NLPService] = None,
        llm_backend_name: Optional[str] = None,
    ):
        """
        Initialize the legal summarizer.

        Args:
            parser_factory: Factory for creating document parsers
            nlp_service: NLP service for text processing and clause extraction
            llm_backend_name: LLM backend to use (openai, anthropic, ollama, mock)
        """
        self.parser_factory = parser_factory or DocumentParserFactory()
        self.nlp_service = nlp_service or NLPService()
        self.llm_backend = get_llm_backend(llm_backend_name)

    async def process_document(
        self, file_path: Path, target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document through the complete summarization pipeline.

        Args:
            file_path: Path to the document file
            target_language: Optional language code for translation (e.g., 'es', 'fr')

        Returns:
            Dictionary with analysis results including:
            - original_text: Extracted text from document
            - cleaned_text: Cleaned version of text
            - summary: Plain-English summary or summary in target language
            - obligations: List of responsibilities
            - permissions: List of permissions
            - risks: List of risks/warnings
            - metadata: Processing metadata
        """
        # Parse document
        parser = self.parser_factory.get_parser(file_path)
        text = parser.parse(file_path)

        # NLP processing
        nlp_result = self.nlp_service.analyze_text(text)
        cleaned_text = nlp_result.get("cleaned_text", text)
        clauses = nlp_result.get("clauses", {})
        stats = nlp_result.get("stats", {})

        # LLM summarization with optional translation
        summary = self.llm_backend.summarise(
            cleaned_text, target_language=target_language
        )

        # Build result
        analysis_result = {
            "original_text": text,
            "cleaned_text": cleaned_text,
            "summary": summary,
            "obligations": clauses.get("obligations", []),
            "permissions": clauses.get("permissions", []),
            "risks": clauses.get("risks", []),
            "stats": stats,
            "translation_method": "integrated" if target_language else "none",
            "target_language": target_language,
        }

        # Add metadata
        try:
            file_size = file_path.stat().st_size if file_path.exists() else 0
        except (OSError, PermissionError):
            file_size = 0

        analysis_result["metadata"] = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_size": file_size,
            "processing_timestamp": None,  # Would be datetime.now().isoformat()
            "translation_applied": target_language is not None,
            "target_language": target_language,
            "llm_backend": self.llm_backend.__class__.__name__,
        }

        return analysis_result

    def process_document_sync(
        self, file_path: Path, target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of process_document.

        This method provides the same document summarization pipeline as the async
        `process_document()` method but for non-async contexts. It performs all
        processing synchronously:

        Args:
            file_path: Path to the document file (PDF, Word, text, or OCR-able)
            target_language: Optional language code for translation (e.g., 'es', 'fr').
                           If provided, the summary will be generated in that language.

        Returns:
            Dictionary with analysis results including:
            - original_text: Extracted text from document
            - cleaned_text: Cleaned version of text
            - summary: Plain-English summary or summary in target language
            - obligations: List of responsibilities/obligations from the document
            - permissions: List of permissions/rights granted
            - risks: List of risks/warnings/restrictions
            - stats: Statistics about the analysis (word count, section count, etc.)
            - translation_method: "integrated" if target_language was specified,
            "none" otherwise
            - target_language: The requested language code (or None)
            - metadata: Processing metadata including file info and backend details

        Raises:
            FileNotFoundError: If the file_path does not exist
            ValueError: If the file format is not supported
            Exception: If parsing, NLP processing, or LLM summarization fails

        Example:
            >>> summarizer = LegalSummarizer()
            >>> result = summarizer.process_document_sync(
            ...     Path("contract.pdf"),
            ...     target_language="es"
            ... )
            >>> print(result["summary"])  # Spanish summary
        """
        # Parse document
        parser = self.parser_factory.get_parser(file_path)
        text = parser.parse(file_path)

        # NLP processing
        nlp_result = self.nlp_service.analyze_text(text)
        cleaned_text = nlp_result.get("cleaned_text", text)
        clauses = nlp_result.get("clauses", {})
        stats = nlp_result.get("stats", {})

        # LLM summarization with optional translation
        summary = self.llm_backend.summarise(
            cleaned_text, target_language=target_language
        )

        # Build result
        analysis_result = {
            "original_text": text,
            "cleaned_text": cleaned_text,
            "summary": summary,
            "obligations": clauses.get("obligations", []),
            "permissions": clauses.get("permissions", []),
            "risks": clauses.get("risks", []),
            "stats": stats,
            "translation_method": "integrated" if target_language else "none",
            "target_language": target_language,
        }

        # Add metadata
        analysis_result["metadata"] = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "processing_timestamp": None,  # Would be datetime.now().isoformat()
            "translation_applied": target_language is not None,
            "target_language": target_language,
            "llm_backend": self.llm_backend.__class__.__name__,
        }

        return analysis_result

    def summarize_text(
        self, text: str, target_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Summarize text directly without document parsing.

        Args:
            text: Legal text to summarize
            target_language: Optional language code for translation

        Returns:
            Dictionary with summary and extracted clauses
        """
        # NLP processing
        nlp_result = self.nlp_service.analyze_text(text)
        cleaned_text = nlp_result.get("cleaned_text", text)
        clauses = nlp_result.get("clauses", {})
        stats = nlp_result.get("stats", {})

        # LLM summarization with optional translation
        summary = self.llm_backend.summarise(
            cleaned_text, target_language=target_language
        )

        return {
            "cleaned_text": cleaned_text,
            "summary": summary,
            "obligations": clauses.get("obligations", []),
            "permissions": clauses.get("permissions", []),
            "risks": clauses.get("risks", []),
            "stats": stats,
            "translation_method": "integrated" if target_language else "none",
            "target_language": target_language,
        }

    def is_available(self) -> bool:
        """
        Check if the summarizer is properly configured.

        Returns:
            True if all required services are available
        """
        return self.nlp_service.is_available() and self.llm_backend is not None
