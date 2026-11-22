"""Transactions page - add, list and delete transactions.

All database work is delegated to database.py. This file only deals with
widgets, layout and showing friendly messages to the user.
"""

import sqlite3
from datetime import date, datetime

import customtkinter as ctk

import database
from ui.theme import (
    COLORS,
    ConfirmDialog,
    card,
    field_label,
    font,
    page_header,
    styled_entry,
)
from utils.calculations import format_inr

# Each column: (heading, stretch weight, minimum width, text alignment).
# The description column stretches to use any extra space.
COLUMNS = (
    ("DATE", 0, 96, "w"),
    ("TYPE", 0, 84, "w"),
    ("CATEGORY", 0, 118, "w"),
    ("DESCRIPTION", 1, 150, "w"),
    ("AMOUNT", 0, 116, "e"),
    ("", 0, 68, "e"),
)

ROW_FONT_SIZE = 11


def _format_date(iso_date):
    """Turn "2026-11-22" into "22 Nov 2026" for easier reading."""
    try:
        return datetime.strptime(str(iso_date), "%Y-%m-%d").strftime("%d %b %Y")
    except (TypeError, ValueError):
        return str(iso_date)  # if the date is unusual, show it as stored


def _shorten(text, limit=46):
    """Keep long descriptions from pushing the table out of shape."""
    text = str(text or "")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _configure_columns(frame):
    """Apply the same column sizes to the header row and every data row."""
    for index, (_, weight, minimum, _) in enumerate(COLUMNS):
        frame.grid_columnconfigure(index, weight=weight, minsize=minimum)


