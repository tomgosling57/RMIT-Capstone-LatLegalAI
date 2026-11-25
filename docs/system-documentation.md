# LatLegal AI: System Documentation

> **Built for LatMatrix**
>
> A multi-service platform that ingests legal documents (PDF, DOCX, TXT),
> extracts text, runs NLP analysis (entities, clauses, language detection),
> and generates plain-English summaries via LLM.
>
> *University capstone project: scope reflects in-progress work.*

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture (Current State)](#2-system-architecture-current-state)
3. [Service Deep Dives](#3-service-deep-dives)
   - 3.1 [Flask Website Service](#31-flask-website-service)
   - 3.2 [Streamlit Chat Service](#32-streamlit-chat-service)
   - 3.3 [Chainlit Conversational AI Service](#33-chainlit-conversational-ai-service)
   - 3.4 [Chainlit Tool Suite (Parsers + NLP)](#34-chainlit-tool-suite-parsers--nlp)
   - 3.5 [FastAPI Backend Service](#35-fastapi-backend-service)
   - 3.6 [Redis](#36-redis)
   - 3.7 [Nginx Reverse Proxy](#37-nginx-reverse-proxy)
4. [Document Processing Pipeline](#4-document-processing-pipeline)
5. [API Reference](#5-api-reference)
6. [Deployment](#6-deployment)
7. [Testing](#7-testing)
8. [Known Duplication & Migration Status](#8-known-duplication--migration-status)
9. [Future Work](#9-future-work)

---

## 1. Project Overview

**LatLegal AI** is a legal document analysis platform that helps users understand
complex legal documents: contracts, trust deeds, articles of incorporation, and
more. Users upload a document and receive a plain-English summary with key
obligations, permissions, risks, and named entities extracted.

The platform supports **PDF** (both digital-native and scanned via OCR), **DOCX**
(Microsoft Word), and **TXT/MD** (plain text) formats. Document processing
happens through a pipeline of format-specific parsers, spaCy NLP for entity
recognition and clause classification, and an LLM (via LiteLLM / OpenRouter) for
summary generation.

Built for **LatMatrix** as a university capstone project, the system uses six
Docker-orchestrated services and is undergoing an active architecture migration.

---

## 2. System Architecture (Current State)

### 2.1 Service Overview

The system runs **six Docker containers** orchestrated by Docker Compose. Nginx
acts as a single entry point, routing traffic to the appropriate service based on
the URL path.

```
                           ┌──────────────┐
                           │    Nginx     │  (port 80; reverse proxy)
                           │  latmatrix-nginx │
                           └──────┬───────┘
                  ┌────────────────┼────────────────┐
                  ▼                ▼                 ▼
           ┌──────────┐   ┌──────────────┐   ┌──────────────┐
           │  Flask   │   │  Streamlit   │   │   Chainlit   │
           │ (website)│   │ (chat UI)    │   │  (AI Chat)   │
           │  :5000   │   │  :8501 /app  │   │  :8001 /chat │
           └─────┬────┘   └──────┬───────┘   └──────┬───────┘
                 │               │                   │
                 └───────┬───────┘                   │
                         │                    ┌──────┴──────┐
                         ▼                    │  SQLite DB  │
                  ┌──────────────┐            │  (Local)    │
                  │    Redis     │            └─────────────┘
                  │  db=0 doc    │
                  │  db=2 rate   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────────────┐
                  │       FastAPI        │
                  │  (storage + legacy)  │
                  │      :8000 /api      │
                  └──────────────────────┘
```

### 2.2 Service Table

| Service | Container Name | Role | Framework | Internal Port |
|---------|---------------|------|-----------|---------------|
| Nginx | `latmatrix-nginx` | Reverse proxy; routes by URL path | nginx:alpine | 80 |
| Website | `latmatrix-website` | Public website (home, auth, pricing) | Flask | 5000 |
| Chat | `latmatrix-chat` | AI analysis UI (auth-gated) | Streamlit | 8501 |
| Chainlit | `latmatrix-chainlit` | Conversational AI interface | Chainlit + LangChain | 8001 |
| API | `latmatrix-api` | Backend storage + legacy processing | FastAPI | 8000 |
| Redis | `latmatrix-redis` | Shared cache (doc bridge + rate limits) | redis:7-alpine | 6379 |

### 2.3 Nginx Routing

| URL Path | Target Service | Notes |
|----------|---------------|-------|
| `/` | Flask (`website:5000`) | Home, auth, pricing pages |
| `/app` | Streamlit (`chat:8501`) | AI analysis UI; requires `/` trailing |
| `/chat` | Chainlit (`chainlit:8001`) | Conversational AI; requires `/` trailing |

Both Streamlit and Chainlit require WebSocket upgrades for real-time
communication (streaming responses, file upload progress).

### 2.4 Two Active Processing Paths

Because of the in-progress architecture migration, there are currently **two
independent document processing paths**:

| Aspect | New Path (Chainlit) | Old Path (FastAPI) |
|--------|--------------------|--------------------|
| Entry point | Chainlit chat UI | Flask upload → FastAPI, or Streamlit → FastAPI |
| Parsing | Local parsers in `chainlit/src/tools/` | Parsers in `backend/src/services/parsers/` |
| NLP | Local NLP in `chainlit/src/tools/` | NLP in `backend/src/services/` |
| LLM | LiteLLM via OpenRouter | Custom `LLMBackend` classes (6 backends) |
| Storage | SQLite (local to Chainlit) | Filesystem via `FileSaver` |
| Status | **Active; primary path** | Active but legacy; being deprecated |

### 2.5 Redis Database Layout

| Database | Purpose | Key Pattern | TTL |
|----------|---------|-------------|-----|
| db=0 | Document context bridge | `pending_doc:<user_id>` | 300s |
| db=2 | Rate-limit counters (Flask-Limiter) | auto-managed | configurable |

---

## 3. Service Deep Dives

### 3.1 Flask Website Service

**Location:** [`website/`](website/)

The Flask service provides the public-facing website: home page, authentication
(login, signup, OAuth), pricing page, and a document upload form that proxies
uploads to the FastAPI backend.

**Framework:** Flask, port **5000**

**Routes:**

| Route | Purpose |
|-------|---------|
| `/` | Home page |
| `/auth` | Login, signup, OAuth redirects |
| `/pricing` | Pricing information |

**Authentication:** Supabase (JWT-based) with OAuth providers (Google, Facebook).
Session management via Flask cookies.

**Templates:** Jinja2 with HTMX for dynamic UI interactions.

**Key Dependencies:**

| Package | Purpose |
|---------|---------|
| `Flask` | Web framework |
| `supabase` | Authentication backend |
| `python-dotenv` | Environment configuration |
| `flask-limiter` | Rate limiting (backed by Redis db=2) |

**Dockerfile:** [`website/Dockerfile`](website/Dockerfile)

---

### 3.2 Streamlit Chat Service

**Location:** [`chat/`](chat/)

An alternative AI analysis UI using Streamlit. Provides document comparison
tools and a developer-facing NLP debugging interface. Auth-gated via Supabase
JWT; users must be logged in through the Flask website.

**Framework:** Streamlit, port **8501**, served at `/app`

**Key Pages:**

| Page | Purpose |
|------|---------|
| `Developer_Tool.py` | NLP debugging: test parsers, view entity extraction |
| (document comparison) | Side-by-side document analysis |

**Dependencies:** Calls FastAPI API endpoints for all document processing; does **not** have local parsers.

**Key Files:**

| File | Purpose |
|------|---------|
| [`chat/src/config.py`](chat/src/config.py) | Service configuration |
| [`chat/src/ui.py`](chat/src/ui.py) | Main UI rendering |
| [`chat/src/auth_guard.py`](chat/src/auth_guard.py) | JWT authentication gate |
| [`chat/src/utils/text_utils.py`](chat/src/utils/text_utils.py) | Text processing utilities |

**Dockerfile:** [`chat/Dockerfile`](chat/Dockerfile)

---

### 3.3 Chainlit Conversational AI Service

**Location:** [`chainlit/`](chainlit/)

The primary AI interface: a Chainlit application that handles document upload,
local parsing, NLP analysis, LLM chat, and summary generation entirely in-process
without HTTP round-trips to FastAPI.

**Framework:** Chainlit + LangChain, port **8001**, served at `/chat`

#### Entry Point

[`chainlit/app.py`](chainlit/app.py); the Chainlit entry point that wires
together lifecycle hooks:

| Hook | Handler | Purpose |
|------|---------|---------|
| `@cl.on_chat_start` | `on_chat_start()` | Initialise memory, runnable, language settings |
| `@cl.on_chat_resume` | `on_chat_resume()` | Reload conversation history |
| `@cl.on_message` | `on_message()` | Route files to processing, text to LLM |
| `@cl.on_settings_update` | `on_settings_update()` | Persist OCR/summary language choices |
| `@cl.on_stop` | `on_stop()` | Handle user stop requests |
| `@cl.on_chat_end` | `on_chat_end()` | Log session end |

#### Authentication

[`chainlit/src/auth.py`](chainlit/src/auth.py); supports two modes:

- **Password auth:** Dev-mode admin credentials (`ADMIN_USERNAME`/`ADMIN_PASSWORD`)
- **OAuth callback:** Third-party providers (Google, GitHub, etc.)

In production, real OAuth user data is used. In dev mode, a mock `dev_user` is
created.

#### Data Layer

[`chainlit/src/database.py`](chainlit/src/database.py); SQLite persistence via
Chainlit's `SQLAlchemyDataLayer`. Schema includes tables for `users`, `threads`,
`steps`, `feedbacks`, and `elements`; all auto-created at import time. A
default admin user is seeded on first run.

Database path: `./data/chainlit.db` (configurable via `CHAINLIT_DB_PATH`).

#### LLM Pipeline

[`chainlit/src/llm.py`](chainlit/src/llm.py); a LangChain `Runnable` pipeline:

```
User Input → Memory (ConversationBufferMemory)
           → Prompt Template (system + history + question)
           → ChatOpenAI (OpenRouter-compatible)
           → StrOutputParser
           → Stream response to user
```

- **Model:** Configurable via `OPENROUTER_MODEL` (default `deepseek/deepseek-chat`)
- **Provider:** OpenRouter API (`https://openrouter.ai/api/v1`)
- **Client:** `ChatOpenAI` from `langchain-openai` (OpenAI-compatible SDK)
- **Streaming:** Tokens streamed via `astream()` with Chainlit callback handler

#### Document Processing

[`chainlit/src/document_processor.py`](chainlit/src/document_processor.py);
orchestrates file upload handling:

1. Validate file size against `MAX_UPLOAD_SIZE` (default 5 MB)
2. Validate file extension against supported formats
3. Parse locally via [`parser_tools.py`](chainlit/src/tools/parser_tools.py)
4. Display extracted text with document statistics
5. Stream LLM analysis
6. Offer download options

#### Language Support

[`chainlit/src/config.py`](chainlit/src/config.py); two independent language
selectors in the ChatSettings UI:

| Setting | Purpose | Options |
|---------|---------|---------|
| OCR Language | Tesseract language for scanned PDFs | English, Hindi, French, Spanish, German (or auto-detect) |
| Summary Language | Target language for LLM-generated summaries | 10 languages including Chinese, Arabic, Urdu, Portuguese |

#### Summary Downloads

[`chainlit/src/summary.py`](chainlit/src/summary.py); provides download
callbacks for generated summaries and extracted text.

#### Configuration

| Environment Variable | Default | Purpose |
|---------------------|---------|---------|
| `OPENROUTER_API_KEY` | `""` | OpenRouter API key |
| `OPENROUTER_MODEL` | `deepseek/deepseek-chat` | LLM model identifier |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | API base URL |
| `MAX_UPLOAD_SIZE_MB` | `5` | Maximum upload size in MB |
| `SPACY_MAX_LENGTH` | `5000000` | spaCy max text length (chars) |
| `CHAINLIT_DB_PATH` | `./data/chainlit.db` | SQLite database path |
| `ADMIN_USERNAME` | `admin` | Dev-mode admin username |
| `ADMIN_PASSWORD` | `admin` | Dev-mode admin password |
| `HOME_PAGE_URL` | `http://localhost:5000` | Link back to Flask website |

#### Dependencies

See [`chainlit/requirements.txt`](chainlit/requirements.txt). Key packages:

- `chainlit`: Chat framework
- `litellm`: Unified LLM interface
- `langchain`, `langchain-openai`, `langchain-classic`: LangChain orchestration
- `pdfplumber`, `python-docx`, `pytesseract`, `pdf2image`, `opencv-python`: Document parsing
- `spacy`, `spacy-lookups-data`, `langdetect`: NLP
- `SQLAlchemy`, `aiosqlite`: Data persistence

**Dockerfile:** [`chainlit/Dockerfile`](chainlit/Dockerfile)

---

### 3.4 Chainlit Tool Suite (Parsers + NLP)

**Location:** [`chainlit/src/tools/`](chainlit/src/tools/)

This is the document processing engine: parsers, NLP processors, and language
detectors that run locally within the Chainlit process.

#### Parser Hierarchy

```
BaseDocumentParser (abstract)
├── PDFParser          - digital/native PDF text extraction (pdfplumber)
├── OCRPDFParser       - scanned PDF OCR (Tesseract + pdf2image + OpenCV)
├── WordParser         - Microsoft Word .docx extraction (python-docx)
└── TextParser         - plain text / markdown (encoding detection)
```

| File | Class | Purpose |
|------|-------|---------|
| [`base_parser.py`](chainlit/src/tools/base_parser.py) | `BaseDocumentParser` | Abstract base with `parse()`, `supports_format()`, metadata helpers |
| [`pdf_parser.py`](chainlit/src/tools/pdf_parser.py) | `PDFParser` | Extract text from digital PDFs via `pdfplumber` |
| [`ocr_pdf_parser.py`](chainlit/src/tools/ocr_pdf_parser.py) | `OCRPDFParser` | OCR for scanned PDFs: Tesseract + image preprocessing |
| [`word_parser.py`](chainlit/src/tools/word_parser.py) | `WordParser` | Extract paragraphs and tables from `.docx` |
| [`text_parser.py`](chainlit/src/tools/text_parser.py) | `TextParser` | Encoding-aware plain text extraction |

#### PDF Type Detection

[`pdf_type_detector.py`](chainlit/src/tools/pdf_type_detector.py);
classifies PDFs into four types:

| Type | Meaning | Action |
|------|---------|--------|
| `DIGITAL` | Born-digital PDF with selectable text | Route to `PDFParser` |
| `SCANNED` | Scanned image-based PDF | Route to `OCRPDFParser` |
| `HYBRID` | Mixed digital + scanned pages | Try `PDFParser`, fallback to OCR |
| `UNKNOWN` | Unable to classify | Try `PDFParser`, fallback to OCR |

#### Parser Factory

[`parser_factory.py`](chainlit/src/tools/parser_factory.py);
`DocumentParserFactory.get_parser()` selects the correct parser:

1. For PDFs: uses `detect_pdf_type()` to classify → routes to `PDFParser` or
   `OCRPDFParser` (with optional language detection)
2. For non-PDFs: iterates parser list checking `supports_format()`
3. OCRPDFParser gets language auto-detected and validated if `detect_lang=True`

#### NLP Tools

| File | Purpose |
|------|---------|
| [`nlp_processor.py`](chainlit/src/tools/nlp_processor.py) | spaCy-based NER, clause classification (obligation/permission/risk), text cleaning |
| [`entity_extractor.py`](chainlit/src/tools/entity_extractor.py) | Named entity extraction (persons, dates, locations) with confidence scoring |
| [`language_detector.py`](chainlit/src/tools/language_detector.py) | OCR language detection via `langdetect`, supported language validation |

#### Tool Registration

[`__init__.py`](chainlit/src/tools/__init__.py); registers Chainlit tools
(`@cl.tool` decorators) for LLM-accessible functions:

| Tool Name | Function | Purpose |
|-----------|----------|---------|
| `parse_pdf` | `parse_pdf()` | Parse a PDF document |
| `parse_word_document` | `parse_word_document()` | Parse a Word document |
| `parse_text_file` | `parse_text_file()` | Parse a text file |
| `detect_pdf_format` | `detect_pdf_format()` | Classify PDF type |
| `get_pdf_metadata` | `get_pdf_metadata()` | Extract PDF metadata |
| `parse_document_auto` | `parse_document_auto()` | Auto-detect and parse |
| `detect_ocr_language` | `detect_ocr_language()` | Detect document language |

#### Orchestration

[`parser_tools.py`](chainlit/src/tools/parser_tools.py); the main entry point
`parse_document()` that:

1. Validates file existence
2. Validates OCR language (if specified)
3. Gets parser from factory (with optional language detection)
4. Calls parser with resolved language
5. Returns `(extracted_pages, page_count, character_count, detected_lang)`

#### File Validation

[`shared/file_validation.py`](shared/file_validation.py); shared MIME-based
file type detection using `python-magic` (libmagic). Used across services.
Handles PDF, DOCX, TXT, PNG, JPEG detection.

> **Note:** A duplicate magic-number check exists at
> [`backend/src/utilities/magicNums.py`](backend/src/utilities/magicNums.py);
> part of the migration consolidation.

---

### 3.5 FastAPI Backend Service

**Location:** [`backend/`](backend/)

Originally the main API for all document processing, the FastAPI service is
being migrated to become a **thin storage service**. It still retains its full
processing pipeline (parsers, NLP, custom LLM backends) but these are now
duplicated from Chainlit and are no longer the primary processing path.

**Framework:** FastAPI, port **8000**

#### Application Factory

[`backend/src/factory.py`](backend/src/factory.py); `create_app()` configures:

- CORS middleware (all origins allowed; restrict in production)
- Request logging middleware
- Global exception handlers for `LatMatrixException`, `HTTPException`, and
  unhandled exceptions
- Health check endpoint (`GET /health`)
- API router at `/api/` prefix
- Conditional dev-only routes (when `DEV_MODE=true`)

#### Route Table

| Endpoint | Method | Purpose | Registration |
|----------|--------|---------|-------------|
| `/health` | GET | Health check | Always |
| `/api/documents/extract-text` | POST | Pure text extraction | Dev-only |
| `/api/documents/extract-entities` | POST | Text + spaCy NER entities | Always |
| `/api/documents/extract` | POST | Text + entities + clause classification | Always |
| `/api/documents/summarize` | POST | LLM summary from file_id or text | Always |
| `/api/documents/analyze` | POST | Full pipeline: extract + entities + LLM | Always |
| `/api/documents/analyze/stream` | POST | Streaming SSE summary | Always |
| `/api/chat/process` | POST | Combined upload + chat (stub) | Always |

#### Controller

[`backend/src/controllers/document.py`](backend/src/controllers/document.py);
`DocumentController` handles all document operations:

- `upload_file()`: extract text + entities
- `extract_document()`: extract + entities + clause classification
- `analyze_document()`: full pipeline with LLM summary
- `summarize_document()`: LLM summary from stored file or direct text
- `stream_summary()`: streaming SSE version of analyze
- `chat_process()`: placeholder for future combined upload + chat

#### Error Handling

[`backend/src/exceptions.py`](backend/src/exceptions.py); structured exception
hierarchy:

| Exception | Status Code | Error Code |
|-----------|-------------|------------|
| `LatMatrixException` | 500 | `INTERNAL_ERROR` |
| `FileParsingError` | 400 | `FILE_PARSING_ERROR` |
| `ValidationError` | 422 | `VALIDATION_ERROR` |
| `LLMBackendError` | 503 | `LLM_BACKEND_ERROR` |
| `EntityExtractionError` | 500 | `ENTITY_EXTRACTION_ERROR` |
| `UnsupportedFileTypeError` | 400 | `UNSUPPORTED_FILE_TYPE` |
| `UnsupportedLanguageError` | 400 | `UNSUPPORTED_LANGUAGE` |

All exceptions return a structured JSON response:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

#### Legacy Components (Deprecated / Duplicated)

| Component | Location | Status |
|-----------|----------|--------|
| PDF Parser | `backend/src/services/parsers/pdf_parser.py` | Duplicate of chainlit |
| OCR PDF Parser | `backend/src/services/parsers/ocr_pdf_parser.py` | Duplicate of chainlit |
| Word Parser | `backend/src/services/parsers/word_parser.py` | Duplicate of chainlit |
| Text Parser | `backend/src/services/parsers/text_parser.py` | Duplicate of chainlit |
| Parser Factory | `backend/src/services/parsers/parser_factory.py` | Duplicate of chainlit |
| PDF Type Detector | `backend/src/services/parsers/pdf_type_detector.py` | Duplicate of chainlit |
| NLP Processor | `backend/src/services/nlp_processor.py` | Duplicate of chainlit |
| Entity Extractor | `backend/src/services/entity_extractor.py` | Duplicate of chainlit |
| LLM Backends (6) | `backend/src/services/llm_backend.py` | Deprecated; replaced by LiteLLM |
| Magic Number Check | `backend/src/utilities/magicNums.py` | Should move to `shared/` |

#### Active Components

| Component | Location | Purpose |
|-----------|----------|---------|
| File Storage | `backend/src/services/file_saver.py` | Persists uploaded files to filesystem |
| File Handler | `backend/src/services/file_handler.py` | File reading and type detection |
| Text Utilities | `backend/src/services/text_utils.py` | Text cleaning and processing |
| Schemas | `backend/src/schemas.py` | Pydantic request/response models |

**Dockerfile:** [`backend/Dockerfile`](backend/Dockerfile)

---

### 3.6 Redis

**Image:** `redis:7-alpine`, port **6379** (internal)

Shared cache service used by two services:

| Database | Consumer | Purpose |
|----------|----------|---------|
| db=0 | Chainlit (future) | Document context bridge; `pending_doc:<user_id>` keys with 300s TTL |
| db=2 | Flask | Rate-limit counters via Flask-Limiter |

**Persistence:** Append-only file, `everysec` fsync.
**Memory:** 256MB limit, `allkeys-lru` eviction policy.

---

### 3.7 Nginx Reverse Proxy

**Location:** [`nginx/nginx.conf`](nginx/nginx.conf)

**Image:** `nginx:alpine`, port **80** (exposed)

Single entry point routing:

| Location | Target | Notes |
|----------|--------|-------|
| `/app/` | `http://streamlit` (chat:8501) | WebSocket upgrade for Streamlit |
| `/chat/` | `http://chainlit:8001` | WebSocket upgrade for Chainlit |
| `/` | `http://flask_app` (website:5000) | Default route |

**Key configuration details:**

- Docker DNS resolver (`127.0.0.11`) with `valid=10s`; forces nginx to
  re-resolve upstream hostnames when containers restart
- Chainlit uses a variable-based `proxy_pass` (`$upstream_chainlit`) to
  avoid DNS caching of container IPs
- Client max body size: 50 MB (supports large file uploads)
- Trailing-slash redirects for `/app` → `/app/` and `/chat` → `/chat/`

---

## 4. Document Processing Pipeline

The document processing pipeline runs locally within the Chainlit process.
This is the **primary processing path**; no HTTP calls to FastAPI are needed.

### 4.1 Pipeline Flow

```
User uploads file
       │
       ▼
┌──────────────────┐
│  File Validation  │  Checks: size (≤5 MB), extension (pdf/docx/txt/md)
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ PDF Type Detect  │  Only for .pdf files. Returns: DIGITAL / SCANNED / HYBRID / UNKNOWN
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Parser Selection │  DocumentParserFactory.get_parser()
│                  │  - DIGITAL → PDFParser
│                  │  - SCANNED → OCRPDFParser (+ language detection)
│                  │  - HYBRID/UNKNOWN → PDFParser (fallback to OCR)
│                  │  - .docx → WordParser
│                  │  - .txt/.md → TextParser
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Text Extraction │  Parser-specific extraction
│                  │  - PDFParser: pdfplumber text extraction
│                  │  - OCRPDFParser: Tesseract OCR (+ language support)
│                  │  - WordParser: python-docx paragraphs + tables
│                  │  - TextParser: encoding-aware plain text
│                  │  Returns: (pages[], page_count, char_count, detected_lang)
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Display Text    │  Show extracted text + document stats in chat
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  LLM Analysis    │  LangChain runnable → LiteLLM / OpenRouter
│                  │  Prompt with extracted text → streaming summary
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Offer Downloads │  Summary + extracted text as downloadable files
└──────────────────┘
```

### 4.2 Language Selection Flow

The ChatSettings UI provides two dropdowns that influence processing:

**OCR Language** affects scanned PDF parsing:

```
User selects "French"
       │
       ▼
OCR_LABEL_TO_CODE["French"] → "fra"
       │
       ▼
parse_document() receives ocr_language="fra"
       │
       ▼
OCRPDFParser uses Tesseract with -l fra
```

**Summary Language** affects LLM output:

```
User selects "Hindi"
       │
       ▼
SUMMARY_LABEL_TO_CODE["Hindi"] → "hi"
       │
       ▼
LLM prompt prefixed with: "Please respond in Hindi language."
```

---

## 5. API Reference

All endpoints are served by the FastAPI service at port 8000. They are available
for direct access or through the auto-generated docs at `http://localhost:8000/docs`.

### 5.1 Endpoint Summary

| # | Endpoint | Method | Purpose | Status |
|---|----------|--------|---------|--------|
| 1 | `/health` | GET | Health check | ✅ Active |
| 2 | `/api/documents/extract-text` | POST | Pure text extraction | 🔧 Dev-only |
| 3 | `/api/documents/extract-entities` | POST | Text + NER entities | ✅ Active |
| 4 | `/api/documents/extract` | POST | Text + entities + clauses | ✅ Active |
| 5 | `/api/documents/summarize` | POST | LLM summary from file_id/text | ✅ Active |
| 6 | `/api/documents/analyze` | POST | Full pipeline (extract + LLM) | ✅ Active |
| 7 | `/api/documents/analyze/stream` | POST | Streaming SSE summary | ✅ Active |
| 8 | `/api/chat/process` | POST | Combined upload + chat | ⏸️ Stub |

### 5.2 Endpoint Details

#### `GET /health`

Health check for monitoring and Docker healthchecks.

**Response 200:**
```json
{ "status": "healthy" }
```

#### `POST /api/documents/extract-text`

Dev-only; pure text extraction without entities or LLM.

**Request:** `multipart/form-data` with `file` (UploadFile) and optional
`extraction_mode` (`"flow"`, `"column"`, or `"ocr"`).

**Response 200:**
```json
{
  "content": ["page 1 text...", "page 2 text..."],
  "filename": "contract.pdf",
  "file_id": "uuid-filename.pdf",
  "upload_timestamp": "2024-01-01T00:00:00.000000Z",
  "status": "success"
}
```

#### `POST /api/documents/extract-entities`

Text extraction + spaCy NER entities.

**Request:** Same as extract-text.

**Response 200:** Adds `entities` object with `names`, `dates`, `locations`,
`all_entities` arrays.

#### `POST /api/documents/extract`

Text extraction + NER entities + clause classification (obligation, permission,
risk). No LLM call.

**Request:** Same as extract-text.

**Response 200:** Structured `ExtractDocumentResponse` with `content`,
`cleaned_text`, `entities` (typed `EntityCollection`), `clauses` (typed
`ClauseItem[]`), file metadata.

#### `POST /api/documents/summarize`

Generate LLM summary from a previously extracted document.

**Request (JSON):**
```json
{
  "file_id": "abc123def456.pdf",
  "max_tokens": 4096
}
```

Or with direct text:
```json
{
  "text": "Full cleaned document text...",
  "entities": {"names": [...], "dates": [...], "locations": [...]},
  "max_tokens": 4096
}
```

**Response 200:**
```json
{
  "success": true,
  "summary": "This agreement between...",
  "llm_entities": "Parties: ACME Corp, Beta Ltd\nDates: January 1, 2024",
  "file_id": "abc123def456.pdf",
  "processing_time_ms": 4523.12
}
```

**Error Responses:** 404 (FILE_NOT_FOUND), 422 (VALIDATION_ERROR),
503 (LLM_BACKEND_ERROR).

#### `POST /api/documents/analyze`

Full pipeline: file upload → text extraction → NER entities → LLM summary.

**Request:** Same as extract-text.

**Response 200:** Combines all data from extract + summarize in one response.

#### `POST /api/documents/analyze/stream`

Streaming version of analyze; LLM summary streamed via Server-Sent Events
(SSE).

**Request:** Same as extract-text.

**Response:** `text/event-stream` with events:

```
data: {"type": "metadata", "filename": "...", "file_id": "...", ...}

data: {"type": "chunk", "content": "This agreement..."}

data: {"type": "chunk", "content": " between the parties..."}

data: {"type": "complete", "summary": "...", "entities": "..."}

data: {"type": "error", "message": "..."}  (on failure)
```

#### `POST /api/chat/process`

**⚠️ Stub; not fully implemented.** Returns a placeholder response.

---

## 6. Deployment

### 6.1 Prerequisites

- Docker (20.10+) and Docker Compose (v2+)
- 4 GB+ RAM recommended (spaCy NLP is memory-intensive)
- For OCR: Tesseract installed in the Chainlit container (handled by Dockerfile)

### 6.2 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd project

# Create environment file (optional; defaults work for development)
cp .env.example .env

# Build and start all services
docker-compose up --build

# Access the application:
#   Website:    http://localhost
#   Chat UI:    http://localhost/app
#   Chainlit:   http://localhost/chat
#   API:        http://localhost:8000
#   API Docs:   http://localhost:8000/docs
```

### 6.3 Environment Variables

| Variable | Default | Services | Purpose |
|----------|---------|----------|---------|
| `OPENROUTER_API_KEY` | `""` | Chainlit | LLM API key (required for AI features) |
| `OPENROUTER_MODEL` | `deepseek/deepseek-chat` | Chainlit | LLM model |
| `SUPABASE_URL` | - | Flask, Streamlit | Supabase project URL |
| `SUPABASE_KEY` | - | Flask, Streamlit | Supabase API key |
| `SECRET_KEY` | - | Flask | Session signing key |
| `CHAINLIT_AUTH_SECRET` | - | Chainlit | JWT signing secret |
| `FLASK_ENV` | `production` | Flask | Environment mode |
| `DEV_MODE` | `""` | FastAPI | Register dev-only routes when `"true"` |
| `MAX_UPLOAD_SIZE_MB` | `5` | Chainlit | Maximum upload size |

### 6.4 Stopping

```bash
docker-compose down
```

To also remove volumes (SQLite data, Redis data, logs):
```bash
docker-compose down -v
```

### 6.5 Legacy Frontend

The original Streamlit prototype is preserved in [`legacy_frontend/`](legacy_frontend/)
for reference. It can be started with:

```bash
docker-compose --profile legacy up
```

---

## 7. Testing

### 7.1 Test Organization

Tests are organized by service with consistent `unit/`, `integration/`, `e2e/`
subdirectories:

| Location | Scope | Notes |
|----------|-------|-------|
| `chainlit/src/tests/` | Chainlit unit + integration | Parser, NLP, OCR, language tests |
| `chat/tests/` | Streamlit UI tests | |
| `backend/src/tests/services/` | Backend unit + integration | Parser, NLP, LLM, summarizer tests |
| `backend/src/tests/services/parsers/` | Parser-specific tests | Multilingual OCR, PDF type detection |
| `tests/` (root) | API integration tests | FastAPI endpoints |
| `tests/e2e/` | End-to-end | Cross-service flows |

### 7.2 Running Tests

```bash
# From project root: API integration tests
pytest tests/

# From backend/src/: Backend unit tests
cd backend/src && pytest tests/unit/

# From backend/src/: Backend integration tests
cd backend/src && pytest tests/integration/

# Slow parser tests require --run-slow flag
cd backend/src && pytest tests/ --run-slow

# Chainlit tests
cd chainlit && pytest src/tests/
```

### 7.3 Test Assets

Sample documents for testing live in service-specific `tests/assets/` directories:

- `chainlit/src/tests/assets/multilingual/`: multilingual PDFs and text files
- `chainlit/src/tests/assets/OCR_test/`: OCR test PDFs (native, scanned)
- `chainlit/src/tests/assets/NLP_test/`: NLP test documents
- `backend/src/tests/services/parsers/`: parser test assets

### 7.4 Conventions

- **Unit tests** test individual functions/classes in isolation
- **Integration tests** test service boundaries (e.g., parser + factory)
- **E2E tests** test cross-service flows (e.g., upload → process → response)
- Slow tests (OCR, large PDFs) require `--run-slow` to opt in
- All new features must include corresponding tests

---

## 8. Known Duplication & Migration Status

The project is mid-migration. Several components exist in **both** the old
location (backend) and the new location (chainlit). This is intentional;
both processing paths function independently during the transition.

### 8.1 Duplicated Components

| Component | Old Location (backend) | New Location (chainlit) | Migration Status |
|-----------|----------------------|------------------------|------------------|
| PDF Parser | `backend/src/services/parsers/pdf_parser.py` | `chainlit/src/tools/pdf_parser.py` | ✅ Migrated, duplicate remains |
| OCR PDF Parser | `backend/src/services/parsers/ocr_pdf_parser.py` | `chainlit/src/tools/ocr_pdf_parser.py` | ✅ Migrated, duplicate remains |
| Word Parser | `backend/src/services/parsers/word_parser.py` | `chainlit/src/tools/word_parser.py` | ✅ Migrated, duplicate remains |
| Text Parser | `backend/src/services/parsers/text_parser.py` | `chainlit/src/tools/text_parser.py` | ✅ Migrated, duplicate remains |
| Parser Factory | `backend/src/services/parsers/parser_factory.py` | `chainlit/src/tools/parser_factory.py` | ✅ Migrated, duplicate remains |
| PDF Type Detector | `backend/src/services/parsers/pdf_type_detector.py` | `chainlit/src/tools/pdf_type_detector.py` | ✅ Migrated, duplicate remains |
| NLP Processor | `backend/src/services/nlp_processor.py` | `chainlit/src/tools/nlp_processor.py` | ✅ Migrated, duplicate remains |
| Entity Extractor | `backend/src/services/entity_extractor.py` | `chainlit/src/tools/entity_extractor.py` | ✅ Migrated, duplicate remains |
| Magic Number Check | `backend/src/utilities/magicNums.py` | `shared/file_validation.py` | 🔄 In progress |
| File Validation | Various places | `shared/file_validation.py` | 🔄 In progress |
| LLM Backends (6) | `backend/src/services/llm_backend.py` | LiteLLM in chainlit | ✅ Replaced, not yet removed |

### 8.2 Current Working State

- **Chainlit** processes documents locally using its own parsers and
  LiteLLM/OpenRouter; this is the **primary path** and works independently.
- **FastAPI** still has all parsers, NLP, and 6 custom LLM backends: these are
  **functional but duplicated**. The FastAPI path is still used by the Flask
  website and Streamlit service.
- **Streamlit** calls FastAPI API endpoints; it does **not** use Chainlit's
  local processing.
- **Chainlit → FastAPI HTTP callback** is **not yet implemented**. When
  completed, Chainlit will stash file metadata in Redis and FastAPI will pick
  it up for persistent storage.

### 8.3 Why Duplication Exists

The migration moves document processing "compute to the data": from a remote
API (FastAPI) to in-process (Chainlit). During this transition, both paths are
kept operational to:

1. Allow the **Streamlit service** to continue working (it depends on FastAPI)
2. Enable incremental testing and validation of the new Chainlit path
3. Preserve the existing API contract for any external consumers

---

## 9. Future Work

### 9.1 Target Architecture

The project is migrating toward a cleaner separation where **Chainlit is the
intelligence hub** and **FastAPI is a thin storage service**:

```
                          ┌──────────────┐
                          │    Nginx     │  (port 80)
                          └──────┬───────┘
               ┌──────────────────┼──────────────────┐
               ▼                                      ▼
        ┌──────────┐                  ┌──────────────────────────────┐
        │  Flask   │                  │          Chainlit            │
        │ (website)│                  │  (Unified AI Interface)      │
        │  :5000   │                  │   :8001 /chat                │
        │          │                  │                              │
        │  auth    │                  │  Document Parsers (local)    │
        │  pricing │                  │  NLP (spaCy)                 │
        │  upload  │                  │  LLM via LiteLLM/OpenRouter  │
        └─────┬────┘                  │  Language Detection          │
              │                       │  SQLite (persistence)        │
              │                       └──────┬──┬───────────────┬────┘
              │                              │  │               │
              └──────────┬───────────────────┘  │               │
                         │                      │               │
                         ▼                      │    ┌──────────┴───┐
                  ┌──────────────┐              │    │   SQLite DB  │
                  │    Redis     │              │    │  (Chainlit)  │
                  │  db=0 doc    │              │    └──────────────┘
                  │  db=2 rate   │              │
                  └──────┬───────┘              │
                         │                      │
                         ▼                      ▼
                ┌───────────────────────────────────────────┐
                │              FastAPI                       │
                │      (storage service only)                │
                │       :8000 /api                           │
                │                                            │
                │  Accepts files via HTTP callback           │
                │  from Chainlit (stashed in Redis)          │
                │  Saves to filesystem                       │
                └───────────────────────────────────────────┘
```

### 9.2 Design Principles for Target State

1. **Chainlit is the intelligence hub**; all parsing, NLP, and LLM logic lives
   here. No HTTP round-trips to FastAPI for processing.
2. **FastAPI is a thin storage layer**; only receives already-parsed documents
   for persistence. No parsers, no NLP, no LLM backends.
3. **LiteLLM replaces all custom LLM backends**; single unified interface
   via `litellm.acompletion()` replaces 6 custom `LLMBackend` classes.
4. **Shared utilities live in `shared/`**; magic number detection, file
   validation, and other cross-service code lives in a top-level `shared/`
   directory, consumed via Dockerfile copy (not a separate service).
5. **Duplication is temporary**; parsers and NLP code currently exist in both
   `backend/` and `chainlit/`. The migration eliminates the backend copies.

### 9.3 Migration Roadmap

| # | Task | Effort | Risk | Depends On |
|---|------|--------|------|------------|
| 1 | Remove duplicate parsers from `backend/src/services/parsers/` | Low | Low; Chainlit is the primary path | - |
| 2 | Remove duplicate NLP from `backend/src/services/` (nlp_processor.py, entity_extractor.py) | Low | Low | - |
| 3 | Remove 6 custom `LLMBackend` classes from `backend/src/services/llm_backend.py` | Medium | Medium; ensure no remaining consumers | - |
| 4 | Move magic number check to `shared/` and consolidate with `shared/file_validation.py` | Low | Low | - |
| 5 | Implement Chainlit → FastAPI HTTP callback for file storage via Redis | Medium | Medium; new integration point | - |
| 6 | Strip FastAPI routes to storage-only endpoints | Medium | High; Streamlit still depends on API | #5, Streamlit migration |
| 7 | Update Dockerfiles for Chainlit (Tesseract, shared utilities) | Low | Low | #4 |

### 9.4 Risk Notes

- **Streamlit dependency:** The Streamlit service still calls FastAPI API
  endpoints for document processing. FastAPI's full processing routes cannot
  be removed until Streamlit is either migrated to use Chainlit or is itself
  deprecated.
- **Callback integration:** The Chainlit → FastAPI HTTP callback is new
  infrastructure and will need careful testing, especially around error
  handling and retry logic.
- **Backward compatibility:** The existing API contract must be preserved
  while both paths are active.

---

> **Document version:** 1.0.0
>
> **Last updated:** 2026-06-08
>
> **Capstone context:** This document describes the system as it currently
> stands, including in-progress migration work and known duplication. See
> [Section 8](#8-known-duplication--migration-status) for details on the
> transition state and [Section 9](#9-future-work) for the target architecture.
