# Running test_error_handling.py

This document provides comprehensive instructions for running the error handling test suite for the LatMatrix Legal Document Summarizer backend.

## Overview

The [`test_error_handling.py`](test_error_handling.py) file tests the following components:

- **Custom Exception Classes**: Validates that custom exceptions are properly structured
- **Global Exception Handlers**: Ensures FastAPI exception handlers work correctly
- **JSON Logging Formatter**: Tests structured logging output
- **Logging Configuration**: Verifies logging setup
- **Request Logging Middleware**: Tests request/response logging
- **Error Response Format**: Validates standardized error response structure
- **Graceful Degradation**: Tests service behavior under failure conditions

## Prerequisites

### 1. Virtual Environment Setup

Before running tests, ensure your virtual environment is activated.

From the `backend/` directory:

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

Install required packages from the backend directory:

```bash
cd backend
pip install -r requirements.txt
```

Key dependencies for testing:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `fastapi` - Web framework
- `starlette` - ASGI toolkit

## Quick Start

### Run All Tests in test_error_handling.py

From the `backend/src` directory:

```bash
# Standard verbose output
pytest tests/test_error_handling.py -v

# With detailed output including print statements
pytest tests/test_error_handling.py -v -s

# Show test coverage
pytest tests/test_error_handling.py -v --cov=. --cov-report=html
```

### Run Specific Test Classes

```bash
# Test custom exceptions only
pytest tests/test_error_handling.py::TestCustomExceptions -v

# Test global exception handlers only
pytest tests/test_error_handling.py::TestGlobalExceptionHandlers -v

# Test logging functionality
pytest tests/test_error_handling.py::TestJSONFormatter -v
pytest tests/test_error_handling.py::TestLoggingConfiguration -v

# Test request logging middleware
pytest tests/test_error_handling.py::TestRequestLogging -v

# Test error response format
pytest tests/test_error_handling.py::TestErrorResponseFormat -v

# Test graceful degradation
pytest tests/test_error_handling.py::TestGracefulDegradation -v
```

### Run Specific Individual Tests

```bash
# Test base exception creation
pytest tests/test_error_handling.py::TestCustomExceptions::test_latmatrix_exception_base -v

# Test file parsing error
pytest tests/test_error_handling.py::TestCustomExceptions::test_file_parsing_error -v

# Test exception handlers
pytest tests/test_error_handling.py::TestGlobalExceptionHandlers::test_latmatrix_exception_handler -v

# Test JSON formatter
pytest tests/test_error_handling.py::TestJSONFormatter::test_json_formatter_basic_log -v
```

## Test Structure

The test file is organized into 7 test classes:

### 1. TestCustomExceptions
Tests the custom exception classes defined in [`exceptions.py`](../exceptions.py):
- `LatMatrixException` - Base exception class
- `FileParsingError` - File parsing failures
- `ValidationError` - Input validation failures
- `LLMBackendError` - LLM service failures
- `UnsupportedFileTypeError` - Unsupported file type errors

**Run**: `pytest tests/test_error_handling.py::TestCustomExceptions -v`

### 2. TestGlobalExceptionHandlers
Tests the FastAPI exception handlers in the app factory:
- Validates LatMatrixException responses
- Tests HTTP 422 validation error handling
- Tests HTTP 404 not found handling
- Tests generic unhandled exception handling

**Run**: `pytest tests/test_error_handling.py::TestGlobalExceptionHandlers -v`

### 3. TestJSONFormatter
Tests the structured JSON logging formatter in [`logging_config.py`](../logging_config.py):
- Validates basic log formatting as JSON
- Tests exception information inclusion in logs

**Run**: `pytest tests/test_error_handling.py::TestJSONFormatter -v`

### 4. TestLoggingConfiguration
Tests the logging configuration setup:
- Validates logger creation
- Checks console handler configuration
- Verifies logging level configuration

**Run**: `pytest tests/test_error_handling.py::TestLoggingConfiguration -v`

### 5. TestRequestLogging
Tests the request logging middleware in [`middleware.py`](../middleware.py):
- Validates request/response logging
- Tests metadata inclusion (method, path, status code)

**Run**: `pytest tests/test_error_handling.py::TestRequestLogging -v`

### 6. TestErrorResponseFormat
Tests standardized error response structure:
- Validates error response has required fields
- Ensures no stack traces are exposed in responses

**Run**: `pytest tests/test_error_handling.py::TestErrorResponseFormat -v`

### 7. TestGracefulDegradation
Tests service behavior under failure conditions:
- LLM failure handling
- File parsing error clarity

**Run**: `pytest tests/test_error_handling.py::TestGracefulDegradation -v`

## Common Commands

### Run with Different Verbosity Levels

```bash
# Minimal output (only pass/fail)
pytest tests/test_error_handling.py

# Standard output with test names
pytest tests/test_error_handling.py -v

# Very verbose with print statements
pytest tests/test_error_handling.py -vv -s

# Show local variables on failure
pytest tests/test_error_handling.py -v -l
```

### Generate Test Reports

```bash
# Generate HTML coverage report
pytest tests/test_error_handling.py --cov=. --cov-report=html

# Generate XML report (for CI/CD)
pytest tests/test_error_handling.py -v --junit-xml=test-results.xml

# Generate terminal coverage report
pytest tests/test_error_handling.py --cov=. --cov-report=term-missing
```

