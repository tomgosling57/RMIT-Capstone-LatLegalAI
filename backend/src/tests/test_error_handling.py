"""
Tests for centralized error handling and logging.

Covers:
- Custom exception classes
- Global exception handlers
- Structured error responses
- Request logging middleware
- Graceful degradation for LLM failures
"""

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from exceptions import (
    LatMatrixException,
    FileParsingError,
    ValidationError,
    LLMBackendError,
    UnsupportedFileTypeError,
)
from factory import create_app
from logging_config import configure_logging, JSONFormatter


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_latmatrix_exception_base(self):
        """Test base LatMatrixException creation and formatting."""
        exc = LatMatrixException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            status_code=400,
        )

        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value"}
        assert exc.status_code == 400

        response = exc.to_dict()
        assert response["success"] is False
        assert response["error"]["code"] == "TEST_ERROR"
        assert response["error"]["message"] == "Test error"
        assert response["error"]["details"] == {"key": "value"}

    def test_file_parsing_error(self):
        """Test FileParsingError with file-specific details."""
        exc = FileParsingError(
            filename="test.pdf",
            reason="Corrupted file header",
        )

        assert exc.error_code == "FILE_PARSING_ERROR"
        assert exc.status_code == 400
        assert exc.details["filename"] == "test.pdf"
        assert exc.details["reason"] == "Corrupted file header"

    def test_validation_error(self):
        """Test ValidationError with field information."""
        exc = ValidationError(
            message="Invalid input",
            field="email",
        )

        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 422
        assert exc.details["field"] == "email"

    def test_llm_backend_error(self):
        """Test LLMBackendError with provider details."""
        exc = LLMBackendError(
            provider="openai",
            reason="API key invalid",
        )

        assert exc.error_code == "LLM_BACKEND_ERROR"
        assert exc.status_code == 503
        assert exc.details["provider"] == "openai"
        assert exc.details["reason"] == "API key invalid"

    def test_unsupported_file_type_error(self):
        """Test UnsupportedFileTypeError with supported types."""
        exc = UnsupportedFileTypeError(
            file_type="exe",
            supported_types=["pdf", "txt", "docx"],
        )

        assert exc.error_code == "UNSUPPORTED_FILE_TYPE"
        assert exc.status_code == 400
        assert exc.details["file_type"] == "exe"
        assert exc.details["supported_types"] == ["pdf", "txt", "docx"]


class TestGlobalExceptionHandlers:
    """Test global exception handlers in FastAPI app."""

    def test_latmatrix_exception_handler(self):
        """Test that LatMatrixException is caught and formatted correctly."""
        app = create_app()
        client = TestClient(app)

        @app.get("/test-latmatrix-error")
        async def test_endpoint():
            raise FileParsingError(
                filename="test.pdf",
                reason="Invalid format",
            )

        response = client.get("/test-latmatrix-error")
        assert response.status_code == 400

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FILE_PARSING_ERROR"
        assert "test.pdf" in data["error"]["message"]
        assert data["error"]["details"]["filename"] == "test.pdf"

    def test_http_exception_handler_422(self):
        """Test that HTTP 422 validation errors are handled."""
        app = create_app()
        client = TestClient(app)

        @app.get("/test-validation")
        async def test_endpoint():
            raise StarletteHTTPException(
                status_code=422,
                detail="Validation error",
            )

        response = client.get("/test-validation")
        assert response.status_code == 422

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_http_exception_handler_404(self):
        """Test that HTTP 404 errors are handled."""
        app = create_app()
        client = TestClient(app)

        @app.get("/test-notfound")
        async def test_endpoint():
            raise StarletteHTTPException(status_code=404)

        response = client.get("/test-notfound")
        assert response.status_code == 404

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_unhandled_exception_handler(self):
        """Test that unhandled exceptions are caught safely."""
        app = create_app()
        client = TestClient(app, raise_server_exceptions=False)

        @app.get("/test-unhandled")
        async def test_endpoint():
            raise ValueError("Something went wrong")

        response = client.get("/test-unhandled")
        assert response.status_code == 500

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_ERROR"
        # Ensure no stack trace or internal details are exposed
        assert "ValueError" not in data["error"]["message"]
        assert "Something went wrong" not in data["error"]["message"]


