import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:pocket_ledger_mobile/data/database/daos/ledger_dao.dart';
import 'package:pocket_ledger_mobile/data/database/database.dart' as db;
import 'package:pocket_ledger_mobile/data/repositories/drift_ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/entities/category.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_constants.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/repositories/ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/services/ledger_aggregates.dart';
import 'package:pocket_ledger_mobile/domain/validation_exception.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

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

  test('createAccount stores opening balance and writes one insert event',
      () async {
    final uuid = await repository.createAccount(
      name: 'Savings',
      currencyCode: CurrencyCode.parse('USD'),
      openingMinor: 50_000,
      isDefault: true,
    );

    final accounts = await repository.watchAccounts().first;
    final account = accounts.firstWhere((item) => item.uuid == uuid);
    expect(account.name, 'Savings');
    expect(account.currencyCode.value, 'USD');
    expect(account.isDefault, isTrue);

    final balances = await repository.openingBalances();
    expect(balances[uuid.value], 50_000);

    final changes = await (database.select(database.syncChanges)
          ..where((row) => row.entityUuid.equals(uuid.value)))
        .get();
    expect(changes, hasLength(1));
    expect(changes.single.entityType, 'account');
    expect(changes.single.operation, 'insert');
    expect(changes.single.payloadVersion, 2);

    final oldDefault =
        (await database.select(database.accounts).get()).firstWhere(
      (row) => row.uuid == LedgerConstants.defaultAccountUuid,
    );
    expect(oldDefault.isDefault, isFalse);
    expect(oldDefault.revision, 2);
  });

  test('transaction update, soft delete and restore stay in sync', () async {
    final account = (await repository.defaultAccount())!;
    final id = await repository.addTransaction(
      type: TransactionType.expense,
      amount: '12.34',
      category: 'Food',
      transactionDate: '2026-11-25',
      description: 'Lunch',
      transactionTimeMs: 1_765_000_000_000,
    );
    final original = (await repository.transactionById(id))!;

    await repository.updateTransaction(
      id: id,
      type: TransactionType.income,
      amount: '20.00',
      category: 'Refund',
      transactionDate: '2026-11-26',
      accountUuid: account.uuid,
      description: 'Reimbursement',
      transactionTimeMs: 1_765_100_000_000,
    );
    final updated = (await repository.transactionById(id))!;
    expect(updated.type, TransactionType.income);
    expect(updated.amount.minor, 2_000);
    expect(updated.category, 'Refund');
    expect(updated.revision, original.revision + 1);
    expect((await repository.transactionTimes())[updated.uuid.value],
        1_765_100_000_000);

    await repository.softDeleteTransaction(id);
    expect((await repository.transactionById(id))!.deletedAt, isNotNull);
    expect(await repository.watchLiveTransactions().first, isEmpty);

    await repository.restoreTransaction(id);
    final restored = (await repository.transactionById(id))!;
    expect(restored.deletedAt, isNull);
    expect(restored.revision, original.revision + 3);
    expect(await repository.watchLiveTransactions().first, hasLength(1));

    final changes = await (database.select(database.syncChanges)
          ..where((row) => row.entityUuid.equals(original.uuid.value)))
        .get();
    expect(changes.map((item) => item.operation), [
      'insert',
      'update',
      'delete',
      'update',
    ]);
  });

  test('bulk delete and restore work through the repository', () async {
    final first = await repository.addTransaction(
      type: TransactionType.expense,
      amount: '10',
      category: 'Food',
      transactionDate: '2026-11-25',
    );
    final second = await repository.addTransaction(
      type: TransactionType.expense,
      amount: '20',
      category: 'Travel',
      transactionDate: '2026-11-24',
    );

    await repository.softDeleteTransactions([first, second]);
    expect(await repository.watchLiveTransactions().first, isEmpty);

    await repository.restoreTransactions([first, second]);
    expect(await repository.watchLiveTransactions().first, hasLength(2));
  });

  test('account delete requires cascade when transactions exist', () async {
    final uuid = await repository.createAccount(
      name: 'Travel wallet',
      currencyCode: CurrencyCode.parse('EUR'),
    );
    await repository.addTransaction(
      type: TransactionType.expense,
      amount: '30',
      category: 'Travel',
      transactionDate: '2026-11-25',
      accountUuid: uuid,
    );

    expect(
      () => repository.softDeleteAccount(uuid, cascade: false),
      throwsA(isA<DomainValidationException>()),
    );

    await repository.softDeleteAccount(uuid, cascade: true);
    final accounts = await repository.watchAccounts().first;
    expect(accounts.map((item) => item.uuid), isNot(contains(uuid)));
    expect(await repository.watchLiveTransactions().first, isEmpty);
    expect((await repository.defaultAccount())!.name,
        LedgerConstants.defaultAccountName);
  });

  test('opening balance plus signed transactions produces live balances',
      () async {
    final account = (await repository.defaultAccount())!;
    await repository.createAccount(
      name: 'Reserve',
      currencyCode: CurrencyCode.parse('USD'),
      openingMinor: 10_000,
    );
    final accounts = await repository.watchAccounts().first;
    final reserve = accounts.firstWhere((item) => item.name == 'Reserve');

    await repository.addTransaction(
      type: TransactionType.expense,
      amount: '25.50',
      category: 'Food',
      transactionDate: '2026-11-25',
      accountUuid: reserve.uuid,
    );
    await repository.addTransaction(
      type: TransactionType.income,
      amount: '100.00',
      category: 'Salary',
      transactionDate: '2026-11-26',
      accountUuid: reserve.uuid,
    );

    final summaries = buildAccountSummaries(
      accounts,
      await repository.watchLiveTransactions().first,
      await repository.openingBalances(),
    );
    final reserveSummary =
        summaries.firstWhere((item) => item.account.uuid == reserve.uuid);
    final defaultSummary =
        summaries.firstWhere((item) => item.account.uuid == account.uuid);
    expect(reserveSummary.balanceMinor, 17_450);
    expect(defaultSummary.balanceMinor, 0);
  });

  test('settings and custom categories persist in app_meta', () async {
    final account = (await repository.defaultAccount())!;
    final original = await repository.settings();
    await repository.updateSettings(
      original.copyWith(
        defaultCurrencyCode: CurrencyCode.parse('USD'),
        defaultAccountUuid: account.uuid,
        dateFormat: LedgerDateFormat.slashDmy,
        themeMode: LedgerThemeMode.system,
      ),
    );
    final reloaded = await repository.settings();
    expect(reloaded.defaultCurrencyCode.value, 'USD');
    expect(reloaded.defaultAccountUuid, account.uuid);
    expect(reloaded.dateFormat, LedgerDateFormat.slashDmy);
    expect(reloaded.themeMode, LedgerThemeMode.system);

    await repository.saveCategories(const [
      LedgerCategory(id: 'custom-pets', name: 'Pets', isDefault: false),
    ]);
    final categories = await repository.categories();
    expect(categories.map((item) => item.name), contains('Pets'));
    expect(categories.where((item) => item.isDefault).length,
        LedgerDefaults.categories.length);
  });

  test('strict amount failure writes no row and no outbox event', () async {
    final before = (await database.select(database.syncChanges).get()).length;

    expect(
      () => repository.addTransaction(
        type: TransactionType.expense,
        amount: '12.345',
        category: 'Food',
        transactionDate: '2026-11-25',
      ),
      throwsA(isA<DomainValidationException>()),
    );

    expect(await database.select(database.transactions).get(), isEmpty);
    expect((await database.select(database.syncChanges).get()), hasLength(before));
  });

  test('import hashes are scoped to their account', () async {
    final first = (await repository.defaultAccount())!;
    final secondUuid = await repository.createAccount(
      name: 'Second',
      currencyCode: CurrencyCode.parse('INR'),
    );

    await repository.addTransaction(
      type: TransactionType.expense,
      amount: '10',
      category: 'Food',
      transactionDate: '2026-11-25',
      importHash: 'shared-hash',
      accountUuid: first.uuid,
    );
    await repository.addTransaction(
      type: TransactionType.expense,
      amount: '10',
      category: 'Food',
      transactionDate: '2026-11-25',
      importHash: 'shared-hash',
      accountUuid: secondUuid,
    );

    final hashes = await repository.importHashes();
    expect(hashes['shared-hash'], {first.uuid.value, secondUuid.value});
  });

  test('deleteAllData soft-deletes data but keeps the device identity', () async {
    final deviceId = await repository.deviceId();
    await repository.addTransaction(
      type: TransactionType.expense,
      amount: '10',
      category: 'Food',
      transactionDate: '2026-11-25',
    );

    await repository.deleteAllData();

    expect(await repository.watchAccounts().first, isEmpty);
    expect(await repository.watchLiveTransactions().first, isEmpty);
    final settings = await repository.settings();
    expect(settings.defaultCurrencyCode.value, 'INR');
    expect(settings.defaultAccountUuid, isNull);
    expect(await repository.deviceId(), deviceId);
    expect(await database.select(database.transactions).get(), hasLength(1));
    expect((await database.select(database.transactions).get()).single.deletedAtMs,
        isNotNull);
  });
}
