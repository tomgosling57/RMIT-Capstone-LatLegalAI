# LatMatrix Chainlit Service — AI Legal Document Assistant

The Chainlit service provides the conversational AI interface for document analysis. Users upload legal documents (PDF, DOCX, TXT) and interact with an LLM-powered assistant that extracts, summarises, and explains document content.

---

## Development Credentials

In the local development environment, log in with:

| Field    | Value   |
|----------|---------|
| Username | `admin` |
| Password | `admin` |

> **Note:** These defaults are configured in [`src/auth.py`](src/auth.py) via the `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables. In production, OAuth providers (Google, GitHub, etc.) are used instead.

---

## Quick Start

### Prerequisites

- Python 3.10+
- Tesseract OCR installed (for scanned PDF support)
- An OpenRouter API key (set as `OPENROUTER_API_KEY`)

### Running Locally

```bash
# Go to the folder
cd chainlit

# Create the virtual environment
python -m venv venv

# Activate the virtual environment
. .venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download the spaCy NLP model (required for entity extraction)
python -m spacy download en_core_web_sm

# Run the Chainlit app
chainlit run src/app.py
```

The application will be available at `http://localhost:8001`.

### Creating the Chainlit Secret

```bash
# Go to the folder
cd chainlit

# Create the virtual environment
python -m venv venv

# Activate the virtual environment
. .venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the Chainlit secret creation command
chainlit create-secret
```
Then once the key is generate, paste it into .env

### Running with Docker

```bash
docker-compose up --build chainlit
```

---

## Architecture

The Chainlit service is organised as follows:

```
chainlit/
├── src/
│   ├── app.py                   # Entry point — lifecycle decorators & message routing
│   ├── auth.py                  # Password & OAuth authentication
│   ├── config.py                # Environment variables & language mappings
│   ├── database.py              # SQLite data layer setup
│   ├── document_processor.py    # File upload, parsing & analysis orchestration
│   ├── heuristics.py            # Intent detection (section summary, translation)
│   ├── llm.py                   # LangChain runnable pipeline & LLM streaming
│   ├── summary.py               # Summary generation, storage & download callbacks
│   ├── tools/                   # Local document parsers & utilities
│   └── tests/                   # Unit, integration & e2e tests
├── public/                      # Static assets (logos, icons, stylesheets)
├── app.py                       # Chainlit configuration entry point
├── chainlit.md                  # In-app README shown in the Chainlit UI sidebar
├── Dockerfile
├── docker-entrypoint.sh
└── requirements.txt
```

---

## Key Features

- **Document Parsing** — PDF (native + OCR), DOCX/DOC, TXT/MD with automatic format detection
- **Multilingual OCR** — English, Hindi, French, Spanish, German (Tesseract)
- **Multi-language Summaries** — 10 languages including Mandarin, Arabic, Urdu, Portuguese
- **AI Chat** — OpenRouter-backed LLM (DeepSeek) with conversation memory
- **Download Results** — Extracted text and AI-generated summaries
- **Authentication** — Password-based (dev) or OAuth (production)

---

## LLM Provider Configuration

The Chainlit service uses **LiteLLM** (via `langchain_community.chat_models.ChatLiteLLM`) to support any LLM provider through a single unified interface. The provider is configured via environment variables.

### General Variables

| Variable         | Default                      | Description                                      |
|------------------|------------------------------|--------------------------------------------------|
| `LLM_PROVIDER`   | `openrouter`                 | Provider slug (see table below)                  |
| `LLM_MODEL`      | `deepseek/deepseek-chat`     | Model name in LiteLLM format                     |
| `LLM_API_KEY`    | *(falls back to provider-specific key)* | Generic API key (auto-mapped to provider) |
| `LLM_BASE_URL`   | *(provider default)*         | Base URL override (for OpenAI-compatible APIs)   |

### Provider-Specific Variables

The `LLM_MODEL` value must follow **LiteLLM's model naming convention** (`<provider>/<model-name>`). The provider prefix tells LiteLLM which API to call, and LiteLLM reads the corresponding environment variable automatically.

