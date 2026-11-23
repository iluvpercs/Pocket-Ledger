"""Database helpers for Pocket Ledger.

All the code that talks to SQLite lives in this file (plus the schema
migrations in ``migrations.py``). Keeping it separate from the Qt screens means
the interface code can focus on the screen, while this file focuses on storing
and reading data.

The public functions are used by the desktop app and the importer service.
Their names and arguments are unchanged from earlier milestones, so existing
callers keep working.

Behind the scenes, every transaction now also has:

* a UUID (a long random id that will be the same on every device),
* created / updated timestamps,
* a revision number,
* a soft-delete marker (``deleted_at_ms``),
* a row in the ``sync_changes`` log.
"""

import contextvars
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from migrations import CREATE_TRANSACTIONS_V1_SQL, SCHEMA_VERSION, migrate
from sync.identity import get_or_create_device_id
from sync.store import (
    append_change,
    count_changes,
    get_changes_since,
    transaction_payload,
    utc_now_ms,
)

DB_PATH_ENV_VAR = "POCKET_LEDGER_DB"
TEST_MODE_ENV_VAR = "POCKET_LEDGER_TEST_MODE"

PROJECT_ROOT = Path(__file__).resolve().parent
LIVE_DATA_DIR = PROJECT_ROOT / "data"
LIVE_DB_PATH = LIVE_DATA_DIR / "pocket_ledger.db"


class DatabaseSafetyError(RuntimeError):
    """Raised when code tries to use the live database in a protected context."""


class DatabaseConfigurationError(DatabaseSafetyError):
    """Raised when ``POCKET_LEDGER_DB`` is set to an unusable value."""


def _canonical_path(path):
    """Return a canonical absolute path for reliable live-path comparison."""
    return Path(os.path.normcase(str(Path(path).expanduser().resolve())))


def _read_environment_db_path():
    """Read and validate the optional database override."""
    raw = os.environ.get(DB_PATH_ENV_VAR)
    if raw is None:
        return None

    text = raw.strip()
    if not text:
        raise DatabaseConfigurationError(
            f"{DB_PATH_ENV_VAR} is set but empty. Set it to a SQLite file path "
            "or remove the variable to use the production database."
        )

    path = _canonical_path(text)
    if path.exists() and path.is_dir():
        raise DatabaseConfigurationError(
            f"{DB_PATH_ENV_VAR} points to a directory, not a database file: {path}"
        )
    if path.name in ("", ".", ".."):
        raise DatabaseConfigurationError(
            f"{DB_PATH_ENV_VAR} must name a database file: {text}"
        )
    return path


def resolve_db_path():
    """Resolve the active database path from the environment or live default."""
    configured = _read_environment_db_path()
    if configured is not None:
        return configured
    return _canonical_path(LIVE_DB_PATH)


def refresh_database_path():
    """Re-read the environment and update the active path globals."""
    global DB_PATH, DATA_DIR
    DB_PATH = resolve_db_path()
    DATA_DIR = DB_PATH.parent
    return DB_PATH


# The production database lives in ``data/`` next to this file. Tests and
# development runs set POCKET_LEDGER_DB to a separate temporary file.
DB_PATH = resolve_db_path()
DATA_DIR = DB_PATH.parent


def in_test_mode():
    """True under pytest or when test mode is explicitly requested."""
    explicit = os.environ.get(TEST_MODE_ENV_VAR, "").strip().lower()
    if explicit in {"1", "true", "yes", "on"}:
        return True
    return "PYTEST_CURRENT_TEST" in os.environ


def is_development_database():
    """True when the active path is not the canonical production database."""
    return str(_canonical_path(DB_PATH)) != str(_canonical_path(LIVE_DB_PATH))

# Kept for backwards compatibility: older code imported this constant.
CREATE_TABLE_SQL = CREATE_TRANSACTIONS_V1_SQL

# The only two transaction types this app accepts.
VALID_TYPES = ("income", "expense")


# ----------------------------------------------------------------- connection
# A context-local connection lets several public write calls share one SQLite
# transaction. It is set by atomic_write() below and is otherwise empty, so
# ordinary app code keeps getting a fresh connection from get_connection().
_write_context = contextvars.ContextVar("pocket_ledger_write_connection", default=None)


def _open_connection():
    """Open a brand-new connection with the settings the app relies on."""
    path = _canonical_path(DB_PATH)

    if in_test_mode() and str(path) == str(_canonical_path(LIVE_DB_PATH)):
        raise DatabaseSafetyError(
            "Refusing to open the live database while test mode is active.\n"
            f"Set {DB_PATH_ENV_VAR} to a temporary SQLite file before any "
            f"database connection is created. Remove {TEST_MODE_ENV_VAR} only "
            "for normal production use."
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)  # create data/ if it is missing
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row  # lets us read columns by name
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_connection():
    """Return a connection to the SQLite database.

    SQLite stores everything in one file, so "connecting" just opens that file.
    Inside :func:`atomic_write` the already-open connection is returned instead,
    which is how a whole CSV import can be one all-or-nothing transaction.
    """
    shared = _write_context.get()
    return shared if shared is not None else _open_connection()


