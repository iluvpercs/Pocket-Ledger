"""Brand design system and reusable widgets for the Pocket Ledger desktop app.

The visual language is deliberately small and strict:

* Black   ``#000000`` - canvas and dark panels
* Violet  ``#7D39EB`` - primary actions, brand mark and active navigation
* Lime    ``#C6FF33`` - money-positive accents and secondary emphasis
* White   ``#FFFFFF`` - cards, primary text and separators

Every screen pulls colours from these constants, so the whole app stays on
brand. Only the four approved colours are used; softer tints are the same
colours at reduced opacity via ``rgba(...)``. No database or import logic
belongs in this module.
"""

from __future__ import annotations

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
BLACK = "#000000"
VIOLET = "#7D39EB"
LIME = "#C6FF33"
WHITE = "#FFFFFF"

# Semantic names used throughout the screens.
BACKGROUND = BLACK
SIDEBAR = BLACK
SURFACE = BLACK
SURFACE_ALT = BLACK
BORDER = VIOLET

PRIMARY = VIOLET
SECONDARY = LIME
HIGHLIGHT = LIME
POSITIVE = LIME
NEGATIVE = VIOLET

TEXT = WHITE
MUTED = WHITE
ON_ACCENT = WHITE       # white on violet: 5.74:1
ON_LIME = BLACK         # black on lime: 17.75:1

# Opacity variants of the four approved colours, never new hues.
PRIMARY_SOFT = "rgba(125, 57, 235, 0.22)"
SECONDARY_SOFT = "rgba(198, 255, 51, 0.16)"
HIGHLIGHT_SOFT = "rgba(198, 255, 51, 0.12)"
POSITIVE_SOFT = "rgba(198, 255, 51, 0.12)"
NEGATIVE_SOFT = "rgba(125, 57, 235, 0.28)"
MUTED_TEXT = "rgba(255, 255, 255, 0.68)"

# Backwards-compatible aliases. Existing call sites keep working unchanged.
ACCENT = PRIMARY
ACCENT_HOVER = SECONDARY
ACCENT_SOFT = PRIMARY_SOFT
SUCCESS = POSITIVE
SUCCESS_SOFT = POSITIVE_SOFT
DANGER = NEGATIVE
DANGER_SOLID = NEGATIVE
DANGER_SOLID_HOVER = VIOLET
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
    "danger_solid_hover": DANGER_SOLID_HOVER,
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
* {{ font-family: "{FONT_FAMILY}"; font-size: 13px; color: {TEXT}; }}
QWidget {{ background: {BLACK}; }}

/* Never paint a dark rectangle behind a label. More specific object-name
   rules below only change text colour, so headings never look clipped. */
QLabel {{ background: transparent; }}
QDialog, QMessageBox {{
    background: {BLACK};
    border: 1px solid {VIOLET};
    border-radius: 18px;
}}

QFrame#card {{
    background: {BLACK};
    border: 1px solid {VIOLET};
    border-radius: 18px;
}}
QFrame#cardWhite {{ background: {WHITE}; border: 1px solid {WHITE}; border-radius: 18px; }}
QFrame#cardViolet {{ background: {VIOLET}; border: 1px solid {VIOLET}; border-radius: 18px; }}
QFrame#cardLime {{ background: {LIME}; border: 1px solid {LIME}; border-radius: 18px; }}
QFrame#cardDark {{
    background: {BLACK};
    border: 1px solid {WHITE};
    border-radius: 18px;
}}
QFrame#sidebar {{ background: {BLACK}; border: none; }}
QFrame#divider {{ background: {VIOLET}; border: none; max-height: 1px; }}
QFrame#barTrack {{ background: {VIOLET}; border: none; border-radius: 5px; }}
QFrame#barFill {{ background: {LIME}; border: none; border-radius: 5px; }}

QFrame#badge {{
    background: {VIOLET};
    border: none;
    border-radius: 10px;
}}
QFrame#badge QLabel {{ color: {WHITE}; font-size: 11px; font-weight: 700; }}
QFrame#badgeLime {{ background: {LIME}; border: none; border-radius: 10px; }}
QFrame#badgeLime QLabel {{ color: {BLACK}; font-size: 11px; font-weight: 700; }}
QFrame#bullet {{ background: {VIOLET}; border-radius: 12px; }}
QFrame#bullet QLabel {{ color: {WHITE}; font-size: 11px; font-weight: 700; }}
QFrame#brandBadge {{ background: {VIOLET}; border-radius: 12px; }}
QFrame#brandBadge QLabel {{
    color: {WHITE}; font-size: 20px; font-weight: 800; letter-spacing: 1px;
}}
QFrame#code {{
    background: {BLACK};
    border: 1px solid {VIOLET};
    border-radius: 10px;
}}
QFrame#code QLabel {{ color: {WHITE}; font-family: Consolas; font-size: 12px; }}
QFrame#feature {{ background: {VIOLET}; border: none; border-radius: 18px; }}
QFrame#featureLime {{ background: {LIME}; border: none; border-radius: 18px; }}
QFrame#feature QLabel, QFrame#featureLime QLabel {{ background: transparent; }}

