"""Dashboard page: a colour-blocked, database-backed money overview.

The headline figures are scoped to one currency (or one account) at a time, so
two different currencies are never added together. Every amount displayed here
comes from ``database.get_account_totals()`` or ``database.get_all_transactions()``
and is formatted with the owning account's precision. The illustrative numbers
from the design brief are deliberately absent: nothing is fabricated.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database
from sync.identity import DEFAULT_ACCOUNT_NAME, DEFAULT_ACCOUNT_UUID
from ui.theme import (
    BadgeLabel,
    IconBadge,
    LIME,
    MetricCard,
    VIOLET,
    WHITE,
    card,
    empty_state,
    feature_panel,
    lime_button,
    page_header,
    primary_button,
    section_title,
)
from utils.formatting import format_signed_minor
from utils.money import format_money


PERIODS = (
    ("month", "This month"),
    ("last_month", "Last month"),
    ("three_months", "Last 3 months"),
    ("year", "This year"),
    ("all", "All time"),
    ("custom", "Custom range"),
)

MONTH_NAMES = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def _row_date(row):
    """Parse an ISO transaction date, returning None when it is unusable."""
    try:
        return date.fromisoformat(str(row.get("transaction_date", ""))[:10])
    except (TypeError, ValueError):
        return None


def _period_bounds(key, start=None, end=None):
    """Return inclusive date bounds and a human label for a filter choice."""
    today = date.today()
    first_this_month = today.replace(day=1)
    if key == "last_month":
        last_month_end = first_this_month - timedelta(days=1)
        return last_month_end.replace(day=1), last_month_end, "Last month"
    if key == "three_months":
        first = first_this_month
        for _ in range(2):
            first = (first - timedelta(days=1)).replace(day=1)
        return first, today, "Last 3 months"
    if key == "year":
        return today.replace(month=1, day=1), today, "This year"
    if key == "all":
        return None, None, "All time"
    if key == "custom":
        return start, end, "Custom range"
    return first_this_month, today, "This month"


def _within_period(row, start, end):
    when = _row_date(row)
    if when is None:
        # An unparseable date can only be included when no window is active.
        return start is None and end is None
    if start is not None and when < start:
        return False
    if end is not None and when > end:
        return False
    return True


def _scope_key(scope):
    if not scope:
        return "none"
    if scope.get("kind") == "account":
        return f"account:{scope.get('value')}"
    if scope.get("kind") == "currency":
        return f"currency:{scope.get('code')}:{scope.get('precision')}"
    return "none"


def _account_in_scope(account, scope):
    if not scope:
        return False
    if scope.get("kind") == "account":
        return account.get("account_uuid") == scope.get("value")
    if scope.get("kind") == "currency":
        return (
            account.get("currency_code") == scope.get("code")
            and int(account.get("currency_precision", 0)) == int(scope.get("precision", 0))
        )
    return False


def _row_in_scope(row, scope):
    if not scope:
        return False
    if scope.get("kind") == "account":
        return row.get("account_uuid") == scope.get("value")
    if scope.get("kind") == "currency":
        return (
            row.get("currency_code") == scope.get("code")
            and int(row.get("currency_precision", 0)) == int(scope.get("precision", 0))
        )
    return False


def _month_keys(period, start, end, rows):
    """Month keys to chart, newest last."""
    today = date.today()
    if period == "last_month":
        anchor = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        return [f"{anchor.year:04d}-{anchor.month:02d}"]
    if period == "year":
        anchor = today.replace(month=1, day=1)
        return [f"{anchor.year:04d}-{month:02d}" for month in range(1, today.month + 1)]
    if period in ("month", "custom"):
        anchor = end or today
        return [f"{anchor.year:04d}-{anchor.month:02d}"]
    # All time: the six months ending with the newest usable transaction.
    candidates = [_row_date(row) for row in rows]
    candidates = [item for item in candidates if item is not None]
    anchor = max(candidates) if candidates else today
    keys = []
    for offset in range(5, -1, -1):
        first = (anchor.replace(day=1) - timedelta(days=1)).replace(day=1)
        for _ in range(offset - 1 if offset else 0):
            first = (first - timedelta(days=1)).replace(day=1)
        target = anchor if offset == 0 else first
        keys.append(f"{target.year:04d}-{target.month:02d}")
    return keys


def _month_label(key):
    try:
        year, month = (int(part) for part in key.split("-"))
        return f"{MONTH_NAMES[month - 1]} '{str(year)[2:]}"
    except (ValueError, IndexError):
        return str(key)


class MonthlyActivityChart(QWidget):
    """A dependency-free grouped bar chart for monthly income and expenses."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.months = []
        self.income = []
        self.expense = []
        self.currency_code = ""
        self.setObjectName("activityChart")
        self.setMinimumHeight(210)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

    def set_data(self, months, income, expense, currency_code=""):
        self.months = list(months)
        self.income = [int(value) for value in income]
        self.expense = [int(value) for value in expense]
        self.currency_code = str(currency_code or "")
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        area = self.contentsRect()
        if area.width() < 80 or area.height() < 80:
            return

        grid_colour = QColor(WHITE)
        grid_colour.setAlpha(46)
        painter.setPen(QPen(grid_colour))
        baseline = area.bottom() - 26
        top = area.top() + 10
        plot_height = max(1, baseline - top)
        for step in range(4):
            y = top + int(plot_height * step / 3)
            painter.drawLine(area.left(), y, area.right(), y)

        values = self.income + self.expense
        peak = max(values) if values else 0
        if peak <= 0:
            painter.setPen(QColor(WHITE))
            painter.drawText(area, Qt.AlignCenter, "No activity in this period.")
            return

        count = max(1, len(self.months))
        slot = area.width() / count
        bar_width = max(8, min(20, int(slot / 3.2)))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        for index, month in enumerate(self.months):
            centre = area.left() + int(slot * (index + 0.5))
            income_height = int(self.income[index] / peak * plot_height)
            expense_height = int(self.expense[index] / peak * plot_height)
            painter.fillRect(
                centre - bar_width - 2, baseline - income_height,
                bar_width, income_height, QColor(VIOLET),
            )
            painter.fillRect(
                centre + 2, baseline - expense_height,
                bar_width, expense_height, QColor(LIME),
            )
            painter.setPen(QColor(WHITE))
            label_area = self._label_rect(area, centre, slot)
            painter.drawText(label_area, Qt.AlignHCenter | Qt.AlignTop, _month_label(month))

    @staticmethod
    def _label_rect(area, centre, slot):
        from PySide6.QtCore import QRect

        width = max(48, int(slot))
        return QRect(centre - width // 2, area.bottom() - 22, width, 20)


class DashboardView(QWidget):
    """The first screen the user sees when the app opens."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._prompt_dismissed = False
        self.summary_cards = {}
        self.kpi_cards = {}
        self._totals = []
        self._rows = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        self.scroll_area.setWidget(content)
        outer.addWidget(self.scroll_area)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(26, 22, 26, 26)
        layout.setSpacing(18)
        layout.addWidget(self._build_brand_header())
        layout.addWidget(page_header("Dashboard", "Your money. Your control."))
        self.first_run_banner = self._build_first_run_banner()
        layout.addWidget(self.first_run_banner)
        layout.addWidget(self._build_kpis())
        layout.addWidget(self._build_insights())
        layout.addWidget(self._build_accounts_section(), 1)

        self.refresh()

    # ----------------------------------------------------------- page header
    def _build_brand_header(self):
        panel = QWidget()
        row = QHBoxLayout(panel)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(16)

        row.addWidget(IconBadge("PL", size=52))
        names = QVBoxLayout()
        names.setSpacing(2)
        wordmark = QLabel("POCKET LEDGER")
        wordmark.setStyleSheet("font-size: 24px; font-weight: 800; letter-spacing: 2px;")
        tagline = QLabel("YOUR MONEY. YOUR CONTROL.")
        tagline.setObjectName("eyebrow")
        names.addWidget(wordmark)
        names.addWidget(tagline)
        row.addLayout(names)

        spacing = QFrame()
        spacing.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row.addWidget(spacing)

        filters = QVBoxLayout()
        filters.setSpacing(5)
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        self.scope_combo = QComboBox()
        self.scope_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.scope_combo.setMinimumContentsLength(10)
        self.scope_combo.setMinimumWidth(190)
        self.scope_combo.currentIndexChanged.connect(self._render_insights)
        self.period_combo = QComboBox()
        for key, label in PERIODS:
            self.period_combo.addItem(label, key)
        self.period_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_row.addWidget(QLabel("VIEW"))
        filter_row.addWidget(self.scope_combo, 1)
        filter_row.addWidget(self.period_combo)
        filters.addLayout(filter_row)

        self.custom_dates = QWidget()
        date_row = QHBoxLayout(self.custom_dates)
        date_row.setContentsMargins(0, 0, 0, 0)
        date_row.setSpacing(8)
        self.start_date = QDateEdit()
        self.end_date = QDateEdit()
        for control in (self.start_date, self.end_date):
            control.setCalendarPopup(True)
            control.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QtCoreDateToday().addMonths(-1))
        self.end_date.setDate(QtCoreDateToday())
        self.start_date.dateChanged.connect(self._render_insights)
        self.end_date.dateChanged.connect(self._render_insights)
        date_row.addWidget(QLabel("FROM"))
        date_row.addWidget(self.start_date)
        date_row.addWidget(QLabel("TO"))
        date_row.addWidget(self.end_date)
        self.custom_dates.hide()
        filters.addWidget(self.custom_dates)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusError")
        self.status_label.setWordWrap(True)
        filters.addWidget(self.status_label)
        row.addLayout(filters, 1)
        return panel

    # ------------------------------------------------------------- first run
    def _build_first_run_banner(self):
        panel, heading = feature_panel(
            "GET STARTED\nMake the default account yours\n"
            "Rename it or add another account and currency to begin.",
            tone="lime",
        )
        row = QHBoxLayout(panel)
        # feature_panel already added its own layout; move the heading into a
        # horizontal row with actions so the panel stays compact.
        panel.layout().removeWidget(heading)
        row.addWidget(heading, 1)

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
        row.addLayout(buttons)
        panel.layout().addLayout(row)
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

    # ------------------------------------------------------------------- KPIs
    def _build_kpis(self):
        host = QWidget()
        grid = QGridLayout(host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for column in range(4):
            grid.setColumnStretch(column, 1)

        self.kpi_cards = {
            "balance": MetricCard("Total balance", "—", "Across the selected view", tone="violet"),
            "income": MetricCard("Income", "—", "This month", tone="white"),
            "expense": MetricCard("Expenses", "—", "This month", tone="lime"),
            "net": MetricCard("Net savings", "—", "Income minus expenses", tone="dark"),
        }
        for index, key in enumerate(("balance", "income", "expense", "net")):
            grid.addWidget(self.kpi_cards[key], 0, index)
        return host

    # --------------------------------------------------------------- insights
    def _build_insights(self):
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.insight_heading = section_title(
            "SPENDING OVERVIEW", "Where the money went in the selected period."
        )
        layout.addWidget(self.insight_heading)

        row = QHBoxLayout()
        row.setSpacing(14)

        breakdown = card()
        breakdown_layout = QVBoxLayout(breakdown)
        breakdown_layout.setContentsMargins(20, 18, 20, 18)
        breakdown_layout.setSpacing(10)
        breakdown_layout.addWidget(QLabel("CATEGORY BREAKDOWN"))
        self.category_host = QWidget()
        self.category_layout = QVBoxLayout(self.category_host)
        self.category_layout.setContentsMargins(0, 0, 0, 0)
        self.category_layout.setSpacing(9)
        breakdown_layout.addWidget(self.category_host)
        breakdown_layout.addStretch(1)
        row.addWidget(breakdown, 1)

        activity = card()
        activity_layout = QVBoxLayout(activity)
        activity_layout.setContentsMargins(20, 18, 20, 18)
        activity_layout.setSpacing(10)
        activity_layout.addWidget(QLabel("MONTHLY ACTIVITY"))
        legend = QHBoxLayout()
        legend.setSpacing(16)
        for text, colour in (("Income", VIOLET), ("Expenses", LIME)):
            swatch = QFrame()
            swatch.setFixedSize(12, 12)
            swatch.setStyleSheet(f"background: {colour}; border: none;")
            legend.addWidget(swatch)
            legend.addWidget(QLabel(text))
        legend.addStretch(1)
        activity_layout.addLayout(legend)
        self.chart = MonthlyActivityChart()
        activity_layout.addWidget(self.chart, 1)
        self.chart_caption = QLabel("")
        self.chart_caption.setObjectName("muted")
        activity_layout.addWidget(self.chart_caption)
        row.addWidget(activity, 2)
        layout.addLayout(row)

        layout.addWidget(self._build_recent())
        return host

    def _build_recent(self):
        panel = card()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        heading = QHBoxLayout()
        heading.addWidget(QLabel("RECENT TRANSACTIONS"))
        heading.addStretch(1)
        view_all = lime_button("View all")
        view_all.clicked.connect(lambda: self.app.show_page("transactions"))
        heading.addWidget(view_all)
        layout.addLayout(heading)

        self.recent_table = QTableWidget(0, 4)
        self.recent_table.setHorizontalHeaderLabels(
            ("DATE", "DETAILS", "ACCOUNT", "AMOUNT")
        )
        self.recent_table.verticalHeader().hide()
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setMinimumHeight(150)
        header = self.recent_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        layout.addWidget(self.recent_table)
        return panel

    # --------------------------------------------------------------- accounts
    def _build_accounts_section(self):
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(
            section_title(
                "ACCOUNT BALANCES",
                "Each account is totalled in its own currency; nothing is mixed.",
            )
        )
        self.cards_host = QWidget()
        self.cards_grid = QGridLayout(self.cards_host)
        self.cards_grid.setContentsMargins(0, 0, 0, 0)
        self.cards_grid.setHorizontalSpacing(14)
        self.cards_grid.setVerticalSpacing(14)
        for column in range(3):
            self.cards_grid.setColumnStretch(column, 1)
        layout.addWidget(self.cards_host)
        return host

    # -------------------------------------------------------------------- data
    def refresh(self):
        """Rebuild every figure from current database values."""
        try:
            totals = database.get_account_totals()
            rows = database.get_all_transactions()
        except Exception as error:
            self._totals = []
            self._rows = []
            self.status_label.setText(f"Could not load dashboard data: {error}")
            self._render_account_cards([])
            self._render_insights()
            self.first_run_banner.hide()
            return
        self._totals = totals
        self._rows = rows
        self.status_label.setText("")
        self._sync_scope_combo(totals)
        self._render_account_cards(totals)
        self._render_insights()
        self._sync_first_run(totals)

    def _sync_scope_combo(self, totals):
        previous = _scope_key(self.scope_combo.currentData())
        self.scope_combo.blockSignals(True)
        self.scope_combo.clear()

        groups = {}
        for total in totals:
            code = str(total["currency_code"])
            precision = int(total["currency_precision"])
            groups.setdefault((code, precision), []).append(total)
            self.scope_combo.addItem(
                f"{total['account_name']} · {code}",
                {
                    "kind": "account",
                    "value": total["account_uuid"],
                    "code": code,
                    "precision": precision,
                    "key": f"account:{total['account_uuid']}",
                },
            )

        for (code, precision), accounts in groups.items():
            if len(accounts) < 2:
                continue
            self.scope_combo.addItem(
                f"All {code} accounts ({len(accounts)})",
                {
                    "kind": "currency",
                    "code": code,
                    "precision": precision,
                    "key": f"currency:{code}:{precision}",
                },
            )

        if not totals:
            self.scope_combo.addItem(
                "No accounts",
                {"kind": "none", "code": "", "precision": 2, "key": "none"},
            )

        preferred = ""
        default = next((item for item in totals if item["is_default"]), None)
        if default is not None:
            group = groups.get((default["currency_code"], int(default["currency_precision"])), [])
            preferred = (
                f"currency:{default['currency_code']}:{int(default['currency_precision'])}"
                if len(group) > 1
                else f"account:{default['account_uuid']}"
            )
        target = previous or preferred
        index = self.scope_combo.findData(
            next(
                (
                    self.scope_combo.itemData(i)
                    for i in range(self.scope_combo.count())
                    if _scope_key(self.scope_combo.itemData(i)) == target
                ),
                None,
            )
        )
        self.scope_combo.setCurrentIndex(max(index, 0))
        self.scope_combo.blockSignals(False)

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

    def _render_account_cards(self, totals):
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.summary_cards = {}

        if not totals:
            self.cards_grid.addWidget(
                empty_state("No accounts yet. Add one from the Accounts page."), 0, 0, 1, 3
            )
            return

        for index, total in enumerate(totals):
            panel, labels = self._build_account_card(total)
            row, column = divmod(index, 3)
            self.cards_grid.addWidget(panel, row, column)
            self.summary_cards[total["account_uuid"]] = labels

    def _build_account_card(self, total):
        code = str(total["currency_code"])
        precision = int(total["currency_precision"])

        panel = card()
        panel.setMinimumWidth(190)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(7)

        top = QHBoxLayout()
        name = QLabel(str(total["account_name"]))
        name.setWordWrap(True)
        name.setStyleSheet("font-size: 15px; font-weight: 800;")
        top.addWidget(name, 1)
        if total["is_default"]:
            top.addWidget(BadgeLabel("DEFAULT", tone="lime"))
        layout.addLayout(top)

        currency = QLabel(f"{code} · {precision} decimals")
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
                format_money(total[f"{key}_minor"], code, precision)
            )
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if key == "balance":
                value.setObjectName("accent")
                value.setStyleSheet("font-weight: 800;")
            row.addWidget(label)
            row.addWidget(value, 1)
            layout.addLayout(row)
            labels[key] = value

        count = int(total["transaction_count"])
        summary = QLabel(f"{count} transaction" + ("" if count == 1 else "s"))
        summary.setObjectName("muted")
        layout.addWidget(summary)
        labels["count"] = summary
        return panel, labels

    # --------------------------------------------------------------- insights
    def _on_filter_changed(self):
        is_custom = self.period_combo.currentData() == "custom"
        self.custom_dates.setVisible(is_custom)
        self._render_insights()

    def _render_insights(self):
        if not hasattr(self, "kpi_cards"):
            return
        scope = self.scope_combo.currentData() if hasattr(self, "scope_combo") else None
        period = self.period_combo.currentData() if hasattr(self, "period_combo") else "month"
        start, end, period_label = _period_bounds(
            period,
            self.start_date.date().toPython() if hasattr(self, "start_date") else None,
            self.end_date.date().toPython() if hasattr(self, "end_date") else None,
        )

        scoped_accounts = [item for item in self._totals if _account_in_scope(item, scope)]
        code = str(scope.get("code", "")) if scope else ""
        precision = int(scope.get("precision", 2)) if scope else 2
        if code and start and end and start > end:
            self.status_label.setText("The custom start date is after the end date.")
            start, end = end, start

        scoped_rows = [
            row for row in self._rows
            if _row_in_scope(row, scope) and _within_period(row, start, end)
        ]
        income = sum(
            int(row["amount_minor"]) for row in scoped_rows
            if row["transaction_type"] == "income"
        )
        expense = sum(
            int(row["amount_minor"]) for row in scoped_rows
            if row["transaction_type"] == "expense"
        )
        balance = sum(int(item["balance_minor"]) for item in scoped_accounts)

        suffix = f" · {code}" if code else ""
        self.kpi_cards["balance"].set_value(
            format_money(balance, code, precision) if code else "—",
            f"Across {len(scoped_accounts)} account(s){suffix}",
        )
        self.kpi_cards["income"].set_value(
            format_money(income, code, precision) if code else "—", period_label + suffix
        )
        self.kpi_cards["expense"].set_value(
            format_money(expense, code, precision) if code else "—", period_label + suffix
        )
        self.kpi_cards["net"].set_value(
            format_money(income - expense, code, precision) if code else "—",
            f"{period_label} net savings{suffix}",
        )

        self.insight_heading.findChild(QLabel).setText("SPENDING OVERVIEW")
        self._render_categories(scoped_rows, expense, code, precision)
        self._render_activity(period, start, end, scoped_rows, code, precision, period_label)
        self._render_recent_rows(scoped_rows, code, precision)

    def _render_categories(self, rows, total_expense, code, precision):
        while self.category_layout.count():
            item = self.category_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        buckets = defaultdict(int)
        for row in rows:
            if row["transaction_type"] == "expense":
                buckets[str(row.get("category") or "Uncategorised")] += int(row["amount_minor"])
        ordered = sorted(buckets.items(), key=lambda pair: pair[1], reverse=True)
        if len(ordered) > 6:
            ordered = ordered[:6] + [("Other", sum(value for _, value in ordered[6:]))]

        if not ordered or total_expense <= 0:
            self.category_layout.addWidget(empty_state("No expenses in this period."))
            return

        for name, minor in ordered:
            row = QHBoxLayout()
            row.setSpacing(10)
            name_label = QLabel(name)
            name_label.setMinimumWidth(110)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(min(100, round(minor * 100 / total_expense)))
            bar.setFixedHeight(12)
            bar.setFormat("")
            bar.setTextVisible(False)
            amount = QLabel(format_money(minor, code, precision))
            amount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(name_label, 1)
            row.addWidget(bar, 2)
            row.addWidget(amount)
            self.category_layout.addLayout(row)

    def _render_activity(self, period, start, end, rows, code, precision, period_label):
        months = _month_keys(period, start, end, rows)
        income_by_month = defaultdict(int)
        expense_by_month = defaultdict(int)
        for row in rows:
            when = _row_date(row)
            if when is None:
                continue
            key = f"{when.year:04d}-{when.month:02d}"
            if row["transaction_type"] == "income":
                income_by_month[key] += int(row["amount_minor"])
            else:
                expense_by_month[key] += int(row["amount_minor"])
        self.chart.set_data(
            months,
            [income_by_month[key] for key in months],
            [expense_by_month[key] for key in months],
            code,
        )
        self.chart_caption.setText(
            f"{period_label} · violet income / lime expenses · {code or 'no currency'}"
        )

    def _render_recent_rows(self, rows, code, precision):
        visible = rows[:6]
        self.recent_table.clearSpans()
        self.recent_table.setRowCount(max(1, len(visible)))
        if not visible:
            item = QTableWidgetItem("No transactions in this period.")
            item.setFlags(Qt.ItemIsEnabled)
            self.recent_table.setItem(0, 0, item)
            self.recent_table.setSpan(0, 0, 1, 4)
            return

        self.recent_table.clearSpans()
        for row_index, row in enumerate(visible):
            when = _row_date(row)
            date_text = when.strftime("%d %b %Y") if when else str(row.get("transaction_date", ""))
            detail = str(row.get("description") or row.get("category") or "—")
            category = str(row.get("category") or "")
            if category and category.lower() not in detail.lower():
                detail = f"{detail} · {category}"
            account = f"{row.get('account_name', 'Account')} · {code or row.get('currency_code', '')}"
            amount = format_signed_minor(
                row["amount_minor"], row["currency_code"],
                int(row["currency_precision"]), row["transaction_type"],
            )
            values = (date_text, detail, account, amount)
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                if column == 3:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setForeground(
                        QColor(LIME if row["transaction_type"] == "income" else WHITE)
                    )
                self.recent_table.setItem(row_index, column, item)

    def on_accounts_changed(self):
        self.refresh()

    def on_data_changed(self):
        self.refresh()


def QtCoreDateToday():
    """Return today's QDate; kept as a helper so tests can patch the clock."""
    from PySide6.QtCore import QDate

    return QDate.currentDate()
