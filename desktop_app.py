"""Pocket Ledger - desktop edition, built with PySide6 (Qt for Python).

Run with:  python desktop_app.py

The sidebar switches between cached pages in a ``QStackedWidget``. All data
work goes through ``database.py`` (and ``importers.service`` for CSV import);
this file only wires screens together.
"""

import sys

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
from ui.dashboard import DashboardView
from ui.import_csv import ImportCsvDialog
from ui.settings import SettingsView
from ui.theme import IconBadge, apply_theme
from ui.transactions import TransactionsView

APP_TITLE = "Pocket Ledger"
WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 760
SIDEBAR_WIDTH = 300

PAGES = {
    "dashboard": DashboardView,
    "transactions": TransactionsView,
    "settings": SettingsView,
}

NAV_ITEMS = (
    ("dashboard", "Dashboard"),
    ("transactions", "Transactions"),
    ("import", "Import CSV"),
    ("settings", "Settings"),
)


class PocketLedgerApp(QMainWindow):
    """Main window: a fixed sidebar and one cached page at a time."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
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
        layout.setContentsMargins(16, 24, 14, 22)
        layout.setSpacing(4)

        brand = QWidget()
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(10)
        brand_layout.addWidget(IconBadge("₹"))
        names = QVBoxLayout()
        title = QLabel("Pocket Ledger")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        caption = QLabel("Personal finance")
        caption.setObjectName("muted")
        names.addWidget(title)
        names.addWidget(caption)
        brand_layout.addLayout(names, 1)
        layout.addWidget(brand)
        layout.addSpacing(26)

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
        footer = QLabel("Local data only\nDesktop · v0.3")
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

        if hasattr(page, "refresh") and name == "transactions":
            page.refresh()
        return page

    def page_widget(self, name=None):
        """Return a cached page, mostly useful for tests."""
        return self.pages.get(name or self.current_page)

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

    # ----------------------------------------------------------- error screen
    def _show_database_error(self, error):
        QMessageBox.critical(self, "Pocket Ledger", f"The database could not be opened:\n{error}")


def main():
    app = QApplication(sys.argv)
    apply_theme(app)
    window = PocketLedgerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
