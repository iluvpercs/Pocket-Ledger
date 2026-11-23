"""Shared pytest fixtures.

Safety rules:

1. An autouse fixture points every test at a private temporary database via
   ``POCKET_LEDGER_DB`` before any database code runs.
2. ``database.py`` refuses live-database connections whenever test mode is
   active, so both reads and writes fail closed.
3. Per-test and session-level fingerprints cover the live database and its
   WAL/SHM/journal sidecars. Tests may copy the live file, but never write to it.
"""

import hashlib
import os
import sqlite3
import sys
from pathlib import Path

import pytest

# Qt must see this before PySide6 is imported by any test module.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Let database.py reject live connections even outside pytest's setup window.
os.environ.setdefault("POCKET_LEDGER_TEST_MODE", "1")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import database  # noqa: E402
from tests.helpers import (  # noqa: E402
    copy_database,
    make_legacy_database,
    require_safe_writable_path,
)

# Single canonical source of truth for the production database path.
LIVE_DB = database._canonical_path(database.LIVE_DB_PATH)
LIVE_FILES = (
    LIVE_DB,
    LIVE_DB.with_name(LIVE_DB.name + "-wal"),
    LIVE_DB.with_name(LIVE_DB.name + "-shm"),
    LIVE_DB.with_name(LIVE_DB.name + "-journal"),
)


def _fingerprint_path(path):
    """Size, mtime and SHA-256 for one path; ``None`` when it is absent."""
    if not path.exists():
        return None
    stat = path.stat()
    return (
        stat.st_size,
        stat.st_mtime_ns,
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def live_fingerprint():
    """Fingerprint the live database and every SQLite sidecar file."""
    return {str(path): _fingerprint_path(path) for path in LIVE_FILES}


def live_database_baseline():
    """Require a real live database before trusting a fingerprint."""
    fingerprint = live_fingerprint()
    if fingerprint[str(LIVE_DB)] is None:
        raise AssertionError(
            f"Live database is missing at {LIVE_DB}; cannot verify database safety."
        )
    return fingerprint


def assert_live_fingerprint_unchanged(before, after, scope):
    """Fail with the exact file names that changed."""
    if before.get(str(LIVE_DB)) is None:
        raise AssertionError(
            f"{scope}: live database was missing at baseline; safety not verified."
        )
    changed = [
        name for name in before if before[name] != after.get(name)
    ]
    assert not changed, (
        f"{scope}: live database fingerprint changed for: {', '.join(changed)}"
    )


@pytest.fixture(scope="session", autouse=True)
def protect_live_database_session():
    """Session-level guard covers writes between individual tests."""
    before = live_database_baseline()
    yield
    after = live_fingerprint()
    assert_live_fingerprint_unchanged(before, after, "session")


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    """Point every test at a temporary database before any DB initialization."""
    path = database._canonical_path(tmp_path / "pocket_ledger.db")
    monkeypatch.setenv(database.DB_PATH_ENV_VAR, str(path))
    database.refresh_database_path()
    return path


@pytest.fixture(autouse=True)
def protect_live_database(isolated_database):
    """Per-test guard; detection backs up the connection-level prevention."""
    before = live_database_baseline()
    yield
    after = live_fingerprint()
    assert_live_fingerprint_unchanged(before, after, "test")


@pytest.fixture(autouse=True)
def cleanup_database_workers(protect_live_database, qapp):
    """Join database workers before the fingerprint fixture is torn down."""
    yield
    from ui.workers import wait_for_all_database_tasks

    wait_for_all_database_tasks(timeout=5.0)


@pytest.fixture(scope="session")
def qapp():
    """One offscreen QApplication for all Qt smoke tests."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def project_root():
    return PROJECT_ROOT


@pytest.fixture
def live_db_path():
    if not LIVE_DB.exists():
        pytest.skip("No live database to copy.")
    return LIVE_DB


@pytest.fixture
def temp_database(isolated_database):
    """An empty, fully migrated database in a temporary folder."""
    database.initialize_database()
    return database.DB_PATH


@pytest.fixture
def legacy_database(isolated_database):
    """A version-0 database with five rows at the active temporary path."""
    make_legacy_database(isolated_database)
    return isolated_database


@pytest.fixture
def live_database_copy(isolated_database, live_db_path):
    """A copy of the real database at the active temporary path."""
    copy_database(live_db_path, isolated_database)
    return isolated_database


@pytest.fixture
def raw_connection():
    """Factory that opens a short-lived connection for assertions."""

    connections = []

    def connect(path):
        require_safe_writable_path(path)
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        connections.append(connection)
        return connection

    yield connect

    for connection in connections:
        connection.close()
