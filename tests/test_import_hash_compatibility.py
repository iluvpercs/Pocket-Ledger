"""Import-hash compatibility and per-account duplicate scoping tests."""

import hashlib
from decimal import Decimal

import database
from importers import csv_parser, dedupe, service
from tests.helpers import fetch_all


def _write(tmp_path, text, name="statement.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8", newline="")
    return path


def test_existing_two_decimal_inr_hashes_are_byte_identical():
    amount = Decimal("-180.00")
    expected = hashlib.sha256(
        "2026-01-15|-18000|stationery|0".encode("utf-8")
    ).hexdigest()

    assert dedupe.amount_to_paise(amount) == -18000
    assert dedupe.build_import_hash("2026-01-15", amount, "Stationery", 0) == expected
    assert (
        dedupe.build_import_hash(
            "2026-01-15", amount, "Stationery", 0, precision=2
        )
        == expected
    )


def test_same_file_can_be_imported_into_two_accounts(temp_database, tmp_path):
    text = "Date,Description,Amount\n12/01/2026,Tea Stall,50.00 Dr\n"
    path = _write(tmp_path, text)
    second = database.create_account("Second INR", "INR")

    first_preview = service.build_preview(path)
    first = service.commit_preview(first_preview)
    assert first.imported == 1

    second_preview = service.build_preview(path, account_uuid=second)
    assert second_preview.rows[0].duplicate_status == "new"
    assert second_preview.rows[0].included is True
    second_summary = service.commit_preview(second_preview)
    assert second_summary.imported == 1

    rows = fetch_all(
        temp_database,
        "SELECT account_uuid, import_hash, amount_minor FROM transactions "
        "ORDER BY id",
    )
    assert len(rows) == 2
    assert rows[0]["import_hash"] == rows[1]["import_hash"]
    assert rows[0]["account_uuid"] != rows[1]["account_uuid"]
    assert all(row["amount_minor"] == 5000 for row in rows)

    # Re-importing into the first account is still a duplicate.
    repeat = service.build_preview(path)
    assert repeat.rows[0].duplicate_status == "duplicate"


def test_jpy_and_kwd_amounts_use_their_own_precision(temp_database, tmp_path):
    jpy = database.create_account("Yen cash", "JPY")
    kwd = database.create_account("Kuwait cash", "KWD")

    jpy_path = _write(
        tmp_path,
        "Date,Description,Amount\n12/01/2026,Yen item,1000 Dr\n",
        "jpy.csv",
    )
    kwd_path = _write(
        tmp_path,
        "Date,Description,Amount\n12/01/2026,Kuwait item,1.234 Dr\n",
        "kwd.csv",
    )

    jpy_summary = service.commit_preview(
        service.build_preview(jpy_path, account_uuid=jpy)
    )
    kwd_summary = service.commit_preview(
        service.build_preview(kwd_path, account_uuid=kwd)
    )
    assert jpy_summary.imported == 1
    assert kwd_summary.imported == 1

    jpy_row = database.get_transaction(jpy_summary.imported_ids[0])
    kwd_row = database.get_transaction(kwd_summary.imported_ids[0])
    assert jpy_row["amount_minor"] == 1000
    assert jpy_row["currency_precision"] == 0
    assert kwd_row["amount_minor"] == 1234
    assert kwd_row["currency_precision"] == 3

    assert dedupe.build_import_hash(
        "2026-01-12", Decimal("1000"), "Yen item", 0, precision=0
    ) != dedupe.build_import_hash(
        "2026-01-12", Decimal("1000"), "Yen item", 0, precision=2
    )


def test_csv_parser_quantises_to_the_account_precision():
    assert csv_parser.parse_amount("1000.4", precision=0) == Decimal("1000")
    assert csv_parser.parse_amount("1000.5", precision=0) == Decimal("1001")
    assert csv_parser.parse_amount("1.2345", precision=3) == Decimal("1.235")
    assert csv_parser.parse_amount("1.2345", precision=2) == Decimal("1.23")
