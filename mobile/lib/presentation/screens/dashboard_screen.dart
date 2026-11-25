import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/domain/entities/dashboard_summary.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';
import 'package:pocket_ledger_mobile/presentation/common/formatters.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/async_value_view.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/category_spending_chart.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/dashboard_empty_state.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/money_text.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/six_month_chart.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summary = ref.watch(dashboardProvider);
    final accounts = ref.watch(accountsProvider);
    final settings = ref.watch(settingsProvider).value ?? const LedgerSettings(
          defaultCurrencyCode: CurrencyCode.inr,
          dateFormat: LedgerDateFormat.iso,
          themeMode: LedgerThemeMode.dark,
        );

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          Semantics(
            label: 'Refresh dashboard',
            child: IconButton(
              tooltip: 'Refresh dashboard',
              icon: const Icon(Icons.refresh),
              onPressed: () {
                ref.invalidate(dashboardProvider);
                ref.invalidate(accountsProvider);
                ref.invalidate(openingBalancesProvider);
              },
            ),
          ),
        ],
      ),
      floatingActionButton: Semantics(
        label: 'Add transaction',
        child: FloatingActionButton.extended(
          onPressed: () => context.push('/transaction/new'),
          icon: const Icon(Icons.add),
          label: const Text('Add'),
        ),
      ),
      body: AsyncValueView(
        value: summary,
        onRetry: () => ref.invalidate(dashboardProvider),
        builder: (data) {
          return AsyncValueView(
            value: accounts,
            builder: (accountList) {
              final byUuid = {
                for (final account in accountList) account.uuid.value: account,
              };
              if (data.recentTransactions.isEmpty) {
                return Padding(
                  padding: const EdgeInsets.all(16),
                  child: DashboardEmptyState(
                    onAdd: () => context.push('/transaction/new'),
                  ),
                );
              }
              final chartCurrency = settings.defaultCurrencyCode.value;
              return ListView(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
                children: [
                  _MonthHeader(
                    month: ref.watch(selectedMonthProvider),
                    onPrevious: ref.read(selectedMonthProvider.notifier).previous,
                    onNext: ref.read(selectedMonthProvider.notifier).next,
                  ),
                  const SizedBox(height: 16),
                  _BalanceCard(totals: data.balances),
                  const SizedBox(height: 16),
                  _MonthTotalsCard(totals: data.monthTotals),
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            'Spending by category — $chartCurrency',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 16),
                          CategorySpendingChart(
                            totals: data.categoryTotals
                                .where((item) => item.currencyCode == chartCurrency)
                                .toList(),
                            currency: settings.defaultCurrencyCode,
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            'Last six months — $chartCurrency',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 16),
                          SixMonthChart(
                            points: data.sixMonthSeries
                                .where(
                                  (point) => point.currencyCode == chartCurrency,
                                )
                                .toList(),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Card(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                          child: Row(
                            children: [
                              Text(
                                'Recent transactions',
                                style: Theme.of(context).textTheme.titleMedium,
                              ),
                              const Spacer(),
                              TextButton(
                                onPressed: () => context.go('/transactions'),
                                child: const Text('See all'),
                              ),
                            ],
                          ),
                        ),
                        for (final transaction in data.recentTransactions)
                          ListTile(
                            title: Text(
                              transaction.description?.isNotEmpty == true
                                  ? transaction.description!
                                  : transaction.category,
                            ),
                            subtitle: Text(
                              formatDate(
                                transaction.transactionDate,
                                settings.dateFormat,
                              ),
                            ),
                            trailing: MoneyText(
                              minor: transaction.amount.minor,
                              currency: byUuid[transaction.accountUuid.value]
                                      ?.currencyCode ??
                                  settings.defaultCurrencyCode,
                              type: transaction.type,
                            ),
                            onTap: () => context.push(
                              '/transaction/${transaction.id}/edit',
                            ),
                          ),
                      ],
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

class _MonthHeader extends StatelessWidget {
  const _MonthHeader({
    required this.month,
    required this.onPrevious,
    required this.onNext,
  });

  final DateTime month;
  final VoidCallback onPrevious;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Semantics(
          label: 'Previous month',
          child: IconButton(
            tooltip: 'Previous month',
            icon: const Icon(Icons.chevron_left),
            onPressed: onPrevious,
          ),
        ),
        Expanded(
          child: Text(
            monthLabel(month),
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleLarge,
          ),
        ),
        Semantics(
          label: 'Next month',
          child: IconButton(
            tooltip: 'Next month',
            icon: const Icon(Icons.chevron_right),
            onPressed: onNext,
          ),
        ),
      ],
    );
  }
}

class _BalanceCard extends StatelessWidget {
  const _BalanceCard({required this.totals});

  final List<CurrencyTotals> totals;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Balance by currency',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            if (totals.isEmpty)
              const Text('No accounts yet.')
            else
              for (final total in totals)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: [
                      Text(total.currencyCode),
                      const Spacer(),
                      MoneyText(
                        minor: total.balanceMinor,
                        currency: CurrencyCode.parse(total.currencyCode),
                      ),
                    ],
                  ),
                ),
          ],
        ),
      ),
    );
  }
}

class _MonthTotalsCard extends StatelessWidget {
  const _MonthTotalsCard({required this.totals});

  final List<CurrencyTotals> totals;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'This month',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            for (final total in totals)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      total.currencyCode,
                      style: Theme.of(context).textTheme.labelLarge,
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Expanded(
                          child: MoneyText(
                            minor: total.incomeMinor,
                            currency: CurrencyCode.parse(total.currencyCode),
                            type: TransactionType.income,
                          ),
                        ),
                        Expanded(
                          child: MoneyText(
                            minor: total.expenseMinor,
                            currency: CurrencyCode.parse(total.currencyCode),
                            type: TransactionType.expense,
                          ),
                        ),
                        Expanded(
                          child: MoneyText(
                            minor: total.netMinor,
                            currency: CurrencyCode.parse(total.currencyCode),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
