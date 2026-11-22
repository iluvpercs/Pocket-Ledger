"""Tests for the pure CSV parser using small, synthetic statements."""

import pytest
from decimal import Decimal

from importers import csv_parser


def write_csv(tmp_path, text, name="statement.csv", encoding="utf-8"):
    path = tmp_path / name
    path.write_text(text, encoding=encoding, newline="")
    return path


def test_single_signed_amount_column_skips_preamble_and_footer(tmp_path):
    path = write_csv(
        tmp_path,
        "Account summary for Demo Customer\n"
        "Statement period 01/04/2026 to 30/04/2026\n"
        "\n"
        "Date,Description,Amount\n"
        "03/04/2026,Coffee Shop,125.50 Dr\n"
        "04/04/2026,Monthly Salary,25000.00 Cr\n"
        "Total,,25125.50\n",
    )

    result = csv_parser.parse_csv(path)

    assert result.ok
    assert result.error is None
    assert result.header_row == 3
    assert result.date_format == "%d/%m/%Y"
    assert [row.description for row in result.rows] == ["Coffee Shop", "Monthly Salary"]
    assert [row.date for row in result.rows] == ["2026-04-03", "2026-04-04"]
    assert [row.amount for row in result.rows] == [
        Decimal("-125.50"),
        Decimal("25000.00"),
    ]
    assert [row.transaction_type for row in result.rows] == ["expense", "income"]
    assert all(row.status == "ok" for row in result.rows)
    assert any("summary" in reason for _, reason in result.skipped_rows)


def test_separate_withdrawal_and_deposit_columns(tmp_path):
    path = write_csv(
        tmp_path,
        "Date,Narration,Withdrawal,Deposit,Closing Balance,Ref No\n"
        "05/05/2026,Metro Card,120.00,,12000.00,R-1\n"
        "06/05/2026,Client Payment,,4500.00,16500.00,R-2\n",
    )

    result = csv_parser.parse_csv(path)

    assert result.mapping["debit"] == 2
    assert result.mapping["credit"] == 3
    assert result.mapping["balance"] == 4
    assert result.mapping["reference"] == 5
    assert [row.amount for row in result.rows] == [
        Decimal("-120.00"),
        Decimal("4500.00"),
    ]
    assert [row.transaction_type for row in result.rows] == ["expense", "income"]
    assert [row.reference for row in result.rows] == ["R-1", "R-2"]
    assert result.rows[0].balance == Decimal("12000.00")


def test_zero_in_inactive_debit_or_credit_column_is_ignored(tmp_path):
    path = write_csv(
        tmp_path,
        "Date,Description,Deposits,Withdrawls,Balance\n"
        "03-Apr-2026,Shop,0.00,\"1,234.50\",\"5,000.00\"\n"
        "04-Apr-2026,Salary,\"2,000.00\",0.00,\"7,000.00\"\n",
    )

    result = csv_parser.parse_csv(path)

    assert result.ok
    assert csv_parser.date_format_label(result.date_format) == "DD-Mon-YYYY"
    assert [row.amount for row in result.rows] == [
        Decimal("-1234.50"),
        Decimal("2000.00"),
    ]


def test_semicolon_delimiter_and_cp1252_encoding(tmp_path):
    path = write_csv(
        tmp_path,
        "Date;Description;Amount\n"
        "07/07/2026;Café Bill;450.00\n"
        "08/07/2026;Bonus;1,500.00 Dr\n",
        encoding="cp1252",
    )

    result = csv_parser.parse_csv(path)

    assert result.ok
    assert result.encoding == "cp1252"
    assert result.delimiter == ";"
    assert result.rows[0].description == "Café Bill"
    assert result.rows[0].amount == Decimal("450.00")
    assert result.rows[1].amount == Decimal("-1500.00")


@pytest.mark.parametrize(
    "text, expected",
    [
        ("1,23,456.78", Decimal("123456.78")),
        ("₹1,234.50", Decimal("1234.50")),
        ("(2,500.00)", Decimal("-2500.00")),
        ("3,000.00 Dr", Decimal("-3000.00")),
        ("4,000.00Cr", Decimal("4000.00")),
        ("-125.50", Decimal("-125.50")),
        ("", None),
        ("   ", None),
    ],
)
def test_parse_amount_variants(text, expected):
    assert csv_parser.parse_amount(text) == expected


def test_parse_amount_rejects_junk():
    with pytest.raises(ValueError):
        csv_parser.parse_amount("not-a-number")


@pytest.mark.parametrize(
    "value, expected",
    [
        ("03/04/2026", "2026-04-03"),
        ("03-04-2026", "2026-04-03"),
        ("03/04/26", "2026-04-03"),
        ("2026-04-03", "2026-04-03"),
        ("03-Apr-2026", "2026-04-03"),
        ("03 Apr 2026", "2026-04-03"),
    ],
)
def test_supported_date_layouts(value, expected):
    code = csv_parser.detect_date_format([value])
    assert csv_parser.parse_date(value, code) == expected


def test_bad_rows_are_reported_without_stopping_the_file(tmp_path):
    path = write_csv(
        tmp_path,
        "Date,Description,Amount\n"
        "08/08/2026,Good Row,100.00\n"
        "not-a-date,Bad Date,100.00\n"
        "09/08/2026,Bad Amount,abc\n"
        "10/08/2026,,50.00\n",
    )

    result = csv_parser.parse_csv(path)

    assert result.ok
    assert result.counts == {"total": 4, "ok": 1, "warning": 1, "error": 2}
    assert [row.status for row in result.rows] == ["ok", "error", "error", "warning"]
    assert result.rows[1].reason
    assert "amount" in result.rows[2].reason.lower()
    assert result.rows[0].amount == Decimal("100.00")


def test_manual_column_mapping_override(tmp_path):
    path = write_csv(
        tmp_path,
        "Statement Date,Vendor,Money In/Out\n"
        "11/11/2026,Corner Shop,250.00 Dr\n",
    )

    auto = csv_parser.parse_csv(path)
    assert auto.mapping.get("date") == 0

    manual = csv_parser.parse_csv(
        path,
        mapping={"description": "Vendor", "amount": 2, "credit": None, "debit": None},
    )
    assert manual.ok
    assert manual.mapping["description"] == 1
    assert manual.mapping["amount"] == 2
    assert manual.mapping["credit"] is None
    assert manual.rows[0].description == "Corner Shop"
    assert manual.rows[0].amount == Decimal("-250.00")


def test_tab_delimiter_is_detected(tmp_path):
    path = write_csv(
        tmp_path,
        "Date\tDescription\tAmount\n"
        "12/12/2026\tBook Store\t399.00 Dr\n"
        "13/12/2026\tGift\t1,000.00 Cr\n",
    )

    result = csv_parser.parse_csv(path)

    assert result.ok
    assert result.delimiter == "\t"
    assert len(result.rows) == 2
    assert result.rows[0].amount == Decimal("-399.00")


def test_ambiguous_date_format_is_reported(monkeypatch):
    monkeypatch.setattr(
        csv_parser,
        "DATE_FORMATS",
        (("%d/%m/%Y", "DD/MM/YYYY"), ("%m/%d/%Y", "MM/DD/YYYY")),
    )

    with pytest.raises(csv_parser.AmbiguousDateFormatError, match="More than one"):
        csv_parser.detect_date_format(["03/04/2026"])


def test_unreadable_file_returns_error_instead_of_raising(tmp_path):
    result = csv_parser.parse_csv(tmp_path / "missing.csv")
    assert not result.ok
    assert result.error