QLabel#title {{ font-size: 28px; font-weight: 800; }}
QLabel#subtitle, QLabel#muted {{ color: {MUTED_TEXT}; }}
QLabel#field {{
    color: {LIME};
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
}}
QLabel#accent {{ color: {LIME}; font-weight: 700; }}
QLabel#eyebrow {{
    color: {LIME};
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
}}
QLabel#sectionTitle {{ font-size: 17px; font-weight: 800; }}
QLabel#metricCaption {{
    color: {WHITE};
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
}}
QLabel#metricValue {{ font-size: 34px; font-weight: 800; }}
QLabel#metricValueSmall {{ font-size: 22px; font-weight: 800; }}
QLabel#statusOk {{ color: {LIME}; font-weight: 700; }}
QLabel#statusError {{ color: {VIOLET}; font-weight: 800; }}
QLabel#onWhite {{ color: {BLACK}; }}
QLabel#onViolet {{ color: {WHITE}; }}
QLabel#onLime {{ color: {BLACK}; }}

QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {BLACK};
    border: 1px solid {VIOLET};
    border-radius: 10px;
    padding: 8px 11px;
    min-height: 24px;
    selection-background-color: {VIOLET};
    selection-color: {WHITE};
}}
QLineEdit:focus, QDateEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{ border: 2px solid {LIME}; }}

QPushButton {{
    background: {BLACK};
    border: 1px solid {WHITE};
    border-radius: 10px;
    padding: 9px 16px;
    min-height: 22px;
    color: {WHITE};
    font-weight: 700;
}}
QPushButton:hover {{ background: {VIOLET}; border-color: {VIOLET}; color: {WHITE}; }}
QPushButton:focus {{ border: 2px solid {LIME}; }}
QPushButton:disabled {{ color: {MUTED_TEXT}; border-color: {VIOLET}; }}
QPushButton#primary {{
    background: {VIOLET}; border: none; color: {WHITE}; font-weight: 800;
    padding: 11px 20px;
}}
QPushButton#primary:hover {{ background: {WHITE}; color: {BLACK}; }}
QPushButton#lime {{
    background: {LIME}; border: none; color: {BLACK}; font-weight: 800;
    padding: 11px 20px;
}}
QPushButton#lime:hover {{ background: {WHITE}; color: {BLACK}; }}
QPushButton#danger {{
    background: {VIOLET}; border: none; color: {WHITE}; font-weight: 800;
}}
QPushButton#danger:hover {{ background: {WHITE}; color: {BLACK}; }}
QPushButton:pressed {{ border-color: {LIME}; }}
QPushButton#primary:pressed, QPushButton#danger:pressed {{
    background: {WHITE}; color: {BLACK};
}}
QPushButton#lime:pressed {{ background: {VIOLET}; color: {WHITE}; }}
QPushButton#ghost {{ background: transparent; border: none; color: {WHITE}; }}
QPushButton#ghost:hover {{ background: {VIOLET}; color: {WHITE}; }}
QPushButton#nav {{
    background: transparent;
    border: none;
    border-left: 4px solid transparent;
    color: {WHITE};
    text-align: left;
    padding: 13px 16px 13px 18px;
    font-size: 14px;
    font-weight: 700;
    border-radius: 12px;
}}
QPushButton#nav:hover {{ background: {VIOLET}; color: {WHITE}; }}
QPushButton#nav:checked {{
    background: {VIOLET};
    color: {WHITE};
    border-left: 4px solid {LIME};
}}

