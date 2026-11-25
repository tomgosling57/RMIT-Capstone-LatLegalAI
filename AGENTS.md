# Project: LatLegal AI — Built for LatMatrix

## Core Instructions
- **Python Environment**: The agentic terminal is a **shell terminal** (bash). Before running any Python code, activate the project's virtual environment: `. .venv/bin/activate`. Do not assume Python packages are globally available.
- **Linting & Formatting**: Run `black --check .` (88-char line length), `flake8`, and `mypy` before committing. Pre-commit hooks enforce these.
- **Capability Discovery**: Look in the `.agents/` directory for available skills: `jira/` (issue management), `github/` (PR creation, review, stacked PRs), `sprint-summary/` (sprint reports), `meta-skills/` (skill-writing guidance).
- **Development Standard**: Use strict type hints for all Python functions and class definitions. Comments should be clean and functional — no decorative comment banners (`# ===`, `# ---`).
- **Testing**: All new features or logic changes must include corresponding pytest tests (see Testing Conventions section below).

## Technical Stack

| Component               | Technology                                                     |
|-------------------------|----------------------------------------------------------------|
| Backend / Storage       | FastAPI (port 8000, serves `/api` routes)                      |
| Website                 | Flask (port 5000 — auth, home, pricing, upload proxy)          |
| Chat UI                 | Streamlit (port 8501 — AI document analysis, route `/app`)     |
| Conversational AI       | Chainlit (port 8001 — doc analysis via chat, route `/chat`)    |
| Reverse Proxy           | Nginx (WebSocket upgrade for Streamlit & Chainlit)             |
| Shared Cache            | Redis (db=0 doc context, db=2 rate limiting)                   |
| NLP Engine              | spaCy (NER, lemmatization, linguistic analysis)                |
| LLM Integration         | 6 backends via abstract `LLMBackend` + factory                 |
| OCR Pipeline            | Tesseract + pdf2image + OpenCV (scanned PDFs)                  |
| Auth                    | Supabase (Flask website) + OAuth (Chainlit: Google, GitHub, etc.) |
| Translation             | `deep-translator` for multilingual summaries                   |
| Testing                 | pytest (see conventions below)                                 |
| Containerisation        | Docker Compose (all 6 services orchestrated)                   |
| Code Quality            | Black, Flake8, mypy, pre-commit hooks                          |

## Architecture Diagram

```
                        ┌──────────────┐
                        │    Nginx     │  (port 80 — reverse proxy)
                        │  (latmatrix-nginx) │
                        └──────┬───────┘
               ┌────────────────┼──────────────┐
               ▼                                ▼
        ┌──────────┐            ┌────────────────────────────────┐
        │  Flask   │            │           Chainlit             │
        │ (website)│            │ (Unified Interface, AI Ingestion & Tools)│
        │ :5000 /  │            │  :8001 /chat  (LiteLLM Enabled)│
        └─────┬────┘            └──────┬──┬───────────────┬──────┘
              │                        │  │               │
              └────────┬───────────────┘  │               │ 1. Unified Parsed MD Stream
                       │                  │               │ 2. Callback HTTP Trigger
                       ▼                  │   ┌───────────┴───┐
                ┌───────────────┐         |   │   SQLite DB   │
                |   Redis       |         |   │ (Local State) │
                |  (File Cache) |         |   └───────────────┘
                └───────────────┘         |
                       |                  |
                       ▼                  ▼
              ┌──────────────────────────────────────────────────┐
              │                     FastAPI                      │
              │         (latmatrix-api — Storage Service)        │
              │                  :8000 /api                      │
              └──────────────────────────────────────────────────┘
```

## Architecture Change & Refactoring (In Progress)

We are migrating to a new architecture where the **backend (FastAPI)** becomes a **storage service** managing file storage only. The following moves are underway:

- **Backend parsers** (`PDFParser`, `OCRPDFParser`, `WordParser`, `TextParser`), **NLP processing** (`nlp_processor.py`, `entity_extractor.py`), **magic number check** (`utilities/magicNums.py`), and **file validation** (`file_handler.py`) are being moved to **Chainlit as tools**.
- **Shared utilities** (magic number check and file validation) should be moved **up a directory** out of these specific services, then copied into Docker containers via Dockerfile configuration — reducing code duplication without creating a whole new service.
- **FastAPI** becomes the **storage service**: receiving files stashed in Redis, triggered by an HTTP callback from Chainlit.
- **Custom `LLMBackend` classes** (`OpenAIBackend`, `AnthropicBackend`, `OllamaBackend`, `OpenRouterBackend`, `OpenRouterMistralBackend`, `MockBackend`) are being **deprecated** in favour of **LiteLLM** (`litellm` package), which is already the primary LLM integration in Chainlit. LiteLLM provides a unified interface to 100+ models and replaces the need for custom backend wrappers.

> **Preserve the existing virtual environment, linting config (Black, Flake8, mypy), and terminal instructions** throughout this migration.
>
> **Chainlit dependency note**: The Chainlit service uses `ConversationBufferMemory` from `langchain_classic.memory` (the `langchain-classic` package). This is because in LangChain v0.3+, `ConversationBufferMemory` was removed from the core `langchain` package. The `langchain-classic` package provides backward compatibility. Ensure `langchain-classic` is listed in [`chainlit/requirements.txt`](chainlit/requirements.txt) whenever this import is used.

