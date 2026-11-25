# Sprint 8 Summary — Sprint-8 to Main

**Pull Request:** N/A — Branch `sprint-8` → `main`
**Branch:** `sprint-8` → `main`
**Date:** 2026-05-19
**Total Changes:** +9,789 additions / −2,130 deletions across 67 files

---

## Overview

Sprint 8 represents a major integration milestone consolidating the full PDF type detection pipeline, multilingual OCR support, a redesigned chat UI with two-tab layout, Mistral LLM backend integration, comprehensive test coverage, and infrastructure hardening. Seven feature branches (T1–T7) were merged into `sprint-8` via pull requests, plus several direct commits from two contributors.

## Summary of Issues Completed

| Key | Summary | Type | Status | Assignee |
|-----|---------|------|--------|----------|
| AALA-71 | Add user prompt capability to chat | Task | In Review | Team Member |
| AALA-76 | Add Request & Response Handling | Task | Done | Team Member |
| AALA-93 | Clickable Logo Link to Homepage of Website in Chat UI | Task | In Review | Team Member |
| AALA-96 | Deprecate `backend/src/routes/file_upload.py` | Task | Done | Team Member |

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total additions | 9,789 |
| Total deletions | 2,130 |
| Files changed | 67 |
| New files created | 24 |
| Files deleted | 1 |
| Issues completed | 4 |
| Pull requests merged | 14 |
| New test files | ~15 |
| New services/modules | 5+ |

---

## Files Changed Summary

### New Files (24)

| File | Lines | Category |
|------|-------|----------|
| `backend/docker-entrypoint.sh` | 39 | Infrastructure |
| `backend/src/schemas.py` | 153 | Backend |
| `backend/src/services/parsers/pdf_type_detector.py` | 425 | Services |
| `backend/src/tests/__init__.py` | 1 | Testing |
| `backend/src/tests/services/__init__.py` | 1 | Testing |
| `backend/src/tests/services/parsers/README.md` | 75 | Documentation |
| `backend/src/tests/services/parsers/__init__.py` | 1 | Testing |
| `backend/src/tests/services/parsers/test_ocr_pdf_parser_logging.py` | 217 | Testing |
| `backend/src/tests/services/parsers/test_parser_factory.py` | 162 | Testing |
| `backend/src/tests/services/parsers/test_pdf_type_detector.py` | 772 | Testing |
| `backend/src/tests/services/parsers/test_pdf_type_detector_integration.py` | 424 | Testing |
| `backend/src/tests/services/parsers/test_text_parser_multilingual.py` | 359 | Testing |
| `backend/src/tests/services/parsers/test_word_parser_multilingual.py` | 351 | Testing |
| `backend/src/tests/services/test_accuracy_utilities.py` | 325 | Testing |
| `backend/src/tests/services/test_document_extract.py` | 594 | Testing |
| `backend/src/tests/services/test_summarizer.py` | 406 | Testing |
| `backend/verify_clause_extraction.py` | 141 | Scripts |
| `chat/src/tests/test_ui_scanned_indicator.py` | 275 | Testing |
| `chat/src/utils/pdf_type_detector.py` | 467 | Chat UI |
| `docs/AA686_MonetisationPlan.pdf` | — | Documentation |
| `llm_backend_test_integration.py` | 76 | Testing |
| `run.sh` | 47 | Infrastructure |
| `scripts/manual_test_analyze_endpoint.py` | 181 | Scripts |
| `tests/e2e/test_scanned_pdf_flow.py` | 166 | Testing |

### Deleted Files (1)

| File | Lines | Reason |
|------|-------|--------|
| `backend/src/tests/services/parsers/test_parsers.py` | 475 | Replaced by granular parser-specific test files |

### Modified Files (37)

