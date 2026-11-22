"""Shared helpers for the Pocket Ledger test suite."""

import sqlite3
from pathlib import Path

from migrations import CREATE_TRANSACTIONS_V1_SQL

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
    destination_path = Path(destination_path)
    source = sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)
    target = sqlite3.connect(destination_path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    return destination_path


def make_legacy_database(path, rows=SAMPLE_LEGACY_ROWS):
    """Create a version-0 database with the original five-column table."""
    path = Path(path)
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


def fetch_all(path, sql, parameters=()):
    """Run a query and return plain dictionaries."""
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
    """The original five columns plus version and table shape."""
    return {
        "rows": fetch_all(
            path,
            """
            SELECT id, transaction_type, amount, category, description, transaction_date
            FROM transactions ORDER BY id
            """,
        ),
        "columns": table_columns(path),
        "user_version": schema_version(path),
    }


def full_snapshot(path):
    """Everything a migration could change, for double-run comparisons."""
    return {
        "transactions": fetch_all(path, "SELECT * FROM transactions ORDER BY id"),
        "changes": fetch_all(path, "SELECT * FROM sync_changes ORDER BY seq"),
        "meta": fetch_all(path, "SELECT * FROM app_meta ORDER BY key"),
        "user_version": schema_version(path),
        "tables": table_names(path),
    }
