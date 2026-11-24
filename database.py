"""Database helpers for Pocket Ledger.

All the code that talks to SQLite lives in this file (plus the schema
migrations in ``migrations.py``). Keeping it separate from the Qt screens means
the interface code can focus on the screen, while this file focuses on storing
and reading data.

Schema 4 stores money as integer minor units and links every transaction to an
account. The public transaction functions keep their old signatures: an
``add_transaction()`` call without an account uses the default INR account, and
rows returned by ``get_all_transactions()`` still contain an ``amount`` float
for the existing UI. New ``amount_minor``, account and currency fields are
also present.

Every transaction and account also has:

* a UUID (the same value on every device),
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

from migrations import CREATE_TRANSACTIONS_V1_SQL, migrate
from sync.identity import get_or_create_device_id
from sync.store import (
    account_payload,
    append_change,
    count_changes,
    get_changes_since,
    transaction_payload,
    upgrade_change,
    utc_now_ms,
)
from utils.currencies import (
    DEFAULT_CURRENCY_PRECISION,
    CurrencyError,
    get_precision,
)
from utils.money import MoneyError, minor_to_decimal, parse_to_minor

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
def _validated_category_date(category, transaction_date):
    if not str(category).strip():
        raise ValueError("Category cannot be empty.")

    try:
        date.fromisoformat(str(transaction_date))
    except (TypeError, ValueError):
        raise ValueError("Date must be a valid date (for example 2026-11-22).") from None


def _amount_to_minor(amount, precision=DEFAULT_CURRENCY_PRECISION, strict=True):
    """Validate a manual amount and return positive integer minor units."""
    try:
        minor = parse_to_minor(amount, precision=precision, strict=strict)
    except MoneyError as error:
        raise ValueError(str(error)) from None
    if minor <= 0:
        raise ValueError("Amount must be greater than zero.")
    return minor


def validate_transaction(
    transaction_type,
    amount,
    category,
    transaction_date,
    precision=DEFAULT_CURRENCY_PRECISION,
):
    """Check the inputs and return the cleaned amount as a float.

    Kept as a public helper for compatibility. New code stores the integer
    minor value returned by :func:`_amount_to_minor`.
    """
    if transaction_type not in VALID_TYPES:
        raise ValueError("Transaction type must be 'income' or 'expense'.")

    minor = _amount_to_minor(amount, precision=precision, strict=True)
    _validated_category_date(category, transaction_date)
    return float(minor_to_decimal(minor, precision))


# ------------------------------------------------------------------- helpers
def _clean_optional_text(value):
    """Turn None or blank text into None; trim everything else."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean_required_text(value, label):
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} cannot be empty.")
    return text


def _transaction_select_sql(where, order):
    return f"""
        SELECT t.*, a.name AS account_name, a.currency_code,
               a.currency_precision
        FROM transactions t
        LEFT JOIN accounts a ON a.uuid = t.account_uuid
        {where}
        {order}
    """


def _public_row(row):
    """Return a dict with the legacy float ``amount`` plus new fields."""
    if row is None:
        return None
    data = dict(row)
    minor = data.get("amount_minor")
    precision = int(data.get("currency_precision") or DEFAULT_CURRENCY_PRECISION)
    if minor is not None:
        data["amount"] = float(minor_to_decimal(int(minor), precision))
    return data


def _fetch_live_row(connection, transaction_id):
    """Return one non-deleted joined row, or None."""
    return connection.execute(
        _transaction_select_sql(
            "WHERE t.id = ? AND t.deleted_at_ms IS NULL", ""
        ),
        (int(transaction_id),),
    ).fetchone()


def _fetch_row(connection, transaction_id):
    """Return one joined row even if it has been soft-deleted."""
    return connection.execute(
        _transaction_select_sql("WHERE t.id = ?", ""),
        (int(transaction_id),),
    ).fetchone()


