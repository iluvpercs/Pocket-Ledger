"""Pure CSV statement parsing - no GUI, no database, no network.

Bank exports are messy: they often start with account details, use different
separators and date formats, and end with a totals line. This module finds the
real table, reads each row defensively and returns a :class:`ParseResult` that
the preview screen can show. A bad row becomes an ``error`` row with a reason;
it never raises out of the row loop.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

# Canonical field names used by auto-detection and by the UI mapping controls.
FIELDS = ("date", "description", "amount", "debit", "credit", "balance", "reference")

# Only day-first layouts are accepted (plus ISO), so a day/month mix-up cannot
# quietly turn 03/04 into March 4th.
DATE_FORMATS = (
    ("%d/%m/%Y", "DD/MM/YYYY"),
    ("%d-%m-%Y", "DD-MM-YYYY"),
    ("%d/%m/%y", "DD/MM/YY"),
    ("%Y-%m-%d", "YYYY-MM-DD"),
    ("%d-%b-%Y", "DD-Mon-YYYY"),
    ("%d-%B-%Y", "DD-Month-YYYY"),
    ("%d %b %Y", "DD Mon YYYY"),
    ("%d %B %Y", "DD Month YYYY"),
)

HEADER_KEYWORDS = {
    "date": ("date", "txndate", "transactiondate", "postingdate", "valuedate", "trandate"),
    "description": (
        "description", "narration", "particulars", "details", "memo",
        "transactiondetails", "remarks", "purpose", "narrative",
    ),
    "amount": ("amount", "amountinr", "transactionamount", "amt", "value"),
    "debit": (
        "debit", "debitamount", "withdrawal", "withdrawalamount", "withdraw",
        "paidout", "moneyout", "dr", "outflow", "expense",
    ),
    "credit": (
        "credit", "creditamount", "deposit", "depositamount", "paidin",
        "moneyin", "cr", "inflow", "income",
    ),
    "balance": ("balance", "closingbalance", "runningbalance", "availablebalance"),
    "reference": (
        "reference", "ref", "refno", "chequeno", "chqno", "transactionid",
        "txnid", "utr", "voucher",
    ),
}

SUMMARY_RE = re.compile(
    r"^(total|totals|subtotal|grandtotal|closingbalance|openingbalance|"
    r"balancebroughtforward|balancecarriedforward|statementtotal|endofstatement|"
    r"net(total)?|summary)",
    re.IGNORECASE,
)

CURRENCY_RE = re.compile(r"[₹$€£]|\b(?:INR|Rs\.?|USD)\b", re.IGNORECASE)
DR_CR_RE = re.compile(r"(dr|cr)\.?$", re.IGNORECASE)


class CSVParseError(ValueError):
    """A file-level problem (bad encoding, no header, unknown date layout)."""


class AmbiguousDateFormatError(CSVParseError):
    """Two or more date layouts fit the data equally well."""


@dataclass
class ParsedRow:
    """One candidate transaction produced from a CSV row."""

    row_number: int
    raw: dict
    date: str | None = None
    description: str = ""
    amount: Decimal | None = None
    transaction_type: str | None = None
    balance: Decimal | None = None
    reference: str | None = None
    category: str = ""
    account_label: str | None = None
    status: str = "ok"  # ok / warning / error
    reason: str = ""
    import_hash: str | None = None
    duplicate_status: str = "new"  # new / duplicate / previously_deleted
    included: bool = True
    force_include: bool = False
    occurrence: int = 0
    occurrence_override: int | None = None

    @property
    def importable(self):
        return self.status in ("ok", "warning") and self.amount is not None and bool(self.date)


@dataclass
class ParseResult:
    """Everything the preview screen needs to know about one file."""

    source_file: str
    encoding: str = ""
    delimiter: str = ","
    header_row: int | None = None
    header: list = field(default_factory=list)
    mapping: dict = field(default_factory=dict)
    date_format: str | None = None
    rows: list = field(default_factory=list)
    skipped_rows: list = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self):
        return self.error is None and self.header_row is not None

    @property
    def counts(self):
        return {
            "total": len(self.rows),
            "ok": sum(row.status == "ok" for row in self.rows),
            "warning": sum(row.status == "warning" for row in self.rows),
            "error": sum(row.status == "error" for row in self.rows),
        }


# ------------------------------------------------------------------ detection
def detect_encoding(path):
    """Try the encodings banks commonly use, in order, and return the winner."""
    data = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            data.decode(encoding)
        except UnicodeDecodeError:
            continue
        return encoding
    raise CSVParseError("Could not work out this file's text encoding.")


def detect_delimiter(text):
    """Pick the separator that gives the most consistent column count."""
    sample = "\n".join(text.splitlines()[:40])
    best = (",", -1.0)
    for delimiter in (",", ";", "\t"):  # comma wins ties
        try:
            rows = list(csv.reader(io.StringIO(sample, newline=""), delimiter=delimiter))
        except csv.Error:
            continue
        # Single-cell rows (preamble/footer text) carry no delimiter evidence.
        counts = [
            len(row)
            for row in rows
            if len(row) > 1 and any(cell.strip() for cell in row)
        ]
        if not counts:
            continue
        common = max(set(counts), key=counts.count)
        score = sum(1 for count in counts if count == common) * (
            1 + min(common, 10) / 10
        )
        if score > best[1]:
            best = (delimiter, score)
    return best[0]


def _normalise(text):
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def _header_score(cell, keywords):
    """3 for an exact match, 2 when the keyword is inside the cell, 1 reverse."""
    value = _normalise(cell)
    if not value:
        return 0
    best = 0
    for keyword in keywords:
        if value == keyword:
            best = max(best, 3)
        elif keyword in value:
            best = max(best, 2)
        elif len(value) >= 3 and value in keyword:
            best = max(best, 1)
    return best


def detect_column_mapping(header):
    """Return ``{field: column index or None}`` for a detected header row."""
    mapping = {}
    claimed = set()
    # Strongest signals first: an "Amount" cell should not steal "Deposit".
    order = ("date", "description", "debit", "credit", "amount", "balance", "reference")
    for field_name in order:
        scores = [
            (_header_score(cell, HEADER_KEYWORDS[field_name]), index)
            for index, cell in enumerate(header)
            if index not in claimed
        ]
        best_score, best_index = max(scores, default=(0, None))
        if best_score >= 2 and best_index is not None:
            mapping[field_name] = best_index
            claimed.add(best_index)
        else:
            mapping[field_name] = None
    return {name: mapping.get(name) for name in FIELDS}


def find_header_row(rows):
    """Return the index of the real header, or None for an unreadable file."""
    best = (None, 0)
    for index, cells in enumerate(rows[:30]):
        mapping = detect_column_mapping(cells)
        found = sum(value is not None for value in mapping.values())
        has_core = mapping.get("date") is not None and (
            mapping.get("description") is not None
            or mapping.get("amount") is not None
            or mapping.get("debit") is not None
            or mapping.get("credit") is not None
        )
        score = found + (3 if has_core else 0)
        if has_core and score > best[1]:
            best = (index, score)
    return best[0]


def resolve_mapping(header, override=None):
    """Merge a manual mapping over the auto-detected one.

    Values may be column indexes, exact header names, or ``None``/``"none"``
    to switch a field off. Fields left out of ``override`` keep their detected
    column.
    """
    result = detect_column_mapping(header)
    if not override:
        return result
    for field_name, value in override.items():
        if field_name not in FIELDS:
            continue
        if value is None or str(value).strip().lower() in ("", "none", "-", "--none--"):
            result[field_name] = None
        elif isinstance(value, int):
            result[field_name] = value if 0 <= value < len(header) else None
        else:
            wanted = _normalise(value)
            result[field_name] = next(
                (index for index, cell in enumerate(header) if _normalise(cell) == wanted),
                None,
            )
    return result


def _parses(value, code):
    try:
        datetime.strptime(value, code)
        return True
    except ValueError:
        return False


def detect_date_format(values):
    """Choose one day-first layout for the whole file, or report ambiguity.

    Values that fit no supported layout (footer text, for example) are ignored
    rather than making every candidate fail.
    """
    clean = [str(value).strip() for value in values if str(value or "").strip()]
    date_like = [
        value for value in clean if any(_parses(value, code) for code, _ in DATE_FORMATS)
    ]
    if not date_like:
        raise CSVParseError("No dates were found in this statement.")

    matches = {}
    for code, _ in DATE_FORMATS:
        if all(_parses(value, code) for value in date_like):
            matches[code] = [
                datetime.strptime(value, code).date() for value in date_like
            ]

    if not matches:
        raise CSVParseError(
            "Dates must use DD/MM/YYYY, DD-MM-YYYY, DD/MM/YY, YYYY-MM-DD or DD Mon YYYY."
        )
    if len(matches) > 1:
        first = next(iter(matches.values()))
        if any(parsed != first for parsed in matches.values()):
            labels = [label for code, label in DATE_FORMATS if code in matches]
            raise AmbiguousDateFormatError(
                "More than one date format fits this file: " + ", ".join(labels) + "."
            )
    return next(iter(matches))


def date_format_label(code):
    """Return the friendly name used in the UI for a strptime code."""
    return dict(DATE_FORMATS).get(code, str(code or "unknown"))


# ------------------------------------------------------------------- parsing
def parse_date(value, date_format):
    """Parse one date with the file's chosen format; return an ISO string."""
    text = str(value or "").strip()
    if not text:
        raise ValueError("Date is missing.")
    return datetime.strptime(text, date_format).date().isoformat()


