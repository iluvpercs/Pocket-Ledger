"""Strawberry theme and small reusable widgets for the PySide6 interface.

Every screen pulls its colours from the named constants below, so the whole app
can be restyled in one place. No database or import logic belongs in this file.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# ------------------------------------------------------------------ palette
# Named Strawberry palette. These are the single source of truth for colours.
BACKGROUND = "#202125"
SIDEBAR = "#282A2F"
SURFACE = "#2F3137"
SURFACE_ALT = "#383B42"
BORDER = "#454950"

PRIMARY = "#F14666"
SECONDARY = "#EE8980"
HIGHLIGHT = "#FFCDAA"
POSITIVE = "#9CB898"
NEGATIVE = "#F14666"

TEXT = "#F7F3EF"
MUTED = "#C8BAB2"
# Dark ink gives 5.0:1 on PRIMARY and 7.0:1 on SECONDARY, so button text
# passes WCAG AA (white only reaches 3.6:1 on #F14666).
ON_ACCENT = "#151619"

# Tinted surfaces derived from the palette above.
PRIMARY_SOFT = "#432D35"
SECONDARY_SOFT = "#493338"
HIGHLIGHT_SOFT = "#4A3D33"
POSITIVE_SOFT = "#2E3B2D"
NEGATIVE_SOFT = "#43272E"

# Backwards-compatible aliases used by the rest of the UI.
ACCENT = PRIMARY
ACCENT_HOVER = SECONDARY
ACCENT_SOFT = PRIMARY_SOFT
SUCCESS = POSITIVE
SUCCESS_SOFT = POSITIVE_SOFT
DANGER = NEGATIVE
DANGER_SOLID = NEGATIVE
DANGER_SOLID_HOVER = SECONDARY
DANGER_SOFT = NEGATIVE_SOFT

COLORS = {
    "window": BACKGROUND,
    "sidebar": SIDEBAR,
    "surface": SURFACE,
    "surface_alt": SURFACE_ALT,
    "border": BORDER,
    "text": TEXT,
    "muted": MUTED,
    "accent": PRIMARY,
    "accent_hover": SECONDARY,
    "accent_soft": PRIMARY_SOFT,
    "success": POSITIVE,
    "success_soft": POSITIVE_SOFT,
    "danger": NEGATIVE,
    "danger_solid": NEGATIVE,
    "danger_solid_hover": SECONDARY,
    "danger_soft": NEGATIVE_SOFT,
    "highlight": HIGHLIGHT,
    "highlight_soft": HIGHLIGHT_SOFT,
    "secondary": SECONDARY,
    "secondary_soft": SECONDARY_SOFT,
    "positive": POSITIVE,
    "negative": NEGATIVE,
    "on_accent": ON_ACCENT,
}

FONT_FAMILY = "Segoe UI"

STYLESHEET = f"""
* {{ font-family: "{FONT_FAMILY}"; font-size: 12px; color: {TEXT}; }}
QWidget {{ background: {BACKGROUND}; }}

/* Fix the old dark rectangles behind every text label. More specific
   object-name rules below never set a background on a QLabel. */
QLabel {{ background: transparent; }}
QDialog, QMessageBox {{ background: {BACKGROUND}; }}

QFrame#card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
QFrame#sidebar {{ background: {SIDEBAR}; border: none; }}

/* Small coloured chips are QFrames, not QLabels, so the "all labels are
   transparent" rule stays true everywhere in the main window. */
QFrame#badge {{
    background: {PRIMARY_SOFT};
    border: 1px solid {PRIMARY};
    border-radius: 9px;
}}
QFrame#badge QLabel {{ color: {HIGHLIGHT}; font-size: 11px; font-weight: 700; }}
QFrame#bullet {{ background: {PRIMARY_SOFT}; border-radius: 11px; }}
QFrame#bullet QLabel {{ color: {HIGHLIGHT}; font-size: 11px; font-weight: 700; }}
QFrame#brandBadge {{ background: {PRIMARY}; border-radius: 11px; }}
QFrame#brandBadge QLabel {{ color: {ON_ACCENT}; font-size: 18px; font-weight: 700; }}
QFrame#code {{
    background: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QFrame#code QLabel {{ color: {MUTED}; font-family: Consolas; font-size: 11px; }}

