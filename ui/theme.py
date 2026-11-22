"""Shared colours, fonts and widgets for the desktop interface.

Every screen imports its colours and fonts from here. That keeps the whole app
consistent and means you can restyle it by editing this one file.
"""

import customtkinter as ctk

# --- Colour palette -------------------------------------------------------
# A dark, low-contrast palette inspired by modern banking apps.
COLORS = {
    "window": "#0B0E13",        # app background
    "sidebar": "#0E1218",       # sidebar background
    "surface": "#141A22",       # cards
    "surface_alt": "#1A2230",   # inputs and hover states
    "border": "#232C3A",        # thin outlines
    "text": "#E9EDF5",          # main text
    "muted": "#8A94A6",         # secondary text
    "accent": "#4C8DFF",        # primary action colour
    "accent_hover": "#3D7BEB",
    "accent_soft": "#16233B",   # tinted background for active items
    "success": "#3DDC97",       # income
    "success_soft": "#10281F",
    "danger": "#F87171",        # expenses and destructive actions
    "danger_solid": "#E5484D",  # solid delete button
    "danger_solid_hover": "#C93C41",
    "danger_soft": "#2A151A",
}

FONT_FAMILY = "Segoe UI"


# --- Theme helpers --------------------------------------------------------

def apply_theme():
    """Turn on dark mode. Call this once before creating the main window."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def font(size=13, weight="normal", family=FONT_FAMILY):
    """Create a font. Fonts must be created after the Tk window exists."""
    return ctk.CTkFont(family=family, size=size, weight=weight)


def center_window(window, width, height):
    """Place the main window in the middle of the screen."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 3)
    window.geometry(f"{width}x{height}+{x}+{y}")


def card(parent, **options):
    """A rounded panel used for every section of the interface."""
    settings = {
        "fg_color": COLORS["surface"],
        "corner_radius": 18,
        "border_width": 1,
        "border_color": COLORS["border"],
    }
    settings.update(options)
    return ctk.CTkFrame(parent, **settings)


def page_header(parent, title, subtitle):
    """Return a title + subtitle block for the top of a page."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(
        frame, text=title, font=font(24, "bold"), text_color=COLORS["text"], anchor="w"
    ).pack(anchor="w")
    ctk.CTkLabel(
        frame, text=subtitle, font=font(12), text_color=COLORS["muted"], anchor="w"
    ).pack(anchor="w", pady=(2, 0))
    return frame


def field_label(parent, text):
    """Small uppercase-style label that sits above an input."""
    return ctk.CTkLabel(
        parent, text=text, font=font(11, "bold"), text_color=COLORS["muted"], anchor="w"
    )


def styled_entry(parent, placeholder="", **options):
    """An entry box that matches the dark theme."""
    settings = {
        "height": 38,
        "corner_radius": 10,
        "fg_color": COLORS["surface_alt"],
        "border_width": 1,
        "border_color": COLORS["border"],
        "text_color": COLORS["text"],
        "placeholder_text_color": COLORS["muted"],
        "font": font(12),
    }
    settings.update(options)
    return ctk.CTkEntry(parent, placeholder_text=placeholder, **settings)


class ConfirmDialog(ctk.CTkToplevel):
    """A small dark dialog that asks the user to confirm an action.

    The caller passes a function as ``on_confirm``. It runs only when the user
    clicks the confirm button, so nothing is deleted by accident.
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

        self.withdraw()  # build everything before showing the window
        self.title("Pocket Ledger")
        self.configure(fg_color=COLORS["window"])
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())  # keep it above the main window
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        # Let the card fill the whole dialog window.
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        panel = card(self)
        panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text=title,
            font=font(17, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 8))

        ctk.CTkLabel(
            panel,
            text=message,
            font=font(12),
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=380,
        ).grid(row=1, column=0, sticky="ew", padx=24)

        buttons = ctk.CTkFrame(panel, fg_color="transparent")
        buttons.grid(row=2, column=0, sticky="e", padx=24, pady=(20, 22))

        ctk.CTkButton(
            buttons,
            text=cancel_text,
            width=96,
            height=36,
            corner_radius=10,
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            font=font(12),
            command=self._cancel,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            buttons,
            text=confirm_text,
            width=110,
            height=36,
            corner_radius=10,
            fg_color=COLORS["danger_solid"],
            hover_color=COLORS["danger_solid_hover"],
            text_color="#FFFFFF",
            font=font(12, "bold"),
            command=self._confirm,
        ).pack(side="left")

        # Escape cancels and Enter confirms, like most desktop dialogs.
        self.bind("<Escape>", lambda event: self._cancel())
        self.bind("<Return>", lambda event: self._confirm())

        # Work out the height, then centre the dialog over the main window.
        self.update_idletasks()
        width = 460
        height = max(210, self.winfo_reqheight())
        owner = parent.winfo_toplevel()
        x = owner.winfo_rootx() + (owner.winfo_width() - width) // 2
        y = owner.winfo_rooty() + (owner.winfo_height() - height) // 3
        self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

        self.deiconify()
        self.lift()
        self.focus_force()
        self.after(120, self._grab_focus)

    def _grab_focus(self):
        """Make the dialog modal once it is visible."""
        try:
            self.grab_set()
        except Exception:
            pass

    def _confirm(self):
        callback = self._on_confirm
        self.destroy()
        if callback is not None:
            callback()

    def _cancel(self):
        self.destroy()
