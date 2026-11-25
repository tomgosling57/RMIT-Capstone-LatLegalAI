"""
LatMatrix LLM Module - LangChain Runnable pipeline and chat interaction.

Provides the system prompt, runnable setup (model, prompt template, memory
injection), and the core ``call_llm()`` / ``stream_summary_analysis()``
functions that stream responses from the LLM backend.

The model is created by :func:`_create_llm_model`, which uses
``ChatLiteLLM`` from ``langchain_community`` (which wraps ``litellm``)
when available, falling back to a minimal :class:`LiteLLMWrapper` that
calls ``litellm`` directly.  No ``langchain-openai`` / ``ChatOpenAI``
dependency is required.

__all__ = [
    "call_llm",
    "load_memory_from_thread",
    "setup_runnable",
    "stream_summary_analysis",
]


"""

import logging
import os
from operator import itemgetter
from typing import Any, AsyncIterator, Iterator, List, Optional, cast

import chainlit as cl
import httpx
from chainlit.types import ThreadDict
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from langchain_core.runnables.config import RunnableConfig

from .config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_PROVIDER,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    SUMMARY_CODE_TO_LABEL,
)
from .summary import store_summary_in_session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LiteLLM wrapper — standalone BaseChatModel without langchain-openai
# ---------------------------------------------------------------------------


class LiteLLMWrapper(BaseChatModel):
    """Minimal ``BaseChatModel`` wrapper around the ``litellm`` package.

    Provides identical functionality to ``ChatLiteLLM`` without requiring
    ``langchain_community``.  Used as a fallback when ``ChatLiteLLM`` is
    not importable.
    """

    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    streaming: bool = True

    @property
    def _llm_type(self) -> str:
        return "litellm_wrapper"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        import litellm

        # Convert LangChain messages → litellm-compatible dicts.
        litellm_messages = [_convert_message_to_dict(msg) for msg in messages]

        response = litellm.completion(
            model=self.model,
            messages=litellm_messages,
            api_key=self.api_key,
            api_base=self.api_base,
            stop=stop,
            **kwargs,
        )
        choice = response["choices"][0]
        message = choice["message"]
        content = message.get("content", "")
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(content=content),
                )
            ]
        )

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        import litellm

        litellm_messages = [_convert_message_to_dict(msg) for msg in messages]

        response = litellm.completion(
            model=self.model,
            messages=litellm_messages,
            api_key=self.api_key,
            api_base=self.api_base,
            stop=stop,
            stream=True,
            **kwargs,
        )
        for chunk in response:
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content", "")
            if content:
                yield ChatGenerationChunk(
                    message=AIMessageChunk(content=content),
                )

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        import litellm

        litellm_messages = [_convert_message_to_dict(msg) for msg in messages]

        response = await litellm.acompletion(
            model=self.model,
            messages=litellm_messages,
            api_key=self.api_key,
            api_base=self.api_base,
            stop=stop,
            stream=True,
            **kwargs,
        )
        async for chunk in response:
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content", "")
            if content:
                yield ChatGenerationChunk(
                    message=AIMessageChunk(content=content),
                )


def _convert_message_to_dict(message: BaseMessage) -> dict:
    """Convert a LangChain ``BaseMessage`` to a litellm-compatible dict."""
    role = _ROLE_MAP.get(message.type, "user")
    content = message.content or ""
    return {"role": role, "content": content}


_ROLE_MAP: dict[str, str] = {
    "human": "user",
    "user": "user",
    "ai": "assistant",
    "assistant": "assistant",
    "system": "system",
    "function": "function",
    "tool": "tool",
}


# ---------------------------------------------------------------------------
# Model factory — provider-agnostic LLM instantiation
# ---------------------------------------------------------------------------


def _resolve_api_key() -> Optional[str]:
    """Return the first non-empty API key from all possible sources."""
    return LLM_API_KEY or OPENROUTER_API_KEY or None


_PROVIDER_API_KEY_ENVVARS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "together_ai": "TOGETHERAI_API_KEY",
    "azure": "AZURE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "cohere": "COHERE_API_KEY",
    "perplexity": "PERPLEXITYAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}


def _ensure_provider_env_vars() -> None:
    """Inject the generic ``LLM_API_KEY`` into the provider-specific env var
    so that ``litellm`` can find it without requiring the user to set both
    ``LLM_API_KEY`` *and* the provider-specific key."""
    api_key = _resolve_api_key()
    if not api_key:
        return
    provider_key_var = _PROVIDER_API_KEY_ENVVARS.get(LLM_PROVIDER)
    if provider_key_var:
        if not os.environ.get(provider_key_var):
            os.environ[provider_key_var] = api_key
    else:
        logger.warning(
            "Unknown LLM_PROVIDER '%s' — no API key variable mapped",
            LLM_PROVIDER,
        )


