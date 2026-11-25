"""
Services module for LatMatrix backend.
Contains business logic services for document processing, summarization, and analysis.
"""

from .summarizer import LegalSummarizer
from .nlp_processor import NLPService
from .parsers.parser_factory import DocumentParserFactory

__all__ = [
    "LegalSummarizer",
    "NLPService",
    "DocumentParserFactory",
]
