"""Settings page - brand, storage information and known limitations."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import database
from ui.theme import (
    IconBadge,
    card,
    code_panel,
    feature_panel,
    page_header,
    section_title,
)
from version import APP_VERSION_TEXT


class SettingsView(QWidget):
    """Information page: the app is deliberately light on configuration."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

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
        layout.setContentsMargins(26, 22, 26, 24)
        layout.setSpacing(14)
        layout.addWidget(page_header("Settings", "App information and data location."))
        layout.addWidget(self._build_brand())
        layout.addWidget(self._build_about())
        layout.addWidget(self._build_storage())
        layout.addWidget(self._build_limitations())
        layout.addWidget(self._build_roadmap())
        layout.addStretch(1)

    def _build_brand(self):
        panel, heading = feature_panel(
            "YOUR MONEY. YOUR CONTROL.\n"
            "Private, local, and deliberately simple.",
            tone="violet",
        )
        row = QHBoxLayout(panel)
        panel.layout().removeWidget(heading)
        row.addWidget(IconBadge("PL", size=46))
        row.addWidget(heading, 1)
        panel.layout().addLayout(row)
        return panel

    def _build_about(self):
        about = card()
        layout = QVBoxLayout(about)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)
        layout.addWidget(section_title("ABOUT POCKET LEDGER"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(7)
        grid.setColumnStretch(1, 1)
        details = (
            ("Version", APP_VERSION_TEXT),
            ("Interface", "PySide6 (Qt for Python)"),
            ("Storage", "SQLite database on this computer"),
            ("Privacy", "Local only — no account, uploads or network calls"),
            ("Currency", "Per account, chosen when the account is created"),
            ("Theme", "Violet · lime · black · white"),
        )
        for row, (label, value) in enumerate(details):
            name = QLabel(label)
            name.setObjectName("muted")
            name.setWordWrap(True)
            text = QLabel(value)
            text.setWordWrap(True)
            grid.addWidget(name, row, 0)
            grid.addWidget(text, row, 1)
        layout.addLayout(grid)
        return about

    def _build_storage(self):
        storage = card()
        layout = QVBoxLayout(storage)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)
        layout.addWidget(
            section_title("DATA LOCATION", "Nothing is sent to the internet.")
        )
        note = QLabel(
            "All transactions stay in one local SQLite file. Copy that file "
            "while the app is closed if you want your own backup."
        )
        note.setObjectName("subtitle")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addWidget(code_panel(str(database.DB_PATH)))

        actions = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusOk")
        self.status_label.setWordWrap(True)
        copy_button = QPushButton("Copy path")
        copy_button.clicked.connect(self._copy_path)
        actions.addWidget(self.status_label, 1)
        actions.addWidget(copy_button)
        layout.addLayout(actions)
        return storage

    def _build_limitations(self):
        panel = card()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)
        layout.addWidget(section_title("KNOWN LIMITATIONS"))
        for text in (
            "No PDF import; CSV import is available today.",
            "No budgets, forecasts, bank connections, cloud sync or mobile app.",
            "Account currency is fixed after creation; create a new account for a different currency.",
            "Amounts are stored as integer minor units (0/2/3 decimal currencies supported).",
        ):
            label = QLabel(f"•  {text}")
            label.setObjectName("subtitle")
            label.setWordWrap(True)
            layout.addWidget(label)
        return panel

    def _build_roadmap(self):
        panel = card()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)
        layout.addWidget(
            section_title("FUTURE PLANNING", "Not implemented in this desktop build.")
        )
        for text in (
            "Phase 5 · Android app — the supplied mobile SVG is reserved for future branding.",
            "Phase 6 · Wi-Fi Sync — planned only; there is no sync UI or network service today.",
        ):
            label = QLabel(f"•  {text}")
            label.setObjectName("subtitle")
            label.setWordWrap(True)
            layout.addWidget(label)
        return panel

    def _copy_path(self):
        QApplication.clipboard().setText(str(database.DB_PATH))
        self.status_label.setText("Path copied to clipboard.")
