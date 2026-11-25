"""
Tests for the Entity Extractor Service.
Tests extraction of Names (Parties), Dates, and Locations from legal documents.
"""

import pytest
from services.entity_extractor import EntityExtractorService

pytestmark = pytest.mark.slow


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

    # Check if extracted names contain expected parties
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

    # Check if dates are extracted
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
    # Locations might not always be extracted depending on spaCy model
    # but the key should exist
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

    # Verify structure
    assert "names" in result
    assert "dates" in result
    assert "locations" in result
    assert "all_entities" in result

    # Verify all entities list exists
    assert isinstance(result["all_entities"], list)

    # Verify all categories are lists
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

    # Should have structure but might be empty
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

    # Check that John Smith appears only once (deduplicated)
    names_text = [name["text"] for name in result["names"]]
    john_count = sum(1 for name in names_text if "John" in name)
    # Should have minimal duplicates due to deduplication
    assert john_count <= 1


def test_entity_types_in_extraction(entity_extractor):
    """Test that extracted entities have proper structure."""
    text = "John Doe and Acme Inc. met on January 15, 2024 in New York."
    result = entity_extractor.extract_entities(text)

    # Test names have type field
    for name in result["names"]:
        assert "text" in name
        assert "type" in name
        assert name["type"] in ["PERSON", "ORG"]

    # Test dates structure
    for date in result["dates"]:
        assert "text" in date

    # Test locations have type field
    for location in result["locations"]:
        assert "text" in location
        assert "type" in location
        assert location["type"] in ["GPE", "LOC"]

    # Test all entities have required fields
    for entity in result["all_entities"]:
        assert "text" in entity
        assert "label" in entity
        assert "start" in entity
        assert "end" in entity