QLabel#title {{ font-size: 25px; font-weight: 700; }}
QLabel#subtitle, QLabel#muted {{ color: {MUTED}; }}
QLabel#field {{ color: {HIGHLIGHT}; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
QLabel#accent {{ color: {HIGHLIGHT}; font-weight: 700; }}
QLabel#statusOk {{ color: {POSITIVE}; }}
QLabel#statusError {{ color: {NEGATIVE}; font-weight: 700; }}
QLabel#devBadge {{
    background: {PRIMARY};
    color: {ON_ACCENT};
    border-radius: 7px;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 700;
}}

QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: 9px;
    padding: 7px 10px;
    min-height: 22px;
    selection-background-color: {PRIMARY};
    selection-color: {ON_ACCENT};
}}
QLineEdit:focus, QDateEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1px solid {PRIMARY}; }}

QPushButton {{
    background: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: 9px;
    padding: 8px 14px;
    color: {TEXT};
}}
QPushButton:hover {{ background: {SECONDARY_SOFT}; color: {HIGHLIGHT}; }}
QPushButton:focus {{ border: 1px solid {PRIMARY}; }}
QPushButton#primary {{
    background: {PRIMARY}; border: none; color: {ON_ACCENT}; font-weight: 700;
}}
QPushButton#primary:hover {{ background: {SECONDARY}; color: {ON_ACCENT}; }}
QPushButton#danger {{
    background: {NEGATIVE}; border: none; color: {ON_ACCENT}; font-weight: 700;
}}
QPushButton#danger:hover {{ background: {SECONDARY}; color: {ON_ACCENT}; }}
QPushButton#ghost {{ background: transparent; border: none; color: {MUTED}; }}
QPushButton#ghost:hover {{ background: {SURFACE_ALT}; color: {HIGHLIGHT}; }}
QPushButton#nav {{
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    color: {MUTED};
    text-align: left;
    padding: 11px 14px 11px 18px;
    font-size: 12px;
    border-radius: 10px;
}}
QPushButton#nav:hover {{ background: {SECONDARY_SOFT}; color: {HIGHLIGHT}; }}
QPushButton#nav:checked {{
    background: {PRIMARY_SOFT};
    color: {HIGHLIGHT};
    border-left: 3px solid {PRIMARY};
    font-weight: 700;
}}

QTableView {{
    background: {SURFACE};
    alternate-background-color: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: 10px;
    gridline-color: {BORDER};
    selection-background-color: {PRIMARY_SOFT};
    selection-color: {HIGHLIGHT};
}}
QTableView::item {{ padding: 4px 6px; }}
QHeaderView::section {{
    background: {SURFACE_ALT};
    color: {MUTED};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 8px 6px;
    font-size: 10px;
    font-weight: 700;
}}
QHeaderView::section:hover {{ color: {HIGHLIGHT}; }}
QComboBox QAbstractItemView {{
    background: {SURFACE_ALT};
    border: 1px solid {BORDER};
    selection-background-color: {PRIMARY};
    selection-color: {ON_ACCENT};
}}
QCheckBox {{ spacing: 7px; }}
QCheckBox::indicator {{
    width: 15px; height: 15px;
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: {SURFACE_ALT};
}}
QCheckBox::indicator:checked {{ background: {PRIMARY}; border: 1px solid {PRIMARY}; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; }}
QScrollBar::handle:vertical:hover {{ background: {SECONDARY}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 5px; }}
QScrollBar::handle:horizontal:hover {{ background: {SECONDARY}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}

QToolTip {{
    background: {SURFACE_ALT};
    border: 1px solid {BORDER};
    color: {TEXT};
    padding: 5px;
}}
"""


def apply_theme(app):
    """Set Fusion, the Strawberry palette and the shared stylesheet once."""
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BACKGROUND))
    palette.setColor(QPalette.WindowText, QColor(TEXT))
    palette.setColor(QPalette.Base, QColor(SURFACE))
    palette.setColor(QPalette.AlternateBase, QColor(SURFACE_ALT))
    palette.setColor(QPalette.Text, QColor(TEXT))
    palette.setColor(QPalette.Button, QColor(SURFACE_ALT))
    palette.setColor(QPalette.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.Highlight, QColor(PRIMARY))
    palette.setColor(QPalette.HighlightedText, QColor(ON_ACCENT))
    palette.setColor(QPalette.Link, QColor(PRIMARY))
    palette.setColor(QPalette.LinkVisited, QColor(SECONDARY))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)


def _colour(name):
    """Look up a palette value by its legacy COLORS key."""
    return QColor(COLORS[name])


def card(parent=None):
    """A rounded panel used for every section of the interface."""
    frame = QFrame(parent)
    frame.setObjectName("card")
    return frame


class BadgeLabel(QFrame):
    """A coloured count chip that behaves like a label for callers.

    It is a QFrame so the chip has a background without breaking the global
    "QLabel { background: transparent; }" fix.
    """

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setObjectName("badge")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 3, 9, 3)
        layout.setSpacing(0)
        self._label = QLabel(text)
        layout.addWidget(self._label)

    def setText(self, text):
        self._label.setText(str(text))

    def text(self):
        return self._label.text()


class IconBadge(QFrame):
    """Small square or circular brand badge with centred text."""

    def __init__(self, text, object_name="brandBadge", size=38, parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setFixedSize(size, size)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)


class NumberBadge(QFrame):
    """Circular step number used on the dashboard."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setObjectName("bullet")
        self.setFixedSize(22, 22)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(str(text))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)


