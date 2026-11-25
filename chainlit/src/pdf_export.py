"""
LatMatrix PDF Export Module - Generates PDF summaries with branding.

Uses WeasyPrint to convert HTML+CSS to PDF, which gives us native
markdown rendering, reliable logo positioning, and a clean template
that is easy to maintain.
"""

import base64
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────
# Logo path discovery
# ────────────────────────────────────────────────────────────


def _resolve_logo_path() -> str | None:
    """Locate logo_light.png relative to this source file or CWD."""
    candidates = [
        Path(__file__).resolve().parent.parent / "public" / "logo_light.png",
        Path.cwd() / "public" / "logo_light.png",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


# ────────────────────────────────────────────────────────────
# Minimal markdown -> HTML converter
# ────────────────────────────────────────────────────────────


def _md_to_html(text: str) -> str:
    """Convert a limited subset of markdown to HTML.

    Handles the patterns typically produced by LLM summaries:
    headings, bold, inline code, bullet lists, and paragraphs.
    """
    lines = text.split("\n")
    html_lines: list[str] = []
    in_list = False

    for line in lines:
        # Headings
        h_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if h_match:
            level = len(h_match.group(1))
            content = _inline_md(h_match.group(2))
            html_lines.append(f"<h{level}>{content}</h{level}>")
            continue

        # Horizontal rule
        if re.match(r"^[-=*]{3,}$", line.strip()):
            html_lines.append("<hr>")
            continue

        # Bullet list items
        li_match = re.match(r"^[\-\*]\s+(.+)$", line)
        if li_match:
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{_inline_md(li_match.group(1))}</li>")
            continue

        # Close open list if we hit a non-list line
        if in_list:
            html_lines.append("</ul>")
            in_list = False

        # Empty line = paragraph break
        if not line.strip():
            continue

        # Regular paragraph
        html_lines.append(f"<p>{_inline_md(line)}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def _inline_md(text: str) -> str:
    """Convert inline markdown patterns to HTML."""
    # ``inline code`` or `code`
    text = re.sub(r"``(.+?)``", r"<code>\1</code>", text)
    text = re.sub(r"(?<!`)`([^`]+?)`(?!`)", r"<code>\1</code>", text)
    # **bold**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # *italic*
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", text)
    # Strip standalone triple backticks (code fences)
    text = re.sub(r"```", "", text)
    return text


# ────────────────────────────────────────────────────────────
# CSS stylesheet for the PDF (stored as a list to avoid triple-quote parsing issues)
# ────────────────────────────────────────────────────────────

_PAGE_CSS = "\n".join([
    "    @page {",
    "        margin: 20mm 25mm;",
    "    }",
    "    body {",
    "        font-family: DejaVu Sans, sans-serif;",
    "        font-size: 10pt;",
    "        line-height: 1.6;",
    "        color: #333;",
    "    }",
    "    .logo {",
    "        text-align: center;",
    "        margin-bottom: 24px;",
    "        padding-top: 0;",
    "    }",
    "    .logo img {",
    "        width: 140px;",
    "    }",
    "    h1 {",
    "        font-size: 16pt;",
    "        text-align: center;",
    "        color: #111;",
    "        margin: 0 0 4px 0;",
    "    }",
    '    .doc-filename {',
    "        font-size: 9pt;",
    "        text-align: center;",
    "        color: #888;",
    "        margin: 0 0 20px 0;",
    "    }",
    "    h2 {",
    "        font-size: 12pt;",
    "        color: #222;",
    "        border-bottom: 1px solid #ccc;",
    "        padding-bottom: 3px;",
    "        margin: 18px 0 6px 0;",
    "    }",
    "    h3 {",
    "        font-size: 11pt;",
    "        color: #333;",
    "        margin: 14px 0 4px 0;",
    "    }",
    "    h4, h5, h6 {",
    "        font-size: 10pt;",
    "        color: #444;",
    "        margin: 12px 0 4px 0;",
    "    }",
    "    .meta {",
    "        font-size: 9pt;",
    "        color: #666;",
    "        margin: 4px 0;",
    "    }",
    "    p {",
    "        margin: 6px 0;",
    "        text-align: justify;",
    "    }",
    "    ul {",
    "        margin: 4px 0 4px 18px;",
    "        padding: 0;",
    "    }",
    "    li {",
    "        margin: 2px 0;",
    "    }",
    "    code {",
    "        font-family: DejaVu Sans Mono, monospace;",
    "        font-size: 9pt;",
    "        background: #f4f4f4;",
    "        padding: 1px 4px;",
    "        border-radius: 3px;",
    "    }",
    "    hr {",
    "        border: none;",
    "        border-top: 1px solid #ddd;",
    "        margin: 16px 0;",
    "    }",
    "    .footer {",
    "        text-align: center;",
    "        font-size: 8pt;",
    "        color: #aaa;",
    "        margin-top: 30px;",
    "        border-top: 1px solid #eee;",
    "        padding-top: 10px;",
    "    }",
])


def _build_html(
    filename: str,
    summary_md: str,
    entities: list[dict[str, Any]],
    clauses: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> str:
    """Build a full HTML document string for the summary PDF."""
    logo_path = _resolve_logo_path()

    logo_html = ""
    if logo_path:
        try:
            with open(logo_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            logo_html = (
                '<div class="logo">'
                f'<img src="data:image/png;base64,{b64}" alt="LatMatrix logo">'
                "</div>"
            )
        except (FileNotFoundError, PermissionError, OSError) as exc:
            logger.warning(
                "Could not read logo at %s: %s; PDF will be generated without logo",
                logo_path,
                exc,
            )
            logo_html = '<div style="height:20px"></div>'
    else:
        logger.warning("logo_light.png not found; PDF will be generated without logo")
        logo_html = '<div style="height:20px"></div>'

    # ── Metadata block ──────────────────────────────────────
    meta_lines = ""
    if metadata:
        ts = metadata.get("timestamp")
        if ts:
            meta_lines += f'<p class="meta">Analyzed: {ts}</p>\n'
        dt = metadata.get("document_type")
        if dt:
            meta_lines += f'<p class="meta">Document Type: {dt}</p>\n'

    # ── Summary ─────────────────────────────────────────────
    summary_html = _md_to_html(summary_md)

    # ── Entities ────────────────────────────────────────────
    entities_html = ""
    if entities:
        items = ""
        for entity in entities:
            name = entity.get("name", entity.get("text", "Unknown"))
            label = entity.get("label", entity.get("type", "Unknown"))
            items += f"<li><strong>{name}</strong> ({label})</li>\n"
        entities_html = f"<h2>Key Entities</h2>\n<ul>\n{items}</ul>\n"

    # ── Clauses ─────────────────────────────────────────────
    clauses_html = ""
    if clauses:
        items = ""
        for i, clause in enumerate(clauses, 1):
            clause_text = clause.get("text", clause.get("clause", ""))
            clause_rendered = _md_to_html(clause_text)
            items += f"<h3>Clause {i}</h3>\n{clause_rendered}\n"
        clauses_html = f"<h2>Key Clauses</h2>\n{items}\n"

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<style>\n{_PAGE_CSS}\n</style>\n"
        "</head>\n"
        "<body>\n"
        f"{logo_html}\n"
        "<h1>Document Summary</h1>\n"
        f'<p class="doc-filename">{filename}</p>\n'
        f"{meta_lines}\n"
        "<h2>Summary</h2>\n"
        f"{summary_html}\n"
        f"{entities_html}\n"
        f"{clauses_html}\n"
        '<div class="footer">Generated by LatMatrix AI</div>\n'
        "</body>\n"
        "</html>"
    )


# ────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────


def generate_pdf_summary(
    filename: str,
    summary: str,
    entities: list[dict[str, Any]],
    clauses: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> bytes:
    """Generate a PDF document with the LatMatrix logo and summary content.

    The summary text may contain markdown formatting (headings, bold,
    lists, code) -- it is converted to HTML and rendered via WeasyPrint.

    Returns the PDF as bytes, ready to be sent as a download element.
    """
    from weasyprint import HTML

    html_str = _build_html(
        filename=filename,
        summary_md=summary,
        entities=entities,
        clauses=clauses,
        metadata=metadata,
    )
    try:
        pdf_bytes = HTML(string=html_str, encoding="utf-8").write_pdf()
    except Exception as exc:
        logger.error(
            "WeasyPrint PDF generation failed: %s", exc, exc_info=True
        )
        raise

    return pdf_bytes
