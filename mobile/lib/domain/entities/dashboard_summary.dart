import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';

/// Totals are always kept separate by ISO currency code. Never add two rows
/// with different currencies together.
final class CurrencyTotals {
  const CurrencyTotals({
    required this.currencyCode,
    required this.balanceMinor,
    required this.incomeMinor,
    required this.expenseMinor,
  });

  final String currencyCode;
  final int balanceMinor;
  final int incomeMinor;
  final int expenseMinor;

  int get netMinor => incomeMinor - expenseMinor;
}

final class CategoryTotal {
  const CategoryTotal({
    required this.category,
    required this.currencyCode,
    required this.amountMinor,
  });

  final String category;
  final String currencyCode;
  final int amountMinor;
}

final class MonthSeriesPoint {
  const MonthSeriesPoint({
    required this.year,
    required this.month,
    required this.currencyCode,
    required this.incomeMinor,
    required this.expenseMinor,
  });

  final int year;
  final int month;
  final String currencyCode;
  final int incomeMinor;
  final int expenseMinor;
}

/// Small, SQL-computed result set. It contains only grouped rows and the five
/// most recent transactions, so assembling [DashboardSummary] never walks the
/// whole ledger on the UI thread.
final class DashboardAggregateData {
  const DashboardAggregateData({
    required this.accountDeltas,
    required this.monthTotals,
    required this.categoryTotals,
    required this.sixMonthSeries,
    required this.recentTransactions,
  });

  final Map<String, int> accountDeltas;
  final List<CurrencyTotals> monthTotals;
  final List<CategoryTotal> categoryTotals;
  final List<MonthSeriesPoint> sixMonthSeries;
  final List<LedgerTransaction> recentTransactions;
}

final class DashboardSummary {
  const DashboardSummary({
    required this.balances,
    required this.monthTotals,
    required this.categoryTotals,
    required this.sixMonthSeries,
    required this.recentTransactions,
  });

  final List<CurrencyTotals> balances;
  final List<CurrencyTotals> monthTotals;
  final List<CategoryTotal> categoryTotals;
  final List<MonthSeriesPoint> sixMonthSeries;
  final List<LedgerTransaction> recentTransactions;

  bool get isEmpty => recentTransactions.isEmpty && balances.isEmpty;
}
