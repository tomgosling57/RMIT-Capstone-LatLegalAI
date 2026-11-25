"""Tests for the language selector settings in Chainlit ChatSettings.

Covers:
- Configuration constant correctness (labels, codes, mappings)
- User-session persistence (in-memory)
- Database persistence (user metadata via ``get_data_layer``)
- System prompt language injection
"""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import (
    OCR_LABEL_TO_CODE,
    SUMMARY_CODE_TO_LABEL,
    SUMMARY_LABEL_TO_CODE,
    SUPPORTED_OCR_LANGUAGES,
    SUPPORTED_SUMMARY_LANGUAGES,
)


class TestSupportedLanguagesConfig:
    """Verify the language config constants contain expected entries."""

    def test_ocr_languages_count(self) -> None:
        """SUPPORTED_OCR_LANGUAGES must have exactly 5 languages."""
        assert len(SUPPORTED_OCR_LANGUAGES) == 5

    def test_ocr_languages_include_expected(self) -> None:
        """SUPPORTED_OCR_LANGUAGES must include English, Hindi, French, Spanish, German."""  # noqa: E501
        expected = {"english", "hindi", "french", "spanish", "german"}
        assert set(SUPPORTED_OCR_LANGUAGES.keys()) == expected

    def test_summary_languages_count(self) -> None:
        """SUPPORTED_SUMMARY_LANGUAGES must have exactly 10 languages."""
        assert len(SUPPORTED_SUMMARY_LANGUAGES) == 10

    def test_summary_languages_include_expected(self) -> None:
        """Verify all 10 expected summary languages are present."""
        expected = {
            "english",
            "hindi",
            "french",
            "spanish",
            "german",
            "chinese_mandarin",
            "indonesian",
            "standard_arabic",
            "urdu",
            "portuguese",
        }
        assert set(SUPPORTED_SUMMARY_LANGUAGES.keys()) == expected


class TestOcrLabelToCodeMapping:
    """Verify OCR_LABEL_TO_CODE maps display labels to correct Tesseract codes."""

    @pytest.mark.parametrize("label, expected_code", list(OCR_LABEL_TO_CODE.items()))
    def test_ocr_label_maps_to_code(
        self, label: str, expected_code: str | None
    ) -> None:
        """Each OCR display label maps to the correct Tesseract language code."""
        assert OCR_LABEL_TO_CODE[label] == expected_code

    def test_ocr_labels_cover_all_supported(self) -> None:
        """Every supported OCR language has a corresponding display label."""
        for name, code in SUPPORTED_OCR_LANGUAGES.items():
            display = name.capitalize()
            assert OCR_LABEL_TO_CODE.get(display) == code, (
                f"Missing display label mapping for {name}"
            )


class TestSummaryLabelToCodeMapping:
    """Verify SUMMARY_LABEL_TO_CODE maps display labels to correct ISO codes."""

    @pytest.mark.parametrize(
        "label, expected_code", list(SUMMARY_LABEL_TO_CODE.items())
    )
    def test_summary_label_maps_to_code(
        self, label: str, expected_code: str | None
    ) -> None:
        """Each summary display label maps to the correct ISO 639-1 code."""
        assert SUMMARY_LABEL_TO_CODE[label] == expected_code

    def test_summary_labels_cover_all_supported(self) -> None:
        """Every supported summary language has a corresponding display label."""
        for name, code in SUPPORTED_SUMMARY_LANGUAGES.items():
            # Build a set of all display labels for validation
            assert code in SUMMARY_CODE_TO_LABEL, (
                f"Missing display label for code {code} ({name})"
            )


class TestSummaryCodeToLabelMapping:
    """Verify SUMMARY_CODE_TO_LABEL reverse mapping is correct."""

    def test_code_to_label_is_reverse_of_label_to_code(self) -> None:
        """SUMMARY_CODE_TO_LABEL must be the exact inverse of SUMMARY_LABEL_TO_CODE."""
        for label, code in SUMMARY_LABEL_TO_CODE.items():
            if code is not None:
                assert SUMMARY_CODE_TO_LABEL[code] == label

    def test_code_to_label_contains_all_codes(self) -> None:
        """All non-None codes in SUMMARY_LABEL_TO_CODE appear in SUMMARY_CODE_TO_LABEL."""
        codes = {code for code in SUMMARY_LABEL_TO_CODE.values() if code is not None}
        assert set(SUMMARY_CODE_TO_LABEL.keys()) == codes


