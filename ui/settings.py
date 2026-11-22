"""Settings page - a placeholder with useful information about the app."""

import customtkinter as ctk

import database
from ui.theme import COLORS, card, font, page_header


class SettingsView(ctk.CTkFrame):
    """Milestone 1 keeps settings simple: information plus future plans."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._status_job = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # the card list takes the space

        header = page_header(
            self, "Settings", "App information and a look at what comes next."
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # The page scrolls when the window is short, so nothing gets clipped.
        self.body = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color="#344054",
        )
        self.body.grid(row=1, column=0, sticky="nsew")

        self._build_about().pack(fill="x", pady=(0, 12))
        self._build_storage().pack(fill="x", pady=(0, 12))
        self._build_coming_soon().pack(fill="x")

    def _build_about(self):
        about = card(self.body)
        about.grid_columnconfigure(0, minsize=150)
        about.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            about,
            text="About Pocket Ledger",
            font=font(14, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=24, pady=(16, 10))

        details = [
            ("Version", "0.2 · Desktop milestone 1"),
            ("Interface", "CustomTkinter (native Windows window)"),
            ("Storage", "SQLite database on this computer"),
            ("Currency", "Indian Rupee (₹)"),
            ("Theme", "Dark"),
        ]

        for index, (label, value) in enumerate(details, start=1):
            ctk.CTkLabel(
                about,
                text=label,
                font=font(11),
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=index, column=0, sticky="w", padx=24, pady=4)
            ctk.CTkLabel(
                about,
                text=value,
                font=font(12),
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=index, column=1, sticky="w", padx=(12, 24), pady=4)

        ctk.CTkFrame(about, fg_color="transparent", height=10).grid(
            row=len(details) + 1, column=0
        )
        return about

    def _build_storage(self):
        storage = card(self.body)
        storage.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            storage,
            text="Data location",
            font=font(14, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(16, 4))

        ctk.CTkLabel(
            storage,
            text=(
                "The desktop app and the Streamlit app share the same database "
                "file. Nothing is sent to the internet."
            ),
            font=font(11),
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=700,
        ).grid(row=1, column=0, sticky="w", padx=24)

        ctk.CTkLabel(
            storage,
            text=str(database.DB_PATH),
            font=font(10, family="Consolas"),
            text_color=COLORS["muted"],
            fg_color=COLORS["surface_alt"],
            corner_radius=8,
            anchor="w",
            justify="left",
            wraplength=640,
            padx=12,
            pady=8,
        ).grid(row=2, column=0, sticky="ew", padx=24, pady=(10, 0))

        actions = ctk.CTkFrame(storage, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=24, pady=(10, 14))
        actions.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            actions,
            text="",
            font=font(10),
            text_color=COLORS["success"],
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            actions,
            text="Copy path",
            width=104,
            height=32,
            corner_radius=9,
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            font=font(11),
            command=self._copy_path,
        ).grid(row=0, column=1, sticky="e")

        return storage

    def _build_coming_soon(self):
        coming = card(self.body)

        ctk.CTkLabel(
            coming,
            text="Coming in later milestones",
            font=font(14, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(anchor="w", padx=24, pady=(16, 6))

        plans = [
            "Dashboard totals for income, expenses and balance.",
            "Monthly reports and charts.",
            "Backup and restore for your database file.",
        ]

        for plan in plans:
            row = ctk.CTkFrame(coming, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=1)
            ctk.CTkLabel(
                row,
                text="•",
                font=font(12),
                text_color=COLORS["accent"],
                width=14,
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=plan,
                font=font(11),
                text_color=COLORS["muted"],
                anchor="w",
            ).pack(side="left")

        ctk.CTkFrame(coming, fg_color="transparent", height=12).pack()
        return coming

    def _copy_path(self):
        """Put the database path on the clipboard."""
        self.clipboard_clear()
        self.clipboard_append(str(database.DB_PATH))
        self.status_label.configure(text="Path copied to clipboard.")

        if self._status_job is not None:
            self.after_cancel(self._status_job)
        self._status_job = self.after(3000, self._clear_status)

    def _clear_status(self):
        self._status_job = None
        if self.status_label.winfo_exists():
            self.status_label.configure(text="")

    def destroy(self):
        if self._status_job is not None:
            try:
                self.after_cancel(self._status_job)
            except Exception:
                pass
            self._status_job = None
        super().destroy()
