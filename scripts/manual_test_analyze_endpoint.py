"""
Manual integration test for the ``/api/documents/analyze`` endpoint.

This script is **not** a pytest test — it is intended to be run manually
because it makes a **real** API call against the configured OpenRouter backend
(``mistralai/mistral-small-24b-instruct-2501``) which incurs cost.

Prerequisites
-------------
1. The LatMatrix backend must be running (e.g. ``uvicorn main:app`` on
   ``http://localhost:8000``).
2. The ``.env`` file (or environment) must have:
   - ``LLM_BACKEND=openrouter``
   - ``OPENROUTER_API_KEY`` set to a valid key
   - ``OPENROUTER_MODEL=mistralai/mistral-small-24b-instruct-2501``
3. The file ``legal_documents/sample-standard_contract.pdf`` must exist
   relative to the project root.

Usage
-----
    python scripts/manual_test_analyze_endpoint.py

Expected behaviour
------------------
- HTTP 200 response from ``/api/documents/analyze``.
- Response JSON contains a non-empty ``llm_summary`` field.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Resolve paths relative to the project root (two levels up from this script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LEGAL_DOCS_DIR = PROJECT_ROOT / "legal_documents"
PDF_PATH = LEGAL_DOCS_DIR / "sample-standard_contract.pdf"

# Default backend URL — adjust if your server runs on a different host/port
API_BASE_URL = "http://localhost:8000"
ANALYZE_ENDPOINT = f"{API_BASE_URL}/api/documents/analyze"

# Timeout for the full request (PDF upload + text extraction + LLM call)
REQUEST_TIMEOUT_SECONDS = 300  # 5 minutes

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_prerequisites() -> None:
    """Verify that the PDF file exists before making the request."""
    if not PDF_PATH.is_file():
        print(f"ERROR: PDF file not found at {PDF_PATH}")
        print("Make sure you are running this script from the project root:")
        print("    python scripts/manual_test_analyze_endpoint.py")
        sys.exit(1)

    print(f"[OK] PDF file found: {PDF_PATH}")
    print(f"     Size: {PDF_PATH.stat().st_size / 1024:.1f} KB")


def _print_response_summary(status_code: int, data: dict) -> None:
    """Pretty-print key fields from the response."""
    print(f"\n{'=' * 60}")
    print(f"HTTP Status Code: {status_code}")
    print(f"{'=' * 60}")

    if status_code != 200:
        print(f"Request failed. Response body:\n{json.dumps(data, indent=2)}")
        return

    success = data.get("success", False)
    filename = data.get("filename", "N/A")
    file_id = data.get("file_id", "N/A")
    pdf_type = data.get("pdf_type", "N/A")
    llm_summary = data.get("llm_summary", "")
    llm_entities = data.get("llm_entities", "")
    content_pages = data.get("content", [])

    print(f"  success      : {success}")
    print(f"  filename     : {filename}")
    print(f"  file_id      : {file_id}")
    print(f"  pdf_type     : {pdf_type}")
    print(f"  text_pages   : {len(content_pages)} page(s)")
    print(f"  llm_summary  : {'✓ present' if llm_summary else '✗ EMPTY'}")
    print(f"  llm_entities : {'✓ present' if llm_entities else '✗ EMPTY'}")

    if llm_summary:
        # Show first 500 characters of the summary
        print("\n  --- Summary preview (first 500 chars) ---")
        print("  {preview}")
        if len(llm_summary) > 500:
            print(f"  ... (truncated, full length: {len(llm_summary)} chars)")

    if llm_entities:
        print("\n  --- Entities ---")
        print(f"  {llm_entities}")


# ---------------------------------------------------------------------------
# Main test logic
# ---------------------------------------------------------------------------


def main() -> None:
    """Upload ``sample-standard_contract.pdf`` and verify the analysis response."""
    _check_prerequisites()

    # Read the PDF file bytes
    pdf_bytes = PDF_PATH.read_bytes()

    print(f"\nSending POST request to: {ANALYZE_ENDPOINT}")
    print(f"  File     : sample-standard_contract.pdf ({len(pdf_bytes)} bytes)")
    print("  Backend  : OpenRouter (mistralai/mistral-small-24b-instruct-2501)")
    print(f"  Timeout  : {REQUEST_TIMEOUT_SECONDS}s")
    print(f"{'─' * 60}")

    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        files = {
            "file": (
                "sample-standard_contract.pdf",
                pdf_bytes,
                "application/pdf",
            )
        }
        data = {"extraction_mode": "flow"}

        response = client.post(ANALYZE_ENDPOINT, files=files, data=data)

    # Parse response
    try:
        response_data = response.json()
    except json.JSONDecodeError:
        response_data = {"raw_text": response.text}

    _print_response_summary(response.status_code, response_data)

    # ------------------------------------------------------------------
    # Assertions (raise on failure so the script exits with code 1)
    # ------------------------------------------------------------------
    print(f"\n{'─' * 60}")
    print("Running assertions...")

    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}. "
        f"Response: {response.text[:500]}"
    )
    print("[PASS] HTTP 200 OK")

    assert isinstance(
        response_data, dict
    ), f"Expected dict response, got {type(response_data).__name__}"
    print("[PASS] Response is a JSON object")

    llm_summary = response_data.get("llm_summary", "")
    assert llm_summary, (
        "Response field 'llm_summary' is empty or missing. "
        "The LLM summarization may have failed."
    )
    print(f"[PASS] llm_summary is present ({len(llm_summary)} chars)")

    # Optional: verify other expected fields exist
    for field in ("success", "content", "entities", "filename", "file_id", "pdf_type"):
        assert field in response_data, f"Expected field '{field}' missing from response"
    print("[PASS] All expected response fields are present")

    print(f"\n{'=' * 60}")
    print("ALL ASSERTIONS PASSED")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
