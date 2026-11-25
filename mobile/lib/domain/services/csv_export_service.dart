import 'package:csv/csv.dart';

import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_precision.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

/// Export columns are a superset of the import columns, so an exported file
/// maps back without any manual changes.
abstract final class CsvExportService {
  static const List<String> headers = [
    'date',
    'description',
    'amount',
    'debit',
    'credit',
    'balance',
    'reference',
    'category',
    'account',
    'currency',
  ];

  static String encode(
    Iterable<LedgerTransaction> transactions,
    Iterable<Account> accounts,
  ) {
    final byUuid = <String, Account>{
      for (final account in accounts) account.uuid.value: account,
    };
    final sorted = transactions.where((item) => item.isLive).toList()
      ..sort((a, b) {
        final byDate = b.transactionDate.compareTo(a.transactionDate);
        return byDate != 0 ? byDate : b.id.compareTo(a.id);
      });

    final rows = <List<dynamic>>[
      headers,
      for (final transaction in sorted)
        _row(transaction, byUuid[transaction.accountUuid.value]),
    ];
    return Csv(lineDelimiter: '\n').encode(rows);
  }

  static List<String> _row(LedgerTransaction transaction, Account? account) {
    final precision = CurrencyPrecision.from(account?.precision.value ?? 2);
    final signedMinor = transaction.type == TransactionType.income
        ? transaction.amount.minor
        : -transaction.amount.minor;
    final signed = MinorAmount.fromMinor(signedMinor)
        .toMajorDecimal(precision)
        .toStringAsFixed(precision.value);
    return [
      transaction.transactionDate,
      transaction.description ?? '',
      signed,
      '',
      '',
      '',
      transaction.externalRef ?? '',
      transaction.category,
      account?.name ?? transaction.accountLabel ?? '',
      account?.currencyCode.value ?? '',
    ];
  }
}
