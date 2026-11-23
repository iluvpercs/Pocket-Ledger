"""Schema versions and safe database migrations.

SQLite stores a small number in every database file called ``user_version``.
Pocket Ledger uses it like a page number in a book:

* version 0 - the original table created by the first Streamlit release
* version 1 - "this is a Pocket Ledger database" (baseline marker)
* version 2 - UUIDs, timestamps, soft deletes and the sync change log
* version 3 - import metadata for future bank-statement importing
* version 4 - accounts, integer minor-unit money and versioned sync payloads

``initialize_database()`` calls :func:`migrate` on every start. If the database
is already current, the only work is one cheap ``PRAGMA`` read.

Each step runs inside its own transaction. If a step fails, SQLite rolls it
back completely, so a half-upgraded table is never left behind.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from sync.identity import (
    DEFAULT_ACCOUNT_NAME,
    DEFAULT_ACCOUNT_UUID,
    get_or_create_device_id,
)
from sync.store import (
    account_payload,
    append_change,
    transaction_payload_v1,
    utc_now_ms,
)
from utils.currencies import DEFAULT_CURRENCY_CODE, DEFAULT_CURRENCY_PRECISION
from utils.money import MoneyError, minor_to_decimal, parse_to_minor, to_decimal

# Increase this number when a new migration step is added.
SCHEMA_VERSION = 4

BACKUP_FOLDER_NAME = "backups"

# The exact table used before schema versioning existed. Keeping the original
# definition here lets a brand-new database start from the same shape and then
# travel through the same migrations as an old one.
CREATE_TRANSACTIONS_V1_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_type TEXT    NOT NULL CHECK (transaction_type IN ('income', 'expense')),
    amount           REAL    NOT NULL CHECK (amount > 0),
    category         TEXT    NOT NULL,
    description      TEXT,
    transaction_date TEXT    NOT NULL
);
"""

