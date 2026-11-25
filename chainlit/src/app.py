"""LatMatrix Chainlit Application - Thin Wiring Layer.

This module is the Chainlit entry point. It connects lifecycle decorators
to modules that each own a single concern:

- ``auth`` — Password and OAuth authentication, logout
- ``database`` — SQLite data layer configuration and schema setup
- ``llm`` — LangChain runnable pipeline, LLM call, memory management
- ``document_processor`` — File upload, parsing, and analysis orchestration
- ``summary`` — Summary generation, storage, and download callbacks
"""

import logging
import os
import tomllib
from typing import Optional

import chainlit as cl
from chainlit.data import get_data_layer
from chainlit.types import ThreadDict
from chainlit.input_widget import Select
from langchain_classic.memory import ConversationBufferMemory

from .config import OCR_LABEL_TO_CODE, SUMMARY_LABEL_TO_CODE

# Import is required to register the data layer and auth decorators.
from . import (
    auth,
)  # registers @cl.password_auth_callback, @cl.oauth_callback, @cl.on_logout

auth  # To prevent removal of unused imports
from .document_processor import (
    handle_document_translation,
    handle_file_upload,
    handle_section_summary,
)
from .llm import call_llm, load_memory_from_thread, setup_runnable
from .summary import reload_summaries_from_db
from .heuristics import is_section_summary_request, is_translation_request

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User metadata persistence helpers
# ---------------------------------------------------------------------------


async def _persist_user_language(
    user: cl.User, summary_language: Optional[str]
) -> None:
    """Persist the *summary_language* to the user's metadata in the database.

    Uses ``SQLAlchemyDataLayer.create_user()`` which already handles upsert
    — if the user exists, it runs ``UPDATE users SET metadata = ...``.
    """
    dl = get_data_layer()
    if dl is None:
        logger.warning("Data layer not available — cannot persist language setting")
        return

    # Fetch existing user to merge metadata
    existing = await dl.get_user(user.identifier)
    metadata = dict(existing.metadata) if existing and existing.metadata else {}
    metadata["summary_language"] = summary_language

    # Update user metadata via create_user (which upserts)
    updated_user = cl.User(
        identifier=user.identifier,
        metadata=metadata,
    )
    await dl.create_user(updated_user)
    logger.info(
        "Persisted summary_language=%s for user=%s",
        summary_language,
        user.identifier,
    )


async def _load_user_language(user: cl.User) -> Optional[str]:
    """Load the persisted *summary_language* from the user's database metadata.

    Returns:
        The ISO 639-1 language code (e.g. ``"fr"``), or ``None`` if no
        language has been set (auto-detect).
    """
    dl = get_data_layer()
    if dl is None:
        logger.warning("Data layer not available — cannot load language setting")
        return None

    existing = await dl.get_user(user.identifier)
    if existing and existing.metadata:
        lang = existing.metadata.get("summary_language")
        logger.info(
            "Loaded summary_language=%s for user=%s",
            lang,
            user.identifier,
        )
        return lang
    return None


def _resolve_summary_initial_index(persisted_lang: Optional[str]) -> int:
    """Return the dropdown index for a persisted summary language code.

    Returns ``0`` (``"Detect Automatically"``) when *persisted_lang* is
    ``None``, or looks up the position of the matching label in
    ``SUMMARY_LABEL_TO_CODE``.
    """
    if not persisted_lang:
        return 0
    labels: list[str] = list(SUMMARY_LABEL_TO_CODE.keys())
    for label, code in SUMMARY_LABEL_TO_CODE.items():
        if code == persisted_lang:
            return labels.index(label)
    return 0


# Read the default theme from Chainlit's config.toml so it can be passed
# to custom elements that need to know the active theme at render time.
_CHAINLIT_CONFIG = os.path.join(
    os.path.dirname(__file__), "..", ".chainlit", "config.toml"
)
try:
    with open(_CHAINLIT_CONFIG, "rb") as _f:
        _cfg = tomllib.load(_f)
    _DEFAULT_THEME: str = _cfg.get("UI", {}).get("default_theme", "light")
except (FileNotFoundError, tomllib.TOMLDecodeError):
    _DEFAULT_THEME = "light"


# ---------------------------------------------------------------------------
# Starters (UI suggestion buttons shown before the first message)
# ---------------------------------------------------------------------------


@cl.set_starters
async def set_starters() -> list[cl.Starter]:
    """Define clickable starter suggestions in the chat UI.

    These appear as labelled buttons above the message input before the
    first user message is sent.  Each starter pre-fills the input with a
    descriptive message and sends it on click.
    """
    return [
        cl.Starter(
            label="Summarise document sections",
            message=(
                "Please summarise the document sections. Identify sections "
                "commonly associated with the document type that are present "
                "in the text. List the sections and explain their purpose."
            ),
            icon="/public/favicon.png",
        ),
        cl.Starter(
            label="Translate document",
            message="Can you translate this document?",
            icon="/public/favicon.png",
        ),
    ]


# ---------------------------------------------------------------------------
# Chat Lifecycle Hooks
# ---------------------------------------------------------------------------


