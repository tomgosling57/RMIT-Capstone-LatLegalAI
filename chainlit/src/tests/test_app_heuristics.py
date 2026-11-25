"""Tests for Chainlit app heuristic functions.

Verifies that ``is_section_summary_request`` and
``is_translation_request`` correctly identify user intents
without producing false positives on unrelated text.
"""

"""Tests for Chainlit app heuristic functions.

Verifies that ``is_section_summary_request`` and
``is_translation_request`` correctly identify user intents
without producing false positives on unrelated text.
"""

from src.heuristics import is_section_summary_request, is_translation_request

# ---------------------------------------------------------------------------
# is_section_summary_request
# ---------------------------------------------------------------------------


class TestIsSectionSummaryRequest:
    """Tests for the section-summary request heuristic."""

    def test_exact_phrase_section_summary(self) -> None:
        """'section summary' should match."""
        assert is_section_summary_request("Give me a section summary")

    def test_summarise_sections(self) -> None:
        """'summarise sections' (British spelling) should match."""
        assert is_section_summary_request("Please summarise sections")

    def test_summarize_sections(self) -> None:
        """'summarize sections' (American spelling) should match."""
        assert is_section_summary_request("Summarize sections please")

    def test_list_sections(self) -> None:
        """'list sections' should match."""
        assert is_section_summary_request("list sections in the document")

    def test_identify_sections(self) -> None:
        """'identify sections' should match."""
        assert is_section_summary_request("Can you identify sections")

    def test_document_sections(self) -> None:
        """'document sections' should match."""
        assert is_section_summary_request("What are the document sections?")

    def test_what_are_the_sections(self) -> None:
        """'what are the sections' should match."""
        assert is_section_summary_request("what are the sections")

    def test_section_breakdown(self) -> None:
        """'section breakdown' should match."""
        assert is_section_summary_request("section breakdown")

    def test_outline_the_document(self) -> None:
        """'outline the document' should match."""
        assert is_section_summary_request("outline the document")

    def test_regular_question_no_match(self) -> None:
        """Normal chat questions should not match."""
        assert not is_section_summary_request("What is the weather today?")

    def test_greeting_no_match(self) -> None:
        """Greetings should not match."""
        assert not is_section_summary_request("Hello, how are you?")

    def test_partial_word_no_match(self) -> None:
        """'sections' alone should not match - needs a keyword pair."""
        assert not is_section_summary_request(
            "I have several sections in my document"
        )

    def test_empty_string(self) -> None:
        """Empty string should not match."""
        assert not is_section_summary_request("")

    def test_case_insensitive(self) -> None:
        """Match should be case-insensitive."""
        assert is_section_summary_request("SECTION SUMMARY PLEASE")
        assert is_section_summary_request("Section Summary")

    def test_leading_trailing_whitespace(self) -> None:
        """Leading/trailing whitespace should be stripped."""
        assert is_section_summary_request("  section summary  ")
        assert is_section_summary_request("\tsection summary\n")

    def test_punctuation_variants(self) -> None:
        """Punctuation around keywords should not prevent matching."""
        assert is_section_summary_request("Section summary?")
        assert is_section_summary_request("Section summary!")
        assert is_section_summary_request("Please summarise the document sections")


# ---------------------------------------------------------------------------
# is_translation_request
# ---------------------------------------------------------------------------


class TestIsTranslationRequest:
    """Tests for the translation request heuristic."""

    # --- Tier 1: Strong signals ---

    def test_translate_keyword(self) -> None:
        """'translate' should always match."""
        assert is_translation_request("Can you translate this document?")

    def test_translation_keyword(self) -> None:
        """'translation' should always match."""
        assert is_translation_request("I need a translation")

    def test_convert_to_keyword(self) -> None:
        """'convert to' should always match."""
        assert is_translation_request("convert to english please")

    def test_translate_mid_sentence(self) -> None:
        """'translate' mid-sentence should still match."""
        assert is_translation_request("Please translate this for me")

    # --- Tier 2: "in {language}" near start ---

    def test_in_english_at_start(self) -> None:
        """'in english' near the start should match."""
        assert is_translation_request("In english please")

    def test_in_hindi_at_start_with_hello(self) -> None:
        """'in hindi' after a short prefix should match."""
        assert is_translation_request("In hindi, can you help?")

    def test_in_french_at_position_0(self) -> None:
        """'in french' at position 0 should match."""
        assert is_translation_request("in french please")

    def test_in_spanish_after_short_prefix(self) -> None:
        """'in spanish' within first 30 chars should match."""
        assert is_translation_request("Reply in spanish")

    def test_in_german_near_start(self) -> None:
        """'in german' within first 30 chars should match."""
        assert is_translation_request("Can you in german")

    def test_in_chinese_close_to_start(self) -> None:
        """'in chinese' within first 30 chars should match."""
        assert is_translation_request("Please in chinese")

    # --- False positive prevention ---

    def test_interested_in_english_literature(self) -> None:
        """'in english' deep in a sentence should match false positive."""
        assert not is_translation_request(
            "I'm interested in English literature"
        )

    def test_whats_in_french_cuisine(self) -> None:
        """'in french' deep in a sentence should match false positive."""
        assert not is_translation_request(
            "I wonder what is in French cuisine that makes it so special?"
        )

    def test_course_in_spanish(self) -> None:
        """'in spanish' deep in a sentence should match false positive."""
        assert not is_translation_request(
            "I am taking a course in Spanish language"
        )

    def test_study_in_german(self) -> None:
        """'in german' deep in a sentence should match false positive."""
        assert not is_translation_request(
            "I want to study in German universities"
        )

    def test_movie_in_hindi(self) -> None:
        """'in hindi' deep in a sentence should not match."""
        assert not is_translation_request(
            "I watched a movie in Hindi yesterday"
        )

    def test_article_in_arabic(self) -> None:
        """'in arabic' deep in a sentence should not match."""
        assert not is_translation_request(
            "I read an article in Arabic about history"
        )

    def test_news_in_portuguese(self) -> None:
        """'in portuguese' deep in a sentence should not match."""
        assert not is_translation_request(
            "I watched the news in Portuguese today"
        )

    def test_song_in_urdu(self) -> None:
        """'in urdu' deep in a sentence should not match."""
        assert not is_translation_request(
            "I heard a beautiful song in Urdu"
        )

    def test_food_in_indonesian(self) -> None:
        """'in indonesian' deep in a sentence should not match."""
        assert not is_translation_request(
            "I love cooking food in Indonesian style"
        )

    # --- Edge cases ---

    def test_greeting_no_match(self) -> None:
        """Greetings should not match."""
        assert not is_translation_request("Hello! How are you?")

    def test_empty_string(self) -> None:
        """Empty string should not match."""
        assert not is_translation_request("")

    def test_case_insensitive_translate(self) -> None:
        """'Translate' with capital T should match."""
        assert is_translation_request("Translate this document")

    def test_case_insensitive_in_english(self) -> None:
        """'In English' with capitals should match when near start."""
        assert is_translation_request("In English please")

    def test_leading_trailing_whitespace(self) -> None:
        """Leading/trailing whitespace should be stripped."""
        assert is_translation_request("  translate  ")
        assert is_translation_request("\ttranslation\n")

    def test_punctuation_around_translate(self) -> None:
        """Punctuation around translation keywords should not match."""
        assert is_translation_request("Translate?")
        assert is_translation_request("Translation!")
        assert is_translation_request("[Translate]")

    def test_in_english_with_punctuation(self) -> None:
        """Punctuation after 'in english' near start should match."""
        assert is_translation_request("In english!")
        assert is_translation_request("In english?")
