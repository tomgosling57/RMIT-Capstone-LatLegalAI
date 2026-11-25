# Chat Service

Streamlit-based AI chat and document analysis service for the LatMatrix Legal Simplifier application.

## Overview

The Chat Service provides the primary user interface for AI-powered document analysis. It features:

- **AI Chat Interface**: Interactive chat with AI for document-related queries
- **Document Analysis**: Upload and analyze legal documents with AI-generated summaries
- **Entity Extraction**: Extract and analyze named entities from documents
- **NLP Developer Tools**: Text extraction comparison and debugging utilities

### Architecture

The Chat Service is an auth-gated Streamlit application that communicates with the **AI Summarizer Service** (FastAPI backend) for processing. Authentication is handled by the **Website Service** (Flask), which validates Supabase JWT tokens before granting access.

```
┌─────────────────┐     ┌─────────────────┐
│  Website        │     │   Chat          │
│  Service        │     │   Service       │
│  (Flask)        │     │   (Streamlit)   │
│  - Auth         │────▶│   - AI Chat     │
│  - JWT Guard    │     │   - Analysis    │
└─────────────────┘     │   - Extraction  │
                        │   - Dev Tools   │
                        └─────────────────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │  AI Summarizer  │
                            │  Service        │
                            │  (FastAPI)      │
                            └───────────────┘
```

## Project Structure

```
chat/
├── src/
│   ├── ui.py                    # Primary summary chat page (entry point)
│   ├── auth_guard.py            # Supabase JWT guard
│   ├── config.py                # API endpoint configuration
│   ├── components/
│   │   ├── theme.py             # Theme styling
│   │   ├── topbar.py            # Navigation topbar
│   │   ├── pdf_viewer_component.py
│   │   └── document_comparison_component.py
│   ├── pages/
│   │   ├── entities.py          # Entity Analyzer
│   │   └── Developer_Tool.py    # NLP Developer Tool
│   ├── styles/
│   │   ├── base.css
│   │   └── components.css
│   └── utils/
│       └── text_utils.py
├── Dockerfile                   # Container definition
├── requirements.txt             # Python dependencies
└── README.md
```

## Pages

### Main Chat Page (`ui.py`)
The primary entry point for authenticated users. Features:
- Document upload and AI summary streaming
- Real-time chat with AI about document content
- Supabase JWT authentication via [`auth_guard.py`](src/auth_guard.py)

### Entity Analyzer (`pages/entities.py`)
Extract and analyze named entities from legal documents:
- Legal entities (companies, organizations)
- People and parties
- Dates, amounts, and key terms

### Developer Tool (`pages/Developer_Tool.py`)
NLP developer utilities for testing and debugging:
- PDF text extraction comparison
- Flow-Aware vs Column-Aware extraction modes
- Accuracy measurement against ground truth

## Running the Chat Service

### Using Docker (Recommended)

```bash
# From project root
docker-compose up chat
```

The service will be available at http://localhost:8501

### Local Development

```bash
cd chat
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd src
streamlit run ui.py --server.port 8501 --server.headless true
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | AI Summarizer Service endpoint | `http://localhost:8000` |
| `SUPABASE_URL` | Supabase project URL | (required for auth) |
| `SUPABASE_KEY` | Supabase anonymous key | (required for auth) |

## Dependencies

### Core
- Python 3.12
- Streamlit >= 1.32
- python-dotenv >= 1.0
- requests >= 2.31

### Authentication
- supabase >= 2.5.0

### Optional
- pdfplumber >= 0.10 (for direct document processing)
- streamlit-pdf-viewer >= 0.0.5 (PDF preview)

## Access

- **Chat Service**: http://localhost:8501
- **Authentication**: Redirects to Website Service (Flask) at http://localhost

## Notes

- The Chat Service is **auth-gated** - users must be authenticated via the Website Service
- Do not add authentication pages (login, signup) here - they belong in the Website Service
- All document processing is delegated to the AI Summarizer Service
