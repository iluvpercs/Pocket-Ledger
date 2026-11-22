"""Database helpers for Pocket Ledger.

All the code that talks to SQLite lives in this file. Keeping it separate from
app.py means the interface code can focus on the screen, while this file
focuses on storing and reading data.
"""

import sqlite3
from datetime import date
from pathlib import Path

# The database file lives next to this file, inside the "data" folder.
# Path(__file__).parent is the folder that contains database.py.
DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "pocket_ledger.db"

# SQL used to create the table. "IF NOT EXISTS" makes this safe to run on
# every start: the table is only created the first time.
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_type TEXT    NOT NULL CHECK (transaction_type IN ('income', 'expense')),
    amount           REAL    NOT NULL CHECK (amount > 0),
    category         TEXT    NOT NULL,
    description      TEXT,
    transaction_date TEXT    NOT NULL
);
"""

# The only two transaction types this app accepts.
VALID_TYPES = ("income", "expense")


def get_connection():
    """Open a connection to the SQLite database.

    SQLite stores everything in one file, so "connecting" just opens that file
    (and creates it if it does not exist yet).
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)  # create data/ if it is missing
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row  # lets us read columns by name
    return connection


def initialize_database():
    """Create the data folder and the transactions table if they are missing."""
    connection = get_connection()
    try:
        connection.execute(CREATE_TABLE_SQL)
        connection.commit()
    finally:
        # Always close the connection, even if something went wrong.
        connection.close()


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


def add_transaction(transaction_type, amount, category, description, transaction_date):
    """Save one transaction and return the id of the new row."""
    amount = validate_transaction(transaction_type, amount, category, transaction_date)

    connection = get_connection()
    try:
        # The "?" placeholders are filled in by SQLite itself. This is called a
        # parameterized query and it protects the database from bad input.
        cursor = connection.execute(
            """
            INSERT INTO transactions
                (transaction_type, amount, category, description, transaction_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                transaction_type,
                amount,
                str(category).strip(),
                str(description or "").strip(),
                str(transaction_date),
            ),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def get_all_transactions():
    """Return every saved transaction, newest date first."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            SELECT id, transaction_type, amount, category, description, transaction_date
            FROM transactions
            ORDER BY transaction_date DESC, id DESC
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def delete_transaction(transaction_id):
    """Delete one transaction by id. Returns True if a row was removed."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            "DELETE FROM transactions WHERE id = ?",
            (int(transaction_id),),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()
