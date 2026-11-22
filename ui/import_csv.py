"""CSV import dialog for the desktop app.

This file only builds widgets and calls ``importers.service``. Parsing,
duplicate detection and committing all stay in the importers package, so the
dialog can be tested and changed without touching the import rules.
"""

import sqlite3
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from importers import csv_parser, service
from ui.theme import COLORS, card, font, page_header, styled_entry
from utils.calculations import format_inr

FIELD_LABELS = {
    "date": "Date",
    "description": "Description",
    "amount": "Amount",
    "debit": "Debit / Withdrawal",
    "credit": "Credit / Deposit",
    "balance": "Balance",
    "reference": "Reference",
}

NONE_OPTION = "— none —"
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 760

ROW_COLUMNS = (
    ("", 0, 34),
    ("DATE", 0, 108),
    ("DESCRIPTION", 1, 220),
    ("CATEGORY", 0, 128),
    ("AMOUNT", 0, 110),
    ("STATUS", 0, 132),
)


def _status_style(status):
    if status == "duplicate":
        return "DUPLICATE", COLORS["muted"], COLORS["surface_alt"]
    if status == "previously_deleted":
        return "WAS DELETED", COLORS["muted"], COLORS["surface_alt"]
    if status == "error":
        return "ERROR", COLORS["danger"], COLORS["danger_soft"]
    if status == "warning":
        return "WARNING", COLORS["accent"], COLORS["accent_soft"]
    return "NEW", COLORS["success"], COLORS["success_soft"]


