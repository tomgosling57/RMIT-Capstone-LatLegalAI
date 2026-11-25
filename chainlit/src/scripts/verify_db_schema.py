#!/usr/bin/env python3
"""
Verify, migrate, or reset the Chainlit SQLite database schema.

Usage:
    # Fail-fast check (used by docker-entrypoint.sh)
    python -m src.scripts.verify_db_schema --check

    # Automatically add missing columns
    python -m src.scripts.verify_db_schema --migrate

    # Delete the database and start fresh (prompts for confirmation)
    python -m src.scripts.verify_db_schema --delete

    # Check a custom database path
    python -m src.scripts.verify_db_schema --check --db-path /custom/path/chainlit.db

Run from the ``chainlit/`` directory with ``PYTHONPATH=.`` or ``PYTHONPATH=src``,
or via ``python -m src.scripts.verify_db_schema`` from the project root with
``PYTHONPATH=chainlit/src``.
"""

import argparse
from datetime import datetime, timezone
import os
import re
import sqlite3
import sys

# Ensure the chainlit src directory is on sys.path so we can import the schema.
# This allows the script to be run as:
#   python path/to/chainlit/src/scripts/verify_db_schema.py --check
#   python -m src.scripts.verify_db_schema --check  (from chainlit/ with PYTHONPATH=.)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # .../chainlit/src/scripts/
_SRC_DIR = os.path.dirname(_SCRIPT_DIR)  # .../chainlit/src/
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from src.database import _CHAINLIT_SCHEMA  # noqa: E402

# ---------------------------------------------------------------------------
# Constants: tables the data layer queries
# ---------------------------------------------------------------------------
_ALL_TABLES = {"users", "threads", "steps", "feedbacks", "elements"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def resolve_db_path(cli_path: str | None) -> str:
    """Resolve the database path from CLI arg, env var, or default."""
    if cli_path:
        return cli_path
    env_path = os.environ.get("CHAINLIT_DB_PATH")
    if env_path:
        return env_path
    # Default: ./data/chainlit.db relative to the chainlit/ directory
    # When running from chainlit/, the default works as-is.
    # When running inside Docker (/app), the default also works as-is.
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "chainlit.db")
    )


# ── Column definition tuple: (type, notnull: bool, default: str|None) ───────


def _normalise_default(value: str | None) -> str | None:
    """Normalise a default-value string for comparison.

    SQLite PRAGMA may return values like ``'someval'`` (single-quoted) or
    ``42`` (bare literal).  The schema definition may use different quoting
    conventions.  Strip outer single quotes so comparisons are reliable.
    """
    if value is None:
        return None
    # Strip outer single quotes
    value = value.strip()
    if value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    return value


# Regex fragment to match a balanced parenthesised block (one level of nesting).
# Handles cases like ``DEFAULT (datetime('now'))`` inside column definitions.
_COLUMNS_RE = r"\(((?:[^()]|\([^()]*\))*)\)"


ColDef = tuple[str, bool, str | None]
"""``(type_name, notnull, default_value)`` — the ``default_value`` is the
raw SQL text of the DEFAULT clause (e.g. ``datetime(\'now\')``) or None."""


def parse_expected_schema(
    schema_sql: str,
) -> dict[str, set[str]]:
    """Parse ``CREATE TABLE`` statements and return ``{table: {col1, ...}}``.

    .. deprecated::
        Prefer :func:`parse_expected_schema_full` for constraint-aware checks.
    """
    return {
        table: set(cols.keys())
        for table, cols in parse_expected_schema_full(schema_sql).items()
    }


