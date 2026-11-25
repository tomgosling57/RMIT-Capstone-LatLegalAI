"""
Factory module for creating and configuring the FastAPI application.
"""

import os
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.formparsers import MultiPartParser
import spacy
from dotenv import load_dotenv

from routes.api import router as api_router
from routes.api import dev_router, should_register_dev_routes
from exceptions import LatMatrixException
from logging_config import configure_logging, get_logger
from middleware import RequestLoggingMiddleware
from config import MAX_PART_SIZE, SPACY_MAX_LENGTH


# Load environment variables
load_dotenv()

# Derive the project root from this file's location
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_LOG_DIR = str(PROJECT_ROOT / "logs")

# Module-level logger (safe: get_logger does NOT call configure_logging)
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure a FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    # Configure logging lazily (not at module import time) so that test
    # isolation is preserved and the logs/ directory is created relative to
    # the project root rather than the current working directory.
    log_dir = os.getenv("LOG_DIR", DEFAULT_LOG_DIR)
    enable_file_logging = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"

    configure_logging(
        log_dir=log_dir,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        enable_file_logging=enable_file_logging,
    )

    # Bump Starlette's multipart part-size limit so that large uploads reach
    # the application handler (where we return a proper 413) instead of being
    # rejected with a generic 400 at the framework level.
    MultiPartParser.max_part_size = MAX_PART_SIZE

    # Initialize FastAPI app
    app = FastAPI(
        title="LatMatrix Prototype API",
        description="Backend API for LatMatrix Prototype with NLP capabilities",
        version="1.0.0",
    )

    # Add CORS middleware (before request logging middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Register global exception handlers
    register_exception_handlers(app)

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> Dict[str, str]:
        """Health check endpoint for monitoring."""
        return {"status": "healthy"}

    # Register API routes (all under /api/ prefix)
    app.include_router(api_router)

    # Conditionally register dev-only routes (e.g. /api/documents/extract-text)
    if should_register_dev_routes():
        logger.info("DEV_MODE enabled — registering dev-only routes")
        app.include_router(dev_router)
    else:
        logger.info("DEV_MODE disabled — dev-only routes not registered")

    logger.info(
        "FastAPI application initialized successfully",
        extra={
            "version": "1.0.0",
            "title": "LatMatrix Prototype API",
            "max_file_size_mb": MAX_PART_SIZE // (1024 * 1024),
        },
    )
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers for the FastAPI application.

    Handles:
    - LatMatrixException: Custom application exceptions
    - StarletteHTTPException: Standard HTTP exceptions from FastAPI
    - Exception: Unhandled exceptions (never expose internal details)

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(LatMatrixException)
    async def latmatrix_exception_handler(
        request: Request, exc: LatMatrixException
    ) -> JSONResponse:
        """
        Handle LatMatrixException with structured error response.

        Args:
            request: The incoming request
            exc: The LatMatrixException instance

        Returns:
            JSON response with error details and appropriate status code
        """
        logger.error(
            f"LatMatrixException: {exc.error_code}",
            extra={
                "error_code": exc.error_code,
                "error_message": exc.message,
                "error_details": exc.details,
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """
        Handle standard HTTP exceptions from FastAPI validation, etc.

        Args:
            request: The incoming request
            exc: The HTTPException instance

        Returns:
            JSON response with error details
        """
        # Map FastAPI validation errors to meaningful error codes
        error_code = "HTTP_ERROR"
        if exc.status_code == 422:
            error_code = "VALIDATION_ERROR"
        elif exc.status_code == 404:
            error_code = "NOT_FOUND"
        elif exc.status_code == 401:
            error_code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            error_code = "FORBIDDEN"

        error_response: Dict[str, Any] = {
            "success": False,
            "error": {
                "code": error_code,
                "message": exc.detail or "An error occurred",
                "details": {},
            },
        }

        logger.warning(
            f"HTTPException: {error_code}",
            extra={
                "error_code": error_code,
                "status_code": exc.status_code,
                "error_detail": exc.detail,
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Handle all unhandled exceptions.

        IMPORTANT: Never expose internal details like stack traces or file paths
        in production responses. Only log them internally.

        Args:
            request: The incoming request
            exc: The Exception instance

        Returns:
            Generic JSON error response (no internal details exposed)
        """
        # Log the full error with traceback for debugging
        logger.error(
            f"Unhandled exception: {exc.__class__.__name__}",
            exc_info=True,
            extra={
                "exception_type": exc.__class__.__name__,
                "path": request.url.path,
                "method": request.method,
            },
        )

        # Return safe, generic error response to client
        error_response: Dict[str, Any] = {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {},
            },
        }

        return JSONResponse(
            status_code=500,
            content=error_response,
        )


def load_spacy_model():
    """
    Load the spaCy NLP model.

    Returns:
        tuple: (nlp_model, loaded_status)
    """
    try:
        nlp = spacy.load("en_core_web_sm")
        # Set the max_length from configuration to allow processing larger documents
        nlp.max_length = SPACY_MAX_LENGTH
        return nlp, True
    except Exception as e:
        print(f"Warning: Could not load spaCy model: {e}")
        return None, False