| File | Lines | Change |
|------|-------|--------|
| `.gitignore` | +3 | Added `.cline/`, `cline*`, `memory-bank/` patterns |
| `AGENTS.md` | +45 | Renamed from `agents.md` with expanded agent instructions |
| `backend/Dockerfile` | +14 / −? | Updated for entrypoint integration |
| `backend/requirements.txt` | +7 / −? | Added `scikit-learn>=1.3`, `jiwer` |
| `backend/src/config.py` | +20 / −? | Configuration updates |
| `backend/src/controllers/document.py` | +461 / −? | Two-step analyzed feature, enhanced processing |
| `backend/src/factory.py` | +13 / −? | App factory pattern updates |
| `backend/src/logging_config.py` | +171 / −? | Refactored for containerised environments |
| `backend/src/main.py` | +7 / −? | Minor updates |
| `backend/src/routes/api.py` | +92 / −? | Re-implemented routes for two-step analyzed feature |
| `backend/src/scripts/document_transformer/doc_transformer/transformer.py` | +388 / −? | Major refactor, Latin/non-Latin font support |
| `backend/src/services/accuracy_calc.py` | +55 / −? | Accuracy calculation utilities |
| `backend/src/services/entity_extractor.py` | +3 | Minor update |
| `backend/src/services/file_handler.py` | +46 / −? | File handling improvements |
| `backend/src/services/file_saver.py` | +30 / −? | File saver service |
| `backend/src/services/llm_backend.py` | +305 / −? | Mistral Open Router backend integration |
| `backend/src/services/nlp_processor.py` | +143 / −? | `analyze_text()` implementation |
| `backend/src/services/parsers/ocr_pdf_parser.py` | +112 / −? | Multilingual handling, type-aware parsing |
| `backend/src/services/parsers/parser_factory.py` | +44 | PDF type-aware routing |
| `backend/src/services/parsers/pdf_parser.py` | +70 / −? | Type-aware parsing enhancements |
| `backend/src/services/summarizer.py` | +86 / −? | `process_document_sync`, graceful error handling |
| `backend/src/services/text_utils.py` | +46 / −? | Text utility improvements |
| `backend/src/tests/conftest.py` | +39 | Test fixtures for parser tests |
| `backend/src/tests/services/parsers/test_ocr_pdf_parser.py` | +365 / −? | Expanded OCR parser tests |
| `backend/src/tests/services/parsers/test_pdf_parser.py` | +405 / −? | Expanded PDF parser tests |
| `backend/src/tests/services/parsers/test_text_parser.py` | +119 | Expanded text parser tests |
| `backend/src/tests/services/parsers/test_word_parser.py` | +269 / −? | Expanded word parser tests |
| `backend/src/tests/services/test_nlp.py` | +195 / −? | NLP service tests |
| `backend/src/utilities/magicNums.py` | +4 / −? | Removed duplicate FastAPI reference |
| `chat/src/components/theme.py` | +25 | Theme component |
| `chat/src/config.py` | +5 | Frontend configuration |
| `chat/src/styles/components.css` | +151 | Expanded chat CSS styles |
| `chat/src/ui.py` | +741 / −? | Two-tab layout redesign |
| `docker-compose.yml` | +4 | Docker volume for backend API logs |
| `scripts/API_Tests/conftest.py` | +77 / −? | API test infrastructure updates |
| `scripts/API_Tests/test_api_upload.py` | +50 | Additional upload tests |
| `scripts/jira/jira_create_issues.py` | +24 / −? | Jira script updates |
| `scripts/jira/jira_update_issues.py` | +5 / −? | Jira script updates |

---

## Key Changes This Sprint
* PDF type detection pipeline for classifying scanned, native, and mixed PDFs
  * New `pdf_type_detector.py` service with parser factory routing
  * Frontend PDF type indicator with premium feature gating in chat UI
  * Integration and unit tests for PDF type detection
* Multilingual OCR and parser enhancements
  * Multilingual text extraction in OCR PDF parser for non-English documents
  * Font fixes in document transformer for Latin and non-Latin character support
  * Multilingual test suites for text and word parsers
* Chat UI redesign with two-tab layout
  * Summary and Extracted Text tabs with expanded CSS styling
  * Pydantic schema modelling for structured API responses
  * Re-implemented routes for two-step analyzed feature
* LLM backend expansion with Mistral AI via Open Router
  * Anthropic model switched to Claude Haiku for cost efficiency
  * Manual test script and integration test utility for LLM backends
* Infrastructure hardening for Docker deployments
  * Docker entrypoint script for log directory permissions
  * Docker volume for backend API logs
  * `run.sh` script with warnings for disabled file logging
