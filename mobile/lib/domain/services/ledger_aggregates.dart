import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/account_summary.dart';
import 'package:pocket_ledger_mobile/domain/entities/dashboard_summary.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

/// All balances are signed minor units and never cross currency boundaries.
List<AccountSummary> buildAccountSummaries(
  Iterable<Account> accounts,
  Iterable<LedgerTransaction> transactions,
  Map<String, int> openingBalances,
) {
  final deltas = <String, int>{};
  for (final transaction in transactions) {
    if (!transaction.isLive) continue;
    final delta = transaction.type == TransactionType.income
        ? transaction.amount.minor
        : -transaction.amount.minor;
    final key = transaction.accountUuid.value;
    deltas[key] = (deltas[key] ?? 0) + delta;
  }

  return [
    for (final account in accounts.where((item) => item.isLive))
      AccountSummary(
        account: account,
        balanceMinor: (openingBalances[account.uuid.value] ?? 0) +
            (deltas[account.uuid.value] ?? 0),
      ),
  ];
}

DashboardSummary buildDashboardSummary({
  required Iterable<Account> accounts,
  required Iterable<LedgerTransaction> transactions,
  required Map<String, int> openingBalances,
  required DateTime selectedMonth,
  required String chartCurrencyCode,
}) {
  final summaries = buildAccountSummaries(accounts, transactions, openingBalances);
  final byUuid = <String, Account>{
    for (final account in accounts) account.uuid.value: account,
  };

  final balancesByCurrency = <String, int>{};
  for (final summary in summaries) {
    final code = summary.account.currencyCode.value;
    balancesByCurrency[code] =
        (balancesByCurrency[code] ?? 0) + summary.balanceMinor;
  }

  final monthStart = DateTime.utc(selectedMonth.year, selectedMonth.month);
  final monthEnd = DateTime.utc(selectedMonth.year, selectedMonth.month + 1);
  final monthByCurrency = <String, _MutableTotals>{};
  final categoryByCurrency = <String, Map<String, int>>{};
  final sixMonth = <String, _MutableTotals>{};
  final now = DateTime.utc(DateTime.now().year, DateTime.now().month);

  for (var offset = 5; offset >= 0; offset--) {
    final month = DateTime.utc(now.year, now.month - offset);
    sixMonth['${month.year}-${month.month.toString().padLeft(2, '0')}'] =
        _MutableTotals();
  }

  for (final transaction in transactions) {
    if (!transaction.isLive) continue;
    final account = byUuid[transaction.accountUuid.value];
    if (account == null) continue;
    final code = account.currencyCode.value;
    final date = DateTime.tryParse('${transaction.transactionDate}T00:00:00Z');
    if (date == null) continue;

    final isSelectedMonth =
        !date.isBefore(monthStart) && date.isBefore(monthEnd);
    if (isSelectedMonth) {
      final totals = monthByCurrency.putIfAbsent(code, _MutableTotals.new);
      _add(totals, transaction);
      if (transaction.type == TransactionType.expense) {
        final categories =
            categoryByCurrency.putIfAbsent(code, () => <String, int>{});
        categories[transaction.category] =
            (categories[transaction.category] ?? 0) + transaction.amount.minor;
      }
    }

    if (code == chartCurrencyCode) {
      final key = '${date.year}-${date.month.toString().padLeft(2, '0')}';
      final totals = sixMonth[key];
      if (totals != null) _add(totals, transaction);
    }
  }

  for (final account in accounts.where((item) => item.isLive)) {
    monthByCurrency.putIfAbsent(
      account.currencyCode.value,
      _MutableTotals.new,
    );
  }

  final recent = transactions.where((item) => item.isLive).toList()
    ..sort((a, b) {
      final byDate = b.transactionDate.compareTo(a.transactionDate);
      return byDate != 0 ? byDate : b.id.compareTo(a.id);
    });

  return DashboardSummary(
    balances: [
      for (final entry in balancesByCurrency.entries)
        CurrencyTotals(
          currencyCode: entry.key,
          balanceMinor: entry.value,
          incomeMinor: 0,
          expenseMinor: 0,
        ),
    ]..sort((a, b) => a.currencyCode.compareTo(b.currencyCode)),
    monthTotals: [
      for (final entry in monthByCurrency.entries)
        CurrencyTotals(
          currencyCode: entry.key,
          balanceMinor: balancesByCurrency[entry.key] ?? 0,
          incomeMinor: entry.value.income,
          expenseMinor: entry.value.expense,
        ),
    ]..sort((a, b) => a.currencyCode.compareTo(b.currencyCode)),
    categoryTotals: [
      for (final currencyEntry in categoryByCurrency.entries)
        for (final categoryEntry in currencyEntry.value.entries)
          CategoryTotal(
            category: categoryEntry.key,
            currencyCode: currencyEntry.key,
            amountMinor: categoryEntry.value,
          ),
    ]..sort((a, b) => b.amountMinor.compareTo(a.amountMinor)),
    sixMonthSeries: [
      for (final entry in sixMonth.entries)
        MonthSeriesPoint(
          year: int.parse(entry.key.split('-').first),
          month: int.parse(entry.key.split('-').last),
          currencyCode: chartCurrencyCode,
          incomeMinor: entry.value.income,
          expenseMinor: entry.value.expense,
        ),
    ],
    recentTransactions: recent.take(5).toList(),
  );
}

