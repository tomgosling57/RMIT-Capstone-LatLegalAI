"""
LatMatrix Summary Module - Summary generation, storage, and download handling.

Provides functions for generating Markdown/plain-text summaries, storing
summary data in the Chainlit user session, offering download actions,
handling download action callbacks, and reloading persisted document
elements from the database on chat resume.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import chainlit as cl
from chainlit.data import get_data_layer

from .pdf_export import generate_pdf_summary

logger = logging.getLogger(__name__)


def generate_markdown_summary(
    filename: str,
    summary: str,
    entities: List[Dict[str, Any]],
    clauses: List[Dict[str, Any]],
    metadata: Dict[str, Any] | None = None,
) -> str:
    """Generate a Markdown-formatted summary document."""
    md_content = f"# Document Summary: {filename}\n\n"
    if metadata:
        md_content += "## Metadata\n"
        if metadata.get("timestamp"):
            md_content += f"- **Analyzed:** {metadata['timestamp']}\n"
        if metadata.get("document_type"):
            md_content += f"- **Document Type:** {metadata['document_type']}\n"
        md_content += "\n"
    md_content += "## Summary\n\n"
    md_content += f"{summary}\n\n"
    if entities:
        md_content += "## Key Entities\n\n"
        for entity in entities:
            name = entity.get("name", entity.get("text", "Unknown"))
            label = entity.get("label", entity.get("type", "Unknown"))
            md_content += f"- **{name}** ({label})\n"
        md_content += "\n"
    if clauses:
        md_content += "## Key Clauses\n\n"
        for i, clause in enumerate(clauses, 1):
            clause_text = clause.get("text", clause.get("clause", ""))
            md_content += f"### Clause {i}\n{clause_text}\n\n"
    return md_content


def generate_txt_summary(
    filename: str,
    summary: str,
    entities: List[Dict[str, Any]],
    clauses: List[Dict[str, Any]],
    metadata: Dict[str, Any] | None = None,
) -> str:
    """Generate a plain text summary document."""
    txt_content = f"DOCUMENT SUMMARY: {filename}\n"
    txt_content += "=" * 80 + "\n\n"
    if metadata:
        txt_content += "METADATA\n"
        txt_content += "-" * 80 + "\n"
        if metadata.get("timestamp"):
            txt_content += f"Analyzed: {metadata['timestamp']}\n"
        if metadata.get("document_type"):
            txt_content += f"Document Type: {metadata['document_type']}\n"
        txt_content += "\n"
    txt_content += "SUMMARY\n"
    txt_content += "-" * 80 + "\n"
    txt_content += f"{summary}\n\n"
    if entities:
        txt_content += "KEY ENTITIES\n"
        txt_content += "-" * 80 + "\n"
        for entity in entities:
            name = entity.get("name", entity.get("text", "Unknown"))
            label = entity.get("label", entity.get("type", "Unknown"))
            txt_content += f"- {name} ({label})\n"
        txt_content += "\n"
    if clauses:
        txt_content += "KEY CLAUSES\n"
        txt_content += "-" * 80 + "\n"
        for i, clause in enumerate(clauses, 1):
            clause_text = clause.get("text", clause.get("clause", ""))
            txt_content += f"Clause {i}:\n{clause_text}\n\n"
    return txt_content


async def store_summary_in_session(
    filename: str,
    summary: str,
    entities: List[Dict[str, Any]],
    clauses: List[Dict[str, Any]],
    extracted_text: str = "",
) -> None:
    """Store summary data in cl.user_session for persistence across messages."""
    summaries = cl.user_session.get("summaries", {})
    summaries[filename] = {
        "summary": summary,
        "entities": entities,
        "clauses": clauses,
        "extracted_text": extracted_text,
        "timestamp": datetime.now().isoformat(),
    }
    cl.user_session.set("summaries", summaries)


async def offer_downloads(
    summary_key: str,
    source_file,
    summary_content: str = "",
    elements: list | None = None,
) -> None:
    """Sends a standalone message offering download options for the document.

    Optional ``elements`` (e.g. ``cl.Text``) are attached to the message for
    data-layer persistence and side-panel display.

    Note:
        The summary text is NOT duplicated here — it is delivered as its own
        message by ``stream_summary_analysis()``, so the browser's native copy
        button on that message captures the summary directly.

    .. deprecated:: 0.1.0
        The *summary_content* parameter is no longer used and will be removed
        in a future version. Summary text is delivered via
        ``stream_summary_analysis()`` instead.
    """
    download_msg = cl.Message(
        content=(
            f"\U0001f4e5 **Download the extracted text or summary from "
            f"`{source_file.name}`:**"
        ),
        elements=elements or [],
        actions=[
            cl.Action(
                name="download_extracted_text",
                value=summary_key,
                label="\U0001f4c4 Download Extracted Text",
                payload={"filename": summary_key},
            ),
            cl.Action(
                name="download_summary_pdf",
                value=summary_key,
                label="\U0001f4e5 Download Summary (PDF)",
                payload={"filename": summary_key},
            ),
        ],
    )
    await download_msg.send()


@cl.action_callback("download_extracted_text")
async def on_download_extracted_text(action: cl.Action) -> None:
    """Handle download action for extracted text."""
    filename = None
    if hasattr(action, "payload") and action.payload:
        filename = action.payload.get("filename")
    if not filename:
        await cl.Message(
            content="\u274c **Error:** No filename provided in action."
        ).send()
        return
    summaries = cl.user_session.get("summaries", {})
    if not summaries or filename not in summaries:
        await cl.Message(
            content=f"\u274c **Error:** Data for `{filename}` not found in session."
        ).send()
        return
    summary_data = summaries[filename]
    extracted_text = summary_data.get("extracted_text", "")
    if not extracted_text:
        await cl.Message(
            content="\u26a0\ufe0f **No extracted text available** for this entry."
        ).send()
        return
    base_name = Path(filename).stem
    md_content = f"# Extracted Text: {base_name}\n\n{extracted_text}"
    md_file_element = cl.File(
        name="Markdown Format",
        content=md_content.encode("utf-8"),
        mime="text/markdown",
    )
    txt_content = f"EXTRACTED TEXT: {base_name}\n{'=' * 80}\n\n{extracted_text}"
    txt_file_element = cl.File(
        name="Text Format",
        content=txt_content.encode("utf-8"),
        mime="text/plain",
    )
    await cl.Message(
        content="\U0001f4c4 **Download extracted text:**",
        elements=[md_file_element, txt_file_element],
    ).send()


@cl.action_callback("download_summary_pdf")
async def on_download_summary_pdf(action: cl.Action) -> None:
    """Handle download action for summary as PDF with logo."""
    filename = None
    if hasattr(action, "payload") and action.payload:
        filename = action.payload.get("filename")
    if not filename:
        await cl.Message(
            content="\u274c **Error:** No filename provided in action."
        ).send()
        return
    summaries = cl.user_session.get("summaries", {})
    if not summaries or filename not in summaries:
        await cl.Message(
            content=f"\u274c **Error:** Summary for `{filename}` not found in session."
        ).send()
        return
    summary_data = summaries[filename]

    # Generate PDF bytes with logo at the top
    pdf_bytes = generate_pdf_summary(
        filename=filename,
        summary=summary_data["summary"],
        entities=summary_data["entities"],
        clauses=summary_data["clauses"],
        metadata={
            "timestamp": summary_data["timestamp"],
            "document_type": "Legal Document",
        },
    )

    pdf_file_element = cl.File(
        name=f"{Path(filename).stem}.pdf",
        content=pdf_bytes,
        mime="application/pdf",
    )
    await cl.Message(
        content="\U0001f4e5 **Download summary (PDF):**",
        elements=[pdf_file_element],
    ).send()


async def reload_summaries_from_db(thread_id: str) -> dict:
    """Reload document summaries from persisted elements in the SQLite table.

    Queries the ``elements`` table for stored ``cl.Text`` elements whose names
    start with ``extracted-text-`` or ``summary-``, parses the ``props`` JSON
    column, and returns a dict keyed by filename.

    Returns:
        A dict mapping filenames to ``{"extracted_text": ..., "summary": ...}``
        entries, or an empty dict if no elements are found or the data layer
        is unavailable.
    """
    dl = get_data_layer()
    if dl is None or not hasattr(dl, "execute_sql"):
        logger.warning("Data layer not available — cannot reload document elements")
        return {}

    try:
        rows = await dl.execute_sql(
            'SELECT name, props FROM elements WHERE "threadId" = :thread_id',
            {"thread_id": thread_id},
        )
        if not rows or not isinstance(rows, list):
            return {}

        summaries: dict = {}
        for row in rows:
            name: str = row.get("name", "")
            if not name.startswith(("extracted-text-", "summary-")):
                continue

            prefix = (
                "extracted-text-" if name.startswith("extracted-text-") else "summary-"
            )
            fname = name[len(prefix) :]

            raw_props = row.get("props", "{}")
            if isinstance(raw_props, str):
                props = json.loads(raw_props)
            elif isinstance(raw_props, dict):
                props = raw_props
            else:
                props = {}

            content = props.get("content", "")
            if not content:
                continue

            entry = summaries.setdefault(fname, {})
            if name.startswith("extracted-text-"):
                entry["extracted_text"] = content
            else:
                entry["summary"] = content

        return summaries
    except Exception:
        logger.warning("Failed to reload document elements on resume", exc_info=True)
        return {}
