"""Schema 3 -> 4 conversion, manifest verification and rollback tests."""

import sqlite3
from decimal import Decimal

import pytest

import database
import migrations
from sync.identity import DEFAULT_ACCOUNT_UUID
from tests.helpers import (
    fetch_all,
    fetch_one,
    full_snapshot,
    make_v3_database,
    schema_version,
    table_columns,
)
from utils.money import minor_to_decimal


AWFUL_ROWS = (
    (3, "expense", 0.1, "Food", "Ten paise", "2026-01-01"),
    (4, "expense", 125.499999, "Food", "Almost 125.50", "2026-01-02"),
    (5, "income", 19.995, "Salary", "Half-up case", "2026-01-03"),
)


def _v3_identity(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        return {
            row["id"]: dict(row)
            for row in connection.execute(
                "SELECT * FROM transactions ORDER BY id"
            )
        }
    finally:
        connection.close()


def test_v4_backfill_preserves_identity_and_converts_float_amounts(legacy_database):
    make_v3_database(legacy_database, AWFUL_ROWS)
    connection = sqlite3.connect(legacy_database)
    try:
        connection.execute(
            "UPDATE transactions SET import_hash = 'legacy-hash-3' WHERE id = 3"
        )
        connection.commit()
    finally:
        connection.close()

    before = _v3_identity(legacy_database)
    assert len(before) == 3

    assert database.initialize_database() == 4
    assert schema_version(legacy_database) == 4

    columns = table_columns(legacy_database)
    assert "amount" not in columns
    assert {"amount_minor", "account_uuid"} <= columns

    after = {
        row["id"]: row
        for row in fetch_all(
            legacy_database, "SELECT * FROM transactions ORDER BY id"
        )
    }
    expected_minor = {
        3: 10,
        4: 12550,
        5: 2000,
    }

    manifest = [
        {
            "id": row_id,
            "uuid": before[row_id]["uuid"],
            "amount_minor": expected_minor[row_id],
        }
        for row_id in sorted(before)
    ]
    actual_manifest = [
        {
            "id": row["id"],
            "uuid": row["uuid"],
            "amount_minor": row["amount_minor"],
        }
        for row in after.values()
    ]
    assert actual_manifest == manifest

    assert sum(row["amount_minor"] for row in after.values()) == 14560
    assert minor_to_decimal(after[3]["amount_minor"], 2) == Decimal("0.10")
    assert minor_to_decimal(after[4]["amount_minor"], 2) == Decimal("125.50")
    assert minor_to_decimal(after[5]["amount_minor"], 2) == Decimal("20.00")

    for row_id, original in before.items():
        migrated = after[row_id]
        assert migrated["uuid"] == original["uuid"]
        assert migrated["created_at_ms"] == original["created_at_ms"]
        assert migrated["updated_at_ms"] == original["updated_at_ms"]
        assert migrated["revision"] == original["revision"]
        assert migrated["import_hash"] == original["import_hash"]
        assert migrated["account_uuid"] == DEFAULT_ACCOUNT_UUID

    assert after[3]["import_hash"] == "legacy-hash-3"
    accounts = fetch_all(legacy_database, "SELECT * FROM accounts")
    assert len(accounts) == 1
    assert accounts[0]["uuid"] == DEFAULT_ACCOUNT_UUID
    assert accounts[0]["currency_code"] == "INR"

    event = fetch_one(
        legacy_database,
        "SELECT * FROM sync_changes WHERE entity_type = 'account'",
    )
    assert event["entity_uuid"] == DEFAULT_ACCOUNT_UUID
    assert event["payload_version"] == 2


def test_running_the_v4_migration_twice_changes_nothing(legacy_database):
    make_v3_database(legacy_database, AWFUL_ROWS)
    database.initialize_database()
    first = full_snapshot(legacy_database)

    assert database.initialize_database() == 4
    second = full_snapshot(legacy_database)

    assert first == second


def test_failure_on_overflow_rolls_back_to_v3(legacy_database):
    make_v3_database(
        legacy_database,
        ((3, "expense", 1e300, "Food", "Too large", "2026-01-01"),),
    )

    with pytest.raises(RuntimeError, match="offending transaction ids.*id=3"):
        database.initialize_database()

    assert schema_version(legacy_database) == 3
    assert "amount" in table_columns(legacy_database)
    assert "amount_minor" not in table_columns(legacy_database)
    row = fetch_one(legacy_database, "SELECT amount FROM transactions WHERE id = 3")
    assert row["amount"] == 1e300
    accounts = fetch_all(
        legacy_database,
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'accounts'",
    )
    assert accounts == []


def test_failure_on_round_trip_mismatch_reports_the_id_and_rolls_back(
    legacy_database, monkeypatch
):
    make_v3_database(
        legacy_database,
        ((3, "expense", 10.0, "Food", "Mismatch", "2026-01-01"),),
    )

    monkeypatch.setattr(
        migrations,
        "minor_to_decimal",
        lambda *_args, **_kwargs: Decimal("999.99"),
    )

    with pytest.raises(RuntimeError, match="offending transaction ids.*id=3"):
        database.initialize_database()

    assert schema_version(legacy_database) == 3
    assert "amount_minor" not in table_columns(legacy_database)
    assert fetch_one(
        legacy_database, "SELECT amount FROM transactions WHERE id = 3"
    )["amount"] == 10.0
