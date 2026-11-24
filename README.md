# Pocket Ledger

A small, private personal finance tracker built with Python, **PySide6 (Qt for
Python)** and SQLite. It runs entirely on your own computer — there are no
accounts, no bank connections and no data leaves your machine.

The original Streamlit web interface has been removed. There is now a single
native desktop application, `desktop_app.py`.

## Features

- Automatically creates a local SQLite database on first run.
- Multi-account support: create, rename, set default, and delete empty accounts.
- Per-account currency (ISO 4217 code + precision 0/2/3). Account currency is fixed after creation.
- Add income and expense transactions with account, amount, category, description and date.
- View transactions in a fast, sortable, filterable table with account/currency display.
- Edit or delete a transaction (delete asks for confirmation first).
- Dashboard shows per-account totals (income, expenses, balance) in each account's currency; no cross-currency aggregation.
- Import bank statements from CSV into a selected account, with reviewable preview, duplicate detection scoped to account, and currency-aware totals.
- Strict amount validation: amount must be greater than zero and respect the selected account's currency precision; amounts are stored as integer minor units (no floating-point financial math).
- Dark theme throughout. Private local data only.

## Database foundation

- Schema versioning with `PRAGMA user_version`, currently version **4**.
- Accounts table: UUID, name, ISO currency code, precision (0/2/3), default flag, timestamps, soft delete, revision/sync metadata.
- Transactions store `amount_minor` (INTEGER minor units) and `account_uuid`; legacy `amount` REAL is kept for compatibility where needed.
- Stable UUIDs on transactions/accounts while keeping local integer `id`.
- Created/updated timestamps, revision numbers, device ids and soft deletes.
- Append-only `sync_changes` log, ready for incremental sync later.
- `import_hash` duplicate detection scoped per account.
- WAL mode, a five-second busy timeout, and automatic pre-migration backups.
- Pytest suite uses temp DB isolation and live-DB fingerprint guards; tests must never write to `data\pocket_ledger.db`.

## Project structure

```
pocket-ledger/
├── desktop_app.py          # Application entry point (window + sidebar)
├── database.py             # Public data functions (all SQL lives here)
├── migrations.py           # Versioned, transactional schema upgrades
├── importers/              # CSV import logic (no GUI, standard library only)
│   ├── __init__.py
│   ├── csv_parser.py       # Encoding, mapping, dates and money parsing
│   ├── dedupe.py           # Import hashes and duplicate classification
│   ├── service.py          # Preview, edits and atomic commit
│   └── rules.json          # Editable keyword -> category rules
├── requirements.txt        # Python packages to install
├── README.md               # This file
├── .gitignore              # Files that should not be committed to Git
├── data/
│   ├── pocket_ledger.db    # Created automatically; your data lives here
│   └── backups/            # Automatic copies made before a migration
├── sync/                   # Local-first building blocks (no network yet)
│   ├── __init__.py
│   ├── identity.py         # This device's stable random id
│   └── store.py            # Append-only change log
├── tests/                  # Automated pytest suite
│   ├── conftest.py         # Temp DB fixtures + live DB protection + offscreen Qt
│   ├── helpers.py
│   ├── test_migrations.py
│   ├── test_database.py
│   ├── test_csv_parser.py
│   ├── test_import_service.py
│   ├── test_apps_smoke.py  # Offscreen Qt window/table/add/edit/delete tests
│   ├── test_models.py      # QAbstractTableModel and proxy tests
│   ├── test_formatting.py  # Helpers moved out of the old interfaces
│   └── test_workers.py     # Database work runs off the UI thread
├── ui/                     # PySide6 screens (thin; no SQL)
│   ├── __init__.py
│   ├── theme.py            # Dark palette, stylesheet and shared widgets
│   ├── models.py           # Table models for transactions and CSV preview
│   ├── workers.py          # QThread wrapper for database calls
│   ├── dashboard.py        # Welcome screen
│   ├── transactions.py     # Add, view, edit, filter, sort and delete
│   ├── import_csv.py       # CSV import dialog (calls importers/)
│   └── settings.py         # App information page
└── utils/
    ├── __init__.py
    ├── calculations.py     # legacy INR helper (deprecated for new UI paths)
    └── formatting.py       # Shared display helpers (no toolkit imports)
```

## Setup

Open PowerShell in the project folder:

```powershell
cd E:\projects\pocket-ledger
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If PowerShell blocks a command, use `.\.venv\Scripts\python.exe` directly or
allow scripts for this terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Run the desktop app

```powershell
.\.venv\Scripts\python.exe desktop_app.py
```

A native window opens with a sidebar: **Dashboard**, **Transactions**,
**Accounts**, **Import CSV** and **Settings**. Close the window (or press `Alt+F4`) to quit.

### Safe development databases

Tests and development runs should never use the real database. Set
`POCKET_LEDGER_DB` to a separate SQLite file before starting Python:

```powershell
$env:POCKET_LEDGER_DB = "$env:TEMP\pocket-ledger-dev.db"
.\.venv\Scripts\python.exe desktop_app.py
```

The desktop window shows a **DEV DB** badge whenever the active path is not the
production `data/pocket_ledger.db`. Settings always shows the active path.

`database.py` also refuses to open the live database when `POCKET_LEDGER_TEST_MODE`
is enabled. Pytest enables this automatically and points every test at a
temporary database before any initialization runs.

### Screens and workflows

- **Dashboard** — per-account cards showing income, expenses and balance in each account's currency. No cross-currency totals. First-run prompt when only the untouched default INR account exists with no transactions.
- **Transactions** — select account, add income/expenses with strict currency-precision validation, browse/sort/filter table, filter by account or all accounts, edit a selected row (or double-click it), and delete with confirmation.
- **Accounts** — create (name + searchable currency), rename, make default, delete. Currency is read-only after creation; deletion is blocked for accounts with live transactions or when it is the only remaining account.
- **Import CSV** — select destination account, review and import a bank statement; duplicate detection is scoped to the selected account. See below.
- **Settings** — app information, active database location and known limitations.

### How the desktop code is organised

- `desktop_app.py` builds the window and switches between cached pages in a
  `QStackedWidget`.
- `ui/theme.py` holds the dark palette and one shared stylesheet.
- `ui/models.py` defines a `QAbstractTableModel` for transactions, a
  `QSortFilterProxyModel` for sorting/filtering, and a model for the CSV
  preview. Qt paints only visible rows, so thousands of transactions stay
  smooth.
- `ui/workers.py` runs database calls in a `QThread`; the UI thread never waits
  on a long read or write.
- `ui/*.py` build widgets only. They call the public functions in `database.py`
  or `importers.service`; no SQL lives in the UI.
- Errors from SQLite are caught and shown inside the window instead of crashing
  the app.

The previous CustomTkinter interface built roughly 20 live widgets per row
(~100,000 widgets for 5,000 transactions) and rebuilt them on every tab switch.
Rendering that list took about 154 seconds and each tab switch about 64 seconds.
The Qt model/view design removes that cost entirely.

## Importing a CSV

The **Import CSV** entry in the sidebar handles statements you downloaded from
your bank — nothing is uploaded anywhere.

1. Choose the destination **account**. Amounts are interpreted using that account's currency and decimal precision, and duplicate detection is scoped to that account.
2. Choose the `.csv` file. The importer detects the encoding (UTF-8 or Windows-1252), the separator (comma, semicolon or tab), the real header row and the date format.
3. Check the column mapping. Date, description, amount (or separate debit/credit), balance and reference are pre-filled and can be changed.
4. Review the table. Rows can be included or excluded, and their date, description, category and amount can be edited inline. Duplicate rows are excluded by default; tick one to force-include it. Warning and error rows show a reason instead of crashing the import.
5. Click **Import**. All included rows are saved in one all-or-nothing database transaction: they get UUIDs, timestamps, change-log entries and account-scoped import hashes just like manually added transactions. A result summary is shown afterwards.

Supported value formats include `DD/MM/YYYY`, `DD-Mon-YYYY`, `YYYY-MM-DD`, Indian number grouping (`1,23,456.78`), currency symbols, `(123.45)` parentheses for negatives, and `Dr`/`Cr` suffixes. Amounts are parsed with `Decimal`; no extra third-party package is needed.

Duplicate detection uses a SHA-256 hash of the normalised date, signed amount in the account's minor units and description, plus an occurrence index so two genuinely identical same-day purchases are both kept. Re-importing the same file into the same account creates zero new transactions. A soft-deleted match is flagged as **WAS DELETED**.

Automatic categories come from the editable `importers/rules.json` file. Add keywords or change `default_category` there; no code change is needed.

## How it works

1. The app calls `initialize_database()` at startup.
2. `database.py` opens the file, then `migrations.py` reads
   `PRAGMA user_version`. If the file is old, it makes a timestamped backup and
   runs each pending step inside its own transaction. An up-to-date database
   only pays for one cheap version check.
3. The form collects a transaction. `add_transaction()` validates the values
   and inserts them using a parameterized query (`?` placeholders), which keeps
   the database safe from malformed input. The same transaction also gets a
   UUID, timestamps, revision 1 and an `insert` entry in the change log.
4. `get_all_transactions()` reads live rows (tombstones are hidden); the Qt
   model supplies display values to the table.
5. Deleting marks the row with `deleted_at_ms` instead of removing it, then
   appends a `delete` entry to the change log. That is what lets a future phone
   learn about the deletion.
6. `update_transaction()` edits only the fields you pass, increases the
   revision and appends an `update` entry.

## Database details

Current schema version is **4** (`PRAGMA user_version = 4`).

Key transaction fields:

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | Local primary key |
| `uuid` | TEXT | Stable global id |
| `transaction_type` | TEXT | `income` or `expense` |
| `amount_minor` | INTEGER | Signed magnitude stored as integer minor units; displayed per account currency |
| `amount` | REAL | Legacy compatibility field kept by migrations/data layer |
| `account_uuid` | TEXT | Owning account |
| `category` | TEXT | Required |
| `description` | TEXT | Optional |
| `transaction_date` | TEXT | `YYYY-MM-DD` |
| `created_at_ms` / `updated_at_ms` | INTEGER | UTC milliseconds |
| `deleted_at_ms` | INTEGER | `NULL` means live |
| `revision` | INTEGER | Incremented on edits |
| `import_hash` | TEXT | Duplicate marker, unique per live account+hash |

Accounts table stores name, currency code, precision, default flag, timestamps, soft delete and sync metadata.

Supporting tables: `app_meta`, `devices`, `sync_changes`, `sync_peers`, `sync_conflicts`, `import_batches`.

The database uses **WAL** mode and a five-second busy timeout. Automatic pre-migration backups are written before schema upgrades.

## Your data

- Everything is stored in `data/pocket_ledger.db`.
- Before a migration, an automatic copy is written to `data/backups/`.
- SQLite may create `pocket_ledger.db-wal` and `pocket_ledger.db-shm` while the
  app is running. These are normal WAL files; close the app before copying the
  database by hand.
- `.gitignore` excludes database files and backups, so personal data is never
  committed.
- To start over, stop the app, delete `data/pocket_ledger.db`, and restart.
  The empty database is recreated automatically.

## Run the tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The suite never writes to the live database. A central connection guard refuses
live connections in test mode, every test uses a temporary `POCKET_LEDGER_DB`,
and per-test plus session-level fingerprints cover the live file and its
WAL/SHM/journal sidecars. Migration tests copy the live file through SQLite's
read-only backup API. Qt tests run offscreen (`QT_QPA_PLATFORM=offscreen`).
Coverage includes:

- migrating a copy of the real database and preserving every row;
- UUIDs, timestamps, schema version, indexes and the change log;
- running migrations twice, and rolling back a deliberately broken step;
- add, view, update, soft delete and import-hash duplicates;
- CSV parsing, mapping overrides, bad rows, Dr/Cr and Indian number formats;
- same-day duplicates, re-imports, soft-deleted matches and force-including;
- all-or-nothing rollback, change-log entries and import metadata;
- offscreen Qt: main window, table load/sort/filter, add/edit/delete, import
  dialog, table models and background workers;
- formatting helpers moved out of the old Streamlit and Tk screens;
- database path isolation, fail-closed live connection checks, worker cleanup
  and live-database fingerprint coverage.

## Troubleshooting

- **Window does not open**: reinstall dependencies with
  `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and run
  `.\.venv\Scripts\python.exe desktop_app.py` from the project folder.
- **Qt platform error in a headless shell**: set
  `$env:QT_QPA_PLATFORM = "offscreen"` before running, or just run the tests,
  which set it automatically.
- **Table looks empty**: check that the app is running from this folder so it
  uses `data/pocket_ledger.db`, and clear the filter box.

## Known limitations / not included yet

- No PDF statement import (text/OCR), no bank connections, no cloud sync/UI sync, no mobile app.
- No monthly reports, budgets, charts, or backup/restore UI (data file is local and can be copied manually while app is closed).
- Account currency is immutable after creation by design; create a new account for a different currency.
- Amounts are integer minor units; supported currency precisions are 0/2/3 decimal places.
- The UI is dark-themed only; no theme switcher.
- Legacy `amount` REAL field remains for compatibility; UI and new logic use `amount_minor` + currency.