CREATE_APP_META_SQL = """
CREATE TABLE IF NOT EXISTS app_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

CREATE_DEVICES_SQL = """
CREATE TABLE IF NOT EXISTS devices (
    device_id        TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    platform         TEXT NOT NULL CHECK (platform IN ('windows', 'android')),
    token_hash       TEXT,
    cert_fingerprint TEXT,
    paired_at_ms     INTEGER,
    last_seen_ms     INTEGER,
    revoked_at_ms    INTEGER
);
"""

CREATE_SYNC_CHANGES_SQL = """
CREATE TABLE IF NOT EXISTS sync_changes (
    seq              INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type      TEXT NOT NULL,
    entity_uuid      TEXT NOT NULL,
    operation        TEXT NOT NULL CHECK (operation IN ('insert', 'update', 'delete')),
    base_revision    INTEGER,
    new_revision     INTEGER,
    payload          TEXT NOT NULL,
    origin_device_id TEXT NOT NULL,
    recorded_at_ms   INTEGER NOT NULL
);
"""

CREATE_SYNC_PEERS_SQL = """
CREATE TABLE IF NOT EXISTS sync_peers (
    peer_device_id   TEXT PRIMARY KEY,
    last_applied_seq INTEGER NOT NULL DEFAULT 0,
    last_sent_seq    INTEGER NOT NULL DEFAULT 0,
    last_sync_at_ms  INTEGER
);
"""

CREATE_SYNC_CONFLICTS_SQL = """
CREATE TABLE IF NOT EXISTS sync_conflicts (
    conflict_id    TEXT PRIMARY KEY,
    entity_uuid    TEXT NOT NULL,
    peer_device_id TEXT,
    local_payload  TEXT,
    remote_payload TEXT,
    resolution     TEXT NOT NULL,
    detected_at_ms INTEGER NOT NULL
);
"""

CREATE_IMPORT_BATCHES_SQL = """
CREATE TABLE IF NOT EXISTS import_batches (
    batch_id       TEXT PRIMARY KEY,
    source_file    TEXT,
    source_type    TEXT CHECK (source_type IN ('csv', 'pdf')),
    bank_format    TEXT,
    imported_at_ms INTEGER NOT NULL,
    imported_count INTEGER NOT NULL DEFAULT 0,
    skipped_count  INTEGER NOT NULL DEFAULT 0,
    device_id      TEXT
);
"""

CREATE_ACCOUNTS_SQL = """
CREATE TABLE IF NOT EXISTS accounts (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid               TEXT    NOT NULL UNIQUE,
    name               TEXT    NOT NULL,
    currency_code      TEXT    NOT NULL,
    currency_precision INTEGER NOT NULL
                       CHECK (currency_precision IN (0, 2, 3)),
    is_default         INTEGER NOT NULL DEFAULT 0
                       CHECK (is_default IN (0, 1)),
    created_at_ms      INTEGER NOT NULL,
    updated_at_ms      INTEGER NOT NULL,
    deleted_at_ms      INTEGER,
    revision           INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    origin_device_id   TEXT    NOT NULL,
    last_modified_by   TEXT    NOT NULL,
    sync_state         TEXT    NOT NULL DEFAULT 'pending'
                       CHECK (sync_state IN ('pending', 'synced', 'conflict'))
);
"""

# Version 4 replaces the REAL amount with integer minor units and links every
# transaction to an account. The original columns and sync metadata survive.
CREATE_TRANSACTIONS_V4_SQL = """
CREATE TABLE transactions_v4 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_type TEXT    NOT NULL CHECK (transaction_type IN ('income', 'expense')),
    amount_minor     INTEGER NOT NULL CHECK (amount_minor > 0),
    category         TEXT    NOT NULL,
    description      TEXT,
    transaction_date TEXT    NOT NULL,

    uuid              TEXT    NOT NULL UNIQUE,
    created_at_ms     INTEGER NOT NULL,
    updated_at_ms     INTEGER NOT NULL,
    deleted_at_ms     INTEGER,
    revision          INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    origin_device_id  TEXT    NOT NULL,
    last_modified_by  TEXT    NOT NULL,
    sync_state        TEXT    NOT NULL DEFAULT 'pending'
                      CHECK (sync_state IN ('pending', 'synced', 'conflict')),

    account_uuid      TEXT    NOT NULL REFERENCES accounts(uuid),
    import_hash       TEXT,
    external_ref      TEXT,
    import_batch_id   TEXT,
    account_label     TEXT
);
"""

# The version-2 table. The five original columns are unchanged; the rest are
# added for identity, conflict detection and synchronisation.
CREATE_TRANSACTIONS_V2_SQL = """
CREATE TABLE transactions_new (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_type TEXT    NOT NULL CHECK (transaction_type IN ('income', 'expense')),
    amount           REAL    NOT NULL CHECK (amount > 0),
    category         TEXT    NOT NULL,
    description      TEXT,
    transaction_date TEXT    NOT NULL,

    uuid              TEXT    NOT NULL UNIQUE,
    created_at_ms     INTEGER NOT NULL,
    updated_at_ms     INTEGER NOT NULL,
    deleted_at_ms     INTEGER,
    revision          INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    origin_device_id  TEXT    NOT NULL,
    last_modified_by  TEXT    NOT NULL,
    sync_state        TEXT    NOT NULL DEFAULT 'pending'
                      CHECK (sync_state IN ('pending', 'synced', 'conflict'))
);
"""

# Columns added in version 3. They are kept in one place so tests and the
# future importer can agree on the names.
IMPORT_COLUMNS = (
    ("import_hash", "TEXT"),
    ("external_ref", "TEXT"),
    ("import_batch_id", "TEXT"),
    ("account_label", "TEXT"),
)


# --------------------------------------------------------------------- helpers
def get_schema_version(connection):
    """Return the database's current ``user_version``."""
    return int(connection.execute("PRAGMA user_version").fetchone()[0])


def _table_exists(connection, table_name):
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_names(connection, table_name):
    return {
        row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")
    }


def _row_count(connection, table_name):
    return int(
        connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    )


