"""Tests for the public database functions used by both applications."""

import json
import sqlite3
import uuid

import pytest

import database
from tests.helpers import fetch_all, fetch_one


def test_add_view_update_delete_flow(temp_database):
    new_id = database.add_transaction(
        "expense", 125.5, "Food", "Lunch", "2026-11-22"
    )

    rows = database.get_all_transactions()
    assert len(rows) == 1
    assert rows[0]["id"] == new_id

    created = database.get_transaction(new_id)
    assert created is not None
    assert created["amount"] == 125.5
    assert created["category"] == "Food"
    assert created["uuid"]
    assert created["revision"] == 1
    assert created["deleted_at_ms"] is None
    assert created["sync_state"] == "pending"

    assert database.update_transaction(
        new_id, amount=200, category="Dining", description="Dinner"
    ) is True

    updated = database.get_transaction(new_id)
    assert updated["amount"] == 200
    assert updated["category"] == "Dining"
    assert updated["description"] == "Dinner"
    assert updated["revision"] == 2
    assert updated["updated_at_ms"] >= created["updated_at_ms"]
    assert updated["created_at_ms"] == created["created_at_ms"]

    with pytest.raises(ValueError, match="greater than zero"):
        database.update_transaction(new_id, amount=0)

    assert database.delete_transaction(new_id) is True
    assert database.get_all_transactions() == []
    assert database.get_transaction(new_id) is None
    assert database.delete_transaction(new_id) is False
    assert database.update_transaction(new_id, amount=50) is False


def test_delete_is_a_soft_delete_with_a_tombstone(temp_database):
    new_id = database.add_transaction(
        "income", 900, "Salary", "", "2026-11-22"
    )
    assert database.delete_transaction(new_id) is True

    raw = fetch_one(
        temp_database, "SELECT * FROM transactions WHERE id = ?", (new_id,)
    )
    assert raw is not None
    assert raw["deleted_at_ms"] is not None
    assert raw["deleted_at_ms"] == raw["updated_at_ms"]
    assert raw["revision"] == 2


def test_change_log_records_insert_update_and_delete(temp_database):
    new_id = database.add_transaction(
        "expense", 125.5, "Food", "Lunch", "2026-11-22"
    )
    transaction_uuid = database.get_transaction(new_id)["uuid"]

    database.update_transaction(new_id, amount=150)
    database.delete_transaction(new_id)

    changes = fetch_all(
        temp_database,
        "SELECT * FROM sync_changes WHERE entity_type = 'transaction' ORDER BY seq",
    )
    assert [change["operation"] for change in changes] == [
        "insert",
        "update",
        "delete",
    ]

    payloads = [json.loads(change["payload"]) for change in changes]
    assert all(payload["uuid"] == transaction_uuid for payload in payloads)
    assert all(change["payload_version"] == 2 for change in changes)
    assert payloads[0]["amount_minor"] == 12550
    assert payloads[1]["amount_minor"] == 15000
    assert payloads[2]["deleted_at_ms"] is not None
    assert all("amount" not in payload for payload in payloads)

    assert changes[0]["base_revision"] is None
    assert changes[0]["new_revision"] == 1
    assert changes[1]["base_revision"] == 1
    assert changes[1]["new_revision"] == 2
    assert changes[2]["base_revision"] == 2
    assert changes[2]["new_revision"] == 3


@pytest.mark.parametrize(
    "transaction_type, amount, category, transaction_date",
    [
        ("credit", 10, "Food", "2026-11-22"),
        ("expense", 0, "Food", "2026-11-22"),
        ("expense", -5, "Food", "2026-11-22"),
        ("expense", "not-a-number", "Food", "2026-11-22"),
        ("expense", 10, "   ", "2026-11-22"),
        ("expense", 10, "Food", "31-12-2026"),
    ],
)
def test_validation_rules_are_unchanged(
    temp_database, transaction_type, amount, category, transaction_date
):
    with pytest.raises(ValueError):
        database.add_transaction(
            transaction_type, amount, category, "", transaction_date
        )

    assert database.get_all_transactions() == []
    transaction_events = fetch_all(
        temp_database,
        "SELECT * FROM sync_changes WHERE entity_type = 'transaction'",
    )
    assert transaction_events == []
    # Only the default account's insert event exists.
    assert database.get_change_count() == 1