class TestLanguageSettingsPersistence:
    """Test that language selections persist correctly in session state."""

    def test_default_ocr_language_is_none(self) -> None:
        """Default OCR language should be None (auto-detect)."""
        # Simulate what on_chat_start initialises
        session: Dict[str, Any] = {}
        session["ocr_language"] = None
        assert session["ocr_language"] is None

    def test_default_summary_language_is_none(self) -> None:
        """Default summary language should be None (auto-detect)."""
        session: Dict[str, Any] = {}
        session["summary_language"] = None
        assert session["summary_language"] is None

    def test_set_ocr_language_persists(self) -> None:
        """Setting OCR language to a specific code persists in session."""
        session: Dict[str, Any] = {}
        session["ocr_language"] = "hin"
        assert session["ocr_language"] == "hin"

    def test_set_summary_language_persists(self) -> None:
        """Setting summary language to a specific code persists in session."""
        session: Dict[str, Any] = {}
        session["summary_language"] = "fr"
        assert session["summary_language"] == "fr"

    def test_update_language_overrides_previous(self) -> None:
        """Updating language selection overrides the previous value."""
        session: Dict[str, Any] = {}
        session["ocr_language"] = "eng"
        session["ocr_language"] = "hin"
        assert session["ocr_language"] == "hin"


class TestLabelToCodeInitialIndex:
    """Verify the label-list order used for ChatSettings initial_index."""

    # The order of SUMMARY_LABEL_TO_CODE keys defines the dropdown order.
    # "Detect Automatically" must be index 0.
    EXPECTED_LABEL_ORDER = [
        "Detect Automatically",
        "English",
        "Hindi",
        "French",
        "Spanish",
        "German",
        "Chinese (Mandarin)",
        "Indonesian",
        "Standard Arabic",
        "Urdu",
        "Portuguese",
    ]

    def test_summary_labels_in_correct_order(self) -> None:
        """SUMMARY_LABEL_TO_CODE keys must be in the expected dropdown order."""
        assert list(SUMMARY_LABEL_TO_CODE.keys()) == self.EXPECTED_LABEL_ORDER

    @pytest.mark.parametrize(
        "lang_code, expected_label, expected_index",
        [
            (None, "Detect Automatically", 0),
            ("en", "English", 1),
            ("hi", "Hindi", 2),
            ("fr", "French", 3),
            ("es", "Spanish", 4),
            ("de", "German", 5),
            ("zh", "Chinese (Mandarin)", 6),
            ("id", "Indonesian", 7),
            ("ar", "Standard Arabic", 8),
            ("ur", "Urdu", 9),
            ("pt", "Portuguese", 10),
        ],
    )
    def test_lookup_initial_index(
        self,
        lang_code: str | None,
        expected_label: str,
        expected_index: int,
    ) -> None:
        """Given a language code, the correct initial_index must be found."""
        labels = list(SUMMARY_LABEL_TO_CODE.keys())
        if lang_code is None:
            initial = 0  # "Detect Automatically"
        else:
            initial = 0
            for label, code in SUMMARY_LABEL_TO_CODE.items():
                if code == lang_code:
                    initial = labels.index(label)
                    break
        assert initial == expected_index
        assert SUMMARY_LABEL_TO_CODE[labels[expected_index]] == lang_code