def parse_expected_schema_full(
    schema_sql: str,
) -> dict[str, dict[str, ColDef]]:
    """Parse ``CREATE TABLE`` statements and return ``{table: {col: (type, notnull, default)}}``."""
    expected: dict[str, dict[str, ColDef]] = {}
    pattern = re.compile(
        rf'CREATE TABLE\s+IF NOT EXISTS\s+"?(\w+)"?\s*{_COLUMNS_RE}',
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(schema_sql):
        table = match.group(1)
        columns_block = match.group(2)
        cols: dict[str, ColDef] = {}
        for line in columns_block.split(","):
            line = line.strip()
            if not line:
                continue
            # Skip table-level constraints
            if line.upper().startswith(
                ("PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "INDEX", "CONSTRAINT")
            ):
                continue
            # Parse:  "col_name" TYPE [NOT NULL] [DEFAULT ...]
            col_match = re.match(
                r'"?(\w+)"?\s+(\w+(?:\s*\(\d+\))?)\s*'
                r'(NOT\s+NULL\s*)?'
                r'(DEFAULT\s+(.+?))?\s*$',
                line,
                re.IGNORECASE,
            )
            if col_match:
                name = col_match.group(1)
                typ = col_match.group(2)
                notnull = bool(col_match.group(3))
                default_raw = col_match.group(5)
                default_val: str | None = default_raw.strip() if default_raw else None
                cols[name] = (typ, notnull, default_val)
        expected[table] = cols
    return expected


def get_actual_schema(db_path: str) -> dict[str, set[str]]:
    """Connect to SQLite and return ``{table: {col1, ...}}``.

    .. deprecated::
        Prefer :func:`get_actual_schema_full` for constraint-aware checks.
    """
    return {
        table: set(cols.keys())
        for table, cols in get_actual_schema_full(db_path).items()
    }


def get_actual_schema_full(
    db_path: str,
) -> dict[str, dict[str, ColDef]]:
    """Connect to SQLite and return ``{table: {col: (type, notnull, default)}}``."""
    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    actual: dict[str, dict[str, ColDef]] = {}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        cursor.execute(f'PRAGMA table_info("{table}")')
        columns: dict[str, ColDef] = {}
        for row in cursor.fetchall():
            # row: (cid, name, type, notnull, dflt_value, pk)
            name: str = row[1]
            typ: str = row[2] or "TEXT"
            notnull: bool = bool(row[3])
            dflt: str | None = row[4]
            columns[name] = (typ, notnull, dflt)
        actual[table] = columns
    conn.close()
    return actual


def get_missing_tables(
    expected: dict[str, set[str]], actual: dict[str, set[str]]
) -> set[str]:
    """Return tables expected in the schema but missing from the DB."""
    return set(expected.keys()) - set(actual.keys())


def get_missing_columns(
    expected: dict[str, set[str]], actual: dict[str, set[str]]
) -> dict[str, set[str]]:
    """Return ``{table: {missing_col1, ...}}`` for columns expected but absent."""
    missing: dict[str, set[str]] = {}
    for table, expected_cols in expected.items():
        actual_cols = actual.get(table, set())
        diff = expected_cols - actual_cols
        if diff:
            missing[table] = diff
    return missing


def get_constraint_mismatches(
    expected: dict[str, dict[str, ColDef]],
    actual: dict[str, dict[str, ColDef]],
) -> dict[str, dict[str, str]]:
    """Return ``{table: {col: description_of_mismatch}}``.

    Compares NOT NULL and DEFAULT constraints for columns that exist in both.
    """
    mismatches: dict[str, dict[str, str]] = {}
    for table, expected_cols in expected.items():
        actual_cols = actual.get(table, {})
        table_mismatches: dict[str, str] = {}
        for col, (typ_e, nn_e, def_e) in expected_cols.items():
            if col not in actual_cols:
                continue
            typ_a, nn_a, def_a = actual_cols[col]

            # Normalise defaults before comparing
            nn_e_norm = nn_e
            def_e_norm = _normalise_default(def_e)
            def_a_norm = _normalise_default(def_a)

            reasons: list[str] = []
            if nn_e and not nn_a:
                reasons.append("missing NOT NULL")
            elif not nn_e and nn_a:
                reasons.append("unexpected NOT NULL")
            if def_e_norm != def_a_norm:
                reasons.append(
                    f"expected DEFAULT {def_e!r}, got {def_a!r}"
                )
            if reasons:
                table_mismatches[col] = "; ".join(reasons)

        if table_mismatches:
            mismatches[table] = table_mismatches
    return mismatches


# ---------------------------------------------------------------------------
# Helpers — admin user seeding
# ---------------------------------------------------------------------------


def _seed_admin_user(conn: sqlite3.Connection) -> None:
    """Insert the default admin user into the users table if not already present.

    The operation is idempotent — subsequent runs are no-ops thanks to
    ``INSERT OR IGNORE`` and the UNIQUE constraint on ``identifier``.
    """
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR IGNORE INTO users (id, identifier, "createdAt", metadata)
        VALUES (?, ?, ?, ?)
        """,
        ("admin", "admin", now, '{"role": "ADMIN"}'),
    )
    print("  Seeded admin user (id=admin, identifier=admin, role=ADMIN)")


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def action_check(db_path: str) -> int:
    """Fail-fast check. Returns 0 if schema matches, 1 if not.

    Checks for:
    * Missing tables
    * Missing columns
    * Constraint mismatches (NOT NULL, DEFAULT) on existing columns
    """
    expected = parse_expected_schema(_CHAINLIT_SCHEMA)
    expected_full = parse_expected_schema_full(_CHAINLIT_SCHEMA)
    try:
        actual = get_actual_schema(db_path)
        actual_full = get_actual_schema_full(db_path)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    missing_tables = get_missing_tables(expected, actual)
    missing_cols = get_missing_columns(expected, actual)
    constraint_mismatches = get_constraint_mismatches(expected_full, actual_full)

    if not missing_tables and not missing_cols and not constraint_mismatches:
        print(f"OK — Database schema at {db_path} matches _CHAINLIT_SCHEMA.")
        return 0

    has_error = False

    if missing_tables:
        has_error = True
        print(
            f"ERROR — Missing tables: {sorted(missing_tables)}",
            file=sys.stderr,
        )
    if missing_cols:
        has_error = True
        for table, cols in missing_cols.items():
            print(
                f"ERROR — Table \"{table}\" is missing columns: {sorted(cols)}",
                file=sys.stderr,
            )
    if constraint_mismatches:
        has_error = True
        for table, cols in constraint_mismatches.items():
            for col, reasons in cols.items():
                print(
                    f"ERROR — Table \"{table}\".\"{col}\" constraint mismatch: "
                    f"{reasons}",
                    file=sys.stderr,
                )

    if has_error:
        print(file=sys.stderr)
        print("To fix (preserves data):", file=sys.stderr)
        print("  python -m src.scripts.verify_db_schema --migrate", file=sys.stderr)
        print(file=sys.stderr)
        print("To reset (deletes all conversation history):", file=sys.stderr)
        print("  docker compose down chainlit", file=sys.stderr)
        print("  docker volume rm project_chainlit_data", file=sys.stderr)
        print("  docker compose up -d chainlit", file=sys.stderr)
    return 1 if has_error else 0


def action_migrate(db_path: str) -> int:
    """Create or migrate the database schema and seed the admin user.

    * If the database file does not exist, it is created from scratch
      using the full ``_CHAINLIT_SCHEMA``, then the admin user is seeded.
    * If the database file already exists, missing tables/columns are
      added and constraint mismatches are fixed (data preserved), then
      the admin user is seeded.

    For constraint mismatches (e.g. missing DEFAULT on a NOT NULL column)
    the affected table is recreated via the standard SQLite
    create-copy-drop-rename approach, which preserves data.
    """
    expected = parse_expected_schema(_CHAINLIT_SCHEMA)
    expected_full = parse_expected_schema_full(_CHAINLIT_SCHEMA)

    # ── Handle missing DB file: create from scratch ─────────────────────
    if not os.path.isfile(db_path):
        print(f"Database not found at {db_path}, creating from scratch...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            for statement in _CHAINLIT_SCHEMA.split(";"):
                stmt = statement.strip()
                if stmt:
                    cursor.execute(stmt)
            _seed_admin_user(conn)
            conn.commit()
            print(f"OK — Database created at {db_path}")
            return 0
        except sqlite3.OperationalError as exc:
            print(f"ERROR during database creation: {exc}", file=sys.stderr)
            return 1
        finally:
            conn.close()

    # ── Existing DB: check and migrate schema ───────────────────────────
    try:
        actual = get_actual_schema(db_path)
        actual_full = get_actual_schema_full(db_path)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    missing_tables = get_missing_tables(expected, actual)
    missing_cols = get_missing_columns(expected, actual)
    constraint_mismatches = get_constraint_mismatches(expected_full, actual_full)

    if not missing_tables and not missing_cols and not constraint_mismatches:
        print(f"Database schema at {db_path} is already up to date.")
    else:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            # ── Create missing tables ────────────────────────────────────
            for table in sorted(missing_tables):
                pattern = re.compile(
                    rf'CREATE TABLE\s+IF NOT EXISTS\s+"?{re.escape(table)}"?\s*{_COLUMNS_RE}',
                    re.DOTALL | re.IGNORECASE,
                )
                match = pattern.search(_CHAINLIT_SCHEMA)
                if match:
                    ddl = f'CREATE TABLE IF NOT EXISTS "{table}" ({match.group(1)})'
                    cursor.execute(ddl)
                    print(f"  Created table \"{table}\"")

            # ── Add missing columns ──────────────────────────────────────
            for table in sorted(missing_cols):
                for col in sorted(missing_cols[table]):
                    col_type = _infer_column_type(table, col)
                    cursor.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN "{col}" {col_type}'
                    )
                    print(f"  Added column \"{table}\".\"{col}\" ({col_type})")

            # ── Fix constraint mismatches ────────────────────────────────
            # SQLite cannot ALTER COLUMN, so we recreate affected tables.
            for table, cols in sorted(constraint_mismatches.items()):
                # Extract the full CREATE TABLE DDL from the expected schema
                pattern = re.compile(
                    rf'CREATE TABLE\s+IF NOT EXISTS\s+"?{re.escape(table)}"?\s*{_COLUMNS_RE}',
                    re.DOTALL | re.IGNORECASE,
                )
                match = pattern.search(_CHAINLIT_SCHEMA)
                if not match:
                    print(
                        f"  WARNING — Could not find schema for \"{table}\", skipping."
                    )
                    continue

                # Check if there are actually any rows to worry about
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                row_count = cursor.fetchone()[0]

                # Build the new table DDL with the corrected schema
                ddl = f'CREATE TABLE IF NOT EXISTS "{table}" ({match.group(1)})'

                # Collect column names from the expected schema for explicit INSERT.
                expected_cols = expected_full.get(table, {})
                col_names = [f'"{c}"' for c in expected_cols.keys()]
                col_list = ", ".join(col_names)

                temp_name = f"{table}_migrate_temp"
                # Use individual execute() calls to avoid executescript()
                # issues with semicolons inside DEFAULT expressions.
                cursor.execute("PRAGMA foreign_keys=OFF")
                cursor.execute(
                    f'CREATE TABLE "{temp_name}" ({match.group(1)})'
                )
                cursor.execute(
                    f'INSERT INTO "{temp_name}" ({col_list}) SELECT {col_list} FROM "{table}"'
                )
                cursor.execute(f'DROP TABLE "{table}"')
                cursor.execute(
                    f'ALTER TABLE "{temp_name}" RENAME TO "{table}"'
                )
                cursor.execute("PRAGMA foreign_keys=ON")
                print(
                    f"  Recreated table \"{table}\" ({row_count} rows preserved) "
                    f"— fixed constraint mismatches: {cols}"
                )

            conn.commit()
            print(f"Migration complete for {db_path}.")
        except sqlite3.OperationalError as exc:
            print(f"ERROR during migration: {exc}", file=sys.stderr)
            return 1
        finally:
            conn.close()

    # ── Seed admin user (idempotent) ─────────────────────────────────────
    conn = sqlite3.connect(db_path)
    try:
        _seed_admin_user(conn)
        conn.commit()
    except sqlite3.OperationalError as exc:
        print(f"ERROR during admin seeding: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()

    print(f"OK — Database at {db_path} is ready.")
    return 0


def _infer_column_type(table: str, column: str) -> str:
    """Infer the SQL type for *column* from ``_CHAINLIT_SCHEMA``."""
    pattern = re.compile(
        rf'CREATE TABLE\s+IF NOT EXISTS\s+"?{re.escape(table)}"?\s*{_COLUMNS_RE}',
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(_CHAINLIT_SCHEMA)
    if match:
        columns_block = match.group(1)
        for line in columns_block.split(","):
            line = line.strip()
            col_match = re.match(r'"?"?(\w+)"?"?\s+(\w+(?:\(\d+\))?)', line)
            if col_match and col_match.group(1) == column:
                return col_match.group(2)
    return "TEXT"  # fallback default


def action_delete(db_path: str) -> int:
    """Delete the database file after user confirmation."""
    if not os.path.isfile(db_path):
        print(f"ERROR: Database not found at {db_path}", file=sys.stderr)
        return 1

    print(f"WARNING: This will permanently delete the database at {db_path}")
    response = input("Delete database? [y/N]: ").strip().lower()
    if response not in ("y", "yes"):
        print("Aborted.")
        return 0

    os.remove(db_path)
    print(f"Deleted {db_path}")
    print("The database will be recreated with the correct schema on next startup.")
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify, migrate, or reset the Chainlit SQLite database schema."
    )
    parser.add_argument(
        "--db-path",
        help="Path to the SQLite database file (default: from CHAINLIT_DB_PATH env "
        "var, or ./data/chainlit.db).",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check",
        action="store_true",
        help="Fail-fast: exit 0 if schema matches, 1 otherwise.",
    )
    group.add_argument(
        "--migrate",
        action="store_true",
        help="Add missing columns/tables via ALTER TABLE / CREATE TABLE.",
    )
    group.add_argument(
        "--delete",
        action="store_true",
        help="Delete the database file (prompts for confirmation).",
    )

    args = parser.parse_args()
    db_path = resolve_db_path(args.db_path)

    if args.check:
        sys.exit(action_check(db_path))
    elif args.migrate:
        sys.exit(action_migrate(db_path))
    elif args.delete:
        sys.exit(action_delete(db_path))


if __name__ == "__main__":
    main()
