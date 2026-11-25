import 'package:drift/drift.dart';

class ImportBatches extends Table {
  TextColumn get batchId => text().named('batch_id')();
  TextColumn get sourceFile => text().nullable().named('source_file')();
  TextColumn get sourceType => text().nullable().named('source_type')();
  TextColumn get bankFormat => text().nullable().named('bank_format')();
  IntColumn get importedAtMs => integer().named('imported_at_ms')();
  IntColumn get importedCount =>
      integer().named('imported_count').withDefault(const Constant(0))();
  IntColumn get skippedCount =>
      integer().named('skipped_count').withDefault(const Constant(0))();
  TextColumn get deviceId => text().nullable().named('device_id')();

  @override
  Set<Column<Object>> get primaryKey => {batchId};

  @override
  List<String> get customConstraints => [
    "CHECK (source_type IN ('csv', 'pdf'))",
  ];
}