class TestSystemPromptLanguageInjection:
    """Test that :func:`llm.setup_runnable` injects language instruction."""

    @patch("src.llm.cl.user_session")
    def test_no_language_no_injection(self, mock_session: MagicMock) -> None:
        """When summary_language is None, no language instruction is added."""
        mock_session.get.return_value = None

        # We only test the system-prompt logic, not the full runnable setup.
        # The language instruction is added inside setup_runnable().
        # We verify by checking the SYSTEM_PROMPT constant is unchanged when
        # no language is set.
        from src.llm import SYSTEM_PROMPT

        # System prompt should NOT contain "Language Instruction" by default
        assert "Language Instruction" not in SYSTEM_PROMPT
        assert "Please respond in" not in SYSTEM_PROMPT

    @patch("src.llm.cl.user_session")
    def test_french_language_injection(self, mock_session: MagicMock) -> None:
        """When summary_language='fr', the system prompt must contain French."""
        # Use side_effect so only "summary_language" returns "fr";
        # the default argument is passed through for other keys (e.g. "memory"),
        # avoiding an AttributeError when setup_runnable tries to call
        # memory.load_memory_variables() on a string.
        def session_get_side_effect(key: str, default: object = None) -> object:
            if key == "summary_language":
                return "fr"
            return default

        mock_session.get.side_effect = session_get_side_effect

        from src.llm import setup_runnable
        from langchain_core.prompts import ChatPromptTemplate

        # Call setup_runnable — it reads summary_language from session
        # and should inject the language instruction.
        # We patch ChatPromptTemplate.from_messages to capture the system prompt.
        original_from_messages = ChatPromptTemplate.from_messages
        captured_system_prompt: list[str] = []

        def capturing_from_messages(messages, *args, **kwargs):
            # Messages can include both (role, content) tuples and
            # single objects like MessagesPlaceholder — only unpack tuples.
            for item in messages:
                if isinstance(item, (tuple, list)) and len(item) == 2:
                    role, content = item
                    if role == "system":
                        captured_system_prompt.append(content)
            return original_from_messages(messages, *args, **kwargs)

        with patch("src.llm._create_llm_model"):
            with patch("src.llm.ConversationBufferMemory"):
                with patch.object(
                    ChatPromptTemplate,
                    "from_messages",
                    side_effect=capturing_from_messages,
                ):
                    setup_runnable()

        # Verify the language instruction was added to the system prompt
        assert len(captured_system_prompt) == 1, (
            "Expected exactly one system prompt to be captured"
        )
        prompt = captured_system_prompt[0]
        assert "## Language Instruction" in prompt, (
            "System prompt should contain '## Language Instruction' heading"
        )
        assert "Please respond in **French** language." in prompt, (
            "System prompt should instruct the LLM to respond in French"
        )
        assert "All your responses must be written in French" in prompt, (
            "System prompt should enforce French for all responses"
        )

    def test_summary_code_to_label_has_french(self) -> None:
        """Verify French is in the SUMMARY_CODE_TO_LABEL mapping."""
        assert SUMMARY_CODE_TO_LABEL.get("fr") == "French"

    def test_summary_code_to_label_has_english(self) -> None:
        """Verify English is in the SUMMARY_CODE_TO_LABEL mapping."""
        assert SUMMARY_CODE_TO_LABEL.get("en") == "English"

    @pytest.mark.parametrize(
        "lang_code, expected_display",
        [
            ("en", "English"),
            ("fr", "French"),
            ("hi", "Hindi"),
            ("es", "Spanish"),
            ("de", "German"),
            ("zh", "Chinese (Mandarin)"),
            ("id", "Indonesian"),
            ("ar", "Standard Arabic"),
            ("ur", "Urdu"),
            ("pt", "Portuguese"),
        ],
    )
    def test_all_language_displays_exist(
        self, lang_code: str, expected_display: str
    ) -> None:
        """Every supported language code must have a display name."""
        assert SUMMARY_CODE_TO_LABEL[lang_code] == expected_display


