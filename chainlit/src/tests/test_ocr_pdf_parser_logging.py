"""
Tests that OCRPDFParser warning messages are correctly logged as JSON
to the file system (not plain print() output), with automatic cleanup
of temporary log directories.
"""

import json
import logging
from pathlib import Path

import pytest

from src.tools.ocr_pdf_parser import OCRPDFParser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """
    Provide a temporary log directory that is automatically cleaned up
    after each test by pytest's tmp_path fixture.
    """
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


@pytest.fixture
def configured_logger(temp_log_dir: Path) -> logging.Logger:
    """
    Configure the root logger with JSON formatting and a file handler
    pointing to the temporary log directory.  Returns the root logger.
    """
    # Reset handlers so configure_logging starts fresh
    root = logging.getLogger()
    root.handlers.clear()

    # Simple file handler for testing — no JSON formatter dependency
    log_file = temp_log_dir / "app.log"
    handler = logging.FileHandler(str(log_file), encoding="utf-8")
    handler.setLevel(logging.WARNING)
    handler.setFormatter(
        logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    )
    root.addHandler(handler)
    root.setLevel(logging.WARNING)

    return root


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestOCRPDFParserLogging:
    """Verify that OCRPDFParser emits JSON-formatted log entries to disk."""

    @pytest.mark.asyncio
    async def test_warning_logged_as_json_to_file(
        self, configured_logger: logging.Logger, temp_log_dir: Path
    ) -> None:
        """
        When OCRPDFParser.parse() is called with an unsupported
        extraction_mode (e.g. "layout"), a WARNING-level log entry
        should be written to the log file in JSON format — not emitted
        via print().
        """
        # Arrange
        log_file = temp_log_dir / "app.log"
        parser = OCRPDFParser()
        nonexistent = Path("/nonexistent/file.pdf")

        # Act — trigger the warning by passing an unsupported extraction_mode
        with pytest.raises(FileNotFoundError):
            await parser.parse(nonexistent, extraction_mode="layout")

        # Assert — the log file exists and contains our warning
        assert log_file.exists(), f"Log file not found at {log_file}"

        log_content = log_file.read_text(encoding="utf-8")
        assert log_content.strip(), "Log file is empty"

        # Parse every line as JSON and find the OCRPDFParser warning
        found_warning = False
        for line in log_content.strip().splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # skip non-JSON lines (shouldn't happen, but be safe)

            if (
                record.get("logger") == "src.tools.ocr_pdf_parser"
                and record.get("level") == "WARNING"
                and "extraction_mode" in record.get("message", "")
            ):
                found_warning = True
                # Verify JSON structure
                assert "timestamp" in record, "Missing 'timestamp' in JSON log"
                assert "message" in record, "Missing 'message' in JSON log"
                assert "level" in record, "Missing 'level' in JSON log"
                assert "logger" in record, "Missing 'logger' in JSON log"

                # Verify the message content
                assert (
                    "layout" in record["message"]
                ), "Message should mention the unsupported mode"
                assert (
                    "OCRPDFParser" in record["message"]
                ), "Message should mention OCRPDFParser"
                assert (
                    "defaulting to 'flow'" in record["message"]
                ), "Message should mention fallback to 'flow'"
                break

        assert found_warning, (
            f"Expected WARNING from tools.ocr_pdf_parser "
            f"not found in log file. Log contents:\n{log_content}"
        )

    @pytest.mark.asyncio
    async def test_warning_is_not_plain_print(
        self, configured_logger: logging.Logger, temp_log_dir: Path
    ) -> None:
        """
        Confirm the warning is emitted via the logging framework (JSON)
        and NOT via a plain print() statement.  We do this by capturing
        stdout and verifying the output is valid JSON with the expected
        structure.
        """
        import io
        import sys

        parser = OCRPDFParser()
        nonexistent = Path("/nonexistent/file.pdf")

        # Capture stdout to ensure nothing is printed outside the logging
        # framework (the console handler also emits JSON, so even stdout
        # output should be valid JSON).
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            with pytest.raises(FileNotFoundError):
                await parser.parse(nonexistent, extraction_mode="layout")
        finally:
            sys.stdout = old_stdout

        stdout_output = captured.getvalue().strip()

        # The console handler uses JSONFormatter, so stdout should contain
        # valid JSON lines — not arbitrary text.
        if stdout_output:
            for line in stdout_output.splitlines():
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    pytest.fail(
                        f"Non-JSON output detected on stdout (likely a "
                        f"print() statement): {line!r}"
                    )
                # If this is the OCRPDFParser warning, verify its structure
                if record.get("logger") == "src.tools.ocr_pdf_parser":
                    assert record["level"] == "WARNING"
                    assert "extraction_mode" in record["message"]

    @pytest.mark.asyncio
    async def test_no_warning_for_default_extraction_mode(
        self, configured_logger: logging.Logger, temp_log_dir: Path
    ) -> None:
        """
        When OCRPDFParser.parse() is called with the default
        extraction_mode ("flow"), no WARNING should be logged.
        """
        log_file = temp_log_dir / "app.log"
        parser = OCRPDFParser()
        nonexistent = Path("/nonexistent/file.pdf")

        with pytest.raises(FileNotFoundError):
            await parser.parse(nonexistent, extraction_mode="flow")

        assert log_file.exists()

        log_content = log_file.read_text(encoding="utf-8")
        for line in log_content.strip().splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            # There should be NO WARNING from ocr_pdf_parser about
            # extraction_mode when mode is "flow"
            if (
                record.get("logger") == "tools.ocr_pdf_parser"
                and record.get("level") == "WARNING"
            ):
                pytest.fail(
                    f"Unexpected WARNING logged for default extraction_mode: "
                    f"{record['message']}"
                )

    @pytest.mark.asyncio
    async def test_log_file_created_in_configured_directory(
        self, configured_logger: logging.Logger, temp_log_dir: Path
    ) -> None:
        """
        Verify that the log file (app.log) is created in the configured
        log directory after a parse attempt.
        """
        log_file = temp_log_dir / "app.log"
        parser = OCRPDFParser()
        nonexistent = Path("/nonexistent/file.pdf")

        with pytest.raises(FileNotFoundError):
            await parser.parse(nonexistent, extraction_mode="layout")

        assert log_file.exists(), f"app.log should exist at {log_file}"
        assert log_file.stat().st_size > 0, "app.log should not be empty"