| Provider       | `LLM_PROVIDER`    | `LLM_MODEL` example                | Required Env Var         |
|----------------|-------------------|------------------------------------|--------------------------|
| OpenAI         | `openai`          | `gpt-4o`                           | `OPENAI_API_KEY`         |
| Anthropic      | `anthropic`       | `claude-sonnet-4-20250514`         | `ANTHROPIC_API_KEY`      |
| OpenRouter     | `openrouter`      | `openrouter/deepseek/deepseek-chat`| `OPENROUTER_API_KEY`     |
| Google Gemini  | `gemini`          | `gemini/gemini-2.0-flash-exp`      | `GEMINI_API_KEY`         |
| Groq           | `groq`            | `groq/llama3-70b-8192`             | `GROQ_API_KEY`           |
| Together AI    | `together_ai`     | `together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1` | `TOGETHERAI_API_KEY` |
| Ollama (local) | `ollama`          | `ollama/llama3`                    | *(none — runs locally)*  |
| Azure OpenAI   | `azure`           | `azure/gpt-4`                      | `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION` |
| Mistral        | `mistral`         | `mistral/mistral-large-latest`     | `MISTRAL_API_KEY`        |
| Cohere         | `cohere`          | `cohere/command-r-plus`            | `COHERE_API_KEY`         |
| Perplexity     | `perplexity`      | `perplexity/llama-3.1-sonar-huge-128k-online` | `PERPLEXITYAI_API_KEY` |
| DeepSeek       | `deepseek`        | `deepseek/deepseek-chat`           | `DEEPSEEK_API_KEY`       |

> **💡 Tip:** Instead of setting each provider-specific variable individually, you can set `LLM_API_KEY` as a single generic fallback. The application automatically writes it to the correct provider-specific environment variable (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) at startup.

### Example: Using OpenAI

```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4o
export OPENAI_API_KEY="<your-openai-api-key>"
```

### Example: Using Anthropic Claude

```bash
export LLM_PROVIDER=anthropic
export LLM_MODEL=claude-sonnet-4-20250514
export ANTHROPIC_API_KEY="<your-anthropic-api-key>"
```

### Example: Using OpenRouter (default)

```bash
export LLM_PROVIDER=openrouter
export LLM_MODEL=openrouter/deepseek/deepseek-chat
export OPENROUTER_API_KEY="<your-openrouter-api-key>"
```

### Backward Compatibility

The legacy `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, and `OPENROUTER_BASE_URL` variables continue to be read as fallbacks when `LLM_PROVIDER=openrouter` (the default). You can migrate incrementally — no existing `.env` files will break.

---

## Full Environment Variable Reference

| Variable              | Default                    | Required | Description                       |
|-----------------------|----------------------------|----------|-----------------------------------|
| `LLM_PROVIDER`        | `openrouter`               | no       | LLM provider slug                 |
| `LLM_MODEL`           | `deepseek/deepseek-chat`   | no       | Model name (LiteLLM format)       |
| `LLM_API_KEY`         | —                          | no       | Generic API key (auto-mapped)     |
| `LLM_BASE_URL`        | —                          | no       | Base URL override                 |
| `OPENROUTER_API_KEY`  | —                          | no*      | OpenRouter API key (legacy)       |
| `OPENROUTER_MODEL`    | `deepseek/deepseek-chat`   | no       | Model name (legacy)               |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | no   | Base URL (legacy)                 |
| `ADMIN_USERNAME`      | `admin`                    | no       | Dev auth username                  |
| `ADMIN_PASSWORD`      | `admin`                    | no       | Dev auth password                  |
| `MAX_UPLOAD_SIZE_MB`  | `5`                        | no       | Maximum file upload size (MB)      |
| `HOME_PAGE_URL`       | `http://localhost:5000`    | no       | Website home page URL              |
| `CHAINLIT_ENV`        | `development`              | no       | Environment (`development`/`production`) |

> *Required for the active provider; ignored otherwise.

---

## Testing

```bash
# From the chainlit directory
cd chainlit

# Run unit tests
python3 -m pytest src/tests/ -v

# Run e2e tests
python3 -m pytest src/tests/e2e/ -v
```