### Run with Markers

```bash
# Run all tests (no markers applied to this test file)
pytest tests/test_error_handling.py -v

# Run tests matching a pattern
pytest tests/test_error_handling.py -k "exception" -v
pytest tests/test_error_handling.py -k "logging" -v
pytest tests/test_error_handling.py -k "handler" -v
```

### Debugging and Inspection

```bash
# Stop on first failure
pytest tests/test_error_handling.py -v -x

# Stop on first failure and drop into debugger
pytest tests/test_error_handling.py -v -x --pdb

# Show print statements and logging
pytest tests/test_error_handling.py -v -s --log-cli-level=DEBUG

# Collect only (don't run, just show what would run)
pytest tests/test_error_handling.py --collect-only
```

## Full Workflow Example

Complete workflow from project root:

```bash
# 1. Navigate to backend directory
cd backend

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies (if not already installed)
pip install -r requirements.txt

# 4. Navigate to src directory
cd src

# 5. Run the tests
pytest tests/test_error_handling.py -v

# 6. Run specific test class with coverage
pytest tests/test_error_handling.py::TestCustomExceptions -v --cov=exceptions --cov-report=html

# 7. Deactivate virtual environment when done
deactivate
```

## Expected Output

When running successfully, you should see output similar to:

```
tests/test_error_handling.py::TestCustomExceptions::test_latmatrix_exception_base PASSED
tests/test_error_handling.py::TestCustomExceptions::test_file_parsing_error PASSED
tests/test_error_handling.py::TestCustomExceptions::test_validation_error PASSED
tests/test_error_handling.py::TestCustomExceptions::test_llm_backend_error PASSED
tests/test_error_handling.py::TestCustomExceptions::test_unsupported_file_type_error PASSED
tests/test_error_handling.py::TestGlobalExceptionHandlers::test_latmatrix_exception_handler PASSED
tests/test_error_handling.py::TestGlobalExceptionHandlers::test_http_exception_handler_422 PASSED
tests/test_error_handling.py::TestGlobalExceptionHandlers::test_http_exception_handler_404 PASSED
tests/test_error_handling.py::TestGlobalExceptionHandlers::test_unhandled_exception_handler PASSED
tests/test_error_handling.py::TestJSONFormatter::test_json_formatter_basic_log PASSED
tests/test_error_handling.py::TestJSONFormatter::test_json_formatter_with_exception PASSED
tests/test_error_handling.py::TestLoggingConfiguration::test_configure_logging_creates_logger PASSED
tests/test_error_handling.py::TestLoggingConfiguration::test_configure_logging_console_handler PASSED
tests/test_error_handling.py::TestLoggingConfiguration::test_configure_logging_sets_level PASSED
tests/test_error_handling.py::TestRequestLogging::test_request_logging_middleware PASSED
tests/test_error_handling.py::TestRequestLogging::test_request_logging_includes_metadata PASSED
tests/test_error_handling.py::TestErrorResponseFormat::test_error_response_structure PASSED
tests/test_error_handling.py::TestErrorResponseFormat::test_no_stack_trace_in_production PASSED
tests/test_error_handling.py::TestGracefulDegradation::test_llm_failure_returns_partial_result PASSED
tests/test_error_handling.py::TestGracefulDegradation::test_file_parsing_error_is_clear PASSED

===================== 20 passed in 2.34s =====================
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pytest'"

**Solution**: Install test dependencies
```bash
pip install pytest pytest-asyncio
```

### Issue: "ModuleNotFoundError: No module named 'exceptions'"

**Solution**: Ensure you're running pytest from the `backend/src` directory. The `pytest.ini` file sets the Python path correctly.

```bash
cd backend/src
pytest tests/test_error_handling.py -v
```

### Issue: "No such file or directory: tests/test_error_handling.py"

**Solution**: Verify you're in the correct directory. Your working directory should be `backend/src/`:

```bash
cd backend/src
pytest tests/test_error_handling.py -v
```

### Issue: Test fails with "FastAPI app not found"

**Solution**: Ensure `factory.py` is in the same directory. Check imports in `factory.py` point to correct modules.

### Issue: "AsyncioDeprecationWarning" or async test failures

**Solution**: Ensure pytest-asyncio is installed and pytest.ini is configured:
```bash
pip install pytest-asyncio
```

The `pytest.ini` file should already have asyncio markers configured.

## CI/CD Integration

For continuous integration pipelines:

```bash
# Basic CI run with output
pytest tests/test_error_handling.py -v --tb=short

# With coverage report for CI
pytest tests/test_error_handling.py -v --cov=. --cov-report=xml

# With JUnit XML for most CI systems
pytest tests/test_error_handling.py -v --junit-xml=test-results.xml
```

## Related Files

- [`exceptions.py`](../exceptions.py) - Custom exception definitions
- [`factory.py`](../factory.py) - FastAPI app factory with exception handlers
- [`logging_config.py`](../logging_config.py) - Logging configuration and JSON formatter
- [`middleware.py`](../middleware.py) - Request logging middleware
- [`pytest.ini`](../pytest.ini) - Pytest configuration

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing Documentation](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
