"""Small helpers used by the Pocket Ledger interface."""


def format_inr(amount):
    """Format a number as Indian Rupees, for example 1250 -> "₹1,250.00"."""
    return f"₹{float(amount):,.2f}"
