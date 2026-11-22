"""Pocket Ledger - desktop edition.

Run with:  python desktop_app.py

This window is built with CustomTkinter and uses the same database.py module
as the Streamlit version, so both apps share one local SQLite file. The
original Streamlit app (app.py) is untouched.
"""

import customtkinter as ctk

import database
from ui.dashboard import DashboardView
from ui.import_csv import ImportCsvDialog
from ui.settings import SettingsView
from ui.theme import COLORS, apply_theme, center_window, font
from ui.transactions import TransactionsView

APP_TITLE = "Pocket Ledger"
WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 760

# Each sidebar item points at the class that builds its page.
PAGES = {
    "dashboard": DashboardView,
    "transactions": TransactionsView,
    "settings": SettingsView,
}

NAV_ITEMS = (
    ("dashboard", "Dashboard"),
    ("transactions", "Transactions"),
    ("import", "Import CSV"),
    ("settings", "Settings"),
)


class PocketLedgerApp(ctk.CTk):
    """The main window: sidebar on the left, one page on the right."""

    def __init__(self):
        apply_theme()  # dark mode, before the window is created
        super().__init__()

        self.title(APP_TITLE)
        self.configure(fg_color=COLORS["window"])
        self.minsize(1020, 680)
        center_window(self, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.current_page = None
        self.nav_buttons = {}
        self.page_container = None
        self.import_dialog = None

        self.grid_columnconfigure(0, weight=0)  # sidebar keeps its width
        self.grid_columnconfigure(1, weight=1)  # page area grows
        self.grid_rowconfigure(0, weight=1)

        # Make sure the table exists before any page tries to read it.
        try:
            database.initialize_database()
        except Exception as error:
            self._show_database_error(error)
            return

        self._build_sidebar()
        self._build_page_container()
        self.show_page("dashboard")

    # --------------------------------------------------------------- sidebar
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self, fg_color=COLORS["sidebar"], corner_radius=0, width=236
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)  # keep the sidebar at 236 pixels wide
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(3, weight=1)  # spacer pushes the footer down

        # Brand: a small rupee badge plus the app name.
        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 26))
        brand.grid_columnconfigure(1, weight=1)

        logo = ctk.CTkFrame(
            brand, width=38, height=38, corner_radius=11, fg_color=COLORS["accent"]
        )
        logo.grid(row=0, column=0, rowspan=2, sticky="w")
        logo.grid_propagate(False)
        ctk.CTkLabel(
            logo, text="₹", font=font(18, "bold"), text_color="#FFFFFF"
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            brand,
            text="Pocket Ledger",
            font=font(16, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="sw", padx=(12, 0))
        ctk.CTkLabel(
            brand,
            text="Personal finance",
            font=font(10),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=1, sticky="nw", padx=(12, 0))

        ctk.CTkLabel(
            sidebar,
            text="MENU",
            font=font(9, "bold"),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 8))

        nav = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav.grid(row=2, column=0, sticky="ew", padx=14)
        nav.grid_columnconfigure(0, weight=1)

        for index, (key, label) in enumerate(NAV_ITEMS):
            button = ctk.CTkButton(
                nav,
                text=label,
                anchor="w",
                height=42,
                corner_radius=10,
                border_spacing=8,
                fg_color="transparent",
                hover_color=COLORS["surface_alt"],
                text_color=COLORS["muted"],
                font=font(12),
                command=lambda name=key: self.show_page(name),
            )
            button.grid(row=index, column=0, sticky="ew", pady=2)
            self.nav_buttons[key] = button

        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 22))
        ctk.CTkLabel(
            footer,
            text="Local data only",
            font=font(10, "bold"),
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            footer,
            text="Desktop · v0.2",
            font=font(9),
            text_color="#5C6678",
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

    # ------------------------------------------------------------- page area
    def _build_page_container(self):
        self.page_container = ctk.CTkFrame(self, fg_color="transparent")
        self.page_container.grid(
            row=0, column=1, sticky="nsew", padx=28, pady=24
        )
        self.page_container.grid_columnconfigure(0, weight=1)
        self.page_container.grid_rowconfigure(0, weight=1)

    def show_page(self, name):
        """Replace the current page and highlight its sidebar button."""
        if name == "import":  # this entry opens a dialog, not a nav page
            return self.open_import_dialog()

        view_class = PAGES.get(name)
        if view_class is None or self.page_container is None:
            return

        for widget in self.page_container.winfo_children():
            widget.destroy()

        for key, button in self.nav_buttons.items():
            if key == name:
                button.configure(
                    fg_color=COLORS["accent_soft"],
                    hover_color=COLORS["accent_soft"],
                    text_color=COLORS["accent"],
                )
            else:
                button.configure(
                    fg_color="transparent",
                    hover_color=COLORS["surface_alt"],
                    text_color=COLORS["muted"],
                )

        view = view_class(self.page_container, self)
        view.grid(row=0, column=0, sticky="nsew")
        self.current_page = name

    # ------------------------------------------------------------ CSV import
    def open_import_dialog(self):
        """Open (or focus) the CSV import dialog from the sidebar."""
        existing = self.import_dialog
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_force()
            return existing
        self.import_dialog = ImportCsvDialog(
            self, on_close=self._on_import_dialog_closed
        )
        return self.import_dialog

    def _on_import_dialog_closed(self):
        self.import_dialog = None

    # ----------------------------------------------------------- error screen
    def _show_database_error(self, error):
        """Shown only if SQLite itself cannot be opened."""
        panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            panel,
            text="The database could not be opened",
            font=font(18, "bold"),
            text_color=COLORS["danger"],
        ).pack(padx=32, pady=(28, 8))

        ctk.CTkLabel(
            panel,
            text=str(error),
            font=font(11),
            text_color=COLORS["muted"],
            wraplength=520,
            justify="left",
        ).pack(padx=32)

        ctk.CTkButton(
            panel,
            text="Close",
            width=110,
            height=38,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            font=font(12, "bold"),
            command=self.destroy,
        ).pack(pady=(22, 28))


def main():
    app = PocketLedgerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
