"""Milestone 3B UI smoke tests (offscreen, temp DB only)."""

from decimal import Decimal

from PySide6.QtCore import Qt

import database
from importers import csv_parser, service


def _pump(seconds=3.0, predicate=None):
    import time
    from PySide6.QtWidgets import QApplication

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate is not None and predicate():
            return True
        time.sleep(0.01)
    return bool(predicate is not None and predicate())


def test_transactions_multi_currency_display_and_precision(qapp, temp_database):
    import desktop_app

    usd = database.create_account("US Wallet", "USD")
    jpy = database.create_account("Japan Cash", "JPY")

    database.add_transaction(
        "expense", "12.50", "Food", "Burger", "2026-11-20", account_uuid=usd
    )
    database.add_transaction(
        "income", "1000", "Salary", "Allowance", "2026-11-21", account_uuid=jpy
    )

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("transactions")
        assert _pump(5, lambda: view.source_model.rowCount() == 2)

        rows = {row["account_name"]: row for row in view.source_model.rows()}
        usd_row = rows["US Wallet"]
        jpy_row = rows["Japan Cash"]
        assert usd_row["amount_minor"] == 1250
        assert usd_row["currency_code"] == "USD"
        assert jpy_row["amount_minor"] == 1000
        assert jpy_row["currency_code"] == "JPY"

        # Find displayed strings in the model.
        texts = []
        for r in range(view.source_model.rowCount()):
            texts.append(
                [view.source_model.data(view.source_model.index(r, c)) for c in range(6)]
            )
        flat = " | ".join(" ".join(str(x) for x in row) for row in texts)
        assert "$12.50" in flat
        assert "¥1,000" in flat
        assert "US Wallet · USD" in flat
        assert "Japan Cash · JPY" in flat

        # Strict precision rejection on USD account.
        view.account_control.setCurrentIndex(view.account_control.findData(usd))
        view.type_control.setCurrentText("Expense")
        view.amount_entry.setText("1.239")
        view.category_entry.setText("Test")
        view.date_entry.setText("2026-11-22")
        view._on_add()
        assert "decimal" in view.status_label.text().lower()
        assert _pump(2, lambda: True)
        # No new row added.
        assert len(database.get_all_transactions()) == 2

        # JPY rejects decimals.
        view.account_control.setCurrentIndex(view.account_control.findData(jpy))
        view.amount_entry.setText("100.5")
        view.category_entry.setText("Test")
        view.date_entry.setText("2026-11-22")
        view._on_add()
        assert "decimal" in view.status_label.text().lower()
        assert len(database.get_all_transactions()) == 2
    finally:
        app.close()


def test_dashboard_shows_per_account_totals_no_cross_currency(qapp, temp_database):
    import desktop_app

    usd = database.create_account("US Wallet", "USD")
    jpy = database.create_account("Japan Cash", "JPY")
    database.add_transaction("income", "10.00", "Pay", "", "2026-11-20", account_uuid=usd)
    database.add_transaction("expense", "2.50", "Food", "", "2026-11-20", account_uuid=usd)
    database.add_transaction("income", "1000", "Pay", "", "2026-11-20", account_uuid=jpy)

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("dashboard")
        view.refresh()
        assert usd in view.summary_cards
        assert jpy in view.summary_cards

        usd_card = view.summary_cards[usd]
        jpy_card = view.summary_cards[jpy]
        assert usd_card["income"].text() == "$10.00"
        assert usd_card["expense"].text() == "$2.50"
        assert usd_card["balance"].text() == "$7.50"
        assert jpy_card["income"].text() == "¥1,000"
        assert jpy_card["expense"].text() == "¥0"
        assert jpy_card["balance"].text() == "¥1,000"

        # Ensure no mixed total label like combining $ and ¥.
        all_text = []
        for labels in view.summary_cards.values():
            for key, widget in labels.items():
                if hasattr(widget, "text"):
                    all_text.append(widget.text())
        joined = " ".join(all_text)
        assert "$" in joined and "¥" in joined
        # No single label contains both currency symbols.
        for text in all_text:
            assert not ("$" in text and "¥" in text)
    finally:
        app.close()


def test_account_delete_blocked_and_currency_read_only(qapp, temp_database, monkeypatch):
    import desktop_app
    import ui.accounts as accounts_module

    usd = database.create_account("US Wallet", "USD")
    database.add_transaction("expense", "1.00", "Food", "", "2026-11-20", account_uuid=usd)

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("accounts")
        view.refresh()
        # select USD row
        for row in range(view.table.rowCount()):
            item = view.table.item(row, 0)
            if item.data(Qt.UserRole) == usd:
                view.table.selectRow(row)
                break

        # Account with transactions: blocked before confirmation dialog.
        dialog_calls = []

        def fake_confirm(*args, **kwargs):
            dialog_calls.append(kwargs)
            kwargs["on_confirm"]()

        monkeypatch.setattr(accounts_module, "ConfirmDialog", fake_confirm)
        view._confirm_delete()
        msg = view.status_label.text().lower()
        assert "cannot be deleted" in msg
        assert "1 transaction" in msg
        assert dialog_calls == []
        assert database.get_account(usd) is not None

        # Currency is not editable: no currency input in table, only in create form.
        headers = [view.table.horizontalHeaderItem(i).text() for i in range(view.table.columnCount())]
        assert "CURRENCY" in headers
        assert not hasattr(view, "currency_edit")
        # Create form has currency picker but page explains read-only after creation.
        labels_text = []
        for lbl in view.findChildren(type(view.status_label)):
            if hasattr(lbl, "text"):
                labels_text.append(lbl.text())
        # Check explanatory note exists.
        notes = [w.text() for w in view.findChildren(__import__("PySide6.QtWidgets", fromlist=["QLabel"]).QLabel)]
        assert any("fixed after creation" in t.lower() for t in notes)
    finally:
        app.close()


