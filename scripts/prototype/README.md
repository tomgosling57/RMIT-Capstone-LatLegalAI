# LatMatrix Prototype — Quick Start
**P000686CSITCP | Summarising Legal Documents in Easy Language**

---

## Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## Choosing an LLM Backend

Set the `LLM_BACKEND` environment variable before running:

| Value | Description | Extra requirement |
|-------|-------------|-------------------|
| `mock` (default) | No API — returns placeholder text | none |
| `openai` | GPT-4o-mini via OpenAI API | `pip install openai` + `OPENAI_API_KEY` |
| `anthropic` | Claude via Anthropic API | `pip install anthropic` + `ANTHROPIC_API_KEY` |
| `ollama` | Local model via Ollama | Ollama running + `OLLAMA_MODEL` env var |

```bash
# Example – use OpenAI
export LLM_BACKEND=openai
export OPENAI_API_KEY=sk-...
```

---

## Run the API server

```bash
uvicorn latmatrix_prototype:app --reload
```

Open the interactive docs at: **http://localhost:8000/docs**

### POST /analyse

```bash
curl -X POST http://localhost:8000/analyse \
  -F "file=@contract.pdf" \
  -F "target_language=french"
```

---

## Run from the CLI

```bash
python prototype.py contract.pdf --lang hindi
```

---

## Project Structure (prototype → production path)

```
latmatrix_prototype.py   ← single-file prototype (start here)
requirements.txt

Next steps for production:
├── app/
│   ├── loaders.py       ← document ingestion
│   ├── nlp.py           ← spaCy extraction
│   ├── llm/
│   │   ├── base.py      ← LLMBackend ABC
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   └── ollama.py
│   ├── translation.py
│   └── api.py           ← FastAPI routes
├── tests/
└── frontend/            ← React/Vue upload UI
```

---

## Response Shape

```json
{
  "filename": "contract.pdf",
  "llm_backend": "openai",
  "summary": {
    "plain_english": "...",
    "translated": "...",
    "translation_language": "french"
  },
  "key_information": {
    "obligations": ["You must notify the company within 30 days ..."],
    "permissions": ["You may terminate the agreement with 14 days notice ..."],
    "risks":       ["Failure to comply may result in a $5,000 penalty ..."]
  },
  "raw_extraction": { ... },
  "stats": { "raw_char_count": 14200, "chunks_processed": 4 }
}
```
