# LatLegal AI — Project Progress Report

**Project:** AA868 Latmatrix Legal Summariser (LaMatrix)
**Period:** Pre-Client Meeting – May 22, 2026
**Team:** 5 members

---

## Overview

This report chronicles the development of LatLegal AI from initial prototyping through to the ongoing architecture migration to Chainlit. The project has progressed through **eight sprint cycles**, evolving from a prototype summarisation script into a multi-service architecture with Chainlit at the centre of document processing.

**Key achievements to date:**
- Complete document parsing pipeline (PDF, DOCX, TXT, scanned/OCR) with multilingual support
- Six LLM backends integrated (OpenAI, Anthropic, OpenRouter, Ollama, Mistral, Mock) — being deprecated for LiteLLM
- Multi-service architecture: Flask website + Streamlit chat + FastAPI backend + Chainlit + Redis + Nginx
- Comprehensive test suite (unit, integration, E2E) with accuracy metrics
- Architecture migration in progress: moving backend services to Chainlit as native tools
- Document section extraction (preamble, definitions, clauses, signatures)
- Downloadable summaries
- Multilingual OCR support for 7 languages

---

## Sprint Timeline

---

### Sprint 1: Pre-Client Meeting — Prototype Phase

**Contributors:** Initial team | **Duration:** Before initial client meeting

- **Prototype Summarisation Script** — Built a working summarisation proof-of-concept using:
  - **pdfminer** for PDF text extraction
  - **spaCy** for hardcoded NLP processing
  - **OpenRouter** for LLM-powered summarisation
- Demonstrated feasibility of the core concept: extract legal text → NLP analysis → LLM summarisation

**Key Outcome:** Validated the technical approach and secured client buy-in for the project.

---

### Sprint 2: March 30 – April 5 — Text Extraction (PDF & Word)

**Team:** 4 members | **Sprint:** Sprint 2

- **Parser Development Started** — Initial work on parsers for PDF and Word document extraction
- **Early OCR Exploration** — Began investigating OCR pipeline for scanned documents
- **Stub Classes Created** — Framework stubs for:
  - Parsers (BaseParser, PDFParser, WordParser, TextParser)
  - NLP processing (NLPService)
  - LLM backends (LLMBackend abstract base)
  - OCR (OCRPDFParser)
  - Summariser (LegalSummarizer)
- **Tests with Sample Files** — Basic test suite using multiple sample legal documents
- **Hosting and Monetisation Report** — Detailed report on available hosting services and monetisation plan for the product

**Challenges:** Establishing dev workflows; determining OCR approach for varying document quality.

---

### Sprint 3: April 6 – April 12 — Parser Completion & NLP Start

**Team:** 4 members | **Sprint:** Sprint 3

- **Parsers Completed**:
  - **TextParser** — UTF-8, BOM handling, plain text extraction
  - **WordParser** — .docx extraction with headings and tables
  - **PDFParser** — pdfplumber-based native PDF extraction with CID normalization
  - **OCRPDFParser** — Tesseract + pdf2image + OpenCV pipeline
- **OCR Basics Implemented** — Functional OCR extraction for scanned documents
- **NLP Started** — Initial text cleaning, basic clause classification via spaCy
- **Async Refactor** — Team Member converted parsers to async for non-blocking operation
- **Entity Extraction Begun** — Team Member created initial spaCy NER implementation

**Key Commits:** 47570f7 (attrib: text parser), c585ce1 (attrib: word parser), f30678d (attrib: PDF parser), b3dad2f (attrib: OCR), aed7d86 (attrib: clause classification), a650415 (attrib: async refactor)

**Challenges:** OCR quality varied across documents; async conversion introduced import issues; entity extraction needed legal domain tuning.

---

### Sprint 4: April 13 – April 19 — LLM Backends, Auth & Branding

**Team:** 3 members | **Sprint:** Sprint 4

- **LLM Backend Framework** — Abstract LLMBackend + factory pattern supporting:
  - **OpenAI** backend integration
  - **Anthropic** backend with rate limiting and retry/backoff
  - **OpenRouter** backend (200+ models via single API)
  - **Mock backend** for testing without credentials
  - API error handling and rate limit management
- **LLM Summary in Streamlit** — First integration of LLM-generated summaries displayed in the Streamlit chat UI
- **API Error Handling** — Error responses and rate limit handling for LLM API calls
- **Logo and Branding** — Created and integrated project logo
- **OAuth Authentication** — Login with Google and Facebook via OAuth integration

**Key Commits:** 8ae80f7 (TomG: PR review skill), ad1fcd5 (TomG: midnight theme), 9250ed7 (TomG: LLM backend merge)

**Challenges:** OpenRouter API format differences compared to native providers; entity extraction still struggled with boilerplate legal text.

---

### Sprint 5: April 20 – April 26 — Document Transformer & NLP Integration

**Contributors:** 3 | **Sprint:** Sprint 5

- **Document Transformer Implemented** — Script for generating test documents with:
  - Multiple file formats (PDF, DOCX, TXT)
  - Various layout styles for testing parser robustness
