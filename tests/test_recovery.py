"""Tests for the controlled soft-delete recovery script.

Every test builds an equivalent temporary database from scratch. The canonical
live database and the prepared recovery copy are never used here.
"""

import hashlib
import json
import os
import sqlite3

import pytest

import database
from scripts import recover_soft_deleted_transactions as recovery
from sync.store import append_change, transaction_payload

TRANSACTION_COLUMNS = (
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
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(path, sql, parameters=()):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute(sql, parameters)]
    finally:
        connection.close()


def _build_source(path, delete_order=None):
    """Create a temporary v3 DB with the five rows soft-deleted and seq 1-10.

    ``delete_order`` is a tuple of transaction ids for seq 6-10. It defaults to
    id order; the prepared recovery copy uses ``(6, 5, 7, 4, 3)``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript(
            """
            CREATE TABLE app_meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE transactions (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_type TEXT    NOT NULL
                    CHECK (transaction_type IN ('income', 'expense')),
                amount           REAL    NOT NULL CHECK (amount > 0),
                category         TEXT    NOT NULL,
                description      TEXT,
                transaction_date TEXT    NOT NULL,

                uuid              TEXT    NOT NULL UNIQUE,
                created_at_ms     INTEGER NOT NULL,
                updated_at_ms     INTEGER NOT NULL,
                deleted_at_ms     INTEGER,
                revision          INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
                origin_device_id  TEXT    NOT NULL,
                last_modified_by  TEXT    NOT NULL,
                sync_state        TEXT    NOT NULL DEFAULT 'pending'
                    CHECK (sync_state IN ('pending', 'synced', 'conflict')),
                import_hash       TEXT,
                external_ref      TEXT,
                import_batch_id   TEXT,
                account_label     TEXT
            );

            CREATE TABLE sync_changes (
                seq              INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type      TEXT NOT NULL,
                entity_uuid      TEXT NOT NULL,
                operation        TEXT NOT NULL
                    CHECK (operation IN ('insert', 'update', 'delete')),
                base_revision    INTEGER,
                new_revision     INTEGER,
                payload          TEXT NOT NULL,
                origin_device_id TEXT NOT NULL,
                recorded_at_ms   INTEGER NOT NULL
            );
            """
        )
        connection.execute(
            "INSERT INTO app_meta (key, value) VALUES ('local_device_id', ?)",
            ("seed-device",),
        )

        placeholders = ", ".join("?" for _ in TRANSACTION_COLUMNS)
        for index, expected in enumerate(recovery.EXPECTED_TRANSACTIONS):
            created = 1_700_000_000_000 + index
            updated = 1_700_000_001_000 + index
            deleted = 1_700_000_002_000 + index
            values = (
                expected["id"],
                expected["transaction_type"],
                expected["amount"],
                expected["category"],
                f"description-{expected['id']}",
                expected["transaction_date"],
                expected["uuid"],
                created,
                updated,
                deleted,
                2,
                "seed-device",
                "seed-device",
                "pending",
                None,
                None,
                None,
                None,
            )
            connection.execute(
                f"INSERT INTO transactions ({', '.join(TRANSACTION_COLUMNS)}) "
                f"VALUES ({placeholders})",
                values,
            )

        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM transactions ORDER BY id"
        )]

        for index, row in enumerate(rows):
            insert_payload = dict(row)
            insert_payload["deleted_at_ms"] = None
            insert_payload["revision"] = 1
            insert_payload["updated_at_ms"] = row["created_at_ms"]
            append_change(
                connection,
                entity_uuid=row["uuid"],
                operation="insert",
                payload=transaction_payload(insert_payload),
                origin_device_id="seed-device",
                base_revision=None,
                new_revision=1,
                recorded_at_ms=1_000 + index,
            )

        rows_by_id = {row["id"]: row for row in rows}
        ordered_deletes = (
            [rows_by_id[row_id] for row_id in delete_order]
            if delete_order is not None
            else rows
        )
        for index, row in enumerate(ordered_deletes):
            append_change(
                connection,
                entity_uuid=row["uuid"],
                operation="delete",
                payload=transaction_payload(row),
                origin_device_id="seed-device",
                base_revision=1,
                new_revision=2,
                recorded_at_ms=2_000 + index,
            )

        connection.execute("PRAGMA user_version = 3")
        connection.commit()
    finally:
        connection.close()
    return path


def _run_success(tmp_path, source=None):
    source = source or _build_source(tmp_path / "source.db")
    working_copy = tmp_path / "working.db"
    report = recovery.recover_soft_deleted_transactions(
        source,
        confirm_recovery=True,
        working_copy=working_copy,
        recovery_at_ms=555_555,
    )
    return source, working_copy, report


def test_successful_recovery_on_temporary_copy(tmp_path):
    source = _build_source(tmp_path / "source.db")
    source_hash_before = _sha256(source)

    source, working_copy, report = _run_success(tmp_path, source)

    assert report["status"] == "completed"
    assert report["source_path"] == str(recovery._canonical(source))
    assert report["working_copy_path"] == str(recovery._canonical(working_copy))
    assert report["source_unchanged"] is True
    assert report["source_sha256_before"] == source_hash_before
    assert report["source_sha256_after"] == source_hash_before
    assert report["source_sha256_before"] != report["working_copy_sha256_after"]
    assert report["schema_version"] == 3
    assert report["integrity"] == "ok"
    assert report["recovery_at_ms"] == 555_555

    assert report["transactions"]["before"] == 5
    assert report["transactions"]["after"] == 5
    assert report["transactions"]["active_before"] == 0
    assert report["transactions"]["deleted_before"] == 5
    assert report["transactions"]["active_after"] == 5
    assert report["transactions"]["deleted_after"] == 0
    assert report["transactions"]["distinct_uuids_after"] == 5

    assert report["sync_events"]["before"] == 10
    assert report["sync_events"]["after"] == 15
    assert report["sync_events"]["original_events_preserved"] is True
    assert report["sync_events"]["recovery_events_appended"] == 5
    assert report["sync_events"]["recovery_event_seqs"] == [11, 12, 13, 14, 15]

    working_rows = _rows(working_copy, "SELECT * FROM transactions ORDER BY id")
    assert [row["id"] for row in working_rows] == [3, 4, 5, 6, 7]
    assert [row["uuid"] for row in working_rows] == list(recovery.EXPECTED_UUIDS)
    assert all(row["deleted_at_ms"] is None for row in working_rows)
    assert all(row["revision"] == 3 for row in working_rows)
    assert all(row["updated_at_ms"] == 555_555 for row in working_rows)

    source_rows = _rows(source, "SELECT * FROM transactions ORDER BY id")
    assert all(row["deleted_at_ms"] is not None for row in source_rows)
    assert all(row["revision"] == 2 for row in source_rows)


def test_successful_recovery_with_prepared_copy_delete_order(tmp_path):
    delete_order = (6, 5, 7, 4, 3)
    source = _build_source(tmp_path / "source.db", delete_order=delete_order)
    expected_delete_uuids = [
        recovery.EXPECTED_UUIDS[recovery.EXPECTED_IDS.index(row_id)]
        for row_id in delete_order
    ]
    events_before = _rows(
        source, "SELECT seq, entity_uuid FROM sync_changes ORDER BY seq"
    )
    assert [event["entity_uuid"] for event in events_before[:5]] == list(
        recovery.EXPECTED_UUIDS
    )
    assert [event["entity_uuid"] for event in events_before[5:]] == expected_delete_uuids

    source, working_copy, report = _run_success(tmp_path, source)

    assert report["status"] == "completed"
    events_after = _rows(working_copy, "SELECT * FROM sync_changes ORDER BY seq")
    assert events_after[:10] == _rows(
        source, "SELECT * FROM sync_changes ORDER BY seq"
    )
    assert [event["entity_uuid"] for event in events_after[5:10]] == expected_delete_uuids
    assert [event["seq"] for event in events_after] == list(range(1, 16))


def test_refuses_schema_v4_or_later(tmp_path):
    source = _build_source(tmp_path / "source.db")
    with sqlite3.connect(source) as connection:
        connection.execute("PRAGMA user_version = 4")

    with pytest.raises(
        recovery.RecoveryValidationError, match="schema 4 or later"
    ):
        recovery.recover_soft_deleted_transactions(
            source,
            confirm_recovery=True,
            working_copy=tmp_path / "working.db",
        )


def test_refuses_canonical_live_database(tmp_path):
    working_copy = tmp_path / "should-not-exist.db"

    with pytest.raises(recovery.RecoverySafetyError, match="canonical live database"):
        recovery.recover_soft_deleted_transactions(
            database.LIVE_DB_PATH,
            confirm_recovery=True,
            working_copy=working_copy,
        )

    assert not working_copy.exists()


def test_refuses_to_overwrite_existing_working_copy(tmp_path):
    source = _build_source(tmp_path / "source.db")
    source_hash = _sha256(source)
    existing = tmp_path / "existing.db"
    sentinel = "do not overwrite this file"
    existing.write_text(sentinel, encoding="utf-8")

    with pytest.raises(recovery.RecoverySafetyError, match="overwrite"):
        recovery.recover_soft_deleted_transactions(
            source,
            confirm_recovery=True,
            working_copy=existing,
        )

    assert existing.read_text(encoding="utf-8") == sentinel
    assert _sha256(source) == source_hash


def test_refuses_hard_link_to_live_database(tmp_path, monkeypatch):
    fake_live = _build_source(tmp_path / "fake_live.db")
    monkeypatch.setattr(recovery.database, "LIVE_DB_PATH", fake_live)
    alias = tmp_path / "live_alias.db"
    working_copy = tmp_path / "should-not-exist.db"

    try:
        os.link(fake_live, alias)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"hard links are not supported on this platform: {error}")

    try:
        with pytest.raises(recovery.RecoverySafetyError, match="hard-link alias"):
            recovery.recover_soft_deleted_transactions(
                alias,
                confirm_recovery=True,
                working_copy=working_copy,
            )
    finally:
        alias.unlink()

    assert not working_copy.exists()


def test_refuses_recovery_without_confirmation(tmp_path):
    source = _build_source(tmp_path / "source.db")
    source_hash = _sha256(source)
    working_copy = tmp_path / "should-not-exist.db"

    with pytest.raises(recovery.RecoverySafetyError, match="confirm"):
        recovery.recover_soft_deleted_transactions(
            source, working_copy=working_copy
        )

    assert not working_copy.exists()
    assert _sha256(source) == source_hash


def test_cli_requires_explicit_database_path():
    parser = recovery.build_parser()

    assert parser.get_default("database") is None
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_refuses_transaction_that_is_already_active(tmp_path):
    source = _build_source(tmp_path / "source.db")
    with sqlite3.connect(source) as connection:
        connection.execute(
            "UPDATE transactions SET deleted_at_ms = NULL WHERE id = 3"
        )

    with pytest.raises(recovery.RecoveryValidationError, match="already active"):
        recovery.recover_soft_deleted_transactions(
            source,
            confirm_recovery=True,
            working_copy=tmp_path / "working.db",
        )

    working_copy = tmp_path / "working.db"
    working_rows = _rows(working_copy, "SELECT id, deleted_at_ms FROM transactions")
    assert len(working_rows) == 5
    assert sum(row["deleted_at_ms"] is None for row in working_rows) == 1


@pytest.mark.parametrize(
    ("field", "value", "expected_message"),
    (
        ("uuid", "00000000-0000-4000-8000-000000000000", "UUID"),
        ("amount", 1.0, "amount"),
    ),
)
def test_refuses_uuid_or_amount_mismatch(tmp_path, field, value, expected_message):
    source = _build_source(tmp_path / "source.db")
    with sqlite3.connect(source) as connection:
        connection.execute(
            f"UPDATE transactions SET {field} = ? WHERE id = 3", (value,)
        )

    with pytest.raises(recovery.RecoveryValidationError, match=expected_message):
        recovery.recover_soft_deleted_transactions(
            source,
            confirm_recovery=True,
            working_copy=tmp_path / "working.db",
        )


def test_refuses_when_recovery_events_already_exist(tmp_path):
    source = _build_source(tmp_path / "source.db")
    uuid = recovery.EXPECTED_UUIDS[0]
    with sqlite3.connect(source) as connection:
        connection.execute(
            """
            INSERT INTO sync_changes
                (seq, entity_type, entity_uuid, operation, base_revision,
                 new_revision, payload, origin_device_id, recorded_at_ms)
            VALUES (11, 'transaction', ?, 'update', 2, 3, '{}', 'seed-device', 9999)
            """,
            (uuid,),
        )

    with pytest.raises(recovery.RecoveryValidationError, match="already exist"):
        recovery.recover_soft_deleted_transactions(
            source,
            confirm_recovery=True,
            working_copy=tmp_path / "working.db",
        )

    working_events = _rows(
        tmp_path / "working.db", "SELECT * FROM sync_changes ORDER BY seq"
    )
    assert len(working_events) == 11


def test_rolls_back_working_copy_if_an_operation_fails(tmp_path, monkeypatch):
    source = _build_source(tmp_path / "source.db")
    source_hash = _sha256(source)
    working_copy = tmp_path / "working.db"
    real_append_change = recovery.append_change
    calls = []

    def flaky_append_change(*args, **kwargs):
        calls.append((args, kwargs))
        if len(calls) == 3:
            raise RuntimeError("simulated append failure")
        return real_append_change(*args, **kwargs)

    monkeypatch.setattr(recovery, "append_change", flaky_append_change)

    with pytest.raises(RuntimeError, match="simulated append failure"):
        recovery.recover_soft_deleted_transactions(
            source,
            confirm_recovery=True,
            working_copy=working_copy,
        )

    assert len(calls) == 3
    assert _sha256(source) == source_hash

    rows = _rows(working_copy, "SELECT * FROM transactions ORDER BY id")
    assert len(rows) == 5
    assert all(row["deleted_at_ms"] is not None for row in rows)
    assert all(row["revision"] == 2 for row in rows)
    assert all(row["updated_at_ms"] != 555_555 for row in rows)

    events = _rows(working_copy, "SELECT * FROM sync_changes ORDER BY seq")
    assert len(events) == 10
    assert [event["seq"] for event in events] == list(range(1, 11))


def test_verifies_source_hash_on_failure_path(tmp_path, monkeypatch):
    source = _build_source(tmp_path / "source.db")
    with sqlite3.connect(source) as connection:
        connection.execute(
            "UPDATE transactions SET deleted_at_ms = NULL WHERE id = 3"
        )
    source_path = str(recovery._canonical(source))
    observed_hashes = []
    real_sha256 = recovery._sha256

    def tracking_sha256(path):
        value = real_sha256(path)
        observed_hashes.append((str(path), value))
        return value

    monkeypatch.setattr(recovery, "_sha256", tracking_sha256)

    with pytest.raises(recovery.RecoveryValidationError, match="already active"):
        recovery.recover_soft_deleted_transactions(
            source,
            confirm_recovery=True,
            working_copy=tmp_path / "working.db",
        )

    source_hashes = [
        value for path, value in observed_hashes if path == source_path
    ]
    assert len(source_hashes) == 2
    assert source_hashes[0] == source_hashes[1]


def test_original_events_1_to_10_are_preserved(tmp_path):
    source, working_copy, _report = _run_success(tmp_path)

    before = _rows(source, "SELECT * FROM sync_changes ORDER BY seq")
    after = _rows(working_copy, "SELECT * FROM sync_changes ORDER BY seq")

    assert before == after[:10]
    assert [event["seq"] for event in after] == list(range(1, 16))


def test_exactly_five_recovery_update_events_are_appended(tmp_path):
    _source, working_copy, _report = _run_success(tmp_path)

    events = _rows(working_copy, "SELECT * FROM sync_changes ORDER BY seq")
    recovery_events = events[10:]

    assert len(recovery_events) == 5
    assert [event["seq"] for event in recovery_events] == [11, 12, 13, 14, 15]
    assert all(event["operation"] == "update" for event in recovery_events)
    assert all(event["base_revision"] == 2 for event in recovery_events)
    assert all(event["new_revision"] == 3 for event in recovery_events)
    assert all(event["entity_uuid"] in recovery.EXPECTED_UUIDS for event in recovery_events)

    payloads = [json.loads(event["payload"]) for event in recovery_events]
    assert all(payload["deleted_at_ms"] is None for payload in payloads)
    assert all(payload["revision"] == 3 for payload in payloads)
    assert sorted(payload["uuid"] for payload in payloads) == sorted(
        recovery.EXPECTED_UUIDS
    )

    rows_by_id = {
        row["id"]: row
        for row in _rows(working_copy, "SELECT * FROM transactions ORDER BY id")
    }
    for expected, event in zip(recovery.EXPECTED_TRANSACTIONS, recovery_events):
        expected_payload = transaction_payload(rows_by_id[expected["id"]])
        assert json.loads(event["payload"]) == expected_payload
        assert event["payload"] == json.dumps(expected_payload, sort_keys=True)


def test_no_duplicate_uuids_after_recovery(tmp_path):
    _source, working_copy, _report = _run_success(tmp_path)

    rows = _rows(working_copy, "SELECT uuid FROM transactions")
    assert len(rows) == 5
    assert len({row["uuid"] for row in rows}) == 5

    connection = sqlite3.connect(working_copy)
    try:
        duplicate_count = connection.execute(
            "SELECT COUNT(*) FROM transactions GROUP BY uuid HAVING COUNT(*) > 1"
        ).fetchall()
    finally:
        connection.close()
    assert duplicate_count == []