# ------------------------------------------------------------------ accounts
def _fetch_account_row(connection, account_uuid, include_deleted=False):
    sql = "SELECT * FROM accounts WHERE uuid = ?"
    if not include_deleted:
        sql += " AND deleted_at_ms IS NULL"
    return connection.execute(sql, (str(account_uuid),)).fetchone()


def _fetch_default_account_row(connection):
    return connection.execute(
        """
        SELECT * FROM accounts
        WHERE is_default = 1 AND deleted_at_ms IS NULL
        ORDER BY id
        LIMIT 1
        """
    ).fetchone()


def _require_live_account(connection, account_uuid=None):
    if account_uuid is None:
        row = _fetch_default_account_row(connection)
        if row is None:
            raise ValueError(
                "No default account exists. Create an account before adding "
                "transactions."
            )
        return row
    row = _fetch_account_row(connection, account_uuid)
    if row is None:
        raise ValueError(f"Account not found: {account_uuid}")
    return row


def _append_account_change(connection, account, operation, base_revision):
    device_id = get_or_create_device_id(connection)
    now = utc_now_ms()
    append_change(
        connection,
        entity_uuid=account["uuid"],
        operation=operation,
        payload=account_payload(account),
        origin_device_id=device_id,
        base_revision=base_revision,
        new_revision=int(account["revision"]),
        entity_type="account",
        recorded_at_ms=now,
        payload_version=2,
    )
    return now


def get_account(account_uuid):
    """Return one live account as a dict, or None."""
    connection = get_connection()
    try:
        row = _fetch_account_row(connection, account_uuid)
        return dict(row) if row is not None else None
    finally:
        connection.close()


def get_default_account():
    """Return the live default account as a dict, or None."""
    connection = get_connection()
    try:
        row = _fetch_default_account_row(connection)
        return dict(row) if row is not None else None
    finally:
        connection.close()


def list_accounts(include_deleted=False):
    """Return accounts ordered with the default first, then by name."""
    connection = get_connection()
    try:
        sql = "SELECT * FROM accounts"
        if not include_deleted:
            sql += " WHERE deleted_at_ms IS NULL"
        sql += " ORDER BY is_default DESC, name COLLATE NOCASE, id"
        return [dict(row) for row in connection.execute(sql)]
    finally:
        connection.close()


def create_account(name, currency_code, is_default=False):
    """Create an account and return its UUID.

    The first account on an empty database becomes the default. ``currency``
    must be a supported ISO 4217 code and its precision is stored with the
    account; the precision never changes afterwards.
    """
    account_name = _clean_required_text(name, "Account name")
    code = str(currency_code or "").strip().upper()
    try:
        precision = get_precision(code)
    except CurrencyError as error:
        raise ValueError(str(error)) from None

    connection = get_connection()
    try:
        device_id = get_or_create_device_id(connection)
        now = utc_now_ms()
        live_count = connection.execute(
            "SELECT COUNT(*) FROM accounts WHERE deleted_at_ms IS NULL"
        ).fetchone()[0]
        make_default = bool(is_default) or int(live_count) == 0

        if make_default:
            connection.execute(
                "UPDATE accounts SET is_default = 0 "
                "WHERE is_default = 1 AND deleted_at_ms IS NULL"
            )

        new_uuid = str(uuid.uuid4())
        cursor = connection.execute(
            """
            INSERT INTO accounts
                (uuid, name, currency_code, currency_precision, is_default,
                 created_at_ms, updated_at_ms, deleted_at_ms, revision,
                 origin_device_id, last_modified_by, sync_state)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 1, ?, ?, 'pending')
            """,
            (
                new_uuid,
                account_name,
                code,
                precision,
                1 if make_default else 0,
                now,
                now,
                device_id,
                device_id,
            ),
        )
        account = _fetch_account_row(connection, new_uuid)
        append_change(
            connection,
            entity_uuid=new_uuid,
            operation="insert",
            payload=account_payload(account),
            origin_device_id=device_id,
            base_revision=None,
            new_revision=1,
            entity_type="account",
            recorded_at_ms=now,
            payload_version=2,
        )
        _finish_write(connection)
        return new_uuid
    except Exception:
        _rollback_write(connection)
        raise
    finally:
        if not in_write_transaction():
            connection.close()


