"""Accounts page: list, create, rename, set default and delete accounts.

The currency of an account is chosen once at creation. Everything stored in
that account is an integer count of that currency's minor unit, so changing the
currency later would silently reinterpret every existing amount. The page says
so in plain language instead of offering an edit control that cannot work.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database
from ui.theme import (
    BadgeLabel,
    ConfirmDialog,
    card,
    danger_button,
    field_label,
    page_header,
    primary_button,
    styled_entry,
)
from utils.currencies import (
    CURRENCY_PRECISION,
    SUPPORTED_PRECISIONS,
    CurrencyError,
    get_precision,
)

SUPPORTED_CODES = sorted(
    code
    for code, precision in CURRENCY_PRECISION.items()
    if precision in SUPPORTED_PRECISIONS
)


def currency_label(code, precision=None):
    """Return a searchable picker label such as ``USD · 2 decimals``."""
    if precision is None:
        precision = CURRENCY_PRECISION.get(code, get_precision(code))
    noun = "decimal" if int(precision) == 1 else "decimals"
    return f"{code} · {int(precision)} {noun}"


class AccountsView(QWidget):
    """Manage the accounts that transactions can belong to."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._accounts = []
        self._loading = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(
            page_header(
                "Accounts",
                "Each account keeps its own currency. Totals are never mixed.",
            )
        )
        layout.addWidget(self._build_create_card())
        layout.addWidget(self._build_table_card(), 1)

        self.refresh()

    # ------------------------------------------------------------------ build
    def _build_create_card(self):
        panel = card()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(10)

        heading = QLabel("Add an account")
        heading.setStyleSheet("font-size: 14px; font-weight: 700;")
        layout.addWidget(heading)

        fields = QHBoxLayout()
        fields.setSpacing(12)
        name_column = QVBoxLayout()
        name_column.setSpacing(4)
        self.name_entry = styled_entry("e.g. Travel wallet")
        name_column.addWidget(field_label("ACCOUNT NAME"))
        name_column.addWidget(self.name_entry)

        currency_column = QVBoxLayout()
        currency_column.setSpacing(4)
        self.currency_combo = QComboBox()
        self.currency_combo.setEditable(True)
        self.currency_combo.setInsertPolicy(QComboBox.NoInsert)
        for code in SUPPORTED_CODES:
            precision = CURRENCY_PRECISION[code]
            self.currency_combo.addItem(currency_label(code, precision), code)
        completer = QCompleter(
            [self.currency_combo.itemText(i) for i in range(self.currency_combo.count())],
            self.currency_combo,
        )
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.currency_combo.setCompleter(completer)
        self.currency_combo.setCurrentIndex(
            self.currency_combo.findData("INR")
        )
        currency_column.addWidget(field_label("CURRENCY (SEARCHABLE)"))
        currency_column.addWidget(self.currency_combo)

        self.add_button = primary_button("Add account")
        self.add_button.clicked.connect(self._create_account)

        fields.addLayout(name_column, 3)
        fields.addLayout(currency_column, 2)
        fields.addWidget(self.add_button, 0, Qt.AlignBottom)
        layout.addLayout(fields)

        note = QLabel(
            "An account's currency is fixed after creation, because every saved "
            "amount is stored in that currency's smallest unit. Create a new "
            "account to use another currency."
        )
        note.setObjectName("subtitle")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusOk")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        return panel

    def _build_table_card(self):
        panel = card()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(10)

        top = QHBoxLayout()
        heading = QLabel("Your accounts")
        heading.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.count_label = BadgeLabel("")
        self.count_label.setObjectName("badge")
        top.addWidget(heading)
        top.addWidget(self.count_label)
        top.addStretch(1)
        layout.addLayout(top)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ("ACCOUNT", "CURRENCY", "TRANSACTIONS", "DEFAULT")
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        self.rename_button = QPushButton("Rename selected")
        self.default_button = QPushButton("Make default")
        self.delete_button = danger_button("Delete selected")
        self.rename_button.clicked.connect(self._rename_selected)
        self.default_button.clicked.connect(self._make_default)
        self.delete_button.clicked.connect(self._confirm_delete)
        actions.addWidget(self.rename_button)
        actions.addWidget(self.default_button)
        actions.addWidget(self.delete_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self._update_buttons()
        return panel

    # ------------------------------------------------------------------ data
    def refresh(self):
        """Reload accounts and their live transaction counts."""
        self._accounts = database.list_accounts()
        counts = {
            row["account_uuid"]: int(row["transaction_count"])
            for row in database.get_account_totals()
        }
        selected = self.selected_account_uuid()

        self._loading = True
        try:
            self.table.setRowCount(len(self._accounts))
            for row_index, account in enumerate(self._accounts):
                name_item = QTableWidgetItem(account["name"])
                name_item.setData(Qt.UserRole, account["uuid"])
                currency_item = QTableWidgetItem(
                    currency_label(
                        account["currency_code"],
                        int(account["currency_precision"]),
                    )
                )
                count_item = QTableWidgetItem(
                    str(counts.get(account["uuid"], 0))
                )
                count_item.setTextAlignment(Qt.AlignCenter)
                default_item = QTableWidgetItem(
                    "Yes" if account["is_default"] else "—"
                )
                default_item.setTextAlignment(Qt.AlignCenter)
                for column, item in enumerate(
                    (name_item, currency_item, count_item, default_item)
                ):
                    self.table.setItem(row_index, column, item)
        finally:
            self._loading = False

        self.count_label.setText(
            f"{len(self._accounts)} account"
            + ("" if len(self._accounts) == 1 else "s")
        )
        self._select_account(selected)
        self._update_buttons()

    def selected_account_uuid(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item is not None else None

    def _account(self, account_uuid):
        for account in self._accounts:
            if account["uuid"] == account_uuid:
                return account
        return None

    def _select_account(self, account_uuid):
        if account_uuid is None:
            return
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None and item.data(Qt.UserRole) == account_uuid:
                self.table.selectRow(row)
                return

    def _update_buttons(self):
        has_selection = self.selected_account_uuid() is not None
        self.rename_button.setEnabled(has_selection)
        self.default_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    # --------------------------------------------------------------- actions
    def _selected_currency_code(self):
        code = self.currency_combo.currentData()
        if code:
            return str(code)
        text = self.currency_combo.currentText().split("·")[0].strip().upper()
        return text

    def _create_account(self):
        name = self.name_entry.text().strip()
        code = self._selected_currency_code()
        try:
            get_precision(code)  # reject unknown codes before touching SQLite
            account_uuid = database.create_account(name, code)
        except (CurrencyError, ValueError) as error:
            self._set_status(str(error), "error")
            return
        self.name_entry.clear()
        self.refresh()
        self._select_account(account_uuid)
        self._set_status(
            f"Account created in {code}.", "success"
        )
        self.app.notify_accounts_changed()

    def _rename_selected(self):
        account_uuid = self.selected_account_uuid()
        account = self._account(account_uuid)
        if account is None:
            self._set_status("Select an account to rename.", "error")
            return
        name, accepted = QInputDialog.getText(
            self, "Rename account", "Account name", text=account["name"]
        )
        if not accepted:
            return
        name = name.strip()
        if not name:
            self._set_status("Account name cannot be empty.", "error")
            return
        try:
            database.rename_account(account_uuid, name)
        except ValueError as error:
            self._set_status(str(error), "error")
            return
        self.refresh()
        self._select_account(account_uuid)
        self._set_status("Account renamed.", "success")
        self.app.notify_accounts_changed()

    def _make_default(self):
        account_uuid = self.selected_account_uuid()
        account = self._account(account_uuid)
        if account is None:
            self._set_status("Select an account first.", "error")
            return
        if account["is_default"]:
            self._set_status(
                f"{account['name']} is already the default account.", "info"
            )
            return
        try:
            database.update_account(account_uuid, is_default=True)
        except ValueError as error:
            self._set_status(str(error), "error")
            return
        self.refresh()
        self._select_account(account_uuid)
        self._set_status(
            f"{account['name']} is now the default account.", "success"
        )
        self.app.notify_accounts_changed()

    def _transaction_count(self, account_uuid):
        """Return the live transaction count for an account, or 0 if unknown."""
        for row in database.get_account_totals():
            if row["account_uuid"] == account_uuid:
                return int(row["transaction_count"])
        return 0

    def _confirm_delete(self):
        account_uuid = self.selected_account_uuid()
        account = self._account(account_uuid)
        if account is None:
            self._set_status("Select an account to delete.", "error")
            return

        name = str(account["name"])
        live_accounts = [
            row for row in database.list_accounts() if row.get("deleted_at_ms") is None
        ]
        if len(live_accounts) <= 1:
            self._set_status(
                f"'{name}' cannot be deleted because it is the only remaining account. "
                "At least one account must remain.",
                "error",
            )
            return

        tx_count = self._transaction_count(account_uuid)
        if tx_count > 0:
            noun = "transaction" if tx_count == 1 else "transactions"
            self._set_status(
                f"'{name}' cannot be deleted while it contains {tx_count} {noun}. "
                "Delete or move those transactions first.",
                "error",
            )
            return

        ConfirmDialog(
            self,
            f"Delete {name}?",
            f"'{name}' has no transactions and can be deleted. "
            "This removes the account from your account list. "
            "Transactions are never deleted along with an account.",
            confirm_text="Delete account",
            on_confirm=lambda: self._delete_account(account_uuid, name),
        )

    def _delete_account(self, account_uuid, account_name=None):
        name = account_name or "Account"
        try:
            database.delete_account(account_uuid)
        except ValueError as error:
            self._set_status(str(error), "error")
            return
        except Exception:
            self._set_status(
                f"Could not delete '{name}' due to an unexpected error. "
                "Please try again.",
                "error",
            )
            return
        self.refresh()
        self._set_status(f"Account '{name}' deleted.", "success")
        self.app.notify_accounts_changed()

    # -------------------------------------------------------- first-run hooks
    def start_rename(self, account_uuid):
        """Select an account and open the rename dialog (used by the prompt)."""
        self.refresh()
        self._select_account(account_uuid)
        self._rename_selected()

    def focus_create(self):
        """Put the cursor in the new-account name field."""
        self.name_entry.setFocus()

    def on_accounts_changed(self):
        self.refresh()

    # --------------------------------------------------------------- helpers
    def _set_status(self, message, kind="success"):
        self.status_label.setText(message)
        self.status_label.setObjectName(
            "statusOk" if kind == "success" else
            ("muted" if kind == "info" else "statusError")
        )
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
