"""Schema versions and safe database migrations.

SQLite stores a small number in every database file called ``user_version``.
Pocket Ledger uses it like a page number in a book:

* version 0 - the original table created by the first Streamlit release
* version 1 - "this is a Pocket Ledger database" (baseline marker)
* version 2 - UUIDs, timestamps, soft deletes and the sync change log
* version 3 - import metadata for future bank-statement importing

``initialize_database()`` calls :func:`migrate` on every start. If the database
is already current, the only work is one cheap ``PRAGMA`` read.

Each step runs inside its own transaction. If a step fails, SQLite rolls it
back completely, so a half-upgraded table is never left behind.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from sync.identity import get_or_create_device_id
from sync.store import append_change, transaction_payload, utc_now_ms

# Increase this number when a new migration step is added.
SCHEMA_VERSION = 3

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
            payload=transaction_payload(row),
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


# version number -> function that performs that step
MIGRATIONS = (
    (1, _migrate_to_v1),
    (2, _migrate_to_v2),
    (3, _migrate_to_v3),
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
