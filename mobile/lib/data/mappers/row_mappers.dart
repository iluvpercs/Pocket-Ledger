import 'package:pocket_ledger_mobile/data/database/database.dart' as generated;
import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/sync_state.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

Account mapAccount(generated.AccountRow row) => Account(
  uuid: Uuid.parse(row.uuid),
  name: row.name,
  currencyCode: CurrencyCode.parse(row.currencyCode),
  isDefault: row.isDefault,
  createdAt: UtcMs(row.createdAtMs),
  updatedAt: UtcMs(row.updatedAtMs),
  deletedAt: row.deletedAtMs == null ? null : UtcMs(row.deletedAtMs!),
  revision: row.revision,
  originDeviceId: Uuid.parse(row.originDeviceId),
  lastModifiedBy: Uuid.parse(row.lastModifiedBy),
  syncState: SyncState.parse(row.syncState),
);

LedgerTransaction mapTransaction(generated.Transaction row) => LedgerTransaction(
  id: row.id,
  uuid: Uuid.parse(row.uuid),
  type: TransactionType.parse(row.transactionType),
  amount: MinorAmount.fromMinor(row.amountMinor),
  accountUuid: Uuid.parse(row.accountUuid),
  category: row.category,
  description: row.description,
  transactionDate: row.transactionDate,
  createdAt: UtcMs(row.createdAtMs),
  updatedAt: UtcMs(row.updatedAtMs),
  deletedAt: row.deletedAtMs == null ? null : UtcMs(row.deletedAtMs!),
  revision: row.revision,
  originDeviceId: Uuid.parse(row.originDeviceId),
  lastModifiedBy: Uuid.parse(row.lastModifiedBy),
  syncState: SyncState.parse(row.syncState),
  importHash: row.importHash,
  externalRef: row.externalRef,
  importBatchId: row.importBatchId,
  accountLabel: row.accountLabel,
);
