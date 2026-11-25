import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:pocket_ledger_mobile/data/database/daos/ledger_dao.dart';
import 'package:pocket_ledger_mobile/data/database/database.dart' as db;
import 'package:pocket_ledger_mobile/data/repositories/drift_ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/repositories/ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

String _iso(DateTime value) =>
    '${value.year.toString().padLeft(4, '0')}-'
    '${value.month.toString().padLeft(2, '0')}-'
    '${value.day.toString().padLeft(2, '0')}';

void main() {
  late db.AppDatabase database;
  late LedgerRepository repository;

  setUp(() async {
    database = db.AppDatabase(NativeDatabase.memory());
    repository = DriftLedgerRepository(LedgerDao(database));
    await database.ensureSeeded();
  });

  tearDown(() async {
    await database.close();
  });

  test('dashboard inputs are grouped in SQL, not by walking rows in Dart',
      () async {
    final account = (await repository.defaultAccount())!;
    final now = DateTime.now();
    final month = DateTime(now.year, now.month, 1);
    final previous = DateTime(now.year, now.month - 1, 1);

    await repository.addTransaction(
      type: TransactionType.income,
      amount: '50.00',
      category: 'Salary',
      transactionDate: _iso(month),
    );
    await repository.addTransaction(
      type: TransactionType.expense,
      amount: '20.00',
      category: 'Food',
      transactionDate: _iso(month),
    );
    await repository.addTransaction(
      type: TransactionType.expense,
      amount: '10.00',
      category: 'Travel',
      transactionDate: _iso(previous),
    );

    final deltas = await repository.watchAccountDeltas().first;
    expect(deltas[account.uuid.value], 2_000);

    final aggregate = await repository
        .watchDashboardAggregate(
          month: month,
          chartCurrencyCode: 'INR',
        )
        .first;
    expect(aggregate.monthTotals.single.incomeMinor, 5_000);
    expect(aggregate.monthTotals.single.expenseMinor, 2_000);
    expect(
      aggregate.categoryTotals
          .firstWhere((item) => item.category == 'Food')
          .amountMinor,
      2_000,
    );
    expect(
      aggregate.categoryTotals.map((item) => item.category),
      isNot(contains('Travel')),
    );
    final point = aggregate.sixMonthSeries.firstWhere(
      (item) => item.year == month.year && item.month == month.month,
    );
    expect(point.incomeMinor, 5_000);
    expect(point.expenseMinor, 2_000);
    expect(aggregate.recentTransactions, hasLength(3));
  });
}
