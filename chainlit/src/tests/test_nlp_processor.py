"""
Tests for the NLP Processor Service.
Tests text cleaning, clause extraction, and NLP analysis for legal documents.

Migrated from backend/src/tests/services/test_nlp.py to work with
chainlit/src/tools/nlp_processor.py
"""

import pytest
from src.tools.nlp_processor import NLPService


@pytest.fixture
def nlp_service():
    """Create an NLP service instance for testing."""
    return NLPService()


@pytest.mark.nlp
def test_nlp_service_initialization(nlp_service):
    """Test that NLP service initializes correctly."""
    assert nlp_service is not None
    assert nlp_service.is_available()


@pytest.mark.nlp
def test_txt_cleaning(nlp_service):
    """Test text cleaning functionality."""
    raw_text = """
    TABLE OF CONTENTS
    1. Introduction ..................... 1
    2. Terms ............................ 5

    Page 1

    1. Introduction
    This is the introduction section.

    2. Terms
    These are the terms and conditions.
    """

    cleaned = nlp_service.clean_text(raw_text)

    # Should remove table of contents
    assert "TABLE OF CONTENTS" not in cleaned
    # Should remove page numbers
    assert "Page 1" not in cleaned
    # Should preserve actual content
    assert "Introduction" in cleaned
    assert "Terms" in cleaned


@pytest.mark.nlp
def test_classification_extraction(nlp_service):
    """Test clause classification and extraction."""
    text = """
    The User shall pay all fees within 30 days.
    The Company may terminate the agreement at any time.
    The User is liable for any damages caused by breach.
    """

    result = nlp_service.extract_clauses(text)

    assert len(result) > 0
    assert result[0]["labels"]["obligation"] is True
    assert result[1]["labels"]["permission"] is True
    assert result[2]["labels"]["risk"] is True