* NLP and text processing improvements
  * `NLPService.analyze_text()` implementation with tests
  * `process_document_sync` implementation
  * Fixed hardcoded text truncation — spaCy `max_length` tuned to 5 million
  * Refactored `remove_before_first_clause_one()` with verified clause extraction
* Comprehensive testing expansion
  * Parser tests with multilingual variants, OCR logging, and PDF type detector
  * Accuracy utilities, summarizer service, and NLP service tests
  * E2E scanned PDF flow test and chat UI scanned indicator tests
  * Backend test infrastructure with shared conftest and fixtures

---

## Architecture Diagram

```
                     ┌─────────────────────────────────────┐
                     │         Chat UI (Streamlit)          │
                     │  ┌───────────────────────────────┐   │
                     │  │  Two-Tab Layout               │   │
                     │  │  ┌──────────┐ ┌────────────┐  │   │
                     │  │  │ Summary  │ │ Extracted  │  │   │
                     │  │  │          │ │ Text       │  │   │
                     │  │  └──────────┘ └────────────┘  │   │
                     │  │  PDF Type Indicator (premium)  │   │
                     │  │  pdf_type_detector.py          │   │
                     │  └───────────────────────────────┘   │
                     └──────────────┬──────────────────────┘
                                    │
                     ┌──────────────┴──────────────────────┐
                     │    AI Summarizer (FastAPI)           │
                     │                                      │
                     │  ┌── Routes (/api/) ─────────────┐  │
                     │  │  POST /documents/analyze       │  │
                     │  │  POST /documents/analyze/      │  │
                     │  │    stream (SSE)                │  │
                     │  │  POST /documents/extract-      │  │
                     │  │    entities                    │  │
                     │  └───────────────────────────────┘  │
                     │                                      │
                     │  ┌── Parser Factory ─────────────┐  │
                     │  │  PDF Type Detector ───────┐   │  │
                     │  │  ├─ Scanned → OCRParser   │   │  │
                     │  │  ├─ Native → PDFParser    │   │  │
                     │  │  └─ Mixed  → Hybrid       │   │  │
                     │  │  TextParser / WordParser   │   │  │
                     │  └───────────────────────────┘   │  │
                     │                                      │
                     │  ┌── LLM Backends ──────────────┐  │
                     │  │  ├─ Anthropic (Claude Haiku) │  │
                     │  │  └─ Mistral (Open Router)    │  │
                     │  └───────────────────────────────┘  │
                     │                                      │
                     │  ┌── Services ──────────────────┐  │
                     │  │  NLPService.analyze_text()   │  │
                     │  │  LegalSummarizer             │  │
                     │  │  EntityExtractor             │  │
                     │  │  AccuracyCalculator          │  │
                     │  └───────────────────────────────┘  │
                     │                                      │
                     │  ┌── Infrastructure ────────────┐  │
                     │  │  Structured JSON Logging     │  │
                     │  │  Docker Entrypoint           │  │
                     │  │  Pydantic Schemas            │  │
                     │  └───────────────────────────────┘  │
                     └──────────────────────────────────────┘
```

[AALA-71]: https://yourorg.atlassian.net/browse/AALA-71
[AALA-76]: https://yourorg.atlassian.net/browse/AALA-76
[AALA-93]: https://yourorg.atlassian.net/browse/AALA-93
[AALA-96]: https://yourorg.atlassian.net/browse/AALA-96

---

## 1. PDF Type Detection Pipeline

### 1.1 PDF Type Detection Service ([`pdf_type_detector.py`](backend/src/services/parsers/pdf_type_detector.py))

**Issue:** PDF Type Detection — *Done*

A new PDF type detection service was implemented that classifies PDFs into three categories:

- **Scanned** — Image-based PDFs that require OCR processing
- **Native** — Text-based PDFs that can be parsed directly
- **Mixed** — PDFs containing both text and scanned image pages

#### What Changed

The [`pdf_type_detector.py`](backend/src/services/parsers/pdf_type_detector.py) module (+425 lines) implements classification logic that analyses PDF structure to determine the document type. The [`parser_factory.py`](backend/src/services/parsers/parser_factory.py) was updated (+44 lines) to route documents to the correct parser based on the detected type.

