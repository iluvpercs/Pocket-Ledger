"""Shared pytest fixtures.

Two rules keep the real financial data safe:

1. Every test that touches a database gets a temporary file in ``tmp_path``.
2. An autouse check hashes the live database before and after each test and
   fails if it changed. Tests may copy the live file, but never write to it.
"""

import hashlib
import sqlite3
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database  # noqa: E402
from tests.helpers import copy_database, make_legacy_database  # noqa: E402

LIVE_DB = PROJECT_ROOT / "data" / "pocket_ledger.db"


def _live_fingerprint():
    if not LIVE_DB.exists():
        return None
    stat = LIVE_DB.stat()
    return (
        stat.st_size,
        stat.st_mtime_ns,
        hashlib.sha256(LIVE_DB.read_bytes()).hexdigest(),
    )


@pytest.fixture(autouse=True)
def protect_live_database():
    """Fail the test if it accidentally writes to data/pocket_ledger.db."""
    before = _live_fingerprint()
    yield
    after = _live_fingerprint()
    assert after == before, (
        "A test modified the live database. Tests must only use temporary copies."
    )


@pytest.fixture
def project_root():
    return PROJECT_ROOT


@pytest.fixture
def live_db_path():
    if not LIVE_DB.exists():
        pytest.skip("No live database to copy.")
    return LIVE_DB


@pytest.fixture
def temp_database(tmp_path, monkeypatch):
    """An empty, fully migrated database in a temporary folder."""
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "pocket_ledger.db")
    database.initialize_database()
    return database.DB_PATH


@pytest.fixture
def legacy_database(tmp_path, monkeypatch):
    """A version-0 database with five rows, patched into database.py."""
    path = tmp_path / "pocket_ledger.db"
    make_legacy_database(path)
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", path)
    return path


@pytest.fixture
def live_database_copy(tmp_path, monkeypatch, live_db_path):
    """A byte-for-byte copy of the real database, patched into database.py."""
    path = copy_database(live_db_path, tmp_path / "pocket_ledger.db")
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", path)
    return path


@pytest.fixture
def raw_connection():
    """Factory that opens a short-lived connection for assertions."""

    connections = []

    def connect(path):
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        connections.append(connection)
        return connection

    yield connect

    for connection in connections:
        connection.close()
