"""Account CRUD and account-aware transaction tests."""

import pytest

import database
from sync.identity import DEFAULT_ACCOUNT_UUID
from tests.helpers import fetch_all, fetch_one


def test_default_inr_account_is_seeded_deterministically(temp_database):
    accounts = database.list_accounts()
    assert len(accounts) == 1
    account = accounts[0]
    assert account["uuid"] == DEFAULT_ACCOUNT_UUID
    assert account["currency_code"] == "INR"
    assert account["currency_precision"] == 2
    assert account["is_default"] == 1
    assert account["deleted_at_ms"] is None

    # A second initialize is idempotent.
    database.initialize_database()
    assert len(database.list_accounts()) == 1


def test_create_rename_list_and_get_account(temp_database):
    usd_uuid = database.create_account("Travel wallet", "usd")
    assert database.get_account(usd_uuid)["currency_code"] == "USD"
    assert database.get_account(usd_uuid)["currency_precision"] == 2

    assert database.rename_account(usd_uuid, "Dollar wallet") is True
    renamed = database.get_account(usd_uuid)
    assert renamed["name"] == "Dollar wallet"
    assert renamed["revision"] == 2

    names = [account["name"] for account in database.list_accounts()]
    assert names[0] == "Default INR account"
    assert "Dollar wallet" in names


def test_create_rejects_unknown_currency_and_blank_name(temp_database):
    with pytest.raises(ValueError, match="Unknown ISO"):
        database.create_account("Bad", "ZZZ")
    with pytest.raises(ValueError, match="cannot be empty"):
        database.create_account("   ", "INR")


def test_add_transaction_defaults_to_default_account_and_reports_new_fields(temp_database):
    transaction_id = database.add_transaction(
        "expense", 125.5, "Food", "Lunch", "2026-11-22"
    )
    row = database.get_transaction(transaction_id)
    assert row["amount"] == 125.5
    assert row["amount_minor"] == 12550
    assert row["account_uuid"] == DEFAULT_ACCOUNT_UUID
    assert row["currency_code"] == "INR"
    assert row["currency_precision"] == 2

    listed = database.get_all_transactions()[0]
    assert listed["amount"] == 125.5
    assert listed["amount_minor"] == 12550
    assert listed["account_name"] == "Default INR account"


def test_account_currency_precision_is_enforced(temp_database):
    jpy = database.create_account("Yen cash", "JPY")
    kwd = database.create_account("Kuwait cash", "KWD")

    jpy_id = database.add_transaction(
        "expense", 1000, "Food", "", "2026-11-22", account_uuid=jpy
    )
    assert database.get_transaction(jpy_id)["amount_minor"] == 1000

    kwd_id = database.add_transaction(
        "expense", "1.234", "Food", "", "2026-11-22", account_uuid=kwd
    )
    assert database.get_transaction(kwd_id)["amount_minor"] == 1234

    with pytest.raises(ValueError, match="decimal places"):
        database.add_transaction(
            "expense", "1000.5", "Food", "", "2026-11-22", account_uuid=jpy
        )
    with pytest.raises(ValueError, match="decimal places"):
        database.add_transaction(
            "expense", "1.2345", "Food", "", "2026-11-22", account_uuid=kwd
        )


def test_get_all_transactions_can_filter_by_account(temp_database):
    usd = database.create_account("Dollar wallet", "USD")
    first = database.add_transaction(
        "expense", 10, "Food", "", "2026-11-22"
    )
    second = database.add_transaction(
        "expense", 20, "Food", "", "2026-11-22", account_uuid=usd
    )

    assert [row["id"] for row in database.get_all_transactions(usd)] == [second]
    assert {row["id"] for row in database.get_all_transactions()} == {first, second}


def test_currency_is_immutable_once_any_transaction_exists(temp_database):
    empty = database.create_account("Empty", "INR")
    assert database.update_account(empty, currency_code="USD") is True
    assert database.get_account(empty)["currency_code"] == "USD"

    used = database.create_account("Used", "INR")
    transaction_id = database.add_transaction(
        "expense", 10, "Food", "", "2026-11-22", account_uuid=used
    )
    with pytest.raises(ValueError, match="cannot be changed"):
        database.update_account(used, currency_code="USD")

    database.delete_transaction(transaction_id)
    with pytest.raises(ValueError, match="cannot be changed"):
        database.update_account(used, currency_code="USD")


def test_delete_account_is_blocked_by_live_transactions(temp_database):
    account_uuid = database.create_account("Wallet", "USD")
    database.add_transaction(
        "expense", 10, "Food", "", "2026-11-22", account_uuid=account_uuid
    )

    with pytest.raises(ValueError, match="still has transactions"):
        database.delete_account(account_uuid)

    assert database.get_account(account_uuid) is not None


def test_delete_empty_account_soft_deletes_and_keeps_history(temp_database):
    account_uuid = database.create_account("Old wallet", "USD")
    assert database.delete_account(account_uuid) is True
    assert database.get_account(account_uuid) is None
    assert account_uuid not in {
        account["uuid"] for account in database.list_accounts()
    }

    row = fetch_one(
        temp_database,
        "SELECT * FROM accounts WHERE uuid = ?",
        (account_uuid,),
    )
    assert row["deleted_at_ms"] is not None
    assert row["revision"] == 2

    events = fetch_all(
        temp_database,
        "SELECT * FROM sync_changes WHERE entity_uuid = ? ORDER BY seq",
        (account_uuid,),
    )
    assert [event["operation"] for event in events] == ["insert", "delete"]
    assert all(event["entity_type"] == "account" for event in events)
    assert all(event["payload_version"] == 2 for event in events)


def test_cannot_delete_the_only_live_account(temp_database):
    with pytest.raises(ValueError, match="only account"):
        database.delete_account(DEFAULT_ACCOUNT_UUID)
    assert database.get_default_account() is not None


def test_deleting_default_promotes_another_account(temp_database):
    second = database.create_account("Second", "USD")

    # The default account has no live transactions, so deletion is allowed.
    assert database.delete_account(DEFAULT_ACCOUNT_UUID) is True
    promoted = database.get_default_account()
    assert promoted["uuid"] == second
    assert promoted["is_default"] == 1


def test_account_changes_are_logged_as_account_events(temp_database):
    account_uuid = database.create_account("Wallet", "EUR")
    database.rename_account(account_uuid, "Euro wallet")

    events = fetch_all(
        temp_database,
        "SELECT * FROM sync_changes WHERE entity_uuid = ? ORDER BY seq",
        (account_uuid,),
    )
    assert [event["operation"] for event in events] == ["insert", "update"]
    assert [event["new_revision"] for event in events] == [1, 2]
    assert all(event["entity_type"] == "account" for event in events)
