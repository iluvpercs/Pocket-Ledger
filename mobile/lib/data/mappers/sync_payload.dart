import 'dart:convert';

import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';

/// JSON payloads match the desktop v2 field lists exactly. New mobile writes
/// never emit legacy v1 payloads.
Map<String, Object?> accountPayload(Account account) => _sorted({
  'uuid': account.uuid.value,
  'name': account.name,
  'currency_code': account.currencyCode.value,
  'currency_precision': account.precision.value,
  'is_default': account.isDefault,
  'created_at_ms': account.createdAt.value,
  'updated_at_ms': account.updatedAt.value,
  'deleted_at_ms': account.deletedAt?.value,
  'revision': account.revision,
  'origin_device_id': account.originDeviceId.value,
  'last_modified_by': account.lastModifiedBy.value,
});

Map<String, Object?> transactionPayload(
  LedgerTransaction transaction, {
  required CurrencyCode currencyCode,
}) => _sorted({
  'uuid': transaction.uuid.value,
  'transaction_type': transaction.type.dbValue,
  'amount_minor': transaction.amount.minor,
  'currency_code': currencyCode.value,
  'currency_precision': currencyCode.precision.value,
  'account_uuid': transaction.accountUuid.value,
  'category': transaction.category,
  'description': transaction.description,
  'transaction_date': transaction.transactionDate,
  'created_at_ms': transaction.createdAt.value,
  'updated_at_ms': transaction.updatedAt.value,
  'deleted_at_ms': transaction.deletedAt?.value,
  'revision': transaction.revision,
  'origin_device_id': transaction.originDeviceId.value,
  'last_modified_by': transaction.lastModifiedBy.value,
  'import_hash': transaction.importHash,
  'external_ref': transaction.externalRef,
  'import_batch_id': transaction.importBatchId,
  'account_label': transaction.accountLabel,
});

String encodePayload(Map<String, Object?> payload) =>
    jsonEncode(_sorted(payload));

Map<String, Object?> _sorted(Map<String, Object?> source) => Map.fromEntries(
  source.entries.toList()..sort((a, b) => a.key.compareTo(b.key)),
);
