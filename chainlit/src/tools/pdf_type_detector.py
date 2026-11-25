"""
PDF type detector for classifying PDF documents as digital, scanned, or hybrid.

Provides a heuristic-based pipeline that inspects a PDF file and determines
whether it is a digital-native PDF (with a selectable text layer), a scanned
(image-based) PDF, a hybrid (mixed content), or unknown.

The detection pipeline consists of three stages:

1. **Stage 1 — /Image XObject count**: Counts image XObjects in the PDF's
   page resources. A high image-to-page ratio suggests scanned content.
2. **Stage 2 — Text extraction sampling**: Attempts to extract text from a
   sample of pages using ``pdfplumber``. Pages yielding meaningful text
   indicate digital content.
3. **Stage 3 — File size heuristic**: Falls back to file-size-based heuristics
   when earlier stages are inconclusive.
"""

from __future__ import annotations

import logging
from collections import namedtuple
from enum import Enum
from pathlib import Path
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)

HIGH_IMAGE_DENSITY: float = 1.5
LOW_IMAGE_DENSITY: float = 0.1

SAMPLE_SIZE: int = 5
MIN_TEXT_LENGTH: int = 50
TEXT_THRESHOLD_RATIO: float = 0.6

SCANNED_SIZE_THRESHOLD: int = 115_000
DIGITAL_SIZE_THRESHOLD: int = 50_000

# Sentinel used by stage functions to signal an inconclusive result.
# Callers check ``is not None`` to decide whether to proceed to the next stage.
# The type is ``None`` because this sentinel is always None and is only
# compared by identity (``is not``).  A ``PDFType`` value would never be
# stored here.
_INCONCLUSIVE: None = None

_ImageStats = namedtuple(
    "_ImageStats", ["total_images", "num_pages", "images_per_page"]
)


class PDFType(Enum):
    """Classification of a PDF document's origin type."""

    DIGITAL = "digital"
    SCANNED = "scanned"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


