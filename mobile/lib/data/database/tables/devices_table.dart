import 'package:drift/drift.dart';

class Devices extends Table {
  TextColumn get deviceId => text().named('device_id')();
  TextColumn get name => text()();
  TextColumn get platform => text()();
  TextColumn get tokenHash => text().nullable().named('token_hash')();
  TextColumn get certFingerprint =>
      text().nullable().named('cert_fingerprint')();
  IntColumn get pairedAtMs => integer().nullable().named('paired_at_ms')();
  IntColumn get lastSeenMs => integer().nullable().named('last_seen_ms')();
  IntColumn get revokedAtMs => integer().nullable().named('revoked_at_ms')();

  @override
  Set<Column<Object>> get primaryKey => {deviceId};

  @override
  List<String> get customConstraints => [
    "CHECK (platform IN ('windows', 'android'))",
  ];
}
