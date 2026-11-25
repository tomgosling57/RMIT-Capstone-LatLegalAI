"""
LLM Backend Abstraction Layer
Based on the prototype implementation with improvements for the backend service.
"""

from __future__ import annotations
import os
import re
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional
from openai import APIConnectionError, APIStatusError, APITimeoutError
import anthropic


def _get_max_tokens() -> int:
    """
    Read the ``LLM_MAX_TOKENS`` environment variable and return its value.

    Falls back to ``16384`` when the variable is unset, empty, or not a valid
    integer.

    Returns:
        Maximum number of tokens the LLM should generate per call.
    """
    raw = os.environ.get("LLM_MAX_TOKENS", "").strip()
    if raw.isdigit():
        return int(raw)
    return 16384


class LLMBackend(ABC):
    """
    Abstract base class for LLM providers.
    Subclass this and implement complete(prompt) to add a new backend.
    """

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Send a prompt to the LLM and return the response."""
        ...

    def summarise(
        self,
        text: str,
        target_language: Optional[str] = None,
        pre_extracted_entities: Optional[dict] = None,
    ) -> str:
        """
        Generate a comprehensive summary of the provided legal text
        and extract key entities.

        Args:
            text: Legal text to summarize
            target_language: Optional language code for translation (e.g., 'es', 'fr')
                            If provided, the summary will be generated in that language.
            pre_extracted_entities: Optional dict of entities already extracted by
                                   the NLP pipeline (spaCy NER). When provided, these
                                   are included in the prompt so the LLM can focus
                                   on summarization rather than re-discovering entities.

        Returns:
            Combined summary and entities in format: "Summary: [summary]\n
            Entities: [entity1, entity2, ...]"
        """
        # Add logging for summarisation request
        from logging_config import get_logger

        logger = get_logger(__name__)
        logger.debug(
            f"Starting summarisation with backend: {self.__class__.__name__}",
            extra={
                "backend": self.__class__.__name__,
                "target_language": target_language,
                "text_length": len(text),
            },
        )
        # Build the entities context block if pre-extracted entities are available
        entities_context = ""
        if pre_extracted_entities:
            parts = []
            names = pre_extracted_entities.get("names", [])
            dates = pre_extracted_entities.get("dates", [])
            locations = pre_extracted_entities.get("locations", [])
            if names:
                parts.append(
                    "Parties/Organisations: " + ", ".join(e["text"] for e in names)
                )
            if dates:
                parts.append("Dates: " + ", ".join(e["text"] for e in dates))
            if locations:
                parts.append("Locations: " + ", ".join(e["text"] for e in locations))
            if parts:
                entities_context = (
                    "\n\nPre-extracted entities (use these to inform your summary):\n"
                    + "\n".join(parts)
                )

        if target_language:
            prompt = (
                f"You are a legal document expert who understands both "
                f"English and {target_language}.\n"
                f"TASK: Read this legal document and:\n"
                f"1. Understand the legal context, definitions, and nuances\n"
                f"2. Generate a comprehensive, detailed summary IN {target_language}\n"
                f"3. Extract key entities (names, organizations, dates, locations)\n"
                f"4. Preserve all legal definitions and precise meanings\n"
                f"5. Note any untranslatable legal concepts\n\n"
                f"DOCUMENT TEXT:\n{text}\n"
                f"{entities_context}\n\n"
                f"Provide your response in the following format:\n"
                f"SUMMARY: [your detailed summary here — cover all key clauses, "
                f"obligations, rights, and terms]\n"
                f"ENTITIES: [comma-separated list of entities]"
            )
        else:
            prompt = (
                "You are a legal document expert who translates complex legal "
                "documents into plain English.\n"
                "Read the following legal document text and write a "
                "comprehensive, detailed summary "
                "in plain English that anyone can understand — no legal jargon.\n"
                "Cover all of the following in your summary:\n"
                "1. The purpose and nature of the agreement\n"
                "2. Key obligations and responsibilities of each party\n"
                "3. Important dates, deadlines, and timeframes\n"
                "4. Financial terms (amounts, fees, payments)\n"
                "5. Rights and permissions granted\n"
                "6. Risks, liabilities, and termination conditions\n"
                "7. Any special conditions or notable clauses\n\n"
                "Use clear section headings and short paragraphs. "
                "Be thorough — do not leave out important details.\n"
                "Also extract key entities (names, organizations, "
                "dates, locations) mentioned in the text.\n\n"
                f"DOCUMENT TEXT:\n{text}\n"
                f"{entities_context}\n\n"
                "Provide your response in the following format:\n"
                "SUMMARY: [your comprehensive summary here — cover all key clauses, "
                "obligations, rights, and terms]\n"
                "ENTITIES: [comma-separated list of entities]"
            )
        try:
            response = self.complete(prompt)
            logger.debug(f"LLM response received from {self.__class__.__name__}")

            # Parse the response to extract summary and entities
            summary = ""
            entities = ""
            trailing_content: list[str] = []

            # Split response by lines and look for the expected sections
            lines = response.split("\n")
            summary_section = False
            entities_section = False

            for line in lines:
                line = line.strip()
                # Handle both "SUMMARY:" and "**SUMMARY:**" (markdown bold) formats
                if re.match(r"\*{0,2}SUMMARY\*{0,2}\s*:", line):
                    summary = re.sub(r"^\*{0,2}SUMMARY\*{0,2}\s*:\s*", "", line).strip()
                    summary_section = True
                    entities_section = False
                elif re.match(r"\*{0,2}ENTITIES\*{0,2}\s*:", line):
                    entities = re.sub(
                        r"^\*{0,2}ENTITIES\*{0,2}\s*:\s*", "", line
                    ).strip()
                    entities_section = True
                    summary_section = False
                elif summary_section and not entities_section:
                    # If we're in the summary section and encounter a new section, stop
                    if re.match(r"\*{0,2}(SUMMARY|ENTITIES)\*{0,2}\s*:", line):
                        continue
                    # Otherwise, append to the summary
                    if summary:
                        summary += "\n" + line
                    else:
                        summary = line
                elif entities_section:
                    # If we're in the entities section, accumulate lines
                    if entities:
                        entities += "\n" + line
                    else:
                        entities = line
                elif not summary_section and not entities_section:
                    # Content before any recognised section header — log as unexpected
                    logger.warning(
                        "LLM response contains content before SUMMARY section: "
                        f"{line[:200]}",
                        extra={
                            "backend": self.__class__.__name__,
                        },
                    )

            # Check for content after the ENTITIES section by looking for
            # lines that appear after the last ENTITIES header but are not
            # part of the entities content itself (e.g. a trailing "---" or
            # "NOTES:" block).  We detect this by scanning backwards from
            # the end of the response for a second ENTITIES header.
            last_entities_idx = -1
            for i, line in enumerate(lines):
                if re.match(r"\*{0,2}ENTITIES\*{0,2}\s*:", line.strip()):
                    last_entities_idx = i
            if last_entities_idx >= 0:
                # Lines after the ENTITIES header line that are not blank
                # and don't look like continuation of the entities list
                # are treated as trailing/unexpected content.
                for line in lines[last_entities_idx + 1 :]:
                    stripped = line.strip()
                    if stripped and not re.match(
                        r"^[\w\s,.\-–—/()&;:'\"«»]+$", stripped
                    ):
                        trailing_content.append(stripped)

            if trailing_content:
                logger.warning(
                    "LLM response contains unexpected content after ENTITIES section: "
                    f"{' '.join(trailing_content)[:500]}",
                    extra={
                        "backend": self.__class__.__name__,
                    },
                )

            # If parsing didn't work as expected, return the raw response
            if not summary and not entities:
                return response

            result = f"Summary: {summary}\nEntities: {entities}"
            if trailing_content:
                result += "\n\n[Note: The LLM also returned additional content "
                "after the entities section that could not be parsed into the"
                "standard format. Review the raw response for details.]"
            return result

        except Exception as e:
            # LLM backend failed - return partial result with extracted text
            # This allows graceful degradation when LLM is unavailable
            logger.error(
                f"LLM backend error during summarisation: {str(e)}",
                exc_info=True,
                extra={
                    "backend": self.__class__.__name__,
                    "error_type": type(e).__name__,
                },
            )
            # Return a note that summarisation is unavailable
            return (
                "Summary: [LLM summarisation is currently unavailable. "
                "Please try again later.]\n"
                "Entities: [Summarisation service is offline]"
            )


class OpenAIBackend(LLMBackend):
    """OpenAI backend. Requires: pip install openai | OPENAI_API_KEY env var."""

    def __init__(self, model: str = "gpt-4o-mini"):
        from openai import OpenAI

        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model

    def complete(self, prompt: str) -> str:
        max_tokens = _get_max_tokens()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return str(response.choices[0].message.content.strip())


class AnthropicBackend(LLMBackend):
    """Anthropic backend.
    Requires: pip install anthropic | ANTHROPIC_API_KEY env var."""

    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 1  # seconds

    def __init__(self, model: Optional[str] = None):
        import anthropic

        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model or os.environ.get(
            "ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"
        )

    def complete(self, prompt: str) -> str:
        """
        Send a prompt to the Anthropic LLM and return the response.

        Implements specific error handling for common API issues:
        - 401 Unauthorized: Invalid API key
        - 429 Too Many Requests: Retry with exponential backoff
        - 400, 413, 422: Invalid requests
        - Network errors: General connection issues

        Returns:
            str: The response from the LLM

        Raises:
            Exception: With descriptive messages for various error types
        """
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                max_tokens = _get_max_tokens()
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return str(message.content[0].text.strip())

            except anthropic.APIStatusError as e:
                # Handle HTTP status errors
                if e.status_code == 401:
                    # Authentication error - invalid API key
                    raise Exception(
                        "Anthropic API authentication failed. "
                        "Please check that your ANTHROPIC_API_KEY "
                        "is valid and has not expired. "
                        f"Error: {e.message}"
                    )

                elif e.status_code == 429:
                    # Rate limit error - implement retry with exponential backoff
                    if attempt < self.MAX_RETRIES:
                        delay = self.RETRY_DELAY_BASE * (2**attempt)
                        logging.warning(
                            f"Anthropic API rate limited (429).\n"
                            f"Retrying in {delay}s... "
                            f"Attempt {attempt + 1}/{self.MAX_RETRIES}"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception(
                            "Anthropic API rate limit exceeded after"
                            " maximum retries. "
                            "Please reduce the frequency of your requests or "
                            "upgrade your plan. "
                            f"Error: {e.message}"
                        )

                elif e.status_code in [400, 413, 422]:
                    # Client error - invalid request
                    error_msg = {
                        400: "Bad Request - Invalid request parameters or malformed "
                        "input",
                        413: "Payload Too Large - Request payload exceeds size limits",
                        422: "Unprocessable Entity - Semantic validation failure",
                    }[e.status_code]
                    raise Exception(
                        f"Anthropic API {error_msg}. "
                        f"Please check your input and try again. Error: {e.message}"
                    )

                else:
                    # Other HTTP status errors
                    raise Exception(
                        f"Anthropic API error {e.status_code}: " f"{e.message}"
                    )

            except anthropic.APIConnectionError:
                # Handle connection errors
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY_BASE * (2**attempt)
                    logging.warning(
                        f"Anthropic API connection error. Retrying in {delay}s... "
                        f"Attempt {attempt + 1}/{self.MAX_RETRIES}"
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(
                        "Anthropic API connection failed after maximum retries. "
                        "Please check your network connection and API key."
                    )

            except anthropic.APITimeoutError:
                # Handle timeout errors
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY_BASE * (2**attempt)
                    logging.warning(
                        f"Anthropic API timeout. Retrying in "
                        f"{delay}s... "
                        f"Attempt {attempt + 1}/{self.MAX_RETRIES}"
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(
                        "Anthropic API timed out after maximum retries. "
                        "Please check your network connection and try again."
                    )

            except Exception as e:
                # Handle any other unexpected errors
                raise Exception(
                    f"Unexpected error communicating with " f"Anthropic API: {str(e)}"
                )

        # This should never be reached, but added for completeness
        raise Exception(
            "Failed to get response from Anthropic " "API after all retries"
        )


class OllamaBackend(LLMBackend):
    """
    Local inference via Ollama (https://ollama.com).
    Requires Ollama running locally. Set OLLAMA_MODEL
    env var (default: llama3).
    """

    def __init__(
        self, model: Optional[str] = None, base_url: str = "http://localhost:11434"
    ):
        import requests

        self._requests = requests
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3")
        self.base_url = base_url

    def complete(self, prompt: str) -> str:
        response = self._requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return str(response.json()["response"].strip())


class OpenRouterBackend(LLMBackend):
    """
    OpenRouter backend (https://openrouter.ai).

    Routes requests to 200+ models from OpenAI, Anthropic, Google, Meta and
    others via a single OpenAI-compatible API endpoint.

    Requirements:
        pip install openai          # reuses the openai SDK
        OPENROUTER_API_KEY env var  # API key from https://openrouter.ai/keys

    Optional env vars:
        OPENROUTER_MODEL            # default: "openai/gpt-4o-mini"
        OPENROUTER_SITE_URL         # sent as HTTP-Referer header (recommended)
        OPENROUTER_SITE_NAME        # sent as X-Title header (recommended)

    Example models:
        "openai/gpt-4o-mini"
        "anthropic/claude-3.5-haiku"
        "google/gemini-flash-1.5"
        "meta-llama/llama-3.1-8b-instruct:free"
    """

    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "openai/gpt-4o-mini"
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 1  # seconds

    def __init__(
        self,
        model: Optional[str] = None,
        site_url: Optional[str] = None,
        site_name: Optional[str] = None,
    ):
        from openai import OpenAI

        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENROUTER_API_KEY environment variable is not set. "
                "Get a key at https://openrouter.ai/keys"
            )

        self.model = model or os.environ.get("OPENROUTER_MODEL") or self.DEFAULT_MODEL

        # OpenRouter recommends passing Referer / X-Title for usage analytics.
        default_headers: dict[str, str] = {}
        resolved_site_url = site_url or os.environ.get("OPENROUTER_SITE_URL")
        resolved_site_name = site_name or os.environ.get("OPENROUTER_SITE_NAME")
        if resolved_site_url:
            default_headers["HTTP-Referer"] = resolved_site_url
        if resolved_site_name:
            default_headers["X-Title"] = resolved_site_name

        self.client = OpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
            default_headers=default_headers or None,
        )

    def complete(self, prompt: str) -> str:
        """
        Send a prompt to the OpenRouter LLM and return the response.

        Implements specific error handling for common API issues:
        - 401 Unauthorized: Invalid API key
        - 429 Too Many Requests: Retry with exponential backoff
        - 400, 413, 422: Invalid requests
        - 402 Payment Required: Insufficient credits
        - 5xx Server errors: Retry with exponential backoff
        - Network errors: General connection issues

        Returns:
            str: The response from the LLM

        Raises:
            Exception: With descriptive messages for various error types
        """
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                max_tokens = _get_max_tokens()
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3,
                )
                return str(response.choices[0].message.content.strip())

            except APIStatusError as e:
                # Handle HTTP status errors
                if e.status_code == 401:
                    # Authentication error - invalid API key
                    raise Exception(
                        "OpenRouter API authentication failed. "
                        "Please check that your OPENROUTER_API_KEY "
                        "is valid and has not expired. "
                        f"Error: {e.message}"
                    )

                elif e.status_code == 402:
                    # Payment required error - insufficient credits
                    raise Exception(
                        "OpenRouter API request failed due to insufficient credits. "
                        "Please verify your account has sufficient credits "
                        "or upgrade your plan. "
                        f"Error: {e.message}"
                    )

                elif e.status_code == 429:
                    # Rate limit error - implement retry with exponential backoff
                    if attempt < self.MAX_RETRIES:
                        delay = self.RETRY_DELAY_BASE * (2**attempt)
                        logging.warning(
                            f"OpenRouter API rate limited (429).\n"
                            f"Retrying in {delay}s... "
                            f"Attempt {attempt + 1}/{self.MAX_RETRIES}"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception(
                            "OpenRouter API rate limit exceeded after"
                            " maximum retries. "
                            "Please reduce the frequency of your requests or "
                            "upgrade your plan. "
                            f"Error: {e.message}"
                        )

                elif e.status_code in [400, 413, 422]:
                    # Client error - invalid request
                    error_msg = {
                        400: "Bad Request - Invalid request parameters or malformed "
                        "input",
                        413: "Payload Too Large - Request payload exceeds size limits",
                        422: "Unprocessable Entity - Semantic validation failure",
                    }[e.status_code]
                    raise Exception(
                        f"OpenRouter API {error_msg}. "
                        f"Please check your input and try again. Error: {e.message}"
                    )

                elif e.status_code in [500, 502, 503]:
                    # Server error - retry with exponential backoff
                    if attempt < self.MAX_RETRIES:
                        delay = self.RETRY_DELAY_BASE * (2**attempt)
                        logging.warning(
                            f"OpenRouter API server error ({e.status_code}). "
                            f"Retrying in {delay}s... Attempt {attempt + 1}/"
                            f"{self.MAX_RETRIES}"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception(
                            f"OpenRouter API server error ({e.status_code}) "
                            f"after maximum retries. "
                            f"Please try again later or contact support. Error: "
                            + e.message
                        )

                else:
                    # Other HTTP status errors
                    raise Exception(
                        f"OpenRouter API error {e.status_code}: " f"{e.message}"
                    )

            except APITimeoutError:
                # Handle timeout errors
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY_BASE * (2**attempt)
                    logging.warning(
                        f"OpenRouter API timeout. Retrying in "
                        f"{delay}s... "
                        f"Attempt {attempt + 1}/{self.MAX_RETRIES}"
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(
                        "OpenRouter API timed out after maximum retries. "
                        "Please check your network connection and try again."
                    )

            except APIConnectionError:
                # Handle connection errors
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY_BASE * (2**attempt)
                    logging.warning(
                        f"OpenRouter API connection error. Retrying in {delay}s... "
                        f"Attempt {attempt + 1}/{self.MAX_RETRIES}"
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(
                        "OpenRouter API connection failed after maximum retries. "
                        "Please check your network connection and API key."
                    )

            except Exception as e:
                # Handle any other unexpected errors
                raise Exception(
                    f"Unexpected error communicating with " f"OpenRouter API: {str(e)}"
                )

        # This should never be reached, but added for completeness
        raise Exception(
            "Failed to get response from OpenRouter " "API after all retries"
        )


class OpenRouterMistralBackend(OpenRouterBackend):
    """
    OpenRouter backend specifically tuned for Mistral Small 24B Instruct.

    This backend extends ``OpenRouterBackend`` and overrides the
    ``summarise()`` method to handle the markdown-heading response format
    (``### SUMMARY`` / ``### ENTITIES``) that Mistral models commonly return,
    in addition to the standard ``SUMMARY:`` / ``ENTITIES:`` format.

    Usage
    -----
    Set ``LLM_BACKEND=openrouter-mistral`` in your ``.env`` file.
    The model is still controlled via ``OPENROUTER_MODEL`` (defaults to
    ``mistralai/mistral-small-24b-instruct-2501``).
    """

    def summarise(
        self,
        text: str,
        target_language: Optional[str] = None,
        pre_extracted_entities: Optional[dict] = None,
    ) -> str:
        """
        Generate a comprehensive summary, handling Mistral's markdown-heading
        response format (``### SUMMARY`` / ``### ENTITIES``).

        Args:
            text: Legal text to summarize
            target_language: Optional language code for translation
            pre_extracted_entities: Optional dict of pre-extracted entities

        Returns:
            Combined summary and entities in format:
            "Summary: [summary]\nEntities: [entity1, entity2, ...]"
        """
        from logging_config import get_logger

        logger = get_logger(__name__)
        logger.debug(
            f"Starting summarisation with backend: {self.__class__.__name__}",
            extra={
                "backend": self.__class__.__name__,
                "target_language": target_language,
                "text_length": len(text),
            },
        )

        # Build the entities context block if pre-extracted entities are available
        entities_context = ""
        if pre_extracted_entities:
            parts = []
            names = pre_extracted_entities.get("names", [])
            dates = pre_extracted_entities.get("dates", [])
            locations = pre_extracted_entities.get("locations", [])
            if names:
                parts.append(
                    "Parties/Organisations: " + ", ".join(e["text"] for e in names)
                )
            if dates:
                parts.append("Dates: " + ", ".join(e["text"] for e in dates))
            if locations:
                parts.append("Locations: " + ", ".join(e["text"] for e in locations))
            if parts:
                entities_context = (
                    "\n\nPre-extracted entities (use these to inform your summary):\n"
                    + "\n".join(parts)
                )

        if target_language:
            prompt = (
                f"You are a legal document expert who understands both "
                f"English and {target_language}.\n"
                f"TASK: Read this legal document and:\n"
                f"1. Understand the legal context, definitions, and nuances\n"
                f"2. Generate a comprehensive, detailed summary IN "
                f"{target_language}\n"
                f"3. Extract key entities (names, organizations, dates, locations)\n"
                f"4. Preserve all legal definitions and precise meanings\n"
                f"5. Note any untranslatable legal concepts\n\n"
                f"DOCUMENT TEXT:\n{text}\n"
                f"{entities_context}\n\n"
                "Provide your response in the following format:\n"
                "SUMMARY: [your detailed summary here]\n"
                "ENTITIES: [comma-separated list of entities]"
            )
        else:
            prompt = (
                "You are a legal document expert who translates complex legal "
                "documents into plain English.\n"
                "Read the following legal document text and write a "
                "comprehensive, detailed summary "
                "in plain English that anyone can understand — no legal jargon.\n"
                "Cover all of the following in your summary:\n"
                "1. The purpose and nature of the agreement\n"
                "2. Key obligations and responsibilities of each party\n"
                "3. Important dates, deadlines, and timeframes\n"
                "4. Financial terms (amounts, fees, payments)\n"
                "5. Rights and permissions granted\n"
                "6. Risks, liabilities, and termination conditions\n"
                "7. Any special conditions or notable clauses\n\n"
                "Use clear section headings and short paragraphs. "
                "Be thorough — do not leave out important details.\n"
                "Also extract key entities (names, organizations, "
                "dates, locations) mentioned in the text.\n\n"
                f"DOCUMENT TEXT:\n{text}\n"
                f"{entities_context}\n\n"
                "Provide your response in the following format:\n"
                "SUMMARY: [your comprehensive summary here]\n"
                "ENTITIES: [comma-separated list of entities]"
            )

        try:
            response = self.complete(prompt)
            logger.debug(f"LLM response received from {self.__class__.__name__}")

            # Parse the response to extract summary and entities.
            # Mistral models commonly return markdown headings like:
            #   ### SUMMARY
            #   ...content...
            #   ### ENTITIES
            #   ...entities...
            # This parser handles both that format and the standard
            # SUMMARY: / ENTITIES: format.
            summary = ""
            entities = ""
            trailing_content: list[str] = []

            lines = response.split("\n")
            summary_section = False
            entities_section = False

            # Match patterns:
            #   "SUMMARY:", "**SUMMARY:**", "### SUMMARY", "## SUMMARY",
            #   "### SUMMARY:", "## **SUMMARY**", etc.
            section_pattern = re.compile(
                r"^\#{0,3}\s*\*{0,2}(SUMMARY|ENTITIES)\*{0,2}\s*:*\s*"
            )
            # Same pattern but for extracting the content after the header
            header_pattern = re.compile(
                r"^\#{0,3}\s*\*{0,2}(SUMMARY|ENTITIES)\*{0,2}\s*:*\s*"
            )

            for line in lines:
                line = line.strip()
                m = section_pattern.match(line)
                if m:
                    section_name = m.group(1)
                    content = header_pattern.sub("", line).strip()
                    if section_name == "SUMMARY":
                        summary = content
                        summary_section = True
                        entities_section = False
                    elif section_name == "ENTITIES":
                        entities = content
                        entities_section = True
                        summary_section = False
                    continue

                if summary_section and not entities_section:
                    if summary:
                        summary += "\n" + line
                    else:
                        summary = line
                elif entities_section:
                    if entities:
                        entities += "\n" + line
                    else:
                        entities = line

            # Check for content after the ENTITIES section by looking for
            # lines that appear after the last ENTITIES header but are not
            # part of the entities content itself (e.g. a trailing "---" or
            # "NOTES:" block).
            last_entities_idx = -1
            for i, line in enumerate(lines):
                if section_pattern.match(line.strip()):
                    m2 = section_pattern.match(line.strip())
                    if m2 and m2.group(1) == "ENTITIES":
                        last_entities_idx = i
            if last_entities_idx >= 0:
                for line in lines[last_entities_idx + 1 :]:
                    stripped = line.strip()
                    if stripped and not re.match(
                        r"^[\w\s,.\-–—/()&;:'\"«»]+$", stripped
                    ):
                        trailing_content.append(stripped)

            if trailing_content:
                logger.warning(
                    "LLM response contains unexpected content after ENTITIES section: "
                    f"{' '.join(trailing_content)[:500]}",
                    extra={
                        "backend": self.__class__.__name__,
                    },
                )

            # If parsing didn't work as expected, return the raw response
            if not summary and not entities:
                return response

            result = f"Summary: {summary}\nEntities: {entities}"
            if trailing_content:
                result += (
                    "\n\n[Note: The LLM also returned additional content after the "
                    "entities section that could not be parsed into the standard "
                    "format. Review the raw response for details.]"
                )
            return result

        except Exception as e:
            logger.error(
                f"LLM backend error during summarisation: {str(e)}",
                exc_info=True,
                extra={
                    "backend": self.__class__.__name__,
                    "error_type": type(e).__name__,
                },
            )
            return (
                "Summary: [LLM summarisation is currently unavailable. "
                "Please try again later.]\n"
                "Entities: [Summarisation service is offline]"
            )


class MockBackend(LLMBackend):
    """
    No-API fallback for testing. Returns a placeholder so the pipeline can
    run end-to-end without any credentials.
    """

    def complete(self, prompt: str) -> str:
        return (
            "[MOCK SUMMARY] This is a placeholder — no real LLM was called.\n"
            "Set LLM_BACKEND=openai|anthropic|ollama|openrouter and provide the\n"
            "appropriate API key or server to get a real summary."
        )


def get_llm_backend(backend_name: Optional[str] = None) -> LLMBackend:
    """
    Factory: reads LLM_BACKEND env var or uses provided name to
    return the matching backend instance.
    backend instance.
    Defaults to MockBackend if not set.

    Args:
        backend_name: Optional backend name to use instead of environment variable

    Returns:
        LLMBackend instance
    """
    name = (backend_name or os.environ.get("LLM_BACKEND", "mock")).lower()
    backends: dict[str, type[LLMBackend]] = {
        "openai": OpenAIBackend,
        "anthropic": AnthropicBackend,
        "ollama": OllamaBackend,
        "openrouter": OpenRouterBackend,
        "openrouter-mistral": OpenRouterMistralBackend,
        "mock": MockBackend,
    }

    if name not in backends:
        raise ValueError(
            f"Unknown LLM_BACKEND '{name}'. " f"Choose from: {', '.join(backends)}"
        )

    return backends[name]()
