import 'package:pocket_ledger_mobile/domain/validation_exception.dart';

/// Whole milliseconds since the Unix epoch, always interpreted as UTC.
final class UtcMs {
  const UtcMs._(this.value);

  final int value;

  factory UtcMs(int value) {
    if (value < 0) {
      throw const DomainValidationException(
        'UTC timestamps cannot be negative.',
      );
    }
    return UtcMs._(value);
  }

  factory UtcMs.now() => UtcMs._(
    DateTime.now().toUtc().millisecondsSinceEpoch,
  );

  factory UtcMs.fromDateTime(DateTime value) => UtcMs._(
    value.toUtc().millisecondsSinceEpoch,
  );

  DateTime toDateTime() => DateTime.fromMillisecondsSinceEpoch(
    value,
    isUtc: true,
  );

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is UtcMs && other.value == value;

  @override
  int get hashCode => value.hashCode;

  @override
  String toString() => '$value';
}
