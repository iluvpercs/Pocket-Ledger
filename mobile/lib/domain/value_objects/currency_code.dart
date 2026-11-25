import 'package:pocket_ledger_mobile/domain/validation_exception.dart';

import 'currency_precision.dart';
import 'currency_table.dart';

/// Normalised ISO 4217 code with a precision the desktop app can store.
final class CurrencyCode {
  const CurrencyCode._(this.value);

  final String value;

  factory CurrencyCode.parse(Object? input) {
    if (input == null) {
      throw const DomainValidationException('A currency code is required.');
    }
    final text = input.toString().trim().toUpperCase();
    if (!RegExp(r'^[A-Z]{3}$').hasMatch(text)) {
      throw DomainValidationException('Invalid currency code: $text.');
    }
    final precision = currencyPrecision[text];
    if (precision == null) {
      throw DomainValidationException('Unknown ISO 4217 currency code: $text.');
    }
    if (!const {0, 2, 3}.contains(precision)) {
      throw DomainValidationException(
        '$text uses $precision decimal places; Pocket Ledger supports 0, 2 or 3.',
      );
    }
    return CurrencyCode._(text);
  }

  CurrencyPrecision get precision => CurrencyPrecision.from(
    currencyPrecision[value]!,
  );

  String get symbol => currencySymbol[value] ?? '$value ';

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is CurrencyCode && other.value == value;

  @override
  int get hashCode => value.hashCode;

  @override
  String toString() => value;
}