- **NLP Integration into Summarised Output** — Integrated natural language processing results (entities, clause classifications) directly into the summarised output displayed to users
- **UI Enhancements** — Improvements to the Streamlit chat interface
- **Secure File Upload (AALA-14)** — Cybersecurity-hardened upload pipeline: whitelist extensions, MIME filtering, magic number verification, UUID renaming, path traversal protection
- **Magic Number Validation** — backend/src/utilities/magicNums.py for binary header inspection

**Key Commits:** 0059376 (attrib: Dockerfile), 6a98c27 (attrib: frontend)

**Challenges:** Document transformer had to handle edge cases in layout variations; magic number detection varied across file formats.

---


### Sprint 6: April 27 – May 3 — API Reorganisation & Test Infrastructure

**Contributors:** 4 | **Sprint:** Sprint 6

- **Route Consolidation (AALA-74, PR #69)** — All routes unified in api.py under /api/. file_upload.py and chat.py removed. Dev routes behind DEV_MODE.
  - Organized endpoints: upload, process, and get result
- **Request & Response Handling (AALA-76)** — Consistent request validation and response formatting across all endpoints
- **Basic Error Handling (AALA-77, PR #62)** — attrib: 6 custom exception types in exceptions.py (+243). Global handlers in factory.py (+191). RequestLoggingMiddleware (+99). 384-line test suite.
- **API Test Scripts (AALA-78, PR #54)** — 7 test files, report generator (+603), test runner (+354), conftest (+212), README (+540).
- **Comparison Reports:**
  - **Database Comparison (AALA-80)** — Supabase vs Firebase, Relational vs NoSQL evaluation. Recommendation: Supabase (PostgreSQL) for scalability, cost predictability, and structural integrity.
  - **AI Model Provider Comparison (AALA-92)** — OpenRouter recommended as the most appropriate provider for development.
- **Deprecation (AALA-96, PR #67/69)** — Upload route removed. Website upload template (-115) and blueprint (-47) deleted.
- **Chat UI Enhancements** — User prompt capability (AALA-AALA-71, +89/-82), clickable logo (AALA-93), dev tools hidden (AALA-95).
- **SSE Bug Fix (AALA-94, PR #59)** — Chunk encoding mismatch fixed for streaming responses.
- **Jira Automation** — 4 scripts + 2299-line API documentation.

**PR #63 (Sprint 6 merge):** +8,793/-494 across 45 files.

**Challenges:** Merge conflicts across 4 members; SSE encoding issues; Jira API v2 to v3 migration.

---

### Sprint 7: May 4 – May 17 — OCR Improvements (Two-Week Sprint)

**Team:** 2 members | **Sprint:** Sprint 7

#### Week 1 (May 4-10): NLP, Streaming & Infrastructure

- **SSE Streaming (AALA-117, PR #78)** — attrib: st.write_stream() replaces requests.post(). Loading indicator + error handling.
- **Truncation Fix (AALA-116, PR #75)** — attrib: MAX_STREAM_TEXT_LENGTH = 100k in config. Warning on truncation.
- **analyze_text() (AALA-115, PR #74)** — attrib: nlp_processor.py +111/-53. test_nlp.py +234/-12.
- **process_document_sync() (AALA-114, PR #73)** — attrib: summarizer.py +75/-4. Full pipeline.
- **Duplicate FastAPI Removal (AALA-118, PR #76)** — attrib: magicNums.py -3.
- **Clause Refactor (AALA-121, PR #77)** — attrib: Regex improved. verify_clause_extraction.py +141.
- **spaCy max_length (AALA-110, PR #71)** — attrib: 1M to 5M. Upload test added (+50).
- **Sprint Summary Skill (PR #72)** — TomG: sprint-summary agent skill (+378).
- **Jira Fixes (AALA-104-106, PR #66)** — API v3 migration.

#### Week 2 (May 11-17): Multilingual OCR & Parser Enhancement

- **Multilingual OCR Support** — OCR pipeline extended to support:
  - French, Spanish, German, Hindi language text extraction
  - Additional language packs and Tesseract configuration
- **Document Transformer Updated** — Enhanced to generate legal documents in multiple languages with appropriate fonts (Latin and non-Latin character support)
- **OCR Language & Font Handling** — Updated OCR to handle multilingual documents with related fonts and character sets
- **NLP Tuning** — Refined NLP processing for legal text analysis accuracy
- **Microservices Architecture** — Monolithic setup to multi-service microservices architecture:
  - Website (Flask :5000) with Supabase auth, Flask-Talisman, rate limiting
  - Chat (Streamlit) with auth guard (JWT), clickable logo, conditional dev tools
  - Nginx reverse proxy with WebSocket upgrades
  - Docker Compose: 6 services (Nginx, Flask, Streamlit, FastAPI, Redis)
- **PDF Type Detection Pipeline** — pdf_type_detector.py for classifying scanned, native, and mixed PDFs

**Challenges:** SSE across Streamlit lifecycle; spaCy ~1GB/100k-char memory trade-off; OCR quality varied across different languages and fonts.

---

### Sprint 8: May 18 – Present — Document Sections & Downloadable Summary

**Team:** 3 members | **Sprint:** Sprint 8

- **Document Section Extraction** — Implemented functionality to identify and extract legal document sections:
  - Preamble — Opening recitals and background sections
  - Definitions — Defined terms and interpretive provisions
  - Clauses — Operational provisions and obligations
  - Signatures — Execution blocks and signature pages
- **Downloadable Summary** — Users can now download generated summaries as formatted documents
- **Architecture Migration** — Moving backend parsers and NLP processing to Chainlit as native tools:
  - FastAPI transitioning to storage-only service
  - LiteLLM replacing custom LLMBackend classes (6 backends to single interface)
  - Shared utilities moved to common directory for Docker container reuse

**Key Developments:**
- Parser tools migrated to chainlit/src/tools/
- LangChain integration for prompt-based document summarization
- Chainlit as unified interface for document processing

**Challenges:** Parallel codebase during migration; maintaining feature parity across old and new architectures.

---

## Overall Project Metrics

| Metric | Value |
|--------|-------|
| Total Commits (Mar-May) | 250+ |
| Contributors | 5 |
| Merged PRs | 35+ |
| Open PRs | 5 |
| Largest PR | Sprint 8 merge: +28,456/-1,277 across 239 files |
| Sprints Completed | 8 (Sprint 1: Pre-client, Sprint 2-8) |
| Sprint Duration | Weekly sprints (Sprint 7: two-week sprint) |
| Jira Issues | 50+ created, 30+ completed |
| LLM Backends | 6 (deprecating for LiteLLM) |
| Parser Types | 4 + PDF Type Detector |
| OCR Languages | 7 (English, Hindi, French, Spanish, German, Italian, Portuguese) |
| Test Files | 30+ across unit/integration/E2E |

---

## Contributors

| Person | Focus | Key PRs | Top Issues |
|--------|-------|---------|------------|
| Team Member | Architecture, Chainlit, LLM, docs, PR mgmt | #53, #55, #61, #63, #86, #87, #88, #93 | AALA-184/185, AALA-92/94/95, AALA-119/120 |
| Contributor A | Parsers, NLP, OCR, PDF detection, tests, Chainlit tools | #54, #62, #71-80, #84, #85 | AALA-125/126/129, AALA-141/146, AALA-186/187/190/193 |
| Contributor B | Chat UI, auth, file security, subscriptions | #64, #67 | AALA-71/76/93/96, AALA-170/180 |
| Contributor C | UI/UX design, branding, presentations | Design contributions | AALA-65, AALA-195 |
| Contributor D | Early NLP, clause classification, OCR | Early commits | Initial parsers + NLP |

---

## Architectural Decisions

1. Prototype (Sprint 1) — pdfminer + spaCy + OpenRouter for feasibility validation
2. Parser Framework (Sprint 2-3) — Abstract BaseParser with factory pattern for extensibility
3. LLM Backend Abstraction (Sprint 4) — Factory pattern for multiple LLM providers with unified interface
4. Microservices (Sprint 7) — Monolith to 6 services behind Nginx
5. Supabase over Firebase (Sprint 6) — PostgreSQL for relational legal data
6. OpenRouter (Sprint 6) — 200+ models via single API
7. Chainlit as Unified Interface (Sprint 8) — FastAPI becomes storage-only
8. LiteLLM (Sprint 8) — Deprecating 6 custom backends for single interface
9. Common Utilities via Docker COPY (Sprint 8) — Shared code without new service

---

## Challenges & Risks

| Challenge | Impact | Status |
|-----------|--------|--------|
| Duplicate pdf_type_detector | Maintenance burden | AALA-178 To Do |
| Hybrid PDF text+scanned | Incomplete extraction | AALA-177 To Do |
| Chainlit migration | Parallel codebase | Ongoing |
| Path traversal in FileSaver | Security risk | AALA-180 |
| chmod 777 in entrypoint | Security risk | AALA-170 |
| OCR quality across languages | Varied accuracy | Ongoing tuning |

---

## Sprint Timeline Summary

| Sprint | Dates | Focus |
|--------|-------|-------|
| Sprint 1 | Pre-Client Meeting | Prototype summarisation (pdfminer + spaCy + OpenRouter) |
| Sprint 2 | Mar 30 - Apr 5 | Text Extraction (PDF & Word), stub classes, hosting report |
| Sprint 3 | Apr 6 - Apr 12 | Parsers completed, OCR basics, NLP started |
| Sprint 4 | Apr 13 - Apr 19 | LLM backends, Streamlit summary, OAuth, branding |
| Sprint 5 | Apr 20 - Apr 26 | Document transformer, NLP integration, UI enhancements |
| Sprint 6 | Apr 27 - May 3 | API reorganisation, test infrastructure, comparison reports |
| Sprint 7 | May 4 - May 17 | Multilingual OCR, NLP tuning, streaming (two-week sprint) |
| Sprint 8 | May 18 - present | Document sections, downloadable summary, Chainlit migration |

Sprints overlapped significantly during transition periods. Sprint 7 was a two-week sprint due to the complexity of multilingual OCR integration.
