import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqlite3/sqlite3.dart' as sqlite3_lib;

import 'package:pocket_ledger_mobile/data/database/tables/tables.dart';
import 'package:pocket_ledger_mobile/data/mappers/sync_payload.dart';
import 'package:pocket_ledger_mobile/domain/entities/account.dart' as domain_account;
import 'package:pocket_ledger_mobile/domain/entities/ledger_constants.dart';
import 'package:pocket_ledger_mobile/domain/entities/sync_state.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

part 'database.g.dart';

@DriftDatabase(
  tables: [
    AppMeta,
    Devices,
    Accounts,
    Transactions,
    SyncChanges,
    SyncPeers,
    SyncConflicts,
    ImportBatches,
  ],
)
class AppDatabase extends _$AppDatabase {
  AppDatabase([QueryExecutor? executor]) : super(executor ?? _openConnection());

  @override
  int get schemaVersion => LedgerConstants.schemaVersion;

  @override
  MigrationStrategy get migration => MigrationStrategy(
    onCreate: (migrator) async {
      await migrator.createAll();
      await _seedFreshSchema();
    },
    onUpgrade: (migrator, from, to) async {
      throw UnsupportedError(
        'Mobile schema has no historical migrations: $from -> $to. '
        'The Android database is always created at v4.',
      );
    },
    beforeOpen: (details) async {
      await customStatement('PRAGMA foreign_keys = ON');
    },
  );

  static QueryExecutor _openConnection() {
    return LazyDatabase(() async {
      final supportDirectory = await getApplicationSupportDirectory();
      final temporaryDirectory = await getTemporaryDirectory();
      final databaseFile = File(
        p.join(supportDirectory.path, LedgerConstants.databaseFileName),
      );
      final temporaryPath = temporaryDirectory.path;

      // Globals do not cross isolates. Set SQLite's temp directory on the
      // background isolate that actually opens the database.
      return NativeDatabase.createInBackground(
        databaseFile,
        isolateSetup: () {
          sqlite3_lib.sqlite3.tempDirectory = temporaryPath;
        },
      );
    });
  }

  /// Seeds the Android identity and deterministic default account.
  /// Callers must ensure the v4 tables already exist.
  Future<void> _seedFreshSchema() async {
    final deviceId = Uuid.generate();
    final now = UtcMs.now();
    final deviceName = 'Pocket Ledger Phone';

    await batch((items) {
      items.insertAll(appMeta, [
        AppMetaCompanion.insert(
          key: LedgerConstants.appMetaDeviceIdKey,
          value: deviceId.value,
        ),
        AppMetaCompanion.insert(
          key: LedgerConstants.appMetaDeviceNameKey,
          value: deviceName,
        ),
        AppMetaCompanion.insert(
          key: LedgerConstants.appMetaDevicePlatformKey,
          value: LedgerConstants.androidPlatform,
        ),
      ]);
    });

    await into(devices).insert(
      DevicesCompanion.insert(
        deviceId: deviceId.value,
        name: deviceName,
        platform: LedgerConstants.androidPlatform,
      ),
    );

    final account = domain_account.Account(
      uuid: Uuid.parse(LedgerConstants.defaultAccountUuid),
      name: LedgerConstants.defaultAccountName,
      currencyCode: CurrencyCode.parse(LedgerConstants.defaultCurrencyCode),
      isDefault: true,
      createdAt: now,
      updatedAt: now,
      revision: 1,
      originDeviceId: deviceId,
      lastModifiedBy: deviceId,
      syncState: SyncState.pending,
    );

    await into(accounts).insert(
      AccountsCompanion.insert(
        uuid: account.uuid.value,
        name: account.name,
        currencyCode: account.currencyCode.value,
        currencyPrecision: account.precision.value,
        isDefault: const Value(true),
        createdAtMs: account.createdAt.value,
        updatedAtMs: account.updatedAt.value,
        deletedAtMs: const Value(null),
        revision: const Value(1),
        originDeviceId: deviceId.value,
        lastModifiedBy: deviceId.value,
        syncState: Value(account.syncState.dbValue),
      ),
    );

    await appendChange(
      entityType: 'account',
      entityUuid: account.uuid.value,
      operation: 'insert',
      baseRevision: null,
      newRevision: account.revision,
      payload: accountPayload(account),
      originDeviceId: deviceId.value,
      recordedAtMs: now.value,
    );
  }

  /// Idempotent startup check for databases created by an earlier build.
  Future<void> ensureSeeded() async {
    final existing = await (select(appMeta)
          ..where((row) => row.key.equals(LedgerConstants.appMetaDeviceIdKey)))
        .getSingleOrNull();
    if (existing != null) return;

    await transaction(() async {
      final device = await (select(appMeta)
            ..where(
              (row) => row.key.equals(LedgerConstants.appMetaDeviceIdKey),
            ))
          .getSingleOrNull();
      if (device == null) {
        await _seedFreshSchema();
      }
    });
  }

  /// Appends one v2 outbox event. Call inside the same transaction as the write.
  Future<void> appendChange({
    required String entityType,
    required String entityUuid,
    required String operation,
    required int? baseRevision,
    required int newRevision,
    required Map<String, Object?> payload,
    required String originDeviceId,
    required int recordedAtMs,
  }) {
    return into(syncChanges).insert(
      SyncChangesCompanion.insert(
        entityType: entityType,
        entityUuid: entityUuid,
        operation: operation,
        baseRevision: Value(baseRevision),
        newRevision: Value(newRevision),
        payload: encodePayload(payload),
        originDeviceId: originDeviceId,
        recordedAtMs: recordedAtMs,
        payloadVersion: const Value(2),
      ),
    );
  }
}