def update_account(
    account_uuid,
    name=None,
    currency_code=None,
    is_default=None,
):
    """Rename an account, change its default flag, or (only when empty) its currency.

    Currency is immutable once any transaction exists, including a soft-deleted
    one, because changing it would silently reinterpret every stored minor unit.
    """
    connection = get_connection()
    try:
        current = _fetch_account_row(connection, account_uuid)
        if current is None:
            return False

        new_name = current["name"] if name is None else _clean_required_text(name, "Account name")
        new_code = current["currency_code"]
        new_precision = int(current["currency_precision"])

        if currency_code is not None:
            code = str(currency_code or "").strip().upper()
            try:
                precision = get_precision(code)
            except CurrencyError as error:
                raise ValueError(str(error)) from None
            if code != current["currency_code"] or precision != int(current["currency_precision"]):
                used = connection.execute(
                    "SELECT COUNT(*) FROM transactions WHERE account_uuid = ?",
                    (str(account_uuid),),
                ).fetchone()[0]
                if int(used) > 0:
                    raise ValueError(
                        "An account's currency cannot be changed once it has "
                        "transactions. Create a new account instead."
                    )
                new_code = code
                new_precision = precision

        new_default = int(current["is_default"])
        if is_default is not None:
            if bool(is_default):
                connection.execute(
                    "UPDATE accounts SET is_default = 0 "
                    "WHERE is_default = 1 AND deleted_at_ms IS NULL"
                )
                new_default = 1
            elif int(current["is_default"]):
                raise ValueError(
                    "Choose another default account instead of unsetting this one."
                )
            else:
                new_default = 0

        now = utc_now_ms()
        new_revision = int(current["revision"]) + 1
        connection.execute(
            """
            UPDATE accounts
               SET name = ?,
                   currency_code = ?,
                   currency_precision = ?,
                   is_default = ?,
                   updated_at_ms = ?,
                   revision = ?,
                   last_modified_by = ?,
                   sync_state = 'pending'
             WHERE uuid = ? AND deleted_at_ms IS NULL
            """,
            (
                new_name,
                new_code,
                new_precision,
                new_default,
                now,
                new_revision,
                get_or_create_device_id(connection),
                str(account_uuid),
            ),
        )
        updated = _fetch_account_row(connection, account_uuid)
        _append_account_change(
            connection, updated, "update", base_revision=int(current["revision"])
        )
        _finish_write(connection)
        return True
    except Exception:
        _rollback_write(connection)
        raise
    finally:
        if not in_write_transaction():
            connection.close()


def rename_account(account_uuid, name):
    """Rename one live account."""
    return update_account(account_uuid, name=name)