#### Key Components

| Component | Purpose |
|-----------|---------|
| `PDFTypeDetector` | Classifies PDFs as scanned/native/mixed |
| `ParserFactory` | Routes documents to OCR, native, or hybrid parser |
| `OCRPDFParser` | Enhanced for type-aware OCR parsing |
| `PDFParser` | Enhanced for type-aware native parsing |

### 1.2 Frontend PDF Type Indicator ([AALA-76])

**Issue:** Add Request & Response Handling — *Done*

A frontend PDF type detection utility was added at [`chat/src/utils/pdf_type_detector.py`](chat/src/utils/pdf_type_detector.py) (+467 lines) that mirrors the backend detection logic. The chat UI now displays a visual indicator showing whether the uploaded document is scanned or native, with premium feature gating for scanned PDF processing.

#### Files Modified

| File | Change | Purpose |
|------|--------|---------|
| [`chat/src/utils/pdf_type_detector.py`](chat/src/utils/pdf_type_detector.py) | +467 lines | Frontend PDF type detection |
| [`chat/src/ui.py`](chat/src/ui.py) | +741 lines | PDF type-aware UI elements |
| [`chat/src/components/theme.py`](chat/src/components/theme.py) | +25 lines | Theme component |
| [`chat/src/tests/test_ui_scanned_indicator.py`](chat/src/tests/test_ui_scanned_indicator.py) | +275 lines | UI indicator tests |
| [`tests/e2e/test_scanned_pdf_flow.py`](tests/e2e/test_scanned_pdf_flow.py) | +166 lines | End-to-end scanned PDF flow test |

---

## 2. Multilingual OCR & Parser Enhancements

### 2.1 Multilingual Text Extraction

**Issue:** Multilingual OCR Support — *Done*

The [`ocr_pdf_parser.py`](backend/src/services/parsers/ocr_pdf_parser.py) was enhanced with multilingual text extraction capabilities for non-English documents. The document transformer at [`backend/src/scripts/document_transformer/doc_transformer/transformer.py`](backend/src/scripts/document_transformer/doc_transformer/transformer.py) received a major refactor (+388 lines) with font fixes for Latin and non-Latin character support.

#### What Changed

- OCR PDF parser now handles non-English languages during text extraction
- Document transformer font system updated to support Latin and non-Latin character sets
- Multilingual test suites added for both text and word parsers

#### New Test Files

| File | Lines | Purpose |
|------|-------|---------|
| [`test_text_parser_multilingual.py`](backend/src/tests/services/parsers/test_text_parser_multilingual.py) | 359 | Multilingual text parser tests |
| [`test_word_parser_multilingual.py`](backend/src/tests/services/parsers/test_word_parser_multilingual.py) | 351 | Multilingual word parser tests |
| [`test_ocr_pdf_parser_logging.py`](backend/src/tests/services/parsers/test_ocr_pdf_parser_logging.py) | 217 | OCR parser logging tests |

---

## 3. Chat UI Redesign

### 3.1 Two-Tab Layout ([AALA-71])

**Issue:** Add User Prompt Capability to Chat — *In Review*

The chat UI was completely redesigned with a two-tab layout featuring Summary and Extracted Text views. The [`chat/src/ui.py`](chat/src/ui.py) received +741 lines of new code implementing the tabbed interface.

#### What Changed

- Two-tab layout (Summary / Extracted Text) replacing the single-pane design
- Expanded CSS styles in [`chat/src/styles/components.css`](chat/src/styles/components.css) (+151 lines)
- Chat configuration in [`chat/src/config.py`](chat/src/config.py)
- Theme component for consistent styling

### 3.2 Pydantic Schema Modelling

New Pydantic schemas were introduced in [`backend/src/schemas.py`](backend/src/schemas.py) (+153 lines) providing structured data models for API request/response handling. The routes in [`backend/src/routes/api.py`](backend/src/routes/api.py) were re-implemented (+92 lines) for a two-step analyzed feature.

#### Key Components

