import 'package:drift/drift.dart';

@TableIndex.sql('''
CREATE INDEX idx_tx_date
ON transactions(transaction_date DESC, id DESC)
''')
@TableIndex.sql('''
CREATE INDEX idx_tx_updated ON transactions(updated_at_ms)
''')
@TableIndex.sql('''
CREATE INDEX idx_tx_account_date
ON transactions(account_uuid, transaction_date DESC, id DESC)
''')
@TableIndex.sql('''
CREATE INDEX idx_tx_account_date_deleted
ON transactions(account_uuid, transaction_date, deleted_at_ms)
''')
@TableIndex.sql('''
CREATE UNIQUE INDEX idx_tx_account_import_hash
ON transactions(account_uuid, import_hash)
WHERE import_hash IS NOT NULL AND deleted_at_ms IS NULL
''')
class Transactions extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get transactionType => text().named('transaction_type')();
  IntColumn get amountMinor => integer().named('amount_minor')();
  TextColumn get category => text()();
  TextColumn get description => text().nullable()();
  TextColumn get transactionDate => text().named('transaction_date')();

  TextColumn get uuid => text().unique()();
  IntColumn get createdAtMs => integer().named('created_at_ms')();
  IntColumn get updatedAtMs => integer().named('updated_at_ms')();
  IntColumn get deletedAtMs => integer().nullable().named('deleted_at_ms')();
  IntColumn get revision => integer().withDefault(const Constant(1))();
  TextColumn get originDeviceId => text().named('origin_device_id')();
  TextColumn get lastModifiedBy => text().named('last_modified_by')();
  TextColumn get syncState =>
      text().named('sync_state').withDefault(const Constant('pending'))();

  TextColumn get accountUuid => text().named('account_uuid')();
  TextColumn get importHash => text().nullable().named('import_hash')();
  TextColumn get externalRef => text().nullable().named('external_ref')();
  TextColumn get importBatchId =>
      text().nullable().named('import_batch_id')();
  TextColumn get accountLabel => text().nullable().named('account_label')();

  @override
  List<String> get customConstraints => [
    "CHECK (transaction_type IN ('income', 'expense'))",
    'CHECK (amount_minor > 0)',
    'CHECK (revision >= 1)',
    "CHECK (sync_state IN ('pending', 'synced', 'conflict'))",
    'FOREIGN KEY (account_uuid) REFERENCES accounts(uuid)',
  ];
}
