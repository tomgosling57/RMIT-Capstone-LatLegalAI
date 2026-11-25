#!/usr/bin/env python
"""
Verification script for improved remove_before_first_clause_one method.
Tests against sample legal documents to ensure no regressions.
"""

from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.nlp_processor import NLPService


def test_sample_documents() -> None:
    """Test the improved method against sample legal documents."""
    service = NLPService()
    sample_dir = Path(__file__).parent.parent / "legal_documents"

    markdown_files = list(sample_dir.glob("sample-*.md"))

    if not markdown_files:
        print("❌ No sample documents found in legal_documents/")
        return

    print(f"Testing {len(markdown_files)} sample legal documents...\n")

    for doc_path in markdown_files:
        print(f"📄 Testing: {doc_path.name}")
        text = doc_path.read_text(encoding="utf-8")

        # Test the method
        result = service.remove_before_first_clause_one(text)

        # Verify results
        if result.startswith("1"):
            print("   ✓ Successfully found clause 1")
            first_line = result.split("\n")[0][:80]
            print(f"   First line: {first_line}...")
        else:
            print("   ⚠ Warning: Result doesn't start with '1'")
            first_line = result.split("\n")[0][:80]
            print(f"   First line: {first_line}...")

        # Check that something was removed
        if len(result) < len(text):
            removed_chars = len(text) - len(result)
            removed_percent = (removed_chars / len(text)) * 100
            msg = (
                f"   ✓ Removed {removed_chars} chars "
                f"({removed_percent:.1f}% of original)"
            )
            print(msg)
        else:
            print("   ℹ No text removed (clause 1 at start or not found)")

        print()


def test_asset_files() -> None:
    """Test against asset files used in existing test suite."""
    service = NLPService()
    asset_dir = (
        Path(__file__).parent
        / "src"
        / "tests"
        / "assets"
        / "NLP_test"
        / "text_cleaning"
    )

    raw_file = asset_dir / "raw.txt"
    if not raw_file.exists():
        print("❌ Asset test file not found")
        return

    print("\n📦 Testing against existing test asset (OCR-extracted legal text):")
    text = raw_file.read_text(encoding="utf-8")
    result = service.remove_before_first_clause_one(text)

    # Display original
    print(f"   Original text length: {len(text)} characters")
    print(f"   Original starts with: {text[:100]}")

    # Display result
    print(f"\n   Result text length: {len(result)} characters")
    print(f"   Result starts with: {result[:100]}")

    # Verify
    if result.startswith("1. The User shall comply"):
        print("\n   ✓ Successfully removed preamble and found clause 1")
    else:
        print("\n   ⚠ Unexpected result")


def test_edge_cases() -> None:
    """Test specific edge cases with controlled examples."""
    service = NLPService()

    print("\n" + "=" * 70)
    print("EDGE CASE TESTS")
    print("=" * 70 + "\n")

    test_cases = [
        (
            "Date with '1'",
            "This agreement made January 1, 2024.\n\n1. Parties\nContent here.",
            "1. Parties",
        ),
        ("No clause 1", "2. First Section\n3. Second Section", "2. First Section"),
        (
            "Multi-line preamble",
            "Header\nLine 2\nLine 3\n\n1. Definition\nBody.",
            "1. Definition",
        ),
        ("Clause with space", "Preamble\n1 The parties\nContent.", "1 The parties"),
    ]

    for test_name, input_text, expected_start in test_cases:
        result = service.remove_before_first_clause_one(input_text)
        success = result.startswith(expected_start)
        status = "✓" if success else "❌"
        print(f"{status} {test_name}")
        if not success:
            print(f"   Expected to start with: '{expected_start}'")
            print(f"   Actually starts with: '{result[:50]}'")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SAMPLE DOCUMENT VERIFICATION")
    print("=" * 70 + "\n")

    test_sample_documents()
    test_asset_files()
    test_edge_cases()

    print("\n" + "=" * 70)
    print("Verification complete!")
    print("=" * 70 + "\n")
