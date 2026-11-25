"""
Logging configuration for the LatMatrix API.

Provides structured JSON logging with rotating file handlers for both
stdout (for Docker) and file-based persistence.
"""

import json
import logging
import logging.handlers
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


# Standard LogRecord attributes set by the logging module.
# Any attribute on a LogRecord that is NOT in this set was passed via
# the extra={...} parameter and should be included in JSON output.
_STANDARD_RECORD_ATTRS: set = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format for structured logging.

    Each log entry includes timestamp, level, logger name, message, and optional
    exception information.  Extra fields passed via the ``extra={...}`` parameter
    (e.g. ``logger.info("msg", extra={"key": "val"})``) are automatically
    included as top-level keys in the JSON output.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON string representation of the log record
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Collect extra fields set via the extra={...} parameter.
        # Python's logging module stores each key in the extra dict as a
        # separate attribute on the LogRecord (not as record.extra), so we
        # iterate over __dict__ and pick up anything that isn't a standard
        # LogRecord attribute.
        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRS:
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data)


# Global status for health check
LOGGING_STATUS = {
    "file_logging_enabled": False,
    "file_logging_active": False,
    "fallback_active": False,
    "error": None,
}


def configure_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    enable_file_logging: bool = True,
) -> logging.Logger:
    """
    Configure structured logging for the application.

    Sets up both console (stdout for Docker) and file-based logging with
    JSON formatting and rotating file handlers.

    Args:
        log_dir: Directory to store log files
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_file_logging: Whether to enable file-based logging

    Returns:
        Configured root logger instance
    """
    global LOGGING_STATUS
    LOGGING_STATUS["file_logging_enabled"] = enable_file_logging

    # Create logs directory if it doesn't exist
    if enable_file_logging:
        log_path = Path(log_dir)
        try:
            log_path.mkdir(parents=True, exist_ok=True)
            LOGGING_STATUS["file_logging_active"] = True
        except (PermissionError, OSError) as e:
            LOGGING_STATUS["file_logging_active"] = False
            LOGGING_STATUS["fallback_active"] = True
            LOGGING_STATUS["error"] = str(e)
            sys.stderr.write(
                "Warning: Could not create log directory"
                f" {log_dir}: {e}. File logging disabled.\n"
            )
            enable_file_logging = False

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create JSON formatter
    json_formatter = JSONFormatter()

    # Console handler (stdout for Docker)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation (10MB per file, keep 5 backups)
    if enable_file_logging:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(log_path / "app.log"),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            file_handler.setLevel(getattr(logging, log_level))
            file_handler.setFormatter(json_formatter)
            logger.addHandler(file_handler)

            # Error log file (only ERROR and CRITICAL)
            error_handler = logging.handlers.RotatingFileHandler(
                filename=str(log_path / "error.log"),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(json_formatter)
            logger.addHandler(error_handler)
            LOGGING_STATUS["file_logging_active"] = True
        except (PermissionError, OSError) as e:
            LOGGING_STATUS["file_logging_active"] = False
            LOGGING_STATUS["fallback_active"] = True
            LOGGING_STATUS["error"] = str(e)
            sys.stderr.write(
                f"Warning: Could not set up rotating file handlers: {e}."
                " File logging disabled.\n"
            )

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance configured with JSON formatting.

    If ``configure_logging()`` has already been called, the root logger's
    handlers are already set up with ``JSONFormatter``, so this function
    simply returns a child logger that propagates to the root (avoiding
    duplicate handler creation).

    If ``configure_logging()`` has NOT been called, this function creates a
    minimal console handler with ``JSONFormatter`` so that callers always
    get structured JSON output regardless of setup order.

    Args:
        name: The logger name, typically ``__name__`` from the calling module.

    Returns:
        A configured Logger instance with JSON formatting.
    """
    logger = logging.getLogger(name)

    # If the root logger already has handlers (configure_logging was called),
    # just return a child logger that propagates — no need for duplicate handlers.
    root = logging.getLogger()
    if root.handlers:
        logger.setLevel(root.level)
        logger.propagate = True
        return logger

    # No root configuration exists yet — set up a minimal console handler
    # with JSON formatting so callers always get structured output.
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

    return logger


def get_file_debug_logger(
    name: str,
    log_dir: str = "logs",
    filename: str = "debug.log",
    level: int = logging.DEBUG,
) -> logging.Logger:
    """
    Get a file-only debug logger.

    If ENABLE_FILE_LOGGING is true, output goes exclusively to the specified
    file and does NOT propagate to the root logger.

    If ENABLE_FILE_LOGGING is false, output propagates to the root logger
    (appearing on stdout/stderr) and no file is created.

    Args:
        name: Logger name (must be unique to avoid handler duplication)
        log_dir: Directory for the log file (default: "logs")
        filename: Log file name (default: "debug.log")
        level: Logging level (default: logging.DEBUG)

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)

    # If file logging is disabled, just return a logger that propagates to root
    enable_file_logging = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"
    if not enable_file_logging:
        logger.setLevel(level)
        logger.propagate = True
        return logger

    # Only add a handler if one doesn't already exist for this logger
    if not logger.handlers:
        log_path = Path(log_dir)
        try:
            log_path.mkdir(parents=True, exist_ok=True)

            handler = logging.FileHandler(
                filename=str(log_path / filename),
                mode="a",
            )
            handler.setLevel(level)
            handler.setFormatter(
                logging.Formatter(
                    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S%z",
                )
            )

            logger.setLevel(level)
            logger.propagate = False  # do NOT bubble up to root / stdout
            logger.addHandler(handler)
        except (PermissionError, OSError) as e:
            # Fallback to propagation if directory creation or file opening fails
            sys.stderr.write(
                f"Warning: Could not set up file logger {name}: {e}. "
                "Falling back to console.\n"
            )
            logger.setLevel(level)
            logger.propagate = True

    return logger


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context: Any,
) -> None:
    """
    Log a message with additional context fields.

    This is a convenience function. For better integration with the structured
    logging formatter, use logger.info/debug/etc directly with the extra parameter:
        logger.info(message, extra={"key": "value"})

    Args:
        logger: Logger instance to use
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        **context: Additional context fields to include in log
    """
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, extra=safe_extra(**context))


def safe_extra(**kwargs: Any) -> dict[str, Any]:
    """
    Return an ``extra`` dict whose keys are guaranteed not to collide with
    standard ``LogRecord`` attributes.

    Python's ``logging.Logger.makeRecord()`` raises ``KeyError`` if any key
    in the ``extra`` dict matches a built-in ``LogRecord`` attribute (such as
    ``"filename"``, ``"name"``, ``"message"``, etc.).  This helper prefixes
    any colliding key with ``"ctx_"`` so the structured JSON formatter can
    still include the value without triggering the safeguard.

    Usage::

        logger.info("msg", extra=safe_extra(filename="foo.txt", count=42))
        # -> extra={"ctx_filename": "foo.txt", "count": 42}

    Returns:
        A dict safe to pass as the ``extra`` parameter to any logger call.
    """
    return {
        (f"ctx_{k}" if k in _STANDARD_RECORD_ATTRS else k): v for k, v in kwargs.items()
    }
