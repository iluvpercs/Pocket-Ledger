import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/sync_state.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

/// Deterministic domain fixtures for pure unit tests. These never touch the
/// database; repository tests create their own rows through the repository.
Account testAccount({
  String name = 'Cash',
  String currencyCode = 'INR',
  bool isDefault = true,
  Uuid? uuid,
  UtcMs? now,
}) {
  final timestamp = now ?? UtcMs(1_000);
  final device = Uuid.parse('00000000-0000-4000-8000-000000000001');
  return Account(
    uuid: uuid ?? Uuid.generate(),
    name: name,
    currencyCode: CurrencyCode.parse(currencyCode),
    isDefault: isDefault,
    createdAt: timestamp,
    updatedAt: timestamp,
    revision: 1,
    originDeviceId: device,
    lastModifiedBy: device,
    syncState: SyncState.pending,
  );
}

LedgerTransaction testTransaction({
  required Account account,
  required int id,
  required int amountMinor,
  TransactionType type = TransactionType.expense,
  String transactionDate = '2026-11-25',
  String category = 'Food',
  String? description,
  String? importHash,
  UtcMs? now,
}) {
  final timestamp = now ?? UtcMs(1_000);
  final device = Uuid.parse('00000000-0000-4000-8000-000000000001');
  return LedgerTransaction(
    id: id,
    uuid: Uuid.generate(),
    type: type,
    amount: MinorAmount.fromMinor(amountMinor),
    accountUuid: account.uuid,
    category: category,
    description: description,
    transactionDate: transactionDate,
    createdAt: timestamp,
    updatedAt: timestamp,
    revision: 1,
    originDeviceId: device,
    lastModifiedBy: device,
    syncState: SyncState.pending,
    importHash: importHash,
  );
}