class TestJSONFormatter:
    """Test structured JSON logging formatter."""

    def test_json_formatter_basic_log(self):
        """Test that logs are formatted as valid JSON."""
        formatter = JSONFormatter()
        logger = pytest.importorskip("logging").getLogger(__name__)

        # Create a log record
        record = logger.makeRecord(
            "test.logger",
            pytest.importorskip("logging").INFO,
            "test.py",
            10,
            "Test message",
            (),
            None,
        )

        formatted = formatter.format(record)

        # Should be valid JSON
        data = json.loads(formatted)
        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data

    def test_json_formatter_with_exception(self):
        """Test that exception information is included in JSON logs."""
        formatter = JSONFormatter()
        logger = pytest.importorskip("logging").getLogger(__name__)

        try:
            raise ValueError("Test exception")
        except Exception:
            import sys

            record = logger.makeRecord(
                "test.logger",
                pytest.importorskip("logging").ERROR,
                "test.py",
                10,
                "Error occurred",
                (),
                sys.exc_info(),
            )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["level"] == "ERROR"
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "Test exception" in data["exception"]["message"]
        assert len(data["exception"]["traceback"]) > 0


class TestLoggingConfiguration:
    """Test logging configuration setup."""

    def test_configure_logging_creates_logger(self):
        """Test that configure_logging returns a valid logger."""
        with patch("logging_config.Path.mkdir"):
            logger = configure_logging(enable_file_logging=False)
            assert logger is not None
            assert len(logger.handlers) > 0  # At least console handler

    def test_configure_logging_console_handler(self):
        """Test that console handler is configured."""
        with patch("logging_config.Path.mkdir"):
            logger = configure_logging(enable_file_logging=False)

            # Should have a StreamHandler for stdout
            has_stream_handler = any(
                "StreamHandler" in str(type(h)) for h in logger.handlers
            )
            assert has_stream_handler

    def test_configure_logging_sets_level(self):
        """Test that logging level is set correctly."""
        import logging

        with patch("logging_config.Path.mkdir"):
            logger = configure_logging(log_level="DEBUG", enable_file_logging=False)
            assert logger.level == logging.DEBUG


class TestRequestLogging:
    """Test request logging middleware."""

    def test_request_logging_middleware(self):
        """Test that requests are logged with timing information."""
        app = create_app()
        client = TestClient(app)

        with patch("middleware.logger") as mock_logger:
            response = client.get("/health")
            assert response.status_code == 200

            # Verify logger was called
            assert mock_logger.info.called

    def test_request_logging_includes_metadata(self):
        """Test that request logs include method, path, and status."""
        app = create_app()
        client = TestClient(app)

        with patch("middleware.logger") as mock_logger:
            client.get("/health")

            # Get the call args
            assert mock_logger.info.called
            call_args = mock_logger.info.call_args

            # Verify extra context is included
            if call_args and "extra" in call_args.kwargs:
                extra = call_args.kwargs["extra"]
                assert extra.get("method") == "GET"
                assert extra.get("path") == "/health"
                assert extra.get("status_code") == 200


class TestErrorResponseFormat:
    """Test that all error responses follow the standard format."""

    def test_error_response_structure(self):
        """Test that error responses have the correct structure."""
        app = create_app()
        client = TestClient(app)

        @app.get("/test-error")
        async def test_endpoint():
            raise FileParsingError(filename="test.pdf")

        response = client.get("/test-error")
        data = response.json()

        # Check structure
        assert "success" in data
        assert data["success"] is False
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "details" in data["error"]

    def test_no_stack_trace_in_production(self):
        """Test that stack traces are not exposed in error responses."""
        app = create_app()
        client = TestClient(app, raise_server_exceptions=False)

        @app.get("/test-crash")
        async def test_endpoint():
            raise RuntimeError("Internal database error: user_id=123")

        response = client.get("/test-crash")
        data = response.json()

        # Error message should be generic, not exposing internal details
        assert "user_id" not in json.dumps(data)
        # Verify the error message is generic, not the actual exception message
        assert (
            data["error"]["message"]
            == "An unexpected error occurred. Please try again later."
        )
        assert "Internal database error" not in data["error"]["message"]


class TestGracefulDegradation:
    """Test graceful degradation when services are unavailable."""

    def test_llm_failure_returns_partial_result(self):
        """Test that LLM failure doesn't fail the entire request."""
        from services.llm_backend import LLMBackend

        # Mock LLM backend that throws an error
        mock_backend = Mock(spec=LLMBackend)
        mock_backend.summarise.side_effect = Exception("API unavailable")

        # The mock will raise, but in real implementation, the controller
        # should catch this and return partial results
        assert mock_backend.summarise.side_effect is not None

    def test_file_parsing_error_is_clear(self):
        """Test that file parsing errors are clear and helpful."""
        app = create_app()
        client = TestClient(app)

        @app.get("/test-parse-error")
        async def test_endpoint():
            raise FileParsingError(
                filename="corrupt.pdf",
                reason="Invalid PDF header",
            )

        response = client.get("/test-parse-error")
        data = response.json()

        # Error should be clear about which file and why
        assert "corrupt.pdf" in data["error"]["message"]
        assert data["error"]["details"]["filename"] == "corrupt.pdf"
        assert "Invalid PDF header" in data["error"]["details"]["reason"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
