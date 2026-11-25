import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/account_card.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/async_value_view.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/empty_state_view.dart';

class AccountsScreen extends ConsumerWidget {
  const AccountsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summaries = ref.watch(accountSummariesProvider);
    final transactions = ref.watch(liveTransactionsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Accounts')),
      floatingActionButton: Semantics(
        label: 'Add account',
        child: FloatingActionButton.extended(
          onPressed: () => context.push('/account/new'),
          icon: const Icon(Icons.add),
          label: const Text('Account'),
        ),
      ),
      body: AsyncValueView(
        value: summaries,
        onRetry: () => ref.invalidate(accountSummariesProvider),
        builder: (items) {
          return AsyncValueView(
            value: transactions,
            builder: (allTransactions) {
              if (items.isEmpty) {
                return const Padding(
                  padding: EdgeInsets.all(16),
                  child: EmptyStateView(
                    icon: Icons.account_balance_wallet_outlined,
                    title: 'No accounts',
                    message: 'Create an account to start recording transactions.',
                  ),
                );
              }
              final withTransactions = <String>{
                for (final transaction in allTransactions)
                  transaction.accountUuid.value,
              };
              return ListView.builder(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
                itemCount: items.length,
                itemBuilder: (context, index) {
                  final summary = items[index];
                  return AccountCard(
                    key: ValueKey('account-${summary.account.uuid.value}'),
                    summary: summary,
                    hasTransactions: withTransactions.contains(
                      summary.account.uuid.value,
                    ),
                    onTap: () => context.push(
                      '/account/${summary.account.uuid.value}',
                    ),
                    onAction: (action) => _handleAction(
                      action,
                      summary.account,
                      withTransactions.contains(
                        summary.account.uuid.value,
                      ),
                      ref,
                      context,
                    ),
                  );
                },
              );
            },
          );
        },
      ),
    );
  }

  Future<void> _handleAction(
    String action,
    Account account,
    bool hasTransactions,
    WidgetRef ref,
    BuildContext context,
  ) async {
    final repository = ref.read(ledgerRepositoryProvider);
    try {
      switch (action) {
        case 'default':
          await repository.setDefaultAccount(account.uuid);
          break;
        case 'rename':
          if (!context.mounted) return;
          context.push('/account/${account.uuid.value}/edit');
          return;
        case 'archive':
          var cascade = false;
          if (hasTransactions) {
            if (!context.mounted) return;
            final confirmed = await showDialog<bool>(
              context: context,
              builder: (_) => AlertDialog(
                title: const Text('Archive account?'),
                content: Text(
                  '${account.name} has transactions. Cascade soft-delete them '
                  'too? You can restore them later from the outbox.',
                ),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(false),
                    child: const Text('Cancel'),
                  ),
                  FilledButton(
                    onPressed: () => Navigator.of(context).pop(true),
                    child: const Text('Archive all'),
                  ),
                ],
              ),
            );
            if (confirmed != true) return;
            cascade = true;
          }
          await repository.softDeleteAccount(account.uuid, cascade: cascade);
          break;
      }
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Account updated.')),
      );
    } catch (error) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    }
  }
}
