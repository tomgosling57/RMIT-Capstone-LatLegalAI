import pytest
from pathlib import Path
import json
from services.nlp_processor import NLPService
from services.file_saver import FileSaver as fs

from services.accuracy_calc import per_label_metrics
from services.accuracy_calc import exact_match_accuracy

ASSETS_DIR = Path(__file__).parent.parent.parent / "tests/assets/NLP_test"

RAW_TXT = ASSETS_DIR / "text_cleaning/raw.txt"
CLEANED_TXT = ASSETS_DIR / "text_cleaning/cleaned.txt"

LEGAL_CLAUSES = ASSETS_DIR / "classification/legal_clauses.txt"
EXPECTED_CLAUSES = ASSETS_DIR / "classification/expected_label.txt"

fileSaver = fs()


@pytest.mark.nlp
def test_txt_cleaning():
    service = NLPService()

    raw_text = RAW_TXT.read_text(encoding="utf-8")
    expected_cleaned = CLEANED_TXT.read_text(encoding="utf-8")

    cleaned = service.clean_text(raw_text)

    assert cleaned.strip() == expected_cleaned.strip()


@pytest.mark.nlp
def test_classification_extraction():
    service = NLPService()

    text = """
    The User shall pay all fees within 30 days.
    The Company may terminate the agreement at any time.
    The User is liable for any damages caused by breach.
    """

    result = service.extract_clauses(text)

    assert result[0]["labels"]["obligation"] is True
    assert result[1]["labels"]["permission"] is True
    assert result[2]["labels"]["risk"] is True


"""
Assumes input clause sentences are same order as expected label sentences
"""


@pytest.mark.nlp
def test_clause_extraction_accuracy():
    service = NLPService()

    raw = LEGAL_CLAUSES.read_text(encoding="utf-8")
    expected = json.loads(EXPECTED_CLAUSES.read_text(encoding="utf-8"))

    result = service.extract_clauses(raw)

    actualLabels = []
    expectedLabels = []
    for label in result:
        actualLabels.append(label.get("labels"))

    for label in expected:
        expectedLabels.append(label.get("labels"))

    assert exact_match_accuracy(actualLabels, expectedLabels) > 0.75

    assert (
        per_label_metrics(
            actualLabels, expectedLabels, ["obligation", "permission", "risk"]
        )
        .get("obligation")
        .get("f1")
        > 0.8
    )
    assert (
        per_label_metrics(
            actualLabels, expectedLabels, ["obligation", "permission", "risk"]
        )
        .get("permission")
        .get("f1")
        > 0.8
    )
    assert (
        per_label_metrics(
            actualLabels, expectedLabels, ["obligation", "permission", "risk"]
        )
        .get("risk")
        .get("f1")
        > 0.8
    )


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
        assert "Schedule 1" in result  # This is not a clause number

    def test_preserves_content_after_clause_1(self, service: NLPService) -> None:
        """Test: Ensure all content after clause 1 is preserved"""
        text = "Preamble\n\n1. First\n\n2. Second\n\n3. Third"
        result = service.remove_before_first_clause_one(text)
        assert "2. Second" in result
        assert "3. Third" in result
        assert "Preamble" not in result
