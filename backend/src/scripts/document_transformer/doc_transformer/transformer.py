"""
doc_transformer/transformer.py
================================
Core library for generating PDF, DOCX, scanned-PDF (image-based), and TXT
documents from plain-text input, with single-column, double-column, and
randomised multi-column (max 3) layout variants for parser testing.

Configurable via constructor or environment variables:
  INPUT_DIR   – directory scanned for *.txt source files (default: ./input)
  OUTPUT_DIR  – directory where all generated files land  (default: ./output)
"""

from __future__ import annotations

import os
import random
import re
import textwrap
from pathlib import Path
from typing import Literal

# ── third-party ──────────────────────────────────────────────────────────────
from PIL import Image, ImageDraw, ImageFont
from docx import Document as DocxDocument
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from fpdf import FPDF
from weasyprint import HTML

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

LayoutType = Literal["single", "double", "multi"]


def _split_paragraphs(text: str) -> list[str]:
    """Return a list of non-empty paragraph strings."""
    return [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]


# ─────────────────────────────────────────────────────────────────────────────
# PDF helpers – WeasyPrint (HTML + CSS)
# ─────────────────────────────────────────────────────────────────────────────

_PDF_CSS = """
@page {
  size: letter;
  margin: 0.75in;
}
body {
  font-family: 'Noto Sans Devanagari', 'Noto Sans', 'FreeSerif', serif;
  font-size: 10pt;
  line-height: 1.4;
  color: #141414;
  /* Prevent pdfplumber from splitting individual glyphs into separate
     text runs by disabling ligature-based font features that can cause
     Pango to position each character independently. */
  font-kerning: normal;
  font-variant-ligatures: normal;
  font-feature-settings: normal;
}
h1 {
  font-size: 14pt;
  margin-bottom: 0.5em;
  page-break-after: avoid;
}
p {
  margin: 0 0 0.4em 0;
  text-align: justify;
  /* Ensure consistent word and letter spacing to prevent pdfplumber
     from interpreting individual glyph positions as separate words. */
  word-spacing: 0px;
  letter-spacing: 0px;
}
/* Single-column layout uses block layout (no column-count) to ensure
   pdfplumber extracts text as continuous runs, especially for complex
   scripts like Devanagari where CSS columns cause individual character
   positioning that pdfplumber interprets as separate words. */
.cols-double {
  column-count: 2;
  column-gap: 0.4in;
}
.cols-multi-1 {
  column-count: 1;
}
.cols-multi-2 {
  column-count: 2;
  column-gap: 0.4in;
}
.cols-multi-3 {
  column-count: 3;
  column-gap: 0.3in;
}
.section-break {
  page-break-before: always;
}
"""


def _html_escape(text: str) -> str:
    """Minimal HTML escaping — only &, <, > need escaping."""
    return text.replace("&", "&").replace("<", "<").replace(">", ">")


def _paragraphs_to_html(paragraphs: list[str], title: str) -> str:
    """Convert a list of paragraphs into an HTML body string.

    Each paragraph is wrapped in ``<p>`` tags.  The title is rendered as
    an ``<h1>`` heading.  WeasyPrint handles Unicode natively, so no
    special encoding is needed beyond standard HTML escaping.
    """
    parts = [f"<h1>{_html_escape(title)}</h1>"]
    for para in paragraphs:
        parts.append(f"<p>{_html_escape(para)}</p>")
    return "\n".join(parts)


def _get_devanagari_font_path() -> str | None:
    """Return the path to a TTF font that supports both Latin and Devanagari
    glyphs, or None.

    FreeSerif is preferred because it covers both Latin (with accented
    characters for Spanish, French, German) and Devanagari scripts in a
    single font file, avoiding missing-glyph issues in fpdf2.
    """
    candidates = (
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "/usr/share/fonts/opentype/freefont/FreeSerif.otf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerifDevanagari-Regular.ttf",
    )
    for path in candidates:
        if Path(path).exists():
            return path
    return None


