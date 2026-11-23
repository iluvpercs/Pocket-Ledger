"""The append-only change log.

Whenever a transaction or account is created, edited or deleted, Pocket Ledger
writes a small row to ``sync_changes``. The table only ever grows; rows are
never updated. Each row gets an increasing ``seq`` number, so a future phone can
say "send me everything after seq 42" instead of downloading the whole database.

Payloads are snapshots. Schema version 4 introduced ``payload_version``:
version 1 is the historical transaction payload with a floating-point
``amount``; version 2 uses integer ``amount_minor`` plus account/currency
fields. Old rows are never rewritten. :func:`upgrade_payload` lets a reader
consume a v1 snapshot without changing the log.

This module contains only the change-log SQL. Transaction/account rules
(validation, what counts as an edit) stay in ``database.py``.
"""

import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sync.identity import DEFAULT_ACCOUNT_UUID
from utils.currencies import DEFAULT_CURRENCY_CODE, DEFAULT_CURRENCY_PRECISION

# The historical v1 transaction snapshot fields. Keep this tuple for the
# recovery script and for readers that have to understand old rows.
LEGACY_PAYLOAD_FIELDS = (
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

# Backwards-compatible name used by the v3 recovery script.
PAYLOAD_FIELDS = LEGACY_PAYLOAD_FIELDS

# A v2 transaction snapshot deliberately has no legacy ``amount`` field.
TRANSACTION_PAYLOAD_FIELDS = (
    "uuid",
    "transaction_type",
    "amount_minor",
    "currency_code",
    "currency_precision",
    "account_uuid",
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

ACCOUNT_PAYLOAD_FIELDS = (
    "uuid",
    "name",
    "currency_code",
    "currency_precision",
    "is_default",
    "created_at_ms",
    "updated_at_ms",
    "deleted_at_ms",
    "revision",
    "origin_device_id",
    "last_modified_by",
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


def _has_key(row, key):
    if isinstance(row, dict):
        return key in row
    try:
        return key in row.keys()
    except AttributeError:
        return False


def transaction_payload_v1(row):
    """Return the historical transaction snapshot, with float ``amount``."""
    return {field: _value(row, field) for field in LEGACY_PAYLOAD_FIELDS}


def transaction_payload(row, version=None):
    """Return a transaction snapshot.

    ``version=None`` chooses v2 when the row contains ``amount_minor`` and v1
    otherwise. That keeps the v3 recovery script and old migrations producing
    exactly the payload they always did, while database writes use v2.
    """
    if version is None:
        version = 2 if _has_key(row, "amount_minor") else 1
    if int(version) == 1:
        return transaction_payload_v1(row)
    return {field: _value(row, field) for field in TRANSACTION_PAYLOAD_FIELDS}


def account_payload(row):
    """Return the account snapshot stored in the change log."""
    return {field: _value(row, field) for field in ACCOUNT_PAYLOAD_FIELDS}


def _sync_changes_columns(connection):
    cached = getattr(connection, "_pocket_ledger_sync_columns", None)
    if cached is None:
        cached = {
            row[1] for row in connection.execute("PRAGMA table_info(sync_changes)")
        }
        try:
            connection._pocket_ledger_sync_columns = cached
        except AttributeError:
            pass
    return cached


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
    payload_version=None,
):
    """Append one change and return its ``seq`` number.

    ``connection`` must already be inside the same transaction as the data
    write, so the row and its log entry are saved together or not at all.
    """
    if operation not in ("insert", "update", "delete"):
        raise ValueError("Unknown change operation.")

    if payload_version is None:
        payload_version = (
            2
            if entity_type == "account" or _has_key(payload, "amount_minor")
            else 1
        )
    payload_version = int(payload_version)

    columns = _sync_changes_columns(connection)
    if "payload_version" in columns:
        cursor = connection.execute(
            """
            INSERT INTO sync_changes
                (entity_type, entity_uuid, operation, base_revision,
                 new_revision, payload, origin_device_id, recorded_at_ms,
                 payload_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                payload_version,
            ),
        )
    else:
        # Historical v2/v3 migrations run before the column exists.
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
    """Return changes newer than ``since_seq``, oldest first (raw rows)."""
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


def upgrade_payload(
    payload,
    entity_type="transaction",
    default_account_uuid=DEFAULT_ACCOUNT_UUID,
    default_currency_code=DEFAULT_CURRENCY_CODE,
    default_currency_precision=DEFAULT_CURRENCY_PRECISION,
):
    """Return a canonical payload without rewriting the stored row.

    v1 transaction payloads get ``amount_minor``, ``account_uuid`` and currency
    fields derived from the legacy INR default. v2 payloads pass through. The
    historical floating-point ``amount`` is removed from the returned dict so
    callers have one canonical representation.
    """
    data = dict(payload or {})
    if entity_type == "account":
        return data

    if "amount_minor" in data and data.get("amount_minor") is not None:
        data.setdefault("currency_code", default_currency_code)
        data.setdefault("currency_precision", default_currency_precision)
        data.setdefault("account_uuid", default_account_uuid)
        data.pop("amount", None)
        return data

    amount = data.get("amount")
    if amount is None:
        amount = 0
    minor = int(
        (Decimal(str(amount)) * (10 ** int(default_currency_precision))).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
    data["amount_minor"] = minor
    data["currency_code"] = default_currency_code
    data["currency_precision"] = int(default_currency_precision)
    data["account_uuid"] = default_account_uuid
    data.pop("amount", None)
    return data


def upgrade_change(change):
    """Return one change row as a dict with a parsed, upgraded payload."""
    data = dict(change)
    try:
        payload = json.loads(data.get("payload") or "{}")
    except (TypeError, ValueError):
        payload = {}
    version = int(data.get("payload_version") or 1)
    data["payload"] = upgrade_payload(payload, data.get("entity_type", "transaction"))
    data["payload_version"] = max(version, 2)
    return data
