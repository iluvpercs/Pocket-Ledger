"""Exact money conversion between user input and integer minor units.

Every amount is stored as an ``INTEGER`` number of minor units. ``Decimal`` is
used for parsing and display so a value such as ``0.1`` never passes through
binary floating point on its way to the database.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from utils.currencies import get_precision

# SQLite INTEGER is a signed 64-bit value.
MAX_MINOR = (1 << 63) - 1
MIN_MINOR = -(1 << 63)

CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "KRW": "₩",
    "CNY": "¥",
    "AUD": "A$",
    "CAD": "C$",
    "NZD": "NZ$",
    "CHF": "CHF ",
    "SGD": "S$",
    "HKD": "HK$",
    "THB": "฿",
    "VND": "₫",
    "BHD": "BD ",
    "KWD": "KD ",
    "OMR": "OMR ",
    "JOD": "JD ",
    "TND": "DT ",
    "IQD": "IQD ",
    "LYD": "LYD ",
}


class MoneyError(ValueError):
    """Raised when an amount cannot be represented as integer minor units."""


def _decimal_unit(precision):
    if precision not in (0, 2, 3):
        raise MoneyError("Currency precision must be 0, 2 or 3.")
    return Decimal(1).scaleb(-int(precision))


def to_decimal(value, precision=2, strict=False):
    """Parse ``value`` into a Decimal quantised to ``precision``.

    ``strict`` is used for manual entry: an input with more fractional digits
    than the currency allows is rejected instead of silently rounded. CSV
    import and migration pass ``strict=False`` and use ``ROUND_HALF_UP``.
    """
    unit = _decimal_unit(precision)
    if isinstance(value, Decimal):
        amount = value
    else:
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise MoneyError("Amount must be a number.") from None

    if not amount.is_finite():
        raise MoneyError("Amount must be a finite number.")

    try:
        quantised = amount.quantize(unit, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        # Decimal's context precision cannot represent values this large, and
        # they could not be stored in a 64-bit SQLite INTEGER anyway.
        raise MoneyError("Amount is too large to store.") from None
    if strict and quantised != amount:
        raise MoneyError(
            f"Amount cannot have more than {int(precision)} decimal places "
            "for this account."
        )
    return quantised


def parse_to_minor(value, precision=2, strict=True):
    """Convert a signed Decimal-compatible value to integer minor units."""
    precision = int(precision)
    amount = to_decimal(value, precision=precision, strict=strict)
    scale = 10 ** precision
    minor = int((amount * scale).to_integral_value(rounding=ROUND_HALF_UP))
    if minor > MAX_MINOR or minor < MIN_MINOR:
        raise MoneyError("Amount is too large to store.")
    return minor


def minor_to_decimal(minor, precision=2):
    """Convert integer minor units back to a Decimal with the right scale."""
    precision = int(precision)
    _decimal_unit(precision)  # validate precision
    if isinstance(minor, bool) or not isinstance(minor, int):
        raise MoneyError("Minor units must be an integer.")
    return (Decimal(int(minor)) / (10 ** precision)).quantize(
        _decimal_unit(precision)
    )


def format_money(minor, currency_code, precision=None):
    """Format integer minor units for display, for example ``₹1,250.00``."""
    code = str(currency_code or "").strip().upper()
    if precision is None:
        precision = get_precision(code)
    precision = int(precision)
    amount = minor_to_decimal(minor, precision)
    symbol = CURRENCY_SYMBOLS.get(code, f"{code} ")
    return f"{symbol}{amount:,.{precision}f}"


def currency_precision(currency_code):
    """Small convenience wrapper used by the data layer and importer."""
    return get_precision(currency_code)
