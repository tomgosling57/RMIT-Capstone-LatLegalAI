"""
Chat Service — AI Chat & Document Analysis UI
=============================================
This Streamlit application is the primary entry point for the Chat Service.
It provides:
  - Authenticating the incoming Supabase JWT (via auth_guard.require_auth)
  - Accepting a legal-document upload
  - A two-tab interface:
      * "Extracted Text" tab — shows raw text, NLP entities, clause classifications
      * "Summary" tab — shows the LLM-generated summary
  - Asynchronous calls to the backend:
      * ``POST /api/documents/extract`` — text extraction + NLP pipeline
      * ``POST /api/documents/summarize`` — LLM summarisation

Additional developer/analysis pages are available via the navigation bar:
  - Entity Analyzer (pages/entities.py): extract named entities from documents
  - Developer Tool (pages/Developer_Tool.py): NLP text extraction comparison tool

All authentication pages (login, signup, OAuth) and non-AI pages (home,
pricing, upload form) live in the Website Service (Flask).  Do NOT add
unrelated pages here.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import requests
import streamlit as st

from auth_guard import check_credentials, require_auth
from components.theme import (
    apply_theme,
    render_alert,
    render_empty_state,
    render_scanned_indicator,
)
from components.topbar import topbar
from config import EXTRACT_ENDPOINT, SUMMARIZE_ENDPOINT
from utils.pdf_type_detector import PDFType, detect_pdf_type

logger = logging.getLogger(__name__)

# Auth guard — must be the very first call.
# Returns the user-info dict or calls st.stop() if the token is missing /
# invalid, redirecting the browser back to the Flask login page.
# When Supabase credentials are not configured, returns a guest user.

check_credentials()
user = require_auth()

# Page configuration & theme
st.set_page_config(
    page_title="LatLegalAI - Legal Document Analysis",
    layout="wide",
    page_icon="static/LegalAiLogo.png",
    initial_sidebar_state="collapsed",
)

apply_theme()
topbar()
st.markdown(
    """# ⚖️ Document Summarizer
## Generates simple language summaries of complex legal documents."""
)

st.write("Upload a document to begin analysis.")

st.markdown("---")

# Session state initialisation
_DEFAULT_STATE: Dict[str, Any] = {
    "extracted_text": None,
    "entities": None,
    "clauses": None,
    "summary": None,
    "llm_entities": None,
    "file_id": None,
    "file_metadata": None,
    "processing_status": "idle",
    "error_message": None,
    "extraction_error": False,
    "summarization_error": False,
    "show_retry": False,
}

for key, default in _DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default


# Helper: render NLP analysis table (entities + clauses combined)


def _render_nlp_analysis_table(
    entities: Dict[str, Any], clauses: List[Dict[str, Any]]
) -> None:
    """Render entities and clause classifications in a multi-column table.

    The table has columns for Type, Value, and Confidence/Labels so that
    all NLP analysis is presented compactly below the extracted text.
    """
    rows: List[str] = []

    # ── Entity rows ──────────────────────────────────────────────────────
    if entities:
        names = entities.get("names", [])
        dates = entities.get("dates", [])
        locations = entities.get("locations", [])

        for e in names:
            rows.append(_nlp_table_row("🏛️ Party", e["text"], e.get("confidence", 0.0)))
        for e in dates:
            rows.append(_nlp_table_row("📅 Date", e["text"], e.get("confidence", 0.0)))
        for e in locations:
            rows.append(
                _nlp_table_row("📍 Location", e["text"], e.get("confidence", 0.0))
            )

    # ── Clause rows ──────────────────────────────────────────────────────
    if clauses:
        for clause in clauses:
            labels = clause.get("labels", {})
            sentence = clause.get("sentence", "")
            label_badges = ""
            if labels.get("obligation", False):
                label_badges += render_status_badge_raw("Obligation", "warning") + " "
            if labels.get("permission", False):
                label_badges += render_status_badge_raw("Permission", "success") + " "
            if labels.get("risk", False):
                label_badges += render_status_badge_raw("Risk", "error") + " "

            rows.append(
                "<tr>"
                '<td class="nlp-type">⚖️ Clause</td>'
                f'<td class="nlp-value">{sentence}</td>'
                f'<td class="nlp-badges">{label_badges}</td>'
                "</tr>"
            )

    if not rows:
        st.markdown(
            "<p style='color: var(--text-muted); font-style: italic;'>"
            "No entities or clause classifications were extracted "
            "from this document.</p>",
            unsafe_allow_html=True,
        )
        return

    st.markdown("### 🔍 NLP Analysis")
    st.markdown(
        '<div class="nlp-analysis-table-wrapper">'
        '<table class="nlp-analysis-table">'
        "<thead><tr>"
        "<th>Type</th><th>Value</th><th>Confidence / Labels</th>"
        "</tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table>"
        "</div>",
        unsafe_allow_html=True,
    )


