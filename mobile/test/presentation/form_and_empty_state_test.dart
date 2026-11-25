import 'dart:async';

import 'package:drift/native.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/data/database/database.dart' as db;
import 'package:pocket_ledger_mobile/domain/entities/category.dart';
import 'package:pocket_ledger_mobile/presentation/screens/settings_screen.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/add_transaction_form.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/brand_logo.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/dashboard_empty_state.dart';

import '../support/test_data.dart';

void main() {
  testWidgets('transaction form rejects surplus precision then accepts exact',
      (tester) async {
    final account = testAccount();
    TransactionDraft? submitted;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AddTransactionForm(
            accounts: [account],
            categories: const [
              LedgerCategory(id: 'food', name: 'Food', isDefault: true),
            ],
            onSubmit: (draft) async {
              submitted = draft;
            },
            initialTimeMs: DateTime(2026, 11, 25, 12).millisecondsSinceEpoch,
          ),
        ),
      ),
    );

    final amountField = find.byType(TextFormField).first;
    await tester.enterText(amountField, '12.345');
    await tester.tap(find.byType(FilledButton));
    await tester.pump();

    expect(
      find.textContaining('more than 2 decimal places'),
      findsWidgets,
    );
    expect(submitted, isNull);

    await tester.enterText(amountField, '12.34');
    await tester.tap(find.byType(FilledButton));
    await tester.pump();

    expect(submitted, isNotNull);
    expect(submitted!.amountText, '12.34');
    expect(submitted!.category, 'Food');
    expect(tester.takeException(), isNull);
  });

  testWidgets('transaction form disables save while the write is in flight',
      (tester) async {
    final pending = Completer<void>();
    final account = testAccount();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AddTransactionForm(
            accounts: [account],
            categories: const [
              LedgerCategory(id: 'food', name: 'Food', isDefault: true),
            ],
            onSubmit: (_) => pending.future,
            initialTimeMs: DateTime(2026, 11, 25, 12).millisecondsSinceEpoch,
          ),
        ),
      ),
    );

    await tester.enterText(find.byType(TextFormField).first, '12.34');
    await tester.tap(find.byType(FilledButton));
    await tester.pump();

    expect(find.widgetWithText(FilledButton, 'Saving…'), findsOneWidget);
    expect(tester.widget<FilledButton>(find.byType(FilledButton)).onPressed, isNull);

    pending.complete();
    await tester.pumpAndSettle();

    final button = find.widgetWithText(FilledButton, 'Add transaction');
    expect(button, findsOneWidget);
    expect(tester.widget<FilledButton>(button).onPressed, isNotNull);
    expect(tester.takeException(), isNull);
  });

  testWidgets('dashboard empty state invites the first transaction',
      (tester) async {
    var tapped = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: DashboardEmptyState(onAdd: () => tapped = true),
        ),
      ),
    );

    expect(find.text('Your ledger is ready'), findsOneWidget);
    expect(find.text('Add your first transaction'), findsOneWidget);
    await tester.tap(find.text('Add your first transaction'));
    await tester.pump();
    expect(tapped, isTrue);
  });

  testWidgets('settings shows the brand logo and private-by-design notice',
      (tester) async {
    final database = db.AppDatabase(NativeDatabase.memory());
    final container = ProviderContainer(
      overrides: [databaseProvider.overrideWithValue(database)],
    );
    addTearDown(() async {
      container.dispose();
      await database.close();
    });

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: const MaterialApp(home: SettingsScreen()),
      ),
    );
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(
      find.text('Private by design'),
      500,
      maxScrolls: 30,
    );
    await tester.pumpAndSettle();

    expect(find.byType(BrandLogo), findsOneWidget);
    expect(find.text('Private by design'), findsOneWidget);
    expect(
      find.text('No network. No telemetry. No automatic import.'),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });
}
