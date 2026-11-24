"""Dashboard page: a per-account overview of income, expenses and balance.

Money is never added across accounts, because two different currencies cannot
be meaningfully summed. Each card is populated from SQL aggregates over
``amount_minor`` and formatted with its account's own symbol and precision.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import database
from sync.identity import DEFAULT_ACCOUNT_NAME, DEFAULT_ACCOUNT_UUID
from ui.theme import BadgeLabel, NumberBadge, card, page_header, primary_button
from utils.money import format_money


def _currency_caption(total):
    return (
        f"{total['currency_code']} · "
        f"{int(total['currency_precision'])} decimals"
    )


class DashboardView(QWidget):
    """The first screen the user sees when the app opens."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._prompt_dismissed = False
        self.summary_cards = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(page_header("Dashboard", "A calm overview of your money."))

        self.first_run_banner = self._build_first_run_banner()
        layout.addWidget(self.first_run_banner)
        layout.addWidget(self._build_hero())
        layout.addLayout(self._build_totals_heading())

        self.cards_host = QWidget()
        self.cards_grid = QGridLayout(self.cards_host)
        self.cards_grid.setContentsMargins(0, 0, 0, 0)
        self.cards_grid.setHorizontalSpacing(14)
        self.cards_grid.setVerticalSpacing(14)
        for column in range(3):
            self.cards_grid.setColumnStretch(column, 1)
        layout.addWidget(self.cards_host)

        layout.addLayout(self._build_tips())
        layout.addWidget(self._build_steps(), 1)

        self.refresh()

    # ------------------------------------------------------------- first run
    def _build_first_run_banner(self):
        panel = card()
        row = QHBoxLayout(panel)
        row.setContentsMargins(24, 18, 24, 18)
        row.setSpacing(18)

        text_column = QVBoxLayout()
        text_column.setSpacing(4)
        eyebrow = QLabel("GET STARTED")
        eyebrow.setObjectName("accent")
        title = QLabel("Make the default account yours")
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        body = QLabel(
            "You are using the default INR account. Rename it to match where "
            "your money lives, or add an account in another currency."
        )
        body.setObjectName("subtitle")
        body.setWordWrap(True)
        text_column.addWidget(eyebrow)
        text_column.addWidget(title)
        text_column.addWidget(body)

        buttons = QVBoxLayout()
        buttons.setSpacing(6)
        rename_button = primary_button("Rename it")
        add_button = QPushButton("Add an account")
        dismiss_button = QPushButton("Not now")
        rename_button.clicked.connect(self._prompt_rename)
        add_button.clicked.connect(self._prompt_add)
        dismiss_button.clicked.connect(self._dismiss_first_run)
        buttons.addWidget(rename_button)
        buttons.addWidget(add_button)
        buttons.addWidget(dismiss_button)

        row.addLayout(text_column, 1)
        row.addLayout(buttons)
        return panel

    def _prompt_rename(self):
        page = self.app.show_page("accounts")
        if page is not None:
            page.start_rename(DEFAULT_ACCOUNT_UUID)

    def _prompt_add(self):
        page = self.app.show_page("accounts")
        if page is not None:
            page.focus_create()

    def _dismiss_first_run(self):
        self._prompt_dismissed = True
        self.first_run_banner.hide()

    # ------------------------------------------------------------------ hero
    def _build_hero(self):
        hero = card()
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(28, 24, 28, 24)
        hero_layout.setSpacing(6)
        eyebrow = QLabel("WELCOME BACK")
        eyebrow.setObjectName("accent")
        headline = QLabel("Your money, kept simple.")
        headline.setStyleSheet("font-size: 26px; font-weight: 700;")
        blurb = QLabel(
            "Record income and expenses in a few clicks, in any currency. "
            "Everything is saved in a local file on this computer — no "
            "sign-ups, no cloud."
        )
        blurb.setObjectName("subtitle")
        blurb.setWordWrap(True)
        add_button = primary_button("Add a transaction")
        add_button.clicked.connect(lambda: self.app.show_page("transactions"))
        hero_layout.addWidget(eyebrow)
        hero_layout.addWidget(headline)
        hero_layout.addWidget(blurb)
        hero_layout.addSpacing(8)
        hero_layout.addWidget(add_button, 0, Qt.AlignLeft)
        return hero

    def _build_totals_heading(self):
        row = QHBoxLayout()
        heading = QLabel("Balances by account")
        heading.setStyleSheet("font-size: 15px; font-weight: 700;")
        note = QLabel("Each account is totalled in its own currency; nothing is mixed.")
        note.setObjectName("subtitle")
        self.status_label = QLabel("")
        self.status_label.setObjectName("muted")
        self.status_label.setWordWrap(True)
        row.addWidget(heading)
        row.addSpacing(10)
        row.addWidget(note, 1)
        row.addWidget(self.status_label)
        return row

    def _build_tips(self):
        tips_row = QHBoxLayout()
        tips_row.setSpacing(14)
        for title, body in (
            ("Private by design", "Your transactions never leave this computer."),
            ("Any currency", "Each account keeps its own symbol and decimals."),
            ("Simple on purpose", "No bank links, no clutter, no surprise fees."),
        ):
            tile = card()
            tile_layout = QVBoxLayout(tile)
            tile_layout.setContentsMargins(20, 16, 20, 16)
            heading = QLabel(title)
            heading.setStyleSheet("font-size: 13px; font-weight: 700;")
            text = QLabel(body)
            text.setObjectName("subtitle")
            text.setWordWrap(True)
            tile_layout.addWidget(heading)
            tile_layout.addWidget(text)
            tips_row.addWidget(tile)
        return tips_row

    def _build_steps(self):
        steps = card()
        steps_layout = QVBoxLayout(steps)
        steps_layout.setContentsMargins(24, 16, 24, 16)
        steps_layout.setSpacing(6)
        heading = QLabel("Getting started")
        heading.setStyleSheet("font-size: 14px; font-weight: 700;")
        steps_layout.addWidget(heading)
        for number, text in enumerate(
            (
                "Choose an account on the Transactions page before you add money.",
                "Review, sort and filter everything you have saved in the table.",
                "Rename an account or add another currency from the Accounts page.",
            ),
            start=1,
        ):
            row = QHBoxLayout()
            bullet = NumberBadge(number)
            description = QLabel(text)
            description.setObjectName("subtitle")
            row.addWidget(bullet)
            row.addWidget(description, 1)
            steps_layout.addLayout(row)
        return steps

    # ------------------------------------------------------------------ data
    def refresh(self):
        """Rebuild the per-account cards from SQL minor-unit aggregates."""
        try:
            totals = database.get_account_totals()
        except Exception as error:
            self._render_cards([])
            self.status_label.setText(f"Could not load account totals: {error}")
            self.status_label.setObjectName("statusError")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
            self.first_run_banner.hide()
            return
        self.status_label.setText("")
        self.status_label.setObjectName("muted")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self._render_cards(totals)
        self._sync_first_run(totals)

    def _sync_first_run(self, totals):
        untouched_default = (
            len(totals) == 1
            and totals[0]["account_uuid"] == DEFAULT_ACCOUNT_UUID
            and totals[0]["account_name"] == DEFAULT_ACCOUNT_NAME
            and totals[0]["currency_code"] == "INR"
            and int(totals[0]["transaction_count"]) == 0
        )
        self.first_run_banner.setVisible(
            untouched_default and not self._prompt_dismissed
        )

    def _render_cards(self, totals):
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.summary_cards = {}

        if not totals:
            empty = QLabel("No accounts yet. Add one from the Accounts page.")
            empty.setObjectName("subtitle")
            self.cards_grid.addWidget(empty, 0, 0)
            return

        for index, total in enumerate(totals):
            panel, labels = self._build_account_card(total)
            row, column = divmod(index, 3)
            self.cards_grid.addWidget(panel, row, column)
            self.summary_cards[total["account_uuid"]] = labels

    def _build_account_card(self, total):
        code = total["currency_code"]
        precision = int(total["currency_precision"])

        panel = card()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        top = QHBoxLayout()
        name = QLabel(total["account_name"])
        name.setStyleSheet("font-size: 15px; font-weight: 700;")
        top.addWidget(name, 1)
        if total["is_default"]:
            top.addWidget(BadgeLabel("Default"))
        layout.addLayout(top)

        currency = QLabel(_currency_caption(total))
        currency.setObjectName("muted")
        layout.addWidget(currency)

        labels = {"name": name, "currency": currency, "total": total}

        for key, caption in (
            ("income", "Income"),
            ("expense", "Expenses"),
            ("balance", "Balance"),
        ):
            row = QHBoxLayout()
            label = QLabel(caption)
            label.setObjectName("subtitle")
            value = QLabel(
                format_money(
                    total[f"{key}_minor"],
                    code,
                    precision,
                )
            )
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if key == "balance":
                value.setObjectName("accent")
                value.setStyleSheet("font-weight: 700;")
            elif key == "income":
                value.setObjectName("statusOk")
            row.addWidget(label)
            row.addWidget(value, 1)
            layout.addLayout(row)
            labels[key] = value

        count = int(total["transaction_count"])
        summary = QLabel(
            f"{count} transaction" + ("" if count == 1 else "s")
        )
        summary.setObjectName("muted")
        layout.addWidget(summary)
        labels["count"] = summary

        return panel, labels

    def on_accounts_changed(self):
        self.refresh()