class ImportCsvDialog(ctk.CTkToplevel):
    """Choose a CSV, check the mapping, edit the preview, then import."""

    def __init__(self, parent, choose_file=None, on_close=None):
        super().__init__(parent)
        self.withdraw()  # build everything before showing the window

        self.title("Pocket Ledger · Import CSV")
        self.configure(fg_color=COLORS["window"])
        self.transient(parent.winfo_toplevel())
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(900, 620)
        self.protocol("WM_DELETE_WINDOW", self.close)

        self._choose_file = choose_file or self._ask_file
        self._on_close = on_close
        self.source_path = None
        self.parse_result = None
        self.preview = None
        self.mapping_vars = {}
        self.row_widgets = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build()

        self.update_idletasks()
        owner = parent.winfo_toplevel()
        x = owner.winfo_rootx() + max(0, (owner.winfo_width() - WINDOW_WIDTH) // 2)
        y = owner.winfo_rooty() + max(0, (owner.winfo_height() - WINDOW_HEIGHT) // 3)
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.deiconify()
        self.lift()
        self.focus_force()

    # ------------------------------------------------------------------ build
    def _build(self):
        body = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color="#344054",
        )
        body.grid(row=0, column=0, sticky="nsew", padx=18, pady=16)
        body.grid_columnconfigure(0, weight=1)

        page_header(
            body, "Import CSV", "Review every row before anything is saved."
        ).grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self._build_file_card(body).grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self._build_mapping_card(body).grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self._build_preview_card(body).grid(row=3, column=0, sticky="nsew")
        self._build_footer(body).grid(row=4, column=0, sticky="ew", pady=(12, 0))

        body.grid_rowconfigure(3, weight=1)

    def _build_file_card(self, parent):
        panel = card(parent)
        panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel,
            text="STATEMENT FILE",
            font=font(10, "bold"),
            text_color=COLORS["accent"],
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(14, 4))

        self.file_label = ctk.CTkLabel(
            panel,
            text="No file chosen yet.",
            font=font(11),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.file_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20)

        ctk.CTkButton(
            panel,
            text="Choose CSV…",
            width=132,
            height=34,
            corner_radius=9,
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            font=font(11, "bold"),
            command=self._choose_csv,
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(10, 14))

        self.detected_label = ctk.CTkLabel(
            panel,
            text="",
            font=font(10),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.detected_label.grid(row=2, column=1, sticky="e", padx=(8, 20), pady=(10, 14))
        return panel

    def _build_mapping_card(self, parent):
        panel = card(parent)
        panel.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(panel, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 4))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text="Column mapping",
            font=font(14, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            top,
            text="Re-read with these columns",
            width=196,
            height=30,
            corner_radius=9,
            fg_color=COLORS["accent_soft"],
            hover_color=COLORS["border"],
            text_color=COLORS["accent"],
            font=font(10, "bold"),
            command=self._remap,
        ).grid(row=0, column=1, sticky="e")

        self.mapping_grid = ctk.CTkFrame(panel, fg_color="transparent")
        self.mapping_grid.grid(row=1, column=0, sticky="ew", padx=20, pady=(2, 16))
        self.mapping_grid.grid_columnconfigure(0, weight=1)
        self.mapping_grid.grid_columnconfigure(2, weight=1)

        self.mapping_hint = ctk.CTkLabel(
            self.mapping_grid,
            text="Choose a statement to auto-detect the columns.",
            font=font(11),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.mapping_hint.grid(row=0, column=0, columnspan=4, sticky="w")
        return panel

    def _build_preview_card(self, parent):
        panel = card(parent)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)

        top = ctk.CTkFrame(panel, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 8))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text="Preview",
            font=font(14, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.counts_label = ctk.CTkLabel(
            top,
            text="0 rows",
            font=font(10, "bold"),
            text_color=COLORS["muted"],
            anchor="e",
        )
        self.counts_label.grid(row=0, column=1, sticky="e")

        header_row = ctk.CTkFrame(panel, fg_color="transparent")
        header_row.grid(row=1, column=0, sticky="ew", padx=(20, 36))
        for index, (title, weight, minimum) in enumerate(ROW_COLUMNS):
            header_row.grid_columnconfigure(index, weight=weight, minsize=minimum)
            ctk.CTkLabel(
                header_row,
                text=title,
                font=font(9, "bold"),
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=0, column=index, sticky="ew", padx=(0, 6))

        ctk.CTkFrame(panel, fg_color=COLORS["border"], height=1).grid(
            row=2, column=0, sticky="ew", padx=20
        )

        rows_frame = ctk.CTkScrollableFrame(
            panel,
            fg_color="transparent",
            corner_radius=0,
            height=230,
            scrollbar_fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color="#344054",
        )
        rows_frame.grid(row=3, column=0, sticky="nsew", padx=(20, 12), pady=(6, 4))
        self.rows_container = ctk.CTkFrame(rows_frame, fg_color="transparent")
        self.rows_container.pack(fill="x")
        self.rows_container.grid_columnconfigure(0, weight=1)

        self.preview_hint = ctk.CTkLabel(
            panel,
            text="Load a statement to see its rows here.",
            font=font(11),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.preview_hint.grid(row=3, column=0, sticky="nw", padx=24, pady=24)
        return panel

    def _build_footer(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        panel.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            panel,
            text="",
            font=font(11),
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=620,
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        self.totals_label = ctk.CTkLabel(
            panel,
            text="",
            font=font(10),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.totals_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        ctk.CTkButton(
            panel,
            text="Cancel",
            width=100,
            height=38,
            corner_radius=10,
            fg_color=COLORS["surface_alt"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            font=font(11),
            command=self.close,
        ).grid(row=0, column=1, sticky="e", padx=(8, 0))

        self.import_button = ctk.CTkButton(
            panel,
            text="Import 0 transactions",
            width=190,
            height=38,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            font=font(11, "bold"),
            command=self._confirm,
        )
        self.import_button.grid(row=1, column=1, sticky="e", padx=(8, 0), pady=(4, 0))
        return panel

    # ------------------------------------------------------------------ files
    @staticmethod
    def _ask_file(parent=None):
        return filedialog.askopenfilename(
            title="Choose a CSV statement",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
            parent=parent,
        )

    def _choose_csv(self):
        chosen = self._choose_file()
        if not chosen:
            return
        self.source_path = Path(chosen)
        self.file_label.configure(text=str(self.source_path))
        self._load(reuse_mapping=False)

    def _remap(self):
        if self.source_path is None:
            self._set_status("Choose a CSV file first.", "error")
            return
        self._load(reuse_mapping=True)

    def _load(self, reuse_mapping=False):
        self._set_status("Reading statement…")
        override = self._selected_mapping() if reuse_mapping else None
        try:
            parsed = csv_parser.parse_csv(self.source_path, mapping=override)
            if not parsed.ok:
                self._set_status(parsed.error or "This file could not be read.", "error")
                return
            self.preview = service.build_preview(
                parsed, source_file=str(self.source_path)
            )
        except (OSError, ValueError, sqlite3.Error) as error:
            self._set_status(str(error), "error")
            return

        self.parse_result = parsed
        self._render_mapping()
        self._render_rows()
        self._set_status(
            f"Detected {csv_parser.date_format_label(parsed.date_format)} dates and "
            f"'{parsed.delimiter.strip() or 'tab'}' separator. Review the rows below."
        )

    def _selected_mapping(self):
        if not self.parse_result:
            return None
        header = self.parse_result.header
        override = {}
        for field_name, variable in self.mapping_vars.items():
            selected = variable.get()
            if selected == NONE_OPTION:
                override[field_name] = None
            elif selected in header:
                override[field_name] = header.index(selected)
        return override

    def _render_mapping(self):
        for widget in self.mapping_grid.winfo_children():
            widget.destroy()
        self.mapping_vars.clear()

        header = self.parse_result.header
        options = [NONE_OPTION] + header
        for index, field_name in enumerate(csv_parser.FIELDS):
            row = index // 2
            column = (index % 2) * 2
            ctk.CTkLabel(
                self.mapping_grid,
                text=FIELD_LABELS[field_name],
                font=font(10),
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=row, column=column, sticky="w", padx=(0, 8), pady=3)

            detected = self.preview.mapping.get(field_name)
            initial = header[detected] if detected is not None and detected < len(header) else NONE_OPTION
            variable = ctk.StringVar(value=initial)
            self.mapping_vars[field_name] = variable
            ctk.CTkComboBox(
                self.mapping_grid,
                values=options,
                variable=variable,
                state="readonly",
                width=190,
                height=30,
                font=font(10),
                dropdown_font=font(10),
            ).grid(row=row, column=column + 1, sticky="ew", padx=(0, 14), pady=3)

    # ------------------------------------------------------------------ preview
    def _render_rows(self):
        for widget in self.rows_container.winfo_children():
            widget.destroy()
        self.row_widgets.clear()

        if not self.preview.rows:
            self.preview_hint.configure(text="No transaction rows were found in this CSV.")
            self.preview_hint.grid()
        else:
            self.preview_hint.grid_remove()

        for index, row in enumerate(self.preview.rows):
            widgets = self._build_row(index, row)
            self.row_widgets.append(widgets)

        self._refresh_footer()

    def _build_row(self, index, row):
        frame = ctk.CTkFrame(self.rows_container, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        for column, (_, weight, minimum) in enumerate(ROW_COLUMNS):
            frame.grid_columnconfigure(column, weight=weight, minsize=minimum)

        include = ctk.BooleanVar(value=row.included)
        checkbox = ctk.CTkCheckBox(
            frame,
            text="",
            variable=include,
            width=26,
            height=26,
            corner_radius=6,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            command=lambda i=index, v=include: self._on_include(i, v),
        )
        checkbox.grid(row=0, column=0, sticky="w")
        if not row.importable:
            checkbox.configure(state="disabled")

        entries = []
        for column, value, width in (
            (1, row.date or "", 100),
            (2, row.description, 210),
            (3, row.category, 120),
            (4, str(row.amount) if row.amount is not None else "", 100),
        ):
            entry = styled_entry(frame, height=30)
            entry.configure(width=width)
            entry.insert(0, value)
            entry.grid(row=0, column=column, sticky="ew", padx=(0, 6))
            entry.bind("<FocusOut>", lambda event, i=index: self._on_edit(i))
            entries.append(entry)

        label_text, colour, background = _status_style(row.duplicate_status)
        if row.status in ("error", "warning"):
            label_text, colour, background = _status_style(row.status)
        badge = ctk.CTkLabel(
            frame,
            text=label_text,
            font=font(9, "bold"),
            text_color=colour,
            fg_color=background,
            corner_radius=8,
            width=90,
            height=22,
        )
        badge.grid(row=0, column=5, sticky="w")

        return {"checkbox": checkbox, "include": include, "entries": entries, "badge": badge}

    def _on_include(self, index, variable):
        if self.preview is None:
            return
        service.apply_edits(self.preview, index, included=variable.get())
        self._refresh_footer()

    def _on_edit(self, index):
        if self.preview is None or index >= len(self.row_widgets):
            return
        widgets = self.row_widgets[index]
        date_entry, description_entry, category_entry, amount_entry = widgets["entries"]
        row = service.apply_edits(
            self.preview,
            index,
            date=date_entry.get(),
            description=description_entry.get(),
            category=category_entry.get(),
            amount=amount_entry.get(),
        )
        label_text, colour, background = _status_style(row.duplicate_status)
        if row.status in ("error", "warning"):
            label_text, colour, background = _status_style(row.status)
        widgets["badge"].configure(
            text=label_text, text_color=colour, fg_color=background
        )
        if row.status == "error":
            widgets["checkbox"].configure(state="disabled")
        self._refresh_footer()

    def _refresh_footer(self):
        if self.preview is None:
            return
        counts = service.preview_counts(self.preview)
        totals = service.preview_totals(self.preview)
        self.counts_label.configure(
            text=(
                f"{counts['total']} rows · {counts['included']} included · "
                f"{counts['duplicates']} duplicates · {counts['errors']} errors"
            )
        )
        self.totals_label.configure(
            text=(
                f"Included: {format_inr(totals['income'])} in · "
                f"{format_inr(totals['expense'])} out · net {format_inr(totals['net'])}"
            )
        )
        self.import_button.configure(
            text=f"Import {counts['included']} transaction"
            + ("s" if counts["included"] != 1 else "")
        )

    # ----------------------------------------------------------------- actions
    def _confirm(self):
        if self.preview is None:
            self._set_status("Choose a CSV file first.", "error")
            return
        for index in range(len(self.preview.rows)):
            self._on_edit(index)
        try:
            summary = service.commit_preview(self.preview)
        except (ValueError, sqlite3.Error) as error:
            self._set_status(f"Import failed; nothing was saved. {error}", "error")
            return
        self._show_summary(summary)

    def _show_summary(self, summary):
        result = ctk.CTkToplevel(self)
        result.withdraw()
        result.title("Pocket Ledger · Import complete")
        result.configure(fg_color=COLORS["window"])
        result.resizable(False, False)
        result.transient(self)
        result.protocol("WM_DELETE_WINDOW", result.destroy)

        panel = card(result)
        panel.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        result.grid_columnconfigure(0, weight=1)
        result.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text="Import complete",
            font=font(17, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 10))

        lines = [
            f"Imported: {summary.imported}",
            f"Skipped duplicates: {summary.skipped_duplicates}",
            f"Excluded: {summary.excluded}",
            f"Errors: {summary.errors}",
        ]
        for offset, line in enumerate(lines, start=1):
            ctk.CTkLabel(
                panel,
                text=line,
                font=font(12),
                text_color=COLORS["muted"] if offset > 1 else COLORS["success"],
                anchor="w",
            ).grid(row=offset, column=0, sticky="w", padx=24, pady=2)

        ctk.CTkButton(
            panel,
            text="Done",
            width=110,
            height=36,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#FFFFFF",
            font=font(11, "bold"),
            command=lambda: (result.destroy(), self.close()),
        ).grid(row=len(lines) + 1, column=0, sticky="e", padx=24, pady=(18, 20))

        result.update_idletasks()
        result.geometry("+%d+%d" % (self.winfo_rootx() + 180, self.winfo_rooty() + 160))
        result.deiconify()
        result.lift()
        result.focus_force()

    def _set_status(self, message, kind="info"):
        colour = {
            "info": COLORS["muted"],
            "error": COLORS["danger"],
            "success": COLORS["success"],
        }[kind]
        self.status_label.configure(text=message, text_color=colour)

    def close(self):
        """Close the dialog and let the main window forget about it."""
        callback = self._on_close
        self.destroy()
        if callback is not None:
            callback()
