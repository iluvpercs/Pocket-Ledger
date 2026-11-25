import 'package:drift/drift.dart';

@TableIndex.sql('''
CREATE UNIQUE INDEX idx_accounts_one_default
ON accounts(is_default)
WHERE is_default = 1 AND deleted_at_ms IS NULL
''')
@TableIndex(name: 'idx_accounts_live', columns: {#deletedAtMs, #name})
class Accounts extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get uuid => text().unique()();
  TextColumn get name => text()();
  TextColumn get currencyCode => text().named('currency_code')();
  IntColumn get currencyPrecision => integer().named('currency_precision')();
  BoolColumn get isDefault =>
      boolean().named('is_default').withDefault(const Constant(false))();
  IntColumn get createdAtMs => integer().named('created_at_ms')();
  IntColumn get updatedAtMs => integer().named('updated_at_ms')();
  IntColumn get deletedAtMs => integer().nullable().named('deleted_at_ms')();
  IntColumn get revision => integer().withDefault(const Constant(1))();
  TextColumn get originDeviceId => text().named('origin_device_id')();
  TextColumn get lastModifiedBy => text().named('last_modified_by')();
  TextColumn get syncState =>
      text().named('sync_state').withDefault(const Constant('pending'))();

  @override
  List<String> get customConstraints => [
    'CHECK (currency_precision IN (0, 2, 3))',
    'CHECK (is_default IN (0, 1))',
    'CHECK (revision >= 1)',
    "CHECK (sync_state IN ('pending', 'synced', 'conflict'))",
  ];
}
