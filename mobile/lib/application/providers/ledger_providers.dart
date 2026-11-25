import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:pocket_ledger_mobile/data/database/database.dart';
import 'package:pocket_ledger_mobile/data/repositories/drift_ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/repositories/ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

final databaseProvider = Provider<AppDatabase>((ref) {
  final database = AppDatabase();
  ref.onDispose(() {
    database.close();
  });
  return database;
});

final ledgerRepositoryProvider = Provider<LedgerRepository>((ref) {
  return DriftLedgerRepository(
    LedgerDao(ref.watch(databaseProvider)),
  );
});

/// Local bootstrap only. It never contacts another device.
final bootstrapProvider = FutureProvider<UtcMs>((ref) async {
  await ref.watch(ledgerRepositoryProvider).ensureBootstrapped();
  return UtcMs.now();
});

final defaultAccountProvider = StreamProvider<Account?>((ref) {
  ref.watch(bootstrapProvider);
  return ref.watch(ledgerRepositoryProvider).watchDefaultAccount();
});
