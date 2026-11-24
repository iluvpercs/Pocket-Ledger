"""Transactions screen: add, view, edit, filter, sort and delete.

The table is a ``QTableView`` backed by a ``QAbstractTableModel`` and a sort /
filter proxy, so only the visible rows are painted even with thousands of
entries. Every database call is handed to ``ui.workers``.
"""

from datetime import date

from PySide6.QtCore import QEvent, QItemSelectionModel, Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QTableView,
    QVBoxLayout,
    QWidget,
)

import database
from ui.models import TransactionProxyModel, TransactionTableModel
from ui.theme import (
    BadgeLabel,
    ConfirmDialog,
    card,
    danger_button,
    field_label,
    page_header,
    primary_button,
    section_title,
    styled_entry,
)
from ui.workers import run_database_task
from utils.money import (
    MoneyError,
    format_money,
    minor_to_decimal,
    normalize_amount_input,
    parse_to_minor,
)


def _load_rows():
    """Read rows and detach them from SQLite before crossing threads."""
    return [dict(row) for row in database.get_all_transactions()]


def _delete_batch(transaction_ids):
    """Soft-delete every id in one SQLite transaction."""
    ids = [int(transaction_id) for transaction_id in transaction_ids]
    with database.atomic_write():
        return sum(
            1 for transaction_id in ids if database.delete_transaction(transaction_id)
        )


def _minor_to_entry_text(amount_minor, precision):
    precision = int(precision)
    value = minor_to_decimal(amount_minor, precision)
    return f"{value:.{precision}f}"


