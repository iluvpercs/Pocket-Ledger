import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:pocket_ledger_mobile/domain/entities/csv_import.dart';
import 'package:pocket_ledger_mobile/domain/validation_exception.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/presentation/screens/account_detail_screen.dart';
import 'package:pocket_ledger_mobile/presentation/screens/account_editor_screen.dart';
import 'package:pocket_ledger_mobile/presentation/screens/accounts_screen.dart';
import 'package:pocket_ledger_mobile/presentation/screens/categories_screen.dart';
import 'package:pocket_ledger_mobile/presentation/screens/csv_preview_screen.dart';
import 'package:pocket_ledger_mobile/presentation/screens/dashboard_screen.dart';
import 'package:pocket_ledger_mobile/presentation/screens/import_csv_screen.dart';
import 'package:pocket_ledger_mobile/presentation/screens/settings_screen.dart';
import 'package:pocket_ledger_mobile/presentation/screens/transaction_editor_screen.dart';
import 'package:pocket_ledger_mobile/presentation/screens/transactions_screen.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/app_error_view.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/app_shell.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/dashboard',
    routes: [
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) =>
            AppShell(navigationShell: navigationShell),
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/dashboard',
                builder: (context, state) => const DashboardScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/transactions',
                builder: (context, state) => const TransactionsScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/accounts',
                builder: (context, state) => const AccountsScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/settings',
                builder: (context, state) => const SettingsScreen(),
              ),
            ],
          ),
        ],
      ),
      GoRoute(
        path: '/transaction/new',
        builder: (context, state) => TransactionEditorScreen(
          initialAccountUuid: _optionalUuid(
            state.uri.queryParameters['account'],
          ),
        ),
      ),
      GoRoute(
        path: '/transaction/:id/edit',
        builder: (context, state) => TransactionEditorScreen(
          id: int.tryParse(state.pathParameters['id'] ?? ''),
        ),
      ),
      GoRoute(
        path: '/account/new',
        builder: (context, state) => const AccountEditorScreen(),
      ),
      GoRoute(
        path: '/account/:uuid/edit',
        builder: (context, state) => AccountEditorScreen(
          accountUuid: Uuid.parse(state.pathParameters['uuid']),
        ),
      ),
      GoRoute(
        path: '/account/:uuid',
        builder: (context, state) => AccountDetailScreen(
          accountUuid: Uuid.parse(state.pathParameters['uuid']),
        ),
      ),
      GoRoute(
        path: '/categories',
        builder: (context, state) => const CategoriesScreen(),
      ),
      GoRoute(
        path: '/import',
        builder: (context, state) => const ImportCsvScreen(),
      ),
      GoRoute(
        path: '/import/preview',
        builder: (context, state) {
          final preview = state.extra;
          if (preview is! CsvPreview) {
            return const Scaffold(
              body: Center(child: Text('No CSV preview is available.')),
            );
          }
          return CsvPreviewScreen(preview: preview);
        },
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      appBar: AppBar(title: const Text('Pocket Ledger')),
      body: Center(
        child: AppErrorView(message: state.error.toString()),
      ),
    ),
  );
});

Uuid? _optionalUuid(String? value) {
  if (value == null || value.isEmpty) return null;
  try {
    return Uuid.parse(value);
  } on DomainValidationException {
    return null;
  }
}
