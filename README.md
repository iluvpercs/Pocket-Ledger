# Pocket Ledger

A small, private personal finance tracker built with Python, Streamlit and
SQLite. It runs entirely on your own computer — there are no accounts, no bank
connections and no data leaves your machine.

The project now has two interfaces that share the same local database:

- `app.py` — the original Streamlit web app.
- `desktop_app.py` — a native Windows window built with CustomTkinter.

## Features

- Automatically creates a local SQLite database on first run.
- Add income and expense transactions with amount, category, description and date.
- View all saved transactions, newest first.
- Delete a transaction (with a confirmation step).
- Input validation: amount must be greater than zero, type must be income or
  expense, and the date must be valid.
- Amounts are shown in Indian Rupees (₹).

## Database foundation (Milestone 1)

- Schema versioning with `PRAGMA user_version`, currently version **3**.
- Stable UUIDs on every transaction while keeping the original integer `id`.
- Created/updated timestamps, revision numbers, device ids and soft deletes.
- Append-only `sync_changes` log, ready for incremental sync later.
- `update_transaction()` for future editing (the screens still show add,
  list and delete only).
- `import_hash` and supporting tables for future statement importing.
- WAL mode, a five-second busy timeout, and automatic pre-migration backups.
- A pytest suite that never writes to the live database.

## Project structure

```
pocket-ledger/
├── app.py                  # Streamlit interface (form, table, delete)
├── desktop_app.py          # Desktop entry point (window + sidebar)
├── database.py             # Public data functions (shared by both apps)
├── migrations.py           # Versioned, transactional schema upgrades
├── importers/              # CSV import logic (no GUI)
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
├── pages/                  # Empty for now; Streamlit Milestone 2 pages
├── sync/                   # Local-first building blocks (no network yet)
│   ├── __init__.py
│   ├── identity.py         # This device's stable random id
│   └── store.py            # Append-only change log
├── tests/                  # Automated pytest suite
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_migrations.py
│   ├── test_database.py
│   ├── test_csv_parser.py
│   ├── test_import_service.py
│   └── test_apps_smoke.py
├── ui/                     # Desktop screens
│   ├── __init__.py
│   ├── theme.py            # Colours, fonts and shared widgets
│   ├── dashboard.py        # Welcome screen
│   ├── transactions.py     # Add, list and delete transactions
│   ├── import_csv.py       # CSV import dialog (calls importers/)
│   └── settings.py         # Placeholder settings page
└── utils/
    ├── __init__.py
    └── calculations.py     # Small helpers such as ₹ formatting
```

## Setup

Open PowerShell in the project folder:

