import 'package:intl/intl.dart';

import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

String formatMoney(
  int minor,
  CurrencyCode currency, {
  TransactionType? type,
}) {
  final body = MinorAmount.fromMinor(minor.abs()).format(currency);
  final sign = switch (type) {
    TransactionType.income => '+',
    TransactionType.expense => '-',
    null => minor.isNegative ? '-' : '',
  };
  return '$sign$body';
}

String formatDate(String isoDate, LedgerDateFormat format) {
  final parsed = DateTime.tryParse('${isoDate}T12:00:00');
  if (parsed == null) return isoDate;
  return DateFormat(format.pattern, 'en_US').format(parsed);
}

String monthLabel(DateTime month) =>
    DateFormat('MMMM yyyy', 'en_US').format(month);

String shortMonthLabel(int year, int month) =>
    DateFormat('MMM', 'en_US').format(DateTime(year, month));
