"""Stable import hashes and duplicate detection.

The hash is deliberately small and deterministic: normalised date, signed
amount in the account's integer minor units and a whitespace-collapsed
lowercase description. An occurrence index (0, 1, 2, ...) is appended so two
genuinely identical same-day purchases are both kept, while importing the same
file twice produces exactly the same hashes every time.

For a 2-decimal currency the minor value is the old "paise" value, so every
hash created before schema 4 remains byte-identical. Uniqueness is scoped to an
account, which lets the same statement be imported into two different accounts.
"""

from __future__ import annotations

import hashlib

from sync.identity import DEFAULT_ACCOUNT_UUID
from utils.currencies import DEFAULT_CURRENCY_PRECISION
from utils.money import parse_to_minor


def normalise_description(text):
    """Collapse whitespace and lowercase a description for comparison."""
    return " ".join(str(text or "").lower().split())


def amount_to_minor(amount, precision=DEFAULT_CURRENCY_PRECISION):
    """Convert a signed amount into whole minor units, without float math."""
    return parse_to_minor(amount, precision=precision, strict=False)


def amount_to_paise(amount):
    """Backwards-compatible alias for a 2-decimal currency."""
    return amount_to_minor(amount, precision=2)


def build_import_hash(
    date_iso,
    amount,
    description,
    occurrence=0,
    precision=DEFAULT_CURRENCY_PRECISION,
):
    """Return the sha256 duplicate marker stored in ``transactions.import_hash``."""
    payload = "|".join(
        (
            str(date_iso or ""),
            str(amount_to_minor(amount, precision=precision)),
            normalise_description(description),
            str(int(occurrence)),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _precision(row):
    return int(getattr(row, "currency_precision", DEFAULT_CURRENCY_PRECISION) or 2)


def _key(row):
    return (
        row.date,
        amount_to_minor(row.amount, _precision(row)),
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
            row.date,
            row.amount,
            row.description,
            occurrence,
            precision=_precision(row),
        )
    return rows


def _scope(row, account_uuid):
    return str(getattr(row, "account_uuid", None) or account_uuid or DEFAULT_ACCOUNT_UUID)


def reserve_free_occurrence(row, rows, connection, account_uuid=None):
    """Find an occurrence slot that is free in this file and in the account.

    The schema has a unique index on ``(account_uuid, import_hash)`` for live
    rows. A user who force-includes a duplicate needs a new slot so the second
    identical payment can be stored as its own transaction.
    """
    key = _key(row)
    used = {other.occurrence for other in rows if other is not row and _key(other) == key}
    candidate = max([row.occurrence] + list(used)) + 1
    scope = _scope(row, account_uuid)
    while candidate in used or read_duplicate_state(
        connection,
        build_import_hash(
            row.date,
            row.amount,
            row.description,
            candidate,
            precision=_precision(row),
        ),
        account_uuid=scope,
    ) != "new":
        candidate += 1
    return candidate


def classify_rows(rows, connection, account_uuid=None):
    """Mark each row new / duplicate / previously_deleted for one account.

    Soft-deleted transactions are included in the lookup: their unique index
    no longer blocks a re-import, but the user should still be told that a
    match existed before.
    """
    counts = {"new": 0, "duplicate": 0, "previously_deleted": 0}
    for row in rows:
        if not row.import_hash:
            row.duplicate_status = "new"
            continue
        scope = _scope(row, account_uuid)
        found = connection.execute(
            "SELECT deleted_at_ms FROM transactions "
            "WHERE import_hash = ? AND account_uuid = ?",
            (row.import_hash, scope),
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


def read_duplicate_state(
    connection,
    import_hash,
    account_uuid=DEFAULT_ACCOUNT_UUID,
):
    """Return 'new', 'duplicate' or 'previously_deleted' for one hash/account."""
    if not import_hash:
        return "new"
    found = connection.execute(
        "SELECT deleted_at_ms FROM transactions "
        "WHERE import_hash = ? AND account_uuid = ?",
        (import_hash, str(account_uuid)),
    ).fetchone()
    if found is None:
        return "new"
    return "duplicate" if found[0] is None else "previously_deleted"
