"""Dashboard page - a friendly welcome screen for the desktop app."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.theme import COLORS, card, page_header, primary_button


class DashboardView(QWidget):
    """The first screen the user sees when the app opens."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(page_header("Dashboard", "A calm overview of your money."))

        hero = card()
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(28, 26, 28, 28)
        hero_layout.setSpacing(6)
        eyebrow = QLabel("WELCOME BACK")
        eyebrow.setObjectName("field")
        eyebrow.setStyleSheet(f"color: {COLORS['accent']};")
        headline = QLabel("Your money, kept simple.")
        headline.setStyleSheet("font-size: 27px; font-weight: 700;")
        blurb = QLabel(
            "Record income and expenses in a few clicks. Everything is saved "
            "in a local file on this computer — no accounts, no cloud."
        )
        blurb.setObjectName("subtitle")
        blurb.setWordWrap(True)
        add_button = primary_button("Add a transaction")
        add_button.clicked.connect(lambda: self.app.show_page("transactions"))
        hero_layout.addWidget(eyebrow)
        hero_layout.addWidget(headline)
        hero_layout.addWidget(blurb)
        hero_layout.addSpacing(12)
        hero_layout.addWidget(add_button, 0, Qt.AlignLeft)
        layout.addWidget(hero)

        tips_row = QHBoxLayout()
        tips_row.setSpacing(14)
        for title, body in (
            ("Private by design", "Your transactions never leave this computer."),
            ("Rupees ready", "Every amount is shown in ₹ with two decimals."),
            ("Simple on purpose", "No accounts, no bank links, no clutter."),
        ):
            tile = card()
            tile_layout = QVBoxLayout(tile)
            tile_layout.setContentsMargins(20, 18, 20, 18)
            heading = QLabel(title)
            heading.setStyleSheet("font-size: 13px; font-weight: 700;")
            text = QLabel(body)
            text.setObjectName("subtitle")
            text.setWordWrap(True)
            tile_layout.addWidget(heading)
            tile_layout.addWidget(text)
            tips_row.addWidget(tile)
        layout.addLayout(tips_row)

        steps = card()
        steps_layout = QVBoxLayout(steps)
        steps_layout.setContentsMargins(24, 18, 24, 18)
        steps_layout.setSpacing(6)
        heading = QLabel("Getting started")
        heading.setStyleSheet("font-size: 14px; font-weight: 700;")
        steps_layout.addWidget(heading)
        for number, text in enumerate(
            (
                "Add an income or expense on the Transactions page.",
                "Review, sort and filter everything you have saved in the table.",
                "Edit or delete a mistake from the table or its row menu.",
            ),
            start=1,
        ):
            row = QHBoxLayout()
            bullet = QLabel(str(number))
            bullet.setFixedSize(22, 22)
            bullet.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            bullet.setStyleSheet(
                f"background: {COLORS['accent_soft']}; color: {COLORS['accent']};"
                "border-radius: 11px; font-weight: 700;"
            )
            description = QLabel(text)
            description.setObjectName("subtitle")
            row.addWidget(bullet)
            row.addWidget(description, 1)
            steps_layout.addLayout(row)
        layout.addWidget(steps, 1)
