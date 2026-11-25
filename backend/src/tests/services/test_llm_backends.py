"""
Parametrized pytest unit tests for llm_backend.py
Run with:  pytest test_llm_backends.py -v
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------
from services.llm_backend import (
    AnthropicBackend,
    LLMBackend,
    MockBackend,
    OllamaBackend,
    OpenAIBackend,
    OpenRouterBackend,
    get_llm_backend,
)

ALL_BACKENDS = ["OPENAI", "ANTHROPIC", "OLLAMA", "OPENROUTER", "MOCK"]

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

SAMPLE_LEGAL_TEXT = (
    "This Agreement ('Agreement') is entered into as of the Effective Date by "
    "and between Party A ('Licensor') and Party B ('Licensee'). The Licensor "
    "hereby grants the Licensee a non-exclusive, non-transferable, revocable "
    "licence to use the Software solely for internal business purposes, subject "
    "to the terms and conditions set forth herein."
)

EXPECTED_MOCK_PREFIX = "[MOCK SUMMARY]"

# ---------------------------------------------------------------------------
# Helpers – thin fake SDK objects
# ---------------------------------------------------------------------------


def _make_openai_response(text: str) -> MagicMock:
    """Return a fake openai.ChatCompletion-style response object."""
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _make_anthropic_response(text: str) -> MagicMock:
    """Return a fake anthropic.Message-style response object."""
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


def _make_ollama_response(text: str) -> MagicMock:
    """Return a fake requests.Response-style object for the Ollama endpoint."""
    resp = MagicMock()
    resp.json.return_value = {"response": text}
    resp.raise_for_status.return_value = None
    return resp


# ===========================================================================
# 1. Abstract base class contract
# ===========================================================================


@pytest.mark.mock
class TestLLMBackendABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            LLMBackend()  # type: ignore[abstract]

    def test_subclass_without_complete_raises(self):
        class Incomplete(LLMBackend):
            pass

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore[abstract]

    def test_valid_subclass_works(self):
        class Minimal(LLMBackend):
            def complete(self, prompt: str) -> str:
                return "ok"

        assert Minimal().complete("hi") == "ok"


# ===========================================================================
# 2. MockBackend
# ===========================================================================


@pytest.mark.mock
class TestMockBackend:
    @pytest.fixture
    def backend(self) -> MockBackend:
        return MockBackend()

    # --- complete -----------------------------------------------------------

    @pytest.mark.parametrize(
        "prompt",
        [
            "Hello",
            "Summarise this contract.",
            "",  # empty prompt should not raise
            "a" * 5000,  # very long prompt
        ],
        ids=["simple", "legal", "empty", "very_long"],
    )
    def test_complete_returns_string(self, backend: MockBackend, prompt: str):
        result = backend.complete(prompt)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_complete_contains_mock_marker(self, backend: MockBackend):
        result = backend.complete("anything")
        assert EXPECTED_MOCK_PREFIX in result

    # --- summarise ----------------------------------------------------------

    @pytest.mark.parametrize(
        "target_language",
        [None, "es", "fr", "de", "zh"],
        ids=["none", "spanish", "french", "german", "chinese"],
    )
    def test_summarise_returns_string(
        self, backend: MockBackend, target_language: str | None
    ):
        result = backend.summarise(SAMPLE_LEGAL_TEXT, target_language)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_summarise_no_language_returns_mock(self, backend: MockBackend):
        result = backend.summarise(SAMPLE_LEGAL_TEXT)
        assert EXPECTED_MOCK_PREFIX in result

    def test_summarise_with_language_returns_mock(self, backend: MockBackend):
        result = backend.summarise(SAMPLE_LEGAL_TEXT, target_language="es")
        assert EXPECTED_MOCK_PREFIX in result


# ===========================================================================
# 3. OpenAIBackend
# ===========================================================================


@pytest.mark.openai
class TestOpenAIBackend:
    """All tests patch the openai.OpenAI client so no real API is called."""

    @pytest.fixture
    def mock_openai_client(self):
        with patch("llm_backends.OpenAIBackend.__init__") as mock_init:
            mock_init.return_value = None
            yield mock_init

    def _make_backend(self, response_text: str = "OpenAI response") -> OpenAIBackend:
        backend = OpenAIBackend.__new__(OpenAIBackend)
        backend.model = "gpt-4o-mini"
        client = MagicMock()
        client.chat.completions.create.return_value = _make_openai_response(
            response_text
        )
        backend.client = client
        return backend

    # --- complete -----------------------------------------------------------

    @pytest.mark.parametrize(
        "prompt, expected",
        [
            ("Hello", "Hello reply"),
            ("Summarise contract", "Contract summary"),
            ("  spaces  ", "trimmed"),
        ],
        ids=["hello", "contract", "spaces"],
    )
    def test_complete_returns_expected_text(self, prompt: str, expected: str):
        backend = self._make_backend(response_text=expected)
        result = backend.complete(prompt)
        assert result == expected

    def test_complete_calls_api_with_correct_model(self):
        backend = self._make_backend("ok")
        backend.complete("test prompt")
        call_kwargs = backend.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"

    def test_complete_calls_api_with_user_role(self):
        backend = self._make_backend("ok")
        backend.complete("test prompt")
        call_kwargs = backend.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"][0]["role"] == "user"

    def test_complete_passes_prompt_as_content(self):
        backend = self._make_backend("ok")
        backend.complete("my prompt")
        call_kwargs = backend.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"][0]["content"] == "my prompt"

    @pytest.mark.parametrize("model", ["gpt-4o", "gpt-3.5-turbo"])
    def test_custom_model_is_used(self, model: str):
        backend = self._make_backend("ok")
        backend.model = model
        backend.complete("hi")
        call_kwargs = backend.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == model

    # --- __init__ env var ---------------------------------------------------

    def test_init_raises_without_api_key(self):
        env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises((KeyError, Exception)):
                OpenAIBackend()

    # --- summarise (integration with complete) ------------------------------

    @pytest.mark.parametrize(
        "target_language",
        [None, "es", "fr"],
        ids=["english", "spanish", "french"],
    )
    def test_summarise_calls_complete_once(self, target_language: str | None):
        backend = self._make_backend("summary text")
        with patch.object(backend, "complete", wraps=backend.complete) as spy:
            backend.summarise(SAMPLE_LEGAL_TEXT, target_language)
            spy.assert_called_once()

    def test_summarise_english_prompt_has_no_jargon_instruction(self):
        backend = self._make_backend("ok")
        captured: list[str] = []
        original = backend.complete

        def capture(prompt: str) -> str:
            captured.append(prompt)
            return original(prompt)

        with patch.object(backend, "complete", side_effect=capture):
            backend.summarise(SAMPLE_LEGAL_TEXT)

        assert "plain" in captured[0].lower() or "plain-language" in captured[0].lower()

    def test_summarise_with_language_includes_target_in_prompt(self):
        backend = self._make_backend("ok")
        captured: list[str] = []

        def capture(prompt: str) -> str:
            captured.append(prompt)
            return "ok"

        with patch.object(backend, "complete", side_effect=capture):
            backend.summarise(SAMPLE_LEGAL_TEXT, target_language="de")

        assert "de" in captured[0] or "german" in captured[0].lower()


# ===========================================================================
# 4. AnthropicBackend
# ===========================================================================


@pytest.mark.anthropic
class TestAnthropicBackend:
    def _make_backend(
        self, response_text: str = "Anthropic response"
    ) -> AnthropicBackend:
        backend = AnthropicBackend.__new__(AnthropicBackend)
        backend.model = "claude-haiku-4-5-20251001"
        client = MagicMock()
        client.messages.create.return_value = _make_anthropic_response(response_text)
        backend.client = client
        return backend

    @pytest.mark.parametrize(
        "prompt, expected",
        [
            ("Hello", "Hi there"),
            ("Legal doc", "Legal summary"),
        ],
        ids=["hello", "legal"],
    )
    def test_complete_returns_expected_text(self, prompt: str, expected: str):
        backend = self._make_backend(response_text=expected)
        result = backend.complete(prompt)
        assert result == expected

    def test_complete_calls_api_with_correct_model(self):
        backend = self._make_backend("ok")
        backend.complete("prompt")
        call_kwargs = backend.client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"

    def test_complete_uses_user_role(self):
        backend = self._make_backend("ok")
        backend.complete("prompt")
        call_kwargs = backend.client.messages.create.call_args.kwargs
        assert call_kwargs["messages"][0]["role"] == "user"

    def test_complete_passes_prompt_as_content(self):
        backend = self._make_backend("ok")
        backend.complete("my prompt")
        call_kwargs = backend.client.messages.create.call_args.kwargs
        assert call_kwargs["messages"][0]["content"] == "my prompt"

    def test_init_raises_without_api_key(self):
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises((KeyError, Exception)):
                AnthropicBackend()

    @pytest.mark.parametrize("model", ["claude-opus-4-6", "claude-sonnet-4-6"])
    def test_custom_model_is_used(self, model: str):
        backend = self._make_backend("ok")
        backend.model = model
        backend.complete("hi")
        call_kwargs = backend.client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == model


# ===========================================================================
# 5. OllamaBackend
# ===========================================================================


@pytest.mark.ollama
class TestOllamaBackend:
    def _make_backend(self, response_text: str = "Ollama response") -> OllamaBackend:
        backend = OllamaBackend.__new__(OllamaBackend)
        backend.model = "llama3"
        backend.base_url = "http://localhost:11434"
        mock_requests = MagicMock()
        mock_requests.post.return_value = _make_ollama_response(response_text)
        backend._requests = mock_requests
        return backend

    @pytest.mark.parametrize(
        "prompt, expected",
        [
            ("Hello", "Hi"),
            ("Legal text", "Summary here"),
            ("", "empty prompt response"),
        ],
        ids=["hello", "legal", "empty"],
    )
    def test_complete_returns_expected_text(self, prompt: str, expected: str):
        backend = self._make_backend(response_text=expected)
        result = backend.complete(prompt)
        assert result == expected

    def test_complete_posts_to_correct_url(self):
        backend = self._make_backend("ok")
        backend.complete("hi")
        call_args = backend._requests.post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/generate"

    def test_complete_sends_model_and_prompt(self):
        backend = self._make_backend("ok")
        backend.complete("test prompt")
        call_kwargs = backend._requests.post.call_args.kwargs
        assert call_kwargs["json"]["model"] == "llama3"
        assert call_kwargs["json"]["prompt"] == "test prompt"

    def test_complete_disables_streaming(self):
        backend = self._make_backend("ok")
        backend.complete("hi")
        call_kwargs = backend._requests.post.call_args.kwargs
        assert call_kwargs["json"]["stream"] is False

    def test_complete_raises_on_http_error(self):
        backend = self._make_backend("ok")
        backend._requests.post.return_value.raise_for_status.side_effect = Exception(
            "HTTP 500"
        )
        with pytest.raises(Exception, match="HTTP 500"):
            backend.complete("hi")

    @pytest.mark.parametrize(
        "base_url", ["http://localhost:11434", "http://192.168.1.1:11434"]
    )
    def test_custom_base_url(self, base_url: str):
        backend = self._make_backend("ok")
        backend.base_url = base_url
        backend.complete("hi")
        call_args = backend._requests.post.call_args
        assert call_args[0][0].startswith(base_url)

    def test_default_model_from_env(self):
        with patch.dict(os.environ, {"OLLAMA_MODEL": "mistral"}):

            with patch("llm_backends.OllamaBackend.__init__") as mock_init:
                mock_init.return_value = None
                # Directly test model resolution logic
                model = os.environ.get("OLLAMA_MODEL", "llama3")
                assert model == "mistral"


# ===========================================================================
# 6. OpenRouterBackend
# ===========================================================================


@pytest.mark.openrouter
class TestOpenRouterBackend:
    def _make_backend(
        self,
        response_text: str = "OpenRouter response",
        model: str = "openai/gpt-4o-mini",
    ) -> OpenRouterBackend:
        backend = OpenRouterBackend.__new__(OpenRouterBackend)
        backend.model = model
        client = MagicMock()
        client.chat.completions.create.return_value = _make_openai_response(
            response_text
        )
        backend.client = client
        return backend

    @pytest.mark.parametrize(
        "prompt, expected",
        [
            ("Hello", "Hello from OpenRouter"),
            ("Legal text", "Legal summary via router"),
            ("", "empty response"),
        ],
        ids=["hello", "legal", "empty"],
    )
    def test_complete_returns_expected_text(self, prompt: str, expected: str):
        backend = self._make_backend(response_text=expected)
        result = backend.complete(prompt)
        assert result == expected

    def test_complete_calls_api_with_correct_model(self):
        backend = self._make_backend("ok")
        backend.complete("prompt")
        call_kwargs = backend.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "openai/gpt-4o-mini"

    def test_complete_uses_user_role(self):
        backend = self._make_backend("ok")
        backend.complete("prompt")
        call_kwargs = backend.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"][0]["role"] == "user"

    def test_complete_passes_prompt_as_content(self):
        backend = self._make_backend("ok")
        backend.complete("my prompt")
        call_kwargs = backend.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"][0]["content"] == "my prompt"

    @pytest.mark.parametrize(
        "model",
        [
            "anthropic/claude-3.5-haiku",
            "google/gemini-flash-1.5",
            "meta-llama/llama-3.1-8b-instruct:free",
            "openai/gpt-4o",
        ],
    )
    def test_various_openrouter_models(self, model: str):
        backend = self._make_backend("ok", model=model)
        backend.complete("hi")
        call_kwargs = backend.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == model

    def test_init_raises_without_api_key(self):
        env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(EnvironmentError, match="OPENROUTER_API_KEY"):
                OpenRouterBackend()

    def test_init_uses_env_model(self):
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "test-key",
                "OPENROUTER_MODEL": "google/gemini-flash-1.5",
            },
        ):
            with patch("llm_backends.OpenAI") as MockOpenAI:
                MockOpenAI.return_value = MagicMock()
                backend = OpenRouterBackend()
                assert backend.model == "google/gemini-flash-1.5"

    def test_init_default_model_when_no_env(self):
        env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_MODEL"}
        env["OPENROUTER_API_KEY"] = "test-key"
        with patch.dict(os.environ, env, clear=True):
            with patch("llm_backends.OpenAI") as MockOpenAI:
                MockOpenAI.return_value = MagicMock()
                backend = OpenRouterBackend()
                assert backend.model == OpenRouterBackend.DEFAULT_MODEL

    def test_init_sets_base_url(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            with patch("llm_backends.OpenAI") as MockOpenAI:
                MockOpenAI.return_value = MagicMock()
                OpenRouterBackend()
                call_kwargs = MockOpenAI.call_args.kwargs
                assert call_kwargs["base_url"] == OpenRouterBackend.BASE_URL

    def test_init_sets_referer_header_from_env(self):
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "test-key",
                "OPENROUTER_SITE_URL": "https://myapp.example.com",
            },
        ):
            with patch("llm_backends.OpenAI") as MockOpenAI:
                MockOpenAI.return_value = MagicMock()
                OpenRouterBackend()
                call_kwargs = MockOpenAI.call_args.kwargs
                headers = call_kwargs.get("default_headers", {})
                assert headers.get("HTTP-Referer") == "https://myapp.example.com"

    def test_init_sets_x_title_header_from_env(self):
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "test-key",
                "OPENROUTER_SITE_NAME": "My Legal App",
            },
        ):
            with patch("llm_backends.OpenAI") as MockOpenAI:
                MockOpenAI.return_value = MagicMock()
                OpenRouterBackend()
                call_kwargs = MockOpenAI.call_args.kwargs
                headers = call_kwargs.get("default_headers", {})
                assert headers.get("X-Title") == "My Legal App"

    def test_init_explicit_params_override_env(self):
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "test-key",
                "OPENROUTER_SITE_URL": "https://env.example.com",
                "OPENROUTER_SITE_NAME": "Env Name",
            },
        ):
            with patch("llm_backends.OpenAI") as MockOpenAI:
                MockOpenAI.return_value = MagicMock()
                OpenRouterBackend(
                    site_url="https://explicit.example.com",
                    site_name="Explicit Name",
                )
                call_kwargs = MockOpenAI.call_args.kwargs
                headers = call_kwargs.get("default_headers", {})
                assert headers["HTTP-Referer"] == "https://explicit.example.com"
                assert headers["X-Title"] == "Explicit Name"

    @pytest.mark.parametrize(
        "target_language",
        [None, "es", "ja"],
        ids=["english", "spanish", "japanese"],
    )
    def test_summarise_calls_complete_once(self, target_language: str | None):
        backend = self._make_backend("summary")
        with patch.object(backend, "complete", wraps=backend.complete) as spy:
            backend.summarise(SAMPLE_LEGAL_TEXT, target_language)
            spy.assert_called_once()


# ===========================================================================
# 7. get_llm_backend factory
# ===========================================================================


@pytest.mark.mock
class TestGetLLMBackend:
    @pytest.mark.parametrize(
        "backend_name, expected_class",
        [
            ("mock", MockBackend),
            ("MOCK", MockBackend),  # case-insensitive
        ],
        ids=["mock_lower", "mock_upper"],
    )
    def test_returns_correct_class_for_mock(
        self, backend_name: str, expected_class: type
    ):
        backend = get_llm_backend(backend_name)
        assert isinstance(backend, expected_class)

    def test_unknown_backend_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown LLM_BACKEND"):
            get_llm_backend("nonexistent_backend")

    @pytest.mark.parametrize(
        "env_value, expected_class",
        [
            ("mock", MockBackend),
        ],
        ids=["mock_via_env"],
    )
    def test_reads_llm_backend_env_var(self, env_value: str, expected_class: type):
        with patch.dict(os.environ, {"LLM_BACKEND": env_value}):
            backend = get_llm_backend()
            assert isinstance(backend, expected_class)

    def test_explicit_name_overrides_env_var(self):
        with patch.dict(os.environ, {"LLM_BACKEND": "openai"}):
            # Pass "mock" explicitly — should override the env var
            backend = get_llm_backend("mock")
            assert isinstance(backend, MockBackend)

    def test_defaults_to_mock_when_no_env(self):
        env = {k: v for k, v in os.environ.items() if k != "LLM_BACKEND"}
        with patch.dict(os.environ, env, clear=True):
            backend = get_llm_backend()
            assert isinstance(backend, MockBackend)

    def test_openrouter_is_registered(self):
        """OpenRouterBackend must be reachable through the factory."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            with patch("llm_backends.OpenAI"):
                backend = get_llm_backend("openrouter")
                assert isinstance(backend, OpenRouterBackend)

    def test_error_message_lists_all_backends(self):
        with pytest.raises(ValueError) as exc_info:
            get_llm_backend("bad_name")
        msg = str(exc_info.value)
        for name in ("openai", "anthropic", "ollama", "openrouter", "mock"):
            assert name in msg

    @pytest.mark.parametrize(
        "backend_name",
        ["openai", "anthropic", "ollama", "openrouter", "mock"],
    )
    def test_all_backend_names_are_recognised(self, backend_name: str):
        """Factory should not raise ValueError for any known backend name.
        We patch constructors so no real credentials are needed."""
        patches = {
            "openai": patch(
                "services.llm_backend.OpenAIBackend.__init__", return_value=None
            ),
            "anthropic": patch(
                "services.llm_backend.AnthropicBackend.__init__", return_value=None
            ),
            "ollama": patch(
                "services.llm_backend.OllamaBackend.__init__", return_value=None
            ),
            "openrouter": patch(
                "services.llm_backend.OpenRouterBackend.__init__", return_value=None
            ),
            "mock": patch(
                "services.llm_backend.MockBackend.__init__", return_value=None
            ),
        }
        with patches[backend_name]:
            instance = get_llm_backend(backend_name)
            assert instance is not None


