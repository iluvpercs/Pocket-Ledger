"""Regression tests for batch deletion from the Transactions screen.

These tests drive the real Delete button handler (via ``clicked``), the Delete
key and the row context menu against a fresh temporary database. The modal
confirmation is shortened by patching ``ConfirmDialog.exec`` so the real dialog
class and the real callback wiring are still exercised.
"""

import json
import sqlite3
import time
from contextlib import contextmanager
from datetime import date, timedelta

import pytest
from PySide6.QtCore import QEvent, QItemSelectionModel, QPoint, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QPushButton

import database
import desktop_app
import ui.transactions as transactions_module


def pump(seconds=5.0, predicate=None):
    """Process Qt events while a database worker thread finishes."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate is not None and predicate():
            return True
        time.sleep(0.01)
    return bool(predicate is not None and predicate())


def seed_transactions(count):
    """Add ``count`` distinct rows and return their integer ids in insertion order."""
    ids = []
    for index in range(count):
        day = date(2026, 1, 1) + timedelta(days=index)
        ids.append(
            database.add_transaction(
                "expense",
                10.0 + index,
                f"Category{index}",
                f"Item {index}",
                day.isoformat(),
            )
        )
    return ids


@contextmanager
def open_transactions(count):
    seed_transactions(count)
    app = desktop_app.PocketLedgerApp()
    try:
        view = app.show_page("transactions")
        assert pump(5, lambda: view.source_model.rowCount() == count)
        yield app, view
    finally:
        app.close()
        pump(0.2)


def delete_button(view):
    """Find the Delete button exactly as the user sees it."""
    buttons = [
        button
        for button in view.findChildren(QPushButton)
        if button.text() == "Delete selected"
    ]
    assert len(buttons) == 1
    return buttons[0]


def select_proxy_rows(view, rows):
    """Select whole rows through the table's own selection model."""
    rows = list(rows)
    selection = view.table.selectionModel()
    selection.clearSelection()
    if rows:
        # Set the current index once: doing it after every select would collapse
        # a multi-row selection down to the last row in Qt.
        view.table.setCurrentIndex(view.proxy_model.index(rows[0], 0))
    for row in rows:
        index = view.proxy_model.index(row, 0)
        selection.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)


def live_ids():
    return {row["id"] for row in database.get_all_transactions()}


@pytest.fixture
def auto_confirm(monkeypatch):
    """Auto-accept the real confirmation dialog and record each prompt."""
    prompts = []

    def accept(self):
        body = self.findChild(QLabel, "subtitle")
        prompts.append(body.text() if body is not None else "")
        self._confirm()
        return QDialog.Accepted

    monkeypatch.setattr(transactions_module.ConfirmDialog, "exec", accept)
    return prompts


def test_delete_one_selected_row(qapp, temp_database, auto_confirm):
    with open_transactions(1) as (_app, view):
        expected_id = view.proxy_model.source_row_id(0)
        select_proxy_rows(view, [0])
        delete_button(view).click()

        assert pump(5, lambda: len(database.get_all_transactions()) == 0)
        assert pump(5, lambda: view.source_model.rowCount() == 0)
        assert expected_id not in live_ids()


def test_delete_two_selected_rows(qapp, temp_database, auto_confirm):
    with open_transactions(5) as (_app, view):
        expected = {view.proxy_model.source_row_id(row) for row in (0, 1)}
        remaining = live_ids() - expected
        select_proxy_rows(view, [0, 1])
        delete_button(view).click()

        assert pump(5, lambda: live_ids() == remaining)
        assert pump(5, lambda: view.source_model.rowCount() == 3)


def test_delete_many_and_all_rows_with_one_confirmation(
    qapp, temp_database, auto_confirm
):
    with open_transactions(12) as (_app, view):
        expected = {view.proxy_model.source_row_id(row) for row in range(12)}
        select_proxy_rows(view, range(12))
        delete_button(view).click()

        assert pump(5, lambda: len(database.get_all_transactions()) == 0)
        assert pump(5, lambda: view.source_model.rowCount() == 0)
        assert len(auto_confirm) == 1, "confirmation must be asked once for the batch"
        assert "12" in auto_confirm[0]
        assert "Deleted 12 transactions" in view.status_label.text()


def test_delete_works_while_sorted(qapp, temp_database, auto_confirm):
    with open_transactions(6) as (_app, view):
        view.proxy_model.sort(4, Qt.DescendingOrder)
        pump(0.3)
        selected_rows = [0, 1, 2]
        expected = {view.proxy_model.source_row_id(row) for row in selected_rows}
        remaining = live_ids() - expected

        select_proxy_rows(view, selected_rows)
        delete_button(view).click()

        assert pump(5, lambda: live_ids() == remaining)
        assert pump(5, lambda: view.source_model.rowCount() == 3)


