# Sprint 5 Summary — Develop to Main

**Pull Request:** [#63 — Sprint 5: Develop to Main](https://github.com/your-org/latmatrix/pull/63)
**Branch:** `develop` → `main`
**Date:** 2026-05-04
**Total Changes:** +8,773 additions / −494 deletions across 45 files

---

## Overview

Sprint 5 focused on three major themes: **backend API reorganisation and hardening**, **comprehensive API test infrastructure**, and **Jira automation tooling**. The sprint also included two research reports that informed architectural decisions for the project.

## Summary of Issues Completed

| Key           | Summary                                                      | Type   | Status    | Assignee         |
|---------------|--------------------------------------------------------------|--------|-----------|------------------|
| AALA-71       | Add user prompt capability to chat                          | Task   | In Review| Team Member     |
| AALA-74       | Organise API routes properly in the backend                 | Task   | Done      | Team Member                |
| AALA-75       | Create endpoints for upload, process, get result           | Story  | Done| Team Member     |
| AALA-76       | Add request & response handling                            | Task   | Done      | Team Member     |
| AALA-92       | Create comparison report for models and providers           | Task   | Done      | Team Member   |
| AALA-93       | Clickable logo link to homepage in chat UI                 | Task   | In Review| Team Member     |
| AALA-94       | Fix LLM API chunk encoding error                           | Bug    | Done      | Team Member   |
| AALA-95       | Eliminate redundant chat pages and conceal dev tools       | Bug    | Done      | Team Member   |
| AALA-96       | Deprecate `backend/src/routes/file_upload.py`               | Task   | Done| Team Member     |
| —             | Database comparison report (Firebase vs Supabase)           | Task   | Done      | Team Member         |
| AALA-80       | Create Comparison Report — Firebase vs Supabase & RDB vs NoSQL| Task   | Done      | Team Member   |
| AALA-102      | base_parser.uses logging.getLogger() instead of project get_logger()| Task   | Done      | Team Member   |
| AALA-103      | llm_backend.py uses logging.getLogger() instead of project get_logger()| Task   | Done      | Team Member   |
| AALA-104      | jira-update-issues. Uses input list with item.pop('key')    | Task   | Done      | Team Member   |
| AALA-105      | jira-get-issues.py uses API v2                              | Task   | Done      | Team Member   |
| AALA-106      | get_batch_issues() uses POST /rest/api/2/issue/bulkfetch    | Task   | Done      | Team Member   |
| AALA-107      | Relative 'logs' path creates directory based on CWD         | Task   | Done      | Team Member   |
| AALA-108      | Middleware logs query params but main endpoints are POST     | Task   | Done      | Team Member   |
| AALA-109      | Inconsistent async test patterns in TestRequestLogging      | Task   | Done      | Team Member   |
| AALA-110      | Hotfix: Tune spaCy `max_length` and test entity extraction   | Task   | Todo | Team Member     |
| AALA-111      | [PR#62] Fix jira script inconsistencies (AALA 104,105,106)   | Task   | Done      | Team Member   |
| AALA-77       | Add Basic Error Handling                                    | Task   | Done      | Team Member     |
| AALA-78       | Test API Using Python Scripts                               | Task   | Done      | Team Member     |

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total additions | 8,773 |
| Total deletions | 494 |
| Files changed | 45 |
| New files created | 22 |
| Files deleted | 5 |
| Issues completed | 22 |
| Backend test files added | 7 |
| Jira automation scripts added | 4 |
| Custom exception types created | 6 |
| New API endpoints | 5 |
| Deprecated endpoints removed | 3 |

---

## Files Changed Summary

### New Files (22)

| File | Lines | Category |
|------|-------|----------|
| `backend/src/config.py` | 29 | Configuration |
| `backend/src/exceptions.py` | 243 | Error handling |
| `backend/src/logging_config.py` | 263 | Logging |
| `backend/src/middleware.py` | 99 | Middleware |
| `backend/src/routes/api.py` | 227 | Routes |
| `backend/src/tests/test_error_handling.py` | 384 | Testing |
| `backend/src/tests/TEST_ERROR_HANDLING_INSTRUCTIONS.md` | 348 | Documentation |
| `scripts/API_Tests/conftest.py` | 212 | Testing |
| `scripts/API_Tests/generate-env.py` | 334 | Testing |
| `scripts/API_Tests/pytest.ini` | 56 | Testing |
| `scripts/API_Tests/report_generator.py` | 603 | Testing |
| `scripts/API_Tests/run_all_tests.py` | 354 | Testing |
| `scripts/API_Tests/test_api_error_handling.py` | 319 | Testing |
| `scripts/API_Tests/test_api_full_flow.py` | 480 | Testing |
| `scripts/API_Tests/test_api_process.py` | 260 | Testing |
| `scripts/API_Tests/test_api_result.py` | 265 | Testing |
| `scripts/API_Tests/test_api_upload.py` | 215 | Testing |
| `scripts/API_Tests/README.md` | 540 | Documentation |
| `scripts/API_Tests/.gitignore` | 28 | Configuration |
| `scripts/API_Tests/requirements.txt` | 20 | Configuration |
| `scripts/jira/api-docs.md` | 2,299 | Documentation |
| `scripts/jira/jira_get_issues.py` | 225 | Automation |
| `scripts/jira/jira_create_issues.py` | 144 | Automation |
| `scripts/jira/jira_update_issues.py` | 92 | Automation |

### Deleted Files (5)

| File | Lines | Reason |
|------|-------|--------|
| `backend/src/routes/chat.py` | 37 | Consolidated into `api.py` |
| `backend/src/routes/file_upload.py` | 36 | Consolidated into `api.py` |
| `website/app/templates/upload.html` | 115 | Legacy upload removed |
| `website/app/upload/routes.py` | 47 | Legacy upload removed |
| `website/app/upload/__init__.py` | 0 | Legacy upload removed |

---

## Key Changes This Sprint
* Middleware for generalized response and request handling and logging in the AI service
  * Standardized request parameters and response codes for varying request types
  * Implemented modular rotating logging system for monitoring and debugging
* Improved error handling in the AI service.
  * Implemented domain specific exception types for the application and client context
  * Identified potential unguarded code blocks and implemented try catch measures with appropriate exception types
* UI/UX improvements for the chat interface: text prompting and clickable home navigation button using the logo
* Revised routing structure for the AI service
  * Standardized the route naming format
  * Removed redundant routes and created clear explanations of each route's purpose in the readme
* Conditional inclusion of developer tools based on environment variables.
* Extensive end to end api tests for the AI service
* Comparison report of model providers; findings showed that OpenRouter is the most appropriate provider for development
* Comparison report of RDB vs NoSQL appropriateness for use case to inform the choice of authentication provider; Firebase or Supabase. 
  * Report clarified that the relational database is the most appropriate choice for this project.
    * Stable structure is important for standardized metadata based permissions for accessing user uploaded files
    * Schema flexibity provides no benefit during development as the database has no important data meaning it can be repopulated at any time
  * Findings showed that for a scalable and deployment ready product supabase is the most appropriate choice because it provides RDB and significantly cheaper authentication than supabase at scale.
  * Hybrid approach was propose to the client to use supabase for authentication because it is more scalable and a SQLite database for development that can be swapped out for a cloud based alternative at any time

## Architecture Diagram

```
                    ┌─────────────────────────────────┐
                    │     Website Service (Flask)      │
                    │  ┌───────────────────────────┐   │
                    │  │  /auth/*                   │   │
                    │  │  /main/*                   │   │
                    │  └───────────────────────────┘   │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────┴──────────────────┐
                    │     Chat Service (Streamlit)     │
                    │  ┌───────────────────────────┐   │
                    │  │  ui.py (prompt + upload)   │   │
                    │  │  topbar.py (clickable logo)│   │
                    │  │  auth_guard.py (JWT)       │   │
                    │  └───────────────────────────┘   │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────┴──────────────────┐
                    │   AI Summarizer (FastAPI)        │
                    │                                  │
                    │  ┌── Middleware ──────────────┐  │
                    │  │  RequestLoggingMiddleware  │  │
                    │  │  CORSMiddleware            │  │
                    │  └───────────────────────────┘  │
                    │                                  │
                    │  ┌── Routes (/api/) ─────────┐  │
                    │  │  POST /documents/extract-  │  │
                    │  │    text (dev-only)         │  │
                    │  │  POST /documents/extract-  │  │
                    │  │    entities                │  │
                    │  │  POST /documents/analyze   │  │
                    │  │  POST /documents/analyze/  │  │
                    │  │    stream (SSE)            │  │
                    │  │  POST /chat/process (stub) │  │
                    │  └───────────────────────────┘  │
                    │                                  │
                    │  ┌── Exception Handlers ──────┐  │
                    │  │  LatMatrixException         │  │
                    │  │  StarletteHTTPException     │  │
                    │  │  Exception (catch-all)      │  │
                    │  └───────────────────────────┘  │
                    │                                  │
                    │  ┌── Logging ────────────────┐  │
                    │  │  JSONFormatter             │  │
                    │  │  RotatingFileHandler       │  │
                    │  │  FileDebugLogger           │  │
                    │  └───────────────────────────┘  │
                    └──────────────────────────────────┘
```

[AALA-71]: https://yourorg.atlassian.net/browse/AALA-71
[AALA-74]: https://yourorg.atlassian.net/browse/AALA-74
[AALA-75]: https://yourorg.atlassian.net/browse/AALA-75
[AALA-76]: https://yourorg.atlassian.net/browse/AALA-76
[AALA-92]: https://yourorg.atlassian.net/browse/AALA-92
[AALA-93]: https://yourorg.atlassian.net/browse/AALA-93
[AALA-94]: https://yourorg.atlassian.net/browse/AALA-94
[AALA-95]: https://yourorg.atlassian.net/browse/AALA-95
[AALA-96]: https://yourorg.atlassian.net/browse/AALA-96

---

## 1. Backend API Reorganisation & Hardening

### 1.1 Route Consolidation ([AALA-74])

**Issue:** Organise API Routes Properly in the Backend — *Done*

The backend route structure was completely overhauled. Previously, routes were scattered across [`backend/src/main.py`](backend/src/main.py), [`backend/src/routes/chat.py`](backend/src/routes/chat.py), and [`backend/src/routes/file_upload.py`](backend/src/routes/file_upload.py), with duplicate `/upload` endpoints and dead code after return statements.

#### What Changed

All routes were consolidated into a single module at [`backend/src/routes/api.py`](backend/src/routes/api.py) under an `/api/` prefix. The module defines two routers:

- **`router`** (`APIRouter(prefix="/api")`) — always registered, contains the main production endpoints
- **`dev_router`** (`APIRouter(prefix="/api")`) — conditionally registered only when `DEV_MODE=true`

The `should_register_dev_routes()` function in [`backend/src/routes/api.py`](backend/src/routes/api.py:221) controls conditional registration:

```python
def should_register_dev_routes() -> bool:
    return os.getenv("DEV_MODE", "").strip().lower() == "true"
```

In [`backend/src/factory.py`](backend/src/factory.py:85), the routers are registered:

```python
# Register API routes (all under /api/ prefix)
app.include_router(api_router)

# Conditionally register dev-only routes
if should_register_dev_routes():
    logger.info("DEV_MODE enabled — registering dev-only routes")
    app.include_router(dev_router)
```

#### New Endpoint Structure

All routes are consolidated in [`backend/src/routes/api.py`](backend/src/routes/api.py) under a `/api/` prefix.

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/documents/extract-text` | Pure text extraction, **dev-only** (conditional registration), no LLM |
| `POST` | `/api/documents/extract-entities` | Text + spaCy NER entities, replaces legacy `/upload` and `/extract-text-entities` |
| `POST` | `/api/documents/analyze` | Full pipeline: text extraction + entity extraction + LLM summarization |
| `POST` | `/api/documents/analyze/stream` | Streaming LLM summary via Server-Sent Events (SSE) |
| `POST` | `/api/chat/process` | **Future**: combined file upload + chat prompt in one request |

#### Endpoint Details

- **`POST /api/documents/extract-text`** — Dev-only. Only registered when `DEV_MODE=true` is set. Performs pure text extraction from uploaded documents (PDF, DOCX, TXT) without entity extraction or LLM summarization. Defined on `dev_router` in [`backend/src/routes/api.py:208`](backend/src/routes/api.py:208).

- **`POST /api/documents/extract-entities`** — Extracts text and runs spaCy NER to identify legal entities. Replaces the legacy `/upload` and `/extract-text-entities` endpoints. Defined on `router` in [`backend/src/routes/api.py:70`](backend/src/routes/api.py:70).

- **`POST /api/documents/analyze`** — Runs the full processing pipeline: text extraction → entity recognition → LLM-powered summarization. Defined on `router` in [`backend/src/routes/api.py:83`](backend/src/routes/api.py:83).

- **`POST /api/documents/analyze/stream`** — Same full pipeline as `/analyze`, but streams the LLM summary back to the client as SSE events for real-time display. Uses a `StreamingResponse` with `text/event-stream` media type. Defined on `router` in [`backend/src/routes/api.py:94`](backend/src/routes/api.py:94).

- **`POST /api/chat/process`** — Placeholder for a future combined file upload + chat prompt endpoint. Currently returns a stub response indicating the feature is not yet implemented. Defined on `router` in [`backend/src/routes/api.py:181`](backend/src/routes/api.py:181).

#### Files Removed

| File | Lines | Reason |
|------|-------|--------|
| [`backend/src/routes/chat.py`](backend/src/routes/chat.py) | 37 | Routes moved to consolidated `api.py` |
| [`backend/src/routes/file_upload.py`](backend/src/routes/file_upload.py) | 36 | Routes moved to consolidated `api.py` |

#### Files Modified

| File | Change | Purpose |
|------|--------|---------|
| [`backend/src/main.py`](backend/src/main.py) | −29 lines | Removed all route definitions; now only creates the app and runs it |
| [`backend/src/factory.py`](backend/src/factory.py) | +197 lines | Added router registration, exception handlers, CORS, middleware, health check |

### 1.2 Request/Response Handling ([AALA-76])

**Issue:** Add Request & Response Handling — *Done*

Consistent request validation and response formatting was added across all backend endpoints.

#### File Size Validation

A new configuration module [`backend/src/config.py`](backend/src/config.py) was created with centralised settings:

```python
# Maximum file size: 50 MB (configurable via MAX_FILE_SIZE_MB env var)
MAX_FILE_SIZE: Final[int] = _MAX_FILE_SIZE_MB * 1024 * 1024

# Starlette multipart part-size limit: 60 MB (10 MB headroom)
MAX_PART_SIZE: Final[int] = _MAX_PART_SIZE_MB * 1024 * 1024

# spaCy max text length: 1,000,000 characters (configurable)
SPACY_MAX_LENGTH: Final[int] = int(os.getenv("SPACY_MAX_LENGTH", "1000000"))
```

In [`backend/src/factory.py:55`](backend/src/factory.py:55), the Starlette multipart limit is bumped so large uploads reach the application handler (where a proper 413 is returned) instead of being rejected with a generic 400:

```python
MultiPartParser.max_part_size = MAX_PART_SIZE
```

In [`backend/src/controllers/document.py`](backend/src/controllers/document.py), the `upload_file` method now checks file size before processing:

```python
if len(file_bytes) > MAX_FILE_SIZE:
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
```

#### spaCy Length Guard

Entity extraction now checks `SPACY_MAX_LENGTH` before processing. Texts exceeding the limit skip NER gracefully instead of crashing with spaCy's `ValueError: [E088]`:

```python
if len(cleaned_text) > SPACY_MAX_LENGTH:
    entities = {"names": [], "dates": [], "locations": [], "all_entities": []}
else:
    entities = entity_extractor.extract_entities(cleaned_text, min_confidence)
```

#### Structured Error Responses

All endpoints now return consistent JSON with `"success": true/false` and proper HTTP status codes:

| Scenario | Status Code | Response Shape |
|----------|-------------|----------------|
| Success | 200 | `{"success": true, "content": ..., "entities": ...}` |
| File too large | 413 | `{"detail": "File too large..."}` |
| Invalid file | 400 | `{"detail": "Invalid file: ..."}` |
| Processing error | 400 | `{"detail": "Error processing file: ..."}` |
| Validation error | 422 | `{"success": false, "error": {"code": "VALIDATION_ERROR", ...}}` |
| Server error | 500 | `{"success": false, "error": {"code": "INTERNAL_ERROR", ...}}` |

#### Graceful Degradation in analyze_document

The `analyze_document` method in [`backend/src/controllers/document.py`](backend/src/controllers/document.py) now handles errors gracefully:

- **File parsing errors** — caught and re-raised as `FileParsingError` (handled by global exception handler)
- **Entity extraction failures** — logged as warnings but don't block the response; entities default to `{}`
- **LLM failures** — propagate up to the global exception handler as `LLMBackendError`

### 1.3 Global Exception Handling ([`backend/src/exceptions.py`](backend/src/exceptions.py))

A comprehensive exception hierarchy was introduced with 6 custom exception types, all inheriting from a base `LatMatrixException`:

| Exception | Error Code | HTTP Status | Purpose |
|-----------|-----------|-------------|---------|
| `LatMatrixException` | `INTERNAL_ERROR` | 500 | Base class for all application errors |
| `FileParsingError` | `FILE_PARSING_ERROR` | 400 | File cannot be parsed (invalid format, corruption) |
| `ValidationError` | `VALIDATION_ERROR` | 422 | Request validation fails |
| `LLMBackendError` | `LLM_BACKEND_ERROR` | 503 | LLM provider unavailable or returns error |
| `EntityExtractionError` | `ENTITY_EXTRACTION_ERROR` | 500 | spaCy NER pipeline fails |
| `UnsupportedFileTypeError` | `UNSUPPORTED_FILE_TYPE` | 400 | Uploaded file type not in allowed list |

All exceptions implement a `to_dict()` method for safe client-facing responses:

```python
def to_dict(self) -> Dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": self.error_code,
            "message": self.message,
            "details": self.details,
        },
    }
