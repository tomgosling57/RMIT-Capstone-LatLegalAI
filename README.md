# LatMatrix Legal Simplifier

LatMatrix Legal Simplifier is an AI-powered web application that helps users understand complex legal documents. Users upload a PDF, DOCX, or TXT file and interact with a conversational AI interface that extracts key entities, summarises clauses, and answers questions about the document in plain language.

**Credits:** Built as an RMIT capstone project by Thomas Gosling, Joshua Leong, Alebron Toma and Oisin Forde.

**About this repository:** This is a public re-upload of the original private project repository. Commit history, contributor metadata, client and team contact details, and third-party reference documentation have been removed for this release. Individual names in the original project documents have been replaced with role labels.

> **💡 Development credentials:** In the local development environment, use `admin` / `admin` as the username and password to log into Chainlit.

---

## Architecture Overview

The application is composed of four custom services orchestrated by Docker Compose, backed by a shared Redis instance and fronted by an Nginx reverse proxy.

```
                     ┌─────────────────────────────┐
                     │       Nginx (port 80)       │
                     │  /        → website :5000   │
                     │  /chat    → chainlit :8001  │
                     │  /app     → chat :8501      │
                     └──────┬───────────┬──────────┘
                            │           │
               ┌────────────┘           └────────────────┐
               ▼                                         ▼
   ┌───────────────────────┐              ┌──────────────────────────┐
   │   Website Service     │              │   Chainlit Service       │
   │   Flask  (port 5000)  │              │   Chainlit + LiteLLM     │
   │   Auth, home, upload  │              │   Conversational AI UI   │
   └───────────────────────┘              └──────────────────────────┘
```

### Services

| Service | Technology | Responsibility |
|---|---|---|
| **website** | Flask | Home page, pricing, authentication (login/signup/OAuth), document upload form |
| **chainlit** | Chainlit + LiteLLM | Conversational AI interface for legal document analysis |
| **api** | FastAPI | Document processing, NLP analysis, LLM summarisation (backend engine) |
| **chat** | Streamlit | Auth-gated AI document analysis UI (legacy, being superseded by chainlit) |
| **redis** | Redis 7 | Rate-limiter backend + document-context bridge between services |
| **nginx** | Nginx | Reverse proxy routing all traffic on port 80 |

### Service READMEs

- [Backend API Service](./backend/README.md)
- [Chainlit Service](./chainlit/README.md)
- [Website Service](./website/README.md)

---

## Prerequisites

### System Dependencies

Several Python packages in this project require **system-level libraries** that must be installed on your host machine — both for local development outside Docker and for running tests locally.

| Package | Required For | System Dependencies |
|---|---|---|
| **Tesseract** (`pytesseract`) | OCR — scanned document parsing | `tesseract-ocr` + language packs |
| **Poppler** (`pdf2image`) | PDF-to-image conversion for OCR | `poppler-utils` |
| **WeasyPrint** | PDF generation with Unicode support | `libpango-1.0-0`, `libpangocairo-1.0-0`, `libcairo2`, `libgdk-pixbuf2.0-0` |
| **python-magic** | File type detection (magic bytes) | `libmagic1` |
| **OpenCV** (`opencv-python`) | Image preprocessing for OCR | `libgl1` |
| **spaCy** | NLP — entity extraction, lemmatisation | Python model download (`en_core_web_sm`) |

#### Linux (Debian / Ubuntu)

```bash
# Tesseract OCR engine + language packs
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu

# Poppler (pdf2image)
sudo apt-get install -y poppler-utils

# WeasyPrint system libraries
sudo apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    librsvg2-2 \
    shared-mime-info \
    fonts-dejavu-core

# File type detection
sudo apt-get install -y libmagic1

# OpenCV
sudo apt-get install -y libgl1
```

#### macOS (with [Homebrew](https://brew.sh))

```bash
brew install tesseract poppler pango librsvg glib
```

#### Windows

