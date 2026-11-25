import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/core/theme/app_theme.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/presentation/router/app_router.dart';

/// SnackBars raised just before a pushed editor closes must outlive that
/// editor's Scaffold, so the app owns a single root messenger.
final rootScaffoldMessengerKey = GlobalKey<ScaffoldMessengerState>();

class PocketLedgerApp extends ConsumerWidget {
  const PocketLedgerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    final mode = ref.watch(settingsProvider).value?.themeMode ??
        LedgerThemeMode.dark;
    final themeMode = mode == LedgerThemeMode.system
        ? ThemeMode.system
        : ThemeMode.dark;

    return MaterialApp.router(
      title: 'Pocket Ledger',
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: themeMode,
      routerConfig: router,
      scaffoldMessengerKey: rootScaffoldMessengerKey,
      debugShowCheckedModeBanner: false,
    );
  }
}