def backup_database(connection, destination):
    """Copy the open database to ``destination`` using SQLite's backup API.

    The backup API is safer than copying the file with Explorer because it
    works while the database is open and includes any data still in the
    write-ahead log. The copy is checked before it is trusted.
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    target = sqlite3.connect(destination)
    try:
        connection.backup(target)
        result = target.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        target.close()

    if result != "ok":
        raise RuntimeError(f"Database backup failed its integrity check: {result}")
    return destination


def _backup_before_migration(connection, backup_dir, current_version):
    """Create a timestamped backup, but only when there is real data to protect."""
    if backup_dir is None:
        return None
    if not _table_exists(connection, "transactions"):
        return None
    if _row_count(connection, "transactions") == 0:
        return None

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    destination = (
        Path(backup_dir) / f"pocket_ledger_pre_v{current_version}_{stamp}.db"
    )
    return backup_database(connection, destination)


# ---------------------------------------------------------------- migrations
def _migrate_to_v1(connection):
    """Baseline: make sure the original transactions table exists."""
    connection.execute(CREATE_TRANSACTIONS_V1_SQL)


def _create_sync_tables(connection):
    """Create the tables that support identity, sync and conflicts."""
    for sql in (
        CREATE_APP_META_SQL,
        CREATE_DEVICES_SQL,
        CREATE_SYNC_CHANGES_SQL,
        CREATE_SYNC_PEERS_SQL,
        CREATE_SYNC_CONFLICTS_SQL,
    ):
        connection.execute(sql)


def _backfill_legacy_rows(connection, legacy_rows, device_id, timestamp_ms):
    """Copy old rows into the new table, keeping their integer ids.

    This function is separate so tests can deliberately break it and prove
    that the surrounding transaction rolls back cleanly.
    """
    for row in legacy_rows:
        connection.execute(
            """
            INSERT INTO transactions_new
                (id, transaction_type, amount, category, description,
                 transaction_date, uuid, created_at_ms, updated_at_ms,
                 deleted_at_ms, revision, origin_device_id, last_modified_by,
                 sync_state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 1, ?, ?, 'pending')
            """,
            (
                row["id"],
                row["transaction_type"],
                row["amount"],
                row["category"],
                row["description"],
                row["transaction_date"],
                str(uuid.uuid4()),
                timestamp_ms,
                timestamp_ms,
                device_id,
                device_id,
            ),
        )


def _migrate_to_v2(connection):
    """Add UUIDs, timestamps, soft deletes and the change log."""
    _create_sync_tables(connection)

    # Safety for a database that was upgraded by hand: never rebuild twice.
    if "uuid" in _column_names(connection, "transactions"):
        return

    device_id = get_or_create_device_id(connection)
    timestamp_ms = utc_now_ms()

    legacy_rows = connection.execute(
        """
        SELECT id, transaction_type, amount, category, description, transaction_date
        FROM transactions
        ORDER BY id
        """
    ).fetchall()

    connection.execute("DROP TABLE IF EXISTS transactions_new")
    connection.execute(CREATE_TRANSACTIONS_V2_SQL)
    _backfill_legacy_rows(connection, legacy_rows, device_id, timestamp_ms)

    if _row_count(connection, "transactions_new") != len(legacy_rows):
        raise RuntimeError("Migration copied the wrong number of transactions.")

    connection.execute("DROP TABLE transactions")
    connection.execute("ALTER TABLE transactions_new RENAME TO transactions")

    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_tx_date "
        "ON transactions(transaction_date DESC, id DESC)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_tx_updated ON transactions(updated_at_ms)"
    )

    # Seed the log with one "insert" per existing row. A phone that pairs
    # later can then pull the full history from change number 0.
    for row in connection.execute("SELECT * FROM transactions ORDER BY id"):
        append_change(
            connection,
            entity_uuid=row["uuid"],
            operation="insert",
            payload=transaction_payload_v1(row),
            origin_device_id=device_id,
            base_revision=None,
            new_revision=row["revision"],
            recorded_at_ms=timestamp_ms,
        )


def _migrate_to_v3(connection):
    """Add the metadata needed by future CSV/PDF statement imports."""
    existing = _column_names(connection, "transactions")
    for column, column_type in IMPORT_COLUMNS:
        if column not in existing:
            connection.execute(
                f"ALTER TABLE transactions ADD COLUMN {column} {column_type}"
            )

    connection.execute(CREATE_IMPORT_BATCHES_SQL)
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tx_import_hash
        ON transactions(import_hash)
        WHERE import_hash IS NOT NULL AND deleted_at_ms IS NULL
        """
    )