QTableView, QTableWidget {{
    background: {BLACK};
    alternate-background-color: {BLACK};
    border: 1px solid {VIOLET};
    border-radius: 12px;
    gridline-color: {VIOLET};
    selection-background-color: {VIOLET};
    selection-color: {WHITE};
}}
QTableView::item, QTableWidget::item {{ padding: 8px 10px; }}
QTableView::item:hover, QTableWidget::item:hover {{ background: {PRIMARY_SOFT}; }}
QHeaderView::section {{
    background: {BLACK};
    color: {LIME};
    border: none;
    border-bottom: 2px solid {VIOLET};
    padding: 10px 8px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
}}
QHeaderView::section:hover {{ color: {WHITE}; }}
QComboBox QAbstractItemView {{
    background: {BLACK};
    border: 1px solid {VIOLET};
    border-radius: 10px;
    selection-background-color: {VIOLET};
    selection-color: {WHITE};
}}
QComboBox QAbstractItemView::item {{ padding: 8px 10px; }}
QComboBox QAbstractItemView::item:selected {{
    background: {VIOLET}; color: {WHITE};
}}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 2px solid {VIOLET};
    border-radius: 4px;
    background: {BLACK};
}}
QCheckBox::indicator:checked {{ background: {LIME}; border: 2px solid {LIME}; }}

QProgressBar {{
    background: {BLACK};
    border: 1px solid {VIOLET};
    border-radius: 5px;
    height: 10px;
    text-align: right;
}}
QProgressBar::chunk {{ background: {LIME}; border-radius: 4px; margin: 1px; }}

QScrollArea {{ background: {BLACK}; border: none; }}
QScrollArea > QWidget > QWidget {{ background: {BLACK}; }}
QScrollArea QFrame#card, QScrollArea QFrame#cardWhite,
QScrollArea QFrame#cardViolet, QScrollArea QFrame#cardLime {{ background: {BLACK}; }}
QScrollArea QFrame#cardWhite {{ background: {WHITE}; }}
QScrollArea QFrame#cardViolet {{ background: {VIOLET}; }}
QScrollArea QFrame#cardLime {{ background: {LIME}; }}

