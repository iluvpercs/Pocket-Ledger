"""End-to-end import tests: preview, dedupe and atomic commit on temp databases."""

import json
import sqlite3
import uuid
from decimal import Decimal

import pytest

import database
from importers import csv_parser, dedupe, service
from tests.helpers import fetch_all, fetch_one


def write_csv(tmp_path, text, name="statement.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8", newline="")
    return path


def make_preview(tmp_path, text, name="statement.csv"):
    parsed = csv_parser.parse_csv(write_csv(tmp_path, text, name))
    assert parsed.ok, parsed.error
    return service.build_preview(parsed)


def test_identical_same_day_rows_are_kept_with_distinct_hashes(temp_database, tmp_path):
    preview = make_preview(
        tmp_path,
        "Date,Description,Amount\n"
        "12/01/2026,Tea Stall,50.00 Dr\n"
        "12/01/2026,Tea Stall,50.00 Dr\n",
    )

    assert len(preview.rows) == 2
    assert preview.rows[0].import_hash != preview.rows[1].import_hash
    assert all(row.included for row in preview.rows)

    summary = service.commit_preview(preview)
    assert summary.imported == 2
    assert summary.errors == 0

    rows = fetch_all(
        temp_database,
        "SELECT transaction_type, amount_minor, import_hash "
        "FROM transactions ORDER BY id",
    )
    assert len(rows) == 2
    assert all(row["transaction_type"] == "expense" for row in rows)
    assert all(row["amount_minor"] == 5000 for row in rows)
    assert rows[0]["import_hash"] != rows[1]["import_hash"]


def test_reimporting_the_same_file_creates_zero_new_transactions(
    temp_database, tmp_path
):
    text = (
        "Date,Description,Amount\n"
        "12/01/2026,Tea Stall,50.00 Dr\n"
        "13/01/2026,Bus Ticket,30.00 Dr\n"
    )
    first = service.commit_preview(make_preview(tmp_path, text, "first.csv"))
    assert first.imported == 2

    before_changes = database.get_change_count()
    second_preview = make_preview(tmp_path, text, "second.csv")
    assert [row.duplicate_status for row in second_preview.rows] == [
        "duplicate",
        "duplicate",
    ]
    assert service.preview_counts(second_preview)["included"] == 0

    second = service.commit_preview(second_preview)
    assert second.imported == 0
    assert second.skipped_duplicates == 2
    assert len(database.get_all_transactions()) == 2
    assert database.get_change_count() == before_changes


def test_soft_deleted_match_is_flagged_and_can_be_imported_again(
    temp_database, tmp_path
):
    first_preview = make_preview(
        tmp_path, "Date,Description,Amount\n14/01/2026,Pharmacy,220.00 Dr\n"
    )
    first = service.commit_preview(first_preview)
    old_id = first.imported_ids[0]
    assert database.delete_transaction(old_id) is True

    second_preview = make_preview(
        tmp_path, "Date,Description,Amount\n14/01/2026,Pharmacy,220.00 Dr\n"
    )
    assert second_preview.rows[0].duplicate_status == "previously_deleted"
    assert second_preview.rows[0].included is False

    service.apply_edits(second_preview, 0, included=True)
    assert second_preview.rows[0].included is True
    summary = service.commit_preview(second_preview)
    assert summary.imported == 1
    assert summary.imported_ids[0] != old_id
    assert len(database.get_all_transactions()) == 1


def test_duplicate_can_be_force_included(temp_database, tmp_path):
    text = "Date,Description,Amount\n15/01/2026,Stationery,180.00 Dr\n"
    service.commit_preview(make_preview(tmp_path, text, "original.csv"))

    preview = make_preview(tmp_path, text, "repeat.csv")
    assert preview.rows[0].duplicate_status == "duplicate"
    service.apply_edits(preview, 0, force_include=True)

    assert preview.rows[0].included is True
    assert preview.rows[0].occurrence_override is not None
    assert preview.rows[0].import_hash != dedupe.build_import_hash(
        "2026-01-15", Decimal("-180.00"), "Stationery", 0
    )

    summary = service.commit_preview(preview)
    assert summary.imported == 1
    hashes = [
        row["import_hash"]
        for row in fetch_all(temp_database, "SELECT import_hash FROM transactions")
    ]
    assert len(hashes) == 2 and hashes[0] != hashes[1]


