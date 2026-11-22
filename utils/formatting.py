"""Display formatting shared by the desktop screens.

These helpers used to live inside ``app.py`` (Streamlit) and
``ui/transactions.py`` (Tk). They are plain functions now, so both the UI and
the tests can use them without starting a GUI toolkit.
"""

from datetime import datetime

from utils.calculations import format_inr


def format_transaction_date(iso_date):
    """Turn ``"2026-11-22"`` into ``"22 Nov 2026"`` for display."""
    try:
        return datetime.strptime(str(iso_date), "%Y-%m-%d").strftime("%d %b %Y")
    except (TypeError, ValueError):
        return str(iso_date)


def shorten(text, limit=46):
    """Trim long descriptions so table columns keep their shape."""
    text = str(text or "")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def transaction_type_label(value):
    """Return the friendly type name, e.g. ``income`` -> ``Income``."""
    return str(value or "").capitalize()


def format_signed_amount(amount, transaction_type=None):
    """Prefix income with ``+`` and expenses with ``−``, then format as INR."""
    prefix = "+" if transaction_type == "income" else "−"
    return prefix + format_inr(amount)


def transaction_label(row):
    """Build the readable single-line label formerly used by Streamlit."""
    return (
        f"#{row['id']} · {row['transaction_date']} · "
        f"{transaction_type_label(row['transaction_type'])} · "
        f"{format_inr(row['amount'])} · {row['category']}"
    )
