"""Stable import hashes and duplicate detection.

The hash is deliberately small and deterministic: normalised date, signed
amount in paise and a whitespace-collapsed lowercase description. An
occurrence index (0, 1, 2, ...) is appended so two genuinely identical
same-day purchases are both kept, while importing the same file twice produces
exactly the same hashes every time.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal, ROUND_HALF_UP


def normalise_description(text):
    """Collapse whitespace and lowercase a description for comparison."""
    return " ".join(str(text or "").lower().split())


def amount_to_paise(amount):
    """Convert a signed Decimal amount into whole paise (no float involved)."""
    return int(
        (Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )


def build_import_hash(date_iso, amount, description, occurrence=0):
    """Return the sha256 duplicate marker stored in ``transactions.import_hash``."""
    payload = "|".join(
        (
            str(date_iso or ""),
            str(amount_to_paise(amount)),
            normalise_description(description),
            str(int(occurrence)),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _key(row):
    return (
        row.date,
        amount_to_paise(row.amount),
        normalise_description(row.description),
    )


def assign_hashes(rows):
    """Give every importable row a hash, counting identical rows in file order."""
    seen = {}
    for row in rows:
        if not row.importable:
            row.import_hash = None
            continue
        key = _key(row)
        file_occurrence = seen.get(key, 0)
        seen[key] = file_occurrence + 1
        occurrence = (
            row.occurrence_override
            if row.occurrence_override is not None
            else file_occurrence
        )
        row.occurrence = occurrence
        row.import_hash = build_import_hash(
            row.date, row.amount, row.description, occurrence
        )
    return rows


def reserve_free_occurrence(row, rows, connection):
    """Find an occurrence slot that is free in this file and in the database.

    The schema has a unique index on live ``import_hash`` values. A user who
    force-includes a duplicate therefore needs a new slot so the second
    identical payment can be stored as its own transaction.
    """
    key = _key(row)
    used = {other.occurrence for other in rows if other is not row and _key(other) == key}
    candidate = max([row.occurrence] + list(used)) + 1
    while candidate in used or read_duplicate_state(
        connection,
        build_import_hash(row.date, row.amount, row.description, candidate),
    ) != "new":
        candidate += 1
    return candidate


def classify_rows(rows, connection):
    """Mark each row new / duplicate / previously_deleted using the live table.

    Soft-deleted transactions are included in the lookup: their unique index no
    longer blocks a re-import, but the user should still be told that a match
    existed before.
    """
    counts = {"new": 0, "duplicate": 0, "previously_deleted": 0}
    for row in rows:
        if not row.import_hash:
            row.duplicate_status = "new"
            continue
        found = connection.execute(
            "SELECT deleted_at_ms FROM transactions WHERE import_hash = ?",
            (row.import_hash,),
        ).fetchone()
        if found is None:
            status = "new"
        elif found[0] is None:
            status = "duplicate"
        else:
            status = "previously_deleted"
        row.duplicate_status = status
        counts[status] += 1
    return counts


def read_duplicate_state(connection, import_hash):
    """Return 'new', 'duplicate' or 'previously_deleted' for one hash."""
    if not import_hash:
        return "new"
    found = connection.execute(
        "SELECT deleted_at_ms FROM transactions WHERE import_hash = ?",
        (import_hash,),
    ).fetchone()
    if found is None:
        return "new"
    return "duplicate" if found[0] is None else "previously_deleted"
