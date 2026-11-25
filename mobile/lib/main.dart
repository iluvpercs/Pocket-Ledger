import 'dart:ui' show PlatformDispatcher;

import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:pocket_ledger_mobile/app.dart';
import 'package:pocket_ledger_mobile/core/logging/app_logger.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/app_error_view.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  FlutterError.onError = (details) {
    AppLogger.error(details.exception, details.stack ?? StackTrace.empty);
  };
  PlatformDispatcher.instance.onError = (error, stack) {
    AppLogger.error(error, stack);
    return true;
  };
  ErrorWidget.builder = (details) => Directionality(
    textDirection: TextDirection.ltr,
    child: Center(
      child: AppErrorView(message: details.exceptionAsString()),
    ),
  );

  runApp(const ProviderScope(child: PocketLedgerApp()));
}
