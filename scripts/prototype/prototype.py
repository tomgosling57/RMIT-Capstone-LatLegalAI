"""
LatMatrix - Legal Document Summarizer (Limited Prototype)
P000686CSITCP

================================================================================
DESIGN CHOICES
================================================================================

1. PDF PARSING — pdfplumber (not OCR)
   pdfplumber reads the PDF's internal text layer directly.  This works for any
   digitally-created document (Word exports, e-signed contracts, court filings).
   OCR was excluded because it adds heavy dependencies, is slower, and introduces
   character errors that corrupt downstream NLP.  See LIMITATIONS for the
   scanned-document case.

2. NLP — spaCy sentence segmentation + keyword classification
   spaCy's en_core_web_sm handles sentence boundary detection.  Legal text is
   difficult to split on newlines alone because a single clause can span many
   lines.  Clause classification (obligation / permission / risk) uses keyword
   sets rather than a trained model — this is transparent, easy to extend, and
   works well on standard legal boilerplate.  The upgrade path is a fine-tuned
   spaCy or BERT classifier trained on labelled legal sentences.

3. LLM LAYER — modular abstract backend
   LLMBackend is an abstract base class with a single complete(prompt) method.
   Switching provider requires only changing the LLM_BACKEND environment
   variable (openai | anthropic | ollama | mock).  No chunking or map-reduce
   is used — the full extracted text is sent in one prompt.  This is appropriate
   for a limited prototype where documents are expected to be reasonably sized.

================================================================================
KNOWN LIMITATIONS
================================================================================

A. SCANNED PDFs — pdfplumber returns empty text for image-based PDFs.  An OCR
   pre-processing step (pytesseract or a cloud service) would be needed to
   support scanned documents.

B. DOCUMENT LENGTH — sending the full text in a single LLM prompt will fail or
   degrade for very long documents (typically >50 pages depending on the model's
   context window).  A chunking strategy would be needed for production.

C. CLAUSE CLASSIFIER ACCURACY — the keyword heuristic misses unusual phrasing
   (e.g. "the Licensee undertakes to...") and can misclassify.  A trained model
   would improve accuracy significantly.

D. NO TRANSLATION — translation is excluded from this prototype to keep the
   scope minimal.

E. NO PERSISTENCE — results are printed to stdout only.  A database layer would
   be needed for any real deployment.

================================================================================
USAGE
================================================================================

  # Run with the mock backend (no API key needed):
  python latmatrix_prototype.py contract.pdf

  # Run with a real LLM:
  LLM_BACKEND=openai OPENAI_API_KEY=sk-... python latmatrix_prototype.py contract.pdf
  LLM_BACKEND=anthropic ANTHROPIC_API_KEY=... python latmatrix_prototype.py contract.pdf
  LLM_BACKEND=ollama OLLAMA_MODEL=llama3 python latmatrix_prototype.py contract.pdf

================================================================================
DEPENDENCIES
================================================================================

  pip install pdfplumber spacy
  python -m spacy download en_core_web_sm

  # For OpenAI backend:    pip install openai
  # For Anthropic backend: pip install anthropic
  # For Ollama backend:    (no extra install — uses stdlib requests)
"""

from __future__ import annotations

import os
import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path

import pdfplumber
import spacy
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# 1. PDF EXTRACTION
# ---------------------------------------------------------------------------


def extract_pdf(path: str | Path) -> str:
    """
    Extract plain text from a digital-native PDF using pdfplumber.
    Raises ValueError if no text layer is found (e.g. scanned document).
    """
    text_parts: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    if not text_parts:
        raise ValueError(
            "No text could be extracted from this PDF.  "
            "It may be a scanned document — OCR support is outside the scope "
            "of this prototype."
        )

    return "\n".join(text_parts)


# ---------------------------------------------------------------------------
# 2. TEXT CLEANING
# ---------------------------------------------------------------------------


def clean_text(raw: str) -> str:
    """Remove PDF artefacts and normalise whitespace."""
    text = re.sub(r"\n{3,}", "\n\n", raw)  # collapse excess blank lines
    text = re.sub(r"[ \t]{2,}", " ", text)  # collapse spaces/tabs
    text = re.sub(r"(?<=[a-z])-\n(?=[a-z])", "", text)  # rejoin hyphenated line-breaks
    return text.strip()


# ---------------------------------------------------------------------------
# 3. NLP — CLAUSE EXTRACTION (spaCy)
# ---------------------------------------------------------------------------

