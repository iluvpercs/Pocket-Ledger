"""Settings page - app information and a look at what comes next."""

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import database
from ui.theme import card, code_panel, page_header


class SettingsView(QWidget):
    """Milestone 1 keeps settings simple: information plus future plans."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(page_header("Settings", "App information and a look at what comes next."))

        layout.addWidget(self._build_about())
        layout.addWidget(self._build_storage())
        layout.addWidget(self._build_coming_soon())
        layout.addStretch(1)

    def _build_about(self):
        about = card()
        layout = QVBoxLayout(about)
        layout.setContentsMargins(24, 16, 24, 16)
        heading = QLabel("About Pocket Ledger")
        heading.setStyleSheet("font-size: 14px; font-weight: 700;")
        layout.addWidget(heading)
        for label, value in (
            ("Version", "0.3 · Qt edition"),
            ("Interface", "PySide6 (Qt for Python)"),
            ("Storage", "SQLite database on this computer"),
            ("Currency", "Per account (chosen when the account is created)"),
            ("Theme", "Dark"),
        ):
            row = QHBoxLayout()
            name = QLabel(label)
            name.setObjectName("muted")
            name.setFixedWidth(150)
            detail = QLabel(value)
            detail.setWordWrap(True)
            row.addWidget(name)
            row.addWidget(detail, 1)
            layout.addLayout(row)
        return about

    def _build_storage(self):
        storage = card()
        layout = QVBoxLayout(storage)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(6)
        heading = QLabel("Data location")
        heading.setStyleSheet("font-size: 14px; font-weight: 700;")
        note = QLabel("All data stays in a local SQLite file. Nothing is sent to the internet.")
        note.setObjectName("subtitle")
        note.setWordWrap(True)
        path = code_panel(str(database.DB_PATH))

        actions = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusOk")
        copy_button = QPushButton("Copy path")
        copy_button.clicked.connect(self._copy_path)
        actions.addWidget(self.status_label, 1)
        actions.addWidget(copy_button)

        layout.addWidget(heading)
        layout.addWidget(note)
        layout.addWidget(path)
        layout.addLayout(actions)
        return storage

    def _build_coming_soon(self):
        coming = card()
        layout = QVBoxLayout(coming)
        layout.setContentsMargins(24, 16, 24, 16)
        heading = QLabel("Known limitations")
        heading.setStyleSheet("font-size: 14px; font-weight: 700;")
        layout.addWidget(heading)
        for plan in (
            "No PDF import, bank connections, cloud sync, or mobile app yet.",
            "No monthly reports, budgets, charts, or backup/restore UI yet.",
            "Account currency is fixed after creation; create a new account for a different currency.",
            "Amounts are stored as integer minor units (0/2/3 decimal currencies supported).",
        ):
            text = QLabel(f"•  {plan}")
            text.setObjectName("subtitle")
            text.setWordWrap(True)
            layout.addWidget(text)
        return coming

    def _copy_path(self):
        QApplication.clipboard().setText(str(database.DB_PATH))
        self.status_label.setText("Path copied to clipboard.")
