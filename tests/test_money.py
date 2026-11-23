"""Exact integer minor-unit money conversion tests."""

from decimal import Decimal

import pytest

from utils.money import (
    MAX_MINOR,
    MoneyError,
    format_money,
    minor_to_decimal,
    parse_to_minor,
)


@pytest.mark.parametrize(
    ("value", "precision", "expected"),
    [
        ("125.50", 2, 12550),
        (125.5, 2, 12550),
        (Decimal("0.10"), 2, 10),
        ("0.1", 2, 10),
        ("-180.00", 2, -18000),
        ("1000", 0, 1000),
        ("1.234", 3, 1234),
        (Decimal("19.995"), 2, 2000),
        ("125.499999", 2, 12550),
    ],
)
def test_parse_to_minor_rounds_half_up(value, precision, expected):
    assert parse_to_minor(value, precision=precision, strict=False) == expected


def test_strict_manual_entry_rejects_excess_decimal_places():
    with pytest.raises(MoneyError, match="decimal places"):
        parse_to_minor("125.499", precision=2, strict=True)
    with pytest.raises(MoneyError, match="decimal places"):
        parse_to_minor("1000.5", precision=0, strict=True)
    with pytest.raises(MoneyError, match="decimal places"):
        parse_to_minor("1.2345", precision=3, strict=True)

    # Trailing zeroes do not count as extra precision.
    assert parse_to_minor("125.500", precision=2, strict=True) == 12550


@pytest.mark.parametrize("value", ["not-a-number", "", None, "NaN", "Infinity"])
def test_parse_to_minor_rejects_non_finite_or_junk(value):
    with pytest.raises(MoneyError):
        parse_to_minor(value, precision=2, strict=True)


def test_parse_to_minor_rejects_overflow():
    with pytest.raises(MoneyError, match="too large"):
        parse_to_minor("1e30", precision=2, strict=False)
    assert parse_to_minor(MAX_MINOR, precision=0, strict=False) == MAX_MINOR


def test_minor_to_decimal_keeps_currency_scale():
    assert minor_to_decimal(12550, 2) == Decimal("125.50")
    assert minor_to_decimal(1000, 0) == Decimal("1000")
    assert minor_to_decimal(1234, 3) == Decimal("1.234")


@pytest.mark.parametrize(
    ("minor", "code", "precision", "expected"),
    [
        (12550, "INR", 2, "₹125.50"),
        (125000, "INR", 2, "₹1,250.00"),
        (1000, "JPY", 0, "¥1,000"),
        (1234, "KWD", 3, "KD 1.234"),
        (250, "ZZZ", 2, "ZZZ 2.50"),
    ],
)
def test_format_money(minor, code, precision, expected):
    assert format_money(minor, code, precision) == expected
