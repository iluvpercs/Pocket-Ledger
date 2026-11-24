"""Phase 3 regressions: manual amounts, fresh pages, icons and UI fit.

Every test uses the isolated ``temp_database`` fixture and offscreen Qt. The
live database is never opened for reading or writing by these checks.
"""

import time
from datetime import date, timedelta

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
)

import database
from utils.money import normalize_amount_input, parse_to_minor


def wait_until(predicate, message, timeout=5.0):
    """Pump Qt events until ``predicate`` is true, then assert it stayed true."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return
        time.sleep(0.01)
    QApplication.processEvents()
    assert predicate(), message


def _set_income(view, amount):
    view.type_control.setCurrentIndex(1)
    view.amount_entry.setText(amount)
    view.category_entry.setText("Gift")
    view.description_entry.setText("Phase 3 check")
    view.date_entry.setText(date.today().isoformat())
    view._on_add()


@pytest.mark.parametrize(
    ("value", "precision", "expected"),
    [
        ("31,417", 2, 3141700),
        ("31,417.00", 2, 3141700),
        ("1,23,456.78", 2, 12345678),
        ("1,234,567.89", 2, 123456789),
        ("31,417", 0, 31417),
        ("1,234.567", 3, 1234567),
    ],
)
def test_manual_grouped_amounts_are_exact_minor_units(value, precision, expected):
    assert parse_to_minor(
        normalize_amount_input(value), precision=precision, strict=True
    ) == expected


def test_parse_to_minor_still_rejects_commas_without_the_manual_normalizer():
    # The CSV importer owns its own grouping rules; the shared parser stays
    # strict so an accidental comma cannot silently become a different value.
    with pytest.raises(ValueError):
        parse_to_minor("31,417", precision=2, strict=True)


def test_ui_add_accepts_commas_and_keeps_decimal_validation(qapp, temp_database):
    import desktop_app

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("transactions")
        _set_income(view, "31,417.00")
        wait_until(
            lambda: len(database.get_all_transactions()) == 1,
            "grouped amount was not saved",
        )
        row = database.get_all_transactions()[0]
        assert row["amount_minor"] == 3141700
        assert row["amount"] == 31417.0
        wait_until(
            lambda: "added" in view.status_label.text().lower(),
            "add confirmation did not arrive",
        )

        view.amount_entry.setText("1,23,456.789")
        view._on_add()
        wait_until(
            lambda: "decimal places" in view.status_label.text().lower(),
            "excess decimals were not rejected after comma stripping",
        )
        assert len(database.get_all_transactions()) == 1
    finally:
        app.close()


def test_ui_edit_accepts_commas(qapp, temp_database, monkeypatch):
    import desktop_app
    import ui.transactions as transactions_module
    from PySide6.QtWidgets import QDialog

    account = database.get_default_account()["uuid"]
    database.add_transaction(
        "income", "100.00", "Gift", "", date.today().isoformat(), account_uuid=account
    )

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("transactions")
        wait_until(
            lambda: view.source_model.rowCount() == 1, "transaction table did not load"
        )

        def accept_with_commas(self):
            self.amount_entry.setText("1,23,456.78")
            return QDialog.Accepted

        monkeypatch.setattr(transactions_module.EditTransactionDialog, "exec", accept_with_commas)
        view.table.selectRow(0)
        view._on_edit()
        wait_until(
            lambda: database.get_all_transactions()[0]["amount_minor"] == 12345678,
            "grouped edit was not saved",
        )
    finally:
        app.close()


def test_transaction_changes_refresh_cached_dashboard(
    qapp, temp_database, monkeypatch
):
    import desktop_app
    import ui.transactions as transactions_module

    app = desktop_app.PocketLedgerApp()
    try:
        dashboard = app.page_widget("dashboard")
        view = app.show_page("transactions")
        _set_income(view, "1,250.00")
        wait_until(
            lambda: dashboard.kpi_cards["balance"].value_label.text() == "₹1,250.00",
            "dashboard did not refresh after add",
        )
        wait_until(
            lambda: dashboard.kpi_cards["income"].value_label.text() == "₹1,250.00",
            "dashboard income did not refresh after add",
        )

        # Navigating away and back must re-read the database, not replay a cache.
        app.show_page("settings")
        app.show_page("dashboard")
        assert dashboard.kpi_cards["balance"].value_label.text() == "₹1,250.00"

        app.show_page("transactions")
        wait_until(
            lambda: view.source_model.rowCount() == 1,
            "transaction table did not reload after navigation",
        )

        def accept_edit(self):
            self.amount_entry.setText("99.00")
            return QDialog.Accepted

        monkeypatch.setattr(transactions_module.EditTransactionDialog, "exec", accept_edit)
        view.table.selectRow(0)
        view._on_edit()
        wait_until(
            lambda: dashboard.kpi_cards["balance"].value_label.text() == "₹99.00",
            "dashboard did not refresh after edit",
        )

        class FakeConfirmDialog:
            def __init__(self, parent, title, message, **kwargs):
                kwargs["on_confirm"]()

        monkeypatch.setattr(transactions_module, "ConfirmDialog", FakeConfirmDialog)
        wait_until(
            lambda: view.source_model.rowCount() == 1, "edited row was not reloaded"
        )
        view.table.selectRow(0)
        view._confirm_delete()
        wait_until(
            lambda: (
                not database.get_all_transactions()
                and dashboard.kpi_cards["balance"].value_label.text() == "₹0.00"
            ),
            "dashboard did not refresh after delete",
        )
    finally:
        app.close()


def test_account_change_refreshes_cached_dashboard(qapp, temp_database):
    import desktop_app

    app = desktop_app.PocketLedgerApp()
    try:
        dashboard = app.page_widget("dashboard")
        accounts = app.show_page("accounts")
        assert len(dashboard.summary_cards) == 1

        accounts.name_entry.setText("US Wallet")
        index = next(
            i
            for i in range(accounts.currency_combo.count())
            if accounts.currency_combo.itemData(i) == "USD"
        )
        accounts.currency_combo.setCurrentIndex(index)
        accounts._create_account()
        wait_until(
            lambda: len(dashboard.summary_cards) == 2,
            "dashboard account cards did not refresh",
        )
        assert any(
            "US Wallet" in dashboard.scope_combo.itemText(i)
            for i in range(dashboard.scope_combo.count())
        )

        app.show_page("dashboard")
        assert len(dashboard.summary_cards) == 2
    finally:
        app.close()


def test_dashboard_period_change_recalculates_from_loaded_rows(qapp, temp_database):
    import desktop_app

    account = database.get_default_account()["uuid"]
    last_month = (date.today().replace(day=1) - timedelta(days=1)).isoformat()
    for amount, when in (("900.00", last_month), ("100.00", date.today().isoformat())):
        database.add_transaction(
            "income", amount, "Salary", "", when, account_uuid=account
        )

    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("dashboard")
        index = view.period_combo.findData("last_month")
        view.period_combo.setCurrentIndex(index)
        QApplication.processEvents()
        assert view.kpi_cards["income"].value_label.text() == "₹900.00"

        index = view.period_combo.findData("all")
        view.period_combo.setCurrentIndex(index)
        QApplication.processEvents()
        assert view.kpi_cards["income"].value_label.text() == "₹1,000.00"
    finally:
        app.close()


def test_visible_controls_fit_at_minimum_window(qapp, temp_database):
    import desktop_app
    from ui import theme

    qt_app = QApplication.instance()
    previous_stylesheet = qt_app.styleSheet()
    qt_app.setStyleSheet(theme.STYLESHEET)
    app = desktop_app.PocketLedgerApp()
    try:
        app.show()
        app.resize(1020, 680)
        QApplication.processEvents()
        for page_name in ("dashboard", "transactions", "accounts", "settings"):
            view = app.show_page(page_name)
            QApplication.processEvents()
            issues = []
            widgets = []
            for widget_type in (QLabel, QPushButton, QComboBox, QLineEdit):
                widgets.extend(view.findChildren(widget_type))
            for widget in widgets:
                if not widget.isVisible() or widget.width() <= 0 or widget.height() <= 0:
                    continue
                if isinstance(widget, QLabel) and widget.wordWrap():
                    continue
                hint = widget.sizeHint()
                if hint.width() > widget.width() + 2 or hint.height() > widget.height() + 2:
                    label = (
                        widget.currentText()
                        if isinstance(widget, QComboBox)
                        else widget.text()
                    )
                    issues.append(
                        (
                            type(widget).__name__,
                            label[:40],
                            hint.width(),
                            widget.width(),
                            hint.height(),
                            widget.height(),
                        )
                    )
            assert not issues, (page_name, issues)
            if page_name in ("dashboard", "settings"):
                scrollers = [
                    area
                    for area in view.findChildren(QScrollArea)
                    if area.isVisible() and area.verticalScrollBar().maximum() > 0
                ]
                assert scrollers, page_name
    finally:
        app.close()
        qt_app.setStyleSheet(previous_stylesheet)


def test_desktop_window_uses_supplied_pc_icon(qapp, temp_database, project_root):
    import desktop_app

    assert desktop_app.APP_ICON_PATH.is_file()
    assert desktop_app.APP_ICON_PATH.name == "PC.ico"
    assert (project_root / "icons" / "PC.svg").is_file()
    assert (project_root / "icons" / "Mobile.svg").is_file()

    app = desktop_app.PocketLedgerApp()
    try:
        icon = app.windowIcon()
        assert not icon.isNull()
        sizes = {(size.width(), size.height()) for size in icon.availableSizes()}
        assert (64, 64) in sizes
    finally:
        app.close()


def test_settings_scrolls_and_states_future_work_only(qapp, temp_database):
    import desktop_app

    app = desktop_app.PocketLedgerApp()
    try:
        app.show()
        app.resize(1020, 680)
        settings = app.show_page("settings")
        QApplication.processEvents()

        assert isinstance(settings.scroll_area, QScrollArea)
        assert settings.scroll_area.isVisible()
        text = "\n".join(label.text() for label in settings.findChildren(QLabel))
        assert "Local only" in text
        assert "Phase 5" in text and "Android" in text
        assert "Phase 6" in text and "Wi-Fi Sync" in text
        assert "Not implemented" in text
        assert {button.text() for button in settings.findChildren(QPushButton)} == {
            "Copy path"
        }

        for button in settings.findChildren(QPushButton):
            assert button.sizeHint().width() <= button.width() + 1
            assert button.sizeHint().height() <= button.height() + 1
    finally:
        app.close()


def test_shared_stylesheet_stays_on_palette_without_shadows(qapp):
    from ui import theme

    stylesheet = theme.STYLESHEET
    for colour in (theme.BLACK, theme.VIOLET, theme.LIME, theme.WHITE):
        assert colour in stylesheet
    for selector in (
        "QPushButton:hover",
        "QPushButton:focus",
        "QComboBox QAbstractItemView::item:selected",
        "QTableView::item:hover",
    ):
        assert selector in stylesheet
    lowered = stylesheet.lower()
    assert "gradient" not in lowered
    assert "shadow" not in lowered
    assert "QLabel { background: transparent; }" in stylesheet
