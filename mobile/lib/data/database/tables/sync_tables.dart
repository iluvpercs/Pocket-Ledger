import 'package:drift/drift.dart';

class SyncChanges extends Table {
  IntColumn get seq => integer().autoIncrement()();
  TextColumn get entityType => text().named('entity_type')();
  TextColumn get entityUuid => text().named('entity_uuid')();
  TextColumn get operation => text()();
  IntColumn get baseRevision => integer().nullable().named('base_revision')();
  IntColumn get newRevision => integer().nullable().named('new_revision')();
  TextColumn get payload => text()();
  TextColumn get originDeviceId => text().named('origin_device_id')();
  IntColumn get recordedAtMs => integer().named('recorded_at_ms')();
  IntColumn get payloadVersion =>
      integer().named('payload_version').withDefault(const Constant(1))();

  @override
  List<String> get customConstraints => [
    "CHECK (operation IN ('insert', 'update', 'delete'))",
  ];
}

class SyncPeers extends Table {
  TextColumn get peerDeviceId => text().named('peer_device_id')();
  IntColumn get lastAppliedSeq =>
      integer().named('last_applied_seq').withDefault(const Constant(0))();
  IntColumn get lastSentSeq =>
      integer().named('last_sent_seq').withDefault(const Constant(0))();
  IntColumn get lastSyncAtMs => integer().nullable().named('last_sync_at_ms')();

  @override
  Set<Column<Object>> get primaryKey => {peerDeviceId};
}

class SyncConflicts extends Table {
  TextColumn get conflictId => text().named('conflict_id')();
  TextColumn get entityUuid => text().named('entity_uuid')();
  TextColumn get peerDeviceId => text().nullable().named('peer_device_id')();
  TextColumn get localPayload => text().nullable().named('local_payload')();
  TextColumn get remotePayload => text().nullable().named('remote_payload')();
  TextColumn get resolution => text()();
  IntColumn get detectedAtMs => integer().named('detected_at_ms')();

  @override
  Set<Column<Object>> get primaryKey => {conflictId};
}
