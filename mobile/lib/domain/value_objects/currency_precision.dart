import 'package:pocket_ledger_mobile/domain/validation_exception.dart';

/// Number of decimal places supported by Pocket Ledger: 0, 2 or 3.
final class CurrencyPrecision {
  const CurrencyPrecision._(this.value);

  static const CurrencyPrecision zero = CurrencyPrecision._(0);
  static const CurrencyPrecision two = CurrencyPrecision._(2);
  static const CurrencyPrecision three = CurrencyPrecision._(3);

  final int value;

  factory CurrencyPrecision.from(int value) {
    return switch (value) {
      0 => zero,
      2 => two,
      3 => three,
      _ => throw const DomainValidationException(
          'Currency precision must be 0, 2 or 3.',
        ),
    };
  }

  int get minorUnitsPerMajorUnit => switch (value) {
    0 => 1,
    2 => 100,
    3 => 1000,
    _ => throw const DomainValidationException(
        'Currency precision must be 0, 2 or 3.',
      ),
  };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is CurrencyPrecision && other.value == value;

  @override
  int get hashCode => value.hashCode;

  @override
  String toString() => 'CurrencyPrecision($value)';
}
