"""CSV import dialog for the desktop app (PySide6 port).

Only widgets live here: parsing, duplicate detection and committing are still
owned by ``importers.service``. The preview uses a Qt table model, so a large
statement does not create thousands of widgets.
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
)

from importers import csv_parser, service
from ui.models import ImportPreviewModel
from ui.theme import BadgeLabel, card, field_label, page_header, primary_button
from ui.workers import run_database_task
from utils.calculations import format_inr

def _parse_and_preview(path, mapping=None):
    """File read + duplicate check, always called in a worker thread."""
    parsed = csv_parser.parse_csv(path, mapping=mapping)
    if not parsed.ok:
        raise ValueError(parsed.error or "This file could not be read.")
    preview = service.build_preview(parsed, source_file=str(path))
    return parsed, preview


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


class ImportCsvDialog(QDialog):
    """Choose a CSV, check the mapping, edit the preview, then import."""

    def __init__(self, parent, choose_file=None, on_close=None):
        super().__init__(parent)
        self.setWindowTitle("Pocket Ledger · Import CSV")
        self.resize(1080, 760)
        self.setMinimumSize(900, 620)

        self._choose_file = choose_file or self._ask_file
        self._on_close = on_close
        self.source_path = None
        self.parse_result = None
        self.preview = None
        self.mapping_vars = {}

        self._build()
        self._set_status("Choose a CSV statement to begin.")

    # ------------------------------------------------------------------ build
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(page_header("Import CSV", "Review every row before anything is saved."))
        layout.addWidget(self._build_file_card())
        layout.addWidget(self._build_mapping_card())
        layout.addWidget(self._build_preview_card(), 1)
        layout.addLayout(self._build_footer())

    def _build_file_card(self):
        panel = card()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(6)
        caption = QLabel("STATEMENT FILE")
        caption.setObjectName("accent")
        self.file_label = QLabel("No file chosen yet.")
        self.file_label.setObjectName("muted")
        actions = QHBoxLayout()
        choose = QPushButton("Choose CSV…")
        choose.clicked.connect(self._choose_csv)
        self.detected_label = QLabel("")
        self.detected_label.setObjectName("muted")
        actions.addWidget(choose)
        actions.addStretch(1)
        actions.addWidget(self.detected_label)
        layout.addWidget(caption)
        layout.addWidget(self.file_label)
        layout.addLayout(actions)
        return panel

    def _build_mapping_card(self):
        panel = card()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(8)
        top = QHBoxLayout()
        heading = QLabel("Column mapping")
        heading.setStyleSheet("font-size: 14px; font-weight: 700;")
        remap = QPushButton("Re-read with these columns")
        remap.clicked.connect(self._remap)
        top.addWidget(heading)
        top.addStretch(1)
        top.addWidget(remap)
        layout.addLayout(top)

        self.mapping_grid = QFormLayout()
        self.mapping_grid.setHorizontalSpacing(14)
        self.mapping_grid.setVerticalSpacing(4)
        self.mapping_hint = QLabel("Choose a statement to auto-detect the columns.")
        self.mapping_hint.setObjectName("muted")
        layout.addLayout(self.mapping_grid)
        layout.addWidget(self.mapping_hint)
        return panel

    def _build_preview_card(self):
        panel = card()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(8)
        top = QHBoxLayout()
        heading = QLabel("Preview")
        heading.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.counts_label = BadgeLabel("0 rows")
        self.counts_label.setObjectName("badge")
        top.addWidget(heading)
        top.addStretch(1)
        top.addWidget(self.counts_label)
        layout.addLayout(top)

        self.preview_model = ImportPreviewModel()
        self.table = QTableView()
        self.table.setModel(self.preview_model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(2, 240)
        self.table.setColumnWidth(3, 130)
        self.preview_model.dataChanged.connect(self._refresh_footer)
        layout.addWidget(self.table, 1)
        return panel

    def _build_footer(self):
        panel = QVBoxLayout()
        panel.setSpacing(3)
        self.status_label = QLabel("")
        self.status_label.setObjectName("muted")
        self.status_label.setWordWrap(True)
        self.totals_label = QLabel("")
        self.totals_label.setObjectName("muted")
        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.close)
        self.import_button = primary_button("Import 0 transactions")
        self.import_button.clicked.connect(self._confirm)
        actions.addWidget(cancel)
        actions.addWidget(self.import_button)
        panel.addWidget(self.status_label)
        panel.addWidget(self.totals_label)
        panel.addLayout(actions)
        return panel

    # ------------------------------------------------------------------ files
    def _ask_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose a CSV statement",
            "",
            "CSV files (*.csv *.txt);;All files (*.*)",
        )
        return path

    def _choose_csv(self):
        chosen = self._choose_file()
        if not chosen:
            return
        self.source_path = Path(chosen)
        self.file_label.setText(str(self.source_path))
        self._load(reuse_mapping=False)

    def _remap(self):
        if self.source_path is None:
            self._set_status("Choose a CSV file first.", "error")
            return
        self._load(reuse_mapping=True)

    def _load(self, reuse_mapping=False):
        self._set_status("Reading statement…")
        override = self._selected_mapping() if reuse_mapping else None
        run_database_task(
            self,
            _parse_and_preview,
            self.source_path,
            override,
            on_success=self._apply_preview,
            on_error=lambda message: self._set_status(
                f"Could not read statement: {message}", "error"
            ),
        )

    def _apply_preview(self, result):
        parsed, preview = result
        self.parse_result = parsed
        self.preview = preview
        self.preview_model.set_preview(preview)
        self._render_mapping()
        detected = csv_parser.date_format_label(parsed.date_format)
        separator = parsed.delimiter.strip() or "tab"
        self.detected_label.setText(f"{detected} · '{separator}' separator")
        self._refresh_footer()
        self._set_status("Review the rows below, then click Import.")

    def _selected_mapping(self):
        if not self.parse_result:
            return None
        header = self.parse_result.header
        override = {}
        for field_name, combo in self.mapping_vars.items():
            selected = combo.currentText()
            if selected == NONE_OPTION:
                override[field_name] = None
            elif selected in header:
                override[field_name] = header.index(selected)
        return override

    def _render_mapping(self):
        while self.mapping_grid.rowCount():
            self.mapping_grid.removeRow(0)
        self.mapping_vars.clear()

        header = self.parse_result.header
        options = [NONE_OPTION] + header
        for index, field_name in enumerate(csv_parser.FIELDS):
            combo = QComboBox()
            combo.addItems(options)
            detected = self.preview.mapping.get(field_name)
            if detected is not None and detected < len(header):
                combo.setCurrentText(header[detected])
            else:
                combo.setCurrentText(NONE_OPTION)
            self.mapping_vars[field_name] = combo
            self.mapping_grid.addRow(field_label(FIELD_LABELS[field_name]), combo)

    # ------------------------------------------------------------------ preview
    def _refresh_footer(self):
        if self.preview is None:
            return
        counts = service.preview_counts(self.preview)
        totals = service.preview_totals(self.preview)
        self.counts_label.setText(
            f"{counts['total']} rows · {counts['included']} included · "
            f"{counts['duplicates']} duplicates · {counts['errors']} errors"
        )
        self.totals_label.setText(
            f"Included: {format_inr(totals['income'])} in · "
            f"{format_inr(totals['expense'])} out · net {format_inr(totals['net'])}"
        )
        label = f"Import {counts['included']} transaction" + ("s" if counts["included"] != 1 else "")
        self.import_button.setText(label)

    # ----------------------------------------------------------------- actions
    def _confirm(self):
        if self.preview is None:
            self._set_status("Choose a CSV file first.", "error")
            return
        self.import_button.setEnabled(False)
        self._set_status("Importing…")

        def done(summary):
            self._show_summary(summary)
            self.close()

        run_database_task(
            self,
            service.commit_preview,
            self.preview,
            on_success=done,
            on_error=lambda message: (
                self._set_status(f"Import failed; nothing was saved. {message}", "error"),
                self.import_button.setEnabled(True),
            ),
        )

    def _show_summary(self, summary):
        QMessageBox.information(
            self,
            "Pocket Ledger · Import complete",
            "Import complete\n\n"
            f"Imported: {summary.imported}\n"
            f"Skipped duplicates: {summary.skipped_duplicates}\n"
            f"Excluded: {summary.excluded}\n"
            f"Errors: {summary.errors}",
        )

    def _set_status(self, message, kind="info"):
        self.status_label.setText(message)
        self.status_label.setObjectName("statusError" if kind == "error" else "muted")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def closeEvent(self, event):
        callback = self._on_close
        super().closeEvent(event)
        if callback is not None:
            callback()
