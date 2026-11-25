"""
LatMatrix Document Processor Module - File upload, parsing, and analysis.

Handles file upload validation (size, format), local document parsing via
the parser_tools, LLM-based analysis of extracted text, and FAQ-style
informational handlers.

Language instructions are now injected globally via the system prompt in
:func:`llm.setup_runnable`, so this module does not need to construct local
``lang_instruction`` strings.
"""

__all__ = [
    "handle_document_translation",
    "handle_file_upload",
    "handle_how_it_works",
    "handle_section_summary",
    "handle_supported_formats",
    "handle_upload_prompt",
    "indented_text_to_markdown",
]


import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import chainlit as cl
from .config import MAX_UPLOAD_SIZE
from .llm import call_llm, stream_summary_analysis
from .summary import offer_downloads, store_summary_in_session
from .tools.parser_tools import (
    ParserToolError,
    UnsupportedLanguageError,
    get_supported_formats,
    parse_document,
)

logger = logging.getLogger(__name__)


def indented_text_to_markdown(text: str) -> str:
    """Convert plain text with 4-space indentation to proper Markdown."""
    lines = text.splitlines()
    result = []
    for line in lines:
        if re.match(r"^ {4,}\S", line):
            result.append(f"- {line.strip()}")
        else:
            result.append(line)
    return "\n".join(result)


async def handle_section_summary(content: str) -> None:
    """Handle a request for a summary of the document sections."""
    content = (
        "In your summary please identify sections in the "
        "document text that are appropriate for apparent document type or style. "
        "Do not invent sections with descriptive names only identify sections "
        "commonly associated with the document type that are present in the "
        "document text. Clearly list the sections and explain their purpose: "
    ) + content
    try:
        await call_llm(content)
    except Exception as e:
        await cl.Message(
            content=(
                f"\u274c **Sorry, I encountered an error while summarizing "
                f"sections.**\n\nDetails: {e}\n\nPlease try again."
            ),
        ).send()


async def handle_file_upload(file: cl.File, user_prompt: str = "") -> None:
    """Handle a file uploaded as an element attached to a message."""
    msg = cl.Message(content=f"\U0001f4c4 Processing **{file.name}**...")
    await msg.send()

    try:
        # Validate file size before processing
        file_size: int = file.size or 0  # type: ignore[assignment]
        if file_size > MAX_UPLOAD_SIZE:
            msg.content = (
                f"\u274c **File too large**\n\n"
                f"`{file.name}` is **{file_size / (1024 * 1024):.1f} MB**, "
                f"which exceeds the maximum allowed size of "
                f"**{MAX_UPLOAD_SIZE // (1024 * 1024)} MB**. "
                f"Please upload a smaller file."
            )
            await msg.update()
            return

        # Validate file format
        file_ext = Path(file.name).suffix.lower()
        supported_formats = get_supported_formats()
        if file_ext not in supported_formats:
            msg.content = (
                f"\u274c **Unsupported file format**\n\n"
                f"`{file.name}` has extension `{file_ext}`, which is not supported.\n\n"
                f"**Supported formats:** {', '.join(supported_formats)}"
            )
            await msg.update()
            return

        # Update message to show parsing progress
        msg.content = (
            f"\U0001f504 Parsing document... (extracting text from `{file.name}`)"
        )
        await msg.update()

        # Read language preference from session (set by language selection UI)
        user_lang: Optional[str] = cl.user_session.get("ocr_language", None)

        # Parse the document locally using the appropriate parser
        extracted_pages, page_count, character_count, detected_lang = (
            await parse_document(
                file.path,
                use_ocr_fallback=True,
                ocr_language=user_lang,
            )
        )

        # Check if extraction was successful
        if not extracted_pages or character_count == 0:
            msg.content = (
                f"\u26a0\ufe0f **Empty document**\n\n"
                f"`{file.name}` was parsed but contains no extractable text. "
                f"This may indicate a scanned PDF without OCR, an encrypted document, "
                f"or a corrupted file."
            )
            await msg.update()
            return

        # Format extracted text for display
        full_text = "\n\n".join(extracted_pages)

        # STEP 1: Show extracted text immediately with document statistics
        lang_line = f"- **Language:** `{detected_lang}`\n" if detected_lang else ""
        extracted_text_content = (
            f"\u2705 **Text extracted from:** `{file.name}`\n\n"
            f"\U0001f4ca **Document Statistics:**\n"
            f"- **Pages:** {page_count}\n"
            f"- **Characters:** {character_count:,}\n"
            f"{lang_line}"
            f"\n### \U0001f4c4 Extracted Text\n\n"
            f"{indented_text_to_markdown(full_text)}"
        )
        msg.elements = [
            cl.Text(  # type: ignore[list-item]
                name=f"extracted-text-{file.name}",
                content=extracted_text_content,
                display="side",
            )
        ]
        await msg.update()

        # Store extracted text in session immediately
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_key = f"Document {Path(file.name).stem} {timestamp}"
        await store_summary_in_session(
            filename=summary_key,
            summary="",
            entities=[],
            clauses=[],
            extracted_text=full_text,
        )

        # STEP 2: Build the LLM prompt for analysis
        # NOTE: Language instructions are injected globally via the system
        # prompt in llm.setup_runnable(), so we don't need a local
        # lang_instruction here.
        if user_prompt:
            prompt = (
                f"The user uploaded the document **{file.name}** and asked:\n\n"
                f'"{user_prompt}"\n\n'
                f"Here is the extracted text from the document:\n\n"
                f"{full_text}\n\n"
                f"Please respond to the user's request above based on this "
                f"document content."
            )
        else:
            prompt = (
                f"Here is the extracted text from the document:\n\n"
                f"{full_text}\n\n"
                "In your summary please identify sections in the "
                "document text that are appropriate for apparent document "
                "type or style. Do not invent sections with descriptive "
                "names only identify sections commonly associated with the "
                "document type that are present in the document text. "
                "Clearly list the sections, preserving the original section "
                "numbers and identifies used in the source and explain their "
                "purpose."
            )

        # STEP 3: Stream summary analysis with loading feedback
        try:
            summary_content = await stream_summary_analysis(
                prompt=prompt,
                file_name=file.name,
                summary_key=summary_key,
            )

            # STEP 4: Update session with completed summary
            await store_summary_in_session(
                filename=summary_key,
                summary=summary_content,
                entities=[],
                clauses=[],
                extracted_text=full_text,
            )

            # Persist the summary as a cl.Text element so it survives
            # chat resume / conversation reload (Chainlit's data layer
            # auto-persists message elements to SQLite).
            summary_text_element = cl.Text(
                name=f"summary-{file.name}",
                content=summary_content,
                display="side",
            )

            # Offer download options as a standalone message (summary text is
            # already delivered by stream_summary_analysis, so no duplication).
            await offer_downloads(
                summary_key,
                file,
                summary_content=summary_content,
                elements=[summary_text_element],
            )

        except Exception as e:
            error_msg = (
                "\u274c **Sorry, I encountered an error while analyzing "
                "the document.**\n\n"
                f"Details: {e}\n\nPlease try again."
            )
            await cl.Message(content=error_msg).send()

        logger.info(
            "File upload processed successfully",
            extra={
                "file_name": file.name,
                "pages": page_count,
                "characters": character_count,
            },
        )

    except FileNotFoundError:
        msg.content = (
            "\u274c **File not found**\n\n"
            f"The uploaded file `{file.name}` could not be located. "
            "Please try uploading again."
        )
        await msg.update()
    except UnsupportedLanguageError as e:
        msg.content = (
            "\u274c **Unsupported language detected**\n\n"
            f"The document `{file.name}` appears to be in a language "
            f"that is not currently supported for OCR processing.\n\n"
            f"**Detected language:** `{e.detected_language}`\n\n"
            f"**Supported languages:** {', '.join(sorted(e.supported_languages))}\n\n"
            f"Please try uploading a document in one of the supported languages, "
            f"or contact support if you need additional language support."
        )
        await msg.update()
        logger.warning(
            "Unsupported language detected during file upload",
            extra={
                "file_name": file.name,
                "detected_language": e.detected_language,
            },
        )
    except ParserToolError as e:
        msg.content = (
            "\u274c **Parsing error**\n\n"
            f"Failed to parse `{file.name}`:\n\n"
            f"```\n{str(e)}\n```"
        )
        await msg.update()
        logger.error(
            "Parser tool error",
            extra={"file_name": file.name, "error": str(e)},
            exc_info=True,
        )
    except Exception as e:
        msg.content = (
            "\u274c **Unexpected error**\n\n"
            f"An unexpected error occurred while processing `{file.name}`:\n\n"
            f"```\n{str(e)}\n```"
        )
        await msg.update()
        logger.error(
            "Unexpected error during file upload",
            extra={"file_name": file.name, "error": str(e)},
            exc_info=True,
        )


