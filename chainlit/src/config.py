import os
from typing import Final, Optional

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# LiteLLM / LLM Provider Configuration (Provider-Agnostic)
# ---------------------------------------------------------------------------
# Chainlit uses LiteLLM (via ``langchain_community.chat_models.ChatLiteLLM``)
# to support any LLM provider.  The ``LLM_MODEL`` variable follows LiteLLM's
# model naming convention — the prefix determines the provider:
#
#   Provider       | Model Prefix / Format
#   ---------------|------------------------------
#   OpenAI         | ``gpt-4o``, ``gpt-4o-mini``
#   Anthropic      | ``claude-sonnet-4-20250514``
#   OpenRouter     | ``openrouter/<model-id>``
#   Google Gemini  | ``gemini/gemini-2.0-flash-exp``
#   Groq           | ``groq/<model-id>``
#   Together AI    | ``together_ai/<model-id>``
#   Ollama (local) | ``ollama/<model-name>``
#   Azure OpenAI   | ``azure/<deployment-name>``
#
# LiteLLM automatically reads the correct provider-specific env var
# (``OPENAI_API_KEY``, ``ANTHROPIC_API_KEY``, ``GROQ_API_KEY``, etc.)
# from the environment.  The ``LLM_API_KEY`` fallback exists as a single
# variable that is mapped to the correct provider key when set.
#
# For OpenAI-compatible providers (OpenRouter, Together AI, DeepSeek,
# Groq, etc.) you may optionally set ``LLM_BASE_URL`` to override the
# API endpoint.
# ---------------------------------------------------------------------------

# Provider selection — determines which env vars are required.
# Supported values: ``openai``, ``anthropic``, ``openrouter``, ``gemini``,
# ``groq``, ``together_ai``, ``ollama``, ``azure``, or any valid LiteLLM
# provider name.  The default ``"openrouter"`` keeps backward compatibility.
LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "openrouter")

# Model name in LiteLLM format (provider/model-name).
# Default: ``deepseek/deepseek-chat`` (via OpenRouter).
LLM_MODEL: str = os.environ.get(
    "LLM_MODEL",
    os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-chat"),
)

# Fallback API key — written to the appropriate provider-specific env var
# (e.g. ``OPENAI_API_KEY``, ``ANTHROPIC_API_KEY``) if set.
LLM_API_KEY: Optional[str] = os.environ.get(
    "LLM_API_KEY",
    os.environ.get("OPENROUTER_API_KEY") or None,
)

# Optional base URL override for OpenAI-compatible providers.
LLM_BASE_URL: Optional[str] = os.environ.get(
    "LLM_BASE_URL",
    os.environ.get("OPENROUTER_BASE_URL") or None,
)

# Backward-compatible aliases so existing OPENROUTER_* references still
# resolve without changes to other modules.
OPENROUTER_API_KEY: str = LLM_API_KEY or ""
OPENROUTER_MODEL: str = LLM_MODEL
OPENROUTER_BASE_URL: str = LLM_BASE_URL or "https://openrouter.ai/api/v1"

# Backend API endpoints
EXTRACT_TEXT_ENTITIES_ENDPOINT = API_BASE_URL + "/api/documents/extract-entities"
ANALYZE_DOCUMENT_ENDPOINT = API_BASE_URL + "/api/documents/analyze"
TEXT_EXTRACTION_ENDPOINT = API_BASE_URL + "/api/documents/extract-text"
STREAM_SUMMARY_ENDPOINT = API_BASE_URL + "/api/documents/analyze/stream"
EXTRACT_ENDPOINT = API_BASE_URL + "/api/documents/extract"
SUMMARIZE_ENDPOINT = API_BASE_URL + "/api/documents/summarize"

# File upload limits
# Maximum upload size in bytes. Default: 5 MB.
# Override via the MAX_UPLOAD_SIZE_MB environment variable.
_MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
MAX_UPLOAD_SIZE: int = _MAX_UPLOAD_SIZE_MB * 1024 * 1024

# spaCy NLP limits
# Maximum text length (in characters) that spaCy's NER pipeline can process.
# Default: 5,000,000
# Texts longer than this limit will raise ValueError: [E088].
#
# Memory Consideration:
# spaCy's NER pipeline consumes approximately 1 GB of RAM per 100,000 characters.
# At the default limit of 5,000,000 characters, expect ~50 GB of peak memory usage
# during entity extraction. Ensure sufficient RAM is available before increasing
# this value further. Override via the SPACY_MAX_LENGTH environment variable.
SPACY_MAX_LENGTH: Final[int] = int(os.getenv("SPACY_MAX_LENGTH", "5000000"))

# Supported OCR languages for document processing.
# Maps language names (lowercase) to Tesseract language codes.
# These are the languages the application supports for OCR-based parsing.
SUPPORTED_OCR_LANGUAGES: Final[dict[str, str]] = {
    "english": "eng",
    "french": "fra",
    "german": "deu",
    "spanish": "spa",
    "hindi": "hin",
}

# Display label-to-code mapping for OCR language selection in the ChatSettings UI.
# Maps the user-facing dropdown labels to Tesseract language codes.
# ``None`` means auto-detect.
OCR_LABEL_TO_CODE: Final[dict[str, str | None]] = {
    "Detect Automatically": None,
    "English": "eng",
    "Hindi": "hin",
    "French": "fra",
    "Spanish": "spa",
    "German": "deu",
}

# Supported summary languages for LLM-generated summaries.
# Maps language display names (lowercase, underscored) to ISO 639-1 two-letter codes.
# These are passed to the LLM prompt to instruct which language to use for summaries.
SUPPORTED_SUMMARY_LANGUAGES: Final[dict[str, str]] = {
    "english": "en",
    "hindi": "hi",
    "french": "fr",
    "spanish": "es",
    "german": "de",
    "chinese_mandarin": "zh",
    "indonesian": "id",
    "standard_arabic": "ar",
    "urdu": "ur",
    "portuguese": "pt",
}

# Display label-to-code mapping for summary language selection in the ChatSettings UI.
# Maps the user-facing dropdown labels to ISO 639-1 two-letter codes.
# ``None`` means no language override (LLM default).
SUMMARY_LABEL_TO_CODE: Final[dict[str, str | None]] = {
    "Detect Automatically": None,
    "English": "en",
    "Hindi": "hi",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Chinese (Mandarin)": "zh",
    "Indonesian": "id",
    "Standard Arabic": "ar",
    "Urdu": "ur",
    "Portuguese": "pt",
}

# Reverse mapping: ISO 639-1 codes -> display labels for summary languages.
# Used to show the human-readable language name in prompts and logs.
SUMMARY_CODE_TO_LABEL: Final[dict[str, str]] = {
    code: label
    for label, code in SUMMARY_LABEL_TO_CODE.items()
    if code is not None
}
try:
    import langdetect  # noqa: F401

    LANGUAGE_DETECTOR_AVAILABLE: Final[bool] = True
except ImportError:
    LANGUAGE_DETECTOR_AVAILABLE: Final[bool] = False  # type: ignore[no-redef, misc]
    import logging

    logging.getLogger(__name__).warning(
        "langdetect package is not installed. Language detection for OCR "
        "will be disabled. Install with: pip install langdetect"
    )
