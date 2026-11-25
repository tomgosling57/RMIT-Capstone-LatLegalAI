"""
Tests for the Entity Extractor Service.
Tests extraction of Names (Parties), Dates, and Locations from legal documents.

Migrated from backend/src/tests/services/test_entity_extractor.py to work with
chainlit/src/tools/entity_extractor.py
"""

import pytest
from src.tools.entity_extractor import EntityExtractorService


@pytest.fixture
def entity_extractor():
    """Create an entity extractor instance for testing."""
    return EntityExtractorService()


def test_entity_extractor_initialization(entity_extractor):
    """Test that entity extractor initializes correctly."""
    assert entity_extractor is not None
    assert entity_extractor.is_available()


def test_extract_names_from_legal_text(entity_extractor):
    """Test extraction of names (parties) from legal text."""
    text = """
    This Agreement is entered into between John Smith and ABC Corporation.
    John Smith is referred to as the "Buyer"
    and ABC Corporation is referred to as the "Seller".
    """

    result = entity_extractor.extract_entities(text)

    assert "names" in result
    assert len(result["names"]) > 0

    names_text = [name["text"] for name in result["names"]]
    assert any("John Smith" in name or "john" in name.lower() for name in names_text)
    assert any("ABC Corporation" in name or "ABC" in name for name in names_text)


def test_extract_dates_from_legal_text(entity_extractor):
    """Test extraction of dates from legal text."""
    text = """
    This Agreement is effective as of January 15, 2024.
    The contract will expire on December 31, 2025.
    Payment is due by March 20, 2024.
    """

    result = entity_extractor.extract_entities(text)

    assert "dates" in result
    assert len(result["dates"]) > 0

    dates_text = [date["text"] for date in result["dates"]]
    assert any("2024" in date or "2025" in date for date in dates_text)


def test_extract_locations_from_legal_text(entity_extractor):
    """Test extraction of locations from legal text."""
    text = """
    This Agreement shall be governed by the laws of New York.
    The principal office is located in San Francisco, California.
    Disputes shall be resolved in London, England.
    """

    result = entity_extractor.extract_entities(text)

    assert "locations" in result
    assert isinstance(result["locations"], list)


def test_extract_all_entities(entity_extractor):
    """Test extraction of all entity types from comprehensive legal text."""
    text = """
    EMPLOYMENT AGREEMENT
    This Agreement is made and entered into as of January 1, 2024,
    between Microsoft Corporation, a company incorporated in Washington,
    and John Johnson, an individual residing in Seattle, Washington.
    The employment shall commence on February 15, 2024 and shall continue
    until December 31, 2025, unless earlier terminated.
    The Employee agrees to work at the Company's offices in New York City
    and occasionally in San Francisco.
    """

    result = entity_extractor.extract_entities(text)

    assert "names" in result
    assert "dates" in result
    assert "locations" in result
    assert "all_entities" in result

    assert isinstance(result["all_entities"], list)
    assert isinstance(result["names"], list)
    assert isinstance(result["dates"], list)
    assert isinstance(result["locations"], list)


def test_entity_extractor_empty_text(entity_extractor):
    """Test entity extractor with empty text."""
    text = ""
    result = entity_extractor.extract_entities(text)

    assert result["names"] == []
    assert result["dates"] == []
    assert result["locations"] == []
    assert result["all_entities"] == []


def test_entity_extractor_no_entities(entity_extractor):
    """Test entity extractor with text containing no entities."""
    text = "This is a simple document about nothing in particular."
    result = entity_extractor.extract_entities(text)

    assert "names" in result
    assert "dates" in result
    assert "locations" in result


def test_entity_extractor_duplicate_handling(entity_extractor):
    """Test that entity extractor deduplicates repeated entities."""
    text = """
    John Smith signed the agreement.
    John Smith also agreed to the terms.
    John Smith shall perform the duties.
    """

    result = entity_extractor.extract_entities(text)

    names_text = [name["text"] for name in result["names"]]
    john_count = sum(1 for name in names_text if "John" in name)
    assert john_count <= 1


def test_entity_types_in_extraction(entity_extractor):
    """Test that extracted entities have proper structure."""
    text = "John Doe and Acme Inc. met on January 15, 2024 in New York."
    result = entity_extractor.extract_entities(text)

    for name in result["names"]:
        assert "text" in name
        assert "type" in name
        assert name["type"] in ["PERSON", "ORG", "PERSON_OR_ORG"]

    for date in result["dates"]:
        assert "text" in date

    for location in result["locations"]:
        assert "text" in location
        assert "type" in location
        assert location["type"] in ["GPE", "LOC"]

    for entity in result["all_entities"]:
        assert "text" in entity
        assert "label" in entity
        assert "start" in entity
        assert "end" in entity