```

Global exception handlers are registered in [`backend/src/factory.py:77`](backend/src/factory.py:77) via `register_exception_handlers(app)`, which handles three tiers:

1. **`LatMatrixException`** — structured error response with error code and details
2. **`StarletteHTTPException`** — maps status codes to error codes (422 → `VALIDATION_ERROR`, 404 → `NOT_FOUND`, etc.)
3. **`Exception`** — generic catch-all that logs the full traceback internally but returns only a safe message to the client

### 1.4 Structured Logging ([`backend/src/logging_config.py`](backend/src/logging_config.py))

A complete structured logging system was implemented (263 lines):

#### JSON Formatter

All logs are output as JSON for machine parsing:

```json
{"timestamp": "2026-05-04T05:34:25.174+00:00", "level": "INFO", "logger": "factory", "message": "FastAPI application initialized successfully", "version": "1.0.0", "max_file_size_mb": 60}
```

#### Rotating File Handlers

| Handler | File | Max Size | Backups | Level |
|---------|------|----------|---------|-------|
| Console | stdout | — | — | Configurable |
| Application | `logs/app.log` | 10 MB | 5 | Configurable |
| Error | `logs/error.log` | 10 MB | 5 | ERROR+ |

#### File Debug Logger

`get_file_debug_logger()` creates a file-only logger that does **not** propagate to the root logger (and therefore does not appear on stdout). This is useful for diagnostic logging under pytest where stdout is captured.

#### safe_extra() Helper

The `safe_extra()` function prevents `KeyError` collisions with standard `LogRecord` attributes. If a key like `"filename"` or `"name"` is passed, it's prefixed with `"ctx_"`:

```python
logger.info("msg", extra=safe_extra(filename="foo.txt", count=42))
# -> extra={"ctx_filename": "foo.txt", "count": 42}
```

### 1.5 Request Logging Middleware ([`backend/src/middleware.py`](backend/src/middleware.py))

A `RequestLoggingMiddleware` was added (99 lines) that:

- Logs all HTTP requests with method, path, and query parameters
- For POST requests, logs Content-Type and Content-Length headers instead of query params
- Records response status code and processing duration in milliseconds
- Logs exceptions during request processing with full traceback

Example log output:
```json
{"timestamp": "...", "level": "INFO", "logger": "middleware", "message": "POST /api/documents/analyze - 200", "method": "POST", "path": "/api/documents/analyze", "status_code": 200, "duration_ms": 1234.56}
```

### 1.6 Controller Improvements ([`backend/src/controllers/document.py`](backend/src/controllers/document.py))

The `DocumentController` was significantly refactored (+322 / −122 lines):

- **File size validation** — returns HTTP 413 before any processing for oversized files
- **spaCy max-length guard** — skips NER for texts exceeding `SPACY_MAX_LENGTH`
- **Graceful error handling** — file parsing errors, LLM failures, and entity extraction errors are handled independently
- **`chat_process()` stub** — placeholder for future file upload + chat prompt endpoint
- **Structured logging** — debug-level logging throughout with `debug_logger` for diagnostic tracing
- **`safe_extra()` usage** — all info-level logs use `safe_extra()` for structured context

### 1.7 LLM Backend Improvements ([`backend/src/services/llm_backend.py`](backend/src/services/llm_backend.py))

The LLM backend was updated (+75 / −41 lines) with:

- Improved error handling for API failures
- Integration with the new structured logging system
- Better handling of streaming responses

### 1.8 Deprecated Route Removal ([AALA-96])

**Issue:** Deprecate `backend/src/routes/file_upload.py` — *In Review*

The legacy file upload route was removed along with the old `backend/src/routes/chat.py` module. All references to these routes were cleaned up across the codebase.

### 1.9 Website Upload Removal

The legacy website upload functionality was completely removed:

| File | Lines Deleted | Reason |
|------|---------------|--------|
| [`website/app/templates/upload.html`](website/app/templates/upload.html) | 115 | Upload functionality moved to backend API |
| [`website/app/upload/routes.py`](website/app/upload/routes.py) | 47 | Upload blueprint removed |
| [`website/app/upload/__init__.py`](website/app/upload/__init__.py) | 0 | Empty init file removed |
| [`website/app/__init__.py`](website/app/__init__.py) | 2 | Upload blueprint unregistered |

---

## 2. API Test Infrastructure

### 2.1 API Test Suite ([`scripts/API_Tests/`](scripts/API_Tests/))

A comprehensive API test suite was created with 7 test files and supporting infrastructure:

#### Test Files

| File | Lines | Purpose |
|------|-------|---------|
| [`test_api_upload.py`](scripts/API_Tests/test_api_upload.py) | 215 | Tests file upload endpoint — validates file types, size limits, and upload responses |
| [`test_api_process.py`](scripts/API_Tests/test_api_process.py) | 260 | Tests document processing endpoint — validates text extraction, entity recognition |
| [`test_api_result.py`](scripts/API_Tests/test_api_result.py) | 265 | Tests result retrieval — validates response structure and data integrity |
| [`test_api_full_flow.py`](scripts/API_Tests/test_api_full_flow.py) | 480 | End-to-end workflow tests — upload → process → verify results |
| [`test_api_error_handling.py`](scripts/API_Tests/test_api_error_handling.py) | 319 | Error handling and edge case tests — invalid files, oversized uploads, missing params |

#### Test Infrastructure

| File | Lines | Purpose |
|------|-------|---------|
| [`conftest.py`](scripts/API_Tests/conftest.py) | 212 | Shared fixtures, test configuration, and mock setup |
| [`pytest.ini`](scripts/API_Tests/pytest.ini) | 56 | Pytest configuration with markers and options |
| [`generate-env.py`](scripts/API_Tests/generate-env.py) | 334 | Environment setup script for test configuration |
| [`report_generator.py`](scripts/API_Tests/report_generator.py) | 603 | Generates HTML/JSON test reports from results |
| [`run_all_tests.py`](scripts/API_Tests/run_all_tests.py) | 354 | Orchestrated test runner with parallel execution support |
| [`README.md`](scripts/API_Tests/README.md) | 540 | Comprehensive documentation for the test suite |
| [`.gitignore`](scripts/API_Tests/.gitignore) | 28 | Git ignore rules for test artifacts |

### 2.2 Backend Error Handling Tests

| File | Lines | Purpose |
|------|-------|---------|
| [`backend/src/tests/test_error_handling.py`](backend/src/tests/test_error_handling.py) | 384 | Unit tests for the new exception hierarchy and error responses |
| [`backend/src/tests/TEST_ERROR_HANDLING_INSTRUCTIONS.md`](backend/src/tests/TEST_ERROR_HANDLING_INSTRUCTIONS.md) | 348 | Instructions for running and interpreting error handling tests |

---

## 3. Jira Automation Tooling

A set of Python scripts was created under [`scripts/jira/`](scripts/jira/) to automate Jira operations:

| File | Lines | Purpose |
|------|-------|---------|
| [`jira_get_issues.py`](scripts/jira/jira_get_issues.py) | 225 | Fetch issues via Jira Bulk Fetch API with 3 output formats |
| [`jira_create_issues.py`](scripts/jira/jira_create_issues.py) | 144 | Create issues programmatically with field validation |
| [`jira_update_issues.py`](scripts/jira/jira_update_issues.py) | 92 | Update existing issues (status, assignee, priority) |
| [`config.py`](scripts/jira/config.py) | 23 | Jira settings read from environment variables |
| [`api-docs.md`](scripts/jira/api-docs.md) | 2,299 | Comprehensive Jira REST API documentation reference |

The `jira_get_issues.py` script supports three output formats:

- **Console** — human-readable formatted output with coloured sections
- **JSON** — machine-parsable JSON output for programmatic consumption
- **Markdown** — documentation-ready Markdown with YAML frontmatter and tables

---

## 4. Chat UI Improvements

### 4.1 Clickable Logo Link ([AALA-93])

**Issue:** Clickable Logo Link to Homepage of Website in Chat UI — *In Review*

- Added a clickable logo button in the Streamlit chat that navigates users back to the website homepage
- The transparent version of the logo was copied into the chat package at [`chat/src/static/LegalAiLogo.png`](chat/src/static/LegalAiLogo.png)
- Modified [`chat/src/components/topbar.py`](chat/src/components/topbar.py) to wrap the logo in an anchor tag pointing to the website URL

### 4.2 User Prompt Capability ([AALA-71])

**Issue:** Add User Prompt Capability to Chat — *In Review*

- Integrated a Streamlit chat input widget into the chat UI
- User input from the prompt is included in requests to the backend API
- Modified the primary flow in [`chat/src/ui.py`](chat/src/ui.py) to pass the prompt to the backend
- The prompt is sent alongside the uploaded document for context-aware processing

### 4.3 Redundant Pages Removed ([AALA-95])

**Issue:** Eliminate Redundant Chat Pages and Conceal Developer Tools — *Done*

- Removed the redundant entity extraction page (`entities.py` → renamed to `entities.py.disabled`)
- Removed the sentiment analysis page from the chat navigation
- Developer Tools page at [`chat/src/pages/Developer_Tool.py`](chat/src/pages/Developer_Tool.py) is now concealed behind a `DEV_MODE` environment variable
- Updated [`chat/src/config.py`](chat/src/config.py) to expose the `DEV_MODE` setting

---

## 5. Bug Fixes

### 5.1 LLM API Chunk Encoding Error ([AALA-94])

**Issue:** Fix LLM API Chunk Encoding Error — *Done*

**Symptoms:** When uploading a file and requesting a summary in the chat, users received a "chunk decoding error" message.

**Root Cause:** The streaming messages response implementation had an encoding mismatch between the LLM provider's chunk format and the SSE parser in the Streamlit client.

**Fix:** Updated the streaming response handling in [`backend/src/routes/api.py`](backend/src/routes/api.py:116) to properly format SSE events with correct `data:` prefixes and JSON-encoded payloads. The `generate_stream()` async generator now sends three event types:

1. **`metadata`** — filename, file_id, upload_timestamp
2. **`chunk`** — incremental summary text chunks
3. **`complete`** — final summary and entities

---

## 6. Research Reports

### 6.1 Database Comparison Report — Firebase vs Supabase

**Issue:** Create Comparison Report — Firebase vs Supabase & RDB vs NoSQL

A comprehensive comparison report was created evaluating database architecture and backend platform choices for the legal document summarization project.

#### Evaluation Areas

| Area | Details |
|------|---------|
| **Relational vs NoSQL** | PostgreSQL vs MongoDB/Firestore — data model fit, query patterns, full-text search |
| **BaaS Providers** | Supabase vs Firebase — features, pricing, scalability |
| **Cost Projections** | Estimated costs at 1K, 10K, 100K, and 1M user scales |
| **Authentication** | Integration details for both providers |
| **Migration Costs** | Effort and risk assessment for migrating between providers |

#### Key Findings

- **Firebase** has higher costs when scaled compared to Supabase, particularly for database operations and bandwidth
- **Supabase** is open source and can be self-hosted, offering cost predictability and data sovereignty
- **PostgreSQL** (Supabase) provides superior full-text search capabilities compared to Firestore's limited query model
- **Relational approach** is better suited for the structured legal document data model with entities, summaries, and user relationships

#### Recommendation

A relational approach powered by Supabase (PostgreSQL) is superior for scalability, cost predictability, and structural integrity.

#### Next Steps

1. Finalise migration of the `DocumentProcessingPipeline` to the Supabase `documents` table
2. Configure Row-Level Security (RLS) policies for `entities` and `summaries` tables
3. Save the report to `docs/database-comparison-report.md`

### 6.2 AI Model Provider Comparison Report ([AALA-92])

**Issue:** Create Comparison Report for Models and Providers — *Done*

A comparison report analysing the benefits and limitations of proprietary providers versus aggregate providers of AI models using APIs.

#### Proprietary Providers

Providers that offer direct API access to their own models (e.g., OpenAI, Anthropic, Google).

| Benefits | Limitations |
|----------|-------------|
| Single provider to manage | Vendor lock-in |
| Consistent API and model behaviour | Limited model choice |
| Direct support and SLAs | Often higher per-token costs |
| Optimised for specific use cases | May lack specialised models |

#### Aggregate Providers

Platforms that aggregate multiple AI models via a single API (e.g., OpenRouter, AWS Bedrock).

| Benefits | Limitations |
|----------|-------------|
| Access to multiple models via one API | Potential latency from routing layer |
| Cost optimisation (choose cheapest model) | Inconsistent model behaviour |
| Fallback options if one provider fails | Complex pricing models |
| Easy model comparison and switching | API surface may be a subset of native APIs |

---

## 7. Configuration & Housekeeping

### 7.1 Linting Configuration

[`.flake8`](.flake8) — Standard Black-compatible ignores shared across the project.

### 7.2 Git Ignore Updates

[`.gitignore`](.gitignore) — Added patterns for:
- `backend/src/logs/` — application log directory
- `*.log` — any log files at any level

### 7.3 Dependency Updates

[`backend/requirements.txt`](backend/requirements.txt):
- Relaxed `python-magic` version constraint from `==0.4.27` to `>=0.4`
- Added Linux dependency note for `libmagic1` system library
- Removed duplicate `python-magic` entry

### 7.4 Documentation Updates

[`backend/README.md`](backend/README.md) — Updated to reflect:
- New consolidated route structure with endpoint table
- Removed references to deprecated `chat.py` and `file_upload.py` modules
- Updated project structure diagram
- Added endpoint details section with purpose descriptions

### 7.5 Utility Refactoring

[`backend/src/utilities/magicNums.py`](backend/src/utilities/magicNums.py) — Refactored (+42 / −28 lines) with improved type hints and cleaner function signatures.

---