def test_delete_works_while_filtered(qapp, temp_database, auto_confirm):
    with open_transactions(5) as (_app, view):
        view.filter_entry.setText("Category2")
        assert pump(0.3, lambda: view.proxy_model.rowCount() == 1)
        expected_id = view.proxy_model.source_row_id(0)
        remaining = live_ids() - {expected_id}

        select_proxy_rows(view, [0])
        delete_button(view).click()

        assert pump(5, lambda: live_ids() == remaining)
        assert pump(5, lambda: view.proxy_model.rowCount() == 0)
        assert pump(5, lambda: view.source_model.rowCount() == 4)


def test_delete_creates_soft_delete_markers_and_sync_tombstones(
    qapp, temp_database, raw_connection, auto_confirm
):
    with open_transactions(3) as (_app, view):
        ids = sorted(live_ids())
        before = {
            row_id: database.get_transaction(row_id)["uuid"] for row_id in ids
        }
        select_proxy_rows(view, [0, 1, 2])
        delete_button(view).click()
        assert pump(5, lambda: len(database.get_all_transactions()) == 0)

        connection = raw_connection(temp_database)
        rows = connection.execute(
            "SELECT * FROM transactions WHERE id IN (?, ?, ?) ORDER BY id", ids
        ).fetchall()
        assert len(rows) == 3
        for row in rows:
            assert row["deleted_at_ms"] is not None
            assert row["revision"] == 2
            assert row["sync_state"] == "pending"

        changes = connection.execute(
            "SELECT * FROM sync_changes WHERE operation = 'delete'"
        ).fetchall()
        assert len(changes) == 3
        payload_uuids = {json.loads(change["payload"])["uuid"] for change in changes}
        assert payload_uuids == set(before.values())


def test_delete_worker_error_is_shown_to_user(
    qapp, temp_database, monkeypatch, auto_confirm
):
    with open_transactions(1) as (_app, view):
        def boom(*_args, **_kwargs):
            raise RuntimeError("disk is full")

        monkeypatch.setattr(database, "delete_transaction", boom)
        select_proxy_rows(view, [0])
        delete_button(view).click()

        assert pump(5, lambda: "disk is full" in (
            view.status_label.text() + view.error_label.text()
        ))


def test_delete_button_disabled_without_selection(
    qapp, temp_database, auto_confirm
):
    with open_transactions(3) as (_app, view):
        button = delete_button(view)
        assert not button.isEnabled()
        select_proxy_rows(view, [0])
        assert button.isEnabled()
        view.table.selectionModel().clearSelection()
        assert not button.isEnabled()


def test_delete_key_uses_same_handler(qapp, temp_database, auto_confirm):
    with open_transactions(2) as (_app, view):
        expected_id = view.proxy_model.source_row_id(0)
        select_proxy_rows(view, [0])
        view.table.setFocus()
        QApplication.sendEvent(
            view.table, QKeyEvent(QEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
        )

        assert pump(5, lambda: expected_id not in live_ids())
        assert len(auto_confirm) == 1


def test_context_menu_delete_uses_same_handler(
    qapp, temp_database, monkeypatch, auto_confirm
):
    with open_transactions(2) as (_app, view):
        expected_id = view.proxy_model.source_row_id(0)
        select_proxy_rows(view, [0])

        class FakeSignal:
            def __init__(self):
                self.slots = []

            def connect(self, slot):
                self.slots.append(slot)

            def trigger(self):
                for slot in self.slots:
                    slot()

        class FakeAction:
            def __init__(self, text):
                self._text = text
                self._enabled = True
                self.triggered = FakeSignal()

            def text(self):
                return self._text

            def setEnabled(self, enabled):
                self._enabled = enabled

        class FakeMenu:
            instances = []

            def __init__(self, parent):
                self._actions = []
                FakeMenu.instances.append(self)

            def addAction(self, text):
                action = FakeAction(text)
                self._actions.append(action)
                return action

            def actions(self):
                return self._actions

            def exec(self, position):
                action = next(a for a in self._actions if "Delete" in a.text())
                action.triggered.trigger()

        # QMenu is a compiled Qt class: patch the module-level name so the view
        # builds a lightweight menu instead of opening a real modal popup.
        monkeypatch.setattr(transactions_module, "QMenu", FakeMenu)
        view.table.customContextMenuRequested.emit(QPoint(0, 0))

        assert pump(5, lambda: expected_id not in live_ids())
        assert FakeMenu.instances and len(auto_confirm) == 1