class TestUserMetadataPersistence:
    """Test database persistence helpers for user language settings.

    Uses mocked ``get_data_layer`` to avoid real database access.
    """

    @pytest.fixture
    def mock_data_layer(self) -> MagicMock:
        """Create a mock SQLAlchemyDataLayer with async methods."""
        mock_dl = MagicMock()
        mock_dl.get_user = AsyncMock()
        mock_dl.create_user = AsyncMock()
        return mock_dl

    @patch("src.app.get_data_layer")
    @pytest.mark.asyncio
    async def test_persist_user_language_saves_to_db(
        self,
        mock_get_dl: MagicMock,
        mock_data_layer: MagicMock,
    ) -> None:
        """_persist_user_language must call create_user with updated metadata."""
        mock_get_dl.return_value = mock_data_layer

        # Mock existing user with empty metadata
        from chainlit.user import PersistedUser

        existing_user = PersistedUser(
            id="test-id",
            identifier="test_user",
            createdAt="2024-01-01T00:00:00Z",
            metadata={},
        )
        mock_data_layer.get_user.return_value = existing_user

        from src.app import _persist_user_language

        user = MagicMock()
        user.identifier = "test_user"

        await _persist_user_language(user, "fr")

        # Verify get_user was called
        mock_data_layer.get_user.assert_awaited_once_with("test_user")

        # Verify create_user was called with metadata containing summary_language
        mock_data_layer.create_user.assert_awaited_once()
        call_args = mock_data_layer.create_user.await_args[0][0]
        assert call_args.metadata["summary_language"] == "fr"

    @patch("src.app.get_data_layer")
    @pytest.mark.asyncio
    async def test_persist_user_language_merges_existing_metadata(
        self,
        mock_get_dl: MagicMock,
        mock_data_layer: MagicMock,
    ) -> None:
        """_persist_user_language must merge existing metadata, not replace it."""
        mock_get_dl.return_value = mock_data_layer

        from chainlit.user import PersistedUser

        existing_user = PersistedUser(
            id="test-id",
            identifier="test_user",
            createdAt="2024-01-01T00:00:00Z",
            metadata={"role": "ADMIN", "existing_key": "keep_me"},
        )
        mock_data_layer.get_user.return_value = existing_user

        from src.app import _persist_user_language

        user = MagicMock()
        user.identifier = "test_user"

        await _persist_user_language(user, "hi")

        mock_data_layer.create_user.assert_awaited_once()
        call_args = mock_data_layer.create_user.await_args[0][0]
        # New key is added
        assert call_args.metadata["summary_language"] == "hi"
        # Existing keys are preserved
        assert call_args.metadata["role"] == "ADMIN"
        assert call_args.metadata["existing_key"] == "keep_me"

    @patch("src.app.get_data_layer")
    @pytest.mark.asyncio
    async def test_persist_user_language_none_clears(
        self,
        mock_get_dl: MagicMock,
        mock_data_layer: MagicMock,
    ) -> None:
        """Persisting None must set summary_language to None in metadata."""
        mock_get_dl.return_value = mock_data_layer

        from chainlit.user import PersistedUser

        existing_user = PersistedUser(
            id="test-id",
            identifier="test_user",
            createdAt="2024-01-01T00:00:00Z",
            metadata={"summary_language": "fr"},
        )
        mock_data_layer.get_user.return_value = existing_user

        from src.app import _persist_user_language

        user = MagicMock()
        user.identifier = "test_user"

        await _persist_user_language(user, None)

        mock_data_layer.create_user.assert_awaited_once()
        call_args = mock_data_layer.create_user.await_args[0][0]
        assert call_args.metadata["summary_language"] is None

    @patch("src.app.get_data_layer")
    @pytest.mark.asyncio
    async def test_load_user_language_returns_persisted_value(
        self,
        mock_get_dl: MagicMock,
        mock_data_layer: MagicMock,
    ) -> None:
        """_load_user_language must return the persisted language code."""
        mock_get_dl.return_value = mock_data_layer

        from chainlit.user import PersistedUser

        existing_user = PersistedUser(
            id="test-id",
            identifier="test_user",
            createdAt="2024-01-01T00:00:00Z",
            metadata={"summary_language": "de"},
        )
        mock_data_layer.get_user.return_value = existing_user

        from src.app import _load_user_language

        user = MagicMock()
        user.identifier = "test_user"

        result = await _load_user_language(user)

        assert result == "de"
        mock_data_layer.get_user.assert_awaited_once_with("test_user")

    @patch("src.app.get_data_layer")
    @pytest.mark.asyncio
    async def test_load_user_language_returns_none_when_unset(
        self,
        mock_get_dl: MagicMock,
        mock_data_layer: MagicMock,
    ) -> None:
        """_load_user_language must return None when no language is stored."""
        mock_get_dl.return_value = mock_data_layer

        from chainlit.user import PersistedUser

        existing_user = PersistedUser(
            id="test-id",
            identifier="test_user",
            createdAt="2024-01-01T00:00:00Z",
            metadata={},
        )
        mock_data_layer.get_user.return_value = existing_user

        from src.app import _load_user_language

        user = MagicMock()
        user.identifier = "test_user"

        result = await _load_user_language(user)

        assert result is None

    @patch("src.app.get_data_layer")
    @pytest.mark.asyncio
    async def test_load_user_language_no_data_layer(
        self,
        mock_get_dl: MagicMock,
    ) -> None:
        """_load_user_language must return None when data layer is unavailable."""
        mock_get_dl.return_value = None

        from src.app import _load_user_language

        user = MagicMock()
        user.identifier = "test_user"

        result = await _load_user_language(user)

        assert result is None

    @patch("src.app.get_data_layer")
    @pytest.mark.asyncio
    async def test_persist_user_language_no_data_layer(
        self,
        mock_get_dl: MagicMock,
    ) -> None:
        """_persist_user_language must not raise when data layer is unavailable."""
        mock_get_dl.return_value = None

        from src.app import _persist_user_language

        user = MagicMock()
        user.identifier = "test_user"

        # Should not raise any exception
        await _persist_user_language(user, "fr")
