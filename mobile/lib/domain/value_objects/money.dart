import 'package:decimal/decimal.dart';

import 'package:pocket_ledger_mobile/domain/validation_exception.dart';

import 'currency_code.dart';
import 'currency_precision.dart';

/// Signed 64-bit minor units, parsed and formatted without binary floats.
final class MinorAmount {
  MinorAmount._(this.minor);

  static final BigInt maxMinor = BigInt.parse('9223372036854775807');
  static final BigInt minMinor = BigInt.parse('-9223372036854775808');

  final int minor;

  factory MinorAmount.fromMinor(int minor) {
    final value = BigInt.from(minor);
    if (value > maxMinor || value < minMinor) {
      throw const DomainValidationException('Amount is too large to store.');
    }
    return MinorAmount._(minor);
  }

  /// Parse major units into minor units. Strings, integers and [Decimal] values
  /// are accepted; [double] is deliberately rejected.
  factory MinorAmount.parse(
    Object? value,
    CurrencyPrecision precision, {
    bool strict = true,
  }) {
    if (value == null) {
      throw const DomainValidationException('Amount is required.');
    }
    if (value is double) {
      throw const DomainValidationException(
        'Floating-point amounts are not allowed.',
      );
    }
    if (value is bool) {
      throw const DomainValidationException('Amount must be a number.');
    }

    final text = switch (value) {
      final Decimal decimal => decimal.toString(),
      final BigInt big => big.toString(),
      final int integer => integer.toString(),
      final String string => string.replaceAll(',', '').trim(),
      _ => throw const DomainValidationException('Amount must be a number.'),
    };

    final parsed = Decimal.tryParse(text);
    if (parsed == null) {
      throw const DomainValidationException('Amount must be a number.');
    }

    final scaled = parsed.shift(precision.value);
    final rounded = scaled.round(); // half away from zero, like ROUND_HALF_UP
    if (strict && rounded != scaled) {
      throw DomainValidationException(
        'Amount cannot have more than ${precision.value} decimal places '
        'for this account.',
      );
    }

    final minor = rounded.toBigInt();
    if (minor > maxMinor || minor < minMinor) {
      throw const DomainValidationException('Amount is too large to store.');
    }
    return MinorAmount._(minor.toInt());
  }

  /// Transaction amounts are strictly positive; direction is stored separately.
  factory MinorAmount.positive(
    Object? value,
    CurrencyPrecision precision, {
    bool strict = true,
  }) {
    final amount = MinorAmount.parse(
      value,
      precision,
      strict: strict,
    );
    if (amount.minor <= 0) {
      throw const DomainValidationException('Amount must be greater than zero.');
    }
    return amount;
  }

  Decimal toMajorDecimal(CurrencyPrecision precision) =>
      Decimal.fromBigInt(BigInt.from(minor)).shift(-precision.value);

  /// Exact fixed-point display text, for example `1250.00` for 125000 minor.
  String format(CurrencyCode code) {
    final precision = code.precision;
    final fixed = toMajorDecimal(precision).toStringAsFixed(precision.value);
    final parts = fixed.split('.');
    final grouped = parts.first.replaceAllMapped(
      RegExp(r'(\d)(?=(\d{3})+$)'),
      (match) => '${match.group(1)},',
    );
    final body = parts.length == 1 ? grouped : '$grouped.${parts.last}';
    return '${code.symbol}$body';
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is MinorAmount && other.minor == minor;

  @override
  int get hashCode => minor.hashCode;

  @override
  String toString() => 'MinorAmount($minor)';
}