| File | Lines | Purpose |
|------|-------|---------|
| [`backend/src/schemas.py`](backend/src/schemas.py) | +153 | Pydantic data models |
| [`backend/src/routes/api.py`](backend/src/routes/api.py) | +92 | Two-step analyzed routes |
| [`backend/src/controllers/document.py`](backend/src/controllers/document.py) | +461 | Enhanced document processing |

---

## 4. LLM Backend Expansion

### 4.1 Mistral Open Router Model Backend

**Issue:** Mistral Model Integration — *Done*

Mistral AI was added via Open Router as an additional LLM backend option alongside the existing Anthropic backend. The [`llm_backend.py`](backend/src/services/llm_backend.py) received +305 lines for Mistral integration.

#### What Changed

- New Mistral backend class supporting Open Router API
- Model configuration for Mistral AI models
- Integration test utility at [`llm_backend_test_integration.py`](llm_backend_test_integration.py) (+76 lines)
- Manual test script at [`scripts/manual_test_analyze_endpoint.py`](scripts/manual_test_analyze_endpoint.py) (+181 lines)

### 4.2 Anthropic Model Switch to Claude Haiku

**Issue:** Claude Model Optimisation — *Done*

The Anthropic LLM backend was updated to use `claude-3-haiku` for faster and more cost-effective inference compared to the previous model.

---

## 5. Infrastructure & DevOps

### 5.1 Docker Logging Permission Fix

**Issue:** Docker Logging Fix — *Done*

A logging permission error that occurred when running the backend in Docker was fixed by adding a proper [`docker-entrypoint.sh`](backend/docker-entrypoint.sh) script and Docker volume for logs.

#### What Changed

| File | Change | Purpose |
|------|--------|---------|
| [`backend/docker-entrypoint.sh`](backend/docker-entrypoint.sh) | +39 lines | Log directory setup with correct permissions |
| [`docker-compose.yml`](docker-compose.yml) | +4 lines | Docker volume for backend API logs |
| [`run.sh`](run.sh) | +47 lines | Script with warnings for disabled file logging |
| [`backend/src/logging_config.py`](backend/src/logging_config.py) | +171 lines | Refactored for containerised environments |
| [`backend/Dockerfile`](backend/Dockerfile) | +14 lines | Updated for entrypoint integration |

### 5.2 Dependency Updates

[`backend/requirements.txt`](backend/requirements.txt) was updated with:
- `scikit-learn>=1.3` — ML/metrics functionality
- `jiwer` — Word error rate calculation for accuracy metrics

---

## 6. NLP & Text Processing

### 6.1 NLPService.analyze_text() ([AALA-74])

**Issue:** Implement NLPService.analyze_text() — *Done*

The [`nlp_processor.py`](backend/src/services/nlp_processor.py) was updated (+143 lines) with a new `analyze_text()` method that performs comprehensive NLP analysis including entity recognition, lemmatisation, and linguistic analysis.

### 6.2 process_document_sync

**Issue:** Implement process_document_sync — *Done*

The [`summarizer.py`](backend/src/services/summarizer.py) was updated (+86 lines) with a synchronous `process_document_sync()` wrapper for convenience, along with graceful handling of `file_path.stat()` failures.

### 6.3 Fixed Hardcoded Text Truncation

**Issue:** Fix Hardcoded Text Truncation — *Done*

The spaCy `max_length` was tuned from a hardcoded value to 5 million characters, configurable via environment variable. This prevents `ValueError: [E088]` crashes when processing large legal documents.

### 6.4 Clause Extraction Refactor

**Issue:** Refactor remove_before_first_clause_one() — *Done*

The `remove_before_first_clause_one()` function was refactored and verified against the clause extraction test suite.

### 6.5 Code Cleanup

- Removed duplicate FastAPI reference from [`magicNums.py`](backend/src/utilities/magicNums.py)
- Renamed `agents.md` → [`AGENTS.md`](AGENTS.md) with expanded agent instructions

---

## 7. Testing Expansion

### 7.1 Parser Tests

The parser test suite was significantly expanded with granular test files replacing the monolithic `test_parsers.py`:

