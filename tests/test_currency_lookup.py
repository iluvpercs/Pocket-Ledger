"""ISO 4217 precision lookup tests."""

import pytest

from utils import currencies


@pytest.mark.parametrize(
    ("code", "precision"),
    [
        ("INR", 2),
        ("USD", 2),
        ("EUR", 2),
        ("JPY", 0),
        ("KRW", 0),
        ("CLP", 0),
        ("VND", 0),
        ("BHD", 3),
        ("IQD", 3),
        ("JOD", 3),
        ("KWD", 3),
        ("OMR", 3),
        ("TND", 3),
    ],
)
def test_known_currency_precisions(code, precision):
    assert currencies.get_precision(code) == precision


def test_lookup_is_case_and_whitespace_insensitive():
    assert currencies.get_precision("  inr ") == 2
    assert currencies.normalise_currency_code(" kwd ") == "KWD"


def test_unknown_codes_are_rejected():
    with pytest.raises(currencies.UnknownCurrencyError):
        currencies.get_precision("ZZZ")
    with pytest.raises(currencies.UnknownCurrencyError):
        currencies.get_precision("")
    with pytest.raises(currencies.UnknownCurrencyError):
        currencies.get_precision(None)


def test_iso_codes_with_four_decimals_are_known_but_unsupported():
    assert currencies.CURRENCY_PRECISION["CLF"] == 4
    assert currencies.CURRENCY_PRECISION["UYW"] == 4
    with pytest.raises(currencies.UnsupportedCurrencyError):
        currencies.get_precision("CLF")
    assert not currencies.is_supported("CLF")
    assert currencies.is_supported("INR")


def test_default_currency_is_inr():
    assert currencies.DEFAULT_CURRENCY_CODE == "INR"
    assert currencies.DEFAULT_CURRENCY_PRECISION == 2
    assert currencies.SUPPORTED_PRECISIONS == {0, 2, 3}
