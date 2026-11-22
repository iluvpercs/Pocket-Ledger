"""Transactions screen: add, view, edit, filter, sort and delete.

The table is a ``QTableView`` backed by a ``QAbstractTableModel`` and a sort /
filter proxy, so only the visible rows are painted even with thousands of
entries. Every database call is handed to ``ui.workers``.
"""

import sqlite3
from datetime import date

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

import database
from ui.models import TransactionProxyModel, TransactionTableModel
from ui.theme import (
    COLORS,
    ConfirmDialog,
    card,
    danger_button,
    field_label,
    page_header,
    primary_button,
    styled_entry,
)
from ui.workers import run_database_task
from utils.formatting import format_inr, format_transaction_date


def _load_rows():
    """Read rows and detach them from SQLite before crossing threads."""
    return [dict(row) for row in database.get_all_transactions()]


class EditTransactionDialog(QDialog):
    """Small modal form for editing one transaction."""

    def __init__(self, parent, row):
        super().__init__(parent)
        self.setWindowTitle("Edit transaction")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(10)

        form = QFormLayout()
        self.type_control = QComboBox()
        self.type_control.addItems(["Expense", "Income"])
        self.type_control.setCurrentText(row["transaction_type"].capitalize())
        self.amount_entry = styled_entry("0.00")
        self.amount_entry.setText(str(row["amount"]))
        self.category_entry = styled_entry("e.g. Food, Rent, Salary")
        self.category_entry.setText(row["category"])
        self.description_entry = styled_entry("Description")
        self.description_entry.setText(row["description"] or "")
        self.date_entry = styled_entry("YYYY-MM-DD")
        self.date_entry.setText(row["transaction_date"])

        form.addRow("Type", self.type_control)
        form.addRow("Amount (₹)", self.amount_entry)
        form.addRow("Category", self.category_entry)
        form.addRow("Description", self.description_entry)
        form.addRow("Date (YYYY-MM-DD)", self.date_entry)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        save = primary_button("Save changes")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)