# Keyword sets for heuristic clause classification.
# These cover the most common legal formulations; extend as needed.
_OBLIGATION_KEYWORDS = {
    "shall",
    "must",
    "required",
    "obligated",
    "obliged",
    "agrees to",
    "agree to",
    "undertakes",
    "undertake",
    "responsible for",
    "liable to",
}
_PERMISSION_KEYWORDS = {
    "may",
    "can",
    "permitted",
    "entitled",
    "allowed",
    "has the right",
    "have the right",
    "authorised",
    "authorized",
}
_RISK_KEYWORDS = {
    "penalty",
    "penalt",
    "liable",
    "liabilit",
    "terminat",
    "breach",
    "violat",
    "forfeit",
    "restrict",
    "prohibit",
    "indemnif",
    "damages",
    "fine",
    "sanction",
    "limitation of liability",
    "warrant",
    "default",
    "consequences",
    "failure to",
}

_nlp: spacy.language.Language | None = None


def _get_nlp() -> spacy.language.Language:
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def _classify(sentence: str) -> str | None:
    """Return 'obligation', 'permission', 'risk', or None."""
    lower = sentence.lower()
    # Risk is checked first — penalty clauses often also contain obligation verbs
    if any(kw in lower for kw in _RISK_KEYWORDS):
        return "risk"
    if any(kw in lower for kw in _OBLIGATION_KEYWORDS):
        return "obligation"
    if any(kw in lower for kw in _PERMISSION_KEYWORDS):
        return "permission"
    return None


def extract_clauses(text: str) -> dict[str, list[str]]:
    """
    Use spaCy sentence segmentation to find obligations, permissions, and risks.
    Returns a dict with up to 10 entries per category.
    """
    nlp = _get_nlp()
    # Cap input to 100k chars to keep spaCy fast on very long documents
    doc = nlp(text[:100_000])

    results: dict[str, list[str]] = {
        "obligations": [],
        "permissions": [],
        "risks": [],
    }
    category_map = {
        "obligation": "obligations",
        "permission": "permissions",
        "risk": "risks",
    }

    seen: set[str] = set()
    for sent in doc.sents:
        label = _classify(sent.text)
        if not label:
            continue
        clean = sent.text.strip()
        # Filter out very short noise and duplicate sentences
        if len(clean) < 15 or clean in seen:
            continue
        seen.add(clean)
        bucket = category_map[label]
        if len(results[bucket]) < 10:
            results[bucket].append(clean)

    return results


# ---------------------------------------------------------------------------
# 4. LLM LAYER — modular backend
# ---------------------------------------------------------------------------


class LLMBackend(ABC):
    """
    Abstract base class for LLM providers.
    Subclass this and implement complete(prompt) to add a new backend.
    """

    @abstractmethod
    def complete(self, prompt: str) -> str: ...

    def summarise(self, text: str) -> str:
        """Generate a plain-English summary of the provided legal text."""
        prompt = (
            "You are a plain-language legal summariser.\n"
            "Read the following legal document text and write a short, clear summary "
            "in plain English that anyone can understand — no legal jargon.\n"
            "Use short paragraphs and simple vocabulary.\n\n"
            f"DOCUMENT TEXT:\n{text}\n\n"
            "PLAIN-ENGLISH SUMMARY:"
        )
        return self.complete(prompt)