def _ensure_model_prefix(model_name: str) -> str:
    """Ensure the model name has a provider prefix required by ``litellm``.

    ``litellm`` requires model names in the format ``provider/model-name``
    (e.g. ``openai/gpt-4o``, ``deepseek/deepseek-chat``).  If the model
    name does not already contain a ``/``, the configured ``LLM_PROVIDER``
    is prepended automatically — preserving backward compatibility for
    users who specify just a bare model name (as was previously accepted
    by the ``ChatOpenAI`` fallback).
    """
    if "/" in model_name:
        return model_name
    provider = LLM_PROVIDER or "openai"
    prefixed = f"{provider}/{model_name}"
    logger.debug(
        "Model '%s' has no provider prefix — prepending '%s/' → '%s'",
        model_name,
        provider,
        prefixed,
    )
    return prefixed


def _create_llm_model() -> BaseChatModel:
    """Create a LangChain chat model for the configured LLM provider.

    Uses ``ChatLiteLLM`` from ``langchain_community`` (which wraps the
    ``litellm`` package) for full multi-provider support.  Falls back to
    :class:`LiteLLMWrapper` (a standalone ``BaseChatModel`` subclass that
    calls ``litellm`` directly) when ``langchain_community`` is not
    available.  As a final fallback, uses ``ChatOpenAI`` from
    ``langchain_openai`` for OpenAI-compatible providers only.
    """
    _ensure_provider_env_vars()

    raw_model_name = LLM_MODEL or OPENROUTER_MODEL
    model_name = _ensure_model_prefix(raw_model_name)
    api_key = _resolve_api_key()
    base_url = LLM_BASE_URL or OPENROUTER_BASE_URL or None

    # Try ChatLiteLLM first (full multi-provider support via litellm).
    try:
        from langchain_community.chat_models import (  # type: ignore[import-untyped]
            ChatLiteLLM,
        )

        kwargs: dict = {
            "model": model_name,
            "streaming": True,
        }
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["api_base"] = base_url

        logger.info(
            "Using ChatLiteLLM — provider=%s model=%s",
            LLM_PROVIDER,
            model_name,
        )
        return ChatLiteLLM(**kwargs)  # type: ignore[return-value]

    except ImportError:
        logger.info(
            "ChatLiteLLM not available, trying LiteLLMWrapper"
        )

    # Fallback 1: LiteLLMWrapper (standalone — calls litellm directly).
    try:
        import litellm  # noqa: F401 — verify litellm is installed

        logger.info(
            "Using LiteLLMWrapper (litellm) — provider=%s model=%s",
            LLM_PROVIDER,
            model_name,
        )
        return LiteLLMWrapper(
            model=model_name,
            api_key=api_key,
            api_base=base_url,
            streaming=True,
        )

    except ImportError:
        logger.info(
            "litellm not available, falling back to ChatOpenAI"
        )

    # Fallback 2: ChatOpenAI (OpenAI-compatible providers only).
    from langchain_openai import ChatOpenAI

    logger.info(
        "Using ChatOpenAI (OpenAI-compatible) — provider=%s model=%s",
        LLM_PROVIDER,
        raw_model_name,
    )
    return ChatOpenAI(
        model=raw_model_name,
        openai_api_key=api_key,
        openai_api_base=base_url,
        streaming=True,
    )


SYSTEM_PROMPT = (
    "You are a helpful legal document assistant. Your role is to assist "
    "users with understanding, analyzing, and summarizing legal documents. "
    "Provide clear, accurate explanations of legal terms, clauses, and "
    "concepts. When discussing legal matters, remind users that you are an "
    "AI assistant and not a substitute for professional legal advice."
)


def setup_runnable(document_context: str = "") -> None:
    """Build and store the LangChain Runnable pipeline in the user session.

    If *document_context* is provided, it is appended to the system prompt so
    that the LLM has access to the extracted document text on every call.

    If the user has configured a ``summary_language``, a language instruction
    is injected into the system prompt so that **all** LLM output (including
    general chat, section summaries, and document analysis) respects the
    user's language preference.
    """
    memory: ConversationBufferMemory = cl.user_session.get(
        "memory", ConversationBufferMemory(return_messages=True)
    )
    model = _create_llm_model()

    system_prompt = SYSTEM_PROMPT

    # Inject language instruction for all LLM output — reads the persisted
    # summary_language from the user session (set by on_chat_start or
    # on_settings_update).
    summary_lang = cl.user_session.get("summary_language")
    if summary_lang:
        display_name = SUMMARY_CODE_TO_LABEL.get(summary_lang, summary_lang.upper())
        system_prompt += (
            f"\n\n---\n"
            f"## Language Instruction\n\n"
            f"Please respond in **{display_name}** language. "
            f"All your responses must be written in {display_name}."
        )

    if document_context:
        system_prompt += (
            "\n\n---\n"
            "## Document Context\n\n"
            "The following text was extracted from a document the user "
            "uploaded. Use it as the primary source for answering any "
            "questions about the document content:\n\n"
            f"{document_context}"
        )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )
    runnable = (
        RunnablePassthrough.assign(
            history=RunnableLambda(memory.load_memory_variables) | itemgetter("history")
        )
        | prompt
        | model
        | StrOutputParser()
    )
    cl.user_session.set("llm_chain", runnable)


