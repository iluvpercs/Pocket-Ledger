import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction_filter.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/presentation/common/navigation.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/async_value_view.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/empty_state_view.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/money_text.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/transaction_tile.dart';

class AccountDetailScreen extends ConsumerWidget {
  const AccountDetailScreen({super.key, required this.accountUuid});

  final Uuid accountUuid;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summaries = ref.watch(accountSummariesProvider);
    final filter = TransactionFilter(accountUuid: accountUuid);
    final transactions = ref.watch(filteredTransactionsProvider(filter));
    final settings = ref.watch(settingsProvider).value ?? const LedgerSettings(
          defaultCurrencyCode: CurrencyCode.inr,
          dateFormat: LedgerDateFormat.iso,
          themeMode: LedgerThemeMode.dark,
        );

    return Scaffold(
      appBar: AppBar(
        title: const Text('Account detail'),
        leading: Semantics(
          label: 'Back to accounts',
          child: IconButton(
            tooltip: 'Back',
            icon: const Icon(Icons.arrow_back),
            onPressed: () => closeOrGo(context, '/accounts'),
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push(
          '/transaction/new?account=${accountUuid.value}',
        ),
        icon: const Icon(Icons.add),
        label: const Text('Add'),
      ),
      body: AsyncValueView(
        value: summaries,
        builder: (items) {
          final summary = items.where(
            (item) => item.account.uuid == accountUuid,
          );
          if (summary.isEmpty) {
            return const Center(child: Text('Account not found.'));
          }
          final account = summary.first.account;
          return AsyncValueView(
            value: transactions,
            builder: (rows) {
              return ListView(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            account.name,
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 12),
                          MoneyText(
                            minor: summary.first.balanceMinor,
                            currency: account.currencyCode,
                            style: Theme.of(context).textTheme.headlineMedium,
                          ),
                          const SizedBox(height: 4),
                          Text('Opening balance + all live transactions'),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (rows.isEmpty)
                    const EmptyStateView(
                      icon: Icons.receipt_long_outlined,
                      title: 'No transactions for this account',
                      message: 'Use Add to record the first one.',
                    )
                  else
                    for (final transaction in rows)
                      TransactionTile(
                        transaction: transaction,
                        currency: account.currencyCode,
                        dateFormat: settings.dateFormat,
                        selected: false,
                        onTap: () => context.push(
                          '/transaction/${transaction.id}/edit',
                        ),
                      ),
                ],
              );
            },
          );
        },
      ),
    );
  }
}