@pytest.mark.nlp
class TestRemoveBeforeFirstClauseOne:
    """Test remove_before_first_clause_one method.

    Verifies robust regex matching that avoids false positives
    from dates and numeric contexts.
    """

    @pytest.fixture
    def service(self) -> NLPService:
        """Provide NLPService instance for tests."""
        return NLPService()

    def test_standard_clause_start_with_period(self, service: NLPService) -> None:
        """Test: Standard clause numbering with period (1.)"""
        text = (
            "Preamble text here.\n\n1. This is the first clause.\n"
            "2. This is the second clause."
        )
        result = service.remove_before_first_clause_one(text)
        assert result.startswith("1. This is the first clause")
        assert "Preamble" not in result

    def test_standard_clause_start_with_space(self, service: NLPService) -> None:
        """Test: Standard clause numbering with space (1 )"""
        text = (
            "Some introductory text\n1 The parties agree to the "
            "following terms.\nMore text."
        )
        result = service.remove_before_first_clause_one(text)
        assert result.startswith("1 The parties")
        assert "introductory" not in result

    def test_standard_clause_start_with_dash(self, service: NLPService) -> None:
        """Test: Clause numbering with dash (1-)"""
        text = "Header information\n1-Overview\nContent starts here."
        result = service.remove_before_first_clause_one(text)
        assert result.startswith("1-Overview")
        assert "Header" not in result

    def test_clause_at_document_start(self, service: NLPService) -> None:
        """Test: Clause 1 at the very start of document"""
        text = "1. First clause at start.\n2. Second clause."
        result = service.remove_before_first_clause_one(text)
        assert result == text

    def test_false_positive_date_january_1(self, service: NLPService) -> None:
        """Test: Avoid matching "1" in dates like "January 1, 2024" """
        text = (
            "This contract was signed on January 1, 2024.\n\n"
            "1. Definitions\nClause content."
        )
        result = service.remove_before_first_clause_one(text)
        assert result.startswith("1. Definitions")
        assert "January" not in result
        assert "signed on" not in result

    def test_false_positive_date_format(self, service: NLPService) -> None:
        """Test: Avoid matching "1" in various date formats"""
        text = (
            "Effective Date: 1 January 2024\n\n1. Parties\nThis agreement is between..."
        )
        result = service.remove_before_first_clause_one(text)
        assert result.startswith("1. Parties")
        assert "Effective Date" not in result
        assert "January" not in result

    def test_false_positive_item_numbering(self, service: NLPService) -> None:
        """Test: Avoid matching "1" in mid-text item numbering"""
        text = (
            "The following items apply: 1) first item, 2) second item."
            "\n\n1. Operative Clause\nDetails follow."
        )
        result = service.remove_before_first_clause_one(text)
        assert result.startswith("1. Operative Clause")
        assert "first item" not in result

    def test_no_clause_one_found(self, service: NLPService) -> None:
        """Test: Return original text when no clause 1 exists"""
        text = "2. Some clause\n3. Another clause\nNo clause 1 present."
        result = service.remove_before_first_clause_one(text)
        assert result == text

    def test_empty_text(self, service: NLPService) -> None:
        """Test: Handle empty text gracefully"""
        text = ""
        result = service.remove_before_first_clause_one(text)
        assert result == ""

    def test_whitespace_only(self, service: NLPService) -> None:
        """Test: Handle text with only whitespace"""
        text = "   \n\n  \t  "
        result = service.remove_before_first_clause_one(text)
        assert result.strip() == ""

    def test_multi_digit_clauses_not_matched(self, service: NLPService) -> None:
        """Test: Verify only "1" matches, not "10", "11", "12", etc."""
        text = "Preamble\n10. Section Ten\n1. First Clause\nContent."
        result = service.remove_before_first_clause_one(text)
        assert result.startswith("1. First Clause")
        assert "Section Ten" not in result

    def test_clause_1_with_multiple_spaces(self, service: NLPService) -> None:
        """Test: Handle clause 1 followed by multiple spaces"""
        text = "Introduction\n1   Multiple spaces after number\nContent."
        result = service.remove_before_first_clause_one(text)
        assert result.startswith("1")
        assert "Introduction" not in result

    def test_multiline_preamble(self, service: NLPService) -> None:
        """Test: Remove multi-line preamble before clause 1"""
        text = (
            "Header\nThis is a long\nmulti-line preamble\nwith many "
            "lines\n\n1. First Clause\nDetails."
        )
        result = service.remove_before_first_clause_one(text)
        assert result.startswith("1. First Clause")
        assert "Header" not in result
        assert "preamble" not in result

    def test_real_contract_pattern(self, service: NLPService) -> None:
        """Test: Real contract with typical structure"""
        text = (
            "EMPLOYMENT AGREEMENT\n"
            "This agreement is made as of January 1, 2024.\n\n"
            "1. Parties\n"
            "The Employer and Employee agree to the following terms.\n\n"
            "2. Compensation\n"
            "The Employee shall receive payment as detailed in "
            "Schedule 1."
        )
        result = service.remove_before_first_clause_one(text)
        assert result.startswith("1. Parties")
        assert "EMPLOYMENT AGREEMENT" not in result
        assert "January 1, 2024" not in result
        assert "Schedule 1" in result

    def test_preserves_content_after_clause_1(self, service: NLPService) -> None:
        """Test: Ensure all content after clause 1 is preserved"""
        text = "Preamble\n\n1. First\n\n2. Second\n\n3. Third"
        result = service.remove_before_first_clause_one(text)
        assert "2. Second" in result
        assert "3. Third" in result
        assert "Preamble" not in result


@pytest.mark.nlp
def test_analyze_text(nlp_service):
    """Test comprehensive text analysis."""
    text = """
    1. Definitions
    The User shall comply with all applicable laws.

    2. Obligations
    The Company may terminate this agreement.
    The User is liable for damages.
    """

    result = nlp_service.analyze_text(text)

    assert "cleaned_text" in result
    assert "clauses" in result
    assert "stats" in result
    assert result["stats"]["clause_count"] > 0


@pytest.mark.nlp
def test_extract_clauses_structure(nlp_service):
    """Test that extracted clauses have proper structure."""
    text = "The party shall perform duties. The company may cancel."
    result = nlp_service.extract_clauses(text)

    for clause in result:
        assert "sentence" in clause
        assert "labels" in clause
        assert "obligation" in clause["labels"]
        assert "permission" in clause["labels"]
        assert "risk" in clause["labels"]


@pytest.mark.nlp
def test_clean_text_removes_page_numbers(nlp_service):
    """Test that page numbers are removed."""
    text = "Some content\n\n42\n\nMore content"
    result = nlp_service.clean_text(text)

    assert "42" not in result or result.count("42") == 0


@pytest.mark.nlp
def test_clean_text_normalizes_whitespace(nlp_service):
    """Test that whitespace is normalized."""
    text = "Text   with    multiple     spaces"
    result = nlp_service.clean_text(text)

    assert "   " not in result


@pytest.mark.nlp
def test_structure_legal_paragraphs(nlp_service):
    """Test legal paragraph structuring."""
    text = "1 Introduction\n1.1 Background\n1.2 Purpose\n2 Terms"
    result = nlp_service.structure_legal_paragraphs(text)

    assert "1" in result
    assert "1.1" in result
    assert "2" in result