async def call_llm(query: str) -> Optional[str]:
    """Send a user query through the LangChain Runnable pipeline."""
    memory: ConversationBufferMemory = cl.user_session.get(
        "memory", ConversationBufferMemory(return_messages=True)
    )

    # Gather extracted text from summaries and rebuild llm_chain with
    # document context so the LLM has document knowledge on every call.
    # The chain is always rebuilt unconditionally so that a language
    # change made in on_settings_update is picked up immediately even
    # when the user sends a chat message (not just a summary request).
    summaries = cl.user_session.get("summaries", {})
    document_context = "\n\n".join(
        f"--- {key} ---\n{data.get('extracted_text', '')}"
        for key, data in summaries.items()
        if data.get("extracted_text")
    )
    setup_runnable(document_context=document_context)

    llm_chain: Runnable = cl.user_session.get("llm_chain")

    msg = cl.Message(content="", author="LatMatrix AI")

    try:
        async for chunk in llm_chain.astream(
            {"question": query},
            config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
        ):
            if chunk:
                await msg.stream_token(chunk)

        if msg.content.strip():
            from datetime import datetime

            summary_key = f"Chat Summary {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            await store_summary_in_session(
                filename=summary_key,
                summary=msg.content,
                entities=[],
                clauses=[],
            )

        await msg.send()
        memory.chat_memory.add_user_message(query)
        memory.chat_memory.add_ai_message(msg.content)
        return msg.content

    except httpx.TimeoutException:
        msg.content = (
            "\u23f1\ufe0f **Request timed out.** The LLM backend is not "
            "responding. Please try again."
        )
        await msg.send()
    except httpx.RequestError as e:
        msg.content = (
            "\U0001f50c **Connection error:** Unable to reach the "
            "LLM backend. "
            f"{str(e)}"
        )
        await msg.send()
    except Exception as e:
        msg.content = (
            "\u274c **Sorry, I encountered an error while processing your "
            "message.**\n\n"
            f"Details: {e}\n\n"
            "Please try again later or upload a document for analysis."
        )
        await msg.send()
    return None


async def load_memory_from_thread(thread: ThreadDict) -> ConversationBufferMemory:
    """Rebuild conversation memory from a thread's persisted steps."""
    memory = ConversationBufferMemory(return_messages=True)
    root_messages = [
        step for step in thread.get("steps", []) if step.get("parentId") is None
    ]
    for step in root_messages:
        role = step.get("type")
        output = step.get("output", "")
        if role == "user_message":
            memory.chat_memory.add_user_message(output)
        elif role == "assistant_message":
            memory.chat_memory.add_ai_message(output)
    return memory


async def stream_summary_analysis(
    prompt: str,
    file_name: str,
    summary_key: str,
) -> str:
    """Stream summary analysis with loading feedback."""
    memory: ConversationBufferMemory = cl.user_session.get(
        "memory", ConversationBufferMemory(return_messages=True)
    )
    # Rebuild the llm_chain with the current language setting so the section
    # summary respects the user's Summary Language preference (the cached
    # llm_chain may have a stale system prompt).
    setup_runnable()
    llm_chain: Runnable = cl.user_session.get("llm_chain")

    loading_msg = cl.Message(
        content=(
            "\u23f3 **Analyzing document...**\n\n"
            "Generating summary and extracting key information..."
        )
    )
    await loading_msg.send()

    summary_msg = cl.Message(content="", author="LatMatrix AI")

    try:
        async for chunk in llm_chain.astream(
            {"question": prompt},
            config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
        ):
            if chunk:
                await summary_msg.stream_token(chunk)

        await summary_msg.send()

        if summary_msg.content.strip():
            memory.chat_memory.add_user_message(prompt)
            memory.chat_memory.add_ai_message(summary_msg.content)

        return summary_msg.content

    except httpx.TimeoutException:
        summary_msg.content = (
            "\u23f1\ufe0f **Request timed out.** The LLM backend is not "
            "responding. Please try again."
        )
        await summary_msg.send()
        raise
    except httpx.RequestError as e:
        summary_msg.content = (
            "\U0001f50c **Connection error:** Unable to reach the LLM backend. "
            f"{str(e)}"
        )
        await summary_msg.send()
        raise
    except Exception as e:
        summary_msg.content = (
            f"\u274c **Error during analysis:** {str(e)}\n\n"
            f"Please try again or contact support."
        )
        await summary_msg.send()
        raise