- **Tesseract**: Download installer from [UB-Mannheim/tesseract wiki](https://github.com/UB-Mannheim/tesseract/wiki)
- **Poppler**: Download from [oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/)
- **WeasyPrint**: See [WeasyPrint Windows installation guide](https://doc.courtbouillon.org/weasyprint/latest/first_steps.html#windows)
- **libmagic / python-magic**: On Windows, use `python-magic-bin` instead of `python-magic` in `requirements.txt`

> **Docker users**: These dependencies are already baked into the service Dockerfiles. You only need to install them locally if you plan to run services or tests outside Docker.

### Docker

All services run inside Docker containers. The only dependency required on the host machine is **Docker Desktop** (which bundles Docker Engine and Docker Compose).

- **macOS / Windows**: [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Linux**: [Install Docker Engine](https://docs.docker.com/engine/install/) then [Docker Compose plugin](https://docs.docker.com/compose/install/)

Verify your installation:

```bash
docker --version        # Docker version 24+ recommended
docker compose version  # Docker Compose version 2.20+ recommended
```

> **Note:** The legacy `docker-compose` (v1) command is not supported. Use `docker compose` (v2, with a space).

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-ORG/RMIT-Capstone-LatMatrix.git
cd RMIT-Capstone-LatMatrix
```

### 2. Set up environment variables

Copy the example environment file and fill in your values, make sure your in the root directory:

```bash
cp env.example .env
```

Open `.env` and set at minimum:

| Variable | Where to get it |
|---|---|
| `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `CHAINLIT_AUTH_SECRET` | Run `chainlit create-secret` (see [Chainlit README](./chainlit/README.md)) |
| `SECRET_KEY` | Run `python -c "import secrets; print(secrets.token_hex(32))"` |

See [`env.example`](./env.example) for all available variables with descriptions, and the individual service READMEs for service-specific variable details.

### 3. Build and start all services

```bash
docker compose up --build
```

### 4. Access the application

| Interface | URL |
|---|---|
| Main website | http://localhost |
| Chainlit chat | http://localhost/chat |
| Streamlit chat | http://localhost/app |
| API (direct) | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

### Stopping the application

```bash
docker compose down
```

To also remove volumes (clears Redis data and Chainlit data):

```bash
docker compose down -v
```

---

## Running Individual Services

```bash
# Start only the API and its dependencies
docker compose up api redis

# Start only the Chainlit service and its dependencies
docker compose up chainlit api redis

# Start only the website service
docker compose up website api redis
```

---

## LLM Provider Configuration

The Chainlit service uses **LiteLLM** to support any LLM provider. The provider is selected via the `LLM_PROVIDER` environment variable, and the model is specified via `LLM_MODEL` in LiteLLM format.

### Quick Examples

```bash
# OpenAI
LLM_PROVIDER=openai    LLM_MODEL=gpt-4o             OPENAI_API_KEY="<your-openai-api-key>"

# Anthropic Claude
LLM_PROVIDER=anthropic LLM_MODEL=claude-sonnet-4-20250514 ANTHROPIC_API_KEY="<your-anthropic-api-key>"

# OpenRouter (default)
LLM_PROVIDER=openrouter LLM_MODEL=openrouter/deepseek/deepseek-chat OPENROUTER_API_KEY="<your-openrouter-api-key>"

# Groq
LLM_PROVIDER=groq      LLM_MODEL=groq/llama3-70b-8192  GROQ_API_KEY="<your-groq-api-key>"

# Ollama (local)
LLM_PROVIDER=ollama    LLM_MODEL=ollama/llama3
```

> **Full documentation:** See [`chainlit/README.md`](./chainlit/README.md#llm-provider-configuration) for a complete provider reference table, and [`env.example`](./env.example) for all available variables.

---

## Environment File Reference

All environment variables are documented in [`env.example`](./env.example). The file is divided into sections:

- **LiteLLM** — LLM provider credentials (see [provider table above](#llm-provider-configuration))
- **Chainlit Service** — Auth secret, OAuth credentials, upload limits
- **Website Service** — Flask secret key, environment mode
- **Chat Service** — Streamlit API URL override

Copy `env.example` to `.env` in the project root before starting any service. Docker Compose automatically loads `.env` for all services.

---

## Project Structure

```
latmatrix/
├── backend/            # FastAPI backend service
│   ├── src/            # Application source code
│   ├── Dockerfile
│   └── README.md
├── chainlit/           # Chainlit conversational AI service
│   ├── src/            # Application source code
│   ├── Dockerfile
│   └── README.md
├── website/            # Flask website service
│   ├── app/            # Application source code
│   ├── Dockerfile
│   └── README.md
├── chat/               # Streamlit chat service
├── tests/              # All test suites
│   ├── unit/           # Unit tests (backend)
│   ├── e2e/            # End-to-end tests
│   ├── frontend/       # Frontend/UI tests
│   └── load/           # Load tests (Locust)
├── nginx/              # Nginx reverse proxy config
├── shared/             # Shared utilities across services
├── docker-compose.yml  # Service orchestration
├── env.example         # Environment variable template
└── pyproject.toml      # Python tooling config (pytest, black, mypy)
```

---

## Development

### Local Python setup

When running services or tests outside Docker, you need to **install system dependencies first** (see [System Dependencies](#system-dependencies) above), then set up a Python virtual environment for the service you want to run.

#### Chainlit

```bash
cd chainlit

# Create and activate the virtual environment
python -m venv .venv
source .venv/bin/activate              # Linux/macOS
# .venv\Scripts\activate               # Windows

# Install Python dependencies
pip install -r requirements.txt

# Download the spaCy NLP model (required for entity extraction)
python -m spacy download en_core_web_sm
```

#### Backend API

```bash
cd backend

# Create and activate the virtual environment
python -m venv .venv
source .venv/bin/activate              # Linux/macOS
# .venv\Scripts\activate               # Windows

# Install Python dependencies
pip install -r requirements.txt

# Download the spaCy NLP model (required for entity extraction)
python -m spacy download en_core_web_sm
```

> **Note:** The spaCy model `en_core_web_sm` is required for entity extraction and text analysis. Tests in `test_entity_extractor.py` and NLP-related tests will fail without it.
>
> **Note:** Both `chainlit/requirements.txt` and `backend/requirements.txt` include `weasyprint` and `pytesseract`. Ensure the corresponding [system dependencies](#system-dependencies) (Tesseract, Poppler, Pango, Cairo, etc.) are installed **before** running `pip install`, or install them first and then retry if `pip` errors on native-library builds.

### Code formatting

```bash
black .
```

### Linting

```bash
flake8 .
```

### Type checking

```bash
mypy .
```

### Running tests locally

See the individual testing READMEs for setup and execution instructions:

- [Backend tests](./tests/unit/README.md)
- [E2E tests](./tests/e2e/README.md)
- [Frontend tests](./tests/frontend/README.md)
- [Load tests](./tests/load/README.md)