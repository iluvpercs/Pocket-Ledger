"""The append-only change log.

Whenever a transaction is created, edited or deleted, Pocket Ledger writes a
small row to ``sync_changes``. The table only ever grows; rows are never
updated. Each row gets an increasing ``seq`` number, so a future phone can say
"send me everything after seq 42" instead of downloading the whole database.

This module contains only the change-log SQL. Transaction rules (validation,
what counts as an edit) stay in ``database.py``.
"""

import json
from datetime import datetime, timezone

# The columns that make up a transaction snapshot inside the log.
PAYLOAD_FIELDS = (
    "uuid",
    "transaction_type",
    "amount",
    "category",
    "description",
    "transaction_date",
    "created_at_ms",
    "updated_at_ms",
    "deleted_at_ms",
    "revision",
    "origin_device_id",
    "last_modified_by",
    "import_hash",
    "external_ref",
    "import_batch_id",
    "account_label",
)


def utc_now_ms():
    """Return the current UTC time as whole milliseconds.

    A single number is easier to compare than a formatted date string, and
    using UTC avoids timezone confusion between devices.
    """
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _value(row, key, default=None):
    """Read a key from either a dict or a sqlite3.Row."""
    try:
        return row[key]
    except (KeyError, IndexError):
        return default


def transaction_payload(row):
    """Turn a transaction row into the dict stored in the change log.

    A snapshot is stored (not just the changed field) so an old change can
    still be understood even after the live row has been edited again.
    """
    return {field: _value(row, field) for field in PAYLOAD_FIELDS}


def append_change(
    connection,
    entity_uuid,
    operation,
    payload,
    origin_device_id,
    base_revision=None,
    new_revision=None,
    entity_type="transaction",
    recorded_at_ms=None,
):
    """Append one change and return its ``seq`` number.

    ``connection`` must already be inside the same transaction as the
    transaction write. That way the data row and its log entry are saved
    together, or not at all.
    """
    if operation not in ("insert", "update", "delete"):
        raise ValueError("Unknown change operation.")

    cursor = connection.execute(
        """
        INSERT INTO sync_changes
            (entity_type, entity_uuid, operation, base_revision,
             new_revision, payload, origin_device_id, recorded_at_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entity_type,
            str(entity_uuid),
            operation,
            base_revision,
            new_revision,
            json.dumps(payload, sort_keys=True),
            str(origin_device_id),
            recorded_at_ms if recorded_at_ms is not None else utc_now_ms(),
        ),
    )
    return cursor.lastrowid


def get_changes_since(connection, since_seq=0, limit=500, exclude_device_id=None):
    """Return changes newer than ``since_seq``, oldest first.

    ``exclude_device_id`` lets a device avoid receiving its own edits back
    during a future sync. The limit keeps responses small.
    """
    sql = "SELECT * FROM sync_changes WHERE seq > ?"
    parameters = [int(since_seq)]

    if exclude_device_id:
        sql += " AND origin_device_id <> ?"
        parameters.append(str(exclude_device_id))

    sql += " ORDER BY seq LIMIT ?"
    parameters.append(int(limit))

    return connection.execute(sql, parameters).fetchall()


def count_changes(connection):
    """Return how many change-log rows exist (used by tests and status screens)."""
    return int(connection.execute("SELECT COUNT(*) FROM sync_changes").fetchone()[0])


def latest_seq(connection):
    """Return the newest change number, or 0 when the log is empty."""
    value = connection.execute("SELECT MAX(seq) FROM sync_changes").fetchone()[0]
    return int(value or 0)