def in_write_transaction():
    """True while the caller is inside :func:`atomic_write`."""
    return _write_context.get() is not None


@contextmanager
def atomic_write():
    """Group several public write calls into one committed transaction.

    Importers call add_transaction() once per row. Normally each call commits
    on its own; here they all share one connection, and the commit (or a full
    rollback on any failure) happens at the end. The public function signatures
    do not change.
    """
    existing = _write_context.get()
    if existing is not None:  # already inside a transaction: just reuse it
        yield existing
        return

    connection = _open_connection()
    token = _write_context.set(connection)
    started = False
    try:
        connection.execute("BEGIN IMMEDIATE")
        started = True
        yield connection
        connection.commit()
    except Exception:
        if started:
            connection.rollback()
        raise
    finally:
        _write_context.reset(token)
        connection.close()


def _finish_write(connection):
    """Commit, unless :func:`atomic_write` owns the commit."""
    if _write_context.get() is not connection:
        connection.commit()


def _rollback_write(connection):
    """Roll back, unless :func:`atomic_write` owns the rollback."""
    if _write_context.get() is not connection:
        connection.rollback()


def initialize_database():
    """Create or upgrade the database, then return its schema version.

    Both apps call this at startup. On an old database this is the moment the
    migration runs; on an up-to-date database it is a single cheap check.
    A backup of existing data is made automatically before any migration.
    """
    connection = get_connection()
    try:
        version = migrate(connection, backup_dir=DATA_DIR / "backups")

        # WAL lets one reader and one writer work at the same time. It is a
        # property of the database file, so setting it once is enough.
        connection.execute("PRAGMA journal_mode = WAL")
        return version
    finally:
        # Always close the connection, even if something went wrong.
        connection.close()


# ---------------------------------------------------------------- validation
def validate_transaction(transaction_type, amount, category, transaction_date):
    """Check the inputs and return the cleaned amount.

    Raises ValueError with a friendly message when something is wrong, so the
    interface can show that message to the user.
    """
    if transaction_type not in VALID_TYPES:
        raise ValueError("Transaction type must be 'income' or 'expense'.")

    try:
        amount_value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number.") from None

    if amount_value <= 0:
        raise ValueError("Amount must be greater than zero.")

    if not str(category).strip():
        raise ValueError("Category cannot be empty.")

    try:
        date.fromisoformat(str(transaction_date))
    except (TypeError, ValueError):
        raise ValueError("Date must be a valid date (for example 2026-11-22).") from None

    # Money is stored with two decimal places.
    return round(amount_value, 2)


