"""User-data paths for frozen Windows builds.

The source-tree app keeps its database in ``data/`` next to the code, which is
convenient for development and tests. Packaged builds must not write into the
installation folder: an update or uninstall has to leave the user's database
alone.

* Portable builds ship a ``portable.marker`` file, so data stays next to the
  extracted EXE in ``data/``.
* Installed builds put data in ``%LOCALAPPDATA%\\Pocket Ledger\\data``.
* An explicit ``POCKET_LEDGER_DB`` always wins.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DATA_DIR_NAME = "Pocket Ledger"
PORTABLE_MARKER = "portable.marker"
DB_FILE_NAME = "pocket_ledger.db"
DB_PATH_ENV_VAR = "POCKET_LEDGER_DB"


def is_frozen():
    """True when running from a PyInstaller bundle rather than the source tree."""
    return bool(getattr(sys, "frozen", False))


def default_data_dir(exe_path=None, local_appdata=None, portable=None):
    """Return the data directory for a packaged Windows build.

    ``exe_path``, ``local_appdata`` and ``portable`` are injectable so this can
    be tested without touching real user folders.
    """
    executable = Path(exe_path or sys.executable).resolve()
    exe_dir = executable.parent
    if portable is None:
        portable = is_frozen() and (exe_dir / PORTABLE_MARKER).exists()
    if portable:
        return exe_dir / "data"

    base = local_appdata or os.environ.get("LOCALAPPDATA")
    if not base:
        base = Path.home() / "AppData" / "Local"
    return Path(base) / APP_DATA_DIR_NAME / "data"


def configure_environment(exe_path=None, local_appdata=None, portable=None):
    """Set ``POCKET_LEDGER_DB`` for frozen builds and return the chosen path.

    Source runs and explicit environment overrides are left untouched.
    """
    if not is_frozen() or os.environ.get(DB_PATH_ENV_VAR):
        return None
    data_dir = default_data_dir(
        exe_path=exe_path, local_appdata=local_appdata, portable=portable
    )
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / DB_FILE_NAME
    os.environ[DB_PATH_ENV_VAR] = str(db_path)
    return db_path