def _select_account_row(view, account_uuid):
    for row in range(view.table.rowCount()):
        item = view.table.item(row, 0)
        if item.data(Qt.UserRole) == account_uuid:
            view.table.selectRow(row)
            return
    raise AssertionError(f"Account row not found: {account_uuid}")


def test_account_delete_only_remaining_blocked(qapp, temp_database, monkeypatch):
    import desktop_app
    import ui.accounts as accounts_module

    default = database.get_default_account()
    dialog_calls = []
    monkeypatch.setattr(
        accounts_module,
        "ConfirmDialog",
        lambda *args, **kwargs: dialog_calls.append((args, kwargs)),
    )

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("accounts")
        view.refresh()
        _select_account_row(view, default["uuid"])
        view._confirm_delete()
        msg = view.status_label.text().lower()
        assert "only remaining account" in msg
        assert "at least one account must remain" in msg
        assert dialog_calls == []
        assert database.get_account(default["uuid"]) is not None
    finally:
        app.close()


def test_account_delete_eligible_requires_confirmation_and_succeeds(qapp, temp_database, monkeypatch):
    import desktop_app
    import ui.accounts as accounts_module

    default = database.get_default_account()
    usd = database.create_account("US Wallet", "USD")
    captured = {}

    def fake_confirm(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        # Do not auto-confirm; verify confirmation was requested.

    monkeypatch.setattr(accounts_module, "ConfirmDialog", fake_confirm)

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("accounts")
        view.refresh()
        _select_account_row(view, usd)
        view._confirm_delete()

        assert captured, "Expected confirmation dialog for eligible account deletion"
        assert captured["args"][1] == "Delete US Wallet?"
        assert "no transactions" in captured["args"][2].lower()
        assert captured["kwargs"].get("confirm_text") == "Delete account"
        assert database.get_account(usd) is not None

        # Now confirm deletion.
        captured["kwargs"]["on_confirm"]()
        assert database.get_account(usd) is None
        assert database.get_default_account()["uuid"] == default["uuid"]
        assert "deleted" in view.status_label.text().lower()
        assert "us wallet" in view.status_label.text().lower()
    finally:
        app.close()


def test_account_delete_unexpected_error_shows_safe_message(qapp, temp_database, monkeypatch):
    import desktop_app
    import ui.accounts as accounts_module

    usd = database.create_account("US Wallet", "USD")

    def boom(*args, **kwargs):
        raise RuntimeError("sensitive traceback detail")

    monkeypatch.setattr(database, "delete_account", boom)
    monkeypatch.setattr(
        accounts_module,
        "ConfirmDialog",
        lambda *args, **kwargs: kwargs["on_confirm"](),
    )

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("accounts")
        view.refresh()
        _select_account_row(view, usd)
        view._confirm_delete()
        msg = view.status_label.text()
        assert "unexpected error" in msg.lower()
        assert "sensitive traceback detail" not in msg
        assert "Traceback" not in msg
    finally:
        app.close()


def test_csv_import_into_non_default_account_and_duplicate_scoped(qapp, temp_database, tmp_path, monkeypatch):
    import desktop_app

    usd = database.create_account("US Wallet", "USD")
    csv_path = tmp_path / "usd.csv"
    csv_path.write_text(
        "Date,Description,Amount\n"
        "22/11/2026,Coffee,12.50\n",
        encoding="utf-8",
    )

    app = desktop_app.PocketLedgerApp()
    dialog = None
    try:
        dialog = app.open_import_dialog()
        # Select USD account
        idx = dialog.account_combo.findData(usd)
        assert idx >= 0
        dialog.account_combo.setCurrentIndex(idx)

        monkeypatch.setattr(dialog, "_choose_file", lambda: str(csv_path))
        summaries = []
        monkeypatch.setattr(dialog, "_show_summary", summaries.append)
        dialog._choose_csv()
        assert _pump(5, lambda: dialog.preview is not None)
        assert dialog.preview.account_uuid == usd
        assert dialog.preview.currency_code == "USD"
        assert "$12.50" in dialog.totals_label.text()

        dialog._confirm()
        assert _pump(5, lambda: len(summaries) == 1)
        assert summaries[0].imported == 1

        rows = database.get_all_transactions(account_uuid=usd)
        assert len(rows) == 1
        assert rows[0]["amount_minor"] == 1250
        assert rows[0]["currency_code"] == "USD"

        # Re-import same file into same account => zero new rows.
        dialog2 = app.open_import_dialog()
        idx2 = dialog2.account_combo.findData(usd)
        dialog2.account_combo.setCurrentIndex(idx2)
        monkeypatch.setattr(dialog2, "_choose_file", lambda: str(csv_path))
        summaries2 = []
        monkeypatch.setattr(dialog2, "_show_summary", summaries2.append)
        dialog2._choose_csv()
        assert _pump(5, lambda: dialog2.preview is not None)
        dialog2._confirm()
        assert _pump(5, lambda: len(summaries2) == 1)
        assert summaries2[0].imported == 0
        assert summaries2[0].skipped_duplicates == 1
        assert len(database.get_all_transactions(account_uuid=usd)) == 1
    finally:
        if dialog is not None and dialog.isVisible():
            dialog.close()
        app.close()