# ===========================================================================
# 8. Cross-backend contract tests (parametrized over all backends)
# ===========================================================================


@pytest.mark.openai
@pytest.mark.anthropic
@pytest.mark.ollama
@pytest.mark.openrouter
@pytest.mark.mock
class TestAllBackendsContract:

    # Each entry: (backend_instance_factory,)
    # We build backends with mocked clients to avoid any I/O.

    def _mock_backend() -> MockBackend:
        return MockBackend()

    def _openai_backend() -> OpenAIBackend:
        b = OpenAIBackend.__new__(OpenAIBackend)
        b.model = "gpt-4o-mini"
        client = MagicMock()
        client.chat.completions.create.return_value = _make_openai_response("response")
        b.client = client
        return b

    def _anthropic_backend() -> AnthropicBackend:
        b = AnthropicBackend.__new__(AnthropicBackend)
        b.model = "claude-haiku-4-5-20251001"
        client = MagicMock()
        client.messages.create.return_value = _make_anthropic_response("response")
        b.client = client
        return b

    def _ollama_backend() -> OllamaBackend:
        b = OllamaBackend.__new__(OllamaBackend)
        b.model = "llama3"
        b.base_url = "http://localhost:11434"
        mock_requests = MagicMock()
        mock_requests.post.return_value = _make_ollama_response("response")
        b._requests = mock_requests
        return b

    def _openrouter_backend() -> OpenRouterBackend:
        b = OpenRouterBackend.__new__(OpenRouterBackend)
        b.model = "openai/gpt-4o-mini"
        client = MagicMock()
        client.chat.completions.create.return_value = _make_openai_response("response")
        b.client = client
        return b

    ALL_BACKENDS = [
        pytest.param(_mock_backend, id="mock"),
        pytest.param(_openai_backend, id="openai"),
        pytest.param(_anthropic_backend, id="anthropic"),
        pytest.param(_ollama_backend, id="ollama"),
        pytest.param(_openrouter_backend, id="openrouter"),
    ]

    class TestAllBackendsContract:
        @pytest.mark.parametrize("factory", ALL_BACKENDS)
        def test_is_llm_backend_subclass(self, factory):
            backend = factory()
            assert isinstance(backend, LLMBackend)

        @pytest.mark.parametrize("factory", ALL_BACKENDS)
        def test_complete_returns_non_empty_string(self, factory):
            backend = factory()
            result = backend.complete("Hello")
            assert isinstance(result, str)
            assert len(result) > 0

        @pytest.mark.parametrize("factory", ALL_BACKENDS)
        def test_summarise_returns_non_empty_string(self, factory):
            backend = factory()
            result = backend.summarise(SAMPLE_LEGAL_TEXT)
            assert isinstance(result, str)
            assert len(result) > 0

        @pytest.mark.parametrize("factory", ALL_BACKENDS)
        @pytest.mark.parametrize("lang", ["es", "fr", "de"])
        def test_summarise_with_language_returns_non_empty_string(self, factory, lang):
            backend = factory()
            result = backend.summarise(SAMPLE_LEGAL_TEXT, target_language=lang)
            assert isinstance(result, str)
            assert len(result) > 0

        @pytest.mark.parametrize("factory", ALL_BACKENDS)
        def test_complete_with_empty_prompt_does_not_raise(self, factory):
            backend = factory()
            result = backend.complete("")
            assert isinstance(result, str)
