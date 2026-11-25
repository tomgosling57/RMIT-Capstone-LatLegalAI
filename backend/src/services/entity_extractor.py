"""
Entity Extraction Service for Legal Documents.
Extracts key entities like Names (Parties), Dates, and Locations using spaCy NER.
Includes domain-specific filtering for legal documents.
Supports both synchronous and asynchronous processing with confidence scoring.
"""

from typing import Dict, List, Any, Set, Tuple
import spacy
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from config import SPACY_MAX_LENGTH

logger = logging.getLogger(__name__)


class EntityExtractorService:
    """
    Service for extracting named entities from legal documents.

    Focuses on:
    1. Parties/Organizations (PERSON, ORG)
    2. Dates (DATE)
    3. Locations (GPE, LOC)

    Includes legal document-specific filtering to reduce false positives.
    """

    # Legal document boilerplate words that are not actual parties
    LEGAL_BOILERPLATE_KEYWORDS = {
        "agreement",
        "contract",
        "employer",
        "employee",
        "buyer",
        "seller",
        "lessor",
        "lessee",
        "landlord",
        "tenant",
        "party",
        "parties",
        "dated",
        "date",
        "effective",
        "commencement",
        "termination",
        "duties",
        "obligations",
        "rights",
        "subject",
        "matter",
        "instrument",
        "clause",
        "section",
        "schedule",
        "appendix",
        "remuneration",
        "notice",
        "provision",
        "term",
        "condition",
        "this contract",
        "the agreement",
        "the parties",
        "the employer",
        "the employee",
        "herein",
        "thereof",
        "thereafter",
        "hereof",
    }

    # Generic terms that are often misidentified as entities
    GENERIC_TERMS = {
        "it",
        "the",
        "a",
        "an",
        "this",
        "that",
        "which",
        "who",
        "what",
        "where",
        "when",
        "why",
        "how",
        "person",
        "people",
        "thing",
        "things",
        "one",
        "two",
        "three",
        "day",
        "year",
        "time",
        "place",
    }

    # Common roles and titles that shouldn't be locations
    COMMON_ROLES = {
        "employer",
        "employee",
        "buyer",
        "seller",
        "lessor",
        "lessee",
        "landlord",
        "tenant",
        "party",
        "parties",
        "client",
        "vendor",
        "contractor",
        "consultant",
        "agent",
        "representative",
        "owner",
        "director",
        "manager",
        "officer",
        "partner",
    }

    # Common abbreviations and short words to filter
    SHORT_ENTITY_THRESHOLD = 3

    # Common date patterns that should be filtered
    TIME_PERIOD_KEYWORDS = {
        "year",
        "years",
        "month",
        "months",
        "week",
        "weeks",
        "day",
        "days",
        "annual",
        "annually",
        "biweekly",
        "weekly",
        "daily",
        "per annum",
    }

    def __init__(self, max_workers: int = 2) -> None:
        """
        Initialize the entity extractor service.

        Args:
            max_workers: Number of threads for async processing
        """
        self._nlp_model = None  # Will be loaded lazily
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._min_confidence = 0.6  # Minimum confidence threshold for entities

    def _load_nlp_model(self) -> None:
        """Lazy load the spaCy NLP model."""
        if self._nlp_model is not None:
            return

        try:
            self._nlp_model = spacy.load("en_core_web_sm")
            # Set the max_length from configuration to allow processing larger documents
            self._nlp_model.max_length = SPACY_MAX_LENGTH
        except Exception as e:
            raise RuntimeError(f"Failed to load spaCy model: {e}")

    def _is_boilerplate(self, text: str) -> bool:
        """
        Check if entity text is likely boilerplate legal language.

        Args:
            text: Entity text to check

        Returns:
            True if text appears to be boilerplate
        """
        text_lower = text.lower().strip()

        # Check if entire text or significant portion is boilerplate
        words = text_lower.split()
        boilerplate_count = sum(
            1 for word in words if word in self.LEGAL_BOILERPLATE_KEYWORDS
        )

        if len(words) > 0 and boilerplate_count / len(words) > 0.5:
            return True

        # Check for exact boilerplate matches
        if text_lower in self.LEGAL_BOILERPLATE_KEYWORDS:
            return True

        return False

    def _is_valid_party_name(
        self, text: str, confidence: float = 0.7
    ) -> Tuple[bool, float]:
        """
        Check if text is likely a valid party name with confidence scoring.

        Args:
            text: Entity text to check
            confidence: Starting confidence score

        Returns:
            Tuple of (is_valid, confidence_score)
        """
        text_lower = text.lower().strip()

        # Filter generic terms
        if text_lower in self.GENERIC_TERMS:
            return False, 0.0

        # Filter boilerplate
        if self._is_boilerplate(text):
            return False, 0.0

        # Check minimum length
        if len(text) < 2:
            return False, 0.0

        # Check for numbers (usually false positives)
        digit_ratio = sum(1 for c in text if c.isdigit()) / len(text)
        if digit_ratio > 0.3:
            confidence -= 0.2

        # Proper names should have capital letters or contain company suffixes
        has_capital = any(c.isupper() for c in text)
        has_company_suffix = any(
            suffix in text_lower
            for suffix in [
                "corp",
                "inc",
                "ltd",
                "llc",
                "company",
                "co.",
                "pty",
                "ltd.",
                "inc.",
                "limited",
            ]
        )

        # Multi-word entities are more likely to be valid party names
        word_count = len(text.split())
        if word_count == 1:
            # Single word: must have capital or company suffix
            if has_capital or has_company_suffix:
                confidence = 0.8 if has_company_suffix else 0.65
            else:
                return False, 0.0
        elif word_count >= 2:
            # Multi-word: higher confidence
            if has_capital:
                confidence = 0.85
            elif has_company_suffix:
                confidence = 0.8
            else:
                # Multi-word without capitals is suspicious
                confidence = 0.5

        # Check if text contains "and" which often indicates party joining
        # (lower confidence)
        if " and " in text_lower:
            confidence -= 0.15

        # Ensure minimum confidence threshold
        if confidence < self._min_confidence:
            return False, confidence

        return True, confidence

    def _is_valid_date(self, text: str) -> Tuple[bool, float]:
        """
        Check if text is likely a valid date
        (not just a time period) with confidence scoring.

        Args:
            text: Date entity text to check

        Returns:
            Tuple of (is_valid, confidence_score)
        """
        text_lower = text.lower()

        # Filter out pure time periods
        if text_lower in self.TIME_PERIOD_KEYWORDS:
            return False, 0.0

        confidence = 0.5

        # Should contain month name, day number, or year
        months = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
            "jan",
            "feb",
            "mar",
            "apr",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
        ]
        has_month = any(month in text_lower for month in months)
        has_day = any(char.isdigit() for char in text)
        has_year = any(year in text for year in [str(y) for y in range(1900, 2100)])

        # Calculate confidence based on date components
        if has_month and has_day:
            confidence = 0.95  # Month + day is very reliable
        elif has_year and re.search(r"\d{4}", text):
            confidence = 0.85  # 4-digit year is reliable
        elif has_month and has_year:
            confidence = 0.90  # Month + year is reliable
        elif has_day or has_year:
            confidence = 0.70  # Just day or year is less certain
        else:
            return False, 0.0

        # Filter out dates that are just numbers without context
        if not has_month and re.match(r"^\d+$", text):
            confidence = 0.3

        # Ensure minimum confidence threshold
        if confidence < self._min_confidence:
            return False, confidence

        return True, confidence

    def _extract_parties_from_context(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract parties using pattern matching (e.g., "between X and Y").

        Args:
            text: Full document text

        Returns:
            List of party dicts with text, type, and confidence
        """
        parties = []

        # Pattern: "between [PARTY] and [PARTY]"
        between_pattern = r"between\s+([A-Z][^,\n]+?)\s+and\s+([A-Z][^,\n.]+)"
        matches = re.finditer(between_pattern, text, re.IGNORECASE)
        for match in matches:
            party1 = match.group(1).strip()
            party2 = match.group(2).strip()

            is_valid1, conf1 = self._is_valid_party_name(party1, confidence=0.9)
            if is_valid1:
                parties.append(
                    {
                        "text": party1,
                        "type": "PERSON_OR_ORG",
                        "confidence": conf1,
                        "source": "pattern",
                    }
                )

            is_valid2, conf2 = self._is_valid_party_name(party2, confidence=0.9)
            if is_valid2:
                parties.append(
                    {
                        "text": party2,
                        "type": "PERSON_OR_ORG",
                        "confidence": conf2,
                        "source": "pattern",
                    }
                )

        # Pattern: "by and between [PARTY] and [PARTY]"
        by_between_pattern = r"by and between\s+([A-Z][^,\n]+?)\s+and\s+([A-Z][^,\n.]+)"
        matches = re.finditer(by_between_pattern, text, re.IGNORECASE)
        for match in matches:
            party1 = match.group(1).strip()
            party2 = match.group(2).strip()

            is_valid1, conf1 = self._is_valid_party_name(party1, confidence=0.95)
            if is_valid1:
                parties.append(
                    {
                        "text": party1,
                        "type": "PERSON_OR_ORG",
                        "confidence": conf1,
                        "source": "pattern",
                    }
                )

            is_valid2, conf2 = self._is_valid_party_name(party2, confidence=0.95)
            if is_valid2:
                parties.append(
                    {
                        "text": party2,
                        "type": "PERSON_OR_ORG",
                        "confidence": conf2,
                        "source": "pattern",
                    }
                )

        return parties

    def extract_entities(
        self, text: str, min_confidence: float = None
    ) -> Dict[str, Any]:
        """
        Extract named entities from legal text with domain-specific filtering.

        Args:
            text: Legal text to analyze
            min_confidence: Override minimum confidence threshold
            (default: self._min_confidence)

        Returns:
            Dictionary with extracted entities:
            names: List of person and organization names with confidence scores
            dates: List of dates found in document with confidence scores
            locations: List of locations (GPE and LOC) with confidence scores
            all_entities: Complete list of all entities with their labels and confidence
        """
        self._load_nlp_model()
        doc = self._nlp_model(text)

        if min_confidence is None:
            min_confidence = self._min_confidence

        entities = {"names": [], "dates": [], "locations": [], "all_entities": []}
        seen_entities: Set[str] = set()

        # First, try to extract parties using context patterns (higher confidence)
        context_parties = self._extract_parties_from_context(text)
        for party_data in context_parties:
            party_text = party_data["text"]
            if (
                party_text not in seen_entities
                and party_data["confidence"] >= min_confidence
            ):
                entities["names"].append(party_data)
                seen_entities.add(party_text)

        # Then process spaCy NER results with filtering
        for ent in doc.ents:
            entity_text = ent.text.strip()
            label = ent.label_

            # Categorize by type with filtering
            if label in ["PERSON", "ORG"]:
                # Extract parties/names with validation and confidence
                if entity_text not in seen_entities:
                    is_valid, confidence = self._is_valid_party_name(entity_text)
                    if is_valid and confidence >= min_confidence:
                        entities["names"].append(
                            {
                                "text": entity_text,
                                "type": label,
                                "confidence": confidence,
                                "source": "spacy",
                            }
                        )
                        seen_entities.add(entity_text)

            elif label == "DATE":
                # Extract dates with validation and confidence
                if entity_text not in seen_entities:
                    is_valid, confidence = self._is_valid_date(entity_text)
                    if is_valid and confidence >= min_confidence:
                        entities["dates"].append(
                            {
                                "text": entity_text,
                                "confidence": confidence,
                                "source": "spacy",
                            }
                        )
                        seen_entities.add(entity_text)

            elif label in ["GPE", "LOC"]:
                # Extract locations with validation
                if entity_text not in seen_entities and len(entity_text) > 2:
                    # Filter out common roles misidentified as locations
                    if entity_text.lower() not in self.COMMON_ROLES:
                        # Calculate confidence for locations
                        location_confidence = 0.75 if label == "GPE" else 0.70
                        if location_confidence >= min_confidence:
                            entities["locations"].append(
                                {
                                    "text": entity_text,
                                    "type": label,
                                    "confidence": location_confidence,
                                    "source": "spacy",
                                }
                            )
                            seen_entities.add(entity_text)

            # Store all entities with their labels
            entities["all_entities"].append(
                {
                    "text": entity_text,
                    "label": label,
                    "start": ent.start_char,
                    "end": ent.end_char,
                }
            )

        return entities

    async def extract_entities_async(
        self, text: str, min_confidence: float = None
    ) -> Dict[str, Any]:
        """
        Asynchronously extract named entities from legal text.
        Uses ThreadPoolExecutor to avoid blocking the event loop.

        Args:
            text: Legal text to analyze
            min_confidence: Override minimum confidence threshold

        Returns:
            Dictionary with extracted entities (same structure as extract_entities)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self.extract_entities, text, min_confidence
        )

    def is_available(self) -> bool:
        """
        Check if the entity extraction service is properly configured.

        Returns:
            True if spaCy model can be loaded
        """
        try:
            spacy.load("en_core_web_sm")
            return True
        except Exception:
            return False
