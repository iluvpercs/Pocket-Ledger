import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_precision.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

import 'sync_state.dart';

/// Pure Dart account entity matching the desktop v4 columns.
final class Account {
  const Account({
    required this.uuid,
    required this.name,
    required this.currencyCode,
    required this.isDefault,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.revision,
    required this.originDeviceId,
    required this.lastModifiedBy,
    required this.syncState,
  });

  final Uuid uuid;
  final String name;
  final CurrencyCode currencyCode;
  CurrencyPrecision get precision => currencyCode.precision;

  final bool isDefault;
  final UtcMs createdAt;
  final UtcMs updatedAt;
  final UtcMs? deletedAt;
  final int revision;
  final Uuid originDeviceId;
  final Uuid lastModifiedBy;
  final SyncState syncState;

  bool get isLive => deletedAt == null;

  Account copyWith({
    String? name,
    CurrencyCode? currencyCode,
    bool? isDefault,
    UtcMs? updatedAt,
    UtcMs? deletedAt,
    int? revision,
    Uuid? lastModifiedBy,
    SyncState? syncState,
  }) {
    return Account(
      uuid: uuid,
      name: name ?? this.name,
      currencyCode: currencyCode ?? this.currencyCode,
      isDefault: isDefault ?? this.isDefault,
      createdAt: createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      deletedAt: deletedAt ?? this.deletedAt,
      revision: revision ?? this.revision,
      originDeviceId: originDeviceId,
      lastModifiedBy: lastModifiedBy ?? this.lastModifiedBy,
      syncState: syncState ?? this.syncState,
    );
  }
}
