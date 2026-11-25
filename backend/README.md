# Backend API Service

FastAPI backend service for the LatMatrix Legal Simplifier. This service is the processing engine consumed by the Website and Chainlit services.

> **⚠️ Implementation Status:** This service is currently a **stub / work in progress**. The API endpoints are defined and return placeholder responses, but the full document processing and LLM summarisation pipeline is not yet fully implemented. The `POST /api/chat/process` endpoint in particular is a stub that returns a fixed response.

---

## Technology Stack

| Component | Technology | Version |
|---|---|---|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com) | ≥ 0.110 |
| **Language** | Python | 3.12 |
| **ASGI Server** | Uvicorn | ≥ 0.29 |
| **Document Parsing** | pdfplumber, python-docx | ≥ 0.10 / 1.1 |
| **OCR** | pytesseract, pdf2image, OpenCV, Pillow | — |
| **NLP** | spaCy (`en_core_web_sm`), langdetect | ≥ 3.7 / 1.0 |
| **LLM Backends** | openai, anthropic | ≥ 1.30 / 0.28 |
| **Translation** | deep-translator | ≥ 1.11 |
| **ML / Metrics** | scikit-learn, jiwer | ≥ 1.3 / 3.0 |
| **Validation** | Pydantic | — |
| **Testing** | pytest, pytest-asyncio, httpx | ≥ 7.4 |
| **Container** | Docker | — |

---

## Dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### System dependencies (non-Python)

Handled automatically inside Docker. For local development outside Docker:

```bash
# Ubuntu / Debian
sudo apt-get install -y \
    libmagic1 \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libgl1

# macOS (Homebrew)
brew install libmagic tesseract poppler
```

After installing Python dependencies, download the spaCy language model:

```bash
python -m spacy download en_core_web_sm
```

---

## Environment Variables

Set these in the project root `.env` file (copied from [`env.example`](../env.example)).

### Optional

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Port the API server listens on |
| `SPACY_MODEL` | `en_core_web_sm` | spaCy model to load for NLP processing |
| `DEV_MODE` | `false` | Set to `true` to register the dev-only `/api/documents/extract-text` endpoint |
| `OPENROUTER_API_KEY` | — | OpenRouter API key (used via LiteLLM) |
| `OPENROUTER_MODEL` | — | Model identifier for OpenRouter |
| `OPENROUTER_BASE_URL` | — | OpenRouter base URL |

---

## API Endpoints

All routes are registered under the `/api/` prefix. Interactive documentation is available at http://localhost:8000/docs when the service is running.

### Core

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | API info and health status |
| `GET` | `/health` | Health check (used by Docker and dependent services) |
| `GET` | `/docs` | Swagger UI (interactive API docs) |

### Document Processing

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/documents/extract-text` | Pure text extraction — **dev only** (`DEV_MODE=true` required) |
| `POST` | `/api/documents/extract-entities` | Text extraction + spaCy NER entity recognition |
| `POST` | `/api/documents/analyze` | Full pipeline: text extraction + entity recognition + LLM summarisation |
| `POST` | `/api/documents/analyze/stream` | Same as `/analyze` but streams the LLM response via Server-Sent Events (SSE) |
| `POST` | `/api/chat/process` | **Stub** — placeholder for a future combined file upload + chat prompt endpoint |

---

## Running the Service

### Using Docker (recommended)

```bash
# From the project root
docker compose up api
```

The service will be available at http://localhost:8000.

### Local development

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Project Structure

```
backend/
├── src/
│   ├── main.py                      # FastAPI application entry point
│   ├── factory.py                   # Application factory
│   ├── controllers/                 # Request controllers
│   ├── routes/
│   │   └── api.py                   # All route definitions
│   ├── processors/                  # Data processors
│   ├── services/
│   │   ├── nlp_processor.py
│   │   ├── summarizer.py
│   │   ├── entity_extractor.py
│   │   ├── file_handler.py
│   │   ├── file_saver.py
│   │   ├── llm_backend.py
│   │   ├── parsers/                 # Document format parsers
│   │   └── text_utils.py
│   └── scripts/
│       └── document_transformer/   # Test asset generation script
│           ├── doc_transformer/
│           │   └── transformer.py
│           └── transform_docs.py   # CLI entry point
├── Dockerfile
├── docker-entrypoint.sh
└── requirements.txt
```

---

## Testing

See the [Backend Testing README](../tests/unit/README.md) for setup and instructions on running the test suite.