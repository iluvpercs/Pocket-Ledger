import 'dart:async';
import 'dart:convert';

import 'package:drift/drift.dart';

import 'package:pocket_ledger_mobile/data/database/database.dart' as db;
import 'package:pocket_ledger_mobile/data/mappers/row_mappers.dart';
import 'package:pocket_ledger_mobile/data/mappers/sync_payload.dart';
import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/category.dart';
import 'package:pocket_ledger_mobile/domain/entities/csv_import.dart';
import 'package:pocket_ledger_mobile/domain/entities/dashboard_summary.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_constants.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/entities/sync_state.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction_filter.dart';
import 'package:pocket_ledger_mobile/domain/validation_exception.dart';
import 'package:pocket_ledger_mobile/domain/validators/input_validators.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

/// Local persistence plus the append-only outbox. There is no sync transport.
class LedgerDao {
  LedgerDao(this._db);

  final db.AppDatabase _db;

  Future<void> ensureBootstrapped() => _db.ensureSeeded();

  Future<Uuid> deviceId() => _deviceUuid();

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

  Stream<List<Account>> watchAccounts() {
    return (_db.select(_db.accounts)
          ..where((row) => row.deletedAtMs.isNull())
          ..orderBy([(row) => OrderingTerm.asc(row.name)]))
        .watch()
        .map((rows) => rows.map(mapAccount).toList());
  }

  Stream<List<LedgerTransaction>> watchLiveTransactions() {
    return (_db.select(_db.transactions)
          ..where((row) => row.deletedAtMs.isNull())
          ..orderBy([
            (row) => OrderingTerm.desc(row.transactionDate),
            (row) => OrderingTerm.desc(row.id),
          ]))
        .watch()
        .map((rows) => rows.map(mapTransaction).toList());
  }

  /// SQLite computes the signed per-account delta so neither the accounts
  /// screen nor the dashboard has to walk every transaction in Dart.
  Stream<Map<String, int>> watchAccountDeltas() {
    return _accountDeltaStream().map((rows) => {
      for (final row in rows)
        row.read<String>('account_uuid'): row.read<int>('delta_minor'),
    });
  }

  /// Grouped dashboard values. Recent rows stay as a normal Drift query; all
  /// totals, categories and six-month points are counted by SQLite.
  Stream<DashboardAggregateData> watchDashboardAggregate({
    required DateTime month,
    required String chartCurrencyCode,
  }) {
    final monthStart = DateTime.utc(month.year, month.month);
    final monthEnd = DateTime.utc(month.year, month.month + 1);

    return _combine5(
      watchAccountDeltas(),
      _watchMonthTotals(monthStart, monthEnd),
      _watchCategoryTotals(monthStart, monthEnd),
      _watchSixMonthSeries(chartCurrencyCode),
      watchTransactions(const TransactionFilter(), limit: 5),
      (deltas, monthTotals, categoryTotals, series, recent) {
        return DashboardAggregateData(
          accountDeltas: deltas,
          monthTotals: monthTotals,
          categoryTotals: categoryTotals,
          sixMonthSeries: series,
          recentTransactions: recent,
        );
      },
    );
  }

  Stream<List<QueryRow>> _accountDeltaStream() {
    return _db.customSelect(
      '''
      SELECT t.account_uuid AS account_uuid,
             COALESCE(SUM(
               CASE WHEN t.transaction_type = 'income'
                    THEN t.amount_minor ELSE -t.amount_minor END
             ), 0) AS delta_minor
      FROM transactions t
      JOIN accounts a ON a.uuid = t.account_uuid
      WHERE t.deleted_at_ms IS NULL AND a.deleted_at_ms IS NULL
      GROUP BY t.account_uuid
      ''',
      readsFrom: {_db.transactions, _db.accounts},
    ).watch();
  }

  Stream<List<CurrencyTotals>> _watchMonthTotals(
    DateTime start,
    DateTime end,
  ) {
    return _db
        .customSelect(
          '''
          SELECT a.currency_code AS currency_code,
                 COALESCE(SUM(CASE WHEN t.transaction_type = 'income'
                                   THEN t.amount_minor ELSE 0 END), 0)
                     AS income_minor,
                 COALESCE(SUM(CASE WHEN t.transaction_type = 'expense'
                                   THEN t.amount_minor ELSE 0 END), 0)
                     AS expense_minor
          FROM transactions t
          JOIN accounts a ON a.uuid = t.account_uuid
          WHERE t.deleted_at_ms IS NULL
            AND a.deleted_at_ms IS NULL
            AND t.transaction_date >= ?
            AND t.transaction_date < ?
          GROUP BY a.currency_code
          ''',
          variables: [
            Variable.withString(_dateText(start)),
            Variable.withString(_dateText(end)),
          ],
          readsFrom: {_db.transactions, _db.accounts},
        )
        .watch()
        .map((rows) {
          return [
            for (final row in rows)
              CurrencyTotals(
                currencyCode: row.read<String>('currency_code'),
                balanceMinor: 0,
                incomeMinor: row.read<int>('income_minor'),
                expenseMinor: row.read<int>('expense_minor'),
              ),
          ];
        });
  }

