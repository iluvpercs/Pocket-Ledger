"""Versioned sync payload tests."""

import json

import database
from sync.identity import DEFAULT_ACCOUNT_UUID
from sync.store import upgrade_payload
from tests.helpers import fetch_all


def _transaction_events(path):
    return fetch_all(
        path,
        "SELECT * FROM sync_changes WHERE entity_type = 'transaction' ORDER BY seq",
    )


def test_new_transaction_payload_is_v2_with_minor_units(temp_database):
    transaction_id = database.add_transaction(
        "expense", 125.5, "Food", "Lunch", "2026-11-22"
    )
    database.update_transaction(transaction_id, amount=150)
    database.delete_transaction(transaction_id)

    events = _transaction_events(temp_database)
    assert [event["operation"] for event in events] == ["insert", "update", "delete"]
    assert all(event["payload_version"] == 2 for event in events)

    payloads = [json.loads(event["payload"]) for event in events]
    assert all("amount" not in payload for payload in payloads)
    assert [payload["amount_minor"] for payload in payloads] == [12550, 15000, 15000]
    assert all(payload["account_uuid"] == DEFAULT_ACCOUNT_UUID for payload in payloads)
    assert all(payload["currency_code"] == "INR" for payload in payloads)
    assert all(payload["currency_precision"] == 2 for payload in payloads)
    assert payloads[2]["deleted_at_ms"] is not None


def test_account_events_are_versioned_and_synced(temp_database):
    account_uuid = database.create_account("Dollar wallet", "USD")
    database.rename_account(account_uuid, "USD wallet")

    events = fetch_all(
        temp_database,
        "SELECT * FROM sync_changes WHERE entity_uuid = ? ORDER BY seq",
        (account_uuid,),
    )
    assert [event["operation"] for event in events] == ["insert", "update"]
    assert all(event["entity_type"] == "account" for event in events)
    assert all(event["payload_version"] == 2 for event in events)

    payloads = [json.loads(event["payload"]) for event in events]
    assert payloads[0]["name"] == "Dollar wallet"
    assert payloads[1]["name"] == "USD wallet"
    assert payloads[0]["currency_code"] == "USD"
    assert payloads[0]["currency_precision"] == 2
    assert payloads[0]["is_default"] == 0


def test_v1_payload_is_upgraded_on_read_without_rewriting_it(temp_database):
    legacy_payload = {
        "uuid": "11111111-1111-4111-8111-111111111111",
        "transaction_type": "expense",
        "amount": 125.5,
        "category": "Food",
        "description": "Legacy lunch",
        "transaction_date": "2026-11-22",
        "created_at_ms": 1,
        "updated_at_ms": 1,
        "deleted_at_ms": None,
        "revision": 1,
        "origin_device_id": "legacy-device",
        "last_modified_by": "legacy-device",
        "import_hash": None,
        "external_ref": None,
        "import_batch_id": None,
        "account_label": "Old account",
    }
    connection = database.get_connection()
    try:
        connection.execute(
            """
            INSERT INTO sync_changes
                (entity_type, entity_uuid, operation, base_revision,
                 new_revision, payload, origin_device_id, recorded_at_ms,
                 payload_version)
            VALUES ('transaction', ?, 'insert', NULL, 1, ?, 'legacy-device', 1, 1)
            """,
            (legacy_payload["uuid"], json.dumps(legacy_payload, sort_keys=True)),
        )
        connection.commit()
    finally:
        connection.close()

    upgraded = upgrade_payload(legacy_payload)
    assert upgraded["amount_minor"] == 12550
    assert upgraded["currency_code"] == "INR"
    assert upgraded["currency_precision"] == 2
    assert upgraded["account_uuid"] == DEFAULT_ACCOUNT_UUID
    assert "amount" not in upgraded

    rows = database.get_sync_changes(upgrade=True)
    legacy_row = next(row for row in rows if row["entity_uuid"] == legacy_payload["uuid"])
    assert legacy_row["payload_version"] == 2
    assert legacy_row["payload"]["amount_minor"] == 12550
    assert "amount" not in legacy_row["payload"]

    # The stored row is untouched.
    raw = fetch_all(
        temp_database,
        "SELECT payload, payload_version FROM sync_changes WHERE entity_uuid = ?",
        (legacy_payload["uuid"],),
    )[0]
    assert raw["payload_version"] == 1
    assert json.loads(raw["payload"]) == legacy_payload


def test_raw_sync_changes_are_available_when_upgrade_is_disabled(temp_database):
    database.add_transaction("expense", 10, "Food", "", "2026-11-22")
    rows = database.get_sync_changes(upgrade=False)
    assert rows
    assert isinstance(rows[0]["payload"], str)