def _seed_default_account(connection, device_id, timestamp_ms):
    """Create the deterministic INR account once and return its row."""
    existing = connection.execute(
        "SELECT * FROM accounts WHERE uuid = ?",
        (DEFAULT_ACCOUNT_UUID,),
    ).fetchone()
    if existing is not None:
        return existing

    connection.execute(
        """
        INSERT INTO accounts
            (uuid, name, currency_code, currency_precision, is_default,
             created_at_ms, updated_at_ms, deleted_at_ms, revision,
             origin_device_id, last_modified_by, sync_state)
        VALUES (?, ?, ?, ?, 1, ?, ?, NULL, 1, ?, ?, 'pending')
        """,
        (
            DEFAULT_ACCOUNT_UUID,
            DEFAULT_ACCOUNT_NAME,
            DEFAULT_CURRENCY_CODE,
            DEFAULT_CURRENCY_PRECISION,
            timestamp_ms,
            timestamp_ms,
            device_id,
            device_id,
        ),
    )
    return connection.execute(
        "SELECT * FROM accounts WHERE uuid = ?",
        (DEFAULT_ACCOUNT_UUID,),
    ).fetchone()


def _build_v4_manifest(rows):
    """Convert every legacy amount to minor units, or report all bad ids.

    ``Decimal(str(amount))`` avoids making decisions from the binary float
    representation. ``ROUND_HALF_UP`` matches the importer's existing
    behaviour. A row is rejected when the value is non-positive, overflows a
    signed 64-bit integer, or does not round-trip exactly at two decimals.
    """
    manifest = []
    errors = []

    for row in rows:
        row_id = row["id"]
        row_uuid = row["uuid"]
        try:
            expected = to_decimal(row["amount"], 2, strict=False)
            if expected <= 0:
                raise MoneyError("amount is not positive")
            minor = parse_to_minor(row["amount"], 2, strict=False)
            if minor <= 0:
                raise MoneyError("amount is not positive after conversion")
            if minor_to_decimal(minor, 2) != expected:
                raise MoneyError(
                    f"round-trip mismatch: {expected} != "
                    f"{minor_to_decimal(minor, 2)}"
                )
        except (MoneyError, ArithmeticError, TypeError, ValueError) as error:
            errors.append((row_id, row_uuid, str(error)))
            continue

        manifest.append(
            {
                "id": int(row_id),
                "uuid": str(row_uuid),
                "amount_minor": int(minor),
            }
        )

    if errors:
        details = ", ".join(
            f"id={row_id} uuid={row_uuid} ({reason})"
            for row_id, row_uuid, reason in errors
        )
        raise RuntimeError(
            "Migration to schema 4 aborted; offending transaction ids: "
            + details
        )

    return manifest