def test_import_hash_blocks_duplicates_until_the_row_is_deleted(temp_database):
    first_id = database.add_transaction(
        "expense",
        99,
        "Food",
        "Snack",
        "2026-11-22",
        import_hash="abc123",
    )

    with pytest.raises(ValueError, match="duplicate"):
        database.add_transaction(
            "expense",
            99,
            "Food",
            "Snack",
            "2026-11-22",
            import_hash="abc123",
        )

    # Only the first row and its insert log entry exist; the failed attempt
    # did not leave half a transaction behind. The seeded default account also
    # has one insert event.
    assert len(database.get_all_transactions()) == 1
    assert database.get_change_count() == 2

    database.delete_transaction(first_id)

    # A deleted row is a tombstone, so importing the same statement again is
    # allowed. This matters when a user re-imports a corrected file.
    second_id = database.add_transaction(
        "expense",
        99,
        "Food",
        "Snack",
        "2026-11-22",
        import_hash="abc123",
    )
    assert second_id != first_id


def test_get_all_transactions_keeps_the_original_row_shape(temp_database):
    database.add_transaction("income", 10, "Gift", "", "2026-11-22")

    row = database.get_all_transactions()[0]
    assert {
        "id",
        "transaction_type",
        "amount",
        "category",
        "description",
        "transaction_date",
        "amount_minor",
        "account_uuid",
        "account_name",
        "currency_code",
        "currency_precision",
    } <= set(row.keys())


def test_newest_date_is_returned_first(temp_database):
    older = database.add_transaction(
        "expense", 10, "Food", "Older", "2026-01-01"
    )
    newer = database.add_transaction(
        "expense", 20, "Food", "Newer", "2026-02-01"
    )

    rows = database.get_all_transactions()
    assert [row["id"] for row in rows] == [newer, older]


def test_connection_uses_wal_busy_timeout_and_foreign_keys(temp_database):
    connection = database.get_connection()
    try:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        connection.close()


def test_device_id_is_created_once_and_reused(temp_database):
    def read_device_id():
        row = fetch_one(
            temp_database,
            "SELECT value FROM app_meta WHERE key = 'local_device_id'",
        )
        return row["value"]

    first = read_device_id()
    second = read_device_id()

    assert first == second
    assert uuid.UUID(first).version == 4

    new_id = database.add_transaction(
        "expense", 10, "Food", "", "2026-11-22"
    )
    row = database.get_transaction(new_id)
    assert row["origin_device_id"] == first
    assert row["last_modified_by"] == first


def test_change_log_can_be_paged_and_filtered(temp_database):
    for index in range(5):
        database.add_transaction(
            "expense", 10 + index, "Food", "", "2026-11-22"
        )

    assert database.get_change_count() == 6

    first_page = database.get_sync_changes(since_seq=0, limit=2)
    assert [row["seq"] for row in first_page] == [1, 2]

    second_page = database.get_sync_changes(since_seq=first_page[-1]["seq"], limit=2)
    assert [row["seq"] for row in second_page] == [3, 4]

    device_id = fetch_one(
        temp_database,
        "SELECT value FROM app_meta WHERE key = 'local_device_id'",
    )["value"]
    assert database.get_sync_changes(exclude_device_id=device_id) == []


def test_description_is_trimmed_and_optional(temp_database):
    blank_id = database.add_transaction(
        "expense", 10, "Food", None, "2026-11-22"
    )
    padded_id = database.add_transaction(
        "expense", 20, "Food", "  note  ", "2026-11-22"
    )

    assert database.get_transaction(blank_id)["description"] == ""
    assert database.get_transaction(padded_id)["description"] == "note"


def test_invalid_import_hash_does_not_break_ordinary_inserts(temp_database):
    new_id = database.add_transaction(
        "expense", 10, "Food", "", "2026-11-22", import_hash="   "
    )

    raw = fetch_one(
        temp_database, "SELECT import_hash FROM transactions WHERE id = ?", (new_id,)
    )
    assert raw["import_hash"] is None
