"""Dark theme and small reusable widgets for the PySide6 interface.

Every screen pulls its colours and stylesheet from here, so the whole app can
be restyled in one place. No database or import logic belongs in this file.
"""

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

# Same palette as the old desktop UI, so the app keeps its look.
COLORS = {
    "window": "#0B0E13",
    "sidebar": "#0E1218",
    "surface": "#141A22",
    "surface_alt": "#1A2230",
    "border": "#232C3A",
    "text": "#E9EDF5",
    "muted": "#8A94A6",
    "accent": "#4C8DFF",
    "accent_hover": "#3D7BEB",
    "accent_soft": "#16233B",
    "success": "#3DDC97",
    "success_soft": "#10281F",
    "danger": "#F87171",
    "danger_solid": "#E5484D",
    "danger_solid_hover": "#C93C41",
    "danger_soft": "#2A151A",
}

FONT_FAMILY = "Segoe UI"

STYLESHEET = f"""
* {{ font-family: "{FONT_FAMILY}"; font-size: 12px; color: {COLORS['text']}; }}
QWidget {{ background: {COLORS['window']}; }}
QFrame#card, QDialog#card {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 14px;
}}
QFrame#sidebar {{ background: {COLORS['sidebar']}; border: none; }}
QLabel#title {{ font-size: 25px; font-weight: 700; }}
QLabel#subtitle, QLabel#field, QLabel#muted {{ color: {COLORS['muted']}; }}
QLabel#field {{ font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
QLabel#badge {{
    background: {COLORS['surface_alt']}; color: {COLORS['muted']};
    border-radius: 8px; padding: 3px 9px; font-size: 11px;
}}
QLabel#statusOk {{ color: {COLORS['success']}; }}
QLabel#statusError {{ color: {COLORS['danger']}; }}
QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {COLORS['surface_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 9px;
    padding: 7px 10px;
    min-height: 22px;
    selection-background-color: {COLORS['accent']};
}}
QLineEdit:focus, QDateEdit:focus, QComboBox:focus {{ border: 1px solid {COLORS['accent']}; }}
QPushButton {{
    background: {COLORS['surface_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 9px;
    padding: 8px 14px;
}}
QPushButton:hover {{ background: {COLORS['border']}; }}
QPushButton#primary {{
    background: {COLORS['accent']}; border: none; color: #FFFFFF; font-weight: 700;
}}
QPushButton#primary:hover {{ background: {COLORS['accent_hover']}; }}
QPushButton#danger {{
    background: {COLORS['danger_solid']}; border: none; color: #FFFFFF; font-weight: 700;
}}
QPushButton#danger:hover {{ background: {COLORS['danger_solid_hover']}; }}
QPushButton#ghost {{ background: transparent; border: none; color: {COLORS['muted']}; }}
QPushButton#ghost:hover {{ background: {COLORS['surface_alt']}; }}
QPushButton#nav {{
    background: transparent; border: none; color: {COLORS['muted']};
    text-align: left; padding: 11px 14px; font-size: 12px; border-radius: 10px;
}}
QPushButton#nav:hover {{ background: {COLORS['surface_alt']}; }}
QPushButton#nav:checked {{
    background: {COLORS['accent_soft']}; color: {COLORS['accent']}; font-weight: 700;
}}
QTableView {{
    background: {COLORS['surface']};
    alternate-background-color: {COLORS['surface_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    gridline-color: {COLORS['border']};
    selection-background-color: {COLORS['accent_soft']};
    selection-color: {COLORS['text']};
}}
QHeaderView::section {{
    background: {COLORS['surface_alt']};
    color: {COLORS['muted']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    padding: 8px 6px;
    font-size: 10px;
    font-weight: 700;
}}
QComboBox QAbstractItemView {{
    background: {COLORS['surface_alt']};
    selection-background-color: {COLORS['accent']};
}}
QCheckBox {{ spacing: 7px; }}
QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 0;
}}
QScrollBar::handle:vertical {{ background: {COLORS['border']}; border-radius: 5px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QToolTip {{
    background: {COLORS['surface_alt']}; border: 1px solid {COLORS['border']};
    padding: 5px;
}}
"""


def apply_theme(app):
    """Set Fusion, a dark palette and the shared stylesheet once at startup."""
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, _colour("window"))
    palette.setColor(QPalette.WindowText, _colour("text"))
    palette.setColor(QPalette.Base, _colour("surface"))
    palette.setColor(QPalette.AlternateBase, _colour("surface_alt"))
    palette.setColor(QPalette.Text, _colour("text"))
    palette.setColor(QPalette.Button, _colour("surface_alt"))
    palette.setColor(QPalette.ButtonText, _colour("text"))
    palette.setColor(QPalette.Highlight, _colour("accent"))
    palette.setColor(QPalette.HighlightedText, _colour("window"))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)


def _colour(name):
    from PySide6.QtGui import QColor

    return QColor(COLORS[name])


def card(parent=None):
    """A rounded panel used for every section of the interface."""
    frame = QFrame(parent)
    frame.setObjectName("card")
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
    """Modal yes/no dialog. ``on_confirm`` runs only on an explicit confirm."""

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

    def _confirm(self):
        callback = self._on_confirm
        self.accept()
        if callback is not None:
            callback()
