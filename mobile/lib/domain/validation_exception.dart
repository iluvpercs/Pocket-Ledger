/// Pure-Dart validation failure, independent of Flutter and database code.
class DomainValidationException implements Exception {
  const DomainValidationException(this.message);

  final String message;

  @override
  String toString() => message;
}