def _has_devanagari(text: str) -> bool:
    """Check if text contains any Devanagari characters (U+0900-U+097F)."""
    return any(0x0900 <= ord(ch) <= 0x097F for ch in text)


def _generate_pdf_fpdf2(
    text: str,
    output_path: Path,
    title: str = "Document",
) -> Path:
    """
    Generate a single-column searchable PDF using fpdf2.

    fpdf2 produces PDFs where pdfplumber extracts Devanagari text as
    continuous character runs (unlike WeasyPrint, which positions each
    Devanagari glyph individually, causing pdfplumber to split characters
    with spaces). This function is used for single-column layouts where
    clean text extraction is critical.

    Falls back to WeasyPrint if the Devanagari font is not available.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    paragraphs = _split_paragraphs(text)
    font_path = _get_devanagari_font_path()

    if font_path is None:
        # Fall back to WeasyPrint if no Devanagari font available
        html = _build_single_column_html(paragraphs, title)
        HTML(string=html).write_pdf(str(output_path))
        return output_path

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Deva", "", font_path)
    pdf.set_font("Deva", "", 10)

    # Title
    pdf.set_font("Deva", "", 14)
    pdf.multi_cell(0, 6, title)
    pdf.ln(2)
    pdf.set_font("Deva", "", 10)

    # Paragraphs
    for para in paragraphs:
        pdf.multi_cell(0, 5, para)
        pdf.ln(1)

    pdf.output(str(output_path))
    return output_path


def generate_pdf(
    text: str,
    output_path: Path,
    layout: LayoutType = "single",
    title: str = "Document",
) -> Path:
    """
    Generate a searchable PDF with the requested column layout.

    For single-column layouts, uses fpdf2 (which produces clean text
    extraction for complex scripts like Devanagari). For double and
    multi-column layouts, uses WeasyPrint (HTML + CSS) which supports
    CSS columns natively.

    Args:
        text: Plain-text content to render.
        output_path: Where to write the PDF file.
        layout: Column layout - "single", "double", or "multi".
        title: Document title rendered as a heading.

    Returns:
        The output Path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if layout == "single":
        # fpdf2 produces clean text extraction for complex scripts like
        # Devanagari.  Only use it when the text actually contains Devanagari
        # characters; for Latin-only text (Spanish, French, German) WeasyPrint
        # works fine and avoids font-missing-glyph warnings.
        if _has_devanagari(text):
            return _generate_pdf_fpdf2(text, output_path, title=title)
        paragraphs = _split_paragraphs(text)
        html = _build_single_column_html(paragraphs, title)
        HTML(string=html).write_pdf(str(output_path))
        return output_path

    # Double and multi-column layouts use WeasyPrint for CSS column support
    paragraphs = _split_paragraphs(text)

    if layout == "double":
        html = _build_double_column_html(paragraphs, title)
    else:
        html = _build_multi_column_html(paragraphs, title)

    HTML(string=html).write_pdf(str(output_path))
    return output_path


