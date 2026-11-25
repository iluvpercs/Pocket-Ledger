import 'dart:async';

import 'package:drift/drift.dart';

import 'package:pocket_ledger_mobile/data/database/database.dart' as db;
import 'package:pocket_ledger_mobile/data/database/tables/tables.dart';
import 'package:pocket_ledger_mobile/data/mappers/row_mappers.dart';
import 'package:pocket_ledger_mobile/data/mappers/sync_payload.dart';
import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_constants.dart';
import 'package:pocket_ledger_mobile/domain/entities/sync_state.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/validation_exception.dart';
import 'package:pocket_ledger_mobile/domain/validators/input_validators.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

/// Local persistence plus the append-only outbox. There is no sync transport.
class LedgerDao {
  LedgerDao(this._db);

  final db.AppDatabase _db;

  Future<void> ensureBootstrapped() => _db.ensureSeeded();

  Future<Account?> defaultAccount() async {
    final row = await _defaultAccountRow();
    return row == null ? null : mapAccount(row);
  }

  Stream<Account?> watchDefaultAccount() {
    return (_db.select(_db.accounts)
          ..where((row) => row.isDefault.equals(true) & row.deletedAtMs.isNull())
          ..limit(1))
        .watch()
        .map((rows) => rows.isEmpty ? null : mapAccount(rows.first));
  }

  Future<Account?> accountByUuid(Uuid uuid) async {
    final row = await _accountRow(uuid, liveOnly: true);
    return row == null ? null : mapAccount(row);
  }

  Future<Uuid> insertAccount({
    required String name,
    required CurrencyCode currencyCode,
    required bool isDefault,
  }) async {
    final cleanName = InputValidators.requiredText(name, 'Account name');
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();
    final uuid = Uuid.generate();

    return _db.transaction(() async {
      if (isDefault) {
        final previousRow = await _defaultAccountRow();
        if (previousRow != null) {
          final previous = mapAccount(previousRow);
          final updated = previous.copyWith(
            isDefault: false,
            updatedAt: now,
            revision: previous.revision + 1,
            lastModifiedBy: deviceId,
            syncState: SyncState.pending,
          );
          await (_db.update(_db.accounts)
                ..where((row) => row.id.equals(previousRow.id)))
              .write(
            AccountsCompanion(
              isDefault: Value(false),
              updatedAtMs: Value(now.value),
              revision: Value(updated.revision),
              lastModifiedBy: Value(deviceId.value),
              syncState: Value(updated.syncState.dbValue),
            ),
          );
          await _appendAccountChange(
            entity: updated,
            operation: 'update',
            baseRevision: previous.revision,
            deviceId: deviceId,
            recordedAt: now,
          );
        }
      }

      final account = Account(
        uuid: uuid,
        name: cleanName,
        currencyCode: currencyCode,
        isDefault: isDefault,
        createdAt: now,
        updatedAt: now,
        revision: 1,
        originDeviceId: deviceId,
        lastModifiedBy: deviceId,
        syncState: SyncState.pending,
      );

      await _db.into(_db.accounts).insert(
        AccountsCompanion.insert(
          uuid: account.uuid.value,
          name: account.name,
          currencyCode: account.currencyCode.value,
          currencyPrecision: account.precision.value,
          isDefault: Value(isDefault),
          createdAtMs: now.value,
          updatedAtMs: now.value,
          deletedAtMs: const Value(null),
          revision: const Value(1),
          originDeviceId: deviceId.value,
          lastModifiedBy: deviceId.value,
          syncState: Value(account.syncState.dbValue),
        ),
      );
      await _appendAccountChange(
        entity: account,
        operation: 'insert',
        baseRevision: null,
        deviceId: deviceId,
        recordedAt: now,
      );
      return uuid;
    });
  }

  Future<int> insertTransaction({
    required TransactionType type,
    required int amountMinor,
    required Uuid accountUuid,
    required String category,
    required String transactionDate,
    String? description,
    String? importHash,
    String? externalRef,
    String? importBatchId,
    String? accountLabel,
  }) async {
    final accountRow = await _accountRow(accountUuid, liveOnly: true);
    if (accountRow == null) {
      throw const DomainValidationException('Account not found.');
    }
    final account = mapAccount(accountRow);
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();
    final uuid = Uuid.generate();

    return _db.transaction(() async {
      final id = await _db.into(_db.transactions).insert(
        TransactionsCompanion.insert(
          transactionType: type.dbValue,
          amountMinor: amountMinor,
          category: category,
          description: Value(description),
          transactionDate: transactionDate,
          uuid: uuid.value,
          createdAtMs: now.value,
          updatedAtMs: now.value,
          deletedAtMs: const Value(null),
          revision: const Value(1),
          originDeviceId: deviceId.value,
          lastModifiedBy: deviceId.value,
          syncState: Value(SyncState.pending.dbValue),
          accountUuid: accountUuid.value,
          importHash: Value(importHash),
          externalRef: Value(externalRef),
          importBatchId: Value(importBatchId),
          accountLabel: Value(accountLabel),
        ),
      );

      final row = await _transactionRow(id);
      if (row == null) {
        throw const DomainValidationException('Transaction insert failed.');
      }
      final transaction = mapTransaction(row);
      await _db.appendChange(
        entityType: 'transaction',
        entityUuid: transaction.uuid.value,
        operation: 'insert',
        baseRevision: null,
        newRevision: transaction.revision,
        payload: transactionPayload(transaction, currencyCode: account.currencyCode),
        originDeviceId: deviceId.value,
        recordedAtMs: now.value,
      );
      return id;
    });
  }