async def handle_how_it_works() -> None:
    """Explain the LatMatrix document analysis workflow."""
    await cl.Message(
        content=(
            "### \U0001f52c How LatMatrix Works\n\n"
            "1. **Upload** a legal document (PDF, DOCX, or TXT)\n"
            "2. **Extract** text locally using intelligent parsers:\n"
            "   - Digital PDFs: Direct text extraction\n"
            "   - Scanned PDFs: OCR (Tesseract) with fallback\n"
            "   - Word documents: Paragraph and table extraction\n"
            "   - Text files: Encoding detection and parsing\n"
            "3. **Display** extracted text in clean Markdown format\n"
            "4. **Analyze** with AI for entities, clauses, and summaries\n\n"
            "Text extraction happens **instantly within Chainlit** \u2014 "
            "no backend round-trip needed. Extracted text is then available "
            "for downstream analysis and summarization."
        )
    ).send()


async def handle_document_translation() -> None:
    """Stub handler for document translation requests.

    Placeholder that acknowledges the feature and informs users
    that full translation support is coming soon.
    """
    await cl.Message(
        content=(
            "\U0001f30d **Document Translation**\n\n"
            "Translation support is on its way! In a future update you will be "
            "able to translate entire documents into your chosen language while "
            "preserving the original formatting.\n\n"
            "For now, you can ask me to explain or summarise sections of a "
            "document in a specific language using the **Summary Language** "
            "setting in the sidebar."
        )
    ).send()


async def handle_supported_formats() -> None:
    """List supported document formats."""
    supported = ", ".join(get_supported_formats())
    await cl.Message(
        content=(
            "### \U0001f4cb Supported Document Formats\n\n"
            "- **PDF** (.pdf) \u2014 Digital and scanned PDFs with OCR fallback\n"
            "- **Word** (.docx, .doc) \u2014 Microsoft Word documents\n"
            "- **Text** (.txt, .md) \u2014 Plain text and Markdown files\n\n"
            f"**Supported extensions:** {supported}\n\n"
            f"**Maximum file size:** "
            f"{MAX_UPLOAD_SIZE // (1024 * 1024)} MB\n\n"
            "**Note:** Scanned PDFs are automatically detected and "
            "processed with OCR (Tesseract)."
        )
    ).send()


async def handle_upload_prompt() -> None:
    """Prompt the user to upload a document."""
    await cl.Message(
        content=(
            "\U0001f4e4 **Ready to upload!**\n\n"
            "Use the file upload button (paperclip icon) in the chat input area "
            "to select a PDF, DOCX, or TXT document for analysis."
        )
    ).send()