class TransactionsView(ctk.CTkFrame):
    """The page where money is added and reviewed."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._status_job = None  # id of the pending "clear message" timer

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # the table takes the extra space

        header = page_header(
            self, "Transactions", "Record money coming in and going out."
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self._build_form().grid(row=1, column=0, sticky="ew", pady=(0, 16))
        self._build_table().grid(row=2, column=0, sticky="nsew")

        self.refresh()

    # ------------------------------------------------------------------ form
    def _build_form(self):
        """Build the card that adds a new income or expense."""
        form = card(self)
        form.grid_columnconfigure(0, weight=1, uniform="form")
        form.grid_columnconfigure(1, weight=1, uniform="form")

        ctk.CTkLabel(
            form,
            text="Add a transaction",
            font=font(15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=24, pady=(14, 8))

        left_pad = (24, 8)
        right_pad = (8, 24)

        # Row 1-2: transaction type and amount.
        field_label(form, "TYPE").grid(row=1, column=0, sticky="w", padx=left_pad)
        self.type_control = ctk.CTkSegmentedButton(
            form,
            values=["Expense", "Income"],
            height=38,
            corner_radius=10,
            border_width=2,
            fg_color=COLORS["surface_alt"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["surface_alt"],
            unselected_hover_color=COLORS["border"],
            text_color=COLORS["text"],
            font=font(12),
        )
        self.type_control.set("Expense")
        self.type_control.grid(
            row=2, column=0, sticky="ew", padx=left_pad, pady=(4, 8)
        )

        field_label(form, "AMOUNT (₹)").grid(row=1, column=1, sticky="w", padx=right_pad)
        self.amount_entry = styled_entry(form, "0.00")
        self.amount_entry.grid(
            row=2, column=1, sticky="ew", padx=right_pad, pady=(4, 8)
        )

        # Row 3-4: category and date.
        field_label(form, "CATEGORY").grid(row=3, column=0, sticky="w", padx=left_pad)
        self.category_entry = styled_entry(form, "e.g. Food, Rent, Salary")
        self.category_entry.grid(
            row=4, column=0, sticky="ew", padx=left_pad, pady=(4, 8)
        )

        field_label(form, "DATE (YYYY-MM-DD)").grid(
            row=3, column=1, sticky="w", padx=right_pad
        )
        self.date_entry = styled_entry(form)
        self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.grid(
            row=4, column=1, sticky="ew", padx=right_pad, pady=(4, 8)
        )

        # Row 5-6: description spans the full width.
        field_label(form, "DESCRIPTION (OPTIONAL)").grid(
            row=5, column=0, columnspan=2, sticky="w", padx=24
        )
        self.description_entry = styled_entry(form, "e.g. Lunch with friends")
        self.description_entry.grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=24, pady=(4, 10)
        )

        # Row 7: inline status message on the left, button on the right.
        self.status_label = ctk.CTkLabel(
            form,
            text="",
            font=font(11),
            text_color=COLORS["success"],
            anchor="w",
            justify="left",
            wraplength=460,
        )
        self.status_label.grid(row=7, column=0, sticky="w", padx=(24, 8), pady=(0, 12))

        ctk.CTkButton(
            form,
            text="Add transaction",
            width=168,
            height=40,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            font=font(12, "bold"),
            command=self._on_add,
        ).grid(row=7, column=1, sticky="e", padx=(8, 24), pady=(0, 12))

        # Pressing Enter in any field adds the transaction.
        for entry in (
            self.amount_entry,
            self.category_entry,
            self.description_entry,
            self.date_entry,
        ):
            entry.bind("<Return>", lambda event: self._on_add())

        return form

    # ----------------------------------------------------------------- table
    def _build_table(self):
        """Build the card that lists every saved transaction."""
        table = card(self)
        table.grid_columnconfigure(0, weight=1)
        table.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(table, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(14, 8))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text="Saved transactions",
            font=font(14, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.count_label = ctk.CTkLabel(
            top,
            text="",
            font=font(10, "bold"),
            text_color=COLORS["muted"],
            fg_color=COLORS["surface_alt"],
            corner_radius=8,
            height=24,
            width=86,
        )
        self.count_label.grid(row=0, column=1, sticky="e")

        # Only shown when reading from the database fails.
        self.error_label = ctk.CTkLabel(
            table,
            text="",
            font=font(11),
            text_color=COLORS["danger"],
            fg_color=COLORS["danger_soft"],
            corner_radius=8,
            anchor="w",
            justify="left",
            wraplength=760,
        )
        self.error_label.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
        self.error_label.grid_remove()

        body = ctk.CTkFrame(table, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 12))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(2, weight=1)

        header_row = ctk.CTkFrame(body, fg_color="transparent")
        # A little right padding keeps the headings lined up with the rows,
        # because the scrollbar takes some width from the list below.
        header_row.grid(row=0, column=0, sticky="ew", padx=(0, 16))
        _configure_columns(header_row)

        for index, (title, _, _, anchor) in enumerate(COLUMNS):
            ctk.CTkLabel(
                header_row,
                text=title,
                font=font(9, "bold"),
                text_color=COLORS["muted"],
                anchor=anchor,
            ).grid(row=0, column=index, sticky="ew", padx=(0, 6))

        ctk.CTkFrame(body, fg_color=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", pady=(8, 4)
        )

        self.rows_frame = ctk.CTkScrollableFrame(
            body,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color="#344054",
        )
        self.rows_frame.grid(row=2, column=0, sticky="nsew")

        # Rows are rebuilt inside this container whenever the data changes.
        # (The scrollable frame itself also owns internal widgets, so we never
        # clear the scrollable frame directly.)
        self.rows_container = ctk.CTkFrame(self.rows_frame, fg_color="transparent")
        self.rows_container.pack(fill="x")

        return table

    # ---------------------------------------------------------------- data
    def refresh(self):
        """Reload transactions from the database and rebuild the table."""
        for widget in self.rows_container.winfo_children():
            widget.destroy()

        try:
            transactions = database.get_all_transactions()
        except sqlite3.Error as error:
            self._show_error(f"Could not load transactions: {error}")
            return

        self._hide_error()

        count = len(transactions)
        self.count_label.configure(text=f"{count} entr{'y' if count == 1 else 'ies'}")

        if not transactions:
            self._show_empty_state()
            return

        for transaction in transactions:
            self._build_row(transaction)

    def _build_row(self, transaction):
        """One table row, with a delete button for that transaction."""
        is_income = transaction["transaction_type"] == "income"
        amount_colour = COLORS["success"] if is_income else COLORS["danger"]

        row = ctk.CTkFrame(self.rows_container, fg_color="transparent", corner_radius=8)
        row.pack(fill="x")
        _configure_columns(row)

        ctk.CTkLabel(
            row,
            text=_format_date(transaction["transaction_date"]),
            font=font(ROW_FONT_SIZE),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=8)

        ctk.CTkLabel(
            row,
            text="Income" if is_income else "Expense",
            font=font(9, "bold"),
            text_color=amount_colour,
            fg_color=COLORS["success_soft"] if is_income else COLORS["danger_soft"],
            corner_radius=8,
            width=68,
            height=24,
        ).grid(row=0, column=1, sticky="w", pady=6)

        ctk.CTkLabel(
            row,
            text=transaction["category"],
            font=font(12),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=2, sticky="ew", padx=(0, 8), pady=8)

        ctk.CTkLabel(
            row,
            text=_shorten(transaction["description"]),
            font=font(11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=3, sticky="ew", padx=(0, 8), pady=8)

        ctk.CTkLabel(
            row,
            text=("+" if is_income else "−") + format_inr(transaction["amount"]),
            font=font(12, "bold"),
            text_color=amount_colour,
            anchor="e",
        ).grid(row=0, column=4, sticky="e", padx=(0, 10), pady=8)

        ctk.CTkButton(
            row,
            text="Delete",
            width=64,
            height=26,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["danger_soft"],
            text_color=COLORS["muted"],
            font=font(10),
            command=lambda item=transaction: self._confirm_delete(item),
        ).grid(row=0, column=5, sticky="e", pady=6)

        # Thin divider between rows.
        ctk.CTkFrame(self.rows_container, fg_color=COLORS["border"], height=1).pack(
            fill="x"
        )

    def _show_empty_state(self):
        empty = ctk.CTkFrame(self.rows_container, fg_color="transparent")
        empty.pack(fill="x", pady=46)

        ctk.CTkLabel(
            empty,
            text="No transactions yet",
            font=font(14, "bold"),
            text_color=COLORS["text"],
        ).pack()
        ctk.CTkLabel(
            empty,
            text="Add your first income or expense using the form above.",
            font=font(11),
            text_color=COLORS["muted"],
        ).pack(pady=(4, 0))

    # -------------------------------------------------------------- actions
    def _on_add(self):
        """Validate the form through database.py and save the transaction."""
        transaction_type = self.type_control.get().lower()
        amount_text = self.amount_entry.get().strip()
        category = self.category_entry.get().strip()
        description = self.description_entry.get().strip()
        transaction_date = self.date_entry.get().strip()

        try:
            database.add_transaction(
                transaction_type=transaction_type,
                amount=amount_text,
                category=category,
                description=description,
                transaction_date=transaction_date,
            )
        except ValueError as error:
            # database.py already wrote a friendly message for the user.
            self._set_status(str(error), "error")
            self._focus_problem_field(str(error))
            return
        except sqlite3.Error as error:
            self._set_status(f"Could not save the transaction: {error}", "error")
            return

        # Clear the fields and leave the date ready for the next entry.
        self.amount_entry.delete(0, "end")
        self.category_entry.delete(0, "end")
        self.description_entry.delete(0, "end")
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, date.today().isoformat())

        self.refresh()
        self._set_status(
            f"{transaction_type.title()} of {format_inr(amount_text)} added.",
            "success",
        )
        self.amount_entry.focus_set()

    def _confirm_delete(self, transaction):
        """Ask for confirmation before removing a transaction."""
        details = (
            f"{transaction['transaction_type'].title()} · "
            f"{format_inr(transaction['amount'])} · {transaction['category']}\n"
            f"{_format_date(transaction['transaction_date'])}"
        )
        if transaction["description"]:
            details += f"\n{transaction['description']}"

        ConfirmDialog(
            self,
            title="Delete this transaction?",
            message=f"{details}\n\nThis cannot be undone.",
            confirm_text="Delete",
            on_confirm=lambda: self._delete(transaction["id"]),
        )

    def _delete(self, transaction_id):
        """Delete one row and refresh the table."""
        try:
            deleted = database.delete_transaction(transaction_id)
        except sqlite3.Error as error:
            self._set_status(f"Could not delete the transaction: {error}", "error")
            return

        self.refresh()

        if deleted:
            self._set_status("Transaction deleted.", "success")
        else:
            self._set_status("That transaction was already removed.", "error")

    # --------------------------------------------------------------- helpers
    def _set_status(self, message, kind="success"):
        """Show a short message under the form, then clear it automatically."""
        colour = COLORS["success"] if kind == "success" else COLORS["danger"]
        self.status_label.configure(text=message, text_color=colour)

        if self._status_job is not None:
            self.after_cancel(self._status_job)
        self._status_job = self.after(5000, self._clear_status)

    def _clear_status(self):
        self._status_job = None
        if self.status_label.winfo_exists():
            self.status_label.configure(text="")

    def _focus_problem_field(self, message):
        """Move the cursor to the field mentioned in the error message."""
        if message.startswith("Amount"):
            self.amount_entry.focus_set()
        elif message.startswith("Category"):
            self.category_entry.focus_set()
        elif message.startswith("Date"):
            self.date_entry.focus_set()

    def _show_error(self, message):
        self.error_label.configure(text=message)
        self.error_label.grid()

    def _hide_error(self):
        self.error_label.grid_remove()

    def destroy(self):
        """Cancel any pending timer before the page is removed."""
        if self._status_job is not None:
            try:
                self.after_cancel(self._status_job)
            except Exception:
                pass
            self._status_job = None
        super().destroy()