def code_panel(text, parent=None):
    """A read-only-looking path/code panel with a transparent text label."""
    frame = QFrame(parent)
    frame.setObjectName("code")
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(8, 8, 8, 8)
    label = QLabel(text)
    label.setWordWrap(True)
    layout.addWidget(label)
    return frame


def page_header(title, subtitle):
    """Return a title + subtitle block for the top of a page."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)

    heading = QLabel(title)
    heading.setObjectName("title")
    sub = QLabel(subtitle)
    sub.setObjectName("subtitle")
    layout.addWidget(heading)
    layout.addWidget(sub)
    return widget


def field_label(text):
    """Small uppercase-style label that sits above an input."""
    label = QLabel(text)
    label.setObjectName("field")
    return label


def styled_entry(placeholder=""):
    """A single-line input that matches the dark theme."""
    entry = QLineEdit()
    entry.setPlaceholderText(placeholder)
    return entry


def primary_button(text):
    button = QPushButton(text)
    button.setObjectName("primary")
    return button


def danger_button(text):
    button = QPushButton(text)
    button.setObjectName("danger")
    return button


def ghost_button(text):
    button = QPushButton(text)
    button.setObjectName("ghost")
    return button


class ConfirmDialog(QDialog):
    """Modal yes/no dialog.

    Constructing the dialog shows it and blocks until the user answers, so a
    caller only needs to create it. ``on_confirm`` runs only when the confirm
    button is pressed; cancelling does nothing.
    """

    def __init__(
        self,
        parent,
        title,
        message,
        confirm_text="Delete",
        cancel_text="Cancel",
        on_confirm=None,
    ):
        super().__init__(parent)
        self._on_confirm = on_confirm
        self.setWindowTitle("Pocket Ledger")
        self.setModal(True)
        self.setFixedWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(12)

        heading = QLabel(title)
        heading.setObjectName("title")
        heading.setStyleSheet("font-size: 17px;")
        body = QLabel(message)
        body.setWordWrap(True)
        body.setObjectName("subtitle")
        layout.addWidget(heading)
        layout.addWidget(body)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton(cancel_text)
        confirm = danger_button(confirm_text)
        cancel.clicked.connect(self.reject)
        confirm.clicked.connect(self._confirm)
        buttons.addWidget(cancel)
        buttons.addWidget(confirm)
        layout.addLayout(buttons)

        self.exec()

    def _confirm(self):
        callback = self._on_confirm
        self.accept()
        if callback is not None:
            callback()
