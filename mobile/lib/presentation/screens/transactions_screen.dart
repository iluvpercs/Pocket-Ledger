import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/category.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction_filter.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/presentation/common/formatters.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/async_value_view.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/empty_state_view.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/transaction_tile.dart';

class TransactionsScreen extends ConsumerStatefulWidget {
  const TransactionsScreen({super.key});

  @override
  ConsumerState<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends ConsumerState<TransactionsScreen> {
  final _scrollController = ScrollController();
  final _selected = <int>{};
  bool _showFilters = false;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(() {
      if (_scrollController.position.extentAfter < 400) {
        ref.read(transactionPageSizeProvider.notifier).loadMore();
      }
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final filter = ref.watch(transactionFilterProvider);
    final transactions = ref.watch(filteredTransactionsProvider(filter));
    final accounts = ref.watch(accountsProvider);
    final categories = ref.watch(categoriesProvider);
    final settings = ref.watch(settingsProvider).value ?? const LedgerSettings(
          defaultCurrencyCode: CurrencyCode.inr,
          dateFormat: LedgerDateFormat.iso,
          themeMode: LedgerThemeMode.dark,
        );

    return Scaffold(
      appBar: AppBar(
        title: Text(
          _selected.isEmpty ? 'Transactions' : '${_selected.length} selected',
        ),
        actions: [
          if (_selected.isEmpty)
            Semantics(
              label: 'Toggle filters',
              child: IconButton(
                tooltip: 'Toggle filters',
                icon:
                    Icon(_showFilters ? Icons.filter_alt : Icons.filter_alt_off),
                onPressed: () => setState(() => _showFilters = !_showFilters),
              ),
            )
          else ...[
            Semantics(
              label: 'Delete selected transactions',
              child: IconButton(
                tooltip: 'Delete selected',
                icon: const Icon(Icons.delete_outline),
                onPressed: _deleteSelected,
              ),
            ),
            Semantics(
              label: 'Clear selection',
              child: IconButton(
                tooltip: 'Clear selection',
                icon: const Icon(Icons.close),
                onPressed: () => setState(_selected.clear),
              ),
            ),
          ],
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
        value: accounts,
        builder: (accountList) {
          final byUuid = {
            for (final account in accountList) account.uuid.value: account,
          };
          return AsyncValueView(
            value: categories,
            builder: (categoryList) {
              return Column(
                children: [
                  if (_showFilters)
                    _FilterPanel(
                      filter: filter,
                      accounts: accountList,
                      categories: categoryList,
                      onChanged: (next) {
                        ref
                            .read(transactionFilterProvider.notifier)
                            .set(next);
                        ref
                            .read(transactionPageSizeProvider.notifier)
                            .reset();
                      },
                      onReset: () {
                        ref.read(transactionFilterProvider.notifier).reset();
                        setState(() => _selected.clear());
                      },
                    ),
                  Expanded(
                    child: AsyncValueView(
                      value: transactions,
                      onRetry: () =>
                          ref.invalidate(filteredTransactionsProvider(filter)),
                      builder: (rows) {
                        if (rows.isEmpty) {
                          return Padding(
                            padding: const EdgeInsets.all(16),
                            child: EmptyStateView(
                              icon: Icons.receipt_long_outlined,
                              title: filter.isEmpty
                                  ? 'No transactions yet'
                                  : 'No matching transactions',
                              message: filter.isEmpty
                                  ? 'Add your first transaction to start '
                                      'tracking your ledger.'
                                  : 'Try a different search or filter.',
                              actionLabel:
                                  filter.isEmpty ? 'Add transaction' : null,
                              onAction: filter.isEmpty
                                  ? () => context.push('/transaction/new')
                                  : null,
                            ),
                          );
                        }

                        // One flat, lazily built list: date headers are
                        // ordinary items, so there is no nested scroll view
                        // for the gesture arena to fight over.
                        final items = <Object>[];
                        for (final entry in _groupByDay(rows).entries) {
                          items.add(entry.key);
                          items.addAll(entry.value);
                        }

                        return ListView.builder(
                          controller: _scrollController,
                          padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
                          itemCount: items.length,
                          itemBuilder: (context, index) {
                            final item = items[index];
                            if (item is String) {
                              return Padding(
                                key: ValueKey('day-$item'),
                                padding: const EdgeInsets.fromLTRB(4, 12, 4, 4),
                                child: Text(
                                  formatDate(item, settings.dateFormat),
                                  style: Theme.of(context).textTheme.labelLarge,
                                ),
                              );
                            }
                            final transaction = item as LedgerTransaction;
                            return Dismissible(
                              key: ValueKey('transaction-${transaction.id}'),
                              direction: DismissDirection.endToStart,
                              background: Container(
                                alignment: Alignment.centerRight,
                                padding: const EdgeInsets.only(right: 20),
                                color: Theme.of(context).colorScheme.error,
                                child: const Icon(Icons.delete),
                              ),
                              onDismissed: (_) => _deleteOne(transaction.id),
                              child: TransactionTile(
                                transaction: transaction,
                                currency: byUuid[transaction.accountUuid.value]
                                        ?.currencyCode ??
                                    settings.defaultCurrencyCode,
                                dateFormat: settings.dateFormat,
                                selected: _selected.contains(transaction.id),
                                onTap: () => _onTap(transaction.id),
                                onLongPress: () => _toggle(transaction.id),
                              ),
                            );
                          },
                        );
                      },
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

  Map<String, List<LedgerTransaction>> _groupByDay(
    List<LedgerTransaction> rows,
  ) {
    final groups = <String, List<LedgerTransaction>>{};
    for (final row in rows) {
      groups.putIfAbsent(row.transactionDate, () => []).add(row);
    }
    return groups;
  }

  void _toggle(int id) {
    setState(() {
      if (_selected.contains(id)) {
        _selected.remove(id);
      } else {
        _selected.add(id);
      }
    });
  }

  void _onTap(int id) {
    if (_selected.isNotEmpty) {
      _toggle(id);
      return;
    }
    context.push('/transaction/$id/edit');
  }

  Future<void> _deleteOne(int id) async {
    try {
      await ref.read(ledgerRepositoryProvider).softDeleteTransaction(id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Transaction deleted.'),
          action: SnackBarAction(
            label: 'Undo',
            onPressed: () => ref
                .read(ledgerRepositoryProvider)
                .restoreTransaction(id),
          ),
        ),
      );
    } catch (error) {
      _showError(error);
    }
  }

  Future<void> _deleteSelected() async {
    final ids = _selected.toList();
    if (ids.isEmpty) return;
    try {
      await ref.read(ledgerRepositoryProvider).softDeleteTransactions(ids);
      if (!mounted) return;
      setState(_selected.clear);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${ids.length} transactions deleted.'),
          action: SnackBarAction(
            label: 'Undo',
            onPressed: () => ref
                .read(ledgerRepositoryProvider)
                .restoreTransactions(ids),
          ),
        ),
      );
    } catch (error) {
      _showError(error);
    }
  }

  void _showError(Object error) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(error.toString())),
    );
  }
}

class _FilterPanel extends StatelessWidget {
  const _FilterPanel({
    required this.filter,
    required this.accounts,
    required this.categories,
    required this.onChanged,
    required this.onReset,
  });

  final TransactionFilter filter;
  final List<Account> accounts;
  final List<LedgerCategory> categories;
  final ValueChanged<TransactionFilter> onChanged;
  final VoidCallback onReset;

  @override
  Widget build(BuildContext context) {
    final categoryNames = [
      for (final category in categories) category.name,
      if (filter.category != null &&
          !categories.any((item) => item.name == filter.category))
        filter.category!,
    ];
    return Card(
      margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            TextField(
              decoration: const InputDecoration(
                labelText: 'Search note or category',
                prefixIcon: Icon(Icons.search),
                border: OutlineInputBorder(),
              ),
              onChanged: (value) =>
                  onChanged(filter.copyWith(search: value)),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                DropdownButton<TransactionTypeFilter>(
                  value: filter.type,
                  items: [
                    for (final type in TransactionTypeFilter.values)
                      DropdownMenuItem(value: type, child: Text(type.id)),
                  ],
                  onChanged: (value) =>
                      onChanged(filter.copyWith(type: value!)),
                ),
                DropdownButton<Uuid?>(
                  value: filter.accountUuid,
                  hint: const Text('All accounts'),
                  items: [
                    const DropdownMenuItem<Uuid?>(
                      value: null,
                      child: Text('All accounts'),
                    ),
                    for (final account in accounts)
                      DropdownMenuItem<Uuid?>(
                        value: account.uuid,
                        child: Text(account.name),
                      ),
                  ],
                  onChanged: (value) => onChanged(
                    filter.copyWith(
                      accountUuid: value,
                      clearAccount: value == null,
                    ),
                  ),
                ),
                DropdownButton<String?>(
                  value: filter.category,
                  hint: const Text('All categories'),
                  items: [
                    const DropdownMenuItem<String?>(
                      value: null,
                      child: Text('All categories'),
                    ),
                    for (final name in categoryNames)
                      DropdownMenuItem<String?>(
                        value: name,
                        child: Text(name),
                      ),
                  ],
                  onChanged: (value) => onChanged(
                    filter.copyWith(
                      category: value,
                      clearCategory: value == null,
                    ),
                  ),
                ),
                OutlinedButton.icon(
                  onPressed: () async {
                    final range = await showDateRangePicker(
                      context: context,
                      firstDate: DateTime(2000),
                      lastDate: DateTime(2100),
                      initialDateRange: filter.fromDate == null ||
                              filter.toDate == null
                          ? null
                          : DateTimeRange(
                              start: filter.fromDate!,
                              end: filter.toDate!,
                            ),
                    );
                    if (range == null) return;
                    onChanged(
                      filter.copyWith(
                        fromDate: range.start,
                        toDate: range.end,
                      ),
                    );
                  },
                  icon: const Icon(Icons.date_range),
                  label: const Text('Date range'),
                ),
                TextButton(
                  onPressed: onReset,
                  child: const Text('Clear'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
