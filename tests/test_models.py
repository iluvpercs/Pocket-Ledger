"""Qt model tests: table display, sorting, filtering and import preview edits."""

from PySide6.QtCore import Qt

from importers import csv_parser, service
from ui.models import ImportPreviewModel, TransactionProxyModel, TransactionTableModel


def _rows():
    return [
        {
            "id": 1,
            "transaction_type": "expense",
            "amount_minor": 12550,
            "category": "Food",
            "description": "Lunch",
            "transaction_date": "2026-11-22",
            "account_uuid": "acc-inr",
            "account_name": "Main",
            "currency_code": "INR",
            "currency_precision": 2,
        },
        {
            "id": 2,
            "transaction_type": "income",
            "amount_minor": 2500000,
            "category": "Salary",
            "description": "Monthly salary",
            "transaction_date": "2026-11-23",
            "account_uuid": "acc-inr",
            "account_name": "Main",
            "currency_code": "INR",
            "currency_precision": 2,
        },
    ]


def test_transaction_model_shapes_rows_without_widgets(qapp):
    model = TransactionTableModel(_rows())
    assert model.rowCount() == 2
    assert model.columnCount() == 6
    assert model.headerData(0, Qt.Horizontal) == "Date"
    assert model.headerData(2, Qt.Horizontal) == "Account"
    assert model.data(model.index(0, 0)) == "22 Nov 2026"
    assert model.data(model.index(0, 1)) == "Expense"
    assert model.data(model.index(0, 2)) == "Main · INR"
    assert model.data(model.index(0, 5)) == "−₹125.50"
    assert model.row_id(1) == 2
    assert model.data(model.index(0, 0), Qt.UserRole) == 1

    model.set_rows([])
    assert model.rowCount() == 0


def test_proxy_filters_all_columns_and_maps_back_to_source(qapp):
    source = TransactionTableModel(_rows())
    proxy = TransactionProxyModel()
    proxy.setSourceModel(source)

    proxy.set_filter_text("salary")
    assert proxy.rowCount() == 1
    assert proxy.source_row_id(0) == 2

    proxy.set_filter_text("22 Nov")
    assert proxy.rowCount() == 1
    assert proxy.source_row_id(0) == 1

    proxy.set_filter_text("")
    proxy.sort(5, Qt.DescendingOrder)
    assert "25,000.00" in proxy.data(proxy.index(0, 5))


def test_import_preview_model_edits_go_through_service(qapp, temp_database, tmp_path):
    path = tmp_path / "s.csv"
    path.write_text(
        "Date,Description,Amount\n22/11/2026,Tea Stall,50.00 Dr\n", encoding="utf-8"
    )
    parsed = csv_parser.parse_csv(path)
    preview = service.build_preview(parsed)

    model = ImportPreviewModel()
    model.set_preview(preview)
    assert model.rowCount() == 1
    assert model.data(model.index(0, 5)) == "NEW"
    assert model.data(model.index(0, 0), Qt.CheckStateRole) == Qt.Checked

    assert model.setData(model.index(0, 2), "Coffee Stall")
    assert preview.rows[0].description == "Coffee Stall"
    assert model.data(model.index(0, 2)) == "Coffee Stall"

    assert model.setData(model.index(0, 0), Qt.Unchecked, Qt.CheckStateRole)
    assert preview.rows[0].included is False
    assert model.data(model.index(0, 0), Qt.CheckStateRole) == Qt.Unchecked
