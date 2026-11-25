import 'dart:convert';

import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:pocket_ledger_mobile/data/database/daos/ledger_dao.dart';
import 'package:pocket_ledger_mobile/data/database/database.dart' as db;
import 'package:pocket_ledger_mobile/data/repositories/drift_ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_constants.dart';
import 'package:pocket_ledger_mobile/domain/repositories/ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/validation_exception.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
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

  Future<List<db.SyncChange>> changesFor(String uuid) {
    return (database.select(database.syncChanges)
          ..where((row) => row.entityUuid.equals(uuid)))
        .get();
  }

  test('fresh database is schema v4 with deterministic INR default account',
      () async {
    final versionRow = await database.customSelect('PRAGMA user_version')
        .getSingle();
    expect(versionRow.data['user_version'], LedgerConstants.schemaVersion);

    final indexes = await database
        .customSelect('PRAGMA index_list(transactions)')
        .get();
    expect(
      indexes.map((row) => row.data['name']),
      contains('idx_tx_account_date_deleted'),
    );

    final account = await repository.defaultAccount();
    expect(account, isNotNull);
    expect(account!.uuid.value, LedgerConstants.defaultAccountUuid);
    expect(account.name, LedgerConstants.defaultAccountName);
    expect(account.currencyCode.value, 'INR');
    expect(account.precision.value, 2);
    expect(account.isDefault, isTrue);
    expect(account.revision, 1);
    expect(account.syncState.dbValue, 'pending');

    final meta = await database.select(database.appMeta).get();
    expect(
      meta.map((row) => row.key),
      containsAll([
        LedgerConstants.appMetaDeviceIdKey,
        LedgerConstants.appMetaDeviceNameKey,
        LedgerConstants.appMetaDevicePlatformKey,
      ]),
    );
    final deviceId =
        meta.firstWhere((row) => row.key == LedgerConstants.appMetaDeviceIdKey)
            .value;
    expect(Uuid.parse(deviceId).value, deviceId);
    final device = await (database.select(database.devices)
          ..where((row) => row.deviceId.equals(deviceId)))
        .getSingle();
    expect(device.platform, LedgerConstants.androidPlatform);
  });

  test('transaction insert stores integer minor units and one v2 outbox event',
      () async {
    final id = await repository.addTransaction(
      type: TransactionType.expense,
      amount: '12.34',
      category: 'Food',
      transactionDate: '2026-11-25',
      description: 'Lunch',
    );

    final row = await (database.select(database.transactions)
          ..where((item) => item.id.equals(id)))
        .getSingle();
    expect(row.amountMinor, 1234);
    expect(row.transactionType, 'expense');
    expect(row.transactionDate, '2026-11-25');
    expect(row.description, 'Lunch');
    expect(row.revision, 1);
    expect(row.syncState, 'pending');

    final changes = await changesFor(row.uuid);
    expect(changes, hasLength(1));
    final change = changes.single;
    expect(change.payloadVersion, 2);
    expect(change.entityType, 'transaction');
    expect(change.operation, 'insert');
    expect(change.newRevision, 1);

    final payload = jsonDecode(change.payload) as Map<String, dynamic>;
    expect(payload['amount_minor'], 1234);
    expect(payload['currency_code'], 'INR');
    expect(payload['currency_precision'], 2);
    expect(payload.containsKey('amount'), isFalse);
  });

  test('soft delete writes a tombstone and v2 delete event atomically',
      () async {
    final id = await repository.addTransaction(
      type: TransactionType.income,
      amount: '50',
      category: 'Salary',
      transactionDate: '2026-11-24',
    );
    await repository.softDeleteTransaction(id);

    final row = await (database.select(database.transactions)
          ..where((item) => item.id.equals(id)))
        .getSingle();
    expect(row.deletedAtMs, isNotNull);
    expect(row.revision, 2);
    expect(row.syncState, 'pending');

    final changes = await changesFor(row.uuid);
    expect(changes, hasLength(2));
    expect(changes.last.operation, 'delete');
    expect(changes.last.baseRevision, 1);
    expect(changes.last.newRevision, 2);
    final payload = jsonDecode(changes.last.payload) as Map<String, dynamic>;
    expect(payload['deleted_at_ms'], isNotNull);
  });

  test('rename account increments revision and appends an update event',
      () async {
    final account = (await database.select(database.accounts).get()).single;
    await repository.renameAccount(
      Uuid.parse(account.uuid),
      'Everyday INR',
    );

    final updated = (await database.select(database.accounts).get()).single;
    expect(updated.name, 'Everyday INR');
    expect(updated.revision, 2);

    final changes = await changesFor(account.uuid);
    expect(changes, hasLength(2));
    expect(changes.last.operation, 'update');
    expect(changes.last.baseRevision, 1);
    expect(changes.last.newRevision, 2);
  });

  test('duplicate import hash does not append a partial outbox event', () async {
    await repository.addTransaction(
      type: TransactionType.expense,
      amount: '10.00',
      category: 'Food',
      transactionDate: '2026-11-25',
      importHash: 'duplicate-hash',
    );
    final before = (await database.select(database.syncChanges).get()).length;

    expect(
      () => repository.addTransaction(
        type: TransactionType.expense,
        amount: '11.00',
        category: 'Food',
        transactionDate: '2026-11-25',
        importHash: 'duplicate-hash',
      ),
      throwsA(anything),
    );

    final after = await database.select(database.syncChanges).get();
    expect(after, hasLength(before));
    expect(await database.select(database.transactions).get(), hasLength(1));
  });

  test('binary float amounts are rejected before writing', () async {
    expect(
      () => repository.addTransaction(
        type: TransactionType.expense,
        amount: 12.34,
        category: 'Food',
        transactionDate: '2026-11-25',
      ),
      throwsA(isA<DomainValidationException>()),
    );
    expect(await database.select(database.transactions).get(), isEmpty);
  });
}
