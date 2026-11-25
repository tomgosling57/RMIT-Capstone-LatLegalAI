#!/usr/bin/env python3
"""
Debug script to examine text differences between extracted and source content.
"""

import asyncio
from pathlib import Path
from services.parsers.pdf_parser import PDFParser


async def main():
    # Path to the failing test file
    test_file = Path(
        "backend/src/tests/assets/golden/pdf/single/\
            ai_ethics_australia_single.pdf"
    )
    source_file = Path(
        "backend/src/tests/assets/golden/\
                       source/ai_ethics_australia.txt"
    )

    print(f"Testing file: {test_file}")
    print(f"Source file: {source_file}")

    # Load source text
    source_text = source_file.read_text(encoding="utf-8")
    print(f"Source length: {len(source_text)}")

    # Parse with PDF parser
    parser = PDFParser()
    extracted = await parser.parse(test_file)

    print(f"Extracted pages count: {len(extracted)}")

    # Flatten extracted text
    extracted_flat = "\n".join(extracted)
    print(f"Extracted length: {len(extracted_flat)}")

    # Normalize both texts
    import re

    def normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    norm_source = normalize_text(source_text)
    norm_extracted = normalize_text(extracted_flat)

    print(f"Source normalized (first 300 chars): {norm_source[:300]}")
    print(f"Extracted normalized (first 300 chars): {norm_extracted[:300]}")

    # Find first difference
    print("\nComparing extracted vs source:")
    print("=" * 50)

    for i, (src_char, ext_char) in enumerate(zip(norm_source, norm_extracted)):
        if src_char != ext_char:
            print(f"First difference at position {i}:")
            print(f"  Source: '{norm_source[max(0, i-20):i+20]}'")
            print(f"  Extracted: '{norm_extracted[max(0, i-20):i+20]}'")
            break
    else:
        if len(norm_source) != len(norm_extracted):
            print(
                f"Texts have different lengths: \
                    source={len(norm_source)}, extracted={len(norm_extracted)}"
            )
            if len(norm_source) > len(norm_extracted):
                print(
                    f"Extra chars in source: \
                        {norm_source[len(norm_extracted):len(norm_source)]}"
                )
            else:
                print(
                    f"Extra chars in extracted: \
                        {norm_extracted[len(norm_source):len(norm_extracted)]}"
                )
        else:
            print("Texts are identical!")


if __name__ == "__main__":
    asyncio.run(main())
