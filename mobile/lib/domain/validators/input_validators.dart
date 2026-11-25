import 'package:pocket_ledger_mobile/domain/validation_exception.dart';

/// Desktop-compatible text and ISO date checks.
abstract final class InputValidators {
  static String requiredText(Object? value, String label) {
    final text = value?.toString().trim() ?? '';
    if (text.isEmpty) {
      throw DomainValidationException('$label cannot be empty.');
    }
    return text;
  }

  static String? optionalText(Object? value) {
    if (value == null) return null;
    final text = value.toString().trim();
    return text.isEmpty ? null : text;
  }

  static String isoDate(Object? value) {
    final text = value?.toString().trim() ?? '';
    if (!RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(text)) {
      throw const DomainValidationException(
        'Date must be a valid date (for example 2026-11-22).',
      );
    }
    final parsed = DateTime.tryParse(text);
    if (parsed == null) {
      throw const DomainValidationException(
        'Date must be a valid date (for example 2026-11-22).',
      );
    }
    return text;
  }
}
