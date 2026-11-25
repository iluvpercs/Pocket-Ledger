import 'dart:developer' as developer;

/// Local-only logging. No analytics, crash reporting or network transport.
abstract final class AppLogger {
  static void error(Object error, StackTrace stack) {
    developer.log(
      error.toString(),
      name: 'PocketLedger',
      level: 1000,
      error: error,
      stackTrace: stack,
    );
  }
}