  Stream<List<CategoryTotal>> _watchCategoryTotals(
    DateTime start,
    DateTime end,
  ) {
    return _db
        .customSelect(
          '''
          SELECT a.currency_code AS currency_code,
                 t.category AS category,
                 COALESCE(SUM(t.amount_minor), 0) AS amount_minor
          FROM transactions t
          JOIN accounts a ON a.uuid = t.account_uuid
          WHERE t.deleted_at_ms IS NULL
            AND a.deleted_at_ms IS NULL
            AND t.transaction_type = 'expense'
            AND t.transaction_date >= ?
            AND t.transaction_date < ?
          GROUP BY a.currency_code, t.category
          ''',
          variables: [
            Variable.withString(_dateText(start)),
            Variable.withString(_dateText(end)),
          ],
          readsFrom: {_db.transactions, _db.accounts},
        )
        .watch()
        .map((rows) {
          return [
            for (final row in rows)
              CategoryTotal(
                category: row.read<String>('category'),
                currencyCode: row.read<String>('currency_code'),
                amountMinor: row.read<int>('amount_minor'),
              ),
          ];
        });
  }

  Stream<List<MonthSeriesPoint>> _watchSixMonthSeries(String currencyCode) {
    final now = DateTime.now().toUtc();
    final start = DateTime.utc(now.year, now.month - 5);
    final end = DateTime.utc(now.year, now.month + 1);

    return _db
        .customSelect(
          '''
          SELECT CAST(substr(t.transaction_date, 1, 4) AS INTEGER) AS year,
                 CAST(substr(t.transaction_date, 6, 2) AS INTEGER) AS month,
                 COALESCE(SUM(CASE WHEN t.transaction_type = 'income'
                                   THEN t.amount_minor ELSE 0 END), 0)
                     AS income_minor,
                 COALESCE(SUM(CASE WHEN t.transaction_type = 'expense'
                                   THEN t.amount_minor ELSE 0 END), 0)
                     AS expense_minor
          FROM transactions t
          JOIN accounts a ON a.uuid = t.account_uuid
          WHERE t.deleted_at_ms IS NULL
            AND a.deleted_at_ms IS NULL
            AND a.currency_code = ?
            AND t.transaction_date >= ?
            AND t.transaction_date < ?
          GROUP BY substr(t.transaction_date, 1, 7)
          ORDER BY substr(t.transaction_date, 1, 7)
          ''',
          variables: [
            Variable.withString(currencyCode),
            Variable.withString(_dateText(start)),
            Variable.withString(_dateText(end)),
          ],
          readsFrom: {_db.transactions, _db.accounts},
        )
        .watch()
        .map((rows) {
          return [
            for (final row in rows)
              MonthSeriesPoint(
                year: row.read<int>('year'),
                month: row.read<int>('month'),
                currencyCode: currencyCode,
                incomeMinor: row.read<int>('income_minor'),
                expenseMinor: row.read<int>('expense_minor'),
              ),
          ];
        });
  }

  Stream<List<LedgerTransaction>> watchTransactions(
    TransactionFilter filter, {
    required int limit,
  }) {
    Expression<bool> clause = _db.transactions.deletedAtMs.isNull();
    final term = filter.search.trim().toLowerCase();
    if (term.isNotEmpty) {
      clause = clause &
          (_db.transactions.category.like('%$term%') |
              _db.transactions.description.like('%$term%'));
    }
    if (filter.accountUuid != null) {
      clause = clause &
          _db.transactions.accountUuid.equals(filter.accountUuid!.value);
    }
    if (filter.type != TransactionTypeFilter.all) {
      clause = clause &
          _db.transactions.transactionType.equals(filter.type.id);
    }
    if (filter.category != null) {
      clause = clause & _db.transactions.category.equals(filter.category!);
    }
    if (filter.fromDate != null) {
      clause = clause & _db.transactions.transactionDate.isBiggerOrEqualValue(
            _dateText(filter.fromDate!),
          );
    }
    if (filter.toDate != null) {
      clause = clause & _db.transactions.transactionDate.isSmallerOrEqualValue(
            _dateText(filter.toDate!),
          );
    }

    return (_db.select(_db.transactions)
          ..where((row) => clause)
          ..orderBy([
            (row) => OrderingTerm.desc(row.transactionDate),
            (row) => OrderingTerm.desc(row.id),
          ])
          ..limit(limit))
        .watch()
        .map((rows) => rows.map(mapTransaction).toList());
  }

