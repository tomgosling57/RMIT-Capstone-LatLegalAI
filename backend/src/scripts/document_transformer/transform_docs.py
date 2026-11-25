#!/usr/bin/env python3
"""
transform_docs.py
=================
Command-line interface for the DocumentTransformer.

Usage examples
--------------
# Process all *.txt files in ./input → ./output  (all formats, all layouts)
python transform_docs.py

# Custom directories
python transform_docs.py --input-dir /data/raw --output-dir /data/docs

# Process a single file
python transform_docs.py --file my_text.txt

# Inline text
python transform_docs.py --text "Hello world. This is a test." --stem hello

# Only specific formats / layouts
python transform_docs.py --formats pdf docx --layouts single double

# List available formats and layouts, then exit
python transform_docs.py --list

Environment variables (override defaults, overridden by CLI flags)
------------------
  INPUT_DIR   default input directory  (default: ./input)
  OUTPUT_DIR  default output directory (default: ./output)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Allow running the script from any working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from doc_transformer.transformer import DocumentTransformer


# ─────────────────────────────────────────────────────────────────────────────
# CLI helpers
# ─────────────────────────────────────────────────────────────────────────────

FORMATS_HELP = "pdf  docx  scanned_pdf  txt"
LAYOUTS_HELP = "single  double  multi"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="transform_docs",
        description="Generate PDF / DOCX / scanned-PDF / TXT documents from "
        "plain-text input with single, double and multi-column layouts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # ── Source ──────────────────────────────────────────────────────────────
    src = p.add_mutually_exclusive_group()
    src.add_argument(
        "--file",
        "-f",
        metavar="PATH",
        help="Path to a single .txt source file.",
    )
    src.add_argument(
        "--text",
        "-t",
        metavar="STRING",
        help="Inline plain-text string (use with --stem to set the output name).",
    )
    # If neither --file nor --text, the transformer scans INPUT_DIR

    p.add_argument(
        "--stem",
        "-s",
        metavar="NAME",
        default="document",
        help="Base name (without extension) used for output files when --text "
        "is provided.  Default: 'document'.",
    )

    # ── Directories ──────────────────────────────────────────────────────────
    p.add_argument(
        "--input-dir",
        "-i",
        metavar="DIR",
        default=None,
        help="Directory containing *.txt source files "
        "(default: $INPUT_DIR env var or ./input).",
    )
    p.add_argument(
        "--output-dir",
        "-o",
        metavar="DIR",
        default=None,
        help="Directory where generated files are written "
        "(default: $OUTPUT_DIR env var or ./output).",
    )

    # ── Filters ──────────────────────────────────────────────────────────────
    p.add_argument(
        "--formats",
        nargs="+",
        metavar="FMT",
        default=None,
        choices=["pdf", "docx", "scanned_pdf", "txt"],
        help=f"Formats to generate (space-separated).  Choices: {FORMATS_HELP}  "
        "Default: all.",
    )
    p.add_argument(
        "--layouts",
        nargs="+",
        metavar="LAYOUT",
        default=None,
        choices=["single", "double", "multi"],
        help=f"Layouts to generate (space-separated).  Choices: {LAYOUTS_HELP}  "
        "Default: all.",
    )

    # ── Misc ─────────────────────────────────────────────────────────────────
    p.add_argument(
        "--list",
        action="store_true",
        help="Print available formats and layouts, then exit.",
    )
    p.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress output.",
    )

    return p


def _print_list():
    print("Available formats:")
    for f in ["pdf", "docx", "scanned_pdf", "txt"]:
        print(f"  {f}")
    print()
    print("Available layouts:")
    for layout in ["single", "double", "multi"]:
        print(f"  {layout}")


def _log(msg: str, quiet: bool):
    if not quiet:
        print(msg)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list:
        _print_list()
        return 0

    transformer = DocumentTransformer(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
    )

    _log(f"Input  directory : {transformer.input_dir}", args.quiet)
    _log(f"Output directory : {transformer.output_dir}", args.quiet)
    if args.formats:
        _log(f"Formats          : {', '.join(args.formats)}", args.quiet)
    if args.layouts:
        _log(f"Layouts          : {', '.join(args.layouts)}", args.quiet)
    _log("", args.quiet)

    t0 = time.perf_counter()

    try:
        if args.text:
            _log(f"Processing inline text (stem={args.stem!r}) …", args.quiet)
            results = transformer.transform_text(
                text=args.text,
                stem=args.stem,
                formats=args.formats,
                layouts=args.layouts,
            )
        elif args.file:
            _log(f"Processing file: {args.file}", args.quiet)
            results = transformer.transform_file(
                input_path=args.file,
                formats=args.formats,
                layouts=args.layouts,
            )
        else:
            _log(f"Scanning {transformer.input_dir} for *.txt files …", args.quiet)
            results = transformer.transform_all(
                formats=args.formats,
                layouts=args.layouts,
            )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise  # show traceback for unexpected errors

    elapsed = time.perf_counter() - t0

    _log(f"Generated {len(results)} file(s) in {elapsed:.1f}s:\n", args.quiet)
    for name, path in sorted(results.items()):
        size_kb = path.stat().st_size / 1024
        _log(f"  {path}  ({size_kb:.1f} KB)", args.quiet)

    if args.quiet:
        # Machine-readable output: one path per line
        for path in sorted(results.values()):
            print(path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
