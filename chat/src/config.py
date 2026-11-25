import os

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# Endpoints (all under /api/ prefix)
EXTRACT_TEXT_ENTITIES_ENDPOINT = API_BASE_URL + "/api/documents/extract-entities"
ANALYZE_DOCUMENT_ENDPOINT = API_BASE_URL + "/api/documents/analyze"
TEXT_EXTRACTION_ENDPOINT = API_BASE_URL + "/api/documents/extract-text"
STREAM_SUMMARY_ENDPOINT = API_BASE_URL + "/api/documents/analyze/stream"

# Tab-based document processing endpoints
EXTRACT_ENDPOINT = API_BASE_URL + "/api/documents/extract"
SUMMARIZE_ENDPOINT = API_BASE_URL + "/api/documents/summarize"

# Legacy upload endpoint (deprecated)
UPLOAD_ENDPOINT = API_BASE_URL + "/api/documents/extract-entities"
