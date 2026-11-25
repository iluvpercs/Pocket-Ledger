import 'package:drift/native.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/data/database/daos/ledger_dao.dart';
import 'package:pocket_ledger_mobile/data/database/database.dart' as db;
import 'package:pocket_ledger_mobile/data/repositories/drift_ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/entities/account_summary.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';
import 'package:pocket_ledger_mobile/presentation/common/navigation.dart';
import 'package:pocket_ledger_mobile/presentation/screens/transactions_screen.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/account_card.dart';

import '../support/test_data.dart';

/// Minimal stand-in for an editor: it performs the same async save, root
/// SnackBar and [closeOrGo] sequence without pulling in every provider screen.
class _SaveProbeScreen extends StatelessWidget {
  const _SaveProbeScreen({required this.onSave});

  final Future<int> Function() onSave;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add transaction')),
      body: FilledButton(
        onPressed: () async {
          await onSave();
          if (!context.mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Transaction added')),
          );
          closeOrGo(context, '/transactions');
        },
        child: const Text('Add transaction'),
      ),
    );
  }
}

Widget _saveProbeApp({
  required String initialLocation,
  required Future<int> Function() onSave,
  required GlobalKey<ScaffoldMessengerState> messengerKey,
}) {
  final router = GoRouter(
    initialLocation: initialLocation,
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => Scaffold(
          body: const Center(child: Text('Home screen')),
          floatingActionButton: FloatingActionButton(
            onPressed: () => context.push('/transaction/new'),
            child: const Icon(Icons.add),
          ),
        ),
      ),
      GoRoute(
        path: '/transactions',
        builder: (context, state) =>
            const Scaffold(body: Center(child: Text('Transactions home'))),
      ),
      GoRoute(
        path: '/transaction/new',
        builder: (context, state) => _SaveProbeScreen(onSave: onSave),
      ),
    ],
  );

  return MaterialApp.router(
    routerConfig: router,
    scaffoldMessengerKey: messengerKey,
  );
}

void main() {
  for (final hasBackStack in [true, false]) {
    testWidgets(
      'save then navigate ${hasBackStack ? 'pops' : 'falls back to a tab'} '
      'and keeps the success snackbar',
      (tester) async {
        final database = db.AppDatabase(NativeDatabase.memory());
        final repository = DriftLedgerRepository(LedgerDao(database));
        await repository.ensureBootstrapped();
        final messengerKey = GlobalKey<ScaffoldMessengerState>();

        late int savedId;
        await tester.pumpWidget(
          _saveProbeApp(
            initialLocation: hasBackStack ? '/' : '/transaction/new',
            onSave: () async {
              savedId = await repository.addTransaction(
                type: TransactionType.expense,
                amount: '12.34',
                category: 'Food',
                transactionDate: '2026-11-25',
              );
              return savedId;
            },
            messengerKey: messengerKey,
          ),
        );
        await tester.pumpAndSettle();

        if (hasBackStack) {
          final context = tester.element(find.text('Home screen'));
          GoRouter.of(context).push('/transaction/new');
          await tester.pumpAndSettle();
        }

        expect(find.byType(_SaveProbeScreen), findsOneWidget);
        await tester.tap(find.widgetWithText(FilledButton, 'Add transaction'));
        await tester.pumpAndSettle();

        expect(find.text('Transaction added'), findsWidgets);
        expect(find.byType(_SaveProbeScreen), findsNothing);
        expect(
          find.text(hasBackStack ? 'Home screen' : 'Transactions home'),
          findsOneWidget,
        );
        expect(messengerKey.currentState, isNotNull);

        final saved = await repository.transactionById(savedId);
        expect(saved, isNotNull);
        expect(saved!.type, TransactionType.expense);
        expect(saved.amount.minor, 1_234);
        await database.close();
      },
    );
  }

  testWidgets('200 transactions scroll in one lazy list', (tester) async {
    final database = db.AppDatabase(NativeDatabase.memory());
    final container = ProviderContainer(
      overrides: [databaseProvider.overrideWithValue(database)],
    );
    await container.read(bootstrapProvider.future);

    final repository = container.read(ledgerRepositoryProvider);
    for (var index = 0; index < 200; index++) {
      await repository.addTransaction(
        type: TransactionType.expense,
        amount: '${index + 1}.00',
        category: 'Food',
        transactionDate: '2026-11-25',
        description: 'Row $index',
      );
    }

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const MaterialApp(home: TransactionsScreen()),
      ),
    );
    await tester.pumpAndSettle();

    final list = find.byType(ListView);
    expect(list, findsOneWidget);
    final before = tester.widget<ListView>(list).controller!.offset;
    await tester.drag(list, const Offset(0, -2_500));
    await tester.pumpAndSettle();
    final after = tester.widget<ListView>(list).controller!.offset;

    expect(after, greaterThan(before));
    expect(tester.takeException(), isNull);
  });

  testWidgets('account row does not overflow at 1.5x text scale', (tester) async {
    final account = testAccount(
      name: 'A very long account name that must ellipsise rather than wrap',
    );
    final summary = AccountSummary(account: account, balanceMinor: 123_456_789);

    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) {
            return MediaQuery(
              data: MediaQuery.of(
                context,
              ).copyWith(textScaler: TextScaler.linear(1.5)),
              child: Scaffold(
                body: Center(
                  child: SizedBox(
                    width: 320,
                    child: AccountCard(
                      summary: summary,
                      hasTransactions: true,
                      onTap: () {},
                      onAction: (_) {},
                    ),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
    await tester.pumpAndSettle();

    final name = find.text(account.name);
    expect(name, findsOneWidget);
    expect(tester.widget<Text>(name).maxLines, 1);
    expect(find.textContaining('Default'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
