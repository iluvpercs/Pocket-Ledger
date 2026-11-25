import 'package:pocket_ledger_mobile/domain/validation_exception.dart';

/// Mirrors the desktop `sync_state` CHECK values. Sync transport is dormant.
enum SyncState {
  pending('pending'),
  synced('synced'),
  conflict('conflict');

  const SyncState(this.dbValue);

  final String dbValue;

  factory SyncState.parse(Object? input) {
    final text = input?.toString().trim().toLowerCase() ?? '';
    return switch (text) {
      'pending' => SyncState.pending,
      'synced' => SyncState.synced,
      'conflict' => SyncState.conflict,
      _ => throw DomainValidationException('Unknown sync state: $text.'),
    };
  }
}
