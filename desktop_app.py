"""Pocket Ledger - desktop edition, built with PySide6 (Qt for Python).

Run with:  python desktop_app.py

The sidebar switches between cached pages in a ``QStackedWidget``. All data
work goes through ``database.py`` (and ``importers.service`` for CSV import);
this file only wires screens together.
"""

import sys
from pathlib import Path

import release_paths  # must configure frozen data paths before database imports
release_paths.configure_environment()

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import database
from ui.accounts import AccountsView
from ui.dashboard import DashboardView
from ui.import_csv import ImportCsvDialog
from ui.settings import SettingsView
from ui.theme import BadgeLabel, IconBadge, apply_theme
from ui.transactions import TransactionsView
from version import APP_ID, APP_NAME, APP_VERSION, APP_VERSION_TEXT

def _resource_path(relative):
    """Resolve bundled assets from source runs and PyInstaller bundles alike."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative


APP_TITLE = APP_NAME
APP_VERSION_LABEL = APP_VERSION_TEXT
APP_ICON_PATH = _resource_path("icons/PC.ico")
APP_USER_MODEL_ID = APP_ID
WINDOW_WIDTH = 1240
WINDOW_HEIGHT = 820
SIDEBAR_WIDTH = 300

PAGES = {
    "dashboard": DashboardView,
    "transactions": TransactionsView,
    "accounts": AccountsView,
    "settings": SettingsView,
}

NAV_ITEMS = (
    ("dashboard", "Dashboard"),
    ("transactions", "Transactions"),
    ("accounts", "Accounts"),
    ("import", "Import CSV"),
    ("settings", "Settings"),
)


class PocketLedgerApp(QMainWindow):
    """Main window: a fixed sidebar and one cached page at a time."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(1020, 680)

        self.current_page = None
        self.nav_buttons = {}
        self.pages = {}
        self.import_dialog = None
        self.page_container = QStackedWidget()

        try:
            database.initialize_database()
        except Exception as error:
            self._show_database_error(error)
            return

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())

        page_area = QWidget()
        page_layout = QVBoxLayout(page_area)
        page_layout.setContentsMargins(28, 24, 28, 24)
        page_layout.addWidget(self.page_container)
        layout.addWidget(page_area, 1)
        self.setCentralWidget(central)

        self.show_page("dashboard")

    # --------------------------------------------------------------- sidebar
    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 14, 20)
        layout.setSpacing(4)

        brand = QWidget()
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(12)
        brand_layout.addWidget(IconBadge("PL", size=52))
        names = QVBoxLayout()
        names.setSpacing(2)
        title = QLabel("Pocket Ledger")
        title.setStyleSheet("font-size: 15px; font-weight: 800;")
        caption = QLabel("YOUR MONEY. YOUR CONTROL.")
        caption.setObjectName("eyebrow")
        caption.setWordWrap(True)
        names.addWidget(title)
        names.addWidget(caption)
        brand_layout.addLayout(names, 1)
        layout.addWidget(brand)
        layout.addSpacing(22)

        divider = QFrame()
        divider.setObjectName("divider")
        layout.addWidget(divider)
        layout.addSpacing(14)

        menu = QLabel("MENU")
        menu.setObjectName("field")
        layout.addWidget(menu)

        group = QButtonGroup(self)
        for key, label in NAV_ITEMS:
            button = QPushButton(label)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, name=key: self.show_page(name))
            group.addButton(button)
            self.nav_buttons[key] = button
            layout.addWidget(button)

        layout.addStretch(1)
        if database.is_development_database():
            layout.addWidget(BadgeLabel("DEV DB", tone="lime"))
        footer = QLabel(f"Local data only\nDesktop · v{APP_VERSION}")
        footer.setObjectName("muted")
        layout.addWidget(footer)
        return sidebar

    # ------------------------------------------------------------- page area
    def show_page(self, name):
        """Show (or lazily build) a page; ``import`` opens a dialog instead."""
        if name == "import":
            dialog = self.open_import_dialog()
            if self.current_page in self.nav_buttons:
                self.nav_buttons[self.current_page].setChecked(True)
            return dialog

        if name not in PAGES or name not in self.nav_buttons:
            return None

        page = self.pages.get(name)
        if page is None:
            page = PAGES[name](self.page_container, self)
            self.pages[name] = page
            self.page_container.addWidget(page)
        self.page_container.setCurrentWidget(page)
        self.nav_buttons[name].setChecked(True)
        self.current_page = name

        if hasattr(page, "refresh") and name in ("transactions", "dashboard", "accounts"):
            page.refresh()
        return page

    def page_widget(self, name=None):
        """Return a cached page, mostly useful for tests."""
        return self.pages.get(name or self.current_page)

    def notify_accounts_changed(self):
        """Refresh pages that show account names, currencies or totals."""
        for name in ("transactions", "dashboard", "accounts"):
            page = self.pages.get(name)
            if page is None:
                continue
            if hasattr(page, "on_accounts_changed"):
                page.on_accounts_changed()
            elif hasattr(page, "refresh"):
                page.refresh()

    def notify_data_changed(self, source=None):
        """Invalidate cached pages after transaction data changes.

        ``source`` is a page that has already scheduled its own refresh. It is
        skipped so one edit never triggers the same query twice. Pages that are
        not built yet need no work: :meth:`show_page` refreshes them when they
        are first opened.
        """
        for name in ("dashboard", "accounts", "transactions"):
            page = self.pages.get(name)
            if page is None or page is source:
                continue
            if hasattr(page, "on_data_changed"):
                page.on_data_changed()
            elif hasattr(page, "refresh"):
                page.refresh()

    # ------------------------------------------------------------ CSV import
    def open_import_dialog(self):
        """Open (or focus) the CSV import dialog from the sidebar."""
        if self.import_dialog is not None and self.import_dialog.isVisible():
            self.import_dialog.raise_()
            self.import_dialog.activateWindow()
            return self.import_dialog
        self.import_dialog = ImportCsvDialog(self, on_close=self._on_import_dialog_closed)
        self.import_dialog.show()
        return self.import_dialog

    def _on_import_dialog_closed(self):
        self.import_dialog = None
        self.notify_accounts_changed()

    # ----------------------------------------------------------- error screen
    def _show_database_error(self, error):
        QMessageBox.critical(self, "Pocket Ledger", f"The database could not be opened:\n{error}")


def _set_windows_app_user_model_id():
    """Keep the taskbar grouped under Pocket Ledger instead of python.exe."""
    if sys.platform != "win32":
        return
    try:
        from ctypes import windll

        windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        # Icon grouping is cosmetic; never block the app on a platform quirk.
        pass


def main():
    _set_windows_app_user_model_id()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    apply_theme(app)
    window = PocketLedgerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
