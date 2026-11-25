"""
Test that the SQLite database schema matches ``_CHAINLIT_SCHEMA``.

The test connects to the database at ``CHAINLIT_DB_PATH`` (default:
``./data/chainlit.db`` relative to the chainlit directory) and verifies:

* Every table declared in ``_CHAINLIT_SCHEMA`` exists in the database.
* Every column declared in each ``CREATE TABLE`` statement exists in the
  corresponding SQLite table.

This catches schema drift — e.g. when a column is added to the schema
definition but an existing database is never migrated (the exact scenario
that occurred with ``start``, ``end``, and ``forId``).

Usage
-----
Run from the ``chainlit/`` directory::

    CHAINLIT_DB_PATH=./data/chainlit.db pytest src/tests/test_db_schema.py -v

In CI, ``CHAINLIT_DB_PATH`` is set to ``/tmp/test_chainlit.db`` via
``pytest.ini``.
"""

import os
import re
import sqlite3
import tempfile

import pytest

from src.database import _CHAINLIT_SCHEMA
from src.scripts.verify_db_schema import action_migrate


# ---------------------------------------------------------------------------
# Module-level setup: ensure the test database exists before any test runs.
# The old ``_ensure_database_schema()`` side-effect-at-import was removed;
# we now create the DB explicitly via ``action_migrate``.
# ---------------------------------------------------------------------------


def setup_module() -> None:
    """Create a temporary test database using ``action_migrate``."""
    db_path = os.environ.get("CHAINLIT_DB_PATH", tempfile.mktemp(suffix=".db"))
    ret = action_migrate(db_path)
    assert ret == 0, f"Failed to create/migrate test database at {db_path}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_expected_schema(schema_sql: str) -> dict[str, set[str]]:
    """Parse ``CREATE TABLE`` statements and return ``{table: {col1, ...}}``.

    This mirrors the logic in :func:`_ensure_database_schema` — it pulls
    column names out of the same DDL strings, so the test stays DRY with
    the authoritative schema definition.
    """
    expected: dict[str, set[str]] = {}
    pattern = re.compile(
        r'CREATE TABLE\s+IF NOT EXISTS\s+"?(\w+)"?\s*\((.*?)\)',
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(schema_sql):
        table = match.group(1)
        columns_block = match.group(2)
        cols: set[str] = set()
        for line in columns_block.split(","):
            line = line.strip()
            if not line:
                continue
            # Skip table-level constraints (PRIMARY KEY, FOREIGN KEY, etc.)
            if line.upper().startswith(
                ("PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "INDEX", "CONSTRAINT")
            ):
                continue
            # The first word (possibly quoted) is the column name
            col_match = re.match(r'"?"?(\w+)"?"?', line)
            if col_match:
                cols.add(col_match.group(1))
        expected[table] = cols
    return expected


def _get_actual_schema(db_path: str) -> dict[str, set[str]]:
    """Connect to the SQLite database and return ``{table: {col1, ...}}``.

    Raises
    ------
    FileNotFoundError
        If *db_path* does not point to an existing file.
    """
    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    actual: dict[str, set[str]] = {}

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        cursor.execute(f'PRAGMA table_info("{table}")')
        columns = {row[1] for row in cursor.fetchall()}
        actual[table] = columns

    conn.close()
    return actual


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_db_schema_all_tables_exist() -> None:
    """Every table declared in ``_CHAINLIT_SCHEMA`` must exist in the DB."""
    expected = _parse_expected_schema(_CHAINLIT_SCHEMA)
    db_path = os.environ.get("CHAINLIT_DB_PATH", "./data/chainlit.db")
    actual = _get_actual_schema(db_path)

    expected_tables = set(expected.keys())
    actual_tables = set(actual.keys())
    missing_tables = expected_tables - actual_tables

    assert not missing_tables, (
        f"Tables declared in _CHAINLIT_SCHEMA but missing from the database: "
        f"{sorted(missing_tables)}"
    )


def test_db_schema_all_columns_exist() -> None:
    """Every column in each ``CREATE TABLE`` must exist in the corresponding table."""
    expected = _parse_expected_schema(_CHAINLIT_SCHEMA)
    db_path = os.environ.get("CHAINLIT_DB_PATH", "./data/chainlit.db")
    actual = _get_actual_schema(db_path)

    failures: list[str] = []
    for table, expected_cols in expected.items():
        actual_cols = actual.get(table, set())
        missing = expected_cols - actual_cols
        if missing:
            failures.append(
                f"  Table \"{table}\" is missing columns: {sorted(missing)}"
            )

    assert not failures, (
        f"Database schema is out of date. Missing columns:\n"
        f"{chr(10).join(failures)}\n\n"
        f"To fix: run  python scripts/verify_db_schema.py --migrate\n"
        f"To reset: run  python scripts/verify_db_schema.py --delete"
    )


def test_db_schema_parse_roundtrip() -> None:
    """Ensure the schema parser itself is correct for every table.

    This test validates ``_parse_expected_schema`` against the actual DDL
    by re-running the same ``CREATE TABLE`` SQL that ``_ensure_database_schema``
    uses.  If the parser is broken, the above tests would give false
    positives, so this is a meta-safety net.
    """
    parsed = _parse_expected_schema(_CHAINLIT_SCHEMA)
    assert "users" in parsed, "Parser did not find 'users' table"
    assert "threads" in parsed, "Parser did not find 'threads' table"
    assert "steps" in parsed, "Parser did not find 'steps' table"
    assert "feedbacks" in parsed, "Parser did not find 'feedbacks' table"
    assert "elements" in parsed, "Parser did not find 'elements' table"

    # Spot-check a few columns that were historically missing
    assert "start" in parsed["steps"], (
        "Parser missed 'start' column in 'steps'"
    )
    assert "end" in parsed["steps"], "Parser missed 'end' column in 'steps'"
    assert "forId" in parsed["elements"], (
        "Parser missed 'forId' column in 'elements'"
    )
    assert "forId" in parsed["feedbacks"], (
        "Parser missed 'forId' column in 'feedbacks'"
    )
