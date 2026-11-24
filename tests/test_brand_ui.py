"""Brand redesign smoke tests: real data, currency safety and readable layout.

All tests use the isolated ``temp_database`` fixture; none of them read or write
the live database.
"""

from datetime import date, timedelta

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

import database


def _kpi_text(view):
    return {
        key: card.value_label.text()
        for key, card in view.kpi_cards.items()
    }


def test_dashboard_headline_figures_are_database_backed(qapp, temp_database):
    import desktop_app

    account = database.get_default_account()["uuid"]
    last_month = (date.today().replace(day=1) - timedelta(days=1)).isoformat()
    database.add_transaction(
        "income", "1500.00", "Salary", "Pay", date.today().isoformat(), account_uuid=account
    )
    database.add_transaction(
        "expense", "250.00", "Food", "Lunch", date.today().isoformat(), account_uuid=account
    )
    database.add_transaction(
        "income", "900.00", "Salary", "Old pay", last_month, account_uuid=account
    )

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("dashboard")
        values = _kpi_text(view)
        assert values["balance"] == "₹2,150.00"
        assert values["income"] == "₹1,500.00"
        assert values["expense"] == "₹250.00"
        assert values["net"] == "₹1,250.00"

        # The concept's illustrative numbers must never be hard-coded.
        joined = " ".join(values.values())
        assert "42,200" not in joined and "44,000" not in joined and "1,800" not in joined

        index = view.period_combo.findData("last_month")
        assert index >= 0
        view.period_combo.setCurrentIndex(index)
        QApplication.processEvents()
        assert _kpi_text(view)["income"] == "₹900.00"
        assert "Old pay" in view.recent_table.item(0, 1).text()

        index = view.period_combo.findData("all")
        view.period_combo.setCurrentIndex(index)
        QApplication.processEvents()
        assert _kpi_text(view)["income"] == "₹2,400.00"
    finally:
        app.close()


def test_dashboard_never_mixes_currencies_in_one_figure(qapp, temp_database):
    import desktop_app

    usd = database.create_account("US Wallet", "USD")
    jpy = database.create_account("Japan Cash", "JPY")
    database.add_transaction(
        "income", "10.00", "Pay", "", "2026-11-20", account_uuid=usd
    )
    database.add_transaction(
        "expense", "2.50", "Food", "", "2026-11-20", account_uuid=usd
    )
    database.add_transaction(
        "income", "1000", "Pay", "", "2026-11-20", account_uuid=jpy
    )

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("dashboard")
        index = view.period_combo.findData("all")
        view.period_combo.setCurrentIndex(index)

        for account_uuid, expected, forbidden in (
            (usd, "$", "¥"),
            (jpy, "¥", "$"),
        ):
            combo_index = next(
                i
                for i in range(view.scope_combo.count())
                if (view.scope_combo.itemData(i) or {}).get("value") == account_uuid
            )
            view.scope_combo.setCurrentIndex(combo_index)
            QApplication.processEvents()
            for value in _kpi_text(view).values():
                assert expected in value
                assert forbidden not in value
                assert "₹" not in value
    finally:
        app.close()


def test_dashboard_scrolls_and_buttons_fit_at_minimum_window(qapp, temp_database):
    import desktop_app

    account = database.get_default_account()["uuid"]
    for amount, category in (("20.00", "Food"), ("75.00", "Salary")):
        database.add_transaction(
            "income", amount, category, "", date.today().isoformat(), account_uuid=account
        )

    app = desktop_app.PocketLedgerApp()
    try:
        app.show()
        app.resize(1020, 680)
        view = app.show_page("dashboard")
        QApplication.processEvents()

        assert view.scroll_area.isVisible()
        assert view.scroll_area.verticalScrollBar().maximum() > 0
        assert view.kpi_cards["balance"].value_label.wordWrap()

        buttons = [
            button
            for button in view.findChildren(QPushButton)
            if button.isVisible() and button.text()
        ]
        assert buttons
        for button in buttons:
            assert button.sizeHint().width() <= button.width() + 1, button.text()
            assert button.sizeHint().height() <= button.height() + 1, button.text()

        # Long explanatory text wraps instead of being clipped.
        for label in view.findChildren(QLabel):
            if len(label.text()) > 55:
                assert label.wordWrap(), label.text()
    finally:
        app.close()