def _nlp_table_row(category: str, text: str, confidence: float) -> str:
    """Return an HTML table row for a single entity."""
    if confidence >= 0.85:
        badge_status = "success"
    elif confidence >= 0.6:
        badge_status = "warning"
    else:
        badge_status = "info"
    badge = (
        f'<span class="status-badge status-badge--{badge_status}">'
        f"{confidence:.0%}</span>"
    )
    return (
        "<tr>"
        f'<td class="nlp-type">{category}</td>'
        f'<td class="nlp-value">{text}</td>'
        f'<td class="nlp-badges">{badge}</td>'
        "</tr>"
    )


def render_status_badge_raw(text: str, status: str) -> str:
    """Return raw HTML for a status badge (no st.markdown wrapper)."""
    return f'<span class="status-badge status-badge--{status}">{text}</span>'


# Helper: render file metadata card


def _render_file_metadata(metadata: Dict[str, Any]) -> None:
    """Render a file metadata card showing filename, size, type, and PDF type."""
    filename = metadata.get("filename", "Unknown")
    size_kb = metadata.get("size_kb", 0)
    mime_type = metadata.get("mime_type", "N/A")
    pdf_type = metadata.get("pdf_type", "UNKNOWN")

    badge_status = "info" if pdf_type == "TEXT_BASED" else "warning"
    pdf_type_badge = (
        f'<span class="status-badge status-badge--{badge_status}"'
        f' style="margin-left:0.5rem;">{pdf_type}</span>'
    )

    doc_card_html = (
        f'<div class="document-card fade-in">'
        f'<div class="document-header">'
        f'<span class="document-title">📄 {filename}</span>'
        f"{pdf_type_badge}"
        f"</div>"
        f'<div class="document-meta">'
        f"Size: {size_kb:.1f} KB &nbsp;·&nbsp; Type: {mime_type}"
        f"</div>"
        f"</div>"
    )
    st.markdown(doc_card_html, unsafe_allow_html=True)


# Helper: render the extracted text tab content


