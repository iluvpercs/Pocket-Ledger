import 'package:pocket_ledger_mobile/domain/validation_exception.dart';
import 'package:uuid/uuid.dart' as uuid_package;

/// Canonical UUID text used for accounts, transactions, devices and outbox rows.
final class Uuid {
  Uuid._(this.value);

  final String value;

  static final RegExp _pattern = RegExp(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    caseSensitive: false,
  );

  factory Uuid.parse(Object? input) {
    final text = input?.toString().trim().toLowerCase() ?? '';
    if (!_pattern.hasMatch(text)) {
      throw DomainValidationException('Invalid UUID: $text.');
    }
    return Uuid._(text);
  }

  factory Uuid.generate() => Uuid._(const uuid_package.Uuid().v4());

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is Uuid && other.value == value;

  @override
  int get hashCode => value.hashCode;

  @override
  String toString() => value;
}