QScrollBar:vertical {{ background: {BLACK}; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {VIOLET}; border-radius: 6px; }}
QScrollBar::handle:vertical:hover {{ background: {LIME}; }}
QScrollBar:horizontal {{ background: {BLACK}; height: 12px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {VIOLET}; border-radius: 6px; }}
QScrollBar::handle:horizontal:hover {{ background: {LIME}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}

QToolTip {{
    background: {VIOLET};
    border: none;
    color: {WHITE};
    padding: 6px;
}}
"""


def apply_theme(app):
    """Set Fusion, the strict brand palette and the shared stylesheet once."""
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BLACK))
    palette.setColor(QPalette.WindowText, QColor(WHITE))
    palette.setColor(QPalette.Base, QColor(BLACK))
    palette.setColor(QPalette.AlternateBase, QColor(BLACK))
    palette.setColor(QPalette.Text, QColor(WHITE))
    palette.setColor(QPalette.Button, QColor(VIOLET))
    palette.setColor(QPalette.ButtonText, QColor(WHITE))
    palette.setColor(QPalette.Highlight, QColor(VIOLET))
    palette.setColor(QPalette.HighlightedText, QColor(WHITE))
    palette.setColor(QPalette.Link, QColor(LIME))
    palette.setColor(QPalette.LinkVisited, QColor(VIOLET))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)


def _colour(name):
    """Look up a palette value by its legacy COLORS key."""
    return QColor(COLORS[name])


def card(parent=None, tone="dark"):
    """A rounded panel. ``tone`` is one of dark/violet/white/lime."""
    names = {
        "dark": "card",
        "violet": "cardViolet",
        "white": "cardWhite",
        "lime": "cardLime",
        "outline": "cardDark",
    }
    frame = QFrame(parent)
    frame.setObjectName(names.get(tone, "card"))
    return frame


def feature_panel(text, tone="violet", parent=None):
    """A bold colour-blocked panel used for short statements or calls to action."""
    frame = QFrame(parent)
    frame.setObjectName("feature" if tone != "lime" else "featureLime")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(8)
    label = QLabel(text)
    label.setObjectName("onViolet" if tone != "lime" else "onLime")
    label.setWordWrap(True)
    layout.addWidget(label)
    return frame, label


def empty_state(message, parent=None):
    """A consistent, readable empty-data message."""
    label = QLabel(message)
    label.setObjectName("subtitle")
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignCenter)
    label.setMinimumHeight(64)
    return label


def section_title(text, note=None, parent=None):
    """A consistent section heading with an optional muted note."""
    widget = QWidget(parent)
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)
    heading = QLabel(text)
    heading.setObjectName("sectionTitle")
    layout.addWidget(heading)
    if note:
        detail = QLabel(note)
        detail.setObjectName("muted")
        detail.setWordWrap(True)
        layout.addWidget(detail, 1)
    else:
        layout.addStretch(1)
    return widget


class BadgeLabel(QFrame):
    """A violet count chip that behaves like a label for callers."""

    def __init__(self, text="", parent=None, tone="violet"):
        super().__init__(parent)
        self.setObjectName("badge" if tone != "lime" else "badgeLime")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(11, 4, 11, 4)
        layout.setSpacing(0)
        self._label = QLabel(text)
        layout.addWidget(self._label)

    def setText(self, text):
        self._label.setText(str(text))

    def text(self):
        return self._label.text()


class IconBadge(QFrame):
    """The violet square PL brand mark, centred."""

    def __init__(self, text, object_name="brandBadge", size=46, parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setFixedSize(size, size)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("onViolet")
        layout.addWidget(label)


class NumberBadge(QFrame):
    """Small violet step number."""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setObjectName("bullet")
        self.setFixedSize(24, 24)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(str(text))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)


class MetricCard(QFrame):
    """Colour-blocked summary tile with a large financial figure.

    ``tone`` controls the block colour; text colour is chosen for contrast
    (black on lime/white, white on violet/black).
    """

    def __init__(self, caption, value, note="", tone="dark", parent=None):
        super().__init__(parent)
        self.setObjectName(
            {"dark": "card", "violet": "cardViolet", "white": "cardWhite", "lime": "cardLime"}[tone]
        )
        self.setMinimumHeight(168)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        text_name = "onLime" if tone in ("white", "lime") else "onViolet"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(8)

        self.caption_label = QLabel(caption.upper())
        self.caption_label.setObjectName("metricCaption" if tone != "white" else "onLime")
        if tone == "white":
            self.caption_label.setStyleSheet("color: #000000; font-size: 11px; font-weight: 800; letter-spacing: 2px;")
        elif tone == "lime":
            self.caption_label.setStyleSheet("color: #000000; font-size: 11px; font-weight: 800; letter-spacing: 2px;")

        self.value_label = QLabel(value)
        self.value_label.setObjectName("metricValueSmall" if len(value) > 15 else "metricValue")
        self.value_label.setObjectName(text_name)
        self.value_label.setStyleSheet(
            f"color: {'#000000' if tone in ('white', 'lime') else '#FFFFFF'};"
            f"font-size: {'22px' if len(value) > 15 else '34px'}; font-weight: 800;"
        )
        self.value_label.setWordWrap(True)

        self.note_label = QLabel(note)
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet(
            f"color: {'rgba(0,0,0,0.72)' if tone in ('white', 'lime') else 'rgba(255,255,255,0.78)'};"
            "font-size: 12px; font-weight: 600;"
        )

        layout.addWidget(self.caption_label)
        layout.addWidget(self.value_label, 1)
        layout.addWidget(self.note_label)
        self.tone = tone

    def set_value(self, value, note=None):
        self.value_label.setText(str(value))
        if note is not None:
            self.note_label.setText(str(note))


def code_panel(text, parent=None):
    """A read-only-looking path/code panel with a transparent text label."""
    frame = QFrame(parent)
    frame.setObjectName("code")
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(12, 10, 12, 10)
    label = QLabel(text)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    layout.addWidget(label)
    return frame


def page_header(title, subtitle):
    """Return a title + subtitle block for the top of a page."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    heading = QLabel(title)
    heading.setObjectName("title")
    sub = QLabel(subtitle)
    sub.setObjectName("subtitle")
    sub.setWordWrap(True)
    layout.addWidget(heading)
    layout.addWidget(sub)
    return widget


def field_label(text):
    """Small uppercase-style label that sits above an input."""
    label = QLabel(text)
    label.setObjectName("field")
    label.setWordWrap(True)
    return label


def styled_entry(placeholder=""):
    """A single-line input that matches the brand theme."""
    entry = QLineEdit()
    entry.setPlaceholderText(placeholder)
    return entry


def primary_button(text):
    button = QPushButton(text)
    button.setObjectName("primary")
    return button


def lime_button(text):
    button = QPushButton(text)
    button.setObjectName("lime")
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
    """Modal yes/no dialog. Constructing it shows and blocks until answered."""

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
        self.setMinimumWidth(420)
        self.setMaximumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(14)

        heading = QLabel(title)
        heading.setObjectName("title")
        heading.setStyleSheet("font-size: 19px;")
        heading.setWordWrap(True)
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