class OpenAIBackend(LLMBackend):
    """OpenAI backend.  Requires: pip install openai  |  OPENAI_API_KEY env var."""

    def __init__(self, model: str = "gpt-4o-mini"):
        from openai import OpenAI  # type: ignore

        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model

    def complete(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()


class AnthropicBackend(LLMBackend):
    """Anthropic backend.
    Requires: pip install anthropic  |  ANTHROPIC_API_KEY env var."""

    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        import anthropic  # type: ignore

        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model

    def complete(self, prompt: str) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()


class OllamaBackend(LLMBackend):
    """
    Local inference via Ollama (https://ollama.com).
    Requires Ollama running locally.  Set OLLAMA_MODEL env var (default: llama3).
    """

    def __init__(
        self, model: str | None = None, base_url: str = "http://localhost:11434"
    ):
        import requests as _requests  # type: ignore

        self._requests = _requests
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3")
        self.base_url = base_url

    def complete(self, prompt: str) -> str:
        response = self._requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"].strip()


class MockBackend(LLMBackend):
    """
    No-API fallback for testing.  Returns a placeholder so the pipeline can
    run end-to-end without any credentials.
    """

    def complete(self, prompt: str) -> str:
        return (
            "[MOCK SUMMARY] This is a placeholder — no real LLM was called.\n"
            "Set LLM_BACKEND=openai|anthropic|ollama and provide the appropriate\n"
            "API key or server to get a real summary."
        )


def get_llm_backend() -> LLMBackend:
    """
    Factory: reads LLM_BACKEND env var and returns the matching backend instance.
    Defaults to MockBackend if the variable is not set.
    """
    name = os.environ.get("LLM_BACKEND", "mock").lower()
    backends: dict[str, type[LLMBackend]] = {
        "openai": OpenAIBackend,
        "anthropic": AnthropicBackend,
        "ollama": OllamaBackend,
        "mock": MockBackend,
    }
    if name not in backends:
        raise ValueError(
            f"Unknown LLM_BACKEND '{name}'. Choose from: {', '.join(backends)}"
        )
    return backends[name]()


# ---------------------------------------------------------------------------
# 5. PIPELINE
# ---------------------------------------------------------------------------


def analyse(pdf_path: str | Path) -> dict:
    """
    Full pipeline for a single PDF:
      extract → clean → NLP clause extraction → LLM summary

    Returns a structured dict with the summary and extracted clauses.
    """
    print("Extracting raw data from PDF...")
    raw = extract_pdf(pdf_path)

    print("Cleaning extracted text...")
    text = clean_text(raw)

    print("Extracting clauses from text...")
    clauses = extract_clauses(text)

    print("Getting LLM backend...")
    llm = get_llm_backend()

    print("Summarising text using LLM...")
    summary = llm.summarise(text)

    return {
        "file": str(pdf_path),
        "backend": os.environ.get("LLM_BACKEND", "mock"),
        "summary": summary,
        "obligations": clauses["obligations"],
        "permissions": clauses["permissions"],
        "risks": clauses["risks"],
        "stats": {
            "char_count": len(text),
            "obligations_found": len(clauses["obligations"]),
            "permissions_found": len(clauses["permissions"]),
            "risks_found": len(clauses["risks"]),
        },
    }


# ---------------------------------------------------------------------------
# 6. OUTPUT — MARKDOWN FILE + STDOUT
# ---------------------------------------------------------------------------


def _build_markdown(result: dict) -> str:
    """Render the analysis result as a markdown string."""
    from datetime import datetime

    pdf_name = Path(result["file"]).name
    s = result["stats"]

    lines: list[str] = [
        "# LatMatrix — Legal Document Analysis",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **File** | `{pdf_name}` |",
        f"| **LLM backend** | `{result['backend']}` |",
        f"| **Generated** | {datetime.now().strftime('%Y-%m-%d %H:%M')} |",
        f"| **Document size** | {s['char_count']:,} characters |",
        "",
        "---",
        "",
        "## 📄 Plain-English Summary",
        "",
        result["summary"],
        "",
        "---",
        "",
    ]

    sections = [
        (
            "## 📌 Responsibilities",
            "obligations",
            "What someone must do under this document.",
        ),
        (
            "## ✅ Permissions",
            "permissions",
            "What someone is allowed to do under this document.",
        ),
        (
            "## ⚠️ Risks & Warnings",
            "risks",
            "Penalties, limitations, and things to watch out for.",
        ),
    ]

    for heading, key, description in sections:
        items = result[key]
        lines += [
            f"{heading}  _{len(items)} found_",
            "",
            f"_{description}_",
            "",
        ]
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("_None identified._")
        lines += ["", "---", ""]

    return "\n".join(lines)


def _write_markdown(result: dict, pdf_path: Path) -> Path:
    """Write the markdown report alongside the source PDF and return its path."""
    out_path = pdf_path.with_suffix(".md")
    out_path.write_text(_build_markdown(result), encoding="utf-8")
    return out_path


def _print_results(result: dict) -> None:
    """Print a summary of results to stdout."""
    sep = "=" * 72

    print(f"\n{sep}")
    print(f"  LatMatrix — {result['file']}  [backend: {result['backend']}]")
    print(sep)

    print("\n📄  PLAIN-ENGLISH SUMMARY")
    print("-" * 72)
    print(result["summary"])

    for label, key, icon in [
        ("RESPONSIBILITIES (what someone must do)", "obligations", "📌"),
        ("PERMISSIONS (what someone can do)", "permissions", "✅"),
        ("RISKS & WARNINGS", "risks", "⚠️ "),
    ]:
        items = result[key]
        print(f"\n{icon}  {label}  ({len(items)} found)")
        print("-" * 72)
        if items:
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item}")
        else:
            print("  None identified.")

    s = result["stats"]
    print(f"\n{sep}")
    print(
        f"  Stats: {s['char_count']:,} chars | "
        f"{s['obligations_found']} obligations | "
        f"{s['permissions_found']} permissions | "
        f"{s['risks_found']} risks"
    )
    print(sep + "\n")


# ---------------------------------------------------------------------------
# 7. CLI ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python prototype.py <path/to/document.pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: file not found — {pdf_path}")
        sys.exit(1)

    result = analyse(pdf_path)
    _print_results(result)

    md_path = _write_markdown(result, pdf_path)
    print(f"✅  Markdown report saved to: {md_path}\n")
