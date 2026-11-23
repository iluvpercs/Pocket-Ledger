"""Regression tests for the database safety guard."""

import inspect

import pytest
from PySide6.QtWidgets import QLabel

import database
from tests import conftest as conftest_module
from tests.conftest import (
    LIVE_DB,
    assert_live_fingerprint_unchanged,
    live_fingerprint,
)
from tests.helpers import (
    copy_database,
    fetch_all,
    make_legacy_database,
    require_safe_writable_path,
)


def test_live_db_connection_is_rejected_in_test_mode(monkeypatch):
    """Even a read connection must fail closed against the live file."""
    monkeypatch.setenv(database.TEST_MODE_ENV_VAR, "1")
    monkeypatch.setenv(database.DB_PATH_ENV_VAR, str(database.LIVE_DB_PATH))
    database.refresh_database_path()

    with pytest.raises(database.DatabaseSafetyError, match="live database"):
        database._open_connection()


def test_temporary_database_connections_still_work(temp_database):
    connection = database.get_connection()
    try:
        assert connection.execute("SELECT 1").fetchone()[0] == 1
    finally:
        connection.close()

    assert database.DB_PATH != database.LIVE_DB_PATH
    assert database.DB_PATH.parent == temp_database.parent


def test_environment_variable_controls_db_path(tmp_path, monkeypatch):
    path = database._canonical_path(tmp_path / "custom.db")
    monkeypatch.setenv(database.DB_PATH_ENV_VAR, str(path))

    assert database.resolve_db_path() == path

    database.refresh_database_path()
    assert database.DB_PATH == path
    assert database.DATA_DIR == path.parent

    connection = database._open_connection()
    try:
        assert connection.execute("SELECT 1").fetchone()[0] == 1
    finally:
        connection.close()


def test_invalid_environment_database_paths_are_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv(database.DB_PATH_ENV_VAR, "   ")
    with pytest.raises(database.DatabaseConfigurationError, match="empty"):
        database.resolve_db_path()

    monkeypatch.setenv(database.DB_PATH_ENV_VAR, str(tmp_path))
    with pytest.raises(database.DatabaseConfigurationError, match="directory"):
        database.resolve_db_path()


def test_test_fixture_isolation_uses_temporary_db(temp_database):
    assert database.in_test_mode()
    assert database.DB_PATH == database._canonical_path(temp_database)
    assert str(database.DB_PATH).lower() != str(database.LIVE_DB_PATH).lower()


def test_late_worker_cannot_open_live_db(qapp, temp_database, monkeypatch):
    """A worker that outlives a fixture still fails closed at connect time."""
    monkeypatch.setenv(database.DB_PATH_ENV_VAR, str(database.LIVE_DB_PATH))
    database.refresh_database_path()

    errors = []
    from ui.workers import run_database_task, wait_for_all_database_tasks

    run_database_task(
        qapp,
        database.get_all_transactions,
        on_success=lambda _rows: pytest.fail("live read unexpectedly succeeded"),
        on_error=errors.append,
    )
    wait_for_all_database_tasks(timeout=5.0)

    assert errors
    assert "live database" in errors[0]


def test_live_fingerprint_covers_database_and_sidecars():
    fingerprint = live_fingerprint()
    assert str(LIVE_DB) in fingerprint
    assert any(name.endswith("-wal") for name in fingerprint)
    assert any(name.endswith("-shm") for name in fingerprint)
    assert any(name.endswith("-journal") for name in fingerprint)


def test_fingerprint_mismatch_names_the_changed_file():
    before = live_fingerprint()
    after = dict(before)
    after[str(LIVE_DB)] = (0, 0, "changed")

    with pytest.raises(AssertionError, match="pocket_ledger.db"):
        assert_live_fingerprint_unchanged(before, after, "test")


def test_missing_live_database_is_not_a_successful_check(tmp_path):
    missing = tmp_path / "missing.db"
    fingerprint = {str(missing): None}

    with pytest.raises(AssertionError, match="missing"):
        assert_live_fingerprint_unchanged(fingerprint, dict(fingerprint), "session")


def test_dev_db_indicator_shows_for_development_path(qapp, temp_database):
    import desktop_app

    window = desktop_app.PocketLedgerApp()
    try:
        labels = [label.text() for label in window.findChildren(QLabel)]
        assert "DEV DB" in labels
    finally:
        window.close()


def test_dev_db_indicator_hidden_for_production_path(
    qapp, temp_database, monkeypatch
):
    import desktop_app

    monkeypatch.setattr(database, "is_development_database", lambda: False)
    window = desktop_app.PocketLedgerApp()
    try:
        labels = [label.text() for label in window.findChildren(QLabel)]
        assert "DEV DB" not in labels
    finally:
        window.close()


def test_settings_shows_active_database_path(qapp, temp_database):
    import desktop_app

    window = desktop_app.PocketLedgerApp()
    try:
        settings = window.show_page("settings")
        labels = "\n".join(label.text() for label in settings.findChildren(QLabel))
        assert str(database.DB_PATH) in labels
    finally:
        window.close()


def test_writable_helpers_reject_the_live_database():
    live = database.LIVE_DB_PATH

    with pytest.raises(database.DatabaseSafetyError, match="live database"):
        require_safe_writable_path(live)
    with pytest.raises(database.DatabaseSafetyError, match="live database"):
        make_legacy_database(live)
    with pytest.raises(database.DatabaseSafetyError, match="live database"):
        fetch_all(live, "SELECT 1")
    with pytest.raises(database.DatabaseSafetyError, match="live database"):
        copy_database(live, live)


def test_raw_connection_factory_rejects_the_live_database(raw_connection):
    with pytest.raises(database.DatabaseSafetyError, match="live database"):
        raw_connection(database.LIVE_DB_PATH)


def test_conftest_live_path_uses_database_canonical_path():
    assert LIVE_DB == database._canonical_path(database.LIVE_DB_PATH)


def test_per_test_fingerprint_runs_after_worker_cleanup():
    source = inspect.getsource(conftest_module.cleanup_database_workers)
    assert "protect_live_database" in source
    assert "wait_for_all_database_tasks" in source