def delete_account(account_uuid):
    """Soft-delete an empty account.

    Deletion is refused while live transactions still reference the account.
    Deleted transaction tombstones do not block deletion, but their currency is
    preserved in the account row (which remains in the database).
    """
    connection = get_connection()
    try:
        current = _fetch_account_row(connection, account_uuid)
        if current is None:
            return False

        live_count = connection.execute(
            """
            SELECT COUNT(*) FROM transactions
            WHERE account_uuid = ? AND deleted_at_ms IS NULL
            """,
            (str(account_uuid),),
        ).fetchone()[0]
        if int(live_count) > 0:
            raise ValueError(
                "Cannot delete an account that still has transactions. "
                "Delete or move those transactions first."
            )

        live_accounts = connection.execute(
            "SELECT COUNT(*) FROM accounts WHERE deleted_at_ms IS NULL"
        ).fetchone()[0]
        if int(live_accounts) <= 1:
            raise ValueError(
                "Cannot delete the only account. Create another account first."
            )

        device_id = get_or_create_device_id(connection)
        now = utc_now_ms()
        new_revision = int(current["revision"]) + 1
        connection.execute(
            """
            UPDATE accounts
               SET deleted_at_ms = ?,
                   updated_at_ms = ?,
                   revision = ?,
                   last_modified_by = ?,
                   sync_state = 'pending',
                   is_default = 0
             WHERE uuid = ? AND deleted_at_ms IS NULL
            """,
            (now, now, new_revision, device_id, str(account_uuid)),
        )

        if int(current["is_default"]):
            promoted = connection.execute(
                """
                SELECT * FROM accounts
                WHERE deleted_at_ms IS NULL AND is_default = 0
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()
            if promoted is not None:
                promoted_revision = int(promoted["revision"]) + 1
                connection.execute(
                    """
                    UPDATE accounts
                       SET is_default = 1,
                           updated_at_ms = ?,
                           revision = ?,
                           last_modified_by = ?,
                           sync_state = 'pending'
                     WHERE uuid = ? AND deleted_at_ms IS NULL
                    """,
                    (now, promoted_revision, device_id, promoted["uuid"]),
                )
                promoted_after = _fetch_account_row(connection, promoted["uuid"])
                _append_account_change(
                    connection,
                    promoted_after,
                    "update",
                    base_revision=int(promoted["revision"]),
                )

        deleted = _fetch_account_row(connection, account_uuid, include_deleted=True)
        _append_account_change(
            connection, deleted, "delete", base_revision=int(current["revision"])
        )
        _finish_write(connection)
        return True
    except Exception:
        _rollback_write(connection)
        raise
    finally:
        if not in_write_transaction():
            connection.close()


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
    account_uuid=None,
):
    """Save one transaction and return the id of the new row.

    ``amount`` is a major-unit value (for example ``125.50``) in the account's
    currency. Without ``account_uuid`` the default account is used. Manual
    entry is strict: more decimal places than the currency allows is an error.
    """
    connection = get_connection()
    try:
        account = _require_live_account(connection, account_uuid)
        precision = int(account["currency_precision"])
        if transaction_type not in VALID_TYPES:
            raise ValueError("Transaction type must be 'income' or 'expense'.")
        minor = _amount_to_minor(amount, precision=precision, strict=True)
        _validated_category_date(category, transaction_date)

        device_id = get_or_create_device_id(connection)
        now = utc_now_ms()
        new_uuid = str(uuid.uuid4())

        cursor = connection.execute(
            """
            INSERT INTO transactions
                (transaction_type, amount_minor, category, description,
                 transaction_date, uuid, created_at_ms, updated_at_ms,
                 deleted_at_ms, revision, origin_device_id, last_modified_by,
                 sync_state, account_uuid, import_hash, external_ref,
                 import_batch_id, account_label)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 1, ?, ?, 'pending',
                    ?, ?, ?, ?, ?)
            """,
            (
                transaction_type,
                minor,
                str(category).strip(),
                str(description or "").strip(),
                str(transaction_date),
                new_uuid,
                now,
                now,
                device_id,
                device_id,
                str(account["uuid"]),
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
            payload_version=2,
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
    except Exception:
        _rollback_write(connection)
        raise
    finally:
        if not in_write_transaction():
            connection.close()


# ---------------------------------------------------------------------- read
def get_all_transactions(account_uuid=None):
    """Return every live transaction, newest date first.

    The original six columns are present, plus ``amount_minor``,
    ``account_uuid``, ``account_name``, ``currency_code`` and
    ``currency_precision``. ``amount`` is a float in major units so the current
    Qt screens keep working without changes.
    """
    connection = get_connection()
    try:
        sql = """
            SELECT t.id, t.transaction_type, t.amount_minor, t.category,
                   t.description, t.transaction_date, t.account_uuid,
                   a.name AS account_name, a.currency_code,
                   a.currency_precision
            FROM transactions t
            LEFT JOIN accounts a ON a.uuid = t.account_uuid
            WHERE t.deleted_at_ms IS NULL
        """
        parameters = []
        if account_uuid is not None:
            sql += " AND t.account_uuid = ?"
            parameters.append(str(account_uuid))
        sql += " ORDER BY t.transaction_date DESC, t.id DESC"
        return [
            _public_row(row) for row in connection.execute(sql, parameters)
        ]
    finally:
        connection.close()


def get_transaction(transaction_id):
    """Return one live transaction with all sync fields, or None."""
    connection = get_connection()
    try:
        return _public_row(_fetch_live_row(connection, transaction_id))
    finally:
        connection.close()


def get_account_totals():
    """Return per-account income, expense, balance and transaction count.

    All totals are integer minor units aggregated in SQL. Accounts with no live
    transactions are included with zero totals. Callers must display each row in
    its own currency and must not sum rows across currencies.
    """
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT
                a.uuid AS account_uuid,
                a.name AS account_name,
                a.currency_code,
                a.currency_precision,
                a.is_default,
                COALESCE(SUM(
                    CASE WHEN t.transaction_type = 'income'
                         THEN t.amount_minor ELSE 0 END
                ), 0) AS income_minor,
                COALESCE(SUM(
                    CASE WHEN t.transaction_type = 'expense'
                         THEN t.amount_minor ELSE 0 END
                ), 0) AS expense_minor,
                COALESCE(SUM(
                    CASE WHEN t.transaction_type = 'income' THEN t.amount_minor
                         WHEN t.transaction_type = 'expense' THEN -t.amount_minor
                         ELSE 0 END
                ), 0) AS balance_minor,
                COUNT(t.id) AS transaction_count
            FROM accounts a
            LEFT JOIN transactions t
                ON t.account_uuid = a.uuid
               AND t.deleted_at_ms IS NULL
            WHERE a.deleted_at_ms IS NULL
            GROUP BY a.id, a.uuid, a.name, a.currency_code, a.currency_precision, a.is_default
            ORDER BY a.is_default DESC, a.id ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
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
    to the change log.
    """
    connection = get_connection()
    try:
        current = _fetch_live_row(connection, transaction_id)
        if current is None:
            return False

        new_type = (
            current["transaction_type"] if transaction_type is None else transaction_type
        )
        new_category = current["category"] if category is None else category
        new_description = (
            current["description"] if description is None else description
        )
        new_date = (
            current["transaction_date"]
            if transaction_date is None
            else transaction_date
        )

        if new_type not in VALID_TYPES:
            raise ValueError("Transaction type must be 'income' or 'expense'.")
        _validated_category_date(new_category, new_date)

        precision = int(current["currency_precision"])
        new_minor = (
            int(current["amount_minor"])
            if amount is None
            else _amount_to_minor(amount, precision=precision, strict=True)
        )

        device_id = get_or_create_device_id(connection)
        now = utc_now_ms()
        new_revision = int(current["revision"]) + 1

        connection.execute(
            """
            UPDATE transactions
            SET transaction_type = ?,
                amount_minor = ?,
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
                new_minor,
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
            payload_version=2,
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
    written to the change log.
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
            payload_version=2,
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
def get_sync_changes(
    since_seq=0,
    limit=500,
    exclude_device_id=None,
    upgrade=True,
):
    """Return change-log rows after ``since_seq``.

    By default each row is a dict with a parsed payload and v1 snapshots
    upgraded to the canonical v2 shape. Pass ``upgrade=False`` for raw rows.
    """
    connection = get_connection()
    try:
        rows = get_changes_since(
            connection,
            since_seq=since_seq,
            limit=limit,
            exclude_device_id=exclude_device_id,
        )
        if not upgrade:
            return rows
        return [upgrade_change(row) for row in rows]
    finally:
        connection.close()


def get_change_count():
    """Return how many entries the change log contains."""
    connection = get_connection()
    try:
        return count_changes(connection)
    finally:
        connection.close()
