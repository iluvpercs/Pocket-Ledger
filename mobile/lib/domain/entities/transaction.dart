import 'package:pocket_ledger_mobile/domain/entities/sync_state.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

/// Pure Dart transaction entity matching the desktop v4 columns.
final class LedgerTransaction {
  const LedgerTransaction({
    required this.id,
    required this.uuid,
    required this.type,
    required this.amount,
    required this.accountUuid,
    required this.category,
    required this.description,
    required this.transactionDate,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.revision,
    required this.originDeviceId,
    required this.lastModifiedBy,
    required this.syncState,
    this.importHash,
    this.externalRef,
    this.importBatchId,
    this.accountLabel,
  });

  final int id;
  final Uuid uuid;
  final TransactionType type;
  final MinorAmount amount;
  final Uuid accountUuid;
  final String category;
  final String? description;
  final String transactionDate;
  final UtcMs createdAt;
  final UtcMs updatedAt;
  final UtcMs? deletedAt;
  final int revision;
  final Uuid originDeviceId;
  final Uuid lastModifiedBy;
  final SyncState syncState;
  final String? importHash;
  final String? externalRef;
  final String? importBatchId;
  final String? accountLabel;

  bool get isLive => deletedAt == null;

  LedgerTransaction copyWith({
    UtcMs? updatedAt,
    UtcMs? deletedAt,
    int? revision,
    Uuid? lastModifiedBy,
    SyncState? syncState,
  }) {
    return LedgerTransaction(
      id: id,
      uuid: uuid,
      type: type,
      amount: amount,
      accountUuid: accountUuid,
      category: category,
      description: description,
      transactionDate: transactionDate,
      createdAt: createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      deletedAt: deletedAt ?? this.deletedAt,
      revision: revision ?? this.revision,
      originDeviceId: originDeviceId,
      lastModifiedBy: lastModifiedBy ?? this.lastModifiedBy,
      syncState: syncState ?? this.syncState,
      importHash: importHash,
      externalRef: externalRef,
      importBatchId: importBatchId,
      accountLabel: accountLabel,
    );
  }
}
