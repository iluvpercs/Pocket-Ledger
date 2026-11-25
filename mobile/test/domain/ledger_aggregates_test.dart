import 'package:flutter_test/flutter_test.dart';

import 'package:pocket_ledger_mobile/domain/services/ledger_aggregates.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

import '../support/test_data.dart';

String _iso(DateTime value) =>
    '${value.year.toString().padLeft(4, '0')}-'
    '${value.month.toString().padLeft(2, '0')}-'
    '${value.day.toString().padLeft(2, '0')}';

void main() {
  test('account balances add opening minor units to signed transaction deltas',
      () {
    final account = testAccount();
    final transactions = [
      testTransaction(
        account: account,
        id: 1,
        amountMinor: 2_000,
        category: 'Food',
      ),
      testTransaction(
        account: account,
        id: 2,
        amountMinor: 5_000,
        type: TransactionType.income,
        category: 'Salary',
      ),
    ];

    final summaries = buildAccountSummaries(
      [account],
      transactions,
      {account.uuid.value: 10_000},
    );

    expect(summaries, hasLength(1));
    expect(summaries.single.balanceMinor, 13_000);
  });

  test('dashboard keeps currencies separate and aggregates by month and category',
      () {
    final inr = testAccount(name: 'Cash', currencyCode: 'INR');
    final usd = testAccount(
      name: 'Dollar wallet',
      currencyCode: 'USD',
      isDefault: false,
    );
    final now = DateTime.now();
    final month = DateTime(now.year, now.month, 1);
    final previous = DateTime(now.year, now.month - 1, 1);
    final transactions = [
      testTransaction(
        account: inr,
        id: 1,
        amountMinor: 2_000,
        category: 'Food',
        transactionDate: _iso(month),
      ),
      testTransaction(
        account: inr,
        id: 2,
        amountMinor: 5_000,
        type: TransactionType.income,
        category: 'Salary',
        transactionDate: _iso(month),
      ),
      testTransaction(
        account: inr,
        id: 3,
        amountMinor: 1_000,
        category: 'Travel',
        transactionDate: _iso(previous),
      ),
      testTransaction(
        account: usd,
        id: 4,
        amountMinor: 3_000,
        category: 'Shopping',
        transactionDate: _iso(month),
      ),
    ];

    final summary = buildDashboardSummary(
      accounts: [inr, usd],
      transactions: transactions,
      openingBalances: {
        inr.uuid.value: 10_000,
        usd.uuid.value: 5_000,
      },
      selectedMonth: month,
      chartCurrencyCode: 'INR',
    );

    expect(
      summary.balances.map((item) => item.currencyCode).toList(),
      ['INR', 'USD'],
    );
    expect(
      summary.balances.map((item) => item.balanceMinor).toList(),
      [12_000, 2_000],
    );

    final inrMonth = summary.monthTotals.firstWhere(
      (item) => item.currencyCode == 'INR',
    );
    expect(inrMonth.incomeMinor, 5_000);
    expect(inrMonth.expenseMinor, 2_000);
    expect(inrMonth.netMinor, 3_000);

    final usdMonth = summary.monthTotals.firstWhere(
      (item) => item.currencyCode == 'USD',
    );
    expect(usdMonth.incomeMinor, 0);
    expect(usdMonth.expenseMinor, 3_000);

    expect(
      summary.categoryTotals.firstWhere((item) => item.category == 'Food')
          .amountMinor,
      2_000,
    );
    expect(
      summary.categoryTotals.firstWhere((item) => item.category == 'Shopping')
          .currencyCode,
      'USD',
    );

    expect(summary.sixMonthSeries, hasLength(6));
    final current = summary.sixMonthSeries.last;
    expect(current.year, now.year);
    expect(current.month, now.month);
    expect(current.incomeMinor, 5_000);
    expect(current.expenseMinor, 2_000);
    expect(summary.recentTransactions, hasLength(4));
  });

  test('empty dashboard has no totals and reports isEmpty', () {
    final summary = buildDashboardSummary(
      accounts: const [],
      transactions: const [],
      openingBalances: const {},
      selectedMonth: DateTime(2026, 11),
      chartCurrencyCode: 'INR',
    );

    expect(summary.isEmpty, isTrue);
    expect(summary.balances, isEmpty);
    expect(summary.monthTotals, isEmpty);
    expect(summary.categoryTotals, isEmpty);
    expect(summary.recentTransactions, isEmpty);
    expect(summary.sixMonthSeries, hasLength(6));
  });
}
