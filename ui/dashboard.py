"""Dashboard page - a friendly welcome screen for the desktop app."""

import customtkinter as ctk

from ui.theme import COLORS, card, font, page_header


class DashboardView(ctk.CTkFrame):
    """The first screen the user sees when the app opens."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)  # pushes everything to the top

        header = page_header(self, "Dashboard", "A calm overview of your money.")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))

        self._build_hero().grid(row=1, column=0, sticky="ew", pady=(0, 14))
        self._build_tips().grid(row=2, column=0, sticky="ew", pady=(0, 14))
        self._build_steps().grid(row=3, column=0, sticky="ew")

    def _build_hero(self):
        """Large welcome card with the main call to action."""
        hero = card(self)
        hero.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hero,
            text="WELCOME BACK",
            font=font(10, "bold"),
            text_color=COLORS["accent"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=28, pady=(26, 6))

        ctk.CTkLabel(
            hero,
            text="Your money, kept simple.",
            font=font(27, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=28)

        ctk.CTkLabel(
            hero,
            text=(
                "Record income and expenses in a few clicks. Everything is saved "
                "in a local file on this computer — no accounts, no cloud."
            ),
            font=font(12),
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=720,
        ).grid(row=2, column=0, sticky="w", padx=28, pady=(8, 22))

        ctk.CTkButton(
            hero,
            text="Add a transaction",
            width=176,
            height=40,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            font=font(12, "bold"),
            command=lambda: self.app.show_page("transactions"),
        ).grid(row=3, column=0, sticky="w", padx=28, pady=(0, 28))

        return hero

    def _build_tips(self):
        """Three small cards that explain the app's promises."""
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        for column in range(3):
            wrapper.grid_columnconfigure(column, weight=1, uniform="tips")

        tips = [
            ("Private by design", "Your transactions never leave this computer."),
            ("Rupees ready", "Every amount is shown in ₹ with two decimals."),
            ("Simple on purpose", "No accounts, no bank links, no clutter."),
        ]

        for column, (title, body) in enumerate(tips):
            tile = card(wrapper)
            tile.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 7, 0 if column == 2 else 7),
            )
            ctk.CTkLabel(
                tile,
                text=title,
                font=font(13, "bold"),
                text_color=COLORS["text"],
                anchor="w",
            ).pack(anchor="w", padx=20, pady=(18, 4))
            ctk.CTkLabel(
                tile,
                text=body,
                font=font(11),
                text_color=COLORS["muted"],
                anchor="w",
                justify="left",
                wraplength=210,
            ).pack(anchor="w", padx=20, pady=(0, 18))

        return wrapper

    def _build_steps(self):
        """A short getting-started checklist."""
        steps = card(self)

        ctk.CTkLabel(
            steps,
            text="Getting started",
            font=font(14, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(anchor="w", padx=24, pady=(18, 10))

        instructions = [
            "Add an income or expense on the Transactions page.",
            "Review everything you have saved in the table.",
            "Delete a mistake with the Delete button on its row.",
        ]

        for number, text in enumerate(instructions, start=1):
            row = ctk.CTkFrame(steps, fg_color="transparent")
            row.pack(fill="x", padx=24, pady=3)
            ctk.CTkLabel(
                row,
                text=str(number),
                font=font(10, "bold"),
                text_color=COLORS["accent"],
                fg_color=COLORS["accent_soft"],
                width=22,
                height=22,
                corner_radius=11,
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=text,
                font=font(12),
                text_color=COLORS["muted"],
                anchor="w",
            ).pack(side="left", padx=(10, 0))

        ctk.CTkFrame(steps, fg_color="transparent", height=14).pack()
        return steps