  Future<LedgerTransaction?> transactionById(int id) async {
    final row = await _transactionRow(id);
    return row == null ? null : mapTransaction(row);
  }

  Future<Uuid> insertAccount({
    required String name,
    required CurrencyCode currencyCode,
    required int openingMinor,
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
            db.AccountsCompanion(
              isDefault: const Value(false),
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
        db.AccountsCompanion.insert(
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
      await _writeMetaInside(
        key: MobileMetaKeys.openingBalance(uuid),
        value: openingMinor.toString(),
        deviceId: deviceId,
        now: now,
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
    int? transactionTimeMs,
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
      final id = await _insertTransactionRow(
        type: type,
        amountMinor: amountMinor,
        accountUuid: accountUuid,
        category: category,
        transactionDate: transactionDate,
        description: description,
        importHash: importHash,
        externalRef: externalRef,
        importBatchId: importBatchId,
        accountLabel: accountLabel,
        deviceId: deviceId,
        now: now,
        uuid: uuid,
      );
      await _appendTransactionChangeInside(
        id: id,
        account: account,
        operation: 'insert',
        baseRevision: null,
        deviceId: deviceId,
        now: now,
      );
      if (transactionTimeMs != null) {
        await _writeMetaInside(
          key: MobileMetaKeys.transactionTime(uuid),
          value: transactionTimeMs.toString(),
          deviceId: deviceId,
          now: now,
        );
      }
      return id;
    });
  }

  Future<void> updateTransaction({
    required int id,
    required TransactionType type,
    required int amountMinor,
    required Uuid accountUuid,
    required String category,
    required String transactionDate,
    required String? description,
    int? transactionTimeMs,
  }) async {
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();

    await _db.transaction(() async {
      final row = await _transactionRow(id);
      if (row == null || row.deletedAtMs != null) {
        throw const DomainValidationException('Live transaction not found.');
      }
      final accountRow = await _accountRow(accountUuid, liveOnly: true);
      if (accountRow == null) {
        throw const DomainValidationException('Account not found.');
      }
      final account = mapAccount(accountRow);
      final current = mapTransaction(row);
      final updated = current.copyWith(
        type: type,
        amount: MinorAmount.fromMinor(amountMinor),
        accountUuid: accountUuid,
        category: category,
        description: description,
        transactionDate: transactionDate,
        updatedAt: now,
        revision: current.revision + 1,
        lastModifiedBy: deviceId,
        syncState: SyncState.pending,
      );

      await (_db.update(_db.transactions)..where((item) => item.id.equals(id)))
        .write(
        db.TransactionsCompanion(
          transactionType: Value(type.dbValue),
          amountMinor: Value(amountMinor),
          accountUuid: Value(accountUuid.value),
          category: Value(category),
          description: Value(description),
          transactionDate: Value(transactionDate),
          updatedAtMs: Value(now.value),
          revision: Value(updated.revision),
          lastModifiedBy: Value(deviceId.value),
          syncState: Value(updated.syncState.dbValue),
        ),
      );
      await _db.appendChange(
        entityType: 'transaction',
        entityUuid: current.uuid.value,
        operation: 'update',
        baseRevision: current.revision,
        newRevision: updated.revision,
        payload: transactionPayload(updated, currencyCode: account.currencyCode),
        originDeviceId: deviceId.value,
        recordedAtMs: now.value,
      );
      if (transactionTimeMs != null) {
        await _writeMetaInside(
          key: MobileMetaKeys.transactionTime(current.uuid),
          value: transactionTimeMs.toString(),
          deviceId: deviceId,
          now: now,
        );
      }
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
        db.AccountsCompanion(
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

  Future<void> setDefaultAccount(Uuid uuid) async {
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();

    await _db.transaction(() async {
      final targetRow = await _accountRow(uuid, liveOnly: true);
      if (targetRow == null) {
        throw const DomainValidationException('Account not found.');
      }
      final target = mapAccount(targetRow);
      if (target.isDefault) return;

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
              ..where((item) => item.id.equals(previousRow.id)))
          .write(
          db.AccountsCompanion(
            isDefault: const Value(false),
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

      final promoted = target.copyWith(
        isDefault: true,
        updatedAt: now,
        revision: target.revision + 1,
        lastModifiedBy: deviceId,
        syncState: SyncState.pending,
      );
      await (_db.update(_db.accounts)
            ..where((item) => item.id.equals(targetRow.id)))
        .write(
        db.AccountsCompanion(
          isDefault: const Value(true),
          updatedAtMs: Value(now.value),
          revision: Value(promoted.revision),
          lastModifiedBy: Value(deviceId.value),
          syncState: Value(promoted.syncState.dbValue),
        ),
      );
      await _appendAccountChange(
        entity: promoted,
        operation: 'update',
        baseRevision: target.revision,
        deviceId: deviceId,
        recordedAt: now,
      );
      await _writeMetaInside(
        key: MobileMetaKeys.defaultAccountUuid,
        value: target.uuid.value,
        deviceId: deviceId,
        now: now,
      );
    });
  }

  Future<void> softDeleteAccount(
    Uuid uuid, {
    required bool cascade,
  }) async {
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();

    await _db.transaction(() async {
      final row = await _accountRow(uuid, liveOnly: true);
      if (row == null) {
        throw const DomainValidationException('Account not found.');
      }
      final current = mapAccount(row);
      final transactionRows = await (_db.select(_db.transactions)
            ..where(
              (item) =>
                  item.accountUuid.equals(uuid.value) & item.deletedAtMs.isNull(),
            ))
          .get();
      if (transactionRows.isNotEmpty && !cascade) {
        throw const DomainValidationException(
          'This account has transactions. Confirm cascade delete to archive '
          'them as well.',
        );
      }
      for (final transactionRow in transactionRows) {
        await _softDeleteTransactionInside(
          transactionRow.id,
          account: current,
          deviceId: deviceId,
          now: now,
        );
      }

      final deleted = current.copyWith(
        updatedAt: now,
        deletedAt: now,
        revision: current.revision + 1,
        lastModifiedBy: deviceId,
        syncState: SyncState.pending,
      );
      await (_db.update(_db.accounts)..where((item) => item.id.equals(row.id)))
        .write(
        db.AccountsCompanion(
          updatedAtMs: Value(now.value),
          deletedAtMs: Value(now.value),
          revision: Value(deleted.revision),
          lastModifiedBy: Value(deviceId.value),
          syncState: Value(deleted.syncState.dbValue),
          isDefault: const Value(false),
        ),
      );
      await _appendAccountChange(
        entity: deleted,
        operation: 'delete',
        baseRevision: current.revision,
        deviceId: deviceId,
        recordedAt: now,
      );

      if (current.isDefault) {
        final replacement = await (_db.select(_db.accounts)
              ..where(
                (item) =>
                    item.deletedAtMs.isNull() & item.uuid.equals(uuid.value).not(),
              )
              ..limit(1))
            .getSingleOrNull();
        if (replacement != null) {
          final account = mapAccount(replacement);
          final promoted = account.copyWith(
            isDefault: true,
            updatedAt: now,
            revision: account.revision + 1,
            lastModifiedBy: deviceId,
            syncState: SyncState.pending,
          );
          await (_db.update(_db.accounts)
                ..where((item) => item.id.equals(replacement.id)))
            .write(
            db.AccountsCompanion(
              isDefault: const Value(true),
              updatedAtMs: Value(now.value),
              revision: Value(promoted.revision),
              lastModifiedBy: Value(deviceId.value),
              syncState: Value(promoted.syncState.dbValue),
            ),
          );
          await _appendAccountChange(
            entity: promoted,
            operation: 'update',
            baseRevision: account.revision,
            deviceId: deviceId,
            recordedAt: now,
          );
        }
      }
    });
  }

  Future<void> softDeleteTransaction(int id) async {
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();

    await _db.transaction(() async {
      await _softDeleteTransactionInside(
        id,
        deviceId: deviceId,
        now: now,
      );
    });
  }

  Future<void> restoreTransaction(int id) async {
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();
    await _db.transaction(() async {
      await _restoreTransactionInside(id, deviceId: deviceId, now: now);
    });
  }

  Future<void> softDeleteTransactions(List<int> ids) async {
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();
    await _db.transaction(() async {
      for (final id in ids) {
        await _softDeleteTransactionInside(
          id,
          deviceId: deviceId,
          now: now,
        );
      }
    });
  }

  Future<void> restoreTransactions(List<int> ids) async {
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();
    await _db.transaction(() async {
      for (final id in ids) {
        await _restoreTransactionInside(id, deviceId: deviceId, now: now);
      }
    });
  }

  Future<Map<String, Set<String>>> importHashes() async {
    final rows = await (_db.select(_db.transactions)
          ..where(
            (row) => row.importHash.isNotNull() & row.deletedAtMs.isNull(),
          ))
        .get();
    final result = <String, Set<String>>{};
    for (final row in rows) {
      final hash = row.importHash;
      if (hash == null) continue;
      result.putIfAbsent(hash, () => <String>{}).add(row.accountUuid);
    }
    return result;
  }

  Future<void> importRows(
    List<ParsedCsvRow> rows, {
    required String sourceFile,
  }) async {
    final importable = rows.where((row) => row.canImport).toList();
    if (importable.isEmpty) return;
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();
    final batchId = Uuid.generate().value;

    await _db.transaction(() async {
      await _db.into(_db.importBatches).insert(
        db.ImportBatchesCompanion.insert(
          batchId: batchId,
          sourceFile: Value(sourceFile),
          sourceType: const Value('csv'),
          importedAtMs: now.value,
          importedCount: Value(importable.length),
          skippedCount: Value(
            rows.length - importable.length,
          ),
          deviceId: Value(deviceId.value),
        ),
      );
      await _db.appendChange(
        entityType: 'import_batch',
        entityUuid: batchId,
        operation: 'insert',
        baseRevision: null,
        newRevision: 1,
        payload: {
          'batch_id': batchId,
          'source_file': sourceFile,
          'source_type': 'csv',
          'imported_at_ms': now.value,
          'imported_count': importable.length,
          'skipped_count': rows.length - importable.length,
        },
        originDeviceId: deviceId.value,
        recordedAtMs: now.value,
      );

      for (final row in importable) {
        final accountRow = await _accountRow(row.accountUuid!, liveOnly: true);
        if (accountRow == null) {
          throw const DomainValidationException('Account not found.');
        }
        final account = mapAccount(accountRow);
        final uuid = Uuid.generate();
        final insertedId = await _insertTransactionRow(
          type: row.type!,
          amountMinor: row.amountMinor!,
          accountUuid: row.accountUuid!,
          category: row.category!,
          transactionDate: row.dateIso!,
          description: row.description,
          importHash: row.importHash,
          externalRef: row.reference,
          importBatchId: batchId,
          accountLabel: row.accountLabel,
          deviceId: deviceId,
          now: now,
          uuid: uuid,
        );
        await _appendTransactionChangeInside(
          id: insertedId,
          account: account,
          operation: 'insert',
          baseRevision: null,
          deviceId: deviceId,
          now: now,
        );
      }
    });
  }

  Future<void> deleteAllData() async {
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();
    await _db.transaction(() async {
      final transactions = await (_db.select(_db.transactions)
            ..where((row) => row.deletedAtMs.isNull()))
          .get();
      for (final row in transactions) {
        await _softDeleteTransactionInside(
          row.id,
          deviceId: deviceId,
          now: now,
        );
      }
      final accounts = await (_db.select(_db.accounts)
            ..where((row) => row.deletedAtMs.isNull()))
          .get();
      for (final row in accounts) {
        final account = mapAccount(row);
        final deleted = account.copyWith(
          updatedAt: now,
          deletedAt: now,
          revision: account.revision + 1,
          lastModifiedBy: deviceId,
          syncState: SyncState.pending,
        );
        await (_db.update(_db.accounts)..where((item) => item.id.equals(row.id)))
          .write(
          db.AccountsCompanion(
            updatedAtMs: Value(now.value),
            deletedAtMs: Value(now.value),
            revision: Value(deleted.revision),
            lastModifiedBy: Value(deviceId.value),
            syncState: Value(deleted.syncState.dbValue),
            isDefault: const Value(false),
          ),
        );
        await _appendAccountChange(
          entity: deleted,
          operation: 'delete',
          baseRevision: account.revision,
          deviceId: deviceId,
          recordedAt: now,
        );
      }

      await _writeMetaInside(
        key: MobileMetaKeys.defaultCurrency,
        value: LedgerConstants.defaultCurrencyCode,
        deviceId: deviceId,
        now: now,
      );
      await _writeMetaInside(
        key: MobileMetaKeys.defaultAccountUuid,
        value: '',
        deviceId: deviceId,
        now: now,
      );
      await _writeMetaInside(
        key: MobileMetaKeys.dateFormat,
        value: LedgerDateFormat.iso.id,
        deviceId: deviceId,
        now: now,
      );
      await _writeMetaInside(
        key: MobileMetaKeys.themeMode,
        value: LedgerThemeMode.dark.id,
        deviceId: deviceId,
        now: now,
      );
      await _writeMetaInside(
        key: MobileMetaKeys.categories,
        value: '[]',
        deviceId: deviceId,
        now: now,
      );
    });
  }

  Future<String?> metaValue(String key) async =>
      (await _metaRow(key))?.value;

  Stream<String?> watchMetaValue(String key) {
    return (_db.select(_db.appMeta)..where((row) => row.key.equals(key)))
        .watch()
        .map((rows) => rows.isEmpty ? null : rows.first.value);
  }

  Future<LedgerSettings> settings() async =>
      _settingsFrom(await _db.select(_db.appMeta).get());

  Stream<LedgerSettings> watchSettings() =>
      _allMetaStream().map(_settingsFrom);

  Future<void> writeSettings(LedgerSettings settings) async {
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();
    await _db.transaction(() async {
      await _writeMetaInside(
        key: MobileMetaKeys.defaultCurrency,
        value: settings.defaultCurrencyCode.value,
        deviceId: deviceId,
        now: now,
      );
      await _writeMetaInside(
        key: MobileMetaKeys.defaultAccountUuid,
        value: settings.defaultAccountUuid?.value ?? '',
        deviceId: deviceId,
        now: now,
      );
      await _writeMetaInside(
        key: MobileMetaKeys.dateFormat,
        value: settings.dateFormat.id,
        deviceId: deviceId,
        now: now,
      );
      await _writeMetaInside(
        key: MobileMetaKeys.themeMode,
        value: settings.themeMode.id,
        deviceId: deviceId,
        now: now,
      );
    });
  }

  Future<List<LedgerCategory>> categories() async =>
      _categoriesFrom(await metaValue(MobileMetaKeys.categories));

  Stream<List<LedgerCategory>> watchCategories() =>
      watchMetaValue(MobileMetaKeys.categories).map(_categoriesFrom);

  Future<void> saveCategories(List<LedgerCategory> categories) async {
    final custom = categories.where((category) => !category.isDefault).toList();
    final encoded = jsonEncode([
      for (final category in custom) {'id': category.id, 'name': category.name},
    ]);
    await _writeMeta(
      key: MobileMetaKeys.categories,
      value: encoded,
    );
  }

  Future<Map<String, int>> openingBalances() async =>
      _prefixedInts(MobileMetaKeys.openingBalancePrefix);

  Stream<Map<String, int>> watchOpeningBalances() =>
      _watchPrefixedInts(MobileMetaKeys.openingBalancePrefix);

  Future<Map<String, int>> transactionTimes() async =>
      _prefixedInts(MobileMetaKeys.transactionTimePrefix);

  Stream<Map<String, int>> transactionTimesStream() =>
      _watchPrefixedInts(MobileMetaKeys.transactionTimePrefix);

  Future<int> _insertTransactionRow({
    required TransactionType type,
    required int amountMinor,
    required Uuid accountUuid,
    required String category,
    required String transactionDate,
    required String? description,
    required String? importHash,
    required String? externalRef,
    required String? importBatchId,
    required String? accountLabel,
    required Uuid deviceId,
    required UtcMs now,
    required Uuid uuid,
  }) {
    return _db.into(_db.transactions).insert(
      db.TransactionsCompanion.insert(
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
  }

  Future<void> _appendTransactionChangeInside({
    required int id,
    required Account account,
    required String operation,
    required int? baseRevision,
    required Uuid deviceId,
    required UtcMs now,
  }) async {
    final row = await _transactionRow(id);
    if (row == null) {
      throw const DomainValidationException('Transaction insert failed.');
    }
    final transaction = mapTransaction(row);
    await _db.appendChange(
      entityType: 'transaction',
      entityUuid: transaction.uuid.value,
      operation: operation,
      baseRevision: baseRevision,
      newRevision: transaction.revision,
      payload: transactionPayload(transaction, currencyCode: account.currencyCode),
      originDeviceId: deviceId.value,
      recordedAtMs: now.value,
    );
  }

  Future<void> _softDeleteTransactionInside(
    int id, {
    Account? account,
    required Uuid deviceId,
    required UtcMs now,
  }) async {
    final row = await _transactionRow(id);
    if (row == null || row.deletedAtMs != null) {
      throw const DomainValidationException('Live transaction not found.');
    }
    final current = mapTransaction(row);
    final resolvedAccount = account ?? await accountByUuid(current.accountUuid);
    if (resolvedAccount == null) {
      throw const DomainValidationException('Account not found.');
    }
    final updated = current.copyWith(
      updatedAt: now,
      deletedAt: now,
      revision: current.revision + 1,
      lastModifiedBy: deviceId,
      syncState: SyncState.pending,
    );

    await (_db.update(_db.transactions)..where((item) => item.id.equals(id)))
      .write(
      db.TransactionsCompanion(
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
      payload: transactionPayload(updated, currencyCode: resolvedAccount.currencyCode),
      originDeviceId: deviceId.value,
      recordedAtMs: now.value,
    );
  }

  Future<void> _restoreTransactionInside(
    int id, {
    required Uuid deviceId,
    required UtcMs now,
  }) async {
    final row = await _transactionRow(id);
    if (row == null || row.deletedAtMs == null) {
      throw const DomainValidationException('Deleted transaction not found.');
    }
    final current = mapTransaction(row);
    final account = await accountByUuid(current.accountUuid);
    if (account == null) {
      throw const DomainValidationException('Account not found.');
    }
    final restored = current.copyWith(
      updatedAt: now,
      deletedAt: null,
      revision: current.revision + 1,
      lastModifiedBy: deviceId,
      syncState: SyncState.pending,
    );

    await (_db.update(_db.transactions)..where((item) => item.id.equals(id)))
      .write(
      db.TransactionsCompanion(
        updatedAtMs: Value(now.value),
        deletedAtMs: const Value(null),
        revision: Value(restored.revision),
        lastModifiedBy: Value(deviceId.value),
        syncState: Value(restored.syncState.dbValue),
      ),
    );
    await _db.appendChange(
      entityType: 'transaction',
      entityUuid: restored.uuid.value,
      operation: 'update',
      baseRevision: current.revision,
      newRevision: restored.revision,
      payload: transactionPayload(restored, currencyCode: account.currencyCode),
      originDeviceId: deviceId.value,
      recordedAtMs: now.value,
    );
  }

  Future<void> _writeMeta({
    required String key,
    required String value,
  }) async {
    final deviceId = await _deviceUuid();
    final now = UtcMs.now();
    await _db.transaction(() async {
      await _writeMetaInside(
        key: key,
        value: value,
        deviceId: deviceId,
        now: now,
      );
    });
  }

  Future<void> _writeMetaInside({
    required String key,
    required String value,
    required Uuid deviceId,
    required UtcMs now,
  }) async {
    await _db.into(_db.appMeta).insert(
      db.AppMetaCompanion.insert(key: key, value: value),
      mode: InsertMode.insertOrReplace,
    );
    await _db.appendChange(
      entityType: 'app_meta',
      entityUuid: key,
      operation: 'update',
      baseRevision: 0,
      newRevision: 1,
      payload: {'key': key, 'value': value},
      originDeviceId: deviceId.value,
      recordedAtMs: now.value,
    );
  }

  Future<db.AppMetaData?> _metaRow(String key) async {
    return (_db.select(_db.appMeta)..where((row) => row.key.equals(key)))
        .getSingleOrNull();
  }

  Stream<List<db.AppMetaData>> _allMetaStream() =>
      _db.select(_db.appMeta).watch();

  LedgerSettings _settingsFrom(List<db.AppMetaData> rows) {
    final values = {for (final row in rows) row.key: row.value};
    Uuid? accountUuid;
    final rawUuid = values[MobileMetaKeys.defaultAccountUuid];
    if (rawUuid != null && rawUuid.isNotEmpty) {
      try {
        accountUuid = Uuid.parse(rawUuid);
      } on DomainValidationException {
        accountUuid = null;
      }
    }
    CurrencyCode currency;
    try {
      currency = CurrencyCode.parse(
        values[MobileMetaKeys.defaultCurrency] ??
            LedgerConstants.defaultCurrencyCode,
      );
    } on DomainValidationException {
      currency = CurrencyCode.parse(LedgerConstants.defaultCurrencyCode);
    }
    return LedgerSettings(
      defaultCurrencyCode: currency,
      defaultAccountUuid: accountUuid,
      dateFormat: LedgerDateFormat.fromId(values[MobileMetaKeys.dateFormat]),
      themeMode: LedgerThemeMode.fromId(values[MobileMetaKeys.themeMode]),
    );
  }

  List<LedgerCategory> _categoriesFrom(String? encoded) {
    final custom = <LedgerCategory>[];
    if (encoded != null && encoded.isNotEmpty) {
      try {
        final decoded = jsonDecode(encoded) as List<dynamic>;
        for (final item in decoded) {
          if (item is! Map<String, dynamic>) continue;
          final name = item['name']?.toString().trim() ?? '';
          if (name.isEmpty) continue;
          custom.add(
            LedgerCategory(
              id: item['id']?.toString() ?? name.toLowerCase(),
              name: name,
              isDefault: false,
            ),
          );
        }
      } on FormatException {
        // Ignore corrupt local preferences rather than blocking the app.
      }
    }
    return [
      for (final name in LedgerDefaults.categories)
        LedgerCategory(
          id: 'default-${name.toLowerCase()}',
          name: name,
          isDefault: true,
        ),
      ...custom,
    ];
  }

  Future<Map<String, int>> _prefixedInts(String prefix) async {
    final result = <String, int>{};
    for (final row in await _db.select(_db.appMeta).get()) {
      if (!row.key.startsWith(prefix)) continue;
      final value = int.tryParse(row.value);
      if (value != null) result[row.key.substring(prefix.length)] = value;
    }
    return result;
  }

  Stream<Map<String, int>> _watchPrefixedInts(String prefix) {
    return _allMetaStream().map((rows) {
      final result = <String, int>{};
      for (final row in rows) {
        if (!row.key.startsWith(prefix)) continue;
        final value = int.tryParse(row.value);
        if (value != null) result[row.key.substring(prefix.length)] = value;
      }
      return result;
    });
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

  Future<Uuid> _deviceUuid() async {
    final row = await (_db.select(_db.appMeta)
          ..where((item) => item.key.equals(LedgerConstants.appMetaDeviceIdKey)))
        .getSingleOrNull();
    if (row == null) {
      throw const DomainValidationException('Android device identity is missing.');
    }
    return Uuid.parse(row.value);
  }

  Future<db.AccountRow?> _defaultAccountRow() async {
    return (_db.select(_db.accounts)
          ..where((row) => row.isDefault.equals(true) & row.deletedAtMs.isNull())
          ..limit(1))
        .getSingleOrNull();
  }

  Future<db.AccountRow?> _accountRow(Uuid uuid, {required bool liveOnly}) async {
    return (_db.select(_db.accounts)
          ..where(
            (row) => row.uuid.equals(uuid.value) &
                (liveOnly ? row.deletedAtMs.isNull() : const Constant(true)),
          )
          ..limit(1))
        .getSingleOrNull();
  }

  Future<db.Transaction?> _transactionRow(int id) async {
    return (_db.select(_db.transactions)..where((row) => row.id.equals(id)))
        .getSingleOrNull();
  }

  String _dateText(DateTime value) =>
      '${value.year.toString().padLeft(4, '0')}-'
      '${value.month.toString().padLeft(2, '0')}-'
      '${value.day.toString().padLeft(2, '0')}';
}

/// Combines the five independent SQL streams behind the dashboard. Each stream
/// is subscribed once per provider instance and cancelled when the screen goes
/// away, so filtered list rebuilds never recreate aggregate queries.
Stream<R> _combine5<A, B, C, D, E, R>(
  Stream<A> first,
  Stream<B> second,
  Stream<C> third,
  Stream<D> fourth,
  Stream<E> fifth,
  R Function(A, B, C, D, E) combine,
) {
  late final StreamController<R> controller;
  late final StreamSubscription<A> firstSubscription;
  late final StreamSubscription<B> secondSubscription;
  late final StreamSubscription<C> thirdSubscription;
  late final StreamSubscription<D> fourthSubscription;
  late final StreamSubscription<E> fifthSubscription;

  A? a;
  B? b;
  C? c;
  D? d;
  E? e;
  var hasA = false;
  var hasB = false;
  var hasC = false;
  var hasD = false;
  var hasE = false;
  var doneCount = 0;

  void emitIfReady() {
    if (!hasA || !hasB || !hasC || !hasD || !hasE || controller.isClosed) return;
    controller.add(combine(a as A, b as B, c as C, d as D, e as E));
  }

  void markDone() {
    doneCount++;
    if (doneCount == 5 && !controller.isClosed) controller.close();
  }

  controller = StreamController<R>(
    onListen: () {
      firstSubscription = first.listen(
        (value) {
          a = value;
          hasA = true;
          emitIfReady();
        },
        onError: controller.addError,
        onDone: markDone,
      );
      secondSubscription = second.listen(
        (value) {
          b = value;
          hasB = true;
          emitIfReady();
        },
        onError: controller.addError,
        onDone: markDone,
      );
      thirdSubscription = third.listen(
        (value) {
          c = value;
          hasC = true;
          emitIfReady();
        },
        onError: controller.addError,
        onDone: markDone,
      );
      fourthSubscription = fourth.listen(
        (value) {
          d = value;
          hasD = true;
          emitIfReady();
        },
        onError: controller.addError,
        onDone: markDone,
      );
      fifthSubscription = fifth.listen(
        (value) {
          e = value;
          hasE = true;
          emitIfReady();
        },
        onError: controller.addError,
        onDone: markDone,
      );
    },
    onCancel: () async {
      await firstSubscription.cancel();
      await secondSubscription.cancel();
      await thirdSubscription.cancel();
      await fourthSubscription.cancel();
      await fifthSubscription.cancel();
    },
  );

  return controller.stream;
}
