"""Smoke tests proving both existing interfaces still work on the new schema.

These are deliberately small: they build the real screens and check that the
old public database functions still behave as expected. Detailed database
behaviour is covered in ``test_database.py``.
"""

import database


def test_streamlit_app_still_loads_and_lists_transactions(
    temp_database, project_root
):
    from streamlit.testing.v1 import AppTest

    database.add_transaction("expense", 42.5, "Food", "Lunch", "2026-11-22")

    app = AppTest.from_file(str(project_root / "app.py"), default_timeout=60)
    app.run()

    assert not app.exception
    assert app.title[0].value == "💰 Pocket Ledger"
    assert len(app.dataframe) == 1
    assert len(app.dataframe[0].value) == 1


def test_desktop_window_builds_navigates_and_adds(temp_database):
    import desktop_app

    app = desktop_app.PocketLedgerApp()
    try:
        app.withdraw()  # keep the test run from flashing a window
        app.update_idletasks()
        app.update()

        assert app.current_page == "dashboard"

        for page in ("transactions", "settings", "dashboard", "transactions"):
            app.show_page(page)
            app.update_idletasks()
            app.update()
            assert app.current_page == page

        view = app.page_container.winfo_children()[0]
        view.amount_entry.insert(0, "42.50")
        view.category_entry.insert(0, "Food")
        view._on_add()
        app.update_idletasks()

        rows = database.get_all_transactions()
        assert len(rows) == 1
        assert rows[0]["amount"] == 42.5
        assert rows[0]["category"] == "Food"

        saved = database.get_transaction(rows[0]["id"])
        assert saved["uuid"]
    finally:
        app.destroy()


def test_desktop_import_dialog_opens(temp_database):
    import desktop_app

    app = desktop_app.PocketLedgerApp()
    dialog = None
    try:
        app.withdraw()
        app.update_idletasks()
        app.update()

        assert "import" in app.nav_buttons
        dialog = app.show_page("import")
        app.update_idletasks()
        app.update()

        assert dialog is not None
        assert dialog.winfo_exists()
        assert dialog.title() == "Pocket Ledger · Import CSV"
        assert "0 rows" in dialog.counts_label.cget("text")
    finally:
        if dialog is not None and dialog.winfo_exists():
            dialog.close()
            app.update()
        app.destroy()