class TransactionsView(QWidget):
    """The page where money is added and reviewed."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._clear_status)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(page_header("Transactions", "Record money coming in and going out."))
        layout.addWidget(self._build_form())
        layout.addWidget(self._build_table(), 1)

        self.refresh()

    # ------------------------------------------------------------------ form
    def _build_form(self):
        form = card()
        grid = QFormLayout(form)
        grid.setContentsMargins(24, 16, 24, 14)
        grid.setLabelAlignment(Qt.AlignLeft)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(6)

        self.type_control = QComboBox()
        self.type_control.addItems(["Expense", "Income"])
        self.amount_entry = styled_entry("0.00")
        self.category_entry = styled_entry("e.g. Food, Rent, Salary")
        self.description_entry = styled_entry("e.g. Lunch with friends")
        self.date_entry = styled_entry()
        self.date_entry.setText(date.today().isoformat())

        grid.addRow(field_label("TYPE"), self.type_control)
        grid.addRow(field_label("AMOUNT (₹)"), self.amount_entry)
        grid.addRow(field_label("CATEGORY"), self.category_entry)
        grid.addRow(field_label("DESCRIPTION (OPTIONAL)"), self.description_entry)
        grid.addRow(field_label("DATE (YYYY-MM-DD)"), self.date_entry)

        actions = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusOk")
        self.status_label.setWordWrap(True)
        add_button = primary_button("Add transaction")
        add_button.clicked.connect(self._on_add)
        for entry in (
            self.amount_entry,
            self.category_entry,
            self.description_entry,
            self.date_entry,
        ):
            entry.returnPressed.connect(self._on_add)
        actions.addWidget(self.status_label, 1)
        actions.addWidget(add_button)
        grid.addRow("", actions)
        return form

    # ----------------------------------------------------------------- table
    def _build_table(self):
        table_card = card()
        layout = QVBoxLayout(table_card)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(10)

        top = QHBoxLayout()
        heading = QLabel("Saved transactions")
        heading.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.count_label = QLabel("")
        self.count_label.setObjectName("badge")
        self.filter_entry = styled_entry("Filter date, type, category, description…")
        top.addWidget(heading)
        top.addWidget(self.count_label)
        top.addStretch(1)
        top.addWidget(self.filter_entry, 2)
        layout.addLayout(top)

        self.error_label = QLabel("")
        self.error_label.setObjectName("statusError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        self.source_model = TransactionTableModel()
        self.proxy_model = TransactionProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.sort(0, Qt.DescendingOrder)

        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.doubleClicked.connect(self._on_edit)
        self.filter_entry.textChanged.connect(self.proxy_model.set_filter_text)
        layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        edit_button = QPushButton("Edit selected")
        delete_button = danger_button("Delete selected")
        edit_button.clicked.connect(self._on_edit)
        delete_button.clicked.connect(self._confirm_delete)
        actions.addWidget(edit_button)
        actions.addWidget(delete_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return table_card

    # ------------------------------------------------------------------ data
    def refresh(self):
        """Reload the table in a worker so the window stays responsive."""
        run_database_task(
            self,
            _load_rows,
            on_success=self._apply_rows,
            on_error=lambda message: self._show_error(f"Could not load transactions: {message}"),
        )

    def _apply_rows(self, rows):
        self._hide_error()
        self.source_model.set_rows(rows)
        count = len(rows)
        self.count_label.setText(f"{count} entr{'y' if count == 1 else 'ies'}")
        if count == 0:
            self._set_status("No transactions yet. Add your first one above.", "info")

    # -------------------------------------------------------------- actions
    def _on_add(self):
        transaction_type = self.type_control.currentText().lower()
        amount = self.amount_entry.text().strip()
        category = self.category_entry.text().strip()
        description = self.description_entry.text().strip()
        transaction_date = self.date_entry.text().strip()

        def saved(new_id):
            self.amount_entry.clear()
            self.category_entry.clear()
            self.description_entry.clear()
            self.date_entry.setText(date.today().isoformat())
            self.refresh()
            self._set_status(
                f"{transaction_type.capitalize()} of {format_inr(amount)} added.",
                "success",
            )
            self.amount_entry.setFocus()

        run_database_task(
            self,
            database.add_transaction,
            transaction_type,
            amount,
            category,
            description,
            transaction_date,
            on_success=saved,
            on_error=lambda message: (
                self._set_status(message, "error"),
                self._focus_problem_field(message),
            ),
        )

    def _selected_row(self):
        index = self.table.currentIndex()
        if not index.isValid():
            return None
        return self.proxy_model.source_row_dict(index.row())

    def _on_edit(self):
        row = self._selected_row()
        if row is None:
            self._set_status("Select a transaction to edit.", "error")
            return

        dialog = EditTransactionDialog(self, row)
        if dialog.exec() != QDialog.Accepted:
            return

        transaction_id = row["id"]
        changes = dict(
            transaction_type=dialog.type_control.currentText().lower(),
            amount=dialog.amount_entry.text().strip(),
            category=dialog.category_entry.text().strip(),
            description=dialog.description_entry.text().strip(),
            transaction_date=dialog.date_entry.text().strip(),
        )

        def updated(ok):
            self.refresh()
            self._set_status(
                "Transaction updated." if ok else "That transaction was already removed.",
                "success" if ok else "error",
            )

        run_database_task(
            self,
            database.update_transaction,
            transaction_id,
            **changes,
            on_success=updated,
            on_error=lambda message: self._set_status(message, "error"),
        )

    def _confirm_delete(self):
        row = self._selected_row()
        if row is None:
            self._set_status("Select a transaction to delete.", "error")
            return

        details = (
            f"{row['transaction_type'].capitalize()} · "
            f"{format_inr(row['amount'])} · {row['category']}\n"
            f"{format_transaction_date(row['transaction_date'])}"
        )
        if row["description"]:
            details += f"\n{row['description']}"
        ConfirmDialog(
            self,
            "Delete this transaction?",
            f"{details}\n\nThis cannot be undone.",
            on_confirm=lambda: self._delete(row["id"]),
        )

    def _delete(self, transaction_id):
        def deleted(ok):
            self.refresh()
            self._set_status(
                "Transaction deleted." if ok else "That transaction was already removed.",
                "success" if ok else "error",
            )

        run_database_task(
            self,
            database.delete_transaction,
            transaction_id,
            on_success=deleted,
            on_error=lambda message: self._set_status(f"Could not delete: {message}", "error"),
        )

    # --------------------------------------------------------------- helpers
    def _set_status(self, message, kind="success"):
        self.status_label.setText(message)
        self.status_label.setObjectName("statusOk" if kind == "success" else "statusError")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self._status_timer.start(5000)

    def _clear_status(self):
        self.status_label.setText("")

    def _focus_problem_field(self, message):
        if message.startswith("Amount"):
            self.amount_entry.setFocus()
        elif message.startswith("Category"):
            self.category_entry.setFocus()
        elif message.startswith("Date"):
            self.date_entry.setFocus()

    def _show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()

    def _hide_error(self):
        self.error_label.hide()
        self.error_label.clear()
