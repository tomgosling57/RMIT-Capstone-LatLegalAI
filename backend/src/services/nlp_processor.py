"""
Natural Language Processing (NLP) Service for Legal Documents.
Focuses on text processing, clause extraction, and named entity recognition.
"""

from typing import Dict, Any
import re
import spacy
from config import SPACY_MAX_LENGTH



class NLPService:
    """
    Service for natural language processing of legal documents.

    This class handles:
    1. Text cleaning and normalization
    2. Sentence segmentation
    3. Clause extraction (obligations, permissions, risks)
    4. Named entity recognition (when implemented)

    Does NOT perform LLM-based summarization - that's handled by the Summarizer service.
    """

    def __init__(self) -> None:
        """Initialize the NLP service."""
        self._nlp_model = None  # Will be loaded lazily

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive NLP analysis on legal text.

        Args:
            text: Legal text to analyze

        Returns:
            Dictionary with:
            - cleaned_text: Cleaned version of input text
            - clauses: Extracted obligations, permissions, and risks
            - stats: Statistics about the analysis
        """
        # This will integrate the prototype's:
        # 1. Text cleaning (clean_text)
        # 2. Clause extraction (extract_clauses)
        # 3. Statistics calculation
        return {}

    def clean_text(self, text: str) -> str:
        """
        Main entry point for legal text cleanup pipeline.
        """
        text = self._normalize_whitespace(text)
        text = self._remove_table_of_contents(text)
        text = self._remove_page_numbers(text)
        text = self.structure_legal_paragraphs(text)
        text = self.remove_before_first_clause_one(text)
        text = self._remove_dotted_leaders(text)
        text = self._fix_broken_line_breaks(text)
        text = self._remove_header_footer_noise(text)
        text = self._normalize_section_spacing(text)
        return text.strip()

    def remove_before_first_clause_one(self, text: str) -> str:
        """
        Remove all text before the first clause numbered "1".

        Matches clause numbering patterns at the start of a line:
        - "1." (period delimiter)
        - "1 " (space delimiter)
        - "1-" (dash delimiter)
        - "1" at end of line

        Avoids false positives from dates, numeric text, or "1" mid-word.

        Args:
            text: The legal document text

        Returns:
            Text starting from the first clause "1", or original text if not found
        """
        # Match "1" at start of line (after newline or at document start) followed by
        # period, space, dash, or end of line. This prevents false matches in:
        # - Dates: "January 1, 2024"
        # - Item numbering mid-text: "Item 1 says"
        # - Numeric contexts: "Page 1" in middle of paragraph
        match = re.search(r"(?:^|\n)1(?:\.|\s|-|$)", text, re.MULTILINE)

        if not match:
            return text  # No clause 1 found, return original text

        # Return text from the start of the match (which may include newline)
        # Strip only leading newline if present
        result = text[match.start() :]
        if result.startswith("\n"):
            result = result[1:]
        return result.strip()

    def _split_top_level_sections(self, text: str) -> list[str]:
        """
        Splits text into top-level sections (e.g., 1, 2, 3)
        Works even with OCR noise like:
        '1Background', '1  Background', '2. Operative Terms'
        """

        # Normalize line breaks first
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        sections = []
        current = []

        top_level = re.compile(r"^(\d{1,3})([\s\.\-]|$)")  # flexible OCR-safe match

        for line in lines:
            is_top = bool(top_level.match(line))

            if is_top:
                if current:
                    sections.append("\n".join(current))
                    current = []

            current.append(line)

        if current:
            sections.append("\n".join(current))

        return sections

    def _structure_subsections(self, section_text: str) -> str:
        """
        Ensures subsection numbers (1.1, 1.2, etc.) start on new lines
        but remain inside the same top-level section.
        """

        lines = section_text.split("\n")

        sub_pattern = re.compile(r"^\d+\.\d+")

        output = []

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            # Ensure subsections always start on a new line
            if sub_pattern.match(stripped_line):
                output.append(stripped_line)
            else:
                # attach normal text to previous line if needed
                if output:
                    output[-1] += " " + stripped_line
                else:
                    output.append(stripped_line)

        return "\n".join(output)

    def structure_legal_paragraphs(self, text: str) -> str:
        """
        Full robust pipeline:
        1. Split into top-level sections
        2. Structure subsections inside each
        """

        sections = self._split_top_level_sections(text)

        structured_sections = [self._structure_subsections(sec) for sec in sections]

        return "\n\n".join(structured_sections)

    def _normalize_whitespace(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        return text

    def _fix_broken_line_breaks(self, text: str) -> str:
        lines = text.split("\n")
        cleaned = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                cleaned.append("")
                continue

            # If line ends without punctuation and next line starts lowercase -> join
            if (
                i < len(lines) - 1
                and stripped
                and not re.search(r"[\.!?;:]$", stripped)
                and lines[i + 1].strip()
                and lines[i + 1].strip()[0].islower()
            ):
                cleaned.append(stripped + " ")
            else:
                cleaned.append(stripped)

        return "\n".join(cleaned)

    def _remove_table_of_contents(self, text: str) -> str:
        """
        Removes TOC blocks based on dotted leaders and page number patterns.
        """
        lines = text.split("\n")
        out = []

        toc_mode = False

        for line in lines:
            stripped_line = line.strip()

            # Detect TOC start
            if re.search(r"table of contents", stripped_line.lower()):
                toc_mode = True
                continue

            # Stop TOC when main content likely resumes
            if toc_mode and re.match(
                r"^(chapter|section|\d+\.|\w+)\s", stripped_line.lower()
            ):
                toc_mode = False

            if toc_mode:
                continue

            # Remove typical TOC lines anyway
            if re.search(r"\.{3,}\s*\d+$", stripped_line):
                continue

            out.append(line)

        return "\n".join(out)

    def _remove_dotted_leaders(self, text: str) -> str:
        return re.sub(r"\.{2,}", " ", text)

    def _remove_page_numbers(self, text: str) -> str:
        lines = text.split("\n")
        cleaned = []

        for line in lines:
            stripped_line = line.strip()

            # Skip pure page numbers like: "12", "  12  "
            if re.fullmatch(r"\d{1,4}", stripped_line):
                continue

            # Skip "Page 12" style footers
            if re.fullmatch(r"(?i)page\s*\d{1,4}", stripped_line):
                continue

            cleaned.append(line)

        # Rebuild while preserving paragraph spacing
        return "\n".join(cleaned)

    def _remove_header_footer_noise(self, text: str) -> str:
        # Remove emails
        text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "", text)

        # Remove phone numbers (basic patterns)
        text = re.sub(
            r"\b(?:\+?\d{1,3})?[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b", "", text
        )

        # Remove repeated ALL CAPS header-like lines
        text = re.sub(r"\n[A-Z\s]{8,}\n", "\n", text)

        return text

    def _normalize_section_spacing(self, text: str) -> str:
        """
        Ensures clean separation between sections/clauses.
        """
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def spacy_sentence_cleanup(self, text: str, nlp) -> str:
        """
        Uses spaCy to improve sentence segmentation consistency.
        """
        doc = nlp(text)

        sentences = []
        for sent in doc.sents:
            s = sent.text.strip()

            # remove junk single-character sentences
            if len(s) <= 1:
                continue

            sentences.append(s)

        return "\n".join(sentences)

    def remove_stopword_noise_lines(self, text: str, nlp) -> str:
        """
        Removes lines that are mostly stopwords (common OCR noise).
        """
        doc = nlp(text)
        cleaned = []

        for sent in doc.sents:
            tokens = [t for t in sent if not t.is_stop and not t.is_punct]

            if len(tokens) == 0:
                continue

            cleaned.append(sent.text.strip())

        return "\n".join(cleaned)

    def extract_clauses(self, text: str) -> Dict[str, list]:
        """
        Extract obligations, permissions, and risks from legal text.

        Args:
            text: Legal text to analyze

        Returns:
            Dictionary with keys:
            - 'obligations': List of obligation clauses
            - 'permissions': List of permission clauses
            - 'risks': List of risk/warning clauses
        """
        self._load_nlp_model()
        doc = self._nlp_model(text)
        results = []

        OBLIGATION_TERMS = {
            "shall",
            "must",
            "required",
            "agree",
            "obligated",
            "responsible",
            "agrees",
        }
        PERMISSION_TERMS = {"may", "can", "allowed", "permitted"}
        RISK_TERMS = {
            "liable",
            "liability",
            "terminate",
            "termination",
            "breach",
            "penalty",
            "damages",
            "risk",
            "default",
            "warranty",
        }

        for sent in doc.sents:
            text_sent = sent.text.strip()
            lower = text_sent.lower()

            # Score for ambiguity reason, instead of boolean
            obligation_score = 0
            permission_score = 0
            risk_score = 0

            # Stronger points for targets keywords
            for w in OBLIGATION_TERMS:
                if w in lower:
                    obligation_score += 2

            for w in PERMISSION_TERMS:
                if w in lower:
                    permission_score += 2

            for w in RISK_TERMS:
                if w in lower:
                    risk_score += 2

            # Smaller score for models guesses
            # Works by finding action, then determining wether permission or obligation
            for token in sent:
                if token.dep_ in {"aux", "ROOT"}:
                    if token.text.lower() in OBLIGATION_TERMS:
                        obligation_score += 1
                    if token.text.lower() in PERMISSION_TERMS:
                        permission_score += 1

            labels = {"obligation": False, "permission": False, "risk": False}

            # allow multi-label for strong risk cases
            # consider adjusting risk threshold if too low
            if risk_score >= 2:
                labels["risk"] = True

            if obligation_score > 2:
                labels["obligation"] = True

            if permission_score > 2:
                labels["permission"] = True

            results.append({"sentence": text_sent, "labels": labels})

        return results

    def _load_nlp_model(self) -> None:
        """Lazy load the spaCy NLP model."""
        # If already loaded, do nothing
        if self._nlp_model is not None:
            return

        try:
            self._nlp_model = spacy.load("en_core_web_sm")
            # Set the max_length from configuration to allow processing larger documents
            self._nlp_model.max_length = SPACY_MAX_LENGTH
        except Exception as e:
            raise RuntimeError(f"Failed to load spaCy model: {e}")

    def is_available(self) -> bool:
        """
        Check if the NLP service is properly configured.

        Returns:
            True if spaCy model can be loaded
        """
        try:
            spacy.load("en_core_web_sm")
            return True
        except Exception:
            return False
