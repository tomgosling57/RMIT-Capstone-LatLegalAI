"""
Custom exception classes for the LatMatrix API.

All exceptions follow a structured format with error codes and messages
that are safe to expose to clients (no internal paths or stack traces).
"""

from typing import Any, Dict, Optional


class LatMatrixException(Exception):
    """
    Base exception class for all LatMatrix errors.

    Attributes:
        error_code: Machine-readable error identifier
        message: Human-readable error message
        details: Additional context or debugging information
        status_code: HTTP status code to return
    """

    error_code: str = "INTERNAL_ERROR"
    message: str = "An internal error occurred"
    status_code: int = 500

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ):
        """
        Initialize the exception.

        Args:
            message: Override the default message
            error_code: Override the default error code
            details: Additional context information
            status_code: Override the HTTP status code
        """
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.status_code = status_code or self.status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to structured response format.

        Returns:
            Dictionary with success=false and error details
        """
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            },
        }


class FileParsingError(LatMatrixException):
    """Raised when a file cannot be parsed."""

    error_code = "FILE_PARSING_ERROR"
    message = "Failed to parse the uploaded file"
    status_code = 400

    def __init__(
        self,
        message: Optional[str] = None,
        filename: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize file parsing error.

        Args:
            message: Override the default message
            filename: Name of the file that failed to parse
            reason: Reason for the parsing failure
            details: Additional context information
        """
        if not message:
            message = f"Failed to parse file: {filename or 'unknown'}"
            if reason:
                message += f" ({reason})"

        error_details = details or {}
        if filename:
            error_details["filename"] = filename
        if reason:
            error_details["reason"] = reason

        super().__init__(
            message=message,
            error_code="FILE_PARSING_ERROR",
            details=error_details,
            status_code=400,
        )


class ValidationError(LatMatrixException):
    """Raised when request validation fails."""

    error_code = "VALIDATION_ERROR"
    message = "Request validation failed"
    status_code = 422

    def __init__(
        self,
        message: Optional[str] = None,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize validation error.

        Args:
            message: Override the default message
            field: Name of the field that failed validation
            details: Additional context information
        """
        error_details = details or {}
        if field:
            error_details["field"] = field

        super().__init__(
            message=message or self.message,
            error_code="VALIDATION_ERROR",
            details=error_details,
            status_code=422,
        )


class LLMBackendError(LatMatrixException):
    """Raised when LLM backend is unavailable or returns an error."""

    error_code = "LLM_BACKEND_ERROR"
    message = "LLM backend is currently unavailable"
    status_code = 503

    def __init__(
        self,
        message: Optional[str] = None,
        provider: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize LLM backend error.

        Args:
            message: Override the default message
            provider: Name of the LLM provider (e.g., 'openai', 'anthropic')
            reason: Reason for the backend failure
            details: Additional context information
        """
        error_details = details or {}
        if provider:
            error_details["provider"] = provider
        if reason:
            error_details["reason"] = reason

        super().__init__(
            message=message or self.message,
            error_code="LLM_BACKEND_ERROR",
            details=error_details,
            status_code=503,
        )


class EntityExtractionError(LatMatrixException):
    """Raised when entity extraction fails."""

    error_code = "ENTITY_EXTRACTION_ERROR"
    message = "Failed to extract entities from text"
    status_code = 500

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize entity extraction error.

        Args:
            message: Override the default message
            details: Additional context information
        """
        super().__init__(
            message=message or self.message,
            error_code="ENTITY_EXTRACTION_ERROR",
            details=details or {},
            status_code=500,
        )


class UnsupportedFileTypeError(LatMatrixException):
    """Raised when an unsupported file type is uploaded."""

    error_code = "UNSUPPORTED_FILE_TYPE"
    message = "This file type is not supported"
    status_code = 400

    def __init__(
        self,
        message: Optional[str] = None,
        file_type: Optional[str] = None,
        supported_types: Optional[list[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize unsupported file type error.

        Args:
            message: Override the default message
            file_type: The unsupported file type
            supported_types: List of supported file types
            details: Additional context information
        """
        error_details = details or {}
        if file_type:
            error_details["file_type"] = file_type
        if supported_types:
            error_details["supported_types"] = supported_types

        if not message:
            message = f"File type '{file_type}' is not supported"
            if supported_types:
                message += f". Supported types: {', '.join(supported_types)}"

        super().__init__(
            message=message,
            error_code="UNSUPPORTED_FILE_TYPE",
            details=error_details,
            status_code=400,
        )


class UnsupportedLanguageError(LatMatrixException):
    """Raised when a detected language is not supported by OCR."""

    error_code = "UNSUPPORTED_LANGUAGE"
    message = "The detected language is not supported for OCR processing"
    status_code = 400

    def __init__(
        self,
        message: Optional[str] = None,
        detected_language: Optional[str] = None,
        supported_languages: Optional[list[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize unsupported language error.

        Args:
            message: Override the default message
            detected_language: The detected language code or name
            supported_languages: List of supported language codes
            details: Additional context information
        """
        error_details = details or {}
        if detected_language:
            error_details["detected_language"] = detected_language
        if supported_languages:
            error_details["supported_languages"] = supported_languages

        if not message:
            message = f"Language '{detected_language}' is not supported for OCR"
            if supported_languages:
                message += f". Supported languages: {', '.join(supported_languages)}"

        super().__init__(
            message=message,
            error_code="UNSUPPORTED_LANGUAGE",
            details=error_details,
            status_code=400,
        )