def parse_amount(value):
    """Parse money with Decimal, returning a signed value (negative = expense).

    Handles Indian grouping (1,23,456.78), currency marks, parentheses,
    ``Dr``/``Cr`` suffixes and blank debit/credit cells. Never uses float.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))

    text = str(value).strip()
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    suffix_match = DR_CR_RE.search(text)
    suffix = suffix_match.group(1).lower() if suffix_match else None
    if suffix_match:
        text = text[: suffix_match.start()].strip()

    text = CURRENCY_RE.sub("", text)
    text = text.replace("\u00a0", "").replace(" ", "").replace(",", "")
    if text.startswith("+"):
        text = text[1:]
    elif text.startswith("-"):
        negative = True
        text = text[1:]
    if not text:
        return None

    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise ValueError(f"Could not read amount {str(value)!r}.") from None
    if not amount.is_finite():
        raise ValueError(f"Could not read amount {str(value)!r}.")

    if suffix == "dr":
        negative = True
    elif suffix == "cr":
        negative = False
    if negative:
        amount = -amount
    return amount.quantize(Decimal("0.01"))


def _cell(cells, index):
    if index is None or index >= len(cells):
        return ""
    return str(cells[index] or "").strip()


def is_summary_row(cells):
    """True for totals/closing-balance/footer lines, not real transactions."""
    filled = [cell.strip() for cell in cells if str(cell or "").strip()]
    if not filled:
        return True
    return bool(SUMMARY_RE.match(filled[0]))


def parse_csv(path, mapping=None, date_format=None):
    """Parse ``path`` into a :class:`ParseResult`.

    ``mapping`` can override any detected column, and ``date_format`` can
    override the detected strptime code. File-level problems are returned in
    ``result.error`` so the UI can show them without a traceback.
    """
    path = Path(path)
    result = ParseResult(source_file=str(path))
    try:
        result.encoding = detect_encoding(path)
        text = path.read_text(encoding=result.encoding)
    except (OSError, UnicodeError, CSVParseError) as error:
        result.error = str(error)
        return result

    try:
        result.delimiter = detect_delimiter(text)
        rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=result.delimiter))
    except csv.Error as error:
        result.error = f"Could not read this CSV file: {error}"
        return result

    header_index = find_header_row(rows)
    if header_index is None:
        result.error = "Could not find a header row with Date and Description/Amount columns."
        return result

    result.header_row = header_index
    result.header = [cell.strip() for cell in rows[header_index]]
    result.mapping = resolve_mapping(result.header, mapping)

    date_column = result.mapping.get("date")
    if date_column is None:
        result.error = "The Date column could not be identified. Map it manually."
        return result

    samples = [_cell(cells, date_column) for cells in rows[header_index + 1 :]]
    try:
        result.date_format = date_format or detect_date_format(samples)
    except CSVParseError as error:
        result.error = str(error)
        return result

    for offset, cells in enumerate(rows[header_index + 1 :], start=1):
        row_number = header_index + offset + 1
        raw = {name: _cell(cells, index) for name, index in result.mapping.items()}
        if not any(raw.values()):
            result.skipped_rows.append((row_number, "empty row"))
            continue
        if is_summary_row(cells):
            result.skipped_rows.append((row_number, "summary/footer row"))
            continue

        row = ParsedRow(row_number=row_number, raw=raw)
        try:
            row.date = parse_date(raw.get("date"), result.date_format)
            row.description = raw.get("description", "")
            row.reference = raw.get("reference") or None

            debit = parse_amount(raw.get("debit"))
            credit = parse_amount(raw.get("credit"))
            amount = parse_amount(raw.get("amount"))

            # Many banks write 0.00 in the inactive column instead of leaving
            # it blank; that is not a "both columns filled" conflict.
            if debit is not None and debit == 0:
                debit = None
            if credit is not None and credit == 0:
                credit = None

            if result.mapping.get("debit") is not None or result.mapping.get("credit") is not None:
                if debit is not None and credit is not None:
                    raise ValueError("Both debit and credit cells are filled.")
                if debit is not None:
                    amount = -abs(debit)
                elif credit is not None:
                    amount = abs(credit)
                else:
                    amount = None
            if amount is None:
                raise ValueError("Amount is missing.")
            if amount == 0:
                raise ValueError("Amount must not be zero.")

            row.amount = amount
            row.transaction_type = "income" if amount > 0 else "expense"

            if result.mapping.get("balance") is not None:
                try:
                    row.balance = parse_amount(raw.get("balance"))
                except ValueError:
                    row.status = "warning"
                    row.reason = "Balance cell could not be read."

            if not row.description:
                row.status = "warning"
                row.reason = row.reason or "Description is empty."
        except Exception as error:  # one bad row must not stop the import
            row.status = "error"
            row.reason = str(error) or error.__class__.__name__
            row.amount = None
            row.transaction_type = None

        result.rows.append(row)

    return result