def test_commit_rolls_back_everything_when_a_write_fails(temp_database, tmp_path, monkeypatch):
    preview = make_preview(
        tmp_path,
        "Date,Description,Amount\n"
        "16/01/2026,One,10.00 Dr\n"
        "17/01/2026,Two,20.00 Dr\n"
        "18/01/2026,Three,30.00 Dr\n",
    )
    original = database.add_transaction
    calls = []

    def flaky_add(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("simulated disk failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(database, "add_transaction", flaky_add)

    with pytest.raises(RuntimeError, match="simulated disk failure"):
        service.commit_preview(preview)

    assert len(calls) == 2
    assert database.get_all_transactions() == []
    assert fetch_all(
        temp_database,
        "SELECT * FROM sync_changes WHERE entity_type = 'transaction'",
    ) == []
    assert fetch_all(temp_database, "SELECT * FROM import_batches") == []
    # Only the seeded default-account insert event remains.
    assert database.get_change_count() == 1


def test_commit_writes_change_log_uuids_and_batch_metadata(temp_database, tmp_path):
    preview = make_preview(
        tmp_path,
        "Date,Description,Amount\n"
        "19/01/2026,Book Store,399.00 Dr\n"
        "20/01/2026,Consulting,5000.00 Cr\n",
    )
    preview.rows[0].reference = "REF-9"

    summary = service.commit_preview(preview)
    assert summary.imported == 2

    device_id = fetch_one(
        temp_database, "SELECT value FROM app_meta WHERE key = 'local_device_id'"
    )["value"]
    for transaction_id in summary.imported_ids:
        row = database.get_transaction(transaction_id)
        assert uuid.UUID(row["uuid"]).version == 4
        assert row["created_at_ms"] > 0
        assert row["updated_at_ms"] >= row["created_at_ms"]
        assert row["revision"] == 1
        assert row["deleted_at_ms"] is None
        assert row["origin_device_id"] == device_id
        assert row["import_batch_id"] == preview.batch_id
        assert row["import_hash"]

    changes = fetch_all(
        temp_database,
        "SELECT * FROM sync_changes WHERE entity_type = 'transaction' ORDER BY seq",
    )
    assert [change["operation"] for change in changes] == ["insert", "insert"]
    payloads = [json.loads(change["payload"]) for change in changes]
    assert all(payload["import_hash"] for payload in payloads)
    assert all(payload["import_batch_id"] == preview.batch_id for payload in payloads)
    assert all(change["payload_version"] == 2 for change in changes)
    assert all("amount" not in payload for payload in payloads)
    assert all(payload["account_uuid"] == preview.account_uuid for payload in payloads)

    batch = fetch_one(
        temp_database, "SELECT * FROM import_batches WHERE batch_id = ?",
        (preview.batch_id,),
    )
    assert batch["source_type"] == "csv"
    assert batch["imported_count"] == 2
    assert batch["skipped_count"] == 0


def test_rules_categorisation_and_default(temp_database, tmp_path):
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        json.dumps(
            {
                "default_category": "Misc",
                "categories": {"Travel": ["metro", "uber"], "Meals": ["cafe"]},
            }
        ),
        encoding="utf-8",
    )
    rules = service.load_rules(rules_path)

    assert service.categorize("Metro Card swipe", rules) == "Travel"
    assert service.categorize("Unknown vendor", rules) == "Misc"

    preview = make_preview(
        tmp_path,
        "Date,Description,Amount\n21/01/2026,Cafe Day,120.00 Dr\n",
    )
    assert preview.rows[0].category == service.categorize("Cafe Day", service.load_rules())


def test_edits_recompute_hash_status_and_totals(temp_database, tmp_path):
    preview = make_preview(
        tmp_path, "Date,Description,Amount\n22/01/2026,Old Text,100.00 Dr\n"
    )
    original_hash = preview.rows[0].import_hash

    service.apply_edits(preview, 0, description="New Text")
    assert preview.rows[0].import_hash != original_hash
    assert preview.rows[0].description == "New Text"

    service.apply_edits(preview, 0, amount="250.00 Cr")
    assert preview.rows[0].amount == Decimal("250.00")
    assert preview.rows[0].transaction_type == "income"
    assert service.preview_totals(preview)["income"] == Decimal("250.00")

    service.apply_edits(preview, 0, included=False)
    assert service.preview_counts(preview)["included"] == 0
    assert service.preview_totals(preview)["income"] == Decimal("0.00")


def test_bad_row_is_not_imported_but_good_rows_are(temp_database, tmp_path):
    preview = make_preview(
        tmp_path,
        "Date,Description,Amount\n"
        "23/01/2026,Good,100.00 Dr\n"
        "bad-date,Broken,100.00 Dr\n",
    )
    counts = service.preview_counts(preview)
    assert counts["errors"] == 1
    assert counts["included"] == 1

    summary = service.commit_preview(preview)
    assert summary.imported == 1
    assert summary.errors == 1
    assert len(database.get_all_transactions()) == 1


def test_build_preview_reports_file_level_errors(tmp_path):
    with pytest.raises(ValueError):
        service.build_preview(csv_parser.parse_csv(tmp_path / "missing.csv"))