def _render_extracted_text_tab() -> None:
    """Render the 'Extracted Text' tab content based on current processing state."""
    status = st.session_state["processing_status"]

    # ── Idle state ────────────────────────────────────────────────────────
    if status == "idle":
        render_empty_state(
            icon="📄",
            title="No Document Processed",
            description=(
                "Upload a document to see extracted text, entities, "
                "and clause classifications."
            ),
        )
        return

    # ── Extracting state ──────────────────────────────────────────────────
    if status == "extracting":
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(
                    """
                    <div class="loading-container fade-in"
                         style="text-align: center;">
                        <div style="display: flex; flex-direction: column;
                             align-items: center; gap: 1rem;">
                            <div class="spinner"></div>
                            <p style="color: var(--text-muted);">
                                Extracting text from document...</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        return

    # ── Error during extraction ───────────────────────────────────────────
    if st.session_state.get("extraction_error"):
        render_alert(
            message=st.session_state.get(
                "error_message", "Failed to extract text from the document."
            ),
            type="error",
            title="Extraction Failed",
        )
        return

    # ── Data available (extracted, summarizing, or complete) ──────────────
    metadata = st.session_state.get("file_metadata")
    if metadata:
        _render_file_metadata(metadata)

    extracted_text = st.session_state.get("extracted_text")
    if extracted_text:
        st.markdown("### 📝 Extracted Text")
        st.markdown(
            f"""
            <div class="extracted-text-container">
                <pre class="extracted-text-pre">{extracted_text}</pre>
            </div>
            """,
            unsafe_allow_html=True,
        )

    entities = st.session_state.get("entities")
    clauses = st.session_state.get("clauses")
    if entities or clauses:
        _render_nlp_analysis_table(entities, clauses)


# Helper: render the summary tab content


def _render_summary_tab() -> None:
    """Render the 'Summary' tab content based on current processing state."""
    status = st.session_state["processing_status"]

    # ── Idle state ────────────────────────────────────────────────────────
    if status == "idle":
        render_empty_state(
            icon="📊",
            title="No Summary Yet",
            description=(
                "Upload a document, review the extracted text, "
                "then click 'Summarize' to generate an AI summary."
            ),
        )
        return

    # ── Extracting state ──────────────────────────────────────────────────
    if status == "extracting":
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(
                    """
                    <div class="loading-container fade-in"
                         style="text-align: center;">
                        <div style="display: flex; flex-direction: column;
                             align-items: center; gap: 1rem;">
                            <div class="spinner"></div>
                            <p style="color: var(--text-muted);">
                                Waiting for text extraction...</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        return

    # ── Extracted state (extraction done, summarisation pending) ──────────
    if status == "extracted":
        render_empty_state(
            icon="✏️",
            title="Ready to Summarize",
            description=(
                "Text has been extracted. Review it in the 'Extracted Text' tab, "
                "then click 'Summarize' below."
            ),
        )
        # Summarize button in the summary tab too
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(
                "Summarize Document", type="primary", key="summarize_btn_tab2"
            ):
                st.session_state["_summarize_clicked"] = True
                st.rerun()
        return

    # ── Summarizing state ─────────────────────────────────────────────────
    if status == "summarizing":
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(
                    """
                    <div class="loading-container fade-in"
                         style="text-align: center;">
                        <div style="display: flex; flex-direction: column;
                             align-items: center; gap: 1rem;">
                            <div class="spinner"></div>
                            <p style="color: var(--text-muted);">
                                Generating AI summary...</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        return

    # ── Error during summarization (extraction succeeded) ─────────────────
    if st.session_state.get("summarization_error"):
        render_alert(
            message=st.session_state.get(
                "error_message",
                "The AI summarization service encountered an issue.",
            ),
            type="error",
            title="Summarization Failed",
        )
        if st.session_state.get("show_retry"):
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("🔄 Retry Summary", type="primary"):
                    st.session_state["processing_status"] = "summarizing"
                    st.session_state["summarization_error"] = False
                    st.session_state["error_message"] = None
                    st.session_state["show_retry"] = False
                    st.rerun()
        return

    # ── Complete state ────────────────────────────────────────────────────
    summary = st.session_state.get("summary")
    llm_entities = st.session_state.get("llm_entities")

    if summary:
        st.markdown(
            f"""
            <div class="summary-box fade-in">
                <div class="summary-title">AI-Generated Summary</div>
                <div class="summary-content">{summary}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<p style='color: var(--text-muted); font-style: italic;'>"
            "No summary was generated.</p>",
            unsafe_allow_html=True,
        )

    if llm_entities:
        st.markdown("### 🔑 Key Entities")
        st.markdown(
            f"""
            <div class="summary-box"
                 style="border-left-color: var(--info);">
                <div class="summary-title">LLM-Extracted Entities</div>
                <div class="summary-content"
                     style="white-space: pre-wrap;">{llm_entities}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# Helper: run the extraction API call


def _run_extraction(uploaded_file: Any) -> None:
    """Call ``POST /api/documents/extract`` and populate session state.

    On success, sets ``processing_status`` to ``"extracted"`` and calls
    ``st.rerun()`` so the UI re-renders and displays the extracted text
    before summarisation begins.
    """
    st.session_state["processing_status"] = "extracting"
    st.session_state["extraction_error"] = False
    st.session_state["error_message"] = None

    file_bytes = uploaded_file.getvalue()

    try:
        files = {"file": (uploaded_file.name, file_bytes, uploaded_file.type)}
        data = {"extraction_mode": "flow"}

        with st.spinner("Extracting text from document..."):
            response = requests.post(
                EXTRACT_ENDPOINT,
                files=files,
                data=data,
                timeout=120,
            )

        if response.status_code == 200:
            result = response.json()

            st.session_state["extracted_text"] = result.get("cleaned_text", "")
            st.session_state["entities"] = result.get("entities")
            st.session_state["clauses"] = result.get("clauses", [])
            st.session_state["file_id"] = result.get("file_id")

            # Store file metadata for the metadata card
            st.session_state["file_metadata"] = {
                "filename": result.get("filename", uploaded_file.name),
                "size_kb": uploaded_file.size / 1024 if uploaded_file.size else 0,
                "mime_type": uploaded_file.type or "N/A",
                "pdf_type": result.get("pdf_type", "UNKNOWN"),
            }

            logger.info(
                "Extraction succeeded for %s (file_id=%s, %d chars, "
                "%d entities, %d clauses)",
                uploaded_file.name,
                result.get("file_id"),
                len(result.get("cleaned_text", "")),
                len(result.get("entities", {}).get("names", [])),
                len(result.get("clauses", [])),
            )

            # ── Signal extraction complete & re-render ───────────────────
            # The UI now displays the extracted text in the "Extracted Text"
            # tab.  On the *next* event cycle the processing block detects
            # status=="extracted" and kicks off summarisation.
            st.session_state["processing_status"] = "extracted"
            st.rerun()
        else:
            # Handle error responses
            error_detail = _extract_error_detail(response)
            st.session_state["extraction_error"] = True
            st.session_state["error_message"] = error_detail
            st.session_state["processing_status"] = "error"
            logger.error(
                "Extraction failed for %s: HTTP %d - %s",
                uploaded_file.name,
                response.status_code,
                error_detail,
            )
            st.rerun()

    except requests.exceptions.Timeout:
        st.session_state["extraction_error"] = True
        st.session_state["error_message"] = (
            "The document extraction timed out. "
            "Please try again with a smaller file."
        )
        st.session_state["processing_status"] = "error"
        logger.error("Extraction timed out for %s", uploaded_file.name)
        st.rerun()
    except requests.exceptions.ConnectionError:
        st.session_state["extraction_error"] = True
        st.session_state["error_message"] = (
            "Could not connect to the backend service. "
            "Please ensure the server is running."
        )
        st.session_state["processing_status"] = "error"
        logger.error("Connection error during extraction for %s", uploaded_file.name)
        st.rerun()
    except Exception as e:
        st.session_state["extraction_error"] = True
        st.session_state["error_message"] = f"An unexpected error occurred: {str(e)}"
        st.session_state["processing_status"] = "error"
        logger.exception(
            "Unexpected error during extraction for %s", uploaded_file.name
        )
        st.rerun()


# Helper: run the summarization API call


def _run_summarization() -> None:
    """Call ``POST /api/documents/summarize`` and populate session state.

    On success, sets ``processing_status`` to ``"complete"`` and calls
    ``st.rerun()`` so the UI re-renders and displays the summary alongside
    the previously-shown extracted text.

    Note: We deliberately do NOT wrap the API call in ``st.spinner()``
    because that creates a full-page overlay that darkens the entire UI.
    Instead, the ``processing_status == "summarizing"`` state causes the
    Summary tab to show an inline spinner, while the Extracted Text tab
    continues to display the extracted text normally.
    """
    st.session_state["processing_status"] = "summarizing"
    st.session_state["summarization_error"] = False
    st.session_state["error_message"] = None
    st.session_state["show_retry"] = False

    file_id = st.session_state.get("file_id")

    try:
        payload: Dict[str, Any] = {}
        if file_id:
            payload["file_id"] = file_id
        else:
            # Fallback: send extracted text directly
            text = st.session_state.get("extracted_text", "")
            if not text:
                st.session_state["summarization_error"] = True
                st.session_state["error_message"] = (
                    "No extracted text available for summarization."
                )
                st.session_state["processing_status"] = "error"
                st.rerun()
                return
            payload["text"] = text
            payload["entities"] = st.session_state.get("entities")

        response = requests.post(
            SUMMARIZE_ENDPOINT,
            json=payload,
            timeout=180,
        )

        if response.status_code == 200:
            result = response.json()

            st.session_state["summary"] = result.get("summary", "")
            st.session_state["llm_entities"] = result.get("llm_entities", "")
            st.session_state["processing_status"] = "complete"
            st.session_state["_switch_to_summary_tab"] = True

            logger.info(
                "Summarization succeeded (file_id=%s, %d chars summary, %.0fms)",
                file_id,
                len(result.get("summary", "")),
                result.get("processing_time_ms", 0),
            )

            # ── Trigger a re-render so the summary tab shows the result ──
            st.rerun()
        else:
            error_detail = _extract_error_detail(response)
            st.session_state["summarization_error"] = True
            st.session_state["error_message"] = error_detail
            st.session_state["show_retry"] = True
            st.session_state["processing_status"] = "error"
            logger.error(
                "Summarization failed: HTTP %d - %s",
                response.status_code,
                error_detail,
            )
            st.rerun()

    except requests.exceptions.Timeout:
        st.session_state["summarization_error"] = True
        st.session_state["error_message"] = (
            "The AI summarization timed out. "
            "Please try again or check the backend status."
        )
        st.session_state["show_retry"] = True
        st.session_state["processing_status"] = "error"
        logger.error("Summarization timed out for file_id=%s", file_id)
        st.rerun()
    except requests.exceptions.ConnectionError:
        st.session_state["summarization_error"] = True
        st.session_state["error_message"] = (
            "Could not connect to the backend service for summarization. "
            "Please ensure the server is running."
        )
        st.session_state["show_retry"] = True
        st.session_state["processing_status"] = "error"
        logger.error("Connection error during summarization for file_id=%s", file_id)
        st.rerun()
    except Exception as e:
        st.session_state["summarization_error"] = True
        st.session_state["error_message"] = f"An unexpected error occurred: {str(e)}"
        st.session_state["show_retry"] = True
        st.session_state["processing_status"] = "error"
        logger.exception(
            "Unexpected error during summarization for file_id=%s", file_id
        )
        st.rerun()


# Helper: extract user-facing error detail from a failed response


def _extract_error_detail(response: requests.Response) -> str:
    """Extract a human-readable error message from a failed API response."""
    try:
        body = response.json()
        # Try the standard error envelope first
        error = body.get("error", {})
        if isinstance(error, dict):
            message = error.get("message", "")
            if message:
                return message
        # Fallback to 'detail' (FastAPI default)
        detail = body.get("detail", "")
        if detail:
            return detail
        # Last resort: return the whole body as string
        return str(body)
    except (ValueError, AttributeError):
        # Not JSON — return raw text (truncated)
        text = response.text
        return text[:500] + ("..." if len(text) > 500 else "")


# Document upload widget
uploaded_file = st.file_uploader(
    "Choose a file",
    type=["pdf", "txt", "png", "jpg", "jpeg", "doc", "docx"],
    help="Supported: PDF, TXT, PNG, JPG, DOC, DOCX",
)

# ── File upload handling ────────────────────────────────────────────────
if uploaded_file is not None:
    st.success(f"✅ Uploaded: {uploaded_file.name}")

    # ── PDF type detection ──────────────────────────────────────────────
    if uploaded_file.type == "application/pdf" or uploaded_file.name.lower().endswith(
        ".pdf"
    ):
        try:
            uploaded_file.seek(0)
            pdf_type = detect_pdf_type(uploaded_file, filename=uploaded_file.name)
            uploaded_file.seek(0)

            if pdf_type == PDFType.SCANNED:
                st.markdown(render_scanned_indicator(), unsafe_allow_html=True)
        except Exception:
            logger.warning(
                "PDF type detection failed for: %s", uploaded_file.name, exc_info=True
            )

    # ── Auto-extract on new file upload ─────────────────────────────────
    # If the user uploaded a new file (different from the one already
    # processed), kick off extraction automatically.
    prev_file_id = st.session_state.get("file_id")
    if st.session_state["processing_status"] == "idle" or prev_file_id is None:
        # Reset all state for a fresh processing run
        for key in _DEFAULT_STATE:
            st.session_state[key] = _DEFAULT_STATE[key]

        # Step 1: Extraction (runs in this event cycle)
        # _run_extraction() will call st.rerun() on success, which halts
        # this cycle and re-renders the UI with the extracted text visible.
        _run_extraction(uploaded_file)

        # NOTE: If extraction succeeded, _run_extraction() calls st.rerun()
        # internally, so we never reach this point.  If we do reach it,
        # extraction failed (status is "error") and we still need to
        # re-render to show the error.
        st.rerun()

# ── Summarize button click handling ─────────────────────────────────────
# When the user clicks the Summarize button (inside the extracted text tab),
# it sets _summarize_clicked = True.  We detect that here and kick off
# summarization.
if st.session_state.pop("_summarize_clicked", False):
    if st.session_state["processing_status"] == "extracted":
        _run_summarization()

st.markdown("---")

# Tabbed interface
# When summarization completes, auto-switch to the Summary tab so the user
# sees the result immediately without having to click the tab themselves.
_tab_labels = ["📄 Extracted Text", "📊 Summary"]
_default_tab = 1 if st.session_state.get("_switch_to_summary_tab") else 0
tab1, tab2 = st.tabs(_tab_labels)

with tab1:
    _render_extracted_text_tab()

with tab2:
    _render_summary_tab()

# If the summary just completed, inject JS to click the Summary tab and
# clear the flag so it only fires once.
if st.session_state.pop("_switch_to_summary_tab", False):
    st.markdown(
        """
        <script>
        // Find the second tab button (Summary tab) and click it
        const tabs = parent.document.querySelectorAll('button[data-testid="stTabs"]');
        if (tabs.length >= 2) {
            tabs[1].click();
        }
        </script>
        """,
        unsafe_allow_html=True,
    )
