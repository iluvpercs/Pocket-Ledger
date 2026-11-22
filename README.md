# Pocket Ledger

A small, private personal finance tracker built with Python, Streamlit and
SQLite. It runs entirely on your own computer — there are no accounts, no bank
connections and no data leaves your machine.

## Milestone 1 features

- Automatically creates a local SQLite database on first run.
- Add income and expense transactions with amount, category, description and date.
- View all saved transactions, newest first.
- Delete a transaction (with a confirmation step).
- Input validation: amount must be greater than zero, type must be income or
  expense, and the date must be valid.
- Amounts are shown in Indian Rupees (₹).

## Project structure

```
pocket-ledger/
├── app.py                  # Streamlit interface (form, table, delete)
├── database.py             # All SQLite code (create, insert, read, delete)
├── requirements.txt        # Python packages to install
├── README.md               # This file
├── .gitignore              # Files that should not be committed to Git
├── data/
│   └── pocket_ledger.db    # Created automatically; your data lives here
├── pages/                  # Empty for now; Milestone 2 pages go here
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

## How it works

1. `app.py` calls `initialize_database()` as soon as the page loads.
2. `database.py` creates the `data` folder if needed, then runs
   `CREATE TABLE IF NOT EXISTS transactions (...)`. Running this repeatedly is
   safe, so the database is always ready.
3. The form collects a transaction. `add_transaction()` validates the values
   and inserts them using a parameterized query (`?` placeholders), which keeps
   the database safe from malformed input.
4. `get_all_transactions()` reads every row and the app displays it as a table.
5. Deleting uses `DELETE FROM transactions WHERE id = ?`, so only the chosen row
   is removed.

## Database details

The table is created with these columns:

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | Primary key, filled in automatically |
| `transaction_type` | TEXT | `income` or `expense` |
| `amount` | REAL | Must be greater than zero |
| `category` | TEXT | Required, e.g. Food, Rent, Salary |
| `description` | TEXT | Optional |
| `transaction_date` | TEXT | Stored as `YYYY-MM-DD` |

SQLite also enforces the type and amount rules with `CHECK` constraints, so bad
data cannot slip in even if the Python code changes later.

Amounts are stored as `REAL` (floating point) to keep this milestone simple.
A production app would store paise as whole numbers to avoid rounding quirks.

## Your data

- Everything is stored in `data/pocket_ledger.db`.
- `.gitignore` excludes database files, so personal data is never committed.
- To start over, stop the app, delete `data/pocket_ledger.db`, and restart.
  The empty database is recreated automatically.

## Troubleshooting

- **`streamlit` is not recognised**: run it as
  `.\.venv\Scripts\python.exe -m streamlit run app.py` instead.
- **Port already in use**: run with another port, e.g.
  `streamlit run app.py --server.port 8502`.
- **Table looks empty**: data is per database file. Check that the app is
  running from this folder so it uses `data/pocket_ledger.db`.

## Not included yet

Milestone 2 and later: dashboard totals, monthly reports, filters, editing
transactions, budgets. The `pages/` and `utils/` folders are ready for them.
