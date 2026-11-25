"""
Application configuration for the LatMatrix API.

Settings are loaded from environment variables with sensible defaults.
"""

import os
from typing import Final


# ── File upload limits ───────────────────────────────────────────────────
# Maximum size (in bytes) for a single uploaded file.
# Default: 50 MB.  Override via the MAX_FILE_SIZE environment variable.
_MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE: Final[int] = _MAX_FILE_SIZE_MB * 1024 * 1024

# ── spaCy NLP limits ──────────────────────────────────────────────────────
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

# ── Streaming endpoint limits ──────────────────────────────────────────────
# Maximum text length (in characters) to send to the LLM for streaming analysis.
# This applies only to the /api/documents/analyze/stream endpoint.
# The non-streaming /api/documents/analyze endpoint sends full text.
# Default: 100,000 characters.
# Override via the MAX_STREAM_TEXT_LENGTH environment variable.
MAX_STREAM_TEXT_LENGTH: Final[int] = int(os.getenv("MAX_STREAM_TEXT_LENGTH", "100000"))

# Maximum size (in bytes) for a single part in a multipart form upload.
# This is the limit enforced by Starlette *before* the request reaches the
# application handler.  It MUST be >= MAX_FILE_SIZE so that the application
# can return a proper 413 response instead of a generic 400.
# Default: 60 MB (10 MB headroom above the default file limit).
_MAX_PART_SIZE_MB = int(os.getenv("MAX_PART_SIZE_MB", str(_MAX_FILE_SIZE_MB + 10)))
MAX_PART_SIZE: Final[int] = _MAX_PART_SIZE_MB * 1024 * 1024