def detect_pdf_type(file_path: Path) -> PDFType:
    """
    Classify a PDF document as DIGITAL, SCANNED, HYBRID, or UNKNOWN.

    The function runs a three-stage heuristic pipeline:

    1. **Stage 1 -- /Image XObject count**: Opens the PDF with ``pdfplumber``
       and counts ``/Image`` XObjects across all pages. A high image-per-page
       density suggests scanned content; a low density suggests digital content.
       If the result is clear-cut, the function returns early.

    2. **Stage 2 -- Text extraction sampling**: Samples the first ``SAMPLE_SIZE``
       pages and attempts to extract text via ``pdfplumber``. If a sufficient
       fraction of sampled pages yield meaningful text, the PDF is considered
       digital (or hybrid if Stage 1 indicated images).

    3. **Stage 3 -- File size heuristic**: When Stages 1 and 2 are inconclusive,
       falls back to file-size-based heuristics. Large files are likely scanned;
       small files are likely digital.

    Args:
        file_path: Path to the PDF file to classify.

    Returns:
        A :class:`PDFType` enum value indicating the classification.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        logger.error("PDF file not found: %s", file_path)
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    if not file_path.is_file():
        logger.error("Path is not a file: %s", file_path)
        raise ValueError(f"Path is not a file: {file_path}")

    logger.info("Starting PDF type detection for: %s", file_path)

    image_stats: Optional[_ImageStats] = None
    try:
        result, image_stats = _stage1_image_xobject_count(file_path)
        if result is not _INCONCLUSIVE:
            logger.info(
                "Stage 1 (/Image XObject count) decisive: %s",
                result.value,
                extra={"file_path": str(file_path), "pdf_type": result.value},
            )
            return result
    except Exception:
        logger.warning(
            "Stage 1 (/Image XObject count) failed for: %s",
            file_path,
            exc_info=True,
        )

    try:
        result = _stage2_text_extraction_sample(file_path, image_stats)
        if result is not _INCONCLUSIVE:
            logger.info(
                "Stage 2 (text extraction sampling) decisive: %s",
                result.value,
                extra={"file_path": str(file_path), "pdf_type": result.value},
            )
            return result
    except Exception:
        logger.warning(
            "Stage 2 (text extraction sampling) failed for: %s",
            file_path,
            exc_info=True,
        )

    try:
        result = _stage3_file_size_heuristic(file_path)
        logger.info(
            "Stage 3 (file size heuristic) result: %s",
            result.value,
            extra={"file_path": str(file_path), "pdf_type": result.value},
        )
        return result
    except Exception:
        logger.warning(
            "Stage 3 (file size heuristic) failed for: %s",
            file_path,
            exc_info=True,
        )

    logger.warning(
        "All detection stages failed for: %s - returning UNKNOWN",
        file_path,
        extra={"file_path": str(file_path), "pdf_type": "unknown"},
    )
    return PDFType.UNKNOWN


def _stage1_image_xobject_count(
    file_path: Path,
) -> tuple[Optional[PDFType], Optional[_ImageStats]]:
    """
    Count ``/Image`` XObjects across all pages to estimate image density.

    A high number of images per page strongly suggests a scanned document.
    A very low number suggests a digital document.

    Returns:
        A tuple of ``(PDFType.SCANNED | PDFType.DIGITAL | _INCONCLUSIVE,
        _ImageStats | None)``. The stats tuple is populated whenever the PDF
        opens successfully so downstream stages can reuse the data.
    """
    logger.debug(
        "Stage 1: Counting /Image XObjects for: %s",
        file_path,
        extra={"file_path": str(file_path)},
    )

    with pdfplumber.open(file_path) as pdf:
        num_pages = len(pdf.pages)
        if num_pages == 0:
            logger.debug(
                "Stage 1: PDF has zero pages - inconclusive",
                extra={"file_path": str(file_path)},
            )
            return _INCONCLUSIVE, None

        total_images = 0
        for page in pdf.pages:
            # pdfplumber 0.11.x exposes images via page.images (list of dicts)
            # rather than page.xobjects; fall back gracefully for either API.
            if hasattr(page, "xobjects") and page.xobjects:
                image_count = sum(
                    1 for xobj in page.xobjects if xobj.get("subtype") == "Image"
                )
            else:
                image_count = len(page.images) if page.images else 0
            total_images += image_count

        images_per_page = total_images / num_pages
        stats = _ImageStats(total_images, num_pages, images_per_page)

        logger.debug(
            "Stage 1: %d images across %d pages (%.2f images/page)",
            total_images,
            num_pages,
            images_per_page,
            extra={
                "file_path": str(file_path),
                "total_images": total_images,
                "num_pages": num_pages,
                "images_per_page": images_per_page,
            },
        )

        if images_per_page >= HIGH_IMAGE_DENSITY:
            logger.debug(
                "Stage 1: High image density (%.2f >= %.2f) -> SCANNED",
                images_per_page,
                HIGH_IMAGE_DENSITY,
                extra={"file_path": str(file_path)},
            )
            return PDFType.SCANNED, stats

        if images_per_page <= LOW_IMAGE_DENSITY:
            logger.debug(
                "Stage 1: Low image density (%.2f <= %.2f) -> DIGITAL",
                images_per_page,
                LOW_IMAGE_DENSITY,
                extra={"file_path": str(file_path)},
            )
            return PDFType.DIGITAL, stats

        logger.debug(
            "Stage 1: Inconclusive (%.2f images/page) - proceeding to Stage 2",
            images_per_page,
            extra={
                "file_path": str(file_path),
                "images_per_page": images_per_page,
            },
        )
        return _INCONCLUSIVE, stats


def _stage2_text_extraction_sample(
    file_path: Path,
    image_stats: Optional[_ImageStats] = None,
) -> Optional[PDFType]:
    """
    Sample the first N pages and attempt text extraction.

    If a sufficient fraction of sampled pages yield meaningful text, the PDF
    is classified as digital (or hybrid if Stage 1 indicated images).

    When ``image_stats`` is provided (from a successful Stage 1 run) the
    function uses it to decide between HYBRID and DIGITAL instead of reopening
    the PDF.

    Returns:
        ``PDFType.DIGITAL``, ``PDFType.HYBRID``, or ``_INCONCLUSIVE``.
    """
    logger.debug(
        "Stage 2: Sampling text extraction for: %s",
        file_path,
        extra={"file_path": str(file_path)},
    )

    with pdfplumber.open(file_path) as pdf:
        num_pages = len(pdf.pages)
        if num_pages == 0:
            logger.debug(
                "Stage 2: PDF has zero pages - inconclusive",
                extra={"file_path": str(file_path)},
            )
            return _INCONCLUSIVE

        pages_to_sample = min(SAMPLE_SIZE, num_pages)
        pages_with_text = 0

        for i in range(pages_to_sample):
            page = pdf.pages[i]
            text = page.extract_text() or ""
            text_length = len(text.strip())

            if text_length >= MIN_TEXT_LENGTH:
                pages_with_text += 1

            logger.debug(
                "Stage 2: Page %d/%d - extracted %d chars",
                i + 1,
                pages_to_sample,
                text_length,
                extra={
                    "file_path": str(file_path),
                    "page": i + 1,
                    "text_length": text_length,
                },
            )

        text_ratio = pages_with_text / pages_to_sample

        logger.debug(
            "Stage 2: %d/%d sampled pages have text (ratio=%.2f)",
            pages_with_text,
            pages_to_sample,
            text_ratio,
            extra={
                "file_path": str(file_path),
                "pages_with_text": pages_with_text,
                "pages_sampled": pages_to_sample,
                "text_ratio": text_ratio,
            },
        )

        if text_ratio >= TEXT_THRESHOLD_RATIO:
            if _has_significant_images(image_stats):
                logger.debug(
                    "Stage 2: High text ratio (%.2f) + significant images -> HYBRID",
                    text_ratio,
                    extra={"file_path": str(file_path)},
                )
                return PDFType.HYBRID

            logger.debug(
                "Stage 2: High text ratio (%.2f) + few images -> DIGITAL",
                text_ratio,
                extra={"file_path": str(file_path)},
            )
            return PDFType.DIGITAL

        logger.debug(
            "Stage 2: Low text ratio (%.2f) - inconclusive, proceeding to Stage 3",
            text_ratio,
            extra={"file_path": str(file_path), "text_ratio": text_ratio},
        )
        return _INCONCLUSIVE


def _has_significant_images(
    image_stats: Optional[_ImageStats] = None,
) -> bool:
    """
    Check whether the PDF contains a meaningful number of images.

    Used by Stage 2 to distinguish ``HYBRID`` from ``DIGITAL`` when text
    extraction succeeds on most pages.  Prefers the cached ``_ImageStats``
    from Stage 1 to avoid reopening the PDF.

    Args:
        image_stats: Optional cached stats from Stage 1. When provided the
            check uses the already-computed ``images_per_page`` value.

    Returns:
        ``True`` if the image density exceeds ``LOW_IMAGE_DENSITY``.
    """
    if image_stats is not None and image_stats.num_pages > 0:
        return image_stats.images_per_page > LOW_IMAGE_DENSITY

    return False


def _stage3_file_size_heuristic(file_path: Path) -> PDFType:
    """
    Fallback heuristic based on file size.

    Scanned PDFs tend to be large (each page is a compressed image).
    Digital PDFs tend to be smaller (text + fonts).

    Returns:
        ``PDFType.SCANNED``, ``PDFType.DIGITAL``, or ``PDFType.UNKNOWN``.
    """
    file_size = file_path.stat().st_size

    logger.debug(
        "Stage 3: File size heuristic for: %s (%d bytes)",
        file_path,
        file_size,
        extra={"file_path": str(file_path), "file_size": file_size},
    )

    if file_size >= SCANNED_SIZE_THRESHOLD:
        logger.debug(
            "Stage 3: File size %d >= %d → SCANNED",
            file_size,
            SCANNED_SIZE_THRESHOLD,
            extra={"file_path": str(file_path)},
        )
        return PDFType.SCANNED

    if file_size <= DIGITAL_SIZE_THRESHOLD:
        logger.debug(
            "Stage 3: File size %d <= %d → DIGITAL",
            file_size,
            DIGITAL_SIZE_THRESHOLD,
            extra={"file_path": str(file_path)},
        )
        return PDFType.DIGITAL

    logger.debug(
        "Stage 3: File size %d in ambiguous range — returning UNKNOWN",
        file_size,
        extra={"file_path": str(file_path)},
    )
    return PDFType.UNKNOWN