def test_entity_extractor_confidence_scores(entity_extractor):
    """Test that extracted entities include confidence scores."""
    text = "John Smith and ABC Corporation signed on January 15, 2024."
    result = entity_extractor.extract_entities(text)

    for name in result["names"]:
        assert "confidence" in name
        assert 0.0 <= name["confidence"] <= 1.0

    for date in result["dates"]:
        assert "confidence" in date
        assert 0.0 <= date["confidence"] <= 1.0

    for location in result["locations"]:
        assert "confidence" in location
        assert 0.0 <= location["confidence"] <= 1.0


def test_entity_extractor_min_confidence_filter(entity_extractor):
    """Test that min_confidence parameter filters results."""
    text = "John Smith and ABC Corporation signed on January 15, 2024."

    result_low = entity_extractor.extract_entities(text, min_confidence=0.3)
    result_high = entity_extractor.extract_entities(text, min_confidence=0.9)

    assert len(result_low["names"]) >= len(result_high["names"])
    assert len(result_low["dates"]) >= len(result_high["dates"])


def test_extract_parties_from_between_pattern(entity_extractor):
    """Test extraction of parties using 'between X and Y' pattern."""
    text = "This agreement is between John Smith and ABC Corporation."
    result = entity_extractor.extract_entities(text)

    assert len(result["names"]) > 0
    names_text = [name["text"] for name in result["names"]]
    assert any("John Smith" in name or "john" in name.lower() for name in names_text)


def test_extract_parties_from_by_and_between_pattern(entity_extractor):
    """Test extraction of parties using 'by and between X and Y' pattern."""
    text = "This agreement is made by and between John Smith and ABC Corporation."
    result = entity_extractor.extract_entities(text)

    assert len(result["names"]) > 0


def test_entity_extractor_boilerplate_filtering(entity_extractor):
    """Test that boilerplate legal terms are filtered out."""
    text = "This agreement between the parties is effective."
    result = entity_extractor.extract_entities(text)

    names_text = [name["text"].lower() for name in result["names"]]
    assert "the parties" not in names_text
    assert "agreement" not in names_text


def test_entity_extractor_generic_terms_filtering(entity_extractor):
    """Test that generic terms are filtered out."""
    text = "The person and the company met."
    result = entity_extractor.extract_entities(text)

    names_text = [name["text"].lower() for name in result["names"]]
    assert "the" not in names_text
    assert "person" not in names_text


def test_entity_extractor_date_validation(entity_extractor):
    """Test that dates are properly validated."""
    text = "The contract is effective January 15, 2024 and expires December 31, 2025."
    result = entity_extractor.extract_entities(text)

    assert "dates" in result
    for date in result["dates"]:
        assert "text" in date
        assert "confidence" in date


def test_entity_extractor_location_confidence(entity_extractor):
    """Test that locations have appropriate confidence scores."""
    text = "The agreement is governed by New York law."
    result = entity_extractor.extract_entities(text)

    for location in result["locations"]:
        assert "confidence" in location
        assert location["confidence"] >= 0.0


def test_entity_extractor_source_tracking(entity_extractor):
    """Test that entity sources are tracked (spacy vs pattern)."""
    text = "This agreement is between John Smith and ABC Corporation."
    result = entity_extractor.extract_entities(text)

    for name in result["names"]:
        assert "source" in name
        assert name["source"] in ["spacy", "pattern"]


def test_entity_extractor_with_company_suffixes(entity_extractor):
    """Test extraction of company names with common suffixes."""
    text = "ABC Corp., XYZ Inc., and DEF Ltd. signed the agreement."
    result = entity_extractor.extract_entities(text)

    assert len(result["names"]) > 0
    names_text = [name["text"] for name in result["names"]]
    assert any("Corp" in name or "Inc" in name or "Ltd" in name for name in names_text)


def test_entity_extractor_capitalization_handling(entity_extractor):
    """Test proper handling of capitalized names."""
    text = "John Smith, JANE DOE, and jane doe all signed."
    result = entity_extractor.extract_entities(text)

    assert len(result["names"]) > 0


def test_entity_extractor_multiword_names(entity_extractor):
    """Test extraction of multi-word entity names."""
    text = "John Michael Smith and International Business Machines Corporation agreed."
    result = entity_extractor.extract_entities(text)

    assert len(result["names"]) > 0