## Document Processing Pipeline

```
Upload → ParserFactory.select_parser() → BaseParser subclass
       → PDFTypeDetector (native vs scanned) → OCRPDFParser if needed
       → Text extraction → spaCy NLP (NER, lemmatisation)
       → LLMBackend.summarise() → Summary + Entities
```

**Parser hierarchy** (in [`backend/src/services/parsers/`](backend/src/services/parsers/)):
- [`base_parser.py`](backend/src/services/parsers/base_parser.py) — abstract `BaseParser` class
- [`pdf_parser.py`](backend/src/services/parsers/pdf_parser.py) — native PDF text extraction
- [`ocr_pdf_parser.py`](backend/src/services/parsers/ocr_pdf_parser.py) — scanned PDF OCR (Tesseract + pdf2image + OpenCV)
- [`word_parser.py`](backend/src/services/parsers/word_parser.py) — `.docx` extraction
- [`text_parser.py`](backend/src/services/parsers/text_parser.py) — plain text extraction
- [`parser_factory.py`](backend/src/services/parsers/parser_factory.py) — `ParserFactory.select_parser()` dispatcher
- [`pdf_type_detector.py`](backend/src/services/parsers/pdf_type_detector.py) — distinguishes native vs scanned PDFs

**File storage abstraction** (in [`backend/src/services/storage/`](backend/src/services/storage/)):
- [`base.py`](backend/src/services/storage/base.py) — `FileStorage` interface
- [`local_storage.py`](backend/src/services/storage/local_storage.py) — local filesystem backend
- [`redis_storage.py`](backend/src/services/storage/redis_storage.py) — Redis-backed storage

## Testing Conventions

| Location                              | Scope                          |
|---------------------------------------|--------------------------------|
| `backend/src/tests/services/`         | Unit + integration tests       |
| `backend/src/tests/services/parsers/` | Parser tests (incl. multilingual OCR) |
| `chat/tests/`                         | Streamlit tests                |
| `chainlit/tests/`                     | Chainlit e2e tests             |
| `tests/` (root)                       | API integration tests          |
| `tests/e2e/`                          | Root-level end-to-end tests    |

Run tests: `pytest tests/` from root or `pytest tests/unit/` from `backend/src/`. Slow parser tests require `--run-slow`.

## Git Workflow

- `main` — production releases (tagged)
- `develop` — integration branch
- `feature/*` — new features (merge into `develop`)
- `hotfix/*` — urgent fixes (merge into `main` and `develop`)

## Error Handling

Custom exception hierarchy rooted at [`backend/src/exceptions.py`](backend/src/exceptions.py):
- `LatMatrixException` (base) → structured JSON with `success`, `error.code`, `error.message`, `error.details`
- `FileParsingError` (400), `ValidationError` (422), `LLMBackendError` (503), `EntityExtractionError` (500), `UnsupportedFileTypeError` (400)
- Global exception handlers registered in [`backend/src/factory.py`](backend/src/factory.py)

## Key File References

- [`backend/src/services/llm_backend.py`](backend/src/services/llm_backend.py) — LLM backend base + all 6 implementations
- [`backend/src/services/parsers/base_parser.py`](backend/src/services/parsers/base_parser.py) — parser abstraction
- [`backend/src/services/parsers/parser_factory.py`](backend/src/services/parsers/parser_factory.py) — parser selection
- [`backend/src/services/storage/base.py`](backend/src/services/storage/base.py) — file storage abstraction
- [`backend/src/exceptions.py`](backend/src/exceptions.py) — error hierarchy
- [`backend/src/factory.py`](backend/src/factory.py) — app factory + exception handlers
- [`docker-compose.yml`](docker-compose.yml) — service definitions
- [`.clinerules`](.clinerules) — testing conventions

## LLM Backends

| Backend              | Env Value               | Class                          | Notes                              |
|----------------------|-------------------------|--------------------------------|------------------------------------|
| OpenAI               | `LLM_BACKEND=openai`    | `OpenAIBackend`                | GPT models (default: gpt-4o-mini) |
| Anthropic            | `LLM_BACKEND=anthropic` | `AnthropicBackend`             | Claude with retry/backoff          |
| Ollama               | `LLM_BACKEND=ollama`    | `OllamaBackend`                | Local inference (default: llama3)  |
| OpenRouter           | `LLM_BACKEND=openrouter`| `OpenRouterBackend`            | 200+ models via OpenAI-compat API  |
| OpenRouter Mistral   | `LLM_BACKEND=openrouter-mistral` | `OpenRouterMistralBackend` | Mistral-optimised with markdown heading parsing |
| Mock (fallback)      | `LLM_BACKEND=mock`      | `MockBackend`                  | No-creds placeholder               |

> **⚠️ DEPRECATED — These custom backends are being replaced by LiteLLM (`litellm` package), which is already the primary LLM integration in Chainlit. LiteLLM provides a unified interface to 100+ models via a single `litellm.acompletion()` call, eliminating the need for separate backend classes.**

All backends inherit from [`backend/src/services/llm_backend.py`](backend/src/services/llm_backend.py). Select via `LLM_BACKEND` env var; factory function `get_llm_backend()` returns the correct instance.

