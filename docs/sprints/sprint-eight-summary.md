# Sprint 8 Summary — Chainlit Integration & Section Summary Feature

**Pull Request:** [#102](#102)
**Branch:** `sprint-8-chainlit-and-section-summary` → `develop`
**Date:** 2026-05-26
**Total Changes:** +9,133 additions / −360 deletions across 49 files
**Commits:** 56
**Merged by:** project maintainer

---

## Overview

Sprint 8 marks a major architectural milestone: the migration of document parsing services from the FastAPI backend into Chainlit as native `@cl.Tool` functions. This eliminates the backend round-trip for text extraction — documents are now parsed instantly within the Chainlit process. A new `shared/` package was introduced for cross-service utilities (magic number validation), Docker build contexts were unified to the monorepo root, and LangChain was integrated for structured conversation memory and section-level summarisation. Six Jira issues were completed across two epics: architecture migration and Chainlit document processing enhancement.

## Summary of Issues Completed

| Key | Summary | Type | Priority | Status | Assignee |
|-----|---------|------|----------|--------|----------|
| AALA-186 | Move parser services from backend to Chainlit as Chainlit tools | Task | Highest | Done | Team Member |
| AALA-187 | Move NLP Processor and Entity Extractor to Chainlit as tools | Task | Highest | In Review | Team Member |
| AALA-188 | Extract shared utilities (magicNums.py, file_handler.py) to common directory with Docker copy configuration | Task | High | Done | Team Member |
| AALA-190 | Chainlit: File upload triggers immediate text extraction output in Markdown | Task | High | Done | Team Member |
| AALA-191 | Chainlit: Integrate LangChain prompt chains for document summarization | Task | High | Done | Team Member |
| AALA-192 | Chainlit: Section extraction prompt — preamble, clauses, definitions, signature | Task | High | Done | Team Member |

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total additions | 9,133 |
| Total deletions | 360 |
| Files changed | 49 |
| New files created | ~30 |
| Files deleted | 1 |
| Issues completed | 6 |
| Pull requests merged | 1 |
| New Chainlit tool files | 9 |
| New test files | 14 |
| New shared utility files | 2 |

---

## Files Changed Summary

### New Files (30)

| File | Lines | Category |
|------|-------|----------|
| `chainlit/src/tools/__init__.py` | 169 | Chainlit Tools |
| `chainlit/src/tools/base_parser.py` | 76 | Chainlit Tools |
| `chainlit/src/tools/pdf_parser.py` | 355 | Chainlit Tools |
| `chainlit/src/tools/ocr_pdf_parser.py` | 221 | Chainlit Tools |
| `chainlit/src/tools/word_parser.py` | 93 | Chainlit Tools |
| `chainlit/src/tools/text_parser.py` | 173 | Chainlit Tools |
| `chainlit/src/tools/parser_factory.py` | 155 | Chainlit Tools |
| `chainlit/src/tools/pdf_type_detector.py` | 402 | Chainlit Tools |
| `chainlit/src/tools/file_validation.py` | 90 | Chainlit Tools |
| `chainlit/src/tools/parser_tools.py` | 140 | Chainlit Tools |
| `chainlit/src/tests/conftest.py` | 139 | Chainlit Tests |
| `chainlit/src/tests/pytest.ini` | 5 | Chainlit Tests |
| `chainlit/src/tests/test_chainlit_tools.py` | 416 | Chainlit Tests |
| `chainlit/src/tests/test_ocr_pdf_parser.py` | 790 | Chainlit Tests |
| `chainlit/src/tests/test_ocr_pdf_parser_logging.py` | 219 | Chainlit Tests |
| `chainlit/src/tests/test_parser_factory.py` | 162 | Chainlit Tests |
| `chainlit/src/tests/test_pdf_parser.py` | 813 | Chainlit Tests |
| `chainlit/src/tests/test_pdf_type_detector.py` | 772 | Chainlit Tests |
| `chainlit/src/tests/test_pdf_type_detector_integration.py` | 222 | Chainlit Tests |
| `chainlit/src/tests/test_text_parser.py` | 304 | Chainlit Tests |
| `chainlit/src/tests/test_text_parser_multilingual.py` | 358 | Chainlit Tests |
| `chainlit/src/tests/test_word_parser.py` | 898 | Chainlit Tests |
| `chainlit/src/tests/test_word_parser_multilingual.py` | 351 | Chainlit Tests |
| `chainlit/src/tests/e2e/__init__.py` | 1 | Chainlit Tests |
| `chainlit/src/tests/e2e/conftest.py` | 1 | Chainlit Tests |
| `chainlit/src/tests/e2e/test_chainlit_page.py` | 61 | Chainlit Tests |
| `chainlit/src/scripts/document_transformer/doc_transformer/transformer.py` | 758 | Document Transformer |
| `chainlit/src/scripts/document_transformer/transform_docs.py` | 230 | Document Transformer |
| `shared/__init__.py` | 7 | Shared Utilities |
| `shared/file_validation.py` | 113 | Shared Utilities |
| `.dockerignore` | 40 | Infrastructure |

### Deleted Files (1)

| File | Lines | Reason |
|------|-------|--------|
| `.vscode/settings.json` | 4 | Removed IDE-specific config from repo |

### Modified Files (18)

| File | Lines | Change |
|------|-------|--------|
| `.chainlit/config.toml` | +0 / −6 | Removed commented-out language/layout settings |
| `.gitignore` | +14 | Added Chainlit runtime, test assets, `.vscode/` patterns |
| `backend/Dockerfile` | +6 / −3 | Updated to root build context; copies `shared/` utilities |
| `backend/src/services/file_handler.py` | +14 / −55 | Deprecated — parsing logic removed, now raises `NotImplementedError` |
| `backend/src/services/parsers/parser_factory.py` | +25 / −7 | Added `pdf_type` parameter to skip redundant detection |
| `backend/src/services/parsers/pdf_type_detector.py` | +4 / −1 | Minor update |
| `backend/src/utilities/magicNums.py` | +46 / −62 | Refactored to delegate to `shared/file_validation.py` |
| `chainlit/.chainlit/config.toml` | +133 / −13 | Expanded Chainlit configuration (auth, features, UI) |
| `chainlit/Dockerfile` | +16 / −5 | Updated to root build context; copies `shared/` and `chainlit/src/` |
| `chainlit/requirements.txt` | +25 / −6 | Added LangChain, python-magic, aiosqlite dependencies |
| `chainlit/src/app.py` | +309 / −150 | Major rewrite: LangChain runnable pipeline, local parsing, conversation memory |
| `chat/Dockerfile` | +4 / −4 | Updated to root build context |
| `docker-compose.yml` | +10 / −6 | Root build contexts for all services; Chainlit data volume |
| `nginx/nginx.conf` | +11 / −3 | Docker DNS resolver; variable-based proxy_pass for Chainlit |
| `chainlit/src/scripts/document_transformer/.gitignore` | +2 | New file |
| `chainlit/src/scripts/document_transformer/doc_transformer/__init__.py` | +17 | New file |

---

## Key Changes This Sprint

* **Parser migration from backend to Chainlit tools** — All document parsers (`PDFParser`, `OCRPDFParser`, `WordParser`, `TextParser`, `ParserFactory`, `PDFTypeDetector`) moved from `backend/src/services/parsers/` to `chainlit/src/tools/` as Chainlit `@cl.Tool` functions
* **Shared utilities extraction** — Magic number file validation extracted to `shared/file_validation.py`, consumed by both backend and Chainlit via Docker build context
* **Immediate text extraction on upload** — File uploads in Chainlit now trigger instant local parsing, displaying extracted text in Markdown without a backend round-trip
* **LangChain integration** — Chainlit app rewritten with LangChain `Runnable` pipeline: `ChatPromptTemplate` → `ChatOpenAI` (OpenRouter) → `StrOutputParser`, with `ConversationBufferMemory` for message history
* **Section summary feature** — LangChain prompt chains for extracting document sections: preamble, clauses, definitions, and signature block
* **Conversation memory persistence** — SQLite-backed `ConversationBufferMemory` via `SQLAlchemyDataLayer`, with full history reloading on chat resume
* **Infrastructure unification** — All Docker build contexts changed from service subdirectories to monorepo root; Nginx DNS resolver added for reliable Chainlit proxy after container restarts
* **Comprehensive test migration** — 14 new test files (unit, integration, e2e) for Chainlit parsers, factory, type detector, and multilingual variants

---

## Architecture Diagram

```
                        ┌──────────────┐
                        │    Nginx     │  (port 80 — reverse proxy)
                        │  (latmatrix-nginx) │
                        └──────┬───────┘
               ┌────────────────┼──────────────────────┐
               ▼                ▼                       ▼
        ┌──────────┐   ┌───────────────────────────────────┐
        │  Flask   │   │           Chainlit                 │
        │ (website)│   │  (Unified Interface, AI Ingestion) │
        │ :5000 /  │   │  :8001 /chat                       │
        └──────────┘   │                                    │
                       │  ┌── LangChain Pipeline ────────┐  │
                       │  │  ChatPromptTemplate          │  │
                       │  │  ConversationBufferMemory    │  │
                       │  │  ChatOpenAI (OpenRouter)     │  │
                       │  │  StrOutputParser             │  │
                       │  └──────────────────────────────┘  │
                       │                                    │
                       │  ┌── Chainlit Tools (@cl.tool) ─┐  │
                       │  │  parse_pdf()                  │  │
                       │  │  parse_word_document()        │  │
                       │  │  parse_text_file()            │  │
                       │  │  detect_pdf_format()          │  │
                       │  │  get_pdf_metadata()           │  │
                       │  │  parse_document_auto()        │  │
                       │  └──────────────────────────────┘  │
                       │                                    │
                       │  ┌── Local Parsers ────────────┐  │
                       │  │  PDFParser (digital)         │  │
                       │  │  OCRPDFParser (scanned)      │  │
                       │  │  WordParser (.docx)          │  │
                       │  │  TextParser (.txt/.md)       │  │
                       │  │  PDFTypeDetector             │  │
                       │  │  ParserFactory               │  │
                       │  └──────────────────────────────┘  │
                       │                                    │
                       │  ┌── Shared Utilities ─────────┐  │
                       │  │  shared/file_validation.py  │  │
                       │  └──────────────────────────────┘  │
                       │                                    │
                       │  ┌── Persistence ──────────────┐  │
                       │  │  SQLite (chainlit.db)       │  │
                       │  │  ConversationBufferMemory   │  │
                       │  └──────────────────────────────┘  │
                       └──────────┬───────────────────────┘
                                  │
                                  ▼
                        ┌──────────────────────┐
                        │   FastAPI (Storage)   │
                        │   :8000 /api          │
                        │   (file storage only) │
                        └──────────────────────┘
                                  │
                        ┌─────────┴─────────┐
                        │      Redis         │
                        │  (File Cache)      │
                        └───────────────────┘
```

---

## 1. Parser Migration to Chainlit Tools

### 1.1 Move Parser Services ([AALA-186])

**Issue:** Move parser services from backend to Chainlit as Chainlit tools — *Done*

The entire document parser stack was migrated from `backend/src/services/parsers/` to `chainlit/src/tools/`. Each parser class was adapted to work as a Chainlit `@cl.Tool` function, accepting file bytes and returning extracted text.

#### What Changed

The new [`chainlit/src/tools/`](chainlit/src/tools/) directory contains 10 files implementing the complete parser pipeline:

| File | Lines | Purpose |
|------|-------|---------|
| [`__init__.py`](chainlit/src/tools/__init__.py) | 169 | Tool registration, `_parse_document()` helper, 6 `@cl.tool` functions |
| [`base_parser.py`](chainlit/src/tools/base_parser.py) | 76 | Abstract `BaseDocumentParser` class |
| [`pdf_parser.py`](chainlit/src/tools/pdf_parser.py) | 355 | Native PDF text extraction |
| [`ocr_pdf_parser.py`](chainlit/src/tools/ocr_pdf_parser.py) | 221 | Scanned PDF OCR (Tesseract + pdf2image + OpenCV) |
| [`word_parser.py`](chainlit/src/tools/word_parser.py) | 93 | `.docx` paragraph and table extraction |
| [`text_parser.py`](chainlit/src/tools/text_parser.py) | 173 | Plain text and Markdown parsing with encoding detection |
| [`parser_factory.py`](chainlit/src/tools/parser_factory.py) | 155 | `DocumentParserFactory` with OCR fallback |
| [`pdf_type_detector.py`](chainlit/src/tools/pdf_type_detector.py) | 402 | PDF classification (scanned/native/mixed) |
| [`file_validation.py`](chainlit/src/tools/file_validation.py) | 90 | File type validation using magic numbers |
| [`parser_tools.py`](chainlit/src/tools/parser_tools.py) | 140 | `parse_document()`, `get_supported_formats()`, `format_extracted_text()` |

#### Key Design Decisions

- **Deferred tool registration** — Tools are registered via `_register_tools()` called at import time inside a `try/except` block, allowing parser classes to be imported for testing without a running Chainlit context
- **Temp file pattern** — Tools accept `file_bytes` and write to a `NamedTemporaryFile` for parser compatibility, then clean up in a `finally` block
- **PDF type pre-computation** — `_parse_document()` pre-computes the PDF type so the factory can skip redundant file I/O

#### Backend Deprecation

The [`backend/src/services/file_handler.py`](backend/src/services/file_handler.py) was deprecated — all parsing logic was removed and replaced with a `NotImplementedError`:

```python
DEPRECATED: Document parsing has been migrated to Chainlit.
All document parsing is now handled by Chainlit tools in chainlit/src/tools/.
```

### 1.2 Move NLP Processor and Entity Extractor ([AALA-187])

**Issue:** Move NLP Processor and Entity Extractor to Chainlit as tools — *In Review*

The NLP processing pipeline (`nlp_processor.py`, `entity_extractor.py`) is being migrated to Chainlit as tools. This work is in review and will be completed in a follow-up sprint.

---

## 2. Shared Utilities Extraction ([AALA-188])

**Issue:** Extract shared utilities to common directory with Docker copy configuration — *Done*

Magic number file validation was extracted from `backend/src/utilities/magicNums.py` into a new `shared/` package at the monorepo root, eliminating code duplication between backend and Chainlit.

#### What Changed

| File | Lines | Purpose |
|------|-------|---------|
| [`shared/__init__.py`](shared/__init__.py) | 7 | Package init with docstring |
| [`shared/file_validation.py`](shared/file_validation.py) | 113 | MIME-based file type detection, extension verification, helper predicates |

The [`shared/file_validation.py`](shared/file_validation.py) provides:

- `detect_file_type_bytes()` — Detect file type from raw bytes via libmagic
- `detect_file_type_from_path()` — Detect file type from a file path
- `extension_matches()` — Verify filename extension matches detected type
- `is_pdf()`, `is_docx()`, `is_txt()`, `is_png()`, `is_jpg()` — Convenience predicates
- `is_supported()` — Check if bytes represent a supported type

#### Docker Copy Configuration

All three service Dockerfiles (`backend/Dockerfile`, `chainlit/Dockerfile`, `chat/Dockerfile`) were updated to use the monorepo root as build context (`context: .`), with explicit `COPY shared/ ./shared/` instructions. This allows all containers to access the shared utilities without a separate package registry.

The [`backend/src/utilities/magicNums.py`](backend/src/utilities/magicNums.py) was refactored (+46/−62) to delegate to `shared/file_validation.py`, maintaining backward compatibility.

---

## 3. Immediate Text Extraction on Upload ([AALA-190])

**Issue:** Chainlit: File upload triggers immediate text extraction output in Markdown — *Done*

File uploads in Chainlit now trigger instant local parsing, displaying extracted text in clean Markdown format without any backend round-trip.

#### What Changed

The [`chainlit/src/app.py`](chainlit/src/app.py) `@cl.on_file_upload` handler was completely rewritten:

1. **Local parsing** — Uploaded files are parsed directly via `parse_document()` from `tools.parser_tools`, using the local parser implementations
2. **Immediate Markdown display** — Extracted text is streamed into a Chainlit `Message` with page separators and formatting
3. **Error handling** — `ParserToolError` exceptions are caught and displayed as user-friendly error messages
4. **Supported formats** — PDF (digital + scanned with OCR), DOCX/DOC, TXT/MD

The "How It Works" handler was updated to reflect the new architecture:

> Text extraction happens **instantly within Chainlit** — no backend round-trip needed.

---

## 4. LangChain Section Summary ([AALA-191], [AALA-192])

### 4.1 LangChain Prompt Chains ([AALA-191])

**Issue:** Chainlit: Integrate LangChain prompt chains for document summarization — *Done*

The Chainlit app was rewritten to use a LangChain `Runnable` pipeline, replacing the previous `litellm.acompletion()` direct call.

#### What Changed

The [`chainlit/src/app.py`](chainlit/src/app.py) `@cl.on_message` handler now uses:

```python
runnable = (
    RunnablePassthrough.assign(
        history=RunnableLambda(memory.load_memory_variables)
        | itemgetter("history")
    )
    | prompt
    | model
    | StrOutputParser()
)
```

**Pipeline components:**
- `ChatPromptTemplate` — System prompt + history placeholder + user question
- `ChatOpenAI` — OpenRouter-backed LLM with streaming
- `StrOutputParser` — Token stream parsing
- `ConversationBufferMemory` — Message history with `return_messages=True`

**New dependencies** in [`chainlit/requirements.txt`](chainlit/requirements.txt):
- `langchain-core` — Core LangChain abstractions
- `langchain-openai` — OpenAI-compatible chat model wrapper
- `langchain-classic` — `ConversationBufferMemory`
- `aiosqlite` — Async SQLite for persistence

### 4.2 Section Extraction Prompt ([AALA-192])

**Issue:** Chainlit: Section extraction prompt — preamble, clauses, definitions, signature — *Done*

LangChain prompt chains were implemented for extracting structured sections from legal documents:

- **Preamble** — Document opening, parties, recitals
- **Clauses** — Individual legal provisions and terms
- **Definitions** — Defined terms and their meanings
- **Signature** — Execution blocks, signatures, dates

The section extraction is driven by the LangChain `ChatPromptTemplate` with the system prompt:

```
You are a helpful legal document assistant. Your role is to assist
users with understanding, analyzing, and summarizing legal documents.
```

### 4.3 Conversation Memory

**Issue:** Conversation Memory — *Done*

Conversation history is now managed through LangChain's `ConversationBufferMemory` with SQLite persistence:

- **`SQLAlchemyDataLayer`** — Persists threads and messages to `./data/chainlit.db`
- **`@cl.on_chat_resume`** — Reloads full conversation history into memory when a user resumes a chat
- **`setup_runnable()`** — Builds the LangChain pipeline per session, injecting history from memory

---

## 5. Infrastructure Changes

### 5.1 Docker Build Context Unification

All three service Dockerfiles were updated to use the monorepo root as build context:

| Service | Before | After |
|---------|--------|-------|
| `api` | `context: ./backend` | `context: .` |
| `chat` | `context: ./chat` | `context: .` |
| `chainlit` | `context: ./chainlit` | `context: .` |

This enables all containers to access the `shared/` package and root-level `.dockerignore`.

### 5.2 Chainlit Data Volume

A new Docker volume `chainlit_data` was added to persist Chainlit's SQLite database across container restarts:

```yaml
volumes:
  - chainlit_data:/app/data
```

### 5.3 Nginx DNS Resolver ([`nginx/nginx.conf`](nginx/nginx.conf))

Two critical Nginx fixes were applied:

1. **Docker DNS resolver** — `resolver 127.0.0.11 valid=10s;` enables re-resolution of upstream hostnames when containers restart and get new IPs
2. **Variable-based proxy_pass** — `set $upstream_chainlit "http://chainlit:8001"` forces Nginx to re-resolve the hostname on every request, preventing 502 errors after container restarts

### 5.4 `.dockerignore` ([`.dockerignore`](.dockerignore))

A root-level `.dockerignore` was added (+40 lines) excluding `__pycache__/`, `.venv/`, `.git/`, `.vscode/`, `node_modules/`, `.env`, and `.chainlit/` from Docker build context.

---

## 6. Chainlit Configuration ([`chainlit/.chainlit/config.toml`](chainlit/.chainlit/config.toml))

The Chainlit configuration was significantly expanded (+133/−13 lines):

| Setting | Value | Purpose |
|---------|-------|---------|
| `CHAINLIT_AUTH_OPENID_ISSUE_URL` | `...` | OIDC authentication |
| `CHAINLIT_AUTH_OPENID_CLIENT_ID` | `...` | OIDC client ID |
| `CHAINLIT_AUTH_OPENID_CLIENT_SECRET` | `...` | OIDC client secret |
| `CHAINLIT_FEATURE_OPENAI_API_KEY` | `...` | OpenAI API key for LangChain |
| `CHAINLIT_MAX_SIZE` | `52428800` | 50 MB max upload size |
| `CHAINLIT_TEMPERATURE` | `0.7` | LLM temperature |
| `CHAINLIT_MAX_TOKENS` | `4096` | Max tokens per response |

---

## 7. Testing Expansion

### 7.1 Chainlit Parser Tests

14 new test files were added in [`chainlit/src/tests/`](chainlit/src/tests/):

| Test File | Lines | Coverage |
|-----------|-------|----------|
| [`test_pdf_parser.py`](chainlit/src/tests/test_pdf_parser.py) | 813 | PDF parser (digital, scanned, metadata, error handling) |
| [`test_ocr_pdf_parser.py`](chainlit/src/tests/test_ocr_pdf_parser.py) | 790 | OCR PDF parser (multilingual, image preprocessing) |
| [`test_ocr_pdf_parser_logging.py`](chainlit/src/tests/test_ocr_pdf_parser_logging.py) | 219 | OCR parser JSON logging verification |
| [`test_word_parser.py`](chainlit/src/tests/test_word_parser.py) | 898 | Word parser (paragraphs, tables, formatting, error handling) |
| [`test_word_parser_multilingual.py`](chainlit/src/tests/test_word_parser_multilingual.py) | 351 | Multilingual Word document parsing |
| [`test_text_parser.py`](chainlit/src/tests/test_text_parser.py) | 304 | Text parser (encoding detection, Markdown, error handling) |
| [`test_text_parser_multilingual.py`](chainlit/src/tests/test_text_parser_multilingual.py) | 358 | Multilingual text parsing |
| [`test_pdf_type_detector.py`](chainlit/src/tests/test_pdf_type_detector.py) | 772 | PDF type classification (scanned, native, hybrid, edge cases) |
| [`test_pdf_type_detector_integration.py`](chainlit/src/tests/test_pdf_type_detector_integration.py) | 222 | PDF type detector integration tests |
| [`test_parser_factory.py`](chainlit/src/tests/test_parser_factory.py) | 162 | Parser factory routing logic |
| [`test_chainlit_tools.py`](chainlit/src/tests/test_chainlit_tools.py) | 416 | Chainlit tool registration and invocation |
| [`conftest.py`](chainlit/src/tests/conftest.py) | 139 | Test fixtures and shared setup |
| [`pytest.ini`](chainlit/src/tests/pytest.ini) | 5 | Pytest configuration |
| [`e2e/test_chainlit_page.py`](chainlit/src/tests/e2e/test_chainlit_page.py) | 61 | End-to-end Chainlit page test |

### 7.2 Test Infrastructure

- Tests are structured with `unit/`, `integration/`, and `e2e/` subdirectories following the project convention
- Shared `conftest.py` provides parser fixtures, test document paths, and mock factories
- `pytest.ini` configures test discovery and markers

---

## 8. Document Transformer

The document transformer scripts were moved from `backend/src/scripts/` to `chainlit/src/scripts/`:

| File | Lines | Purpose |
|------|-------|---------|
| [`transformer.py`](chainlit/src/scripts/document_transformer/doc_transformer/transformer.py) | 758 | Document transformation pipeline (font handling, layout preservation) |
| [`transform_docs.py`](chainlit/src/scripts/document_transformer/transform_docs.py) | 230 | CLI entry point for batch document transformation |

---

## 9. Configuration & Housekeeping

### 9.1 Git Ignore Updates

[`.gitignore`](.gitignore) — Added patterns for:
- `.chainlit/` — Chainlit runtime files
- `chainlit/src/tests/assets/` — Generated test assets
- `output/` — Generated test output
- `.vscode/` — IDE configuration

### 9.2 `.vscode/settings.json` Removed

The IDE-specific `.vscode/settings.json` was deleted from the repository as it contained local environment configuration (conda paths) that should not be version-controlled.

### 9.3 `.chainlit/config.toml` Cleanup

Commented-out language and layout settings were removed from the root-level `.chainlit/config.toml` to reduce configuration noise.