# ------------------------------------------------------------------- helpers
def _clean_optional_text(value):
    """Turn None or blank text into None; trim everything else."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _fetch_live_row(connection, transaction_id):
    """Return one non-deleted row, or None."""
    return connection.execute(
        """
        SELECT * FROM transactions
        WHERE id = ? AND deleted_at_ms IS NULL
        """,
        (int(transaction_id),),
    ).fetchone()


def _fetch_row(connection, transaction_id):
    """Return one row even if it has been soft-deleted."""
    return connection.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (int(transaction_id),),
    ).fetchone()


# -------------------------------------------------------------------- create
def add_transaction(
    transaction_type,
    amount,
    category,
    description,
    transaction_date,
    import_hash=None,
    external_ref=None,
    import_batch_id=None,
    account_label=None,
):
    """Save one transaction and return the id of the new row.

    The extra keyword arguments are optional and unused by the current
    interfaces. They are ready for the statement importer: ``import_hash``
    lets Pocket Ledger recognise a row that was already imported.
    """
    amount = validate_transaction(transaction_type, amount, category, transaction_date)

    connection = get_connection()
    try:
        device_id = get_or_create_device_id(connection)
        now = utc_now_ms()
        new_uuid = str(uuid.uuid4())

        # The "?" placeholders are filled in by SQLite itself. This is called a
        # parameterized query and it protects the database from bad input.
        cursor = connection.execute(
            """
            INSERT INTO transactions
                (transaction_type, amount, category, description,
                 transaction_date, uuid, created_at_ms, updated_at_ms,
                 deleted_at_ms, revision, origin_device_id, last_modified_by,
                 sync_state, import_hash, external_ref, import_batch_id,
                 account_label)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 1, ?, ?, 'pending', ?, ?, ?, ?)
            """,
            (
                transaction_type,
                amount,
                str(category).strip(),
                str(description or "").strip(),
                str(transaction_date),
                new_uuid,
                now,
                now,
                device_id,
                device_id,
                _clean_optional_text(import_hash),
                _clean_optional_text(external_ref),
                _clean_optional_text(import_batch_id),
                _clean_optional_text(account_label),
            ),
        )

        row = _fetch_row(connection, cursor.lastrowid)
        append_change(
            connection,
            entity_uuid=new_uuid,
            operation="insert",
            payload=transaction_payload(row),
            origin_device_id=device_id,
            base_revision=None,
            new_revision=1,
            recorded_at_ms=now,
        )

        _finish_write(connection)
        return cursor.lastrowid
    except sqlite3.IntegrityError as error:
        _rollback_write(connection)
        if "import_hash" in str(error):
            raise ValueError(
                "This transaction looks like a duplicate of one already imported."
            ) from None
        raise
    finally:
        if not in_write_transaction():
            connection.close()


# ---------------------------------------------------------------------- read
def get_all_transactions():
    """Return every live transaction, newest date first.

    Deleted rows are hidden here, so the desktop screens behave exactly as
    before. The row still exists in the table as a
    "tombstone" so the deletion can be synchronised later.
    """
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            SELECT id, transaction_type, amount, category, description, transaction_date
            FROM transactions
            WHERE deleted_at_ms IS NULL
            ORDER BY transaction_date DESC, id DESC
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_transaction(transaction_id):
    """Return one live transaction with all sync fields, or None."""
    connection = get_connection()
    try:
        return _fetch_live_row(connection, transaction_id)
    finally:
        connection.close()


# -------------------------------------------------------------------- update
def update_transaction(
    transaction_id,
    transaction_type=None,
    amount=None,
    category=None,
    description=None,
    transaction_date=None,
):
    """Edit a transaction. Returns True when a live row was updated.

    Only the arguments you pass are changed; the rest keep their current
    values. The revision number goes up by one and an "update" entry is added
    to the change log, which is what a future sync will send to another
    device.
    """
    connection = get_connection()
    try:
        current = _fetch_live_row(connection, transaction_id)
        if current is None:
            return False

        new_type = (
            current["transaction_type"] if transaction_type is None else transaction_type
        )
        new_amount = current["amount"] if amount is None else amount
        new_category = current["category"] if category is None else category
        new_description = (
            current["description"] if description is None else description
        )
        new_date = (
            current["transaction_date"]
            if transaction_date is None
            else transaction_date
        )

        cleaned_amount = validate_transaction(
            new_type, new_amount, new_category, new_date
        )

        device_id = get_or_create_device_id(connection)
        now = utc_now_ms()
        new_revision = int(current["revision"]) + 1

        connection.execute(
            """
            UPDATE transactions
            SET transaction_type = ?,
                amount = ?,
                category = ?,
                description = ?,
                transaction_date = ?,
                updated_at_ms = ?,
                revision = ?,
                last_modified_by = ?,
                sync_state = 'pending'
            WHERE id = ? AND deleted_at_ms IS NULL
            """,
            (
                new_type,
                cleaned_amount,
                str(new_category).strip(),
                str(new_description or "").strip(),
                str(new_date),
                now,
                new_revision,
                device_id,
                int(transaction_id),
            ),
        )

        updated = _fetch_row(connection, transaction_id)
        append_change(
            connection,
            entity_uuid=current["uuid"],
            operation="update",
            payload=transaction_payload(updated),
            origin_device_id=device_id,
            base_revision=int(current["revision"]),
            new_revision=new_revision,
            recorded_at_ms=now,
        )

        _finish_write(connection)
        return True
    except Exception:
        _rollback_write(connection)
        raise
    finally:
        if not in_write_transaction():
            connection.close()


# -------------------------------------------------------------------- delete
def delete_transaction(transaction_id):
    """Soft-delete one transaction by id.

    Returns True if a live row was removed. The row stays in the table with a
    ``deleted_at_ms`` timestamp (a "tombstone"), and a "delete" entry is
    written to the change log. That is how a future phone will learn that the
    transaction disappeared instead of quietly keeping its own copy.
    """
    connection = get_connection()
    try:
        current = _fetch_live_row(connection, transaction_id)
        if current is None:
            return False

        device_id = get_or_create_device_id(connection)
        now = utc_now_ms()
        new_revision = int(current["revision"]) + 1

        connection.execute(
            """
            UPDATE transactions
            SET deleted_at_ms = ?,
                updated_at_ms = ?,
                revision = ?,
                last_modified_by = ?,
                sync_state = 'pending'
            WHERE id = ? AND deleted_at_ms IS NULL
            """,
            (now, now, new_revision, device_id, int(transaction_id)),
        )

        deleted = _fetch_row(connection, transaction_id)
        append_change(
            connection,
            entity_uuid=current["uuid"],
            operation="delete",
            payload=transaction_payload(deleted),
            origin_device_id=device_id,
            base_revision=int(current["revision"]),
            new_revision=new_revision,
            recorded_at_ms=now,
        )

        _finish_write(connection)
        return True
    except Exception:
        _rollback_write(connection)
        raise
    finally:
        if not in_write_transaction():
            connection.close()


# ------------------------------------------------------------------- sync log
def get_sync_changes(since_seq=0, limit=500, exclude_device_id=None):
    """Return change-log rows after ``since_seq`` (for future sync clients)."""
    connection = get_connection()
    try:
        return get_changes_since(
            connection,
            since_seq=since_seq,
            limit=limit,
            exclude_device_id=exclude_device_id,
        )
    finally:
        connection.close()


def get_change_count():
    """Return how many entries the change log contains."""
    connection = get_connection()
    try:
        return count_changes(connection)
    finally:
        connection.close()
