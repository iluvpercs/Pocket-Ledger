"""Tests for schema versioning, data preservation and rollback."""

import sqlite3
import uuid
from datetime import datetime, timezone

import pytest

import database
import migrations
from tests.helpers import (
    fetch_all,
    fetch_one,
    full_snapshot,
    index_names,
    legacy_snapshot,
    schema_version,
    table_columns,
    table_names,
)


def test_live_database_copy_keeps_every_transaction(live_database_copy):
    """The most important test: a copy of the real file survives migration."""
    before = legacy_snapshot(live_database_copy)
    assert len(before["rows"]) == 5

    version = database.initialize_database()

    after = legacy_snapshot(live_database_copy)
    assert version == migrations.SCHEMA_VERSION
    assert after["user_version"] == migrations.SCHEMA_VERSION
    assert after["rows"] == before["rows"]
    assert len(database.get_all_transactions()) == 5


def test_migration_adds_columns_tables_and_indexes(legacy_database):
    database.initialize_database()

    columns = table_columns(legacy_database)
    expected_columns = {
        "id",
        "transaction_type",
        "amount",
        "category",
        "description",
        "transaction_date",
        "uuid",
        "created_at_ms",
        "updated_at_ms",
        "deleted_at_ms",
        "revision",
        "origin_device_id",
        "last_modified_by",
        "sync_state",
        "import_hash",
        "external_ref",
        "import_batch_id",
        "account_label",
    }
    assert expected_columns <= columns

    tables = table_names(legacy_database)
    assert {
        "transactions",
        "app_meta",
        "devices",
        "sync_changes",
        "sync_peers",
        "sync_conflicts",
        "import_batches",
    } <= tables

    indexes = index_names(legacy_database)
    assert {"idx_tx_date", "idx_tx_updated", "idx_tx_import_hash"} <= indexes


def test_existing_rows_get_unique_uuids_and_valid_timestamps(legacy_database):
    database.initialize_database()

    rows = fetch_all(legacy_database, "SELECT * FROM transactions ORDER BY id")
    assert len(rows) == 5

    uuids = [row["uuid"] for row in rows]
    assert len(set(uuids)) == 5
    for value in uuids:
        parsed = uuid.UUID(value)
        assert parsed.version == 4

    device = fetch_one(
        legacy_database,
        "SELECT value FROM app_meta WHERE key = 'local_device_id'",
    )["value"]
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    for row in rows:
        assert row["created_at_ms"] > 0
        assert row["created_at_ms"] == row["updated_at_ms"]
        assert abs(now_ms - row["created_at_ms"]) < 60_000
        assert row["deleted_at_ms"] is None
        assert row["revision"] == 1
        assert row["origin_device_id"] == device
        assert row["last_modified_by"] == device
        assert row["sync_state"] == "pending"


def test_migration_seeds_one_change_log_entry_per_row(legacy_database):
    database.initialize_database()

    changes = fetch_all(
        legacy_database, "SELECT * FROM sync_changes ORDER BY seq"
    )
    rows = fetch_all(legacy_database, "SELECT * FROM transactions ORDER BY id")

    assert len(changes) == len(rows) == 5
    assert [change["seq"] for change in changes] == [1, 2, 3, 4, 5]
    assert all(change["operation"] == "insert" for change in changes)
    assert [change["entity_uuid"] for change in changes] == [
        row["uuid"] for row in rows
    ]
    assert all(change["new_revision"] == 1 for change in changes)


def test_running_migrations_twice_changes_nothing(legacy_database):
    database.initialize_database()
    first = full_snapshot(legacy_database)

    database.initialize_database()
    second = full_snapshot(legacy_database)

    assert first == second
    assert schema_version(legacy_database) == migrations.SCHEMA_VERSION


def test_failed_migration_rolls_back_and_can_be_retried(
    legacy_database, monkeypatch
):
    before = legacy_snapshot(legacy_database)
    original_backfill = migrations._backfill_legacy_rows

    def explode(*args, **kwargs):
        raise RuntimeError("simulated failure while copying rows")

    monkeypatch.setattr(migrations, "_backfill_legacy_rows", explode)

    with pytest.raises(RuntimeError, match="simulated failure"):
        database.initialize_database()

    # Version 1 was committed, but the version-2 rebuild was rolled back.
    after_failure = legacy_snapshot(legacy_database)
    assert after_failure["user_version"] == 1
    assert after_failure["rows"] == before["rows"]
    assert after_failure["columns"] == before["columns"]
    assert "uuid" not in after_failure["columns"]
    assert "transactions_new" not in table_names(legacy_database)
    assert "sync_changes" not in table_names(legacy_database)

    # Put the real function back and retry: the database is still usable.
    monkeypatch.setattr(migrations, "_backfill_legacy_rows", original_backfill)
    assert database.initialize_database() == migrations.SCHEMA_VERSION

    after_retry = legacy_snapshot(legacy_database)
    assert after_retry["rows"] == before["rows"]
    assert "uuid" in after_retry["columns"]


def test_fresh_database_is_created_at_latest_version(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fresh.db")

    assert database.initialize_database() == migrations.SCHEMA_VERSION

    assert schema_version(tmp_path / "fresh.db") == migrations.SCHEMA_VERSION
    assert fetch_one(tmp_path / "fresh.db", "PRAGMA journal_mode")["journal_mode"] == "wal"
    assert fetch_one(tmp_path / "fresh.db", "SELECT COUNT(*) AS n FROM transactions")["n"] == 0
    assert table_columns(tmp_path / "fresh.db") >= {"uuid", "import_hash"}


def test_backup_is_created_before_migrating(legacy_database):
    database.initialize_database()

    backups = sorted((legacy_database.parent / "backups").glob("*.db"))
    assert len(backups) == 1

    backup = backups[0]
    assert schema_version(backup) == 0
    assert fetch_one(backup, "PRAGMA integrity_check")["integrity_check"] == "ok"
    assert fetch_one(backup, "SELECT COUNT(*) AS n FROM transactions")["n"] == 5


def test_existing_ids_are_reused_and_next_id_continues(legacy_database):
    database.initialize_database()

    ids = [
        row["id"]
        for row in fetch_all(legacy_database, "SELECT id FROM transactions ORDER BY id")
    ]
    assert ids == [3, 4, 5, 6, 7]

    new_id = database.add_transaction(
        "expense", 10, "Food", "Tea", "2026-02-01"
    )
    assert new_id == 8


def test_database_from_a_newer_app_is_refused(legacy_database):
    connection = sqlite3.connect(legacy_database)
    try:
        connection.execute("PRAGMA user_version = 99")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(RuntimeError, match="newer version"):
        database.initialize_database()

    assert schema_version(legacy_database) == 99
