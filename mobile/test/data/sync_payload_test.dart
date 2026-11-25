import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';

import 'package:pocket_ledger_mobile/data/mappers/sync_payload.dart';
import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/sync_state.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

void main() {
  final device = Uuid.parse('11111111-1111-4111-8111-111111111111');
  final accountUuid = Uuid.parse('22222222-2222-4222-8222-222222222222');
  final transactionUuid = Uuid.parse('33333333-3333-4333-8333-333333333333');

  test('account payload contains exactly the desktop v2 fields', () {
    final account = Account(
      uuid: accountUuid,
      name: 'Default INR account',
      currencyCode: CurrencyCode.parse('INR'),
      isDefault: true,
      createdAt: UtcMs(1000),
      updatedAt: UtcMs(2000),
      revision: 1,
      originDeviceId: device,
      lastModifiedBy: device,
      syncState: SyncState.pending,
    );

    final payload = accountPayload(account);
    expect(
      payload.keys.toSet(),
      {
        'uuid',
        'name',
        'currency_code',
        'currency_precision',
        'is_default',
        'created_at_ms',
        'updated_at_ms',
        'deleted_at_ms',
        'revision',
        'origin_device_id',
        'last_modified_by',
      },
    );
    expect(payload['currency_precision'], 2);
    expect(payload['is_default'], isTrue);
  });

  test('transaction payload is v2 and never contains a floating amount', () {
    final transaction = LedgerTransaction(
      id: 1,
      uuid: transactionUuid,
      type: TransactionType.expense,
      amount: MinorAmount.fromMinor(1234),
      accountUuid: accountUuid,
      category: 'Food',
      description: null,
      transactionDate: '2026-11-25',
      createdAt: UtcMs(1000),
      updatedAt: UtcMs(2000),
      revision: 1,
      originDeviceId: device,
      lastModifiedBy: device,
      syncState: SyncState.pending,
    );

    final payload = transactionPayload(
      transaction,
      currencyCode: CurrencyCode.parse('INR'),
    );
    expect(
      payload.keys.toSet(),
      {
        'uuid',
        'transaction_type',
        'amount_minor',
        'currency_code',
        'currency_precision',
        'account_uuid',
        'category',
        'description',
        'transaction_date',
        'created_at_ms',
        'updated_at_ms',
        'deleted_at_ms',
        'revision',
        'origin_device_id',
        'last_modified_by',
        'import_hash',
        'external_ref',
        'import_batch_id',
        'account_label',
      },
    );
    expect(payload['amount_minor'], 1234);
    expect(payload.containsKey('amount'), isFalse);

    final encoded = encodePayload(payload);
    final decoded = jsonDecode(encoded) as Map<String, dynamic>;
    final keys = decoded.keys.toList();
    expect(keys, keys.toList()..sort());
  });
}
