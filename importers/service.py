"""CSV import service: parse -> preview -> user edits -> atomic commit.

This module is the only place that knows the whole workflow. It never builds
widgets. All writes go through the public ``database.py`` functions inside one
``database.atomic_write()`` block, so UUIDs, revisions, device ids and change
log entries are created exactly as they are for a manually added transaction.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import date as date_type
from decimal import Decimal
from pathlib import Path

import database
from importers import csv_parser, dedupe
from sync.identity import get_or_create_device_id
from sync.store import utc_now_ms

DEFAULT_RULES_PATH = Path(__file__).with_name("rules.json")

# Used if the rules file is missing, so the importer still works.
FALLBACK_RULES = {
    "default_category": "Other",
    "categories": {
        "Food": ["swiggy", "zomato", "restaurant", "cafe", "grocery"],
        "Transport": ["uber", "ola", "petrol", "fuel", "metro"],
        "Salary": ["salary", "payroll", "stipend"],
    },
}


@dataclass
class ImportPreview:
    """A mutable model the UI can edit before anything is saved."""

    source_file: str
    parse_result: csv_parser.ParseResult
    rows: list
    batch_id: str
    rules: dict
    mapping: dict

    @property
    def default_category(self):
        return str(self.rules.get("default_category", "Other"))


@dataclass
class ImportSummary:
    """Counts returned after a committed import."""

    batch_id: str = ""
    imported: int = 0
    skipped_duplicates: int = 0
    excluded: int = 0
    errors: int = 0
    imported_ids: list = field(default_factory=list)

    @property
    def total_rows(self):
        return self.imported + self.skipped_duplicates + self.excluded + self.errors


# ---------------------------------------------------------------------- rules
def load_rules(path=None):
    """Read the editable category rules JSON, falling back to built-in rules."""
    path = Path(path) if path else DEFAULT_RULES_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("categories"), dict):
            raise ValueError("rules file must contain a 'categories' object")
        return data
    except (OSError, ValueError):
        return dict(FALLBACK_RULES)


def categorize(description, rules):
    """Return the first matching category, or the configured default."""
    text = dedupe.normalise_description(description)
    for category, keywords in rules.get("categories", {}).items():
        for keyword in keywords or ():
            if dedupe.normalise_description(keyword) in text:
                return str(category)
    return str(rules.get("default_category", "Other"))


# --------------------------------------------------------------------- preview
def _classify(preview):
    """Refresh duplicate badges using a short-lived database connection."""
    connection = database.get_connection()
    try:
        return dedupe.classify_rows(preview.rows, connection)
    finally:
        if not database.in_write_transaction():
            connection.close()


def build_preview(parsed, source_file=None, rules=None, mapping=None):
    """Turn a ParseResult into an editable preview with hashes and badges."""
    if isinstance(parsed, (str, Path)):
        parsed = csv_parser.parse_csv(parsed, mapping=mapping)
    if not parsed.ok:
        raise ValueError(parsed.error or "This CSV file could not be read.")

    rules = rules if rules is not None else load_rules()
    effective_mapping = mapping or parsed.mapping
    dedupe.assign_hashes(parsed.rows)

    preview = ImportPreview(
        source_file=str(source_file or parsed.source_file),
        parse_result=parsed,
        rows=parsed.rows,
        batch_id=str(uuid.uuid4()),
        rules=rules,
        mapping=effective_mapping,
    )
    _classify(preview)

    for row in preview.rows:
        if not row.category:
            row.category = categorize(row.description, rules)
        row.included = row.importable and (
            row.force_include or row.duplicate_status == "new"
        )
    return preview


def apply_edits(preview, index, **changes):
    """Apply UI edits to one row, then recompute its hash and duplicate badge.

    Supported keys: ``date``, ``description``, ``amount``, ``category``,
    ``included`` and ``force_include``. Parsing errors are shown on the row
    instead of raising.
    """
    row = preview.rows[index]

    if "date" in changes:
        text = str(changes["date"] or "").strip()
        try:
            # The preview shows ISO dates, but accept the file's own layout too.
            try:
                row.date = date_type.fromisoformat(text).isoformat()
            except ValueError:
                row.date = csv_parser.parse_date(text, preview.parse_result.date_format)
        except (TypeError, ValueError) as error:
            row.date = None
            row.status = "error"
            row.reason = str(error)
    if "description" in changes:
        row.description = str(changes["description"] or "").strip()
    if "amount" in changes:
        try:
            amount = csv_parser.parse_amount(changes["amount"])
            if amount is None:
                raise ValueError("Amount is missing.")
            if amount == 0:
                raise ValueError("Amount must not be zero.")
            row.amount = amount
            row.transaction_type = "income" if amount > 0 else "expense"
            if row.status == "error" and "Amount" not in str(row.reason):
                row.status = "ok"
                row.reason = ""
        except (TypeError, ValueError) as error:
            row.amount = None
            row.status = "error"
            row.reason = str(error)
    if "category" in changes:
        row.category = str(changes["category"] or "").strip() or preview.default_category
    if "force_include" in changes:
        row.force_include = bool(changes["force_include"])
    if "included" in changes:
        row.included = bool(changes["included"])
        if row.included and row.duplicate_status == "duplicate":
            row.force_include = True
        elif not row.included:
            row.force_include = False
            row.occurrence_override = None
    if row.force_include and row.importable:
        row.included = True
        if row.duplicate_status == "duplicate" and row.occurrence_override is None:
            connection = database.get_connection()
            try:
                row.occurrence_override = dedupe.reserve_free_occurrence(
                    row, preview.rows, connection
                )
            finally:
                if not database.in_write_transaction():
                    connection.close()
    if row.status == "error":
        row.included = False
    if row.importable and row.status == "error":
        row.status = "ok"  # the user fixed the bad field
        row.reason = ""
    if row.importable and row.status == "warning" and not row.reason:
        row.status = "ok"

    dedupe.assign_hashes(preview.rows)
    _classify(preview)
    return row


def preview_counts(preview):
    """Row counts for the preview footer."""
    duplicates = sum(
        row.duplicate_status in ("duplicate", "previously_deleted")
        for row in preview.rows
    )
    included = sum(row.included and row.importable for row in preview.rows)
    return {
        "total": len(preview.rows),
        "included": included,
        "excluded": len(preview.rows) - included,
        "duplicates": duplicates,
        "errors": sum(row.status == "error" for row in preview.rows),
        "warnings": sum(row.status == "warning" for row in preview.rows),
    }


def preview_totals(preview):
    """Income, expense and net totals for the rows that will be imported."""
    income = Decimal("0")
    expense = Decimal("0")
    for row in preview.rows:
        if not row.included or not row.importable or row.amount is None:
            continue
        if row.amount > 0:
            income += row.amount
        else:
            expense += -row.amount
    return {"income": income, "expense": expense, "net": income - expense}


# --------------------------------------------------------------------- commit
def commit_preview(preview):
    """Save all included rows in ONE transaction, or save none of them.

    The import batch row and every change-log entry live in the same
    transaction as the transactions themselves, so a failure part-way through
    leaves the database exactly as it was.
    """
    summary = ImportSummary(batch_id=preview.batch_id)

    with database.atomic_write() as connection:
        device_id = get_or_create_device_id(connection)
        connection.execute(
            """
            INSERT INTO import_batches
                (batch_id, source_file, source_type, bank_format,
                 imported_at_ms, imported_count, skipped_count, device_id)
            VALUES (?, ?, 'csv', NULL, ?, 0, 0, ?)
            """,
            (
                preview.batch_id,
                preview.source_file,
                utc_now_ms(),
                device_id,
            ),
        )

        for row in preview.rows:
            if not row.included or not row.importable or row.import_hash is None:
                if row.status == "error":
                    summary.errors += 1
                elif row.duplicate_status == "duplicate" and row.importable:
                    summary.skipped_duplicates += 1
                else:
                    summary.excluded += 1
                continue

            # Recheck inside the write transaction: the preview may be stale.
            state = dedupe.read_duplicate_state(connection, row.import_hash)
            if state == "duplicate":
                summary.skipped_duplicates += 1
                continue

            try:
                new_id = database.add_transaction(
                    transaction_type=row.transaction_type,
                    amount=abs(row.amount),
                    category=row.category or preview.default_category,
                    description=row.description,
                    transaction_date=row.date,
                    import_hash=row.import_hash,
                    external_ref=row.reference,
                    import_batch_id=preview.batch_id,
                    account_label=row.account_label,
                )
            except ValueError as error:
                if "duplicate" in str(error).lower():
                    summary.skipped_duplicates += 1
                else:
                    summary.errors += 1
                continue
            summary.imported_ids.append(new_id)
            summary.imported += 1

        connection.execute(
            "UPDATE import_batches SET imported_count = ?, skipped_count = ? "
            "WHERE batch_id = ?",
            (summary.imported, summary.skipped_duplicates, preview.batch_id),
        )

    return summary


def import_csv_file(path, mapping=None, rules=None, source_file=None):
    """Convenience helper: parse and build a preview without any UI."""
    parsed = csv_parser.parse_csv(path, mapping=mapping)
    return build_preview(parsed, source_file=source_file, rules=rules, mapping=mapping)
