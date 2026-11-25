import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

enum CsvFieldKind {
  none('Ignore', []),
  date('Date', ['date', 'txndate', 'transactiondate', 'postingdate', 'valuedate', 'trandate']),
  amount('Signed amount', ['amount', 'amountinr', 'transactionamount', 'amt', 'value']),
  debit('Debit', ['debit', 'debitamount', 'withdrawal', 'withdrawalamount', 'withdraw', 'paidout', 'moneyout', 'dr', 'outflow', 'expense']),
  credit('Credit', ['credit', 'creditamount', 'deposit', 'depositamount', 'paidin', 'moneyin', 'cr', 'inflow', 'income']),
  description('Description', ['description', 'narration', 'particulars', 'details', 'memo', 'transactiondetails', 'remarks', 'purpose', 'narrative']),
  category('Category', ['category', 'cat']),
  account('Account', ['account', 'accountname', 'accountlabel']),
  currency('Currency', ['currency', 'currencycode', 'ccy']),
  reference('Reference', ['reference', 'ref', 'refno', 'chequeno', 'chqno', 'transactionid', 'txnid', 'utr', 'voucher']),
  balance('Balance', ['balance', 'closingbalance', 'runningbalance', 'availablebalance']);

  const CsvFieldKind(this.label, this.aliases);

  final String label;
  final List<String> aliases;
}

final class CsvMapping {
  const CsvMapping(this.columns);

  final List<CsvFieldKind> columns;

  CsvFieldKind operator [](int index) =>
      index >= 0 && index < columns.length ? columns[index] : CsvFieldKind.none;

  int? indexOf(CsvFieldKind kind) {
    for (var index = 0; index < columns.length; index++) {
      if (columns[index] == kind) return index;
    }
    return null;
  }

  CsvMapping withColumn(int index, CsvFieldKind kind) {
    final updated = List<CsvFieldKind>.from(columns);
    if (index >= 0 && index < updated.length) updated[index] = kind;
    return CsvMapping(updated);
  }

  static CsvMapping detect(List<String> headers) {
    final columns = List<CsvFieldKind>.filled(headers.length, CsvFieldKind.none);
    final used = <CsvFieldKind>{};
    for (var index = 0; index < headers.length; index++) {
      final normalised = _normaliseHeader(headers[index]);
      for (final kind in CsvFieldKind.values) {
        if (kind == CsvFieldKind.none || used.contains(kind)) continue;
        if (kind.aliases.contains(normalised)) {
          columns[index] = kind;
          used.add(kind);
          break;
        }
      }
    }
    if (used.isEmpty && headers.length >= 3) {
      columns[0] = CsvFieldKind.date;
      columns[1] = CsvFieldKind.description;
      columns[2] = CsvFieldKind.amount;
      if (headers.length >= 4) columns[3] = CsvFieldKind.category;
      if (headers.length >= 5) columns[4] = CsvFieldKind.account;
      if (headers.length >= 6) columns[5] = CsvFieldKind.currency;
    }
    return CsvMapping(columns);
  }

  static String _normaliseHeader(String value) =>
      value.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '');
}

enum CsvRowStatus { valid, invalid, duplicate }

final class ParsedCsvRow {
  const ParsedCsvRow({
    required this.line,
    required this.status,
    this.dateIso,
    this.amountMinor,
    this.type,
    this.category,
    this.description,
    this.accountUuid,
    this.currencyCode,
    this.signedMinor,
    this.importHash,
    this.reference,
    this.accountLabel,
    this.error,
  });

  final int line;
  final CsvRowStatus status;
  final String? dateIso;
  final int? amountMinor;
  final TransactionType? type;
  final String? category;
  final String? description;
  final Uuid? accountUuid;
  final CurrencyCode? currencyCode;
  final int? signedMinor;
  final String? importHash;
  final String? reference;
  final String? accountLabel;
  final String? error;

  bool get canImport =>
      status == CsvRowStatus.valid &&
      dateIso != null &&
      amountMinor != null &&
      type != null &&
      category != null &&
      accountUuid != null &&
      currencyCode != null &&
      importHash != null;
}

final class CsvPreview {
  const CsvPreview({
    required this.headers,
    required this.delimiterLabel,
    required this.hasHeaderRow,
    required this.mapping,
    required this.dateFormat,
    required this.roundAmounts,
    required this.sourceFile,
    required this.rows,
  });

  final String sourceFile;
  final List<String> headers;
  final String delimiterLabel;
  final bool hasHeaderRow;
  final CsvMapping mapping;
  final LedgerDateFormat dateFormat;
  final bool roundAmounts;
  final List<ParsedCsvRow> rows;

  int get validCount =>
      rows.where((row) => row.status == CsvRowStatus.valid).length;
  int get invalidCount =>
      rows.where((row) => row.status == CsvRowStatus.invalid).length;
  int get duplicateCount =>
      rows.where((row) => row.status == CsvRowStatus.duplicate).length;

  List<ParsedCsvRow> get importableRows =>
      rows.where((row) => row.canImport).toList();
}