void _add(_MutableTotals totals, LedgerTransaction transaction) {
  if (transaction.type == TransactionType.income) {
    totals.income += transaction.amount.minor;
  } else {
    totals.expense += transaction.amount.minor;
  }
}

class _MutableTotals {
  int income = 0;
  int expense = 0;
}

/// Builds account cards from the SQL delta map. Only live accounts are walked.
List<AccountSummary> assembleAccountSummaries(
  Iterable<Account> accounts,
  Map<String, int> deltas,
  Map<String, int> openingBalances,
) {
  return [
    for (final account in accounts.where((item) => item.isLive))
      AccountSummary(
        account: account,
        balanceMinor: (openingBalances[account.uuid.value] ?? 0) +
            (deltas[account.uuid.value] ?? 0),
      ),
  ];
}

/// Builds the dashboard from grouped SQL results. Only the per-account delta
/// map is iterated here; transaction rows have already been counted by SQLite.
DashboardSummary assembleDashboardSummary({
  required Iterable<Account> accounts,
  required Map<String, int> openingBalances,
  required DashboardAggregateData aggregate,
  required String chartCurrencyCode,
}) {
  final liveAccounts = accounts.where((item) => item.isLive).toList();
  final balancesByCurrency = <String, int>{};
  for (final account in liveAccounts) {
    final code = account.currencyCode.value;
    balancesByCurrency[code] = (balancesByCurrency[code] ?? 0) +
        (openingBalances[account.uuid.value] ?? 0) +
        (aggregate.accountDeltas[account.uuid.value] ?? 0);
  }

  final monthByCurrency = <String, CurrencyTotals>{
    for (final account in liveAccounts)
      account.currencyCode.value: CurrencyTotals(
        currencyCode: account.currencyCode.value,
        balanceMinor: balancesByCurrency[account.currencyCode.value] ?? 0,
        incomeMinor: 0,
        expenseMinor: 0,
      ),
  };
  for (final total in aggregate.monthTotals) {
    monthByCurrency[total.currencyCode] = CurrencyTotals(
      currencyCode: total.currencyCode,
      balanceMinor: balancesByCurrency[total.currencyCode] ?? 0,
      incomeMinor: total.incomeMinor,
      expenseMinor: total.expenseMinor,
    );
  }

  final seriesByKey = {
    for (final point in aggregate.sixMonthSeries)
      '${point.year}-${point.month.toString().padLeft(2, '0')}': point,
  };
  final now = DateTime.now().toUtc();
  final sixMonth = <MonthSeriesPoint>[
    for (var offset = 5; offset >= 0; offset--)
      () {
        final month = DateTime.utc(now.year, now.month - offset);
        final key =
            '${month.year}-${month.month.toString().padLeft(2, '0')}';
        final point = seriesByKey[key];
        return MonthSeriesPoint(
          year: month.year,
          month: month.month,
          currencyCode: chartCurrencyCode,
          incomeMinor: point?.incomeMinor ?? 0,
          expenseMinor: point?.expenseMinor ?? 0,
        );
      }(),
  ];

  return DashboardSummary(
    balances: [
      for (final entry in balancesByCurrency.entries)
        CurrencyTotals(
          currencyCode: entry.key,
          balanceMinor: entry.value,
          incomeMinor: 0,
          expenseMinor: 0,
        ),
    ]..sort((a, b) => a.currencyCode.compareTo(b.currencyCode)),
    monthTotals: monthByCurrency.values.toList()
      ..sort((a, b) => a.currencyCode.compareTo(b.currencyCode)),
    categoryTotals: aggregate.categoryTotals.toList()
      ..sort((a, b) => b.amountMinor.compareTo(a.amountMinor)),
    sixMonthSeries: sixMonth,
    recentTransactions: aggregate.recentTransactions,
  );
}
