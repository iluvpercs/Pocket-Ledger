"""Offscreen Qt smoke tests for the desktop app and its screens.

Qt runs with ``QT_QPA_PLATFORM=offscreen`` (set in ``conftest.py``), so these
tests open real windows without a display. All database work targets a temp
database through the ``temp_database`` fixture.
"""

import time

from PySide6.QtCore import Qt

import database


def pump(seconds=3.0, predicate=None):
    """Process Qt events while waiting for a worker thread to finish."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()
        if predicate is not None and predicate():
            return True
        time.sleep(0.01)
    return bool(predicate is not None and predicate())


def test_desktop_window_builds_navigates_and_adds(qapp, temp_database):
    import desktop_app

    app = desktop_app.PocketLedgerApp()
    try:
        assert app.current_page == "dashboard"

        for page in ("transactions", "settings", "dashboard", "transactions"):
            assert app.show_page(page) is not None
            assert app.current_page == page

        view = app.page_widget("transactions")
        view.amount_entry.setText("42.50")
        view.category_entry.setText("Food")
        view.description_entry.setText("Lunch")
        view.date_entry.setText("2026-11-22")
        view._on_add()

        assert pump(5, lambda: len(database.get_all_transactions()) == 1)
        rows = database.get_all_transactions()
        assert rows[0]["amount"] == 42.5
        assert rows[0]["category"] == "Food"
        assert database.get_transaction(rows[0]["id"])["uuid"]
    finally:
        app.close()


def test_desktop_table_loads_sorts_and_filters(qapp, temp_database):
    import desktop_app

    for amount, category in ((10.0, "Food"), (20.0, "Rent"), (30.0, "Food")):
        database.add_transaction("expense", amount, category, "Item", "2026-11-20")

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("transactions")
        assert pump(5, lambda: view.source_model.rowCount() == 3)
        assert view.count_label.text() == "3 entries"
        assert view.proxy_model.rowCount() == 3

        view.filter_entry.setText("Rent")
        assert view.proxy_model.rowCount() == 1
        assert view.proxy_model.source_row_dict(0)["category"] == "Rent"

        view.filter_entry.clear()
        view.proxy_model.sort(5, Qt.DescendingOrder)
        first = view.proxy_model.data(view.proxy_model.index(0, 5))
        assert "30.00" in first
    finally:
        app.close()


def test_desktop_add_edit_delete_via_ui(qapp, temp_database, monkeypatch):
    import desktop_app
    import ui.transactions as transactions_module
    from PySide6.QtWidgets import QDialog

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("transactions")
        view.amount_entry.setText("42.50")
        view.category_entry.setText("Food")
        view._on_add()
        assert pump(5, lambda: len(database.get_all_transactions()) == 1)
        # The add handler kicks off a second worker to reload the table.
        assert pump(5, lambda: view.source_model.rowCount() == 1)

        class FakeValue:
            def __init__(self, value):
                self.value = value

            def text(self):
                return self.value

            def currentText(self):
                return self.value

        class FakeEditDialog:
            def __init__(self, parent, row):
                self.type_control = FakeValue("Expense")
                self.amount_entry = FakeValue("99.00")
                self.category_entry = FakeValue("Travel")
                self.description_entry = FakeValue("Edited")
                self.date_entry = FakeValue("2026-11-23")

            def exec(self):
                return QDialog.Accepted

            def amount_minor(self):
                return 9900

        monkeypatch.setattr(transactions_module, "EditTransactionDialog", FakeEditDialog)
        view.table.selectRow(0)
        view._on_edit()
        assert pump(
            5,
            lambda: bool(database.get_all_transactions())
            and database.get_all_transactions()[0]["amount"] == 99.0,
        )
        assert database.get_all_transactions()[0]["category"] == "Travel"

        class FakeConfirmDialog:
            def __init__(self, parent, title, message, **kwargs):
                kwargs["on_confirm"]()

        monkeypatch.setattr(transactions_module, "ConfirmDialog", FakeConfirmDialog)
        view.table.selectRow(0)
        view._confirm_delete()
        assert pump(5, lambda: len(database.get_all_transactions()) == 0)
    finally:
        app.close()


def test_desktop_import_dialog_opens(qapp, temp_database):
    import desktop_app

    app = desktop_app.PocketLedgerApp()
    dialog = None
    try:
        assert "import" in app.nav_buttons
        dialog = app.show_page("import")
        assert dialog is not None
        assert dialog.windowTitle() == "Pocket Ledger · Import CSV"
        assert "0 rows" in dialog.counts_label.text()
        assert dialog.preview_model.rowCount() == 0
    finally:
        if dialog is not None:
            dialog.close()
            pump(0.2)
        app.close()


def test_desktop_import_dialog_loads_and_commits_csv(qapp, temp_database, tmp_path, monkeypatch):
    import desktop_app

    csv_path = tmp_path / "statement.csv"
    csv_path.write_text(
        "Date,Description,Amount\n"
        "22/11/2026,Tea Stall,50.00 Dr\n"
        "23/11/2026,Monthly salary,25,000.00 Cr\n",
        encoding="utf-8",
    )

    app = desktop_app.PocketLedgerApp()
    dialog = None
    try:
        dialog = app.show_page("import")
        monkeypatch.setattr(dialog, "_choose_file", lambda: str(csv_path))
        summaries = []
        monkeypatch.setattr(dialog, "_show_summary", summaries.append)

        dialog._choose_csv()
        assert pump(5, lambda: dialog.preview is not None)
        assert dialog.preview_model.rowCount() == 2
        assert "2 rows" in dialog.counts_label.text()

        dialog._confirm()
        assert pump(5, lambda: len(database.get_all_transactions()) == 2)
        assert pump(5, lambda: len(summaries) == 1)
        assert summaries[0].imported == 2
        assert {row["category"] for row in database.get_all_transactions()} <= {
            "Food",
            "Salary",
            "Other",
        }
    finally:
        if dialog is not None:
            dialog.close()
            pump(0.2)
        app.close()


def test_streamlit_module_is_gone(project_root):
    assert not (project_root / "app.py").exists()