def _verify_v4_rows(connection, table, original_rows, manifest, account_uuid):
    """Check count, sum, and the full per-row id/uuid/minor manifest."""
    rows = [
        dict(row)
        for row in connection.execute(
            f"SELECT * FROM {table} ORDER BY id"
        )
    ]
    if len(rows) != len(manifest):
        raise RuntimeError(
            f"Migration copied {len(rows)} rows, expected {len(manifest)}."
        )

    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise RuntimeError("Migration produced duplicate transaction ids.")

    expected_sum = sum(item["amount_minor"] for item in manifest)
    actual_sum = sum(int(row["amount_minor"]) for row in rows)
    if actual_sum != expected_sum:
        raise RuntimeError(
            f"Migration SUM(amount_minor) is {actual_sum}, expected {expected_sum}."
        )

    distinct_uuids = {row["uuid"] for row in rows}
    if len(distinct_uuids) != len(rows):
        raise RuntimeError("Migration produced duplicate transaction UUIDs.")

    unchanged = (
        "transaction_type",
        "category",
        "description",
        "transaction_date",
        "uuid",
        "created_at_ms",
        "updated_at_ms",
        "deleted_at_ms",
        "revision",
        "origin_device_id",
        "last_modified_by",
        "sync_state",
        "import_hash",
        "external_ref",
        "import_batch_id",
        "account_label",
    )

    for item in manifest:
        row = by_id.get(item["id"])
        if row is None:
            raise RuntimeError(
                f"Migration lost transaction id {item['id']}."
            )
        if row["uuid"] != item["uuid"]:
            raise RuntimeError(
                f"Migration changed UUID for id {item['id']}: "
                f"{item['uuid']} -> {row['uuid']}."
            )
        if int(row["amount_minor"]) != item["amount_minor"]:
            raise RuntimeError(
                f"Migration wrote the wrong minor amount for id {item['id']}."
            )
        if row["account_uuid"] != account_uuid:
            raise RuntimeError(
                f"Migration wrote the wrong account for id {item['id']}."
            )

    for original in original_rows:
        migrated = by_id.get(original["id"])
        if migrated is None:
            raise RuntimeError(
                f"Migration lost transaction id {original['id']}."
            )
        for column in unchanged:
            if migrated[column] != original[column]:
                raise RuntimeError(
                    f"Migration changed {column} for id {original['id']}."
                )


