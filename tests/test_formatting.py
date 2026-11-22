"""Tests for display helpers moved out of the old Streamlit and Tk screens."""

from utils.formatting import (
    format_signed_amount,
    format_transaction_date,
    shorten,
    transaction_label,
    transaction_type_label,
)


def test_format_transaction_date():
    assert format_transaction_date("2026-11-22") == "22 Nov 2026"
    assert format_transaction_date("not-a-date") == "not-a-date"


def test_shorten():
    assert shorten("Short text") == "Short text"
    assert shorten("A" * 60) == "A" * 45 + "…"


def test_type_and_amount_labels():
    assert transaction_type_label("income") == "Income"
    assert format_signed_amount(1234.5, "income") == "+₹1,234.50"
    assert format_signed_amount(1234.5, "expense") == "−₹1,234.50"


def test_transaction_label_matches_old_streamlit_dropdown():
    row = {
        "id": 7,
        "transaction_date": "2026-11-22",
        "transaction_type": "expense",
        "amount": 42.5,
        "category": "Food",
    }
    assert transaction_label(row) == "#7 · 2026-11-22 · Expense · ₹42.50 · Food"