def _build_single_column_html(paragraphs: list[str], title: str) -> str:
    body = _paragraphs_to_html(paragraphs, title)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>{_PDF_CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


def _build_double_column_html(paragraphs: list[str], title: str) -> str:
    body = _paragraphs_to_html(paragraphs, title)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>{_PDF_CSS}</style>
</head>
<body class="cols-double">
{body}
</body>
</html>"""


def _build_multi_column_html(paragraphs: list[str], title: str) -> str:
    """Split paragraphs into chunks, each on a separate page with a random
    column count (1–3).

    When n=1, no CSS column class is applied (plain block layout) to avoid
    pdfplumber splitting individual characters into separate words, which
    is a known issue with CSS columns and complex scripts like Devanagari.
    """
    CHUNK = max(1, len(paragraphs) // max(3, len(paragraphs) // 6))
    chunks = [paragraphs[i : i + CHUNK] for i in range(0, len(paragraphs), CHUNK)]
    if not chunks:
        chunks = [paragraphs]

    sections: list[str] = []
    for idx, chunk in enumerate(chunks):
        n = random.randint(1, 3)
        # For n=1, use plain block layout (no CSS columns) to prevent
        # pdfplumber from splitting individual characters into separate words.
        cls = "" if n == 1 else f"cols-multi-{n}"
        body = _paragraphs_to_html(chunk, title if idx == 0 else "")
        if cls:
            section_class = cls if idx == 0 else f"{cls} section-break"
            sections.append(f'<div class="{section_class}">\n{body}\n</div>')
        else:
            section_class = "" if idx == 0 else "section-break"
            sections.append(f'<div class="{section_class}">\n{body}\n</div>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>{_PDF_CSS}</style>
</head>
<body>
{"".join(sections)}
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# DOCX helpers – python-docx
# ─────────────────────────────────────────────────────────────────────────────


def _set_docx_columns(section, n_cols: int, equal_width: bool = True):
    """Add <w:cols> element to a section to produce a multi-column layout."""
    sectPr = section._sectPr
    # Remove existing cols element if present
    for old in sectPr.findall(qn("w:cols")):
        sectPr.remove(old)

    cols_el = OxmlElement("w:cols")
    cols_el.set(qn("w:num"), str(n_cols))
    cols_el.set(qn("w:equalWidth"), "1" if equal_width else "0")
    cols_el.set(qn("w:space"), "720")  # ~0.5 inch gutter in twips
    sectPr.append(cols_el)


def _add_section_break(doc: DocxDocument, n_cols: int):
    """Append a continuous section break, then set column count for it."""
    from docx.oxml.ns import qn as _qn
    from docx.oxml import OxmlElement as _OE

    # Add a paragraph that carries the section break
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    sectPr = _OE("w:sectPr")

    cols_el = _OE("w:cols")
    cols_el.set(_qn("w:num"), str(n_cols))
    cols_el.set(_qn("w:equalWidth"), "1")
    cols_el.set(_qn("w:space"), "720")
    sectPr.append(cols_el)

    pgSzEl = _OE("w:pgSz")
    pgSzEl.set(_qn("w:w"), "12240")  # 8.5 in
    pgSzEl.set(_qn("w:h"), "15840")  # 11 in
    sectPr.append(pgSzEl)

    pgMarEl = _OE("w:pgMar")
    pgMarEl.set(_qn("w:top"), "1080")
    pgMarEl.set(_qn("w:right"), "1080")
    pgMarEl.set(_qn("w:bottom"), "1080")
    pgMarEl.set(_qn("w:left"), "1080")
    sectPr.append(pgMarEl)

    # Attach sectPr to the paragraph's pPr
    pPr.append(sectPr)


def generate_docx(
    text: str,
    output_path: Path,
    layout: LayoutType = "single",
    title: str = "Document",
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    paragraphs = _split_paragraphs(text)
    doc = DocxDocument()

    # Title
    doc.add_heading(title, level=0)

    if layout in ("single", "double"):
        n_cols = 1 if layout == "single" else 2
        for para in paragraphs:
            doc.add_paragraph(para)
        section = doc.sections[0]
        _set_docx_columns(section, n_cols)

    else:  # multi
        # Split paragraphs into chunks, each chunk in a random column count
        CHUNK = max(1, len(paragraphs) // max(3, len(paragraphs) // 8))
        chunks = [paragraphs[i : i + CHUNK] for i in range(0, len(paragraphs), CHUNK)]

        # Set the *document* section to 1 col (for the title)
        _set_docx_columns(doc.sections[0], 1)

        for idx, chunk in enumerate(chunks):
            n = random.randint(1, 3)
            if idx > 0:
                _add_section_break(doc, n)
            for para in chunk:
                doc.add_paragraph(para)

        # Finalise last section column count
        _set_docx_columns(doc.sections[-1], random.randint(1, 3))

    doc.save(str(output_path))
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# TXT output
# ─────────────────────────────────────────────────────────────────────────────


def generate_txt(
    text: str,
    output_path: Path,
    layout: LayoutType = "single",
    title: str = "Document",
    line_width: int = 80,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    paragraphs = _split_paragraphs(text)

    if layout == "single":
        n_cols = 1
    elif layout == "double":
        n_cols = 2
    else:
        n_cols = None  # random per chunk

    lines_out: list[str] = [title, "=" * min(len(title), line_width), ""]

    def _wrap_col(para: str, width: int) -> list[str]:
        return textwrap.wrap(para, width=width) or [""]

    if n_cols is not None:
        if n_cols == 1:
            for para in paragraphs:
                lines_out.extend(_wrap_col(para, line_width))
                lines_out.append("")
        else:
            col_w = (line_width - (n_cols - 1) * 2) // n_cols
            # Interleave paragraphs across columns side-by-side
            half = max(1, len(paragraphs) // 2)
            left_paras = paragraphs[:half]
            right_paras = paragraphs[half:]
            left_lines = []
            for p in left_paras:
                left_lines.extend(_wrap_col(p, col_w))
                left_lines.append("")
            right_lines = []
            for p in right_paras:
                right_lines.extend(_wrap_col(p, col_w))
                right_lines.append("")
            max_len = max(len(left_lines), len(right_lines))
            left_lines += [""] * (max_len - len(left_lines))
            right_lines += [""] * (max_len - len(right_lines))
            for _left, _right in zip(left_lines, right_lines):
                lines_out.append(f"{_left:<{col_w}}  {_right}")
    else:
        # Multi: random col per chunk
        CHUNK = max(1, len(paragraphs) // 4)
        chunks = [paragraphs[i : i + CHUNK] for i in range(0, len(paragraphs), CHUNK)]
        for chunk in chunks:
            n = random.randint(1, 3)
            lines_out.append(f"[{n}-column section]")
            lines_out.append("-" * line_width)
            if n == 1:
                for para in chunk:
                    lines_out.extend(_wrap_col(para, line_width))
                    lines_out.append("")
            else:
                col_w = (line_width - (n - 1) * 2) // n
                col_groups = [[] for _ in range(n)]
                for i, para in enumerate(chunk):
                    col_groups[i % n].extend(_wrap_col(para, col_w))
                    col_groups[i % n].append("")
                max_len = max((len(g) for g in col_groups), default=0)
                for g in col_groups:
                    g += [""] * (max_len - len(g))
                for row in zip(*col_groups):
                    lines_out.append("  ".join(f"{cell:<{col_w}}" for cell in row))
            lines_out.append("")

    output_path.write_text("\n".join(lines_out), encoding="utf-8")
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Scanned PDF (image-based, no selectable text)
# ─────────────────────────────────────────────────────────────────────────────

_SCAN_DPI = 150
_PAGE_W_PX = int(8.5 * _SCAN_DPI)  # 1275
_PAGE_H_PX = int(11.0 * _SCAN_DPI)  # 1650
_MARGIN_PX = int(0.75 * _SCAN_DPI)  # 112
_FONT_SIZE_PX = 18  # approximate readable size at 150 dpi


def _get_pil_font(
    size: int = _FONT_SIZE_PX, text: str = ""
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Return a PIL font suitable for rendering *text*.
    Falls back to default if no truetype available.

    When *text* contains Devanagari characters (Hindi), the function
    prefers a Devanagari-capable font (Noto Sans Devanagari or FreeSerif).
    """
    # Detect Devanagari Unicode block (U+0900–U+097F)
    has_devanagari = any(0x0900 <= ord(ch) <= 0x097F for ch in text)

    if has_devanagari:
        devanagari_candidates = (
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSerifDevanagari-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
            "/usr/share/fonts/opentype/freefont/FreeSerif.otf",
        )
        for name in devanagari_candidates:
            if Path(name).exists():
                try:
                    return ImageFont.truetype(name, size)
                except Exception:
                    continue

    # Fallback: try common system mono fonts (Latin scripts)
    try:
        for name in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
            "/System/Library/Fonts/Courier.ttc",
        ):
            if Path(name).exists():
                return ImageFont.truetype(name, size)
    except Exception:
        pass
    return ImageFont.load_default()