@cl.on_chat_start
async def on_chat_start() -> None:
    """Initialise memory, runnable, and language settings for a new chat session.

    Loads the user's persisted ``summary_language`` from the database (if set)
    and restores it in the user session and the ChatSettings widget.
    """
    user = cl.user_session.get("user")
    user_id = getattr(user, "identifier", "unknown")
    logger.info(f"{user_id} has started the conversation")

    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))
    setup_runnable()

    # Load persisted summary language from the database
    persisted_lang = await _load_user_language(user) if user else None
    cl.user_session.set("ocr_language", None)
    cl.user_session.set("summary_language", persisted_lang)

    # Determine initial indices for the ChatSettings Select widgets
    summary_initial = _resolve_summary_initial_index(persisted_lang)

    # Create the ChatSettings form with language selector dropdowns
    await cl.ChatSettings(
        [  # type: ignore[arg-type]
            Select(
                id="OCR_Language",
                label="OCR Language",
                description="Language for text recognition in scanned documents",
                values=[
                    "Detect Automatically",
                    "English",
                    "Hindi",
                    "French",
                    "Spanish",
                    "German",
                ],
                initial_index=0,
            ),
            Select(
                id="Summary_Language",
                label="Summary Language",
                description="Language for AI-generated document summaries",
                values=[
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
                ],
                initial_index=summary_initial,
            ),
        ]
    ).send()

    # Track whether the first user message has been sent.
    cl.user_session.set("first_message_received", False)


@cl.on_settings_update
async def on_settings_update(settings: dict) -> None:
    """Persist language selections from ChatSettings to the user session and DB.

    When the user changes the summary language in the sidebar, the selection
    is stored in both the in-memory session *and* the user's metadata in the
    SQLite ``users`` table so it survives conversation restarts.

    The LLM chain is also rebuilt so the system prompt picks up the new
    language instruction immediately — without waiting for the next message.
    """
    ocr_label = settings.get("OCR_Language", "Detect Automatically")
    summary_label = settings.get("Summary_Language", "Detect Automatically")

    # Use the centralised label-to-code mappings from config
    cl.user_session.set("ocr_language", OCR_LABEL_TO_CODE.get(ocr_label))
    summary_lang = SUMMARY_LABEL_TO_CODE.get(summary_label)
    cl.user_session.set("summary_language", summary_lang)

    # Rebuild the LLM chain so the system prompt includes the updated
    # language instruction.  Without this, the cached llm_chain still
    # has the stale system prompt from on_chat_start(), and downstream
    # callers like stream_summary_analysis() would not respect the new
    # language setting.
    if cl.user_session.get("llm_chain") is not None:
        setup_runnable()

    # Persist the summary_language to the database so it survives restarts
    user = cl.user_session.get("user")
    if user:
        await _persist_user_language(user, summary_lang)

    logger.info(
        "Language settings updated",
        extra={
            "ocr_language": cl.user_session.get("ocr_language"),
            "summary_language": summary_lang,
        },
    )


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict) -> None:
    """Reload conversation history and document data when resuming a thread.

    Restores conversation memory from persisted thread steps, re-initialises
    the LLM runnable pipeline (including extracted document context so the
    LLM can answer questions about previously uploaded documents), rebuilds
    the ``summaries`` session dict from the ``elements`` SQLite table, and
    restores the user's language preference from the database.
    """
    memory = await load_memory_from_thread(thread)
    cl.user_session.set("memory", memory)

    # Restore language setting from DB metadata on resume
    user = cl.user_session.get("user")
    if user:
        persisted_lang = await _load_user_language(user)
        cl.user_session.set("summary_language", persisted_lang)
    else:
        cl.user_session.set("summary_language", None)

    # Rebuild the summaries dict from persisted elements in the SQLite table.
    thread_id = thread.get("id")
    document_context = ""
    if thread_id:
        summaries = await reload_summaries_from_db(thread_id)
        if summaries:
            cl.user_session.set("summaries", summaries)
            # Build document context from extracted text so the LLM runnable
            # can inject it into the system prompt on resume.
            document_context = "\n\n".join(
                f"--- {key} ---\n{data.get('extracted_text', '')}"
                for key, data in summaries.items()
                if data.get("extracted_text")
            )
            logger.info(
                "Restored %d document entries from elements on chat resume",
                len(summaries),
            )

    setup_runnable(document_context=document_context)


async def _send_header_elements() -> None:
    """Send the TitleHeader custom element in a zero-width message.

    The element is rendered on the first user message so it
    appear simultaneously in the top bar.  The TitleHeader receives the
    configured default theme so it can render the appropriate title logo
    (title_light.png or title_dark.png).
    """
    title_element = cl.CustomElement(
        name="TitleHeader",
        props={
            "theme": _DEFAULT_THEME,
        },
        display="inline",
    )
    await cl.Message(content="\u200c", elements=[title_element]).send()


# Heuristic functions (_is_section_summary_request, _is_translation_request)
# are imported from .heuristics above.


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Route incoming messages to file processing or LLM chat.

    On the first user message, the Title element is registered (deferred
    from chat start).  Subsequent messages are routed to the appropriate
    handler based on content heuristics or forwarded to the LLM.
    """
    first_message = not cl.user_session.get("first_message_received", False)
    if first_message:
        cl.user_session.set("first_message_received", True)
        await _send_header_elements()

    # --- File uploads ---
    if message.elements:
        user_prompt = message.content.strip()
        for file in message.elements:
            await handle_file_upload(file, user_prompt=user_prompt)
        return

    content = message.content.strip()

    # --- Stub: Section summary request ---
    if is_section_summary_request(content):
        await handle_section_summary(content)
        return

    # --- Stub: Document translation request ---
    if is_translation_request(content):
        await handle_document_translation()
        return

    # --- Default: route to LLM chat ---
    await call_llm(content)


@cl.on_stop
def on_stop() -> None:
    """Handle user stop requests."""
    print("[chainlit] User requested stop")


@cl.on_chat_end
def on_chat_end() -> None:
    """Clean up when a chat session ends."""
    user = cl.user_session.get("user")
    user_id = getattr(user, "identifier", "unknown")
    logger.info(f"{user_id} has ended the chat")
