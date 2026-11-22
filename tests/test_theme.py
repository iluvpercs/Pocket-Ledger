"""Theme regression tests for the Strawberry palette and label backgrounds."""

from PySide6.QtWidgets import QApplication, QLabel

from ui import theme


def _contrast(foreground, background):
    """WCAG contrast ratio for two hex colours."""

    def luminance(value):
        channels = [int(value[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        channels = [
            channel / 12.92
            if channel <= 0.03928
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    lighter, darker = sorted(
        (luminance(foreground), luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def test_theme_exposes_strawberry_palette_with_readable_button_text():
    assert theme.BACKGROUND == "#202125"
    assert theme.PRIMARY == "#F14666"
    assert theme.SECONDARY == "#EE8980"
    assert theme.HIGHLIGHT == "#FFCDAA"
    assert theme.POSITIVE == "#9CB898"
    assert theme.NEGATIVE == "#F14666"
    assert theme.TEXT == "#F7F3EF"
    assert theme.MUTED == "#C8BAB2"

    # Legacy names still resolve to the new palette.
    assert theme.COLORS["accent"] == theme.PRIMARY
    assert theme.COLORS["success"] == theme.POSITIVE
    assert theme.COLORS["danger"] == theme.NEGATIVE
    assert theme.COLORS["highlight"] == theme.HIGHLIGHT

    assert _contrast(theme.ON_ACCENT, theme.PRIMARY) >= 4.5
    assert _contrast(theme.ON_ACCENT, theme.SECONDARY) >= 4.5


def test_main_window_labels_have_transparent_backgrounds(qapp, temp_database):
    import desktop_app

    window = desktop_app.PocketLedgerApp()
    try:
        window.show()
        for page in ("transactions", "settings", "dashboard"):
            window.show_page(page)
        QApplication.processEvents()

        assert "QLabel { background: transparent; }" in theme.STYLESHEET
        labels = window.findChildren(QLabel)
        assert labels
        for label in labels:
            assert not label.autoFillBackground(), label.text()
            assert "background" not in label.styleSheet().lower(), label.text()
    finally:
        window.close()


def test_sidebar_text_fits_at_default_and_resized_sizes(qapp, temp_database):
    import desktop_app

    window = desktop_app.PocketLedgerApp()
    try:
        window.show()
        title = next(
            label
            for label in window.findChildren(QLabel)
            if label.text() == "Pocket Ledger"
        )

        for width, height in ((1180, 760), (1020, 680), (1400, 900)):
            window.resize(width, height)
            QApplication.processEvents()

            assert title.sizeHint().width() <= title.width()
            for button in window.nav_buttons.values():
                assert button.sizeHint().width() <= button.width(), button.text()
    finally:
        window.close()