  Future<void> renameAccount(Uuid uuid, String name) async {
    final cleanName = InputValidators.requiredText(name, 'Account name');
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();

    await _db.transaction(() async {
      final row = await _accountRow(uuid, liveOnly: true);
      if (row == null) {
        throw const DomainValidationException('Account not found.');
      }
      final current = mapAccount(row);
      final updated = current.copyWith(
        name: cleanName,
        updatedAt: now,
        revision: current.revision + 1,
        lastModifiedBy: deviceId,
        syncState: SyncState.pending,
      );

      await (_db.update(_db.accounts)..where((item) => item.id.equals(row.id)))
        .write(
          AccountsCompanion(
            name: Value(cleanName),
            updatedAtMs: Value(now.value),
            revision: Value(updated.revision),
            lastModifiedBy: Value(deviceId.value),
            syncState: Value(updated.syncState.dbValue),
          ),
        );
      await _appendAccountChange(
        entity: updated,
        operation: 'update',
        baseRevision: current.revision,
        deviceId: deviceId,
        recordedAt: now,
      );
    });
  }

  Future<void> softDeleteTransaction(int id) async {
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();

    await _db.transaction(() async {
      final row = await _transactionRow(id);
      if (row == null || row.deletedAtMs != null) {
        throw const DomainValidationException('Live transaction not found.');
      }
      final current = mapTransaction(row);
      final account = await accountByUuid(current.accountUuid);
      if (account == null) {
        throw const DomainValidationException('Account not found.');
      }
      final updated = current.copyWith(
        updatedAt: now,
        deletedAt: now,
        revision: current.revision + 1,
        lastModifiedBy: deviceId,
        syncState: SyncState.pending,
      );

      await (_db.update(_db.transactions)
            ..where((item) => item.id.equals(id)))
        .write(
          TransactionsCompanion(
            updatedAtMs: Value(now.value),
            deletedAtMs: Value(now.value),
            revision: Value(updated.revision),
            lastModifiedBy: Value(deviceId.value),
            syncState: Value(updated.syncState.dbValue),
          ),
        );
      await _db.appendChange(
        entityType: 'transaction',
        entityUuid: updated.uuid.value,
        operation: 'delete',
        baseRevision: current.revision,
        newRevision: updated.revision,
        payload: transactionPayload(
          updated,
          currencyCode: account.currencyCode,
        ),
        originDeviceId: deviceId.value,
        recordedAtMs: now.value,
      );
    });
  }

  Future<Uuid> _deviceUuid() async {
    final row = await (select(_db.appMeta)
          ..where((item) => item.key.equals(LedgerConstants.appMetaDeviceIdKey)))
        .getSingleOrNull();
    if (row == null) {
      throw const DomainValidationException('Android device identity is missing.');
    }
    return Uuid.parse(row.value);
  }

  Future<db.Account?> _defaultAccountRow() async {
    return (select(_db.accounts)
          ..where((row) => row.isDefault.equals(true) & row.deletedAtMs.isNull())
          ..limit(1))
        .getSingleOrNull();
  }

  Future<db.Account?> _accountRow(Uuid uuid, {required bool liveOnly}) async {
    return (select(_db.accounts)
          ..where(
            (row) => row.uuid.equals(uuid.value) &
                (liveOnly ? row.deletedAtMs.isNull() : const Constant(true)),
          )
          ..limit(1))
        .getSingleOrNull();
  }

  Future<db.Transaction?> _transactionRow(int id) async {
    return (select(_db.transactions)..where((row) => row.id.equals(id)))
        .getSingleOrNull();
  }

  Future<void> _appendAccountChange({
    required Account entity,
    required String operation,
    required int? baseRevision,
    required Uuid deviceId,
    required UtcMs recordedAt,
  }) {
    return _db.appendChange(
      entityType: 'account',
      entityUuid: entity.uuid.value,
      operation: operation,
      baseRevision: baseRevision,
      newRevision: entity.revision,
      payload: accountPayload(entity),
      originDeviceId: deviceId.value,
      recordedAtMs: recordedAt.value,
    );
  }
}