def _migrate_to_v4(connection):
    """Accounts plus integer minor units, rebuilt in one transaction.

    The caller's transaction wraps this whole function. Any exception rolls
    every DDL and data statement back, leaving the database at schema 3.
    """
    columns = _column_names(connection, "transactions")
    if (
        "amount" not in columns
        and "amount_minor" in columns
        and "account_uuid" in columns
    ):
        # A previous run already rebuilt the table but did not record the
        # version (for example a hand-edited database). Finish the additive
        # pieces idempotently instead of rebuilding twice.
        device_id = get_or_create_device_id(connection)
        timestamp_ms = utc_now_ms()
        connection.execute(CREATE_ACCOUNTS_SQL)
        _seed_default_account(connection, device_id, timestamp_ms)
        if "payload_version" not in _column_names(connection, "sync_changes"):
            connection.execute(
                "ALTER TABLE sync_changes "
                "ADD COLUMN payload_version INTEGER NOT NULL DEFAULT 1"
            )
        return

    device_id = get_or_create_device_id(connection)
    timestamp_ms = utc_now_ms()

    connection.execute(CREATE_ACCOUNTS_SQL)
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_one_default
        ON accounts(is_default)
        WHERE is_default = 1 AND deleted_at_ms IS NULL
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_accounts_live
        ON accounts(deleted_at_ms, name)
        """
    )
    account = _seed_default_account(connection, device_id, timestamp_ms)

    if "account_uuid" not in columns:
        connection.execute("ALTER TABLE transactions ADD COLUMN account_uuid TEXT")
    if "amount_minor" not in columns:
        connection.execute("ALTER TABLE transactions ADD COLUMN amount_minor INTEGER")

    original_rows = [
        dict(row)
        for row in connection.execute(
            "SELECT * FROM transactions ORDER BY id"
        )
    ]
    manifest = _build_v4_manifest(original_rows)

    for item in manifest:
        cursor = connection.execute(
            """
            UPDATE transactions
               SET account_uuid = ?, amount_minor = ?
             WHERE id = ?
            """,
            (DEFAULT_ACCOUNT_UUID, item["amount_minor"], item["id"]),
        )
        if cursor.rowcount != 1:
            raise RuntimeError(
                f"Backfill for transaction id {item['id']} touched "
                f"{cursor.rowcount} rows."
            )

    _verify_v4_rows(
        connection,
        "transactions",
        original_rows,
        manifest,
        DEFAULT_ACCOUNT_UUID,
    )

    connection.execute("DROP TABLE IF EXISTS transactions_v4")
    connection.execute(CREATE_TRANSACTIONS_V4_SQL)
    for original in original_rows:
        minor = next(
            item["amount_minor"] for item in manifest if item["id"] == original["id"]
        )
        connection.execute(
            """
            INSERT INTO transactions_v4
                (id, transaction_type, amount_minor, category, description,
                 transaction_date, uuid, created_at_ms, updated_at_ms,
                 deleted_at_ms, revision, origin_device_id, last_modified_by,
                 sync_state, account_uuid, import_hash, external_ref,
                 import_batch_id, account_label)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                original["id"],
                original["transaction_type"],
                minor,
                original["category"],
                original["description"],
                original["transaction_date"],
                original["uuid"],
                original["created_at_ms"],
                original["updated_at_ms"],
                original["deleted_at_ms"],
                original["revision"],
                original["origin_device_id"],
                original["last_modified_by"],
                original["sync_state"],
                DEFAULT_ACCOUNT_UUID,
                original["import_hash"],
                original["external_ref"],
                original["import_batch_id"],
                original["account_label"],
            ),
        )

    _verify_v4_rows(
        connection,
        "transactions_v4",
        original_rows,
        manifest,
        DEFAULT_ACCOUNT_UUID,
    )

    connection.execute("DROP TABLE transactions")
    connection.execute("ALTER TABLE transactions_v4 RENAME TO transactions")

    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_tx_date "
        "ON transactions(transaction_date DESC, id DESC)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_tx_updated ON transactions(updated_at_ms)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_tx_account_date "
        "ON transactions(account_uuid, transaction_date DESC, id DESC)"
    )
    connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tx_account_import_hash
        ON transactions(account_uuid, import_hash)
        WHERE import_hash IS NOT NULL AND deleted_at_ms IS NULL
        """
    )

    if "payload_version" not in _column_names(connection, "sync_changes"):
        connection.execute(
            "ALTER TABLE sync_changes "
            "ADD COLUMN payload_version INTEGER NOT NULL DEFAULT 1"
        )

    # append_change may have cached the old column set while seeding v2.
    try:
        del connection._pocket_ledger_sync_columns
    except AttributeError:
        pass

    existing_event = connection.execute(
        """
        SELECT 1 FROM sync_changes
        WHERE entity_type = 'account' AND entity_uuid = ?
          AND operation = 'insert'
        LIMIT 1
        """,
        (DEFAULT_ACCOUNT_UUID,),
    ).fetchone()
    if existing_event is None:
        append_change(
            connection,
            entity_uuid=DEFAULT_ACCOUNT_UUID,
            operation="insert",
            payload=account_payload(account),
            origin_device_id=device_id,
            base_revision=None,
            new_revision=1,
            entity_type="account",
            recorded_at_ms=timestamp_ms,
            payload_version=2,
        )


# version number -> function that performs that step
MIGRATIONS = (
    (1, _migrate_to_v1),
    (2, _migrate_to_v2),
    (3, _migrate_to_v3),
    (4, _migrate_to_v4),
)


def migrate(connection, backup_dir=None):
    """Bring ``connection`` up to :data:`SCHEMA_VERSION` and return the version.

    The caller owns the connection. Each migration step is committed on its
    own, so a failure in step 3 still leaves a valid step-2 database that can
    be retried after the bug is fixed.
    """
    current_version = get_schema_version(connection)

    if current_version > SCHEMA_VERSION:
        raise RuntimeError(
            "This database was created by a newer version of Pocket Ledger "
            f"(schema {current_version}, this app supports {SCHEMA_VERSION}). "
            "Please update the app instead of opening it with an older copy."
        )

    if current_version == SCHEMA_VERSION:
        return current_version

    _backup_before_migration(connection, backup_dir, current_version)

    previous_isolation = connection.isolation_level
    connection.isolation_level = None  # take full control of transactions

    try:
        for version, step in MIGRATIONS:
            if version <= current_version:
                continue

            connection.execute("BEGIN IMMEDIATE")
            try:
                step(connection)
                # PRAGMA values cannot use "?" placeholders, but the value is
                # a hard-coded integer from this file, never user input.
                connection.execute(f"PRAGMA user_version = {int(version)}")
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
    finally:
        connection.isolation_level = previous_isolation

    return get_schema_version(connection)