```powershell
cd E:\projects\pocket-ledger
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the app

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit prints a local address (usually <http://localhost:8501>) and opens it
in your browser. Press `Ctrl+C` in the terminal to stop the app.

If you prefer to activate the virtual environment first:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks `Activate.ps1`, either run the command shown above with
`.\.venv\Scripts\python.exe` directly, or allow scripts for this terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Run the desktop app

```powershell
.\.venv\Scripts\python.exe desktop_app.py
```

A native window opens with a sidebar: Dashboard, Transactions and Settings.
Close the window (or press `Alt+F4`) to quit.

The desktop app uses the same `data/pocket_ledger.db` file as the Streamlit
app, so existing transactions appear in both. `database.py` and
`utils/calculations.py` are shared, which is why the two interfaces stay in
sync.

### Desktop milestone 1

- Dark, rounded-card layout with sidebar navigation.
- Dashboard: welcome screen with a shortcut to Transactions.
- Transactions: add income/expenses, see them in a table, delete with a
  confirmation dialog.
- Settings: app information, database location and a preview of future work.
- Amounts shown in Indian Rupees (₹); the same validation rules apply.

### How the desktop code is organised

- `desktop_app.py` builds the window, the sidebar and page switching.
- `ui/theme.py` stores the palette, fonts and reusable widgets.
- `ui/dashboard.py`, `ui/transactions.py` and `ui/settings.py` each build one
  page. They only call functions in `database.py` — no SQL lives in the UI.
- Errors from SQLite are caught and shown inside the window instead of
  crashing the app.

## Importing a CSV (Milestone 2)

The desktop app has an **Import CSV** entry in its sidebar. It is meant for
statements you downloaded from your bank — nothing is uploaded anywhere.

1. Choose the `.csv` file. The importer detects the encoding (UTF-8 or
   Windows-1252), the separator (comma, semicolon or tab), the real header row
   and the date format.
2. Check the column mapping. Date, description, amount (or separate
   debit/credit), balance and reference are pre-filled and can be changed.
3. Review the table. Each row can be included or excluded, and its date,
   description, category and amount can be edited inline. Duplicate rows are
   excluded by default; tick one to force-include it. Warning and error rows
   show a reason instead of crashing the import.
4. Click **Import**. All included rows are saved in one all-or-nothing
   database transaction: they get UUIDs, timestamps, change-log entries and
   import hashes just like manually added transactions. A result summary is
   shown afterwards.

Supported value formats include `DD/MM/YYYY`, `DD-Mon-YYYY`, `YYYY-MM-DD`,
Indian number grouping (`1,23,456.78`), currency symbols, `(123.45)`
parentheses for negatives, and `Dr`/`Cr` suffixes. Amounts are parsed with
`Decimal`; no new third-party packages are needed.

Duplicate detection uses a SHA-256 hash of the normalised date, signed amount
in paise and description, plus an occurrence index so two genuinely identical
same-day purchases are both kept. Re-importing the same file creates zero new
transactions. A soft-deleted match is flagged as **WAS DELETED**.

Automatic categories come from the editable `importers/rules.json` file. Add
keywords or change `default_category` there; no code change is needed. Only
the desktop app has this feature — the Streamlit app is unchanged.

## How it works

1. Both interfaces call `initialize_database()` at startup.
2. `database.py` opens the file, then `migrations.py` reads
   `PRAGMA user_version`. If the file is old, it makes a timestamped backup and
   runs each pending step inside its own transaction. An up-to-date database
   only pays for one cheap version check.
3. The form collects a transaction. `add_transaction()` validates the values
   and inserts them using a parameterized query (`?` placeholders), which keeps
   the database safe from malformed input. The same transaction also gets a
   UUID, timestamps, revision 1 and an `insert` entry in the change log.
4. `get_all_transactions()` reads live rows (tombstones are hidden) and the app
   displays them as a table.
5. Deleting marks the row with `deleted_at_ms` instead of removing it, then
   appends a `delete` entry to the change log. That is what lets a future phone
   learn about the deletion.
6. `update_transaction()` edits only the fields you pass, increases the
   revision and appends an `update` entry.

## Database details

The original columns are unchanged, so both apps keep working:

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | Local primary key, still used by both screens |
| `transaction_type` | TEXT | `income` or `expense` |
| `amount` | REAL | Must be greater than zero |
| `category` | TEXT | Required, e.g. Food, Rent, Salary |
| `description` | TEXT | Optional |
| `transaction_date` | TEXT | Stored as `YYYY-MM-DD` |

Milestone 1 adds columns for identity, editing and future sync:

| Column | Type | Notes |
| --- | --- | --- |
| `uuid` | TEXT | Random global id, unique per transaction |
| `created_at_ms` | INTEGER | UTC milliseconds |
| `updated_at_ms` | INTEGER | UTC milliseconds |
| `deleted_at_ms` | INTEGER | `NULL` means the row is live |
| `revision` | INTEGER | Starts at 1, increases on every edit |
| `origin_device_id` | TEXT | Device that created the row |
| `last_modified_by` | TEXT | Device that made the latest change |
| `sync_state` | TEXT | `pending`, `synced` or `conflict` |
| `import_hash` | TEXT | Duplicate marker for future statement imports |
| `external_ref` | TEXT | Bank reference (future) |
| `import_batch_id` | TEXT | Import batch (future) |
| `account_label` | TEXT | Bank account label (future) |

Supporting tables: `app_meta` (device id and settings), `devices` (paired
devices), `sync_changes` (append-only log), `sync_peers` (sync cursors),
`sync_conflicts` (losing versions) and `import_batches` (import history).

`PRAGMA user_version` records the schema version (currently **3**). The
database uses **WAL** mode and a five-second busy timeout, so the desktop
window and a future local API can read and write without tripping over each
other. A unique partial index on `import_hash` prevents importing the same
live transaction twice.

SQLite also enforces the type and amount rules with `CHECK` constraints, so bad
data cannot slip in even if the Python code changes later.

Amounts are stored as `REAL` (floating point) to keep this milestone simple.
A production app would store paise as whole numbers to avoid rounding quirks.

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

The suite never writes to the live database. Migration tests copy it with
SQLite's backup API, and an automatic check fails the run if the live file's
size, timestamp or SHA-256 changes. Tests cover:

- migrating a copy of the real database and preserving every row;
- UUIDs, timestamps, schema version, indexes and the change log;
- running migrations twice, and rolling back a deliberately broken step;
- add, view, update, soft delete and import-hash duplicates;
- CSV parsing, mapping overrides, bad rows, Dr/Cr and Indian number formats;
- same-day duplicates, re-imports, soft-deleted matches and force-including;
- all-or-nothing rollback, change-log entries and import metadata;
- both the Streamlit page and the CustomTkinter window still loading, including
  the CSV import dialog.

## Troubleshooting

- **`streamlit` is not recognised**: run it as
  `.\.venv\Scripts\python.exe -m streamlit run app.py` instead.
- **Port already in use**: run with another port, e.g.
  `streamlit run app.py --server.port 8502`.
- **Table looks empty**: data is per database file. Check that the app is
  running from this folder so it uses `data/pocket_ledger.db`.
- **Desktop window does not open**: install the dependencies again with
  `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and run
  `.\.venv\Scripts\python.exe desktop_app.py` from the project folder.

## Not included yet

Milestone 3 and later: PDF statement import (text first, OCR-ready), FastAPI
sync, Flutter Android, dashboard totals, monthly reports, filters, budgets, and
charts in the desktop app (Matplotlib). The data layer supports editing and soft
deletes, but the screens only expose add, list, delete and CSV import for now.