| Test File | Lines | Coverage |
|-----------|-------|----------|
| [`test_ocr_pdf_parser.py`](backend/src/tests/services/parsers/test_ocr_pdf_parser.py) | +365 | OCR PDF parser with expanded coverage |
| [`test_ocr_pdf_parser_logging.py`](backend/src/tests/services/parsers/test_ocr_pdf_parser_logging.py) | +217 | OCR parser JSON logging verification |
| [`test_pdf_parser.py`](backend/src/tests/services/parsers/test_pdf_parser.py) | +405 | Native PDF parser with expanded coverage |
| [`test_parser_factory.py`](backend/src/tests/services/parsers/test_parser_factory.py) | +162 | Parser factory routing logic |
| [`test_text_parser.py`](backend/src/tests/services/parsers/test_text_parser.py) | +119 | Text parser tests |
| [`test_text_parser_multilingual.py`](backend/src/tests/services/parsers/test_text_parser_multilingual.py) | +359 | Multilingual text parsing |
| [`test_word_parser.py`](backend/src/tests/services/parsers/test_word_parser.py) | +269 | Word parser with expanded coverage |
| [`test_word_parser_multilingual.py`](backend/src/tests/services/parsers/test_word_parser_multilingual.py) | +351 | Multilingual word parsing |
| [`test_pdf_type_detector.py`](backend/src/tests/services/parsers/test_pdf_type_detector.py) | +772 | PDF type classification |
| [`test_pdf_type_detector_integration.py`](backend/src/tests/services/parsers/test_pdf_type_detector_integration.py) | +424 | PDF type detector integration |

### 7.2 Service Tests

| Test File | Lines | Coverage |
|-----------|-------|----------|
| [`test_accuracy_utilities.py`](backend/src/tests/services/test_accuracy_utilities.py) | +325 | Accuracy calculation metrics |
| [`test_summarizer.py`](backend/src/tests/services/test_summarizer.py) | +406 | LegalSummarizer service (init, summarization, orchestration, error handling) |
| [`test_nlp.py`](backend/src/tests/services/test_nlp.py) | +195 | NLP service (analyze_text, entity extraction) |
| [`test_document_extract.py`](backend/src/tests/services/test_document_extract.py) | +594 | Document extraction pipeline |

### 7.3 E2E & Chat UI Tests

| Test File | Lines | Coverage |
|-----------|-------|----------|
| [`tests/e2e/test_scanned_pdf_flow.py`](tests/e2e/test_scanned_pdf_flow.py) | +166 | End-to-end scanned PDF processing flow |
| [`chat/src/tests/test_ui_scanned_indicator.py`](chat/src/tests/test_ui_scanned_indicator.py) | +275 | Chat UI scanned PDF indicator |

### 7.4 Test Infrastructure

- New [`backend/src/tests/conftest.py`](backend/src/tests/conftest.py) with accuracy fixtures
- New `__init__.py` files for test package structure
- Parser test README at [`backend/src/tests/services/parsers/README.md`](backend/src/tests/services/parsers/README.md)

---

## 8. Bug Fixes

### 8.1 Graceful File Size Handling

**Issue:** Graceful File Size Handling — *Done*

**Symptoms:** When `file_path.stat()` failed with a `PermissionError`, the summarizer would crash instead of handling the error gracefully.

**Root Cause:** The `file_size` attribute was accessed directly without exception handling.

**Fix:** Added `try/except (OSError, PermissionError)` wrapper around `file_path.stat().st_size` so that permission-denied or other filesystem errors do not crash the pipeline; `file_size` defaults to `0` in such cases.

---

## 9. Configuration & Housekeeping

### 9.1 Git Ignore Updates

[`.gitignore`](.gitignore) — Added patterns for:
- `.cline/` — Cline agent directory
- `cline*` — Cline-related files
- `memory-bank/` — Agent memory bank

### 9.2 Agent Configuration

[`AGENTS.md`](AGENTS.md) — Renamed from `agents.md` with expanded agent instructions including:
- Python environment activation requirements
- Capability discovery in `.agents/` directory
- Strict type hinting standards
- Testing requirements with pytest
- Technical stack documentation

### 9.3 Documentation

- Monetisation plan added at [`docs/AA686_MonetisationPlan.pdf`](docs/AA686_MonetisationPlan.pdf)
- Parser test README at [`backend/src/tests/services/parsers/README.md`](backend/src/tests/services/parsers/README.md)
