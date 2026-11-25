#!/usr/bin/env python3
"""
Canonical entry point for verifying/migrating/resetting the Chainlit DB schema.

This script delegates to the authoritative copy at
``chainlit/src/scripts/verify_db_schema.py``.

Usage
-----
    python scripts/verify_db_schema.py --check
    python scripts/verify_db_schema.py --migrate
    python scripts/verify_db_schema.py --delete

Run with ``--help`` for full details.
"""

import os
import subprocess
import sys

_CANONICAL = os.path.join(
    os.path.dirname(__file__),
    "..",
    "chainlit",
    "src",
    "scripts",
    "verify_db_schema.py",
)

if __name__ == "__main__":
    # Forward all arguments to the canonical script
    cmd = [sys.executable, os.path.abspath(_CANONICAL)] + sys.argv[1:]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
