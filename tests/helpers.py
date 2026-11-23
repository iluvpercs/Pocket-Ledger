"""Shared helpers for the Pocket Ledger test suite."""

import sqlite3
from pathlib import Path

import database
import migrations
from migrations import CREATE_TRANSACTIONS_V1_SQL
from utils.money import parse_to_minor


def require_safe_writable_path(path):
    """Reject writable helper targets that resolve to the canonical live DB."""
    candidate = database._canonical_path(path)
    if candidate == database._canonical_path(database.LIVE_DB_PATH):
        raise database.DatabaseSafetyError(
            "Refusing writable test/helper access to the live database at "
            f"{candidate}. Use a temporary POCKET_LEDGER_DB path instead."
        )
    return Path(path)

# Five neutral sample rows used to build a throwaway "old" database. The real
# data is never copied into the repository; the live-database test copies it
# at run time instead.
SAMPLE_LEGACY_ROWS = (
    (3, "income", 5000.0, "Salary", "", "2026-01-01"),
    (4, "expense", 250.0, "Food", "Lunch", "2026-01-02"),
    (5, "expense", 120.0, "Transport", "Bus", "2026-01-03"),
    (6, "expense", 800.0, "Entertainment", "Cinema", "2026-01-04"),
    (7, "income", 1000.0, "Freelance", "", "2026-01-05"),
)


def copy_database(source_path, destination_path):
    """Copy a database safely with SQLite's backup API."""
    source_path = Path(source_path)
    destination_path = require_safe_writable_path(destination_path)
    # immutable=1 keeps SQLite from creating -wal/-shm sidecars beside the
    # live database. This is a read-only inspection copy, not a live backup.
    source = sqlite3.connect(
        f"file:{source_path.as_posix()}?mode=ro&immutable=1", uri=True
    )
    target = sqlite3.connect(destination_path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    return destination_path


def make_legacy_database(path, rows=SAMPLE_LEGACY_ROWS):
    """Create a version-0 database with the original five-column table."""
    path = require_safe_writable_path(path)
    connection = sqlite3.connect(path)
    try:
        connection.execute(CREATE_TRANSACTIONS_V1_SQL)
        connection.executemany(
            """
            INSERT INTO transactions
                (id, transaction_type, amount, category, description, transaction_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.execute("PRAGMA user_version = 0")
        connection.commit()
    finally:
        connection.close()
    return path


def make_v3_database(path, rows=SAMPLE_LEGACY_ROWS):
    """Create a schema-3 database with the supplied legacy rows.

    This deliberately stops before the schema-4 migration so tests can migrate
    a realistic v3 file (including awkward float amounts) on a temp copy.
    """
    path = Path(path)
    path.unlink(missing_ok=True)  # start from the supplied rows, not a fixture
    path = make_legacy_database(path, rows)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        migrations._migrate_to_v2(connection)
        migrations._migrate_to_v3(connection)
        connection.execute("PRAGMA user_version = 3")
        connection.commit()
    finally:
        connection.close()
    return path


def fetch_all(path, sql, parameters=()):
    """Run a query and return plain dictionaries."""
    require_safe_writable_path(path)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute(sql, parameters)]
    finally:
        connection.close()


def fetch_one(path, sql, parameters=()):
    rows = fetch_all(path, sql, parameters)
    return rows[0] if rows else None


def schema_version(path):
    return int(fetch_one(path, "PRAGMA user_version")["user_version"])


def table_names(path):
    return {
        row["name"]
        for row in fetch_all(
            path, "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }


def index_names(path):
    return {
        row["name"]
        for row in fetch_all(
            path, "SELECT name FROM sqlite_master WHERE type = 'index'"
        )
    }


def table_columns(path, table="transactions"):
    return {
        row["name"]
        for row in fetch_all(path, f"PRAGMA table_info({table})")
    }


def legacy_snapshot(path):
    """The original columns plus version and table shape.

    Before schema 4 the stored value is ``amount``; afterwards it is
    ``amount_minor``. The snapshot normalises both to ``amount_minor`` so
    before/after migration comparisons stay meaningful.
    """
    columns = table_columns(path)
    if "amount_minor" in columns:
        rows = fetch_all(
            path,
            """
            SELECT id, transaction_type, amount_minor, category, description,
                   transaction_date
            FROM transactions ORDER BY id
            """,
        )
    else:
        rows = fetch_all(
            path,
            """
            SELECT id, transaction_type, amount, category, description,
                   transaction_date
            FROM transactions ORDER BY id
            """,
        )
        for row in rows:
            row["amount_minor"] = parse_to_minor(
                row.pop("amount"), precision=2, strict=False
            )
    return {
        "rows": rows,
        "columns": columns,
        "user_version": schema_version(path),
    }


def full_snapshot(path):
    """Everything a migration could change, for double-run comparisons."""
    return {
        "transactions": fetch_all(path, "SELECT * FROM transactions ORDER BY id"),
        "accounts": fetch_all(path, "SELECT * FROM accounts ORDER BY id"),
        "changes": fetch_all(path, "SELECT * FROM sync_changes ORDER BY seq"),
        "meta": fetch_all(path, "SELECT * FROM app_meta ORDER BY key"),
        "user_version": schema_version(path),
        "tables": table_names(path),
    }