def _render_text_to_image(
    paragraphs: list[str],
    n_cols: int,
    noise: bool = True,
) -> Image.Image:
    """Render plain paragraphs onto a page image in n_cols columns."""
    img = Image.new("RGB", (_PAGE_W_PX, _PAGE_H_PX), color=(252, 250, 248))
    draw = ImageDraw.Draw(img)
    # Combine all paragraphs to detect script requirements (e.g. Devanagari)
    all_text = " ".join(paragraphs)
    font = _get_pil_font(_FONT_SIZE_PX, text=all_text)
    line_h = _FONT_SIZE_PX + 4

    gutter_px = int(0.2 * _SCAN_DPI)
    col_w = (_PAGE_W_PX - 2 * _MARGIN_PX - (n_cols - 1) * gutter_px) // n_cols

    # Distribute paragraphs across columns
    col_paragraphs: list[list[str]] = [[] for _ in range(n_cols)]
    for i, p in enumerate(paragraphs):
        col_paragraphs[i % n_cols].append(p)

    for ci in range(n_cols):
        x0 = _MARGIN_PX + ci * (col_w + gutter_px)
        y = _MARGIN_PX
        for para in col_paragraphs[ci]:
            # Wrap text to column width (rough char-based)
            chars_per_line = max(1, col_w // (_FONT_SIZE_PX // 2 + 1))
            wrapped = textwrap.wrap(para, width=chars_per_line) or [""]
            for line in wrapped:
                if y + line_h > _PAGE_H_PX - _MARGIN_PX:
                    break
                draw.text((x0, y), line, font=font, fill=(20, 20, 20))
                y += line_h
            y += line_h  # paragraph gap

    # Optional scan noise
    if noise:
        import random as _r

        pixels = img.load()
        for _ in range(2000):
            rx = _r.randint(0, _PAGE_W_PX - 1)
            ry = _r.randint(0, _PAGE_H_PX - 1)
            v = _r.randint(180, 230)
            pixels[rx, ry] = (v, v, v)

    return img


def generate_scanned_pdf(
    text: str,
    output_path: Path,
    layout: LayoutType = "single",
    title: str = "Document",
) -> Path:
    """
    Produce a PDF whose pages are rasterised images (simulating a scanner),
    containing no selectable text layer.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    paragraphs = _split_paragraphs(text)
    # Prepend title with a decorative Devanagari-compatible separator
    # instead of "=" underline, which Tesseract's Devanagari model
    # misreads as danda characters (॥) — see AALA-209.
    separator = f"— {title} —"
    paragraphs = [title, separator] + paragraphs

    # Decide column counts per page
    PARAS_PER_PAGE = 12

    def _col_count(idx: int) -> int:
        if layout == "single":
            return 1
        if layout == "double":
            return 2
        return random.randint(1, 3)

    # Split paragraphs into pages
    page_chunks = [
        paragraphs[i : i + PARAS_PER_PAGE]
        for i in range(0, len(paragraphs), PARAS_PER_PAGE)
    ]
    if not page_chunks:
        page_chunks = [[title]]

    images: list[Image.Image] = []
    for idx, chunk in enumerate(page_chunks):
        n = _col_count(idx)
        images.append(_render_text_to_image(chunk, n_cols=n))

    # Save as multi-page PDF via Pillow
    images[0].save(
        str(output_path),
        format="PDF",
        save_all=True,
        append_images=images[1:],
        resolution=_SCAN_DPI,
    )
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# High-level transformer
# ─────────────────────────────────────────────────────────────────────────────


class DocumentTransformer:
    """
    Converts a plain-text input into multiple document formats and layout
    variants for parser testing.

    Parameters
    ----------
    input_dir  : directory containing *.txt source files (default: ./input)
    output_dir : directory where generated files are written (default: ./output)
    """

    LAYOUTS: tuple[LayoutType, ...] = ("single", "double", "multi")
    FORMATS = ("pdf", "docx", "scanned_pdf", "txt")

    def __init__(
        self,
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
    ) -> None:
        self.input_dir = Path(input_dir or os.getenv("INPUT_DIR", "input"))
        self.output_dir = Path(output_dir or os.getenv("OUTPUT_DIR", "output"))

    # ------------------------------------------------------------------
    def transform_text(
        self,
        text: str,
        stem: str = "document",
        formats: list[str] | None = None,
        layouts: list[LayoutType] | None = None,
    ) -> dict[str, Path]:
        """
        Generate documents from raw text.

        Returns a dict mapping ``<stem>_<layout>.<ext>`` keys to output Paths.
        """
        formats = formats or list(self.FORMATS)
        layouts = layouts or list(self.LAYOUTS)
        results: dict[str, Path] = {}

        for layout in layouts:
            for fmt in formats:
                key, path = self._generate_one(text, stem, fmt, layout)
                results[key] = path

        return results

    # ------------------------------------------------------------------
    def transform_file(
        self,
        input_path: str | Path,
        formats: list[str] | None = None,
        layouts: list[LayoutType] | None = None,
    ) -> dict[str, Path]:
        """Read a .txt file from disk and generate all variants."""
        input_path = Path(input_path)
        text = input_path.read_text(encoding="utf-8")
        return self.transform_text(
            text=text,
            stem=input_path.stem,
            formats=formats,
            layouts=layouts,
        )

    # ------------------------------------------------------------------
    def transform_all(
        self,
        formats: list[str] | None = None,
        layouts: list[LayoutType] | None = None,
    ) -> dict[str, Path]:
        """Process every *.txt file found in input_dir."""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        results: dict[str, Path] = {}
        txt_files = sorted(self.input_dir.glob("*.txt"))
        if not txt_files:
            raise FileNotFoundError(
                f"No *.txt files found in input directory: {self.input_dir}"
            )
        for f in txt_files:
            results.update(self.transform_file(f, formats=formats, layouts=layouts))
        return results

    # ------------------------------------------------------------------
    def _generate_one(
        self,
        text: str,
        stem: str,
        fmt: str,
        layout: LayoutType,
    ) -> tuple[str, Path]:
        title = stem.replace("_", " ").replace("-", " ").title()

        if fmt == "pdf":
            suffix = f"{stem}_{layout}.pdf"
            out_path = self.output_dir / "pdf" / layout / suffix
            generate_pdf(text, out_path, layout=layout, title=title)

        elif fmt == "docx":
            suffix = f"{stem}_{layout}.docx"
            out_path = self.output_dir / "docx" / layout / suffix
            generate_docx(text, out_path, layout=layout, title=title)

        elif fmt == "scanned_pdf":
            suffix = f"{stem}_{layout}_scanned.pdf"
            out_path = self.output_dir / "scanned_pdf" / layout / suffix
            generate_scanned_pdf(text, out_path, layout=layout, title=title)

        elif fmt == "txt":
            suffix = f"{stem}_{layout}.txt"
            out_path = self.output_dir / "txt" / layout / suffix
            generate_txt(text, out_path, layout=layout, title=title)

        else:
            raise ValueError(f"Unknown format: {fmt!r}")

        return suffix, out_path
