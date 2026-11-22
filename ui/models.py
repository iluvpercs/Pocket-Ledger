"""Qt table models for the desktop screens.

The models only shape data for ``QTableView``. They never issue SQL: rows come
from the public ``database.py`` functions or from ``importers.service``, which
keeps the import logic reusable without a GUI.
"""

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QColor

from ui.theme import (
    HIGHLIGHT,
    HIGHLIGHT_SOFT,
    NEGATIVE,
    NEGATIVE_SOFT,
    POSITIVE,
    POSITIVE_SOFT,
)
from utils.formatting import (
    format_signed_amount,
    format_transaction_date,
    shorten,
    transaction_type_label,
)


class TransactionTableModel(QAbstractTableModel):
    """A virtual table over the rows returned by ``get_all_transactions()``."""

    HEADERS = ("Date", "Type", "Category", "Description", "Amount")
    SortRole = Qt.UserRole + 1

    def __init__(self, rows=None, parent=None):
        super().__init__(parent)
        self._rows = list(rows or [])

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        return None

    def set_rows(self, rows):
        self.beginResetModel()
        self._rows = list(rows or [])
        self.endResetModel()

    def rows(self):
        return list(self._rows)

    def row_id(self, row):
        if 0 <= row < len(self._rows):
            return self._rows[row]["id"]
        return None

    def row_dict(self, row):
        if 0 <= row < len(self._rows):
            return dict(self._rows[row])
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        row = self._rows[index.row()]
        column = index.column()

        if role == Qt.UserRole:
            return row["id"]
        if role == self.SortRole:
            if column == 0:
                return str(row["transaction_date"])
            if column == 4:
                return float(row["amount"])
            return str(self.data(index, Qt.DisplayRole) or "")
        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight | Qt.AlignVCenter if column == 4 else Qt.AlignLeft | Qt.AlignVCenter
        if role == Qt.ForegroundRole:
            if column in (1, 4):
                colour = POSITIVE if row["transaction_type"] == "income" else NEGATIVE
                return QColor(colour)
            return None
        if role != Qt.DisplayRole:
            return None

        if column == 0:
            return format_transaction_date(row["transaction_date"])
        if column == 1:
            return transaction_type_label(row["transaction_type"])
        if column == 2:
            return row["category"]
        if column == 3:
            return shorten(row["description"])
        if column == 4:
            return format_signed_amount(row["amount"], row["transaction_type"])
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class TransactionProxyModel(QSortFilterProxyModel):
    """Sortable table with a free-text filter across every visible column."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_text = ""
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortRole(TransactionTableModel.SortRole)

    def set_filter_text(self, text):
        # invalidateFilter() is deprecated in Qt 6.12; begin/endFilterChange
        # is the supported way to refresh a custom filter after state changes.
        self.beginFilterChange()
        self._filter_text = str(text or "").strip().lower()
        self.endFilterChange()

    def filter_text(self):
        return self._filter_text

    def filterAcceptsRow(self, source_row, source_parent):
        if not self._filter_text:
            return True
        source = self.sourceModel()
        if source is None:
            return True
        for column in range(source.columnCount()):
            value = source.data(source.index(source_row, column, source_parent))
            if value is not None and self._filter_text in str(value).lower():
                return True
        return False

    def source_row_id(self, proxy_row):
        source_index = self.mapToSource(self.index(proxy_row, 0))
        if not source_index.isValid():
            return None
        return self.sourceModel().row_id(source_index.row())

    def source_row_dict(self, proxy_row):
        source_index = self.mapToSource(self.index(proxy_row, 0))
        if not source_index.isValid():
            return None
        return self.sourceModel().row_dict(source_index.row())


class ImportPreviewModel(QAbstractTableModel):
    """Editable preview of CSV rows, backed by ``ImportPreview``.

    Using a model instead of one widget per row is what keeps a 5,000-row
    statement responsive: Qt only paints the rows currently on screen.
    """

    HEADERS = ("", "DATE", "DESCRIPTION", "CATEGORY", "AMOUNT", "STATUS")
    IncludeRole = Qt.UserRole + 1
    STATUS_STYLES = {
        "NEW": (POSITIVE, POSITIVE_SOFT),
        "WARNING": (HIGHLIGHT, HIGHLIGHT_SOFT),
        "DUPLICATE": (HIGHLIGHT, HIGHLIGHT_SOFT),
        "WAS DELETED": (HIGHLIGHT, HIGHLIGHT_SOFT),
        "ERROR": (NEGATIVE, NEGATIVE_SOFT),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.preview = None

    def set_preview(self, preview):
        self.beginResetModel()
        self.preview = preview
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid() or self.preview is None:
            return 0
        return len(self.preview.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return None

    @staticmethod
    def status_text(row):
        if row.status in ("error", "warning"):
            return "ERROR" if row.status == "error" else "WARNING"
        if row.duplicate_status == "duplicate":
            return "DUPLICATE"
        if row.duplicate_status == "previously_deleted":
            return "WAS DELETED"
        return "NEW"

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or self.preview is None:
            return None
        row = self.preview.rows[index.row()]
        column = index.column()

        if column == 0:
            if role in (Qt.DisplayRole, Qt.EditRole, self.IncludeRole):
                return bool(row.included)
            if role == Qt.CheckStateRole:
                return Qt.Checked if row.included else Qt.Unchecked
            return None
        if column == 5 and role in (Qt.ForegroundRole, Qt.BackgroundRole):
            foreground, background = self.STATUS_STYLES[self.status_text(row)]
            return QColor(foreground if role == Qt.ForegroundRole else background)
        if role in (Qt.DisplayRole, Qt.EditRole):
            if column == 1:
                return row.date or ""
            if column == 2:
                return row.description
            if column == 3:
                return row.category
            if column == 4:
                return str(row.amount) if row.amount is not None else ""
            if column == 5:
                return self.status_text(row)
        if role == Qt.TextAlignmentRole and column == 4:
            return Qt.AlignRight | Qt.AlignVCenter
        return None

    def flags(self, index):
        if not index.isValid() or self.preview is None:
            return Qt.NoItemFlags
        row = self.preview.rows[index.row()]
        if index.column() == 0:
            flags = Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
            return flags if row.importable else Qt.ItemIsEnabled
        if not row.importable:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or self.preview is None:
            return False
        from importers import service

        row_number = index.row()
        column = index.column()
        if column == 0 and role in (Qt.CheckStateRole, self.IncludeRole, Qt.EditRole):
            # Shiboken enums are truthy even when they represent Unchecked, so
            # compare the numeric value explicitly.
            try:
                checked = int(value) == int(Qt.Checked)
            except (TypeError, ValueError):
                checked = str(value).lower() in ("true", "checked", "yes", "1")
            service.apply_edits(self.preview, row_number, included=checked)
        elif column == 1:
            service.apply_edits(self.preview, row_number, date=str(value))
        elif column == 2:
            service.apply_edits(self.preview, row_number, description=str(value))
        elif column == 3:
            service.apply_edits(self.preview, row_number, category=str(value))
        elif column == 4:
            service.apply_edits(self.preview, row_number, amount=str(value))
        else:
            return False

        self.dataChanged.emit(
            self.index(row_number, 0), self.index(row_number, self.columnCount() - 1)
        )
        return True