class EditTransactionDialog(QDialog):
    """Small modal form for editing one transaction."""

    def __init__(self, parent, row):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("Edit transaction")
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(10)

        form = QFormLayout()
        self.type_control = QComboBox()
        self.type_control.addItems(["Expense", "Income"])
        self.type_control.setCurrentText(row["transaction_type"].capitalize())

        self.amount_entry = styled_entry("0.00")
        self.amount_entry.setText(
            _minor_to_entry_text(row["amount_minor"], row["currency_precision"])
        )

        self.category_entry = styled_entry("e.g. Food, Rent, Salary")
        self.category_entry.setText(row["category"])
        self.description_entry = styled_entry("Description")
        self.description_entry.setText(row["description"] or "")
        self.date_entry = styled_entry("YYYY-MM-DD")
        self.date_entry.setText(row["transaction_date"])

        account_label = (
            f"{row.get('account_name', 'Account')} · "
            f"{row.get('currency_code', '')} "
            f"({int(row.get('currency_precision', 2))} decimals)"
        )
        account_info = QLabel(account_label)
        account_info.setObjectName("muted")
        account_info.setWordWrap(True)

        form.addRow("Account", account_info)
        form.addRow("Type", self.type_control)
        form.addRow(
            field_label(f"AMOUNT ({row.get('currency_code', 'AMOUNT')})"),
            self.amount_entry,
        )
        form.addRow("Category", self.category_entry)
        form.addRow("Description", self.description_entry)
        form.addRow("Date (YYYY-MM-DD)", self.date_entry)
        layout.addLayout(form)

        note = QLabel(
            "Amount is checked against this account's currency precision. "
            "Transactions stay in the account they were created in."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.error_label = QLabel("")
        self.error_label.setObjectName("statusError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        save = primary_button("Save changes")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._accept_if_valid)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def _accept_if_valid(self):
        try:
            self.amount_minor()
        except (MoneyError, ValueError) as error:
            self.error_label.setText(str(error))
            self.error_label.show()
            self.amount_entry.setFocus()
            return
        self.error_label.hide()
        self.accept()

    def amount_minor(self):
        return parse_to_minor(
            normalize_amount_input(self.amount_entry.text()),
            precision=int(self.row["currency_precision"]),
            strict=True,
        )


class TransactionsView(QWidget):
    """The page where money is added and reviewed."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.accounts = []
        self._loading_accounts = False
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._clear_status)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 24)
        layout.setSpacing(16)
        layout.addWidget(page_header("Transactions", "Record money coming in and going out."))
        layout.addWidget(self._build_form())
        layout.addWidget(self._build_table(), 1)

        self.refresh_accounts()
        self.refresh()

    # ------------------------------------------------------------------ form
    def _build_form(self):
        form = card()
        outer = QVBoxLayout(form)
        outer.setContentsMargins(22, 18, 22, 18)
        outer.setSpacing(12)
        outer.addWidget(
            section_title("ADD TRANSACTION", "Amounts use the selected account's currency.")
        )

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        for column in (0, 1):
            grid.setColumnStretch(column, 1)
            grid.setColumnMinimumWidth(column, 250)

        def labelled(caption, control):
            holder = QWidget()
            column = QVBoxLayout(holder)
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(5)
            label = field_label(caption)
            column.addWidget(label)
            column.addWidget(control)
            return holder, label

        self.account_control = QComboBox()
        self.account_control.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.account_control.setMinimumContentsLength(18)
        self.account_control.currentIndexChanged.connect(self._on_account_changed)
        self.type_control = QComboBox()
        self.type_control.addItems(["Expense", "Income"])
        self.amount_entry = styled_entry("0.00")
        self.category_entry = styled_entry("e.g. Food, Rent, Salary")
        self.description_entry = styled_entry("e.g. Lunch with friends")
        self.date_entry = styled_entry()
        self.date_entry.setText(date.today().isoformat())
        self.amount_hint = QLabel("")
        self.amount_hint.setObjectName("muted")
        self.amount_hint.setWordWrap(True)

        account_field, _ = labelled("ACCOUNT", self.account_control)
        type_field, _ = labelled("TYPE", self.type_control)
        amount_field, self.amount_label = labelled("AMOUNT", self.amount_entry)
        category_field, _ = labelled("CATEGORY", self.category_entry)
        description_field, _ = labelled(
            "DESCRIPTION (OPTIONAL)", self.description_entry
        )
        date_field, _ = labelled("DATE (YYYY-MM-DD)", self.date_entry)

        grid.addWidget(account_field, 0, 0)
        grid.addWidget(type_field, 0, 1)
        grid.addWidget(amount_field, 1, 0)
        grid.addWidget(category_field, 1, 1)
        grid.addWidget(description_field, 2, 0)
        grid.addWidget(date_field, 2, 1)
        grid.addWidget(self.amount_hint, 3, 0, 1, 2)
        outer.addLayout(grid)

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
        outer.addLayout(actions)
        return form

    # ----------------------------------------------------------------- table
    def _build_table(self):
        table_card = card()
        layout = QVBoxLayout(table_card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(section_title("ALL TRANSACTIONS", "Sort and filter everything you have saved."), 1)
        self.count_label = BadgeLabel("")
        self.count_label.setObjectName("badge")
        top.addWidget(self.count_label)
        layout.addLayout(top)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.account_filter = QComboBox()
        self.account_filter.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.account_filter.setMinimumContentsLength(14)
        self.account_filter.setMinimumWidth(180)
        self.account_filter.currentIndexChanged.connect(self._on_filter_changed)
        self.filter_entry = styled_entry("Filter date, type, account, category, description…")
        controls.addWidget(self.account_filter)
        controls.addWidget(self.filter_entry, 2)
        layout.addLayout(controls)

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
        self.table.setMinimumHeight(230)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.doubleClicked.connect(self._on_edit)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.installEventFilter(self)
        self.table.selectionModel().selectionChanged.connect(self._update_action_state)
        self.filter_entry.textChanged.connect(self.proxy_model.set_filter_text)
        layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        self.edit_button = QPushButton("Edit selected")
        self.delete_button = danger_button("Delete selected")
        self.delete_button.setEnabled(False)
        self.edit_button.clicked.connect(lambda: self._on_edit())
        self.delete_button.clicked.connect(lambda _checked=False: self._confirm_delete())
        actions.addWidget(self.edit_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return table_card

    # ----------------------------------------------------------- account data
    def refresh_accounts(self):
        self.accounts = database.list_accounts()
        selected_add = self.account_control.currentData()
        selected_filter = self.account_filter.currentData() if hasattr(self, "account_filter") else None

        self._loading_accounts = True
        try:
            self.account_control.clear()
            self.account_filter.clear()
            self.account_filter.addItem("All accounts", None)
            for account in self.accounts:
                label = f"{account['name']} · {account['currency_code']}"
                self.account_control.addItem(label, account["uuid"])
                self.account_filter.addItem(label, account["uuid"])

            default = next((a for a in self.accounts if a["is_default"]), self.accounts[0] if self.accounts else None)
            if default is not None:
                add_index = self.account_control.findData(
                    selected_add if selected_add else default["uuid"]
                )
                self.account_control.setCurrentIndex(add_index if add_index >= 0 else 0)

            filter_index = self.account_filter.findData(selected_filter)
            self.account_filter.setCurrentIndex(filter_index if filter_index >= 0 else 0)
        finally:
            self._loading_accounts = False

        self._on_account_changed()
        self._on_filter_changed()

    def selected_account(self):
        account_uuid = self.account_control.currentData()
        for account in self.accounts:
            if account["uuid"] == account_uuid:
                return account
        return self.accounts[0] if self.accounts else None

    def _on_account_changed(self, _index=None):
        account = self.selected_account()
        if account is None:
            self.amount_label.setText("AMOUNT")
            self.amount_hint.setText("No account available")
            return
        code = account["currency_code"]
        precision = int(account["currency_precision"])
        noun = "decimal" if precision == 1 else "decimals"
        self.amount_label.setText(f"AMOUNT ({code})")
        self.amount_hint.setText(
            f"Enter up to {precision} {noun} for {code}. "
            "Grouping commas are accepted; too many decimals are rejected."
        )

    def _on_filter_changed(self, _index=None):
        if self._loading_accounts:
            return
        account_uuid = self.account_filter.currentData()
        self.proxy_model.set_account_filter(account_uuid)
        self._update_action_state()

    def on_accounts_changed(self):
        self.refresh_accounts()
        self.refresh()

    def on_data_changed(self):
        self.refresh()

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
        deleted = getattr(self, "_pending_deleted_ids", None)
        if deleted is not None:
            self._select_first_visible_not(deleted)
            self._pending_deleted_ids = None
        else:
            self._update_action_state()
        if count == 0 and deleted is None:
            self._set_status("No transactions yet. Add your first one above.", "info")

    # -------------------------------------------------------------- actions
    def _on_add(self):
        account = self.selected_account()
        if account is None:
            self._set_status("Create an account before adding transactions.", "error")
            return

        transaction_type = self.type_control.currentText().lower()
        amount_text = normalize_amount_input(self.amount_entry.text())
        category = self.category_entry.text().strip()
        description = self.description_entry.text().strip()
        transaction_date = self.date_entry.text().strip()

        try:
            amount_minor = parse_to_minor(
                amount_text,
                precision=int(account["currency_precision"]),
                strict=True,
            )
        except (MoneyError, ValueError) as error:
            self._set_status(str(error), "error")
            self.amount_entry.setFocus()
            return

        def saved(_new_id):
            self.amount_entry.clear()
            self.category_entry.clear()
            self.description_entry.clear()
            self.date_entry.setText(date.today().isoformat())
            self.refresh()
            self.app.notify_data_changed(source=self)
            self._set_status(
                f"{transaction_type.capitalize()} of "
                f"{format_money(amount_minor, account['currency_code'], int(account['currency_precision']))} added.",
                "success",
            )
            self.amount_entry.setFocus()

        run_database_task(
            self,
            database.add_transaction,
            transaction_type,
            amount_text,
            category,
            description,
            transaction_date,
            account_uuid=account["uuid"],
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

    def _selected_ids(self):
        ids = []
        seen = set()
        for index in self.table.selectionModel().selectedRows(0):
            source = self.proxy_model.mapToSource(index)
            if not source.isValid():
                continue
            row_id = self.source_model.row_id(source.row())
            if row_id is not None and row_id not in seen:
                seen.add(row_id)
                ids.append(row_id)
        return ids

    def _update_action_state(self):
        has_selection = bool(self._selected_ids())
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def _select_first_visible_not(self, exclude_ids):
        selection = self.table.selectionModel()
        selection.clearSelection()
        for row in range(self.proxy_model.rowCount()):
            if self.proxy_model.source_row_id(row) in exclude_ids:
                continue
            index = self.proxy_model.index(row, 0)
            selection.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
            self.table.setCurrentIndex(index)
            break
        self._update_action_state()

    def eventFilter(self, watched, event):
        if watched is self.table and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
                self._confirm_delete()
                return True
        return super().eventFilter(watched, event)

    def _show_context_menu(self, position):
        menu = QMenu(self.table)
        action = menu.addAction("Delete selected")
        action.setEnabled(bool(self._selected_ids()))
        action.triggered.connect(self._confirm_delete)
        menu.exec(self.table.viewport().mapToGlobal(position))

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
            amount=_minor_to_entry_text(dialog.amount_minor(), row["currency_precision"]),
            category=dialog.category_entry.text().strip(),
            description=dialog.description_entry.text().strip(),
            transaction_date=dialog.date_entry.text().strip(),
        )

        def updated(ok):
            self.refresh()
            self.app.notify_data_changed(source=self)
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
        ids = self._selected_ids()
        if not ids:
            self._set_status("Select a transaction to delete.", "error")
            return

        count = len(ids)
        noun = "transaction" if count == 1 else "transactions"
        title = f"Delete {count} {noun}?"
        ConfirmDialog(
            self,
            title,
            f"{title}\n\nThis cannot be undone.",
            on_confirm=lambda: self._delete(ids),
        )

    def _delete(self, transaction_ids):
        ids = list(transaction_ids)

        def deleted(deleted_count):
            self._pending_deleted_ids = set(ids)
            self.refresh()
            self.app.notify_data_changed(source=self)
            noun = "transaction" if deleted_count == 1 else "transactions"
            self._set_status(f"Deleted {deleted_count} {noun}.")

        def failed(message):
            text = f"Could not delete: {message}"
            self._show_error(text)
            self._set_status(text, "error")

        run_database_task(
            self,
            _delete_batch,
            ids,
            on_success=deleted,
            on_error=failed,
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
