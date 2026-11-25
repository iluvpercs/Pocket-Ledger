import 'package:flutter_test/flutter_test.dart';

import 'package:pocket_ledger_mobile/domain/validation_exception.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_precision.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

void main() {
  group('MinorAmount', () {
    test('parses exact major units for supported precisions', () {
      expect(MinorAmount.positive('12.34', CurrencyPrecision.two).minor, 1234);
      expect(MinorAmount.positive(1234, CurrencyPrecision.two).minor, 123400);
      expect(MinorAmount.positive('5', CurrencyPrecision.zero).minor, 5);
      expect(MinorAmount.positive('1.234', CurrencyPrecision.three).minor, 1234);
    });

    test('strict manual entry rejects surplus fractional digits', () {
      expect(
        () => MinorAmount.positive('12.345', CurrencyPrecision.two),
        throwsA(isA<DomainValidationException>()),
      );
    });

    test('non-strict conversion rounds half away from zero', () {
      expect(
        MinorAmount.parse('12.345', CurrencyPrecision.two, strict: false).minor,
        1235,
      );
      expect(
        MinorAmount.parse('-1.005', CurrencyPrecision.two, strict: false).minor,
        -101,
      );
    });

    test('rejects binary floats and non-positive transaction amounts', () {
      expect(
        () => MinorAmount.positive(12.34, CurrencyPrecision.two),
        throwsA(isA<DomainValidationException>()),
      );
      expect(
        () => MinorAmount.positive('0', CurrencyPrecision.two),
        throwsA(isA<DomainValidationException>()),
      );
      expect(
        () => MinorAmount.positive('-1', CurrencyPrecision.two),
        throwsA(isA<DomainValidationException>()),
      );
    });

    test('formats exact fixed-point text with the desktop symbol', () {
      expect(
        MinorAmount.fromMinor(125000).format(CurrencyCode.parse('INR')),
        '₹1,250.00',
      );
      expect(
        MinorAmount.fromMinor(1234).format(CurrencyCode.parse('USD')),
        r'$12.34',
      );
    });
  });

  group('CurrencyCode', () {
    test('normalises ISO codes and mirrors desktop precision rules', () {
      expect(CurrencyCode.parse(' inr ').value, 'INR');
      expect(CurrencyCode.parse('inr').precision.value, 2);
      expect(CurrencyCode.parse('BHD').precision.value, 3);
      expect(
        () => CurrencyCode.parse('CLF'),
        throwsA(isA<DomainValidationException>()),
      );
      expect(
        () => CurrencyCode.parse('XX'),
        throwsA(isA<DomainValidationException>()),
      );
    });
  });

  group('Uuid and UtcMs', () {
    test('UUIDs are canonical lowercase text', () {
      final generated = Uuid.generate();
      expect(Uuid.parse(generated.value.toUpperCase()), generated);
      expect(
        () => Uuid.parse('not-a-uuid'),
        throwsA(isA<DomainValidationException>()),
      );
    });

    test('timestamps are stored as UTC milliseconds', () {
      final timestamp = UtcMs.fromDateTime(
        DateTime.parse('2026-11-25T10:30:00Z'),
      );
      expect(timestamp.toDateTime().isUtc, isTrue);
      expect(timestamp.toDateTime().toIso8601String(), '2026-11-25T10:30:00.000Z');
      expect(() => UtcMs(-1), throwsA(isA<DomainValidationException>()));
    });
  });
}
