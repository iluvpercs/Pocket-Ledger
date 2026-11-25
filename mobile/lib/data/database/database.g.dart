// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'database.dart';

// ignore_for_file: type=lint
class $AppMetaTable extends AppMeta with TableInfo<$AppMetaTable, AppMetaData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $AppMetaTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _keyMeta = const VerificationMeta('key');
  @override
  late final GeneratedColumn<String> key = GeneratedColumn<String>(
    'key',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _valueMeta = const VerificationMeta('value');
  @override
  late final GeneratedColumn<String> value = GeneratedColumn<String>(
    'value',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [key, value];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'app_meta';
  @override
  VerificationContext validateIntegrity(
    Insertable<AppMetaData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('key')) {
      context.handle(
        _keyMeta,
        key.isAcceptableOrUnknown(data['key']!, _keyMeta),
      );
    } else if (isInserting) {
      context.missing(_keyMeta);
    }
    if (data.containsKey('value')) {
      context.handle(
        _valueMeta,
        value.isAcceptableOrUnknown(data['value']!, _valueMeta),
      );
    } else if (isInserting) {
      context.missing(_valueMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {key};
  @override
  AppMetaData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return AppMetaData(
      key: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}key'],
      )!,
      value: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}value'],
      )!,
    );
  }

  @override
  $AppMetaTable createAlias(String alias) {
    return $AppMetaTable(attachedDatabase, alias);
  }
}

class AppMetaData extends DataClass implements Insertable<AppMetaData> {
  final String key;
  final String value;
  const AppMetaData({required this.key, required this.value});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['key'] = Variable<String>(key);
    map['value'] = Variable<String>(value);
    return map;
  }

  AppMetaCompanion toCompanion(bool nullToAbsent) {
    return AppMetaCompanion(key: Value(key), value: Value(value));
  }

  factory AppMetaData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return AppMetaData(
      key: serializer.fromJson<String>(json['key']),
      value: serializer.fromJson<String>(json['value']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'key': serializer.toJson<String>(key),
      'value': serializer.toJson<String>(value),
    };
  }

  AppMetaData copyWith({String? key, String? value}) =>
      AppMetaData(key: key ?? this.key, value: value ?? this.value);
  AppMetaData copyWithCompanion(AppMetaCompanion data) {
    return AppMetaData(
      key: data.key.present ? data.key.value : this.key,
      value: data.value.present ? data.value.value : this.value,
    );
  }

  @override
  String toString() {
    return (StringBuffer('AppMetaData(')
          ..write('key: $key, ')
          ..write('value: $value')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(key, value);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is AppMetaData &&
          other.key == this.key &&
          other.value == this.value);
}

class AppMetaCompanion extends UpdateCompanion<AppMetaData> {
  final Value<String> key;
  final Value<String> value;
  final Value<int> rowid;
  const AppMetaCompanion({
    this.key = const Value.absent(),
    this.value = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  AppMetaCompanion.insert({
    required String key,
    required String value,
    this.rowid = const Value.absent(),
  }) : key = Value(key),
       value = Value(value);
  static Insertable<AppMetaData> custom({
    Expression<String>? key,
    Expression<String>? value,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (key != null) 'key': key,
      if (value != null) 'value': value,
      if (rowid != null) 'rowid': rowid,
    });
  }

  AppMetaCompanion copyWith({
    Value<String>? key,
    Value<String>? value,
    Value<int>? rowid,
  }) {
    return AppMetaCompanion(
      key: key ?? this.key,
      value: value ?? this.value,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (key.present) {
      map['key'] = Variable<String>(key.value);
    }
    if (value.present) {
      map['value'] = Variable<String>(value.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('AppMetaCompanion(')
          ..write('key: $key, ')
          ..write('value: $value, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $DevicesTable extends Devices with TableInfo<$DevicesTable, Device> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $DevicesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _deviceIdMeta = const VerificationMeta(
    'deviceId',
  );
  @override
  late final GeneratedColumn<String> deviceId = GeneratedColumn<String>(
    'device_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
    'name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _platformMeta = const VerificationMeta(
    'platform',
  );
  @override
  late final GeneratedColumn<String> platform = GeneratedColumn<String>(
    'platform',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _tokenHashMeta = const VerificationMeta(
    'tokenHash',
  );
  @override
  late final GeneratedColumn<String> tokenHash = GeneratedColumn<String>(
    'token_hash',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _certFingerprintMeta = const VerificationMeta(
    'certFingerprint',
  );
  @override
  late final GeneratedColumn<String> certFingerprint = GeneratedColumn<String>(
    'cert_fingerprint',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _pairedAtMsMeta = const VerificationMeta(
    'pairedAtMs',
  );
  @override
  late final GeneratedColumn<int> pairedAtMs = GeneratedColumn<int>(
    'paired_at_ms',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _lastSeenMsMeta = const VerificationMeta(
    'lastSeenMs',
  );
  @override
  late final GeneratedColumn<int> lastSeenMs = GeneratedColumn<int>(
    'last_seen_ms',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _revokedAtMsMeta = const VerificationMeta(
    'revokedAtMs',
  );
  @override
  late final GeneratedColumn<int> revokedAtMs = GeneratedColumn<int>(
    'revoked_at_ms',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    deviceId,
    name,
    platform,
    tokenHash,
    certFingerprint,
    pairedAtMs,
    lastSeenMs,
    revokedAtMs,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'devices';
  @override
  VerificationContext validateIntegrity(
    Insertable<Device> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('device_id')) {
      context.handle(
        _deviceIdMeta,
        deviceId.isAcceptableOrUnknown(data['device_id']!, _deviceIdMeta),
      );
    } else if (isInserting) {
      context.missing(_deviceIdMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
        _nameMeta,
        name.isAcceptableOrUnknown(data['name']!, _nameMeta),
      );
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('platform')) {
      context.handle(
        _platformMeta,
        platform.isAcceptableOrUnknown(data['platform']!, _platformMeta),
      );
    } else if (isInserting) {
      context.missing(_platformMeta);
    }
    if (data.containsKey('token_hash')) {
      context.handle(
        _tokenHashMeta,
        tokenHash.isAcceptableOrUnknown(data['token_hash']!, _tokenHashMeta),
      );
    }
    if (data.containsKey('cert_fingerprint')) {
      context.handle(
        _certFingerprintMeta,
        certFingerprint.isAcceptableOrUnknown(
          data['cert_fingerprint']!,
          _certFingerprintMeta,
        ),
      );
    }
    if (data.containsKey('paired_at_ms')) {
      context.handle(
        _pairedAtMsMeta,
        pairedAtMs.isAcceptableOrUnknown(
          data['paired_at_ms']!,
          _pairedAtMsMeta,
        ),
      );
    }
    if (data.containsKey('last_seen_ms')) {
      context.handle(
        _lastSeenMsMeta,
        lastSeenMs.isAcceptableOrUnknown(
          data['last_seen_ms']!,
          _lastSeenMsMeta,
        ),
      );
    }
    if (data.containsKey('revoked_at_ms')) {
      context.handle(
        _revokedAtMsMeta,
        revokedAtMs.isAcceptableOrUnknown(
          data['revoked_at_ms']!,
          _revokedAtMsMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {deviceId};
  @override
  Device map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Device(
      deviceId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}device_id'],
      )!,
      name: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}name'],
      )!,
      platform: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}platform'],
      )!,
      tokenHash: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}token_hash'],
      ),
      certFingerprint: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}cert_fingerprint'],
      ),
      pairedAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}paired_at_ms'],
      ),
      lastSeenMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}last_seen_ms'],
      ),
      revokedAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}revoked_at_ms'],
      ),
    );
  }

  @override
  $DevicesTable createAlias(String alias) {
    return $DevicesTable(attachedDatabase, alias);
  }
}

class Device extends DataClass implements Insertable<Device> {
  final String deviceId;
  final String name;
  final String platform;
  final String? tokenHash;
  final String? certFingerprint;
  final int? pairedAtMs;
  final int? lastSeenMs;
  final int? revokedAtMs;
  const Device({
    required this.deviceId,
    required this.name,
    required this.platform,
    this.tokenHash,
    this.certFingerprint,
    this.pairedAtMs,
    this.lastSeenMs,
    this.revokedAtMs,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['device_id'] = Variable<String>(deviceId);
    map['name'] = Variable<String>(name);
    map['platform'] = Variable<String>(platform);
    if (!nullToAbsent || tokenHash != null) {
      map['token_hash'] = Variable<String>(tokenHash);
    }
    if (!nullToAbsent || certFingerprint != null) {
      map['cert_fingerprint'] = Variable<String>(certFingerprint);
    }
    if (!nullToAbsent || pairedAtMs != null) {
      map['paired_at_ms'] = Variable<int>(pairedAtMs);
    }
    if (!nullToAbsent || lastSeenMs != null) {
      map['last_seen_ms'] = Variable<int>(lastSeenMs);
    }
    if (!nullToAbsent || revokedAtMs != null) {
      map['revoked_at_ms'] = Variable<int>(revokedAtMs);
    }
    return map;
  }

  DevicesCompanion toCompanion(bool nullToAbsent) {
    return DevicesCompanion(
      deviceId: Value(deviceId),
      name: Value(name),
      platform: Value(platform),
      tokenHash: tokenHash == null && nullToAbsent
          ? const Value.absent()
          : Value(tokenHash),
      certFingerprint: certFingerprint == null && nullToAbsent
          ? const Value.absent()
          : Value(certFingerprint),
      pairedAtMs: pairedAtMs == null && nullToAbsent
          ? const Value.absent()
          : Value(pairedAtMs),
      lastSeenMs: lastSeenMs == null && nullToAbsent
          ? const Value.absent()
          : Value(lastSeenMs),
      revokedAtMs: revokedAtMs == null && nullToAbsent
          ? const Value.absent()
          : Value(revokedAtMs),
    );
  }

  factory Device.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Device(
      deviceId: serializer.fromJson<String>(json['deviceId']),
      name: serializer.fromJson<String>(json['name']),
      platform: serializer.fromJson<String>(json['platform']),
      tokenHash: serializer.fromJson<String?>(json['tokenHash']),
      certFingerprint: serializer.fromJson<String?>(json['certFingerprint']),
      pairedAtMs: serializer.fromJson<int?>(json['pairedAtMs']),
      lastSeenMs: serializer.fromJson<int?>(json['lastSeenMs']),
      revokedAtMs: serializer.fromJson<int?>(json['revokedAtMs']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'deviceId': serializer.toJson<String>(deviceId),
      'name': serializer.toJson<String>(name),
      'platform': serializer.toJson<String>(platform),
      'tokenHash': serializer.toJson<String?>(tokenHash),
      'certFingerprint': serializer.toJson<String?>(certFingerprint),
      'pairedAtMs': serializer.toJson<int?>(pairedAtMs),
      'lastSeenMs': serializer.toJson<int?>(lastSeenMs),
      'revokedAtMs': serializer.toJson<int?>(revokedAtMs),
    };
  }

  Device copyWith({
    String? deviceId,
    String? name,
    String? platform,
    Value<String?> tokenHash = const Value.absent(),
    Value<String?> certFingerprint = const Value.absent(),
    Value<int?> pairedAtMs = const Value.absent(),
    Value<int?> lastSeenMs = const Value.absent(),
    Value<int?> revokedAtMs = const Value.absent(),
  }) => Device(
    deviceId: deviceId ?? this.deviceId,
    name: name ?? this.name,
    platform: platform ?? this.platform,
    tokenHash: tokenHash.present ? tokenHash.value : this.tokenHash,
    certFingerprint: certFingerprint.present
        ? certFingerprint.value
        : this.certFingerprint,
    pairedAtMs: pairedAtMs.present ? pairedAtMs.value : this.pairedAtMs,
    lastSeenMs: lastSeenMs.present ? lastSeenMs.value : this.lastSeenMs,
    revokedAtMs: revokedAtMs.present ? revokedAtMs.value : this.revokedAtMs,
  );
  Device copyWithCompanion(DevicesCompanion data) {
    return Device(
      deviceId: data.deviceId.present ? data.deviceId.value : this.deviceId,
      name: data.name.present ? data.name.value : this.name,
      platform: data.platform.present ? data.platform.value : this.platform,
      tokenHash: data.tokenHash.present ? data.tokenHash.value : this.tokenHash,
      certFingerprint: data.certFingerprint.present
          ? data.certFingerprint.value
          : this.certFingerprint,
      pairedAtMs: data.pairedAtMs.present
          ? data.pairedAtMs.value
          : this.pairedAtMs,
      lastSeenMs: data.lastSeenMs.present
          ? data.lastSeenMs.value
          : this.lastSeenMs,
      revokedAtMs: data.revokedAtMs.present
          ? data.revokedAtMs.value
          : this.revokedAtMs,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Device(')
          ..write('deviceId: $deviceId, ')
          ..write('name: $name, ')
          ..write('platform: $platform, ')
          ..write('tokenHash: $tokenHash, ')
          ..write('certFingerprint: $certFingerprint, ')
          ..write('pairedAtMs: $pairedAtMs, ')
          ..write('lastSeenMs: $lastSeenMs, ')
          ..write('revokedAtMs: $revokedAtMs')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    deviceId,
    name,
    platform,
    tokenHash,
    certFingerprint,
    pairedAtMs,
    lastSeenMs,
    revokedAtMs,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Device &&
          other.deviceId == this.deviceId &&
          other.name == this.name &&
          other.platform == this.platform &&
          other.tokenHash == this.tokenHash &&
          other.certFingerprint == this.certFingerprint &&
          other.pairedAtMs == this.pairedAtMs &&
          other.lastSeenMs == this.lastSeenMs &&
          other.revokedAtMs == this.revokedAtMs);
}

class DevicesCompanion extends UpdateCompanion<Device> {
  final Value<String> deviceId;
  final Value<String> name;
  final Value<String> platform;
  final Value<String?> tokenHash;
  final Value<String?> certFingerprint;
  final Value<int?> pairedAtMs;
  final Value<int?> lastSeenMs;
  final Value<int?> revokedAtMs;
  final Value<int> rowid;
  const DevicesCompanion({
    this.deviceId = const Value.absent(),
    this.name = const Value.absent(),
    this.platform = const Value.absent(),
    this.tokenHash = const Value.absent(),
    this.certFingerprint = const Value.absent(),
    this.pairedAtMs = const Value.absent(),
    this.lastSeenMs = const Value.absent(),
    this.revokedAtMs = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  DevicesCompanion.insert({
    required String deviceId,
    required String name,
    required String platform,
    this.tokenHash = const Value.absent(),
    this.certFingerprint = const Value.absent(),
    this.pairedAtMs = const Value.absent(),
    this.lastSeenMs = const Value.absent(),
    this.revokedAtMs = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : deviceId = Value(deviceId),
       name = Value(name),
       platform = Value(platform);
  static Insertable<Device> custom({
    Expression<String>? deviceId,
    Expression<String>? name,
    Expression<String>? platform,
    Expression<String>? tokenHash,
    Expression<String>? certFingerprint,
    Expression<int>? pairedAtMs,
    Expression<int>? lastSeenMs,
    Expression<int>? revokedAtMs,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (deviceId != null) 'device_id': deviceId,
      if (name != null) 'name': name,
      if (platform != null) 'platform': platform,
      if (tokenHash != null) 'token_hash': tokenHash,
      if (certFingerprint != null) 'cert_fingerprint': certFingerprint,
      if (pairedAtMs != null) 'paired_at_ms': pairedAtMs,
      if (lastSeenMs != null) 'last_seen_ms': lastSeenMs,
      if (revokedAtMs != null) 'revoked_at_ms': revokedAtMs,
      if (rowid != null) 'rowid': rowid,
    });
  }

  DevicesCompanion copyWith({
    Value<String>? deviceId,
    Value<String>? name,
    Value<String>? platform,
    Value<String?>? tokenHash,
    Value<String?>? certFingerprint,
    Value<int?>? pairedAtMs,
    Value<int?>? lastSeenMs,
    Value<int?>? revokedAtMs,
    Value<int>? rowid,
  }) {
    return DevicesCompanion(
      deviceId: deviceId ?? this.deviceId,
      name: name ?? this.name,
      platform: platform ?? this.platform,
      tokenHash: tokenHash ?? this.tokenHash,
      certFingerprint: certFingerprint ?? this.certFingerprint,
      pairedAtMs: pairedAtMs ?? this.pairedAtMs,
      lastSeenMs: lastSeenMs ?? this.lastSeenMs,
      revokedAtMs: revokedAtMs ?? this.revokedAtMs,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (deviceId.present) {
      map['device_id'] = Variable<String>(deviceId.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (platform.present) {
      map['platform'] = Variable<String>(platform.value);
    }
    if (tokenHash.present) {
      map['token_hash'] = Variable<String>(tokenHash.value);
    }
    if (certFingerprint.present) {
      map['cert_fingerprint'] = Variable<String>(certFingerprint.value);
    }
    if (pairedAtMs.present) {
      map['paired_at_ms'] = Variable<int>(pairedAtMs.value);
    }
    if (lastSeenMs.present) {
      map['last_seen_ms'] = Variable<int>(lastSeenMs.value);
    }
    if (revokedAtMs.present) {
      map['revoked_at_ms'] = Variable<int>(revokedAtMs.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('DevicesCompanion(')
          ..write('deviceId: $deviceId, ')
          ..write('name: $name, ')
          ..write('platform: $platform, ')
          ..write('tokenHash: $tokenHash, ')
          ..write('certFingerprint: $certFingerprint, ')
          ..write('pairedAtMs: $pairedAtMs, ')
          ..write('lastSeenMs: $lastSeenMs, ')
          ..write('revokedAtMs: $revokedAtMs, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $AccountsTable extends Accounts
    with TableInfo<$AccountsTable, AccountRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $AccountsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _uuidMeta = const VerificationMeta('uuid');
  @override
  late final GeneratedColumn<String> uuid = GeneratedColumn<String>(
    'uuid',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways('UNIQUE'),
  );
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
    'name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _currencyCodeMeta = const VerificationMeta(
    'currencyCode',
  );
  @override
  late final GeneratedColumn<String> currencyCode = GeneratedColumn<String>(
    'currency_code',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _currencyPrecisionMeta = const VerificationMeta(
    'currencyPrecision',
  );
  @override
  late final GeneratedColumn<int> currencyPrecision = GeneratedColumn<int>(
    'currency_precision',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _isDefaultMeta = const VerificationMeta(
    'isDefault',
  );
  @override
  late final GeneratedColumn<bool> isDefault = GeneratedColumn<bool>(
    'is_default',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_default" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _createdAtMsMeta = const VerificationMeta(
    'createdAtMs',
  );
  @override
  late final GeneratedColumn<int> createdAtMs = GeneratedColumn<int>(
    'created_at_ms',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMsMeta = const VerificationMeta(
    'updatedAtMs',
  );
  @override
  late final GeneratedColumn<int> updatedAtMs = GeneratedColumn<int>(
    'updated_at_ms',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _deletedAtMsMeta = const VerificationMeta(
    'deletedAtMs',
  );
  @override
  late final GeneratedColumn<int> deletedAtMs = GeneratedColumn<int>(
    'deleted_at_ms',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _revisionMeta = const VerificationMeta(
    'revision',
  );
  @override
  late final GeneratedColumn<int> revision = GeneratedColumn<int>(
    'revision',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(1),
  );
  static const VerificationMeta _originDeviceIdMeta = const VerificationMeta(
    'originDeviceId',
  );
  @override
  late final GeneratedColumn<String> originDeviceId = GeneratedColumn<String>(
    'origin_device_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _lastModifiedByMeta = const VerificationMeta(
    'lastModifiedBy',
  );
  @override
  late final GeneratedColumn<String> lastModifiedBy = GeneratedColumn<String>(
    'last_modified_by',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _syncStateMeta = const VerificationMeta(
    'syncState',
  );
  @override
  late final GeneratedColumn<String> syncState = GeneratedColumn<String>(
    'sync_state',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('pending'),
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    uuid,
    name,
    currencyCode,
    currencyPrecision,
    isDefault,
    createdAtMs,
    updatedAtMs,
    deletedAtMs,
    revision,
    originDeviceId,
    lastModifiedBy,
    syncState,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'accounts';
  @override
  VerificationContext validateIntegrity(
    Insertable<AccountRow> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('uuid')) {
      context.handle(
        _uuidMeta,
        uuid.isAcceptableOrUnknown(data['uuid']!, _uuidMeta),
      );
    } else if (isInserting) {
      context.missing(_uuidMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
        _nameMeta,
        name.isAcceptableOrUnknown(data['name']!, _nameMeta),
      );
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('currency_code')) {
      context.handle(
        _currencyCodeMeta,
        currencyCode.isAcceptableOrUnknown(
          data['currency_code']!,
          _currencyCodeMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_currencyCodeMeta);
    }
    if (data.containsKey('currency_precision')) {
      context.handle(
        _currencyPrecisionMeta,
        currencyPrecision.isAcceptableOrUnknown(
          data['currency_precision']!,
          _currencyPrecisionMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_currencyPrecisionMeta);
    }
    if (data.containsKey('is_default')) {
      context.handle(
        _isDefaultMeta,
        isDefault.isAcceptableOrUnknown(data['is_default']!, _isDefaultMeta),
      );
    }
    if (data.containsKey('created_at_ms')) {
      context.handle(
        _createdAtMsMeta,
        createdAtMs.isAcceptableOrUnknown(
          data['created_at_ms']!,
          _createdAtMsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_createdAtMsMeta);
    }
    if (data.containsKey('updated_at_ms')) {
      context.handle(
        _updatedAtMsMeta,
        updatedAtMs.isAcceptableOrUnknown(
          data['updated_at_ms']!,
          _updatedAtMsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMsMeta);
    }
    if (data.containsKey('deleted_at_ms')) {
      context.handle(
        _deletedAtMsMeta,
        deletedAtMs.isAcceptableOrUnknown(
          data['deleted_at_ms']!,
          _deletedAtMsMeta,
        ),
      );
    }
    if (data.containsKey('revision')) {
      context.handle(
        _revisionMeta,
        revision.isAcceptableOrUnknown(data['revision']!, _revisionMeta),
      );
    }
    if (data.containsKey('origin_device_id')) {
      context.handle(
        _originDeviceIdMeta,
        originDeviceId.isAcceptableOrUnknown(
          data['origin_device_id']!,
          _originDeviceIdMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_originDeviceIdMeta);
    }
    if (data.containsKey('last_modified_by')) {
      context.handle(
        _lastModifiedByMeta,
        lastModifiedBy.isAcceptableOrUnknown(
          data['last_modified_by']!,
          _lastModifiedByMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_lastModifiedByMeta);
    }
    if (data.containsKey('sync_state')) {
      context.handle(
        _syncStateMeta,
        syncState.isAcceptableOrUnknown(data['sync_state']!, _syncStateMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  AccountRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return AccountRow(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      uuid: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}uuid'],
      )!,
      name: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}name'],
      )!,
      currencyCode: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}currency_code'],
      )!,
      currencyPrecision: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}currency_precision'],
      )!,
      isDefault: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_default'],
      )!,
      createdAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}created_at_ms'],
      )!,
      updatedAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}updated_at_ms'],
      )!,
      deletedAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}deleted_at_ms'],
      ),
      revision: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}revision'],
      )!,
      originDeviceId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}origin_device_id'],
      )!,
      lastModifiedBy: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_modified_by'],
      )!,
      syncState: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_state'],
      )!,
    );
  }

  @override
  $AccountsTable createAlias(String alias) {
    return $AccountsTable(attachedDatabase, alias);
  }
}

class AccountRow extends DataClass implements Insertable<AccountRow> {
  final int id;
  final String uuid;
  final String name;
  final String currencyCode;
  final int currencyPrecision;
  final bool isDefault;
  final int createdAtMs;
  final int updatedAtMs;
  final int? deletedAtMs;
  final int revision;
  final String originDeviceId;
  final String lastModifiedBy;
  final String syncState;
  const AccountRow({
    required this.id,
    required this.uuid,
    required this.name,
    required this.currencyCode,
    required this.currencyPrecision,
    required this.isDefault,
    required this.createdAtMs,
    required this.updatedAtMs,
    this.deletedAtMs,
    required this.revision,
    required this.originDeviceId,
    required this.lastModifiedBy,
    required this.syncState,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['uuid'] = Variable<String>(uuid);
    map['name'] = Variable<String>(name);
    map['currency_code'] = Variable<String>(currencyCode);
    map['currency_precision'] = Variable<int>(currencyPrecision);
    map['is_default'] = Variable<bool>(isDefault);
    map['created_at_ms'] = Variable<int>(createdAtMs);
    map['updated_at_ms'] = Variable<int>(updatedAtMs);
    if (!nullToAbsent || deletedAtMs != null) {
      map['deleted_at_ms'] = Variable<int>(deletedAtMs);
    }
    map['revision'] = Variable<int>(revision);
    map['origin_device_id'] = Variable<String>(originDeviceId);
    map['last_modified_by'] = Variable<String>(lastModifiedBy);
    map['sync_state'] = Variable<String>(syncState);
    return map;
  }

  AccountsCompanion toCompanion(bool nullToAbsent) {
    return AccountsCompanion(
      id: Value(id),
      uuid: Value(uuid),
      name: Value(name),
      currencyCode: Value(currencyCode),
      currencyPrecision: Value(currencyPrecision),
      isDefault: Value(isDefault),
      createdAtMs: Value(createdAtMs),
      updatedAtMs: Value(updatedAtMs),
      deletedAtMs: deletedAtMs == null && nullToAbsent
          ? const Value.absent()
          : Value(deletedAtMs),
      revision: Value(revision),
      originDeviceId: Value(originDeviceId),
      lastModifiedBy: Value(lastModifiedBy),
      syncState: Value(syncState),
    );
  }

  factory AccountRow.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return AccountRow(
      id: serializer.fromJson<int>(json['id']),
      uuid: serializer.fromJson<String>(json['uuid']),
      name: serializer.fromJson<String>(json['name']),
      currencyCode: serializer.fromJson<String>(json['currencyCode']),
      currencyPrecision: serializer.fromJson<int>(json['currencyPrecision']),
      isDefault: serializer.fromJson<bool>(json['isDefault']),
      createdAtMs: serializer.fromJson<int>(json['createdAtMs']),
      updatedAtMs: serializer.fromJson<int>(json['updatedAtMs']),
      deletedAtMs: serializer.fromJson<int?>(json['deletedAtMs']),
      revision: serializer.fromJson<int>(json['revision']),
      originDeviceId: serializer.fromJson<String>(json['originDeviceId']),
      lastModifiedBy: serializer.fromJson<String>(json['lastModifiedBy']),
      syncState: serializer.fromJson<String>(json['syncState']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'uuid': serializer.toJson<String>(uuid),
      'name': serializer.toJson<String>(name),
      'currencyCode': serializer.toJson<String>(currencyCode),
      'currencyPrecision': serializer.toJson<int>(currencyPrecision),
      'isDefault': serializer.toJson<bool>(isDefault),
      'createdAtMs': serializer.toJson<int>(createdAtMs),
      'updatedAtMs': serializer.toJson<int>(updatedAtMs),
      'deletedAtMs': serializer.toJson<int?>(deletedAtMs),
      'revision': serializer.toJson<int>(revision),
      'originDeviceId': serializer.toJson<String>(originDeviceId),
      'lastModifiedBy': serializer.toJson<String>(lastModifiedBy),
      'syncState': serializer.toJson<String>(syncState),
    };
  }

  AccountRow copyWith({
    int? id,
    String? uuid,
    String? name,
    String? currencyCode,
    int? currencyPrecision,
    bool? isDefault,
    int? createdAtMs,
    int? updatedAtMs,
    Value<int?> deletedAtMs = const Value.absent(),
    int? revision,
    String? originDeviceId,
    String? lastModifiedBy,
    String? syncState,
  }) => AccountRow(
    id: id ?? this.id,
    uuid: uuid ?? this.uuid,
    name: name ?? this.name,
    currencyCode: currencyCode ?? this.currencyCode,
    currencyPrecision: currencyPrecision ?? this.currencyPrecision,
    isDefault: isDefault ?? this.isDefault,
    createdAtMs: createdAtMs ?? this.createdAtMs,
    updatedAtMs: updatedAtMs ?? this.updatedAtMs,
    deletedAtMs: deletedAtMs.present ? deletedAtMs.value : this.deletedAtMs,
    revision: revision ?? this.revision,
    originDeviceId: originDeviceId ?? this.originDeviceId,
    lastModifiedBy: lastModifiedBy ?? this.lastModifiedBy,
    syncState: syncState ?? this.syncState,
  );
  AccountRow copyWithCompanion(AccountsCompanion data) {
    return AccountRow(
      id: data.id.present ? data.id.value : this.id,
      uuid: data.uuid.present ? data.uuid.value : this.uuid,
      name: data.name.present ? data.name.value : this.name,
      currencyCode: data.currencyCode.present
          ? data.currencyCode.value
          : this.currencyCode,
      currencyPrecision: data.currencyPrecision.present
          ? data.currencyPrecision.value
          : this.currencyPrecision,
      isDefault: data.isDefault.present ? data.isDefault.value : this.isDefault,
      createdAtMs: data.createdAtMs.present
          ? data.createdAtMs.value
          : this.createdAtMs,
      updatedAtMs: data.updatedAtMs.present
          ? data.updatedAtMs.value
          : this.updatedAtMs,
      deletedAtMs: data.deletedAtMs.present
          ? data.deletedAtMs.value
          : this.deletedAtMs,
      revision: data.revision.present ? data.revision.value : this.revision,
      originDeviceId: data.originDeviceId.present
          ? data.originDeviceId.value
          : this.originDeviceId,
      lastModifiedBy: data.lastModifiedBy.present
          ? data.lastModifiedBy.value
          : this.lastModifiedBy,
      syncState: data.syncState.present ? data.syncState.value : this.syncState,
    );
  }

  @override
  String toString() {
    return (StringBuffer('AccountRow(')
          ..write('id: $id, ')
          ..write('uuid: $uuid, ')
          ..write('name: $name, ')
          ..write('currencyCode: $currencyCode, ')
          ..write('currencyPrecision: $currencyPrecision, ')
          ..write('isDefault: $isDefault, ')
          ..write('createdAtMs: $createdAtMs, ')
          ..write('updatedAtMs: $updatedAtMs, ')
          ..write('deletedAtMs: $deletedAtMs, ')
          ..write('revision: $revision, ')
          ..write('originDeviceId: $originDeviceId, ')
          ..write('lastModifiedBy: $lastModifiedBy, ')
          ..write('syncState: $syncState')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    uuid,
    name,
    currencyCode,
    currencyPrecision,
    isDefault,
    createdAtMs,
    updatedAtMs,
    deletedAtMs,
    revision,
    originDeviceId,
    lastModifiedBy,
    syncState,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is AccountRow &&
          other.id == this.id &&
          other.uuid == this.uuid &&
          other.name == this.name &&
          other.currencyCode == this.currencyCode &&
          other.currencyPrecision == this.currencyPrecision &&
          other.isDefault == this.isDefault &&
          other.createdAtMs == this.createdAtMs &&
          other.updatedAtMs == this.updatedAtMs &&
          other.deletedAtMs == this.deletedAtMs &&
          other.revision == this.revision &&
          other.originDeviceId == this.originDeviceId &&
          other.lastModifiedBy == this.lastModifiedBy &&
          other.syncState == this.syncState);
}

class AccountsCompanion extends UpdateCompanion<AccountRow> {
  final Value<int> id;
  final Value<String> uuid;
  final Value<String> name;
  final Value<String> currencyCode;
  final Value<int> currencyPrecision;
  final Value<bool> isDefault;
  final Value<int> createdAtMs;
  final Value<int> updatedAtMs;
  final Value<int?> deletedAtMs;
  final Value<int> revision;
  final Value<String> originDeviceId;
  final Value<String> lastModifiedBy;
  final Value<String> syncState;
  const AccountsCompanion({
    this.id = const Value.absent(),
    this.uuid = const Value.absent(),
    this.name = const Value.absent(),
    this.currencyCode = const Value.absent(),
    this.currencyPrecision = const Value.absent(),
    this.isDefault = const Value.absent(),
    this.createdAtMs = const Value.absent(),
    this.updatedAtMs = const Value.absent(),
    this.deletedAtMs = const Value.absent(),
    this.revision = const Value.absent(),
    this.originDeviceId = const Value.absent(),
    this.lastModifiedBy = const Value.absent(),
    this.syncState = const Value.absent(),
  });
  AccountsCompanion.insert({
    this.id = const Value.absent(),
    required String uuid,
    required String name,
    required String currencyCode,
    required int currencyPrecision,
    this.isDefault = const Value.absent(),
    required int createdAtMs,
    required int updatedAtMs,
    this.deletedAtMs = const Value.absent(),
    this.revision = const Value.absent(),
    required String originDeviceId,
    required String lastModifiedBy,
    this.syncState = const Value.absent(),
  }) : uuid = Value(uuid),
       name = Value(name),
       currencyCode = Value(currencyCode),
       currencyPrecision = Value(currencyPrecision),
       createdAtMs = Value(createdAtMs),
       updatedAtMs = Value(updatedAtMs),
       originDeviceId = Value(originDeviceId),
       lastModifiedBy = Value(lastModifiedBy);
  static Insertable<AccountRow> custom({
    Expression<int>? id,
    Expression<String>? uuid,
    Expression<String>? name,
    Expression<String>? currencyCode,
    Expression<int>? currencyPrecision,
    Expression<bool>? isDefault,
    Expression<int>? createdAtMs,
    Expression<int>? updatedAtMs,
    Expression<int>? deletedAtMs,
    Expression<int>? revision,
    Expression<String>? originDeviceId,
    Expression<String>? lastModifiedBy,
    Expression<String>? syncState,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (uuid != null) 'uuid': uuid,
      if (name != null) 'name': name,
      if (currencyCode != null) 'currency_code': currencyCode,
      if (currencyPrecision != null) 'currency_precision': currencyPrecision,
      if (isDefault != null) 'is_default': isDefault,
      if (createdAtMs != null) 'created_at_ms': createdAtMs,
      if (updatedAtMs != null) 'updated_at_ms': updatedAtMs,
      if (deletedAtMs != null) 'deleted_at_ms': deletedAtMs,
      if (revision != null) 'revision': revision,
      if (originDeviceId != null) 'origin_device_id': originDeviceId,
      if (lastModifiedBy != null) 'last_modified_by': lastModifiedBy,
      if (syncState != null) 'sync_state': syncState,
    });
  }

  AccountsCompanion copyWith({
    Value<int>? id,
    Value<String>? uuid,
    Value<String>? name,
    Value<String>? currencyCode,
    Value<int>? currencyPrecision,
    Value<bool>? isDefault,
    Value<int>? createdAtMs,
    Value<int>? updatedAtMs,
    Value<int?>? deletedAtMs,
    Value<int>? revision,
    Value<String>? originDeviceId,
    Value<String>? lastModifiedBy,
    Value<String>? syncState,
  }) {
    return AccountsCompanion(
      id: id ?? this.id,
      uuid: uuid ?? this.uuid,
      name: name ?? this.name,
      currencyCode: currencyCode ?? this.currencyCode,
      currencyPrecision: currencyPrecision ?? this.currencyPrecision,
      isDefault: isDefault ?? this.isDefault,
      createdAtMs: createdAtMs ?? this.createdAtMs,
      updatedAtMs: updatedAtMs ?? this.updatedAtMs,
      deletedAtMs: deletedAtMs ?? this.deletedAtMs,
      revision: revision ?? this.revision,
      originDeviceId: originDeviceId ?? this.originDeviceId,
      lastModifiedBy: lastModifiedBy ?? this.lastModifiedBy,
      syncState: syncState ?? this.syncState,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (uuid.present) {
      map['uuid'] = Variable<String>(uuid.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (currencyCode.present) {
      map['currency_code'] = Variable<String>(currencyCode.value);
    }
    if (currencyPrecision.present) {
      map['currency_precision'] = Variable<int>(currencyPrecision.value);
    }
    if (isDefault.present) {
      map['is_default'] = Variable<bool>(isDefault.value);
    }
    if (createdAtMs.present) {
      map['created_at_ms'] = Variable<int>(createdAtMs.value);
    }
    if (updatedAtMs.present) {
      map['updated_at_ms'] = Variable<int>(updatedAtMs.value);
    }
    if (deletedAtMs.present) {
      map['deleted_at_ms'] = Variable<int>(deletedAtMs.value);
    }
    if (revision.present) {
      map['revision'] = Variable<int>(revision.value);
    }
    if (originDeviceId.present) {
      map['origin_device_id'] = Variable<String>(originDeviceId.value);
    }
    if (lastModifiedBy.present) {
      map['last_modified_by'] = Variable<String>(lastModifiedBy.value);
    }
    if (syncState.present) {
      map['sync_state'] = Variable<String>(syncState.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('AccountsCompanion(')
          ..write('id: $id, ')
          ..write('uuid: $uuid, ')
          ..write('name: $name, ')
          ..write('currencyCode: $currencyCode, ')
          ..write('currencyPrecision: $currencyPrecision, ')
          ..write('isDefault: $isDefault, ')
          ..write('createdAtMs: $createdAtMs, ')
          ..write('updatedAtMs: $updatedAtMs, ')
          ..write('deletedAtMs: $deletedAtMs, ')
          ..write('revision: $revision, ')
          ..write('originDeviceId: $originDeviceId, ')
          ..write('lastModifiedBy: $lastModifiedBy, ')
          ..write('syncState: $syncState')
          ..write(')'))
        .toString();
  }
}

class $TransactionsTable extends Transactions
    with TableInfo<$TransactionsTable, Transaction> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $TransactionsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _transactionTypeMeta = const VerificationMeta(
    'transactionType',
  );
  @override
  late final GeneratedColumn<String> transactionType = GeneratedColumn<String>(
    'transaction_type',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _amountMinorMeta = const VerificationMeta(
    'amountMinor',
  );
  @override
  late final GeneratedColumn<int> amountMinor = GeneratedColumn<int>(
    'amount_minor',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _categoryMeta = const VerificationMeta(
    'category',
  );
  @override
  late final GeneratedColumn<String> category = GeneratedColumn<String>(
    'category',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _descriptionMeta = const VerificationMeta(
    'description',
  );
  @override
  late final GeneratedColumn<String> description = GeneratedColumn<String>(
    'description',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _transactionDateMeta = const VerificationMeta(
    'transactionDate',
  );
  @override
  late final GeneratedColumn<String> transactionDate = GeneratedColumn<String>(
    'transaction_date',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _uuidMeta = const VerificationMeta('uuid');
  @override
  late final GeneratedColumn<String> uuid = GeneratedColumn<String>(
    'uuid',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways('UNIQUE'),
  );
  static const VerificationMeta _createdAtMsMeta = const VerificationMeta(
    'createdAtMs',
  );
  @override
  late final GeneratedColumn<int> createdAtMs = GeneratedColumn<int>(
    'created_at_ms',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMsMeta = const VerificationMeta(
    'updatedAtMs',
  );
  @override
  late final GeneratedColumn<int> updatedAtMs = GeneratedColumn<int>(
    'updated_at_ms',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _deletedAtMsMeta = const VerificationMeta(
    'deletedAtMs',
  );
  @override
  late final GeneratedColumn<int> deletedAtMs = GeneratedColumn<int>(
    'deleted_at_ms',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _revisionMeta = const VerificationMeta(
    'revision',
  );
  @override
  late final GeneratedColumn<int> revision = GeneratedColumn<int>(
    'revision',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(1),
  );
  static const VerificationMeta _originDeviceIdMeta = const VerificationMeta(
    'originDeviceId',
  );
  @override
  late final GeneratedColumn<String> originDeviceId = GeneratedColumn<String>(
    'origin_device_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _lastModifiedByMeta = const VerificationMeta(
    'lastModifiedBy',
  );
  @override
  late final GeneratedColumn<String> lastModifiedBy = GeneratedColumn<String>(
    'last_modified_by',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _syncStateMeta = const VerificationMeta(
    'syncState',
  );
  @override
  late final GeneratedColumn<String> syncState = GeneratedColumn<String>(
    'sync_state',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('pending'),
  );
  static const VerificationMeta _accountUuidMeta = const VerificationMeta(
    'accountUuid',
  );
  @override
  late final GeneratedColumn<String> accountUuid = GeneratedColumn<String>(
    'account_uuid',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _importHashMeta = const VerificationMeta(
    'importHash',
  );
  @override
  late final GeneratedColumn<String> importHash = GeneratedColumn<String>(
    'import_hash',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _externalRefMeta = const VerificationMeta(
    'externalRef',
  );
  @override
  late final GeneratedColumn<String> externalRef = GeneratedColumn<String>(
    'external_ref',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _importBatchIdMeta = const VerificationMeta(
    'importBatchId',
  );
  @override
  late final GeneratedColumn<String> importBatchId = GeneratedColumn<String>(
    'import_batch_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _accountLabelMeta = const VerificationMeta(
    'accountLabel',
  );
  @override
  late final GeneratedColumn<String> accountLabel = GeneratedColumn<String>(
    'account_label',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    transactionType,
    amountMinor,
    category,
    description,
    transactionDate,
    uuid,
    createdAtMs,
    updatedAtMs,
    deletedAtMs,
    revision,
    originDeviceId,
    lastModifiedBy,
    syncState,
    accountUuid,
    importHash,
    externalRef,
    importBatchId,
    accountLabel,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'transactions';
  @override
  VerificationContext validateIntegrity(
    Insertable<Transaction> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('transaction_type')) {
      context.handle(
        _transactionTypeMeta,
        transactionType.isAcceptableOrUnknown(
          data['transaction_type']!,
          _transactionTypeMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_transactionTypeMeta);
    }
    if (data.containsKey('amount_minor')) {
      context.handle(
        _amountMinorMeta,
        amountMinor.isAcceptableOrUnknown(
          data['amount_minor']!,
          _amountMinorMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_amountMinorMeta);
    }
    if (data.containsKey('category')) {
      context.handle(
        _categoryMeta,
        category.isAcceptableOrUnknown(data['category']!, _categoryMeta),
      );
    } else if (isInserting) {
      context.missing(_categoryMeta);
    }
    if (data.containsKey('description')) {
      context.handle(
        _descriptionMeta,
        description.isAcceptableOrUnknown(
          data['description']!,
          _descriptionMeta,
        ),
      );
    }
    if (data.containsKey('transaction_date')) {
      context.handle(
        _transactionDateMeta,
        transactionDate.isAcceptableOrUnknown(
          data['transaction_date']!,
          _transactionDateMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_transactionDateMeta);
    }
    if (data.containsKey('uuid')) {
      context.handle(
        _uuidMeta,
        uuid.isAcceptableOrUnknown(data['uuid']!, _uuidMeta),
      );
    } else if (isInserting) {
      context.missing(_uuidMeta);
    }
    if (data.containsKey('created_at_ms')) {
      context.handle(
        _createdAtMsMeta,
        createdAtMs.isAcceptableOrUnknown(
          data['created_at_ms']!,
          _createdAtMsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_createdAtMsMeta);
    }
    if (data.containsKey('updated_at_ms')) {
      context.handle(
        _updatedAtMsMeta,
        updatedAtMs.isAcceptableOrUnknown(
          data['updated_at_ms']!,
          _updatedAtMsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMsMeta);
    }
    if (data.containsKey('deleted_at_ms')) {
      context.handle(
        _deletedAtMsMeta,
        deletedAtMs.isAcceptableOrUnknown(
          data['deleted_at_ms']!,
          _deletedAtMsMeta,
        ),
      );
    }
    if (data.containsKey('revision')) {
      context.handle(
        _revisionMeta,
        revision.isAcceptableOrUnknown(data['revision']!, _revisionMeta),
      );
    }
    if (data.containsKey('origin_device_id')) {
      context.handle(
        _originDeviceIdMeta,
        originDeviceId.isAcceptableOrUnknown(
          data['origin_device_id']!,
          _originDeviceIdMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_originDeviceIdMeta);
    }
    if (data.containsKey('last_modified_by')) {
      context.handle(
        _lastModifiedByMeta,
        lastModifiedBy.isAcceptableOrUnknown(
          data['last_modified_by']!,
          _lastModifiedByMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_lastModifiedByMeta);
    }
    if (data.containsKey('sync_state')) {
      context.handle(
        _syncStateMeta,
        syncState.isAcceptableOrUnknown(data['sync_state']!, _syncStateMeta),
      );
    }
    if (data.containsKey('account_uuid')) {
      context.handle(
        _accountUuidMeta,
        accountUuid.isAcceptableOrUnknown(
          data['account_uuid']!,
          _accountUuidMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_accountUuidMeta);
    }
    if (data.containsKey('import_hash')) {
      context.handle(
        _importHashMeta,
        importHash.isAcceptableOrUnknown(data['import_hash']!, _importHashMeta),
      );
    }
    if (data.containsKey('external_ref')) {
      context.handle(
        _externalRefMeta,
        externalRef.isAcceptableOrUnknown(
          data['external_ref']!,
          _externalRefMeta,
        ),
      );
    }
    if (data.containsKey('import_batch_id')) {
      context.handle(
        _importBatchIdMeta,
        importBatchId.isAcceptableOrUnknown(
          data['import_batch_id']!,
          _importBatchIdMeta,
        ),
      );
    }
    if (data.containsKey('account_label')) {
      context.handle(
        _accountLabelMeta,
        accountLabel.isAcceptableOrUnknown(
          data['account_label']!,
          _accountLabelMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Transaction map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Transaction(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      transactionType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}transaction_type'],
      )!,
      amountMinor: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}amount_minor'],
      )!,
      category: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}category'],
      )!,
      description: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}description'],
      ),
      transactionDate: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}transaction_date'],
      )!,
      uuid: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}uuid'],
      )!,
      createdAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}created_at_ms'],
      )!,
      updatedAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}updated_at_ms'],
      )!,
      deletedAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}deleted_at_ms'],
      ),
      revision: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}revision'],
      )!,
      originDeviceId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}origin_device_id'],
      )!,
      lastModifiedBy: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_modified_by'],
      )!,
      syncState: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_state'],
      )!,
      accountUuid: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}account_uuid'],
      )!,
      importHash: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}import_hash'],
      ),
      externalRef: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}external_ref'],
      ),
      importBatchId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}import_batch_id'],
      ),
      accountLabel: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}account_label'],
      ),
    );
  }

  @override
  $TransactionsTable createAlias(String alias) {
    return $TransactionsTable(attachedDatabase, alias);
  }
}

class Transaction extends DataClass implements Insertable<Transaction> {
  final int id;
  final String transactionType;
  final int amountMinor;
  final String category;
  final String? description;
  final String transactionDate;
  final String uuid;
  final int createdAtMs;
  final int updatedAtMs;
  final int? deletedAtMs;
  final int revision;
  final String originDeviceId;
  final String lastModifiedBy;
  final String syncState;
  final String accountUuid;
  final String? importHash;
  final String? externalRef;
  final String? importBatchId;
  final String? accountLabel;
  const Transaction({
    required this.id,
    required this.transactionType,
    required this.amountMinor,
    required this.category,
    this.description,
    required this.transactionDate,
    required this.uuid,
    required this.createdAtMs,
    required this.updatedAtMs,
    this.deletedAtMs,
    required this.revision,
    required this.originDeviceId,
    required this.lastModifiedBy,
    required this.syncState,
    required this.accountUuid,
    this.importHash,
    this.externalRef,
    this.importBatchId,
    this.accountLabel,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['transaction_type'] = Variable<String>(transactionType);
    map['amount_minor'] = Variable<int>(amountMinor);
    map['category'] = Variable<String>(category);
    if (!nullToAbsent || description != null) {
      map['description'] = Variable<String>(description);
    }
    map['transaction_date'] = Variable<String>(transactionDate);
    map['uuid'] = Variable<String>(uuid);
    map['created_at_ms'] = Variable<int>(createdAtMs);
    map['updated_at_ms'] = Variable<int>(updatedAtMs);
    if (!nullToAbsent || deletedAtMs != null) {
      map['deleted_at_ms'] = Variable<int>(deletedAtMs);
    }
    map['revision'] = Variable<int>(revision);
    map['origin_device_id'] = Variable<String>(originDeviceId);
    map['last_modified_by'] = Variable<String>(lastModifiedBy);
    map['sync_state'] = Variable<String>(syncState);
    map['account_uuid'] = Variable<String>(accountUuid);
    if (!nullToAbsent || importHash != null) {
      map['import_hash'] = Variable<String>(importHash);
    }
    if (!nullToAbsent || externalRef != null) {
      map['external_ref'] = Variable<String>(externalRef);
    }
    if (!nullToAbsent || importBatchId != null) {
      map['import_batch_id'] = Variable<String>(importBatchId);
    }
    if (!nullToAbsent || accountLabel != null) {
      map['account_label'] = Variable<String>(accountLabel);
    }
    return map;
  }

  TransactionsCompanion toCompanion(bool nullToAbsent) {
    return TransactionsCompanion(
      id: Value(id),
      transactionType: Value(transactionType),
      amountMinor: Value(amountMinor),
      category: Value(category),
      description: description == null && nullToAbsent
          ? const Value.absent()
          : Value(description),
      transactionDate: Value(transactionDate),
      uuid: Value(uuid),
      createdAtMs: Value(createdAtMs),
      updatedAtMs: Value(updatedAtMs),
      deletedAtMs: deletedAtMs == null && nullToAbsent
          ? const Value.absent()
          : Value(deletedAtMs),
      revision: Value(revision),
      originDeviceId: Value(originDeviceId),
      lastModifiedBy: Value(lastModifiedBy),
      syncState: Value(syncState),
      accountUuid: Value(accountUuid),
      importHash: importHash == null && nullToAbsent
          ? const Value.absent()
          : Value(importHash),
      externalRef: externalRef == null && nullToAbsent
          ? const Value.absent()
          : Value(externalRef),
      importBatchId: importBatchId == null && nullToAbsent
          ? const Value.absent()
          : Value(importBatchId),
      accountLabel: accountLabel == null && nullToAbsent
          ? const Value.absent()
          : Value(accountLabel),
    );
  }

  factory Transaction.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Transaction(
      id: serializer.fromJson<int>(json['id']),
      transactionType: serializer.fromJson<String>(json['transactionType']),
      amountMinor: serializer.fromJson<int>(json['amountMinor']),
      category: serializer.fromJson<String>(json['category']),
      description: serializer.fromJson<String?>(json['description']),
      transactionDate: serializer.fromJson<String>(json['transactionDate']),
      uuid: serializer.fromJson<String>(json['uuid']),
      createdAtMs: serializer.fromJson<int>(json['createdAtMs']),
      updatedAtMs: serializer.fromJson<int>(json['updatedAtMs']),
      deletedAtMs: serializer.fromJson<int?>(json['deletedAtMs']),
      revision: serializer.fromJson<int>(json['revision']),
      originDeviceId: serializer.fromJson<String>(json['originDeviceId']),
      lastModifiedBy: serializer.fromJson<String>(json['lastModifiedBy']),
      syncState: serializer.fromJson<String>(json['syncState']),
      accountUuid: serializer.fromJson<String>(json['accountUuid']),
      importHash: serializer.fromJson<String?>(json['importHash']),
      externalRef: serializer.fromJson<String?>(json['externalRef']),
      importBatchId: serializer.fromJson<String?>(json['importBatchId']),
      accountLabel: serializer.fromJson<String?>(json['accountLabel']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'transactionType': serializer.toJson<String>(transactionType),
      'amountMinor': serializer.toJson<int>(amountMinor),
      'category': serializer.toJson<String>(category),
      'description': serializer.toJson<String?>(description),
      'transactionDate': serializer.toJson<String>(transactionDate),
      'uuid': serializer.toJson<String>(uuid),
      'createdAtMs': serializer.toJson<int>(createdAtMs),
      'updatedAtMs': serializer.toJson<int>(updatedAtMs),
      'deletedAtMs': serializer.toJson<int?>(deletedAtMs),
      'revision': serializer.toJson<int>(revision),
      'originDeviceId': serializer.toJson<String>(originDeviceId),
      'lastModifiedBy': serializer.toJson<String>(lastModifiedBy),
      'syncState': serializer.toJson<String>(syncState),
      'accountUuid': serializer.toJson<String>(accountUuid),
      'importHash': serializer.toJson<String?>(importHash),
      'externalRef': serializer.toJson<String?>(externalRef),
      'importBatchId': serializer.toJson<String?>(importBatchId),
      'accountLabel': serializer.toJson<String?>(accountLabel),
    };
  }

  Transaction copyWith({
    int? id,
    String? transactionType,
    int? amountMinor,
    String? category,
    Value<String?> description = const Value.absent(),
    String? transactionDate,
    String? uuid,
    int? createdAtMs,
    int? updatedAtMs,
    Value<int?> deletedAtMs = const Value.absent(),
    int? revision,
    String? originDeviceId,
    String? lastModifiedBy,
    String? syncState,
    String? accountUuid,
    Value<String?> importHash = const Value.absent(),
    Value<String?> externalRef = const Value.absent(),
    Value<String?> importBatchId = const Value.absent(),
    Value<String?> accountLabel = const Value.absent(),
  }) => Transaction(
    id: id ?? this.id,
    transactionType: transactionType ?? this.transactionType,
    amountMinor: amountMinor ?? this.amountMinor,
    category: category ?? this.category,
    description: description.present ? description.value : this.description,
    transactionDate: transactionDate ?? this.transactionDate,
    uuid: uuid ?? this.uuid,
    createdAtMs: createdAtMs ?? this.createdAtMs,
    updatedAtMs: updatedAtMs ?? this.updatedAtMs,
    deletedAtMs: deletedAtMs.present ? deletedAtMs.value : this.deletedAtMs,
    revision: revision ?? this.revision,
    originDeviceId: originDeviceId ?? this.originDeviceId,
    lastModifiedBy: lastModifiedBy ?? this.lastModifiedBy,
    syncState: syncState ?? this.syncState,
    accountUuid: accountUuid ?? this.accountUuid,
    importHash: importHash.present ? importHash.value : this.importHash,
    externalRef: externalRef.present ? externalRef.value : this.externalRef,
    importBatchId: importBatchId.present
        ? importBatchId.value
        : this.importBatchId,
    accountLabel: accountLabel.present ? accountLabel.value : this.accountLabel,
  );
  Transaction copyWithCompanion(TransactionsCompanion data) {
    return Transaction(
      id: data.id.present ? data.id.value : this.id,
      transactionType: data.transactionType.present
          ? data.transactionType.value
          : this.transactionType,
      amountMinor: data.amountMinor.present
          ? data.amountMinor.value
          : this.amountMinor,
      category: data.category.present ? data.category.value : this.category,
      description: data.description.present
          ? data.description.value
          : this.description,
      transactionDate: data.transactionDate.present
          ? data.transactionDate.value
          : this.transactionDate,
      uuid: data.uuid.present ? data.uuid.value : this.uuid,
      createdAtMs: data.createdAtMs.present
          ? data.createdAtMs.value
          : this.createdAtMs,
      updatedAtMs: data.updatedAtMs.present
          ? data.updatedAtMs.value
          : this.updatedAtMs,
      deletedAtMs: data.deletedAtMs.present
          ? data.deletedAtMs.value
          : this.deletedAtMs,
      revision: data.revision.present ? data.revision.value : this.revision,
      originDeviceId: data.originDeviceId.present
          ? data.originDeviceId.value
          : this.originDeviceId,
      lastModifiedBy: data.lastModifiedBy.present
          ? data.lastModifiedBy.value
          : this.lastModifiedBy,
      syncState: data.syncState.present ? data.syncState.value : this.syncState,
      accountUuid: data.accountUuid.present
          ? data.accountUuid.value
          : this.accountUuid,
      importHash: data.importHash.present
          ? data.importHash.value
          : this.importHash,
      externalRef: data.externalRef.present
          ? data.externalRef.value
          : this.externalRef,
      importBatchId: data.importBatchId.present
          ? data.importBatchId.value
          : this.importBatchId,
      accountLabel: data.accountLabel.present
          ? data.accountLabel.value
          : this.accountLabel,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Transaction(')
          ..write('id: $id, ')
          ..write('transactionType: $transactionType, ')
          ..write('amountMinor: $amountMinor, ')
          ..write('category: $category, ')
          ..write('description: $description, ')
          ..write('transactionDate: $transactionDate, ')
          ..write('uuid: $uuid, ')
          ..write('createdAtMs: $createdAtMs, ')
          ..write('updatedAtMs: $updatedAtMs, ')
          ..write('deletedAtMs: $deletedAtMs, ')
          ..write('revision: $revision, ')
          ..write('originDeviceId: $originDeviceId, ')
          ..write('lastModifiedBy: $lastModifiedBy, ')
          ..write('syncState: $syncState, ')
          ..write('accountUuid: $accountUuid, ')
          ..write('importHash: $importHash, ')
          ..write('externalRef: $externalRef, ')
          ..write('importBatchId: $importBatchId, ')
          ..write('accountLabel: $accountLabel')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    transactionType,
    amountMinor,
    category,
    description,
    transactionDate,
    uuid,
    createdAtMs,
    updatedAtMs,
    deletedAtMs,
    revision,
    originDeviceId,
    lastModifiedBy,
    syncState,
    accountUuid,
    importHash,
    externalRef,
    importBatchId,
    accountLabel,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Transaction &&
          other.id == this.id &&
          other.transactionType == this.transactionType &&
          other.amountMinor == this.amountMinor &&
          other.category == this.category &&
          other.description == this.description &&
          other.transactionDate == this.transactionDate &&
          other.uuid == this.uuid &&
          other.createdAtMs == this.createdAtMs &&
          other.updatedAtMs == this.updatedAtMs &&
          other.deletedAtMs == this.deletedAtMs &&
          other.revision == this.revision &&
          other.originDeviceId == this.originDeviceId &&
          other.lastModifiedBy == this.lastModifiedBy &&
          other.syncState == this.syncState &&
          other.accountUuid == this.accountUuid &&
          other.importHash == this.importHash &&
          other.externalRef == this.externalRef &&
          other.importBatchId == this.importBatchId &&
          other.accountLabel == this.accountLabel);
}

class TransactionsCompanion extends UpdateCompanion<Transaction> {
  final Value<int> id;
  final Value<String> transactionType;
  final Value<int> amountMinor;
  final Value<String> category;
  final Value<String?> description;
  final Value<String> transactionDate;
  final Value<String> uuid;
  final Value<int> createdAtMs;
  final Value<int> updatedAtMs;
  final Value<int?> deletedAtMs;
  final Value<int> revision;
  final Value<String> originDeviceId;
  final Value<String> lastModifiedBy;
  final Value<String> syncState;
  final Value<String> accountUuid;
  final Value<String?> importHash;
  final Value<String?> externalRef;
  final Value<String?> importBatchId;
  final Value<String?> accountLabel;
  const TransactionsCompanion({
    this.id = const Value.absent(),
    this.transactionType = const Value.absent(),
    this.amountMinor = const Value.absent(),
    this.category = const Value.absent(),
    this.description = const Value.absent(),
    this.transactionDate = const Value.absent(),
    this.uuid = const Value.absent(),
    this.createdAtMs = const Value.absent(),
    this.updatedAtMs = const Value.absent(),
    this.deletedAtMs = const Value.absent(),
    this.revision = const Value.absent(),
    this.originDeviceId = const Value.absent(),
    this.lastModifiedBy = const Value.absent(),
    this.syncState = const Value.absent(),
    this.accountUuid = const Value.absent(),
    this.importHash = const Value.absent(),
    this.externalRef = const Value.absent(),
    this.importBatchId = const Value.absent(),
    this.accountLabel = const Value.absent(),
  });
  TransactionsCompanion.insert({
    this.id = const Value.absent(),
    required String transactionType,
    required int amountMinor,
    required String category,
    this.description = const Value.absent(),
    required String transactionDate,
    required String uuid,
    required int createdAtMs,
    required int updatedAtMs,
    this.deletedAtMs = const Value.absent(),
    this.revision = const Value.absent(),
    required String originDeviceId,
    required String lastModifiedBy,
    this.syncState = const Value.absent(),
    required String accountUuid,
    this.importHash = const Value.absent(),
    this.externalRef = const Value.absent(),
    this.importBatchId = const Value.absent(),
    this.accountLabel = const Value.absent(),
  }) : transactionType = Value(transactionType),
       amountMinor = Value(amountMinor),
       category = Value(category),
       transactionDate = Value(transactionDate),
       uuid = Value(uuid),
       createdAtMs = Value(createdAtMs),
       updatedAtMs = Value(updatedAtMs),
       originDeviceId = Value(originDeviceId),
       lastModifiedBy = Value(lastModifiedBy),
       accountUuid = Value(accountUuid);
  static Insertable<Transaction> custom({
    Expression<int>? id,
    Expression<String>? transactionType,
    Expression<int>? amountMinor,
    Expression<String>? category,
    Expression<String>? description,
    Expression<String>? transactionDate,
    Expression<String>? uuid,
    Expression<int>? createdAtMs,
    Expression<int>? updatedAtMs,
    Expression<int>? deletedAtMs,
    Expression<int>? revision,
    Expression<String>? originDeviceId,
    Expression<String>? lastModifiedBy,
    Expression<String>? syncState,
    Expression<String>? accountUuid,
    Expression<String>? importHash,
    Expression<String>? externalRef,
    Expression<String>? importBatchId,
    Expression<String>? accountLabel,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (transactionType != null) 'transaction_type': transactionType,
      if (amountMinor != null) 'amount_minor': amountMinor,
      if (category != null) 'category': category,
      if (description != null) 'description': description,
      if (transactionDate != null) 'transaction_date': transactionDate,
      if (uuid != null) 'uuid': uuid,
      if (createdAtMs != null) 'created_at_ms': createdAtMs,
      if (updatedAtMs != null) 'updated_at_ms': updatedAtMs,
      if (deletedAtMs != null) 'deleted_at_ms': deletedAtMs,
      if (revision != null) 'revision': revision,
      if (originDeviceId != null) 'origin_device_id': originDeviceId,
      if (lastModifiedBy != null) 'last_modified_by': lastModifiedBy,
      if (syncState != null) 'sync_state': syncState,
      if (accountUuid != null) 'account_uuid': accountUuid,
      if (importHash != null) 'import_hash': importHash,
      if (externalRef != null) 'external_ref': externalRef,
      if (importBatchId != null) 'import_batch_id': importBatchId,
      if (accountLabel != null) 'account_label': accountLabel,
    });
  }

  TransactionsCompanion copyWith({
    Value<int>? id,
    Value<String>? transactionType,
    Value<int>? amountMinor,
    Value<String>? category,
    Value<String?>? description,
    Value<String>? transactionDate,
    Value<String>? uuid,
    Value<int>? createdAtMs,
    Value<int>? updatedAtMs,
    Value<int?>? deletedAtMs,
    Value<int>? revision,
    Value<String>? originDeviceId,
    Value<String>? lastModifiedBy,
    Value<String>? syncState,
    Value<String>? accountUuid,
    Value<String?>? importHash,
    Value<String?>? externalRef,
    Value<String?>? importBatchId,
    Value<String?>? accountLabel,
  }) {
    return TransactionsCompanion(
      id: id ?? this.id,
      transactionType: transactionType ?? this.transactionType,
      amountMinor: amountMinor ?? this.amountMinor,
      category: category ?? this.category,
      description: description ?? this.description,
      transactionDate: transactionDate ?? this.transactionDate,
      uuid: uuid ?? this.uuid,
      createdAtMs: createdAtMs ?? this.createdAtMs,
      updatedAtMs: updatedAtMs ?? this.updatedAtMs,
      deletedAtMs: deletedAtMs ?? this.deletedAtMs,
      revision: revision ?? this.revision,
      originDeviceId: originDeviceId ?? this.originDeviceId,
      lastModifiedBy: lastModifiedBy ?? this.lastModifiedBy,
      syncState: syncState ?? this.syncState,
      accountUuid: accountUuid ?? this.accountUuid,
      importHash: importHash ?? this.importHash,
      externalRef: externalRef ?? this.externalRef,
      importBatchId: importBatchId ?? this.importBatchId,
      accountLabel: accountLabel ?? this.accountLabel,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (transactionType.present) {
      map['transaction_type'] = Variable<String>(transactionType.value);
    }
    if (amountMinor.present) {
      map['amount_minor'] = Variable<int>(amountMinor.value);
    }
    if (category.present) {
      map['category'] = Variable<String>(category.value);
    }
    if (description.present) {
      map['description'] = Variable<String>(description.value);
    }
    if (transactionDate.present) {
      map['transaction_date'] = Variable<String>(transactionDate.value);
    }
    if (uuid.present) {
      map['uuid'] = Variable<String>(uuid.value);
    }
    if (createdAtMs.present) {
      map['created_at_ms'] = Variable<int>(createdAtMs.value);
    }
    if (updatedAtMs.present) {
      map['updated_at_ms'] = Variable<int>(updatedAtMs.value);
    }
    if (deletedAtMs.present) {
      map['deleted_at_ms'] = Variable<int>(deletedAtMs.value);
    }
    if (revision.present) {
      map['revision'] = Variable<int>(revision.value);
    }
    if (originDeviceId.present) {
      map['origin_device_id'] = Variable<String>(originDeviceId.value);
    }
    if (lastModifiedBy.present) {
      map['last_modified_by'] = Variable<String>(lastModifiedBy.value);
    }
    if (syncState.present) {
      map['sync_state'] = Variable<String>(syncState.value);
    }
    if (accountUuid.present) {
      map['account_uuid'] = Variable<String>(accountUuid.value);
    }
    if (importHash.present) {
      map['import_hash'] = Variable<String>(importHash.value);
    }
    if (externalRef.present) {
      map['external_ref'] = Variable<String>(externalRef.value);
    }
    if (importBatchId.present) {
      map['import_batch_id'] = Variable<String>(importBatchId.value);
    }
    if (accountLabel.present) {
      map['account_label'] = Variable<String>(accountLabel.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('TransactionsCompanion(')
          ..write('id: $id, ')
          ..write('transactionType: $transactionType, ')
          ..write('amountMinor: $amountMinor, ')
          ..write('category: $category, ')
          ..write('description: $description, ')
          ..write('transactionDate: $transactionDate, ')
          ..write('uuid: $uuid, ')
          ..write('createdAtMs: $createdAtMs, ')
          ..write('updatedAtMs: $updatedAtMs, ')
          ..write('deletedAtMs: $deletedAtMs, ')
          ..write('revision: $revision, ')
          ..write('originDeviceId: $originDeviceId, ')
          ..write('lastModifiedBy: $lastModifiedBy, ')
          ..write('syncState: $syncState, ')
          ..write('accountUuid: $accountUuid, ')
          ..write('importHash: $importHash, ')
          ..write('externalRef: $externalRef, ')
          ..write('importBatchId: $importBatchId, ')
          ..write('accountLabel: $accountLabel')
          ..write(')'))
        .toString();
  }
}

class $SyncChangesTable extends SyncChanges
    with TableInfo<$SyncChangesTable, SyncChange> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncChangesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _seqMeta = const VerificationMeta('seq');
  @override
  late final GeneratedColumn<int> seq = GeneratedColumn<int>(
    'seq',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _entityTypeMeta = const VerificationMeta(
    'entityType',
  );
  @override
  late final GeneratedColumn<String> entityType = GeneratedColumn<String>(
    'entity_type',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _entityUuidMeta = const VerificationMeta(
    'entityUuid',
  );
  @override
  late final GeneratedColumn<String> entityUuid = GeneratedColumn<String>(
    'entity_uuid',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _operationMeta = const VerificationMeta(
    'operation',
  );
  @override
  late final GeneratedColumn<String> operation = GeneratedColumn<String>(
    'operation',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _baseRevisionMeta = const VerificationMeta(
    'baseRevision',
  );
  @override
  late final GeneratedColumn<int> baseRevision = GeneratedColumn<int>(
    'base_revision',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _newRevisionMeta = const VerificationMeta(
    'newRevision',
  );
  @override
  late final GeneratedColumn<int> newRevision = GeneratedColumn<int>(
    'new_revision',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _payloadMeta = const VerificationMeta(
    'payload',
  );
  @override
  late final GeneratedColumn<String> payload = GeneratedColumn<String>(
    'payload',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _originDeviceIdMeta = const VerificationMeta(
    'originDeviceId',
  );
  @override
  late final GeneratedColumn<String> originDeviceId = GeneratedColumn<String>(
    'origin_device_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _recordedAtMsMeta = const VerificationMeta(
    'recordedAtMs',
  );
  @override
  late final GeneratedColumn<int> recordedAtMs = GeneratedColumn<int>(
    'recorded_at_ms',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _payloadVersionMeta = const VerificationMeta(
    'payloadVersion',
  );
  @override
  late final GeneratedColumn<int> payloadVersion = GeneratedColumn<int>(
    'payload_version',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(1),
  );
  @override
  List<GeneratedColumn> get $columns => [
    seq,
    entityType,
    entityUuid,
    operation,
    baseRevision,
    newRevision,
    payload,
    originDeviceId,
    recordedAtMs,
    payloadVersion,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sync_changes';
  @override
  VerificationContext validateIntegrity(
    Insertable<SyncChange> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('seq')) {
      context.handle(
        _seqMeta,
        seq.isAcceptableOrUnknown(data['seq']!, _seqMeta),
      );
    }
    if (data.containsKey('entity_type')) {
      context.handle(
        _entityTypeMeta,
        entityType.isAcceptableOrUnknown(data['entity_type']!, _entityTypeMeta),
      );
    } else if (isInserting) {
      context.missing(_entityTypeMeta);
    }
    if (data.containsKey('entity_uuid')) {
      context.handle(
        _entityUuidMeta,
        entityUuid.isAcceptableOrUnknown(data['entity_uuid']!, _entityUuidMeta),
      );
    } else if (isInserting) {
      context.missing(_entityUuidMeta);
    }
    if (data.containsKey('operation')) {
      context.handle(
        _operationMeta,
        operation.isAcceptableOrUnknown(data['operation']!, _operationMeta),
      );
    } else if (isInserting) {
      context.missing(_operationMeta);
    }
    if (data.containsKey('base_revision')) {
      context.handle(
        _baseRevisionMeta,
        baseRevision.isAcceptableOrUnknown(
          data['base_revision']!,
          _baseRevisionMeta,
        ),
      );
    }
    if (data.containsKey('new_revision')) {
      context.handle(
        _newRevisionMeta,
        newRevision.isAcceptableOrUnknown(
          data['new_revision']!,
          _newRevisionMeta,
        ),
      );
    }
    if (data.containsKey('payload')) {
      context.handle(
        _payloadMeta,
        payload.isAcceptableOrUnknown(data['payload']!, _payloadMeta),
      );
    } else if (isInserting) {
      context.missing(_payloadMeta);
    }
    if (data.containsKey('origin_device_id')) {
      context.handle(
        _originDeviceIdMeta,
        originDeviceId.isAcceptableOrUnknown(
          data['origin_device_id']!,
          _originDeviceIdMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_originDeviceIdMeta);
    }
    if (data.containsKey('recorded_at_ms')) {
      context.handle(
        _recordedAtMsMeta,
        recordedAtMs.isAcceptableOrUnknown(
          data['recorded_at_ms']!,
          _recordedAtMsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_recordedAtMsMeta);
    }
    if (data.containsKey('payload_version')) {
      context.handle(
        _payloadVersionMeta,
        payloadVersion.isAcceptableOrUnknown(
          data['payload_version']!,
          _payloadVersionMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {seq};
  @override
  SyncChange map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SyncChange(
      seq: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}seq'],
      )!,
      entityType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}entity_type'],
      )!,
      entityUuid: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}entity_uuid'],
      )!,
      operation: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}operation'],
      )!,
      baseRevision: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}base_revision'],
      ),
      newRevision: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}new_revision'],
      ),
      payload: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}payload'],
      )!,
      originDeviceId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}origin_device_id'],
      )!,
      recordedAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}recorded_at_ms'],
      )!,
      payloadVersion: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}payload_version'],
      )!,
    );
  }

  @override
  $SyncChangesTable createAlias(String alias) {
    return $SyncChangesTable(attachedDatabase, alias);
  }
}

class SyncChange extends DataClass implements Insertable<SyncChange> {
  final int seq;
  final String entityType;
  final String entityUuid;
  final String operation;
  final int? baseRevision;
  final int? newRevision;
  final String payload;
  final String originDeviceId;
  final int recordedAtMs;
  final int payloadVersion;
  const SyncChange({
    required this.seq,
    required this.entityType,
    required this.entityUuid,
    required this.operation,
    this.baseRevision,
    this.newRevision,
    required this.payload,
    required this.originDeviceId,
    required this.recordedAtMs,
    required this.payloadVersion,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['seq'] = Variable<int>(seq);
    map['entity_type'] = Variable<String>(entityType);
    map['entity_uuid'] = Variable<String>(entityUuid);
    map['operation'] = Variable<String>(operation);
    if (!nullToAbsent || baseRevision != null) {
      map['base_revision'] = Variable<int>(baseRevision);
    }
    if (!nullToAbsent || newRevision != null) {
      map['new_revision'] = Variable<int>(newRevision);
    }
    map['payload'] = Variable<String>(payload);
    map['origin_device_id'] = Variable<String>(originDeviceId);
    map['recorded_at_ms'] = Variable<int>(recordedAtMs);
    map['payload_version'] = Variable<int>(payloadVersion);
    return map;
  }

  SyncChangesCompanion toCompanion(bool nullToAbsent) {
    return SyncChangesCompanion(
      seq: Value(seq),
      entityType: Value(entityType),
      entityUuid: Value(entityUuid),
      operation: Value(operation),
      baseRevision: baseRevision == null && nullToAbsent
          ? const Value.absent()
          : Value(baseRevision),
      newRevision: newRevision == null && nullToAbsent
          ? const Value.absent()
          : Value(newRevision),
      payload: Value(payload),
      originDeviceId: Value(originDeviceId),
      recordedAtMs: Value(recordedAtMs),
      payloadVersion: Value(payloadVersion),
    );
  }

  factory SyncChange.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SyncChange(
      seq: serializer.fromJson<int>(json['seq']),
      entityType: serializer.fromJson<String>(json['entityType']),
      entityUuid: serializer.fromJson<String>(json['entityUuid']),
      operation: serializer.fromJson<String>(json['operation']),
      baseRevision: serializer.fromJson<int?>(json['baseRevision']),
      newRevision: serializer.fromJson<int?>(json['newRevision']),
      payload: serializer.fromJson<String>(json['payload']),
      originDeviceId: serializer.fromJson<String>(json['originDeviceId']),
      recordedAtMs: serializer.fromJson<int>(json['recordedAtMs']),
      payloadVersion: serializer.fromJson<int>(json['payloadVersion']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'seq': serializer.toJson<int>(seq),
      'entityType': serializer.toJson<String>(entityType),
      'entityUuid': serializer.toJson<String>(entityUuid),
      'operation': serializer.toJson<String>(operation),
      'baseRevision': serializer.toJson<int?>(baseRevision),
      'newRevision': serializer.toJson<int?>(newRevision),
      'payload': serializer.toJson<String>(payload),
      'originDeviceId': serializer.toJson<String>(originDeviceId),
      'recordedAtMs': serializer.toJson<int>(recordedAtMs),
      'payloadVersion': serializer.toJson<int>(payloadVersion),
    };
  }

  SyncChange copyWith({
    int? seq,
    String? entityType,
    String? entityUuid,
    String? operation,
    Value<int?> baseRevision = const Value.absent(),
    Value<int?> newRevision = const Value.absent(),
    String? payload,
    String? originDeviceId,
    int? recordedAtMs,
    int? payloadVersion,
  }) => SyncChange(
    seq: seq ?? this.seq,
    entityType: entityType ?? this.entityType,
    entityUuid: entityUuid ?? this.entityUuid,
    operation: operation ?? this.operation,
    baseRevision: baseRevision.present ? baseRevision.value : this.baseRevision,
    newRevision: newRevision.present ? newRevision.value : this.newRevision,
    payload: payload ?? this.payload,
    originDeviceId: originDeviceId ?? this.originDeviceId,
    recordedAtMs: recordedAtMs ?? this.recordedAtMs,
    payloadVersion: payloadVersion ?? this.payloadVersion,
  );
  SyncChange copyWithCompanion(SyncChangesCompanion data) {
    return SyncChange(
      seq: data.seq.present ? data.seq.value : this.seq,
      entityType: data.entityType.present
          ? data.entityType.value
          : this.entityType,
      entityUuid: data.entityUuid.present
          ? data.entityUuid.value
          : this.entityUuid,
      operation: data.operation.present ? data.operation.value : this.operation,
      baseRevision: data.baseRevision.present
          ? data.baseRevision.value
          : this.baseRevision,
      newRevision: data.newRevision.present
          ? data.newRevision.value
          : this.newRevision,
      payload: data.payload.present ? data.payload.value : this.payload,
      originDeviceId: data.originDeviceId.present
          ? data.originDeviceId.value
          : this.originDeviceId,
      recordedAtMs: data.recordedAtMs.present
          ? data.recordedAtMs.value
          : this.recordedAtMs,
      payloadVersion: data.payloadVersion.present
          ? data.payloadVersion.value
          : this.payloadVersion,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SyncChange(')
          ..write('seq: $seq, ')
          ..write('entityType: $entityType, ')
          ..write('entityUuid: $entityUuid, ')
          ..write('operation: $operation, ')
          ..write('baseRevision: $baseRevision, ')
          ..write('newRevision: $newRevision, ')
          ..write('payload: $payload, ')
          ..write('originDeviceId: $originDeviceId, ')
          ..write('recordedAtMs: $recordedAtMs, ')
          ..write('payloadVersion: $payloadVersion')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    seq,
    entityType,
    entityUuid,
    operation,
    baseRevision,
    newRevision,
    payload,
    originDeviceId,
    recordedAtMs,
    payloadVersion,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncChange &&
          other.seq == this.seq &&
          other.entityType == this.entityType &&
          other.entityUuid == this.entityUuid &&
          other.operation == this.operation &&
          other.baseRevision == this.baseRevision &&
          other.newRevision == this.newRevision &&
          other.payload == this.payload &&
          other.originDeviceId == this.originDeviceId &&
          other.recordedAtMs == this.recordedAtMs &&
          other.payloadVersion == this.payloadVersion);
}

class SyncChangesCompanion extends UpdateCompanion<SyncChange> {
  final Value<int> seq;
  final Value<String> entityType;
  final Value<String> entityUuid;
  final Value<String> operation;
  final Value<int?> baseRevision;
  final Value<int?> newRevision;
  final Value<String> payload;
  final Value<String> originDeviceId;
  final Value<int> recordedAtMs;
  final Value<int> payloadVersion;
  const SyncChangesCompanion({
    this.seq = const Value.absent(),
    this.entityType = const Value.absent(),
    this.entityUuid = const Value.absent(),
    this.operation = const Value.absent(),
    this.baseRevision = const Value.absent(),
    this.newRevision = const Value.absent(),
    this.payload = const Value.absent(),
    this.originDeviceId = const Value.absent(),
    this.recordedAtMs = const Value.absent(),
    this.payloadVersion = const Value.absent(),
  });
  SyncChangesCompanion.insert({
    this.seq = const Value.absent(),
    required String entityType,
    required String entityUuid,
    required String operation,
    this.baseRevision = const Value.absent(),
    this.newRevision = const Value.absent(),
    required String payload,
    required String originDeviceId,
    required int recordedAtMs,
    this.payloadVersion = const Value.absent(),
  }) : entityType = Value(entityType),
       entityUuid = Value(entityUuid),
       operation = Value(operation),
       payload = Value(payload),
       originDeviceId = Value(originDeviceId),
       recordedAtMs = Value(recordedAtMs);
  static Insertable<SyncChange> custom({
    Expression<int>? seq,
    Expression<String>? entityType,
    Expression<String>? entityUuid,
    Expression<String>? operation,
    Expression<int>? baseRevision,
    Expression<int>? newRevision,
    Expression<String>? payload,
    Expression<String>? originDeviceId,
    Expression<int>? recordedAtMs,
    Expression<int>? payloadVersion,
  }) {
    return RawValuesInsertable({
      if (seq != null) 'seq': seq,
      if (entityType != null) 'entity_type': entityType,
      if (entityUuid != null) 'entity_uuid': entityUuid,
      if (operation != null) 'operation': operation,
      if (baseRevision != null) 'base_revision': baseRevision,
      if (newRevision != null) 'new_revision': newRevision,
      if (payload != null) 'payload': payload,
      if (originDeviceId != null) 'origin_device_id': originDeviceId,
      if (recordedAtMs != null) 'recorded_at_ms': recordedAtMs,
      if (payloadVersion != null) 'payload_version': payloadVersion,
    });
  }

  SyncChangesCompanion copyWith({
    Value<int>? seq,
    Value<String>? entityType,
    Value<String>? entityUuid,
    Value<String>? operation,
    Value<int?>? baseRevision,
    Value<int?>? newRevision,
    Value<String>? payload,
    Value<String>? originDeviceId,
    Value<int>? recordedAtMs,
    Value<int>? payloadVersion,
  }) {
    return SyncChangesCompanion(
      seq: seq ?? this.seq,
      entityType: entityType ?? this.entityType,
      entityUuid: entityUuid ?? this.entityUuid,
      operation: operation ?? this.operation,
      baseRevision: baseRevision ?? this.baseRevision,
      newRevision: newRevision ?? this.newRevision,
      payload: payload ?? this.payload,
      originDeviceId: originDeviceId ?? this.originDeviceId,
      recordedAtMs: recordedAtMs ?? this.recordedAtMs,
      payloadVersion: payloadVersion ?? this.payloadVersion,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (seq.present) {
      map['seq'] = Variable<int>(seq.value);
    }
    if (entityType.present) {
      map['entity_type'] = Variable<String>(entityType.value);
    }
    if (entityUuid.present) {
      map['entity_uuid'] = Variable<String>(entityUuid.value);
    }
    if (operation.present) {
      map['operation'] = Variable<String>(operation.value);
    }
    if (baseRevision.present) {
      map['base_revision'] = Variable<int>(baseRevision.value);
    }
    if (newRevision.present) {
      map['new_revision'] = Variable<int>(newRevision.value);
    }
    if (payload.present) {
      map['payload'] = Variable<String>(payload.value);
    }
    if (originDeviceId.present) {
      map['origin_device_id'] = Variable<String>(originDeviceId.value);
    }
    if (recordedAtMs.present) {
      map['recorded_at_ms'] = Variable<int>(recordedAtMs.value);
    }
    if (payloadVersion.present) {
      map['payload_version'] = Variable<int>(payloadVersion.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SyncChangesCompanion(')
          ..write('seq: $seq, ')
          ..write('entityType: $entityType, ')
          ..write('entityUuid: $entityUuid, ')
          ..write('operation: $operation, ')
          ..write('baseRevision: $baseRevision, ')
          ..write('newRevision: $newRevision, ')
          ..write('payload: $payload, ')
          ..write('originDeviceId: $originDeviceId, ')
          ..write('recordedAtMs: $recordedAtMs, ')
          ..write('payloadVersion: $payloadVersion')
          ..write(')'))
        .toString();
  }
}

class $SyncPeersTable extends SyncPeers
    with TableInfo<$SyncPeersTable, SyncPeer> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncPeersTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _peerDeviceIdMeta = const VerificationMeta(
    'peerDeviceId',
  );
  @override
  late final GeneratedColumn<String> peerDeviceId = GeneratedColumn<String>(
    'peer_device_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _lastAppliedSeqMeta = const VerificationMeta(
    'lastAppliedSeq',
  );
  @override
  late final GeneratedColumn<int> lastAppliedSeq = GeneratedColumn<int>(
    'last_applied_seq',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _lastSentSeqMeta = const VerificationMeta(
    'lastSentSeq',
  );
  @override
  late final GeneratedColumn<int> lastSentSeq = GeneratedColumn<int>(
    'last_sent_seq',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _lastSyncAtMsMeta = const VerificationMeta(
    'lastSyncAtMs',
  );
  @override
  late final GeneratedColumn<int> lastSyncAtMs = GeneratedColumn<int>(
    'last_sync_at_ms',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    peerDeviceId,
    lastAppliedSeq,
    lastSentSeq,
    lastSyncAtMs,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sync_peers';
  @override
  VerificationContext validateIntegrity(
    Insertable<SyncPeer> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('peer_device_id')) {
      context.handle(
        _peerDeviceIdMeta,
        peerDeviceId.isAcceptableOrUnknown(
          data['peer_device_id']!,
          _peerDeviceIdMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_peerDeviceIdMeta);
    }
    if (data.containsKey('last_applied_seq')) {
      context.handle(
        _lastAppliedSeqMeta,
        lastAppliedSeq.isAcceptableOrUnknown(
          data['last_applied_seq']!,
          _lastAppliedSeqMeta,
        ),
      );
    }
    if (data.containsKey('last_sent_seq')) {
      context.handle(
        _lastSentSeqMeta,
        lastSentSeq.isAcceptableOrUnknown(
          data['last_sent_seq']!,
          _lastSentSeqMeta,
        ),
      );
    }
    if (data.containsKey('last_sync_at_ms')) {
      context.handle(
        _lastSyncAtMsMeta,
        lastSyncAtMs.isAcceptableOrUnknown(
          data['last_sync_at_ms']!,
          _lastSyncAtMsMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {peerDeviceId};
  @override
  SyncPeer map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SyncPeer(
      peerDeviceId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}peer_device_id'],
      )!,
      lastAppliedSeq: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}last_applied_seq'],
      )!,
      lastSentSeq: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}last_sent_seq'],
      )!,
      lastSyncAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}last_sync_at_ms'],
      ),
    );
  }

  @override
  $SyncPeersTable createAlias(String alias) {
    return $SyncPeersTable(attachedDatabase, alias);
  }
}

class SyncPeer extends DataClass implements Insertable<SyncPeer> {
  final String peerDeviceId;
  final int lastAppliedSeq;
  final int lastSentSeq;
  final int? lastSyncAtMs;
  const SyncPeer({
    required this.peerDeviceId,
    required this.lastAppliedSeq,
    required this.lastSentSeq,
    this.lastSyncAtMs,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['peer_device_id'] = Variable<String>(peerDeviceId);
    map['last_applied_seq'] = Variable<int>(lastAppliedSeq);
    map['last_sent_seq'] = Variable<int>(lastSentSeq);
    if (!nullToAbsent || lastSyncAtMs != null) {
      map['last_sync_at_ms'] = Variable<int>(lastSyncAtMs);
    }
    return map;
  }

  SyncPeersCompanion toCompanion(bool nullToAbsent) {
    return SyncPeersCompanion(
      peerDeviceId: Value(peerDeviceId),
      lastAppliedSeq: Value(lastAppliedSeq),
      lastSentSeq: Value(lastSentSeq),
      lastSyncAtMs: lastSyncAtMs == null && nullToAbsent
          ? const Value.absent()
          : Value(lastSyncAtMs),
    );
  }

  factory SyncPeer.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SyncPeer(
      peerDeviceId: serializer.fromJson<String>(json['peerDeviceId']),
      lastAppliedSeq: serializer.fromJson<int>(json['lastAppliedSeq']),
      lastSentSeq: serializer.fromJson<int>(json['lastSentSeq']),
      lastSyncAtMs: serializer.fromJson<int?>(json['lastSyncAtMs']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'peerDeviceId': serializer.toJson<String>(peerDeviceId),
      'lastAppliedSeq': serializer.toJson<int>(lastAppliedSeq),
      'lastSentSeq': serializer.toJson<int>(lastSentSeq),
      'lastSyncAtMs': serializer.toJson<int?>(lastSyncAtMs),
    };
  }

  SyncPeer copyWith({
    String? peerDeviceId,
    int? lastAppliedSeq,
    int? lastSentSeq,
    Value<int?> lastSyncAtMs = const Value.absent(),
  }) => SyncPeer(
    peerDeviceId: peerDeviceId ?? this.peerDeviceId,
    lastAppliedSeq: lastAppliedSeq ?? this.lastAppliedSeq,
    lastSentSeq: lastSentSeq ?? this.lastSentSeq,
    lastSyncAtMs: lastSyncAtMs.present ? lastSyncAtMs.value : this.lastSyncAtMs,
  );
  SyncPeer copyWithCompanion(SyncPeersCompanion data) {
    return SyncPeer(
      peerDeviceId: data.peerDeviceId.present
          ? data.peerDeviceId.value
          : this.peerDeviceId,
      lastAppliedSeq: data.lastAppliedSeq.present
          ? data.lastAppliedSeq.value
          : this.lastAppliedSeq,
      lastSentSeq: data.lastSentSeq.present
          ? data.lastSentSeq.value
          : this.lastSentSeq,
      lastSyncAtMs: data.lastSyncAtMs.present
          ? data.lastSyncAtMs.value
          : this.lastSyncAtMs,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SyncPeer(')
          ..write('peerDeviceId: $peerDeviceId, ')
          ..write('lastAppliedSeq: $lastAppliedSeq, ')
          ..write('lastSentSeq: $lastSentSeq, ')
          ..write('lastSyncAtMs: $lastSyncAtMs')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(peerDeviceId, lastAppliedSeq, lastSentSeq, lastSyncAtMs);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncPeer &&
          other.peerDeviceId == this.peerDeviceId &&
          other.lastAppliedSeq == this.lastAppliedSeq &&
          other.lastSentSeq == this.lastSentSeq &&
          other.lastSyncAtMs == this.lastSyncAtMs);
}

class SyncPeersCompanion extends UpdateCompanion<SyncPeer> {
  final Value<String> peerDeviceId;
  final Value<int> lastAppliedSeq;
  final Value<int> lastSentSeq;
  final Value<int?> lastSyncAtMs;
  final Value<int> rowid;
  const SyncPeersCompanion({
    this.peerDeviceId = const Value.absent(),
    this.lastAppliedSeq = const Value.absent(),
    this.lastSentSeq = const Value.absent(),
    this.lastSyncAtMs = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  SyncPeersCompanion.insert({
    required String peerDeviceId,
    this.lastAppliedSeq = const Value.absent(),
    this.lastSentSeq = const Value.absent(),
    this.lastSyncAtMs = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : peerDeviceId = Value(peerDeviceId);
  static Insertable<SyncPeer> custom({
    Expression<String>? peerDeviceId,
    Expression<int>? lastAppliedSeq,
    Expression<int>? lastSentSeq,
    Expression<int>? lastSyncAtMs,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (peerDeviceId != null) 'peer_device_id': peerDeviceId,
      if (lastAppliedSeq != null) 'last_applied_seq': lastAppliedSeq,
      if (lastSentSeq != null) 'last_sent_seq': lastSentSeq,
      if (lastSyncAtMs != null) 'last_sync_at_ms': lastSyncAtMs,
      if (rowid != null) 'rowid': rowid,
    });
  }

  SyncPeersCompanion copyWith({
    Value<String>? peerDeviceId,
    Value<int>? lastAppliedSeq,
    Value<int>? lastSentSeq,
    Value<int?>? lastSyncAtMs,
    Value<int>? rowid,
  }) {
    return SyncPeersCompanion(
      peerDeviceId: peerDeviceId ?? this.peerDeviceId,
      lastAppliedSeq: lastAppliedSeq ?? this.lastAppliedSeq,
      lastSentSeq: lastSentSeq ?? this.lastSentSeq,
      lastSyncAtMs: lastSyncAtMs ?? this.lastSyncAtMs,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (peerDeviceId.present) {
      map['peer_device_id'] = Variable<String>(peerDeviceId.value);
    }
    if (lastAppliedSeq.present) {
      map['last_applied_seq'] = Variable<int>(lastAppliedSeq.value);
    }
    if (lastSentSeq.present) {
      map['last_sent_seq'] = Variable<int>(lastSentSeq.value);
    }
    if (lastSyncAtMs.present) {
      map['last_sync_at_ms'] = Variable<int>(lastSyncAtMs.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SyncPeersCompanion(')
          ..write('peerDeviceId: $peerDeviceId, ')
          ..write('lastAppliedSeq: $lastAppliedSeq, ')
          ..write('lastSentSeq: $lastSentSeq, ')
          ..write('lastSyncAtMs: $lastSyncAtMs, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SyncConflictsTable extends SyncConflicts
    with TableInfo<$SyncConflictsTable, SyncConflict> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncConflictsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _conflictIdMeta = const VerificationMeta(
    'conflictId',
  );
  @override
  late final GeneratedColumn<String> conflictId = GeneratedColumn<String>(
    'conflict_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _entityUuidMeta = const VerificationMeta(
    'entityUuid',
  );
  @override
  late final GeneratedColumn<String> entityUuid = GeneratedColumn<String>(
    'entity_uuid',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _peerDeviceIdMeta = const VerificationMeta(
    'peerDeviceId',
  );
  @override
  late final GeneratedColumn<String> peerDeviceId = GeneratedColumn<String>(
    'peer_device_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _localPayloadMeta = const VerificationMeta(
    'localPayload',
  );
  @override
  late final GeneratedColumn<String> localPayload = GeneratedColumn<String>(
    'local_payload',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _remotePayloadMeta = const VerificationMeta(
    'remotePayload',
  );
  @override
  late final GeneratedColumn<String> remotePayload = GeneratedColumn<String>(
    'remote_payload',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _resolutionMeta = const VerificationMeta(
    'resolution',
  );
  @override
  late final GeneratedColumn<String> resolution = GeneratedColumn<String>(
    'resolution',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _detectedAtMsMeta = const VerificationMeta(
    'detectedAtMs',
  );
  @override
  late final GeneratedColumn<int> detectedAtMs = GeneratedColumn<int>(
    'detected_at_ms',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    conflictId,
    entityUuid,
    peerDeviceId,
    localPayload,
    remotePayload,
    resolution,
    detectedAtMs,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sync_conflicts';
  @override
  VerificationContext validateIntegrity(
    Insertable<SyncConflict> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('conflict_id')) {
      context.handle(
        _conflictIdMeta,
        conflictId.isAcceptableOrUnknown(data['conflict_id']!, _conflictIdMeta),
      );
    } else if (isInserting) {
      context.missing(_conflictIdMeta);
    }
    if (data.containsKey('entity_uuid')) {
      context.handle(
        _entityUuidMeta,
        entityUuid.isAcceptableOrUnknown(data['entity_uuid']!, _entityUuidMeta),
      );
    } else if (isInserting) {
      context.missing(_entityUuidMeta);
    }
    if (data.containsKey('peer_device_id')) {
      context.handle(
        _peerDeviceIdMeta,
        peerDeviceId.isAcceptableOrUnknown(
          data['peer_device_id']!,
          _peerDeviceIdMeta,
        ),
      );
    }
    if (data.containsKey('local_payload')) {
      context.handle(
        _localPayloadMeta,
        localPayload.isAcceptableOrUnknown(
          data['local_payload']!,
          _localPayloadMeta,
        ),
      );
    }
    if (data.containsKey('remote_payload')) {
      context.handle(
        _remotePayloadMeta,
        remotePayload.isAcceptableOrUnknown(
          data['remote_payload']!,
          _remotePayloadMeta,
        ),
      );
    }
    if (data.containsKey('resolution')) {
      context.handle(
        _resolutionMeta,
        resolution.isAcceptableOrUnknown(data['resolution']!, _resolutionMeta),
      );
    } else if (isInserting) {
      context.missing(_resolutionMeta);
    }
    if (data.containsKey('detected_at_ms')) {
      context.handle(
        _detectedAtMsMeta,
        detectedAtMs.isAcceptableOrUnknown(
          data['detected_at_ms']!,
          _detectedAtMsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_detectedAtMsMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {conflictId};
  @override
  SyncConflict map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SyncConflict(
      conflictId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}conflict_id'],
      )!,
      entityUuid: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}entity_uuid'],
      )!,
      peerDeviceId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}peer_device_id'],
      ),
      localPayload: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}local_payload'],
      ),
      remotePayload: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}remote_payload'],
      ),
      resolution: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}resolution'],
      )!,
      detectedAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}detected_at_ms'],
      )!,
    );
  }

  @override
  $SyncConflictsTable createAlias(String alias) {
    return $SyncConflictsTable(attachedDatabase, alias);
  }
}

class SyncConflict extends DataClass implements Insertable<SyncConflict> {
  final String conflictId;
  final String entityUuid;
  final String? peerDeviceId;
  final String? localPayload;
  final String? remotePayload;
  final String resolution;
  final int detectedAtMs;
  const SyncConflict({
    required this.conflictId,
    required this.entityUuid,
    this.peerDeviceId,
    this.localPayload,
    this.remotePayload,
    required this.resolution,
    required this.detectedAtMs,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['conflict_id'] = Variable<String>(conflictId);
    map['entity_uuid'] = Variable<String>(entityUuid);
    if (!nullToAbsent || peerDeviceId != null) {
      map['peer_device_id'] = Variable<String>(peerDeviceId);
    }
    if (!nullToAbsent || localPayload != null) {
      map['local_payload'] = Variable<String>(localPayload);
    }
    if (!nullToAbsent || remotePayload != null) {
      map['remote_payload'] = Variable<String>(remotePayload);
    }
    map['resolution'] = Variable<String>(resolution);
    map['detected_at_ms'] = Variable<int>(detectedAtMs);
    return map;
  }

  SyncConflictsCompanion toCompanion(bool nullToAbsent) {
    return SyncConflictsCompanion(
      conflictId: Value(conflictId),
      entityUuid: Value(entityUuid),
      peerDeviceId: peerDeviceId == null && nullToAbsent
          ? const Value.absent()
          : Value(peerDeviceId),
      localPayload: localPayload == null && nullToAbsent
          ? const Value.absent()
          : Value(localPayload),
      remotePayload: remotePayload == null && nullToAbsent
          ? const Value.absent()
          : Value(remotePayload),
      resolution: Value(resolution),
      detectedAtMs: Value(detectedAtMs),
    );
  }

  factory SyncConflict.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SyncConflict(
      conflictId: serializer.fromJson<String>(json['conflictId']),
      entityUuid: serializer.fromJson<String>(json['entityUuid']),
      peerDeviceId: serializer.fromJson<String?>(json['peerDeviceId']),
      localPayload: serializer.fromJson<String?>(json['localPayload']),
      remotePayload: serializer.fromJson<String?>(json['remotePayload']),
      resolution: serializer.fromJson<String>(json['resolution']),
      detectedAtMs: serializer.fromJson<int>(json['detectedAtMs']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'conflictId': serializer.toJson<String>(conflictId),
      'entityUuid': serializer.toJson<String>(entityUuid),
      'peerDeviceId': serializer.toJson<String?>(peerDeviceId),
      'localPayload': serializer.toJson<String?>(localPayload),
      'remotePayload': serializer.toJson<String?>(remotePayload),
      'resolution': serializer.toJson<String>(resolution),
      'detectedAtMs': serializer.toJson<int>(detectedAtMs),
    };
  }

  SyncConflict copyWith({
    String? conflictId,
    String? entityUuid,
    Value<String?> peerDeviceId = const Value.absent(),
    Value<String?> localPayload = const Value.absent(),
    Value<String?> remotePayload = const Value.absent(),
    String? resolution,
    int? detectedAtMs,
  }) => SyncConflict(
    conflictId: conflictId ?? this.conflictId,
    entityUuid: entityUuid ?? this.entityUuid,
    peerDeviceId: peerDeviceId.present ? peerDeviceId.value : this.peerDeviceId,
    localPayload: localPayload.present ? localPayload.value : this.localPayload,
    remotePayload: remotePayload.present
        ? remotePayload.value
        : this.remotePayload,
    resolution: resolution ?? this.resolution,
    detectedAtMs: detectedAtMs ?? this.detectedAtMs,
  );
  SyncConflict copyWithCompanion(SyncConflictsCompanion data) {
    return SyncConflict(
      conflictId: data.conflictId.present
          ? data.conflictId.value
          : this.conflictId,
      entityUuid: data.entityUuid.present
          ? data.entityUuid.value
          : this.entityUuid,
      peerDeviceId: data.peerDeviceId.present
          ? data.peerDeviceId.value
          : this.peerDeviceId,
      localPayload: data.localPayload.present
          ? data.localPayload.value
          : this.localPayload,
      remotePayload: data.remotePayload.present
          ? data.remotePayload.value
          : this.remotePayload,
      resolution: data.resolution.present
          ? data.resolution.value
          : this.resolution,
      detectedAtMs: data.detectedAtMs.present
          ? data.detectedAtMs.value
          : this.detectedAtMs,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SyncConflict(')
          ..write('conflictId: $conflictId, ')
          ..write('entityUuid: $entityUuid, ')
          ..write('peerDeviceId: $peerDeviceId, ')
          ..write('localPayload: $localPayload, ')
          ..write('remotePayload: $remotePayload, ')
          ..write('resolution: $resolution, ')
          ..write('detectedAtMs: $detectedAtMs')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    conflictId,
    entityUuid,
    peerDeviceId,
    localPayload,
    remotePayload,
    resolution,
    detectedAtMs,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncConflict &&
          other.conflictId == this.conflictId &&
          other.entityUuid == this.entityUuid &&
          other.peerDeviceId == this.peerDeviceId &&
          other.localPayload == this.localPayload &&
          other.remotePayload == this.remotePayload &&
          other.resolution == this.resolution &&
          other.detectedAtMs == this.detectedAtMs);
}

class SyncConflictsCompanion extends UpdateCompanion<SyncConflict> {
  final Value<String> conflictId;
  final Value<String> entityUuid;
  final Value<String?> peerDeviceId;
  final Value<String?> localPayload;
  final Value<String?> remotePayload;
  final Value<String> resolution;
  final Value<int> detectedAtMs;
  final Value<int> rowid;
  const SyncConflictsCompanion({
    this.conflictId = const Value.absent(),
    this.entityUuid = const Value.absent(),
    this.peerDeviceId = const Value.absent(),
    this.localPayload = const Value.absent(),
    this.remotePayload = const Value.absent(),
    this.resolution = const Value.absent(),
    this.detectedAtMs = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  SyncConflictsCompanion.insert({
    required String conflictId,
    required String entityUuid,
    this.peerDeviceId = const Value.absent(),
    this.localPayload = const Value.absent(),
    this.remotePayload = const Value.absent(),
    required String resolution,
    required int detectedAtMs,
    this.rowid = const Value.absent(),
  }) : conflictId = Value(conflictId),
       entityUuid = Value(entityUuid),
       resolution = Value(resolution),
       detectedAtMs = Value(detectedAtMs);
  static Insertable<SyncConflict> custom({
    Expression<String>? conflictId,
    Expression<String>? entityUuid,
    Expression<String>? peerDeviceId,
    Expression<String>? localPayload,
    Expression<String>? remotePayload,
    Expression<String>? resolution,
    Expression<int>? detectedAtMs,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (conflictId != null) 'conflict_id': conflictId,
      if (entityUuid != null) 'entity_uuid': entityUuid,
      if (peerDeviceId != null) 'peer_device_id': peerDeviceId,
      if (localPayload != null) 'local_payload': localPayload,
      if (remotePayload != null) 'remote_payload': remotePayload,
      if (resolution != null) 'resolution': resolution,
      if (detectedAtMs != null) 'detected_at_ms': detectedAtMs,
      if (rowid != null) 'rowid': rowid,
    });
  }

  SyncConflictsCompanion copyWith({
    Value<String>? conflictId,
    Value<String>? entityUuid,
    Value<String?>? peerDeviceId,
    Value<String?>? localPayload,
    Value<String?>? remotePayload,
    Value<String>? resolution,
    Value<int>? detectedAtMs,
    Value<int>? rowid,
  }) {
    return SyncConflictsCompanion(
      conflictId: conflictId ?? this.conflictId,
      entityUuid: entityUuid ?? this.entityUuid,
      peerDeviceId: peerDeviceId ?? this.peerDeviceId,
      localPayload: localPayload ?? this.localPayload,
      remotePayload: remotePayload ?? this.remotePayload,
      resolution: resolution ?? this.resolution,
      detectedAtMs: detectedAtMs ?? this.detectedAtMs,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (conflictId.present) {
      map['conflict_id'] = Variable<String>(conflictId.value);
    }
    if (entityUuid.present) {
      map['entity_uuid'] = Variable<String>(entityUuid.value);
    }
    if (peerDeviceId.present) {
      map['peer_device_id'] = Variable<String>(peerDeviceId.value);
    }
    if (localPayload.present) {
      map['local_payload'] = Variable<String>(localPayload.value);
    }
    if (remotePayload.present) {
      map['remote_payload'] = Variable<String>(remotePayload.value);
    }
    if (resolution.present) {
      map['resolution'] = Variable<String>(resolution.value);
    }
    if (detectedAtMs.present) {
      map['detected_at_ms'] = Variable<int>(detectedAtMs.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SyncConflictsCompanion(')
          ..write('conflictId: $conflictId, ')
          ..write('entityUuid: $entityUuid, ')
          ..write('peerDeviceId: $peerDeviceId, ')
          ..write('localPayload: $localPayload, ')
          ..write('remotePayload: $remotePayload, ')
          ..write('resolution: $resolution, ')
          ..write('detectedAtMs: $detectedAtMs, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $ImportBatchesTable extends ImportBatches
    with TableInfo<$ImportBatchesTable, ImportBatche> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ImportBatchesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _batchIdMeta = const VerificationMeta(
    'batchId',
  );
  @override
  late final GeneratedColumn<String> batchId = GeneratedColumn<String>(
    'batch_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _sourceFileMeta = const VerificationMeta(
    'sourceFile',
  );
  @override
  late final GeneratedColumn<String> sourceFile = GeneratedColumn<String>(
    'source_file',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _sourceTypeMeta = const VerificationMeta(
    'sourceType',
  );
  @override
  late final GeneratedColumn<String> sourceType = GeneratedColumn<String>(
    'source_type',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _bankFormatMeta = const VerificationMeta(
    'bankFormat',
  );
  @override
  late final GeneratedColumn<String> bankFormat = GeneratedColumn<String>(
    'bank_format',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _importedAtMsMeta = const VerificationMeta(
    'importedAtMs',
  );
  @override
  late final GeneratedColumn<int> importedAtMs = GeneratedColumn<int>(
    'imported_at_ms',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _importedCountMeta = const VerificationMeta(
    'importedCount',
  );
  @override
  late final GeneratedColumn<int> importedCount = GeneratedColumn<int>(
    'imported_count',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _skippedCountMeta = const VerificationMeta(
    'skippedCount',
  );
  @override
  late final GeneratedColumn<int> skippedCount = GeneratedColumn<int>(
    'skipped_count',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _deviceIdMeta = const VerificationMeta(
    'deviceId',
  );
  @override
  late final GeneratedColumn<String> deviceId = GeneratedColumn<String>(
    'device_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    batchId,
    sourceFile,
    sourceType,
    bankFormat,
    importedAtMs,
    importedCount,
    skippedCount,
    deviceId,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'import_batches';
  @override
  VerificationContext validateIntegrity(
    Insertable<ImportBatche> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('batch_id')) {
      context.handle(
        _batchIdMeta,
        batchId.isAcceptableOrUnknown(data['batch_id']!, _batchIdMeta),
      );
    } else if (isInserting) {
      context.missing(_batchIdMeta);
    }
    if (data.containsKey('source_file')) {
      context.handle(
        _sourceFileMeta,
        sourceFile.isAcceptableOrUnknown(data['source_file']!, _sourceFileMeta),
      );
    }
    if (data.containsKey('source_type')) {
      context.handle(
        _sourceTypeMeta,
        sourceType.isAcceptableOrUnknown(data['source_type']!, _sourceTypeMeta),
      );
    }
    if (data.containsKey('bank_format')) {
      context.handle(
        _bankFormatMeta,
        bankFormat.isAcceptableOrUnknown(data['bank_format']!, _bankFormatMeta),
      );
    }
    if (data.containsKey('imported_at_ms')) {
      context.handle(
        _importedAtMsMeta,
        importedAtMs.isAcceptableOrUnknown(
          data['imported_at_ms']!,
          _importedAtMsMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_importedAtMsMeta);
    }
    if (data.containsKey('imported_count')) {
      context.handle(
        _importedCountMeta,
        importedCount.isAcceptableOrUnknown(
          data['imported_count']!,
          _importedCountMeta,
        ),
      );
    }
    if (data.containsKey('skipped_count')) {
      context.handle(
        _skippedCountMeta,
        skippedCount.isAcceptableOrUnknown(
          data['skipped_count']!,
          _skippedCountMeta,
        ),
      );
    }
    if (data.containsKey('device_id')) {
      context.handle(
        _deviceIdMeta,
        deviceId.isAcceptableOrUnknown(data['device_id']!, _deviceIdMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {batchId};
  @override
  ImportBatche map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ImportBatche(
      batchId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}batch_id'],
      )!,
      sourceFile: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}source_file'],
      ),
      sourceType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}source_type'],
      ),
      bankFormat: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}bank_format'],
      ),
      importedAtMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}imported_at_ms'],
      )!,
      importedCount: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}imported_count'],
      )!,
      skippedCount: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}skipped_count'],
      )!,
      deviceId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}device_id'],
      ),
    );
  }

  @override
  $ImportBatchesTable createAlias(String alias) {
    return $ImportBatchesTable(attachedDatabase, alias);
  }
}

class ImportBatche extends DataClass implements Insertable<ImportBatche> {
  final String batchId;
  final String? sourceFile;
  final String? sourceType;
  final String? bankFormat;
  final int importedAtMs;
  final int importedCount;
  final int skippedCount;
  final String? deviceId;
  const ImportBatche({
    required this.batchId,
    this.sourceFile,
    this.sourceType,
    this.bankFormat,
    required this.importedAtMs,
    required this.importedCount,
    required this.skippedCount,
    this.deviceId,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['batch_id'] = Variable<String>(batchId);
    if (!nullToAbsent || sourceFile != null) {
      map['source_file'] = Variable<String>(sourceFile);
    }
    if (!nullToAbsent || sourceType != null) {
      map['source_type'] = Variable<String>(sourceType);
    }
    if (!nullToAbsent || bankFormat != null) {
      map['bank_format'] = Variable<String>(bankFormat);
    }
    map['imported_at_ms'] = Variable<int>(importedAtMs);
    map['imported_count'] = Variable<int>(importedCount);
    map['skipped_count'] = Variable<int>(skippedCount);
    if (!nullToAbsent || deviceId != null) {
      map['device_id'] = Variable<String>(deviceId);
    }
    return map;
  }

  ImportBatchesCompanion toCompanion(bool nullToAbsent) {
    return ImportBatchesCompanion(
      batchId: Value(batchId),
      sourceFile: sourceFile == null && nullToAbsent
          ? const Value.absent()
          : Value(sourceFile),
      sourceType: sourceType == null && nullToAbsent
          ? const Value.absent()
          : Value(sourceType),
      bankFormat: bankFormat == null && nullToAbsent
          ? const Value.absent()
          : Value(bankFormat),
      importedAtMs: Value(importedAtMs),
      importedCount: Value(importedCount),
      skippedCount: Value(skippedCount),
      deviceId: deviceId == null && nullToAbsent
          ? const Value.absent()
          : Value(deviceId),
    );
  }

  factory ImportBatche.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ImportBatche(
      batchId: serializer.fromJson<String>(json['batchId']),
      sourceFile: serializer.fromJson<String?>(json['sourceFile']),
      sourceType: serializer.fromJson<String?>(json['sourceType']),
      bankFormat: serializer.fromJson<String?>(json['bankFormat']),
      importedAtMs: serializer.fromJson<int>(json['importedAtMs']),
      importedCount: serializer.fromJson<int>(json['importedCount']),
      skippedCount: serializer.fromJson<int>(json['skippedCount']),
      deviceId: serializer.fromJson<String?>(json['deviceId']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'batchId': serializer.toJson<String>(batchId),
      'sourceFile': serializer.toJson<String?>(sourceFile),
      'sourceType': serializer.toJson<String?>(sourceType),
      'bankFormat': serializer.toJson<String?>(bankFormat),
      'importedAtMs': serializer.toJson<int>(importedAtMs),
      'importedCount': serializer.toJson<int>(importedCount),
      'skippedCount': serializer.toJson<int>(skippedCount),
      'deviceId': serializer.toJson<String?>(deviceId),
    };
  }

  ImportBatche copyWith({
    String? batchId,
    Value<String?> sourceFile = const Value.absent(),
    Value<String?> sourceType = const Value.absent(),
    Value<String?> bankFormat = const Value.absent(),
    int? importedAtMs,
    int? importedCount,
    int? skippedCount,
    Value<String?> deviceId = const Value.absent(),
  }) => ImportBatche(
    batchId: batchId ?? this.batchId,
    sourceFile: sourceFile.present ? sourceFile.value : this.sourceFile,
    sourceType: sourceType.present ? sourceType.value : this.sourceType,
    bankFormat: bankFormat.present ? bankFormat.value : this.bankFormat,
    importedAtMs: importedAtMs ?? this.importedAtMs,
    importedCount: importedCount ?? this.importedCount,
    skippedCount: skippedCount ?? this.skippedCount,
    deviceId: deviceId.present ? deviceId.value : this.deviceId,
  );
  ImportBatche copyWithCompanion(ImportBatchesCompanion data) {
    return ImportBatche(
      batchId: data.batchId.present ? data.batchId.value : this.batchId,
      sourceFile: data.sourceFile.present
          ? data.sourceFile.value
          : this.sourceFile,
      sourceType: data.sourceType.present
          ? data.sourceType.value
          : this.sourceType,
      bankFormat: data.bankFormat.present
          ? data.bankFormat.value
          : this.bankFormat,
      importedAtMs: data.importedAtMs.present
          ? data.importedAtMs.value
          : this.importedAtMs,
      importedCount: data.importedCount.present
          ? data.importedCount.value
          : this.importedCount,
      skippedCount: data.skippedCount.present
          ? data.skippedCount.value
          : this.skippedCount,
      deviceId: data.deviceId.present ? data.deviceId.value : this.deviceId,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ImportBatche(')
          ..write('batchId: $batchId, ')
          ..write('sourceFile: $sourceFile, ')
          ..write('sourceType: $sourceType, ')
          ..write('bankFormat: $bankFormat, ')
          ..write('importedAtMs: $importedAtMs, ')
          ..write('importedCount: $importedCount, ')
          ..write('skippedCount: $skippedCount, ')
          ..write('deviceId: $deviceId')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    batchId,
    sourceFile,
    sourceType,
    bankFormat,
    importedAtMs,
    importedCount,
    skippedCount,
    deviceId,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ImportBatche &&
          other.batchId == this.batchId &&
          other.sourceFile == this.sourceFile &&
          other.sourceType == this.sourceType &&
          other.bankFormat == this.bankFormat &&
          other.importedAtMs == this.importedAtMs &&
          other.importedCount == this.importedCount &&
          other.skippedCount == this.skippedCount &&
          other.deviceId == this.deviceId);
}

class ImportBatchesCompanion extends UpdateCompanion<ImportBatche> {
  final Value<String> batchId;
  final Value<String?> sourceFile;
  final Value<String?> sourceType;
  final Value<String?> bankFormat;
  final Value<int> importedAtMs;
  final Value<int> importedCount;
  final Value<int> skippedCount;
  final Value<String?> deviceId;
  final Value<int> rowid;
  const ImportBatchesCompanion({
    this.batchId = const Value.absent(),
    this.sourceFile = const Value.absent(),
    this.sourceType = const Value.absent(),
    this.bankFormat = const Value.absent(),
    this.importedAtMs = const Value.absent(),
    this.importedCount = const Value.absent(),
    this.skippedCount = const Value.absent(),
    this.deviceId = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  ImportBatchesCompanion.insert({
    required String batchId,
    this.sourceFile = const Value.absent(),
    this.sourceType = const Value.absent(),
    this.bankFormat = const Value.absent(),
    required int importedAtMs,
    this.importedCount = const Value.absent(),
    this.skippedCount = const Value.absent(),
    this.deviceId = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : batchId = Value(batchId),
       importedAtMs = Value(importedAtMs);
  static Insertable<ImportBatche> custom({
    Expression<String>? batchId,
    Expression<String>? sourceFile,
    Expression<String>? sourceType,
    Expression<String>? bankFormat,
    Expression<int>? importedAtMs,
    Expression<int>? importedCount,
    Expression<int>? skippedCount,
    Expression<String>? deviceId,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (batchId != null) 'batch_id': batchId,
      if (sourceFile != null) 'source_file': sourceFile,
      if (sourceType != null) 'source_type': sourceType,
      if (bankFormat != null) 'bank_format': bankFormat,
      if (importedAtMs != null) 'imported_at_ms': importedAtMs,
      if (importedCount != null) 'imported_count': importedCount,
      if (skippedCount != null) 'skipped_count': skippedCount,
      if (deviceId != null) 'device_id': deviceId,
      if (rowid != null) 'rowid': rowid,
    });
  }

  ImportBatchesCompanion copyWith({
    Value<String>? batchId,
    Value<String?>? sourceFile,
    Value<String?>? sourceType,
    Value<String?>? bankFormat,
    Value<int>? importedAtMs,
    Value<int>? importedCount,
    Value<int>? skippedCount,
    Value<String?>? deviceId,
    Value<int>? rowid,
  }) {
    return ImportBatchesCompanion(
      batchId: batchId ?? this.batchId,
      sourceFile: sourceFile ?? this.sourceFile,
      sourceType: sourceType ?? this.sourceType,
      bankFormat: bankFormat ?? this.bankFormat,
      importedAtMs: importedAtMs ?? this.importedAtMs,
      importedCount: importedCount ?? this.importedCount,
      skippedCount: skippedCount ?? this.skippedCount,
      deviceId: deviceId ?? this.deviceId,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (batchId.present) {
      map['batch_id'] = Variable<String>(batchId.value);
    }
    if (sourceFile.present) {
      map['source_file'] = Variable<String>(sourceFile.value);
    }
    if (sourceType.present) {
      map['source_type'] = Variable<String>(sourceType.value);
    }
    if (bankFormat.present) {
      map['bank_format'] = Variable<String>(bankFormat.value);
    }
    if (importedAtMs.present) {
      map['imported_at_ms'] = Variable<int>(importedAtMs.value);
    }
    if (importedCount.present) {
      map['imported_count'] = Variable<int>(importedCount.value);
    }
    if (skippedCount.present) {
      map['skipped_count'] = Variable<int>(skippedCount.value);
    }
    if (deviceId.present) {
      map['device_id'] = Variable<String>(deviceId.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ImportBatchesCompanion(')
          ..write('batchId: $batchId, ')
          ..write('sourceFile: $sourceFile, ')
          ..write('sourceType: $sourceType, ')
          ..write('bankFormat: $bankFormat, ')
          ..write('importedAtMs: $importedAtMs, ')
          ..write('importedCount: $importedCount, ')
          ..write('skippedCount: $skippedCount, ')
          ..write('deviceId: $deviceId, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $AppMetaTable appMeta = $AppMetaTable(this);
  late final $DevicesTable devices = $DevicesTable(this);
  late final $AccountsTable accounts = $AccountsTable(this);
  late final $TransactionsTable transactions = $TransactionsTable(this);
  late final $SyncChangesTable syncChanges = $SyncChangesTable(this);
  late final $SyncPeersTable syncPeers = $SyncPeersTable(this);
  late final $SyncConflictsTable syncConflicts = $SyncConflictsTable(this);
  late final $ImportBatchesTable importBatches = $ImportBatchesTable(this);
  late final Index idxAccountsOneDefault = Index(
    'idx_accounts_one_default',
    'CREATE UNIQUE INDEX idx_accounts_one_default ON accounts (is_default) WHERE is_default = 1 AND deleted_at_ms IS NULL',
  );
  late final Index idxAccountsLive = Index(
    'idx_accounts_live',
    'CREATE INDEX idx_accounts_live ON accounts (deleted_at_ms, name)',
  );
  late final Index idxTxDate = Index(
    'idx_tx_date',
    'CREATE INDEX idx_tx_date ON transactions (transaction_date DESC, id DESC)',
  );
  late final Index idxTxUpdated = Index(
    'idx_tx_updated',
    'CREATE INDEX idx_tx_updated ON transactions (updated_at_ms)',
  );
  late final Index idxTxAccountDate = Index(
    'idx_tx_account_date',
    'CREATE INDEX idx_tx_account_date ON transactions (account_uuid, transaction_date DESC, id DESC)',
  );
  late final Index idxTxAccountDateDeleted = Index(
    'idx_tx_account_date_deleted',
    'CREATE INDEX idx_tx_account_date_deleted ON transactions (account_uuid, transaction_date, deleted_at_ms)',
  );
  late final Index idxTxAccountImportHash = Index(
    'idx_tx_account_import_hash',
    'CREATE UNIQUE INDEX idx_tx_account_import_hash ON transactions (account_uuid, import_hash) WHERE import_hash IS NOT NULL AND deleted_at_ms IS NULL',
  );
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    appMeta,
    devices,
    accounts,
    transactions,
    syncChanges,
    syncPeers,
    syncConflicts,
    importBatches,
    idxAccountsOneDefault,
    idxAccountsLive,
    idxTxDate,
    idxTxUpdated,
    idxTxAccountDate,
    idxTxAccountDateDeleted,
    idxTxAccountImportHash,
  ];
}

typedef $$AppMetaTableCreateCompanionBuilder = AppMetaCompanion Function({
  required String key,
  required String value,
  Value<int> rowid,
});
typedef $$AppMetaTableUpdateCompanionBuilder = AppMetaCompanion Function({
  Value<String> key,
  Value<String> value,
  Value<int> rowid,
});

class $$AppMetaTableFilterComposer
    extends Composer<_$AppDatabase, $AppMetaTable> {
  $$AppMetaTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get key => $composableBuilder(
    column: $table.key,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get value => $composableBuilder(
    column: $table.value,
    builder: (column) => ColumnFilters(column),
  );
}

class $$AppMetaTableOrderingComposer
    extends Composer<_$AppDatabase, $AppMetaTable> {
  $$AppMetaTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get key => $composableBuilder(
    column: $table.key,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get value => $composableBuilder(
    column: $table.value,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$AppMetaTableAnnotationComposer
    extends Composer<_$AppDatabase, $AppMetaTable> {
  $$AppMetaTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get key =>
      $composableBuilder(column: $table.key, builder: (column) => column);

  GeneratedColumn<String> get value =>
      $composableBuilder(column: $table.value, builder: (column) => column);
}

class $$AppMetaTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $AppMetaTable,
          AppMetaData,
          $$AppMetaTableFilterComposer,
          $$AppMetaTableOrderingComposer,
          $$AppMetaTableAnnotationComposer,
          $$AppMetaTableCreateCompanionBuilder,
          $$AppMetaTableUpdateCompanionBuilder,
          (
            AppMetaData,
            BaseReferences<_$AppDatabase, $AppMetaTable, AppMetaData>,
          ),
          AppMetaData,
          PrefetchHooks Function()
        > {
  $$AppMetaTableTableManager(_$AppDatabase db, $AppMetaTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$AppMetaTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$AppMetaTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$AppMetaTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> key = const Value.absent(),
            Value<String> value = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) => AppMetaCompanion(key: key, value: value, rowid: rowid),
          createCompanionCallback: ({
            required String key,
            required String value,
            Value<int> rowid = const Value.absent(),
          }) => AppMetaCompanion.insert(key: key, value: value, rowid: rowid),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$AppMetaTable, AppMetaData>(table),
                  BaseReferences<_$AppDatabase, $AppMetaTable, AppMetaData>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$AppMetaTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $AppMetaTable,
      AppMetaData,
      $$AppMetaTableFilterComposer,
      $$AppMetaTableOrderingComposer,
      $$AppMetaTableAnnotationComposer,
      $$AppMetaTableCreateCompanionBuilder,
      $$AppMetaTableUpdateCompanionBuilder,
      (AppMetaData, BaseReferences<_$AppDatabase, $AppMetaTable, AppMetaData>),
      AppMetaData,
      PrefetchHooks Function()
    >;
typedef $$DevicesTableCreateCompanionBuilder = DevicesCompanion Function({
  required String deviceId,
  required String name,
  required String platform,
  Value<String?> tokenHash,
  Value<String?> certFingerprint,
  Value<int?> pairedAtMs,
  Value<int?> lastSeenMs,
  Value<int?> revokedAtMs,
  Value<int> rowid,
});
typedef $$DevicesTableUpdateCompanionBuilder = DevicesCompanion Function({
  Value<String> deviceId,
  Value<String> name,
  Value<String> platform,
  Value<String?> tokenHash,
  Value<String?> certFingerprint,
  Value<int?> pairedAtMs,
  Value<int?> lastSeenMs,
  Value<int?> revokedAtMs,
  Value<int> rowid,
});

class $$DevicesTableFilterComposer
    extends Composer<_$AppDatabase, $DevicesTable> {
  $$DevicesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get deviceId => $composableBuilder(
    column: $table.deviceId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get platform => $composableBuilder(
    column: $table.platform,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get tokenHash => $composableBuilder(
    column: $table.tokenHash,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get certFingerprint => $composableBuilder(
    column: $table.certFingerprint,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get pairedAtMs => $composableBuilder(
    column: $table.pairedAtMs,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get lastSeenMs => $composableBuilder(
    column: $table.lastSeenMs,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get revokedAtMs => $composableBuilder(
    column: $table.revokedAtMs,
    builder: (column) => ColumnFilters(column),
  );
}

class $$DevicesTableOrderingComposer
    extends Composer<_$AppDatabase, $DevicesTable> {
  $$DevicesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get deviceId => $composableBuilder(
    column: $table.deviceId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get platform => $composableBuilder(
    column: $table.platform,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get tokenHash => $composableBuilder(
    column: $table.tokenHash,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get certFingerprint => $composableBuilder(
    column: $table.certFingerprint,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get pairedAtMs => $composableBuilder(
    column: $table.pairedAtMs,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get lastSeenMs => $composableBuilder(
    column: $table.lastSeenMs,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get revokedAtMs => $composableBuilder(
    column: $table.revokedAtMs,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$DevicesTableAnnotationComposer
    extends Composer<_$AppDatabase, $DevicesTable> {
  $$DevicesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get deviceId =>
      $composableBuilder(column: $table.deviceId, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get platform =>
      $composableBuilder(column: $table.platform, builder: (column) => column);

  GeneratedColumn<String> get tokenHash =>
      $composableBuilder(column: $table.tokenHash, builder: (column) => column);

  GeneratedColumn<String> get certFingerprint => $composableBuilder(
    column: $table.certFingerprint,
    builder: (column) => column,
  );

  GeneratedColumn<int> get pairedAtMs => $composableBuilder(
    column: $table.pairedAtMs,
    builder: (column) => column,
  );

  GeneratedColumn<int> get lastSeenMs => $composableBuilder(
    column: $table.lastSeenMs,
    builder: (column) => column,
  );

  GeneratedColumn<int> get revokedAtMs => $composableBuilder(
    column: $table.revokedAtMs,
    builder: (column) => column,
  );
}

class $$DevicesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $DevicesTable,
          Device,
          $$DevicesTableFilterComposer,
          $$DevicesTableOrderingComposer,
          $$DevicesTableAnnotationComposer,
          $$DevicesTableCreateCompanionBuilder,
          $$DevicesTableUpdateCompanionBuilder,
          (Device, BaseReferences<_$AppDatabase, $DevicesTable, Device>),
          Device,
          PrefetchHooks Function()
        > {
  $$DevicesTableTableManager(_$AppDatabase db, $DevicesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$DevicesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$DevicesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$DevicesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> deviceId = const Value.absent(),
                Value<String> name = const Value.absent(),
                Value<String> platform = const Value.absent(),
                Value<String?> tokenHash = const Value.absent(),
                Value<String?> certFingerprint = const Value.absent(),
                Value<int?> pairedAtMs = const Value.absent(),
                Value<int?> lastSeenMs = const Value.absent(),
                Value<int?> revokedAtMs = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => DevicesCompanion(
                deviceId: deviceId,
                name: name,
                platform: platform,
                tokenHash: tokenHash,
                certFingerprint: certFingerprint,
                pairedAtMs: pairedAtMs,
                lastSeenMs: lastSeenMs,
                revokedAtMs: revokedAtMs,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String deviceId,
                required String name,
                required String platform,
                Value<String?> tokenHash = const Value.absent(),
                Value<String?> certFingerprint = const Value.absent(),
                Value<int?> pairedAtMs = const Value.absent(),
                Value<int?> lastSeenMs = const Value.absent(),
                Value<int?> revokedAtMs = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => DevicesCompanion.insert(
                deviceId: deviceId,
                name: name,
                platform: platform,
                tokenHash: tokenHash,
                certFingerprint: certFingerprint,
                pairedAtMs: pairedAtMs,
                lastSeenMs: lastSeenMs,
                revokedAtMs: revokedAtMs,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$DevicesTable, Device>(table),
                  BaseReferences<_$AppDatabase, $DevicesTable, Device>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$DevicesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $DevicesTable,
      Device,
      $$DevicesTableFilterComposer,
      $$DevicesTableOrderingComposer,
      $$DevicesTableAnnotationComposer,
      $$DevicesTableCreateCompanionBuilder,
      $$DevicesTableUpdateCompanionBuilder,
      (Device, BaseReferences<_$AppDatabase, $DevicesTable, Device>),
      Device,
      PrefetchHooks Function()
    >;
typedef $$AccountsTableCreateCompanionBuilder = AccountsCompanion Function({
  Value<int> id,
  required String uuid,
  required String name,
  required String currencyCode,
  required int currencyPrecision,
  Value<bool> isDefault,
  required int createdAtMs,
  required int updatedAtMs,
  Value<int?> deletedAtMs,
  Value<int> revision,
  required String originDeviceId,
  required String lastModifiedBy,
  Value<String> syncState,
});
typedef $$AccountsTableUpdateCompanionBuilder = AccountsCompanion Function({
  Value<int> id,
  Value<String> uuid,
  Value<String> name,
  Value<String> currencyCode,
  Value<int> currencyPrecision,
  Value<bool> isDefault,
  Value<int> createdAtMs,
  Value<int> updatedAtMs,
  Value<int?> deletedAtMs,
  Value<int> revision,
  Value<String> originDeviceId,
  Value<String> lastModifiedBy,
  Value<String> syncState,
});

class $$AccountsTableFilterComposer
    extends Composer<_$AppDatabase, $AccountsTable> {
  $$AccountsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get uuid => $composableBuilder(
    column: $table.uuid,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get currencyCode => $composableBuilder(
    column: $table.currencyCode,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get currencyPrecision => $composableBuilder(
    column: $table.currencyPrecision,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isDefault => $composableBuilder(
    column: $table.isDefault,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get createdAtMs => $composableBuilder(
    column: $table.createdAtMs,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get updatedAtMs => $composableBuilder(
    column: $table.updatedAtMs,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get deletedAtMs => $composableBuilder(
    column: $table.deletedAtMs,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get revision => $composableBuilder(
    column: $table.revision,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get originDeviceId => $composableBuilder(
    column: $table.originDeviceId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastModifiedBy => $composableBuilder(
    column: $table.lastModifiedBy,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncState => $composableBuilder(
    column: $table.syncState,
    builder: (column) => ColumnFilters(column),
  );
}

class $$AccountsTableOrderingComposer
    extends Composer<_$AppDatabase, $AccountsTable> {
  $$AccountsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get uuid => $composableBuilder(
    column: $table.uuid,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get currencyCode => $composableBuilder(
    column: $table.currencyCode,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get currencyPrecision => $composableBuilder(
    column: $table.currencyPrecision,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isDefault => $composableBuilder(
    column: $table.isDefault,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get createdAtMs => $composableBuilder(
    column: $table.createdAtMs,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get updatedAtMs => $composableBuilder(
    column: $table.updatedAtMs,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get deletedAtMs => $composableBuilder(
    column: $table.deletedAtMs,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get revision => $composableBuilder(
    column: $table.revision,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get originDeviceId => $composableBuilder(
    column: $table.originDeviceId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastModifiedBy => $composableBuilder(
    column: $table.lastModifiedBy,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncState => $composableBuilder(
    column: $table.syncState,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$AccountsTableAnnotationComposer
    extends Composer<_$AppDatabase, $AccountsTable> {
  $$AccountsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get uuid =>
      $composableBuilder(column: $table.uuid, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get currencyCode => $composableBuilder(
    column: $table.currencyCode,
    builder: (column) => column,
  );

  GeneratedColumn<int> get currencyPrecision => $composableBuilder(
    column: $table.currencyPrecision,
    builder: (column) => column,
  );

  GeneratedColumn<bool> get isDefault =>
      $composableBuilder(column: $table.isDefault, builder: (column) => column);

  GeneratedColumn<int> get createdAtMs => $composableBuilder(
    column: $table.createdAtMs,
    builder: (column) => column,
  );

  GeneratedColumn<int> get updatedAtMs => $composableBuilder(
    column: $table.updatedAtMs,
    builder: (column) => column,
  );

  GeneratedColumn<int> get deletedAtMs => $composableBuilder(
    column: $table.deletedAtMs,
    builder: (column) => column,
  );

  GeneratedColumn<int> get revision =>
      $composableBuilder(column: $table.revision, builder: (column) => column);

  GeneratedColumn<String> get originDeviceId => $composableBuilder(
    column: $table.originDeviceId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get lastModifiedBy => $composableBuilder(
    column: $table.lastModifiedBy,
    builder: (column) => column,
  );

  GeneratedColumn<String> get syncState =>
      $composableBuilder(column: $table.syncState, builder: (column) => column);
}

class $$AccountsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $AccountsTable,
          AccountRow,
          $$AccountsTableFilterComposer,
          $$AccountsTableOrderingComposer,
          $$AccountsTableAnnotationComposer,
          $$AccountsTableCreateCompanionBuilder,
          $$AccountsTableUpdateCompanionBuilder,
          (
            AccountRow,
            BaseReferences<_$AppDatabase, $AccountsTable, AccountRow>,
          ),
          AccountRow,
          PrefetchHooks Function()
        > {
  $$AccountsTableTableManager(_$AppDatabase db, $AccountsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$AccountsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$AccountsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$AccountsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> uuid = const Value.absent(),
                Value<String> name = const Value.absent(),
                Value<String> currencyCode = const Value.absent(),
                Value<int> currencyPrecision = const Value.absent(),
                Value<bool> isDefault = const Value.absent(),
                Value<int> createdAtMs = const Value.absent(),
                Value<int> updatedAtMs = const Value.absent(),
                Value<int?> deletedAtMs = const Value.absent(),
                Value<int> revision = const Value.absent(),
                Value<String> originDeviceId = const Value.absent(),
                Value<String> lastModifiedBy = const Value.absent(),
                Value<String> syncState = const Value.absent(),
              }) => AccountsCompanion(
                id: id,
                uuid: uuid,
                name: name,
                currencyCode: currencyCode,
                currencyPrecision: currencyPrecision,
                isDefault: isDefault,
                createdAtMs: createdAtMs,
                updatedAtMs: updatedAtMs,
                deletedAtMs: deletedAtMs,
                revision: revision,
                originDeviceId: originDeviceId,
                lastModifiedBy: lastModifiedBy,
                syncState: syncState,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String uuid,
                required String name,
                required String currencyCode,
                required int currencyPrecision,
                Value<bool> isDefault = const Value.absent(),
                required int createdAtMs,
                required int updatedAtMs,
                Value<int?> deletedAtMs = const Value.absent(),
                Value<int> revision = const Value.absent(),
                required String originDeviceId,
                required String lastModifiedBy,
                Value<String> syncState = const Value.absent(),
              }) => AccountsCompanion.insert(
                id: id,
                uuid: uuid,
                name: name,
                currencyCode: currencyCode,
                currencyPrecision: currencyPrecision,
                isDefault: isDefault,
                createdAtMs: createdAtMs,
                updatedAtMs: updatedAtMs,
                deletedAtMs: deletedAtMs,
                revision: revision,
                originDeviceId: originDeviceId,
                lastModifiedBy: lastModifiedBy,
                syncState: syncState,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$AccountsTable, AccountRow>(table),
                  BaseReferences<_$AppDatabase, $AccountsTable, AccountRow>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$AccountsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $AccountsTable,
      AccountRow,
      $$AccountsTableFilterComposer,
      $$AccountsTableOrderingComposer,
      $$AccountsTableAnnotationComposer,
      $$AccountsTableCreateCompanionBuilder,
      $$AccountsTableUpdateCompanionBuilder,
      (AccountRow, BaseReferences<_$AppDatabase, $AccountsTable, AccountRow>),
      AccountRow,
      PrefetchHooks Function()
    >;
typedef $$TransactionsTableCreateCompanionBuilder =
    TransactionsCompanion Function({
      Value<int> id,
      required String transactionType,
      required int amountMinor,
      required String category,
      Value<String?> description,
      required String transactionDate,
      required String uuid,
      required int createdAtMs,
      required int updatedAtMs,
      Value<int?> deletedAtMs,
      Value<int> revision,
      required String originDeviceId,
      required String lastModifiedBy,
      Value<String> syncState,
      required String accountUuid,
      Value<String?> importHash,
      Value<String?> externalRef,
      Value<String?> importBatchId,
      Value<String?> accountLabel,
    });
typedef $$TransactionsTableUpdateCompanionBuilder =
    TransactionsCompanion Function({
      Value<int> id,
      Value<String> transactionType,
      Value<int> amountMinor,
      Value<String> category,
      Value<String?> description,
      Value<String> transactionDate,
      Value<String> uuid,
      Value<int> createdAtMs,
      Value<int> updatedAtMs,
      Value<int?> deletedAtMs,
      Value<int> revision,
      Value<String> originDeviceId,
      Value<String> lastModifiedBy,
      Value<String> syncState,
      Value<String> accountUuid,
      Value<String?> importHash,
      Value<String?> externalRef,
      Value<String?> importBatchId,
      Value<String?> accountLabel,
    });

class $$TransactionsTableFilterComposer
    extends Composer<_$AppDatabase, $TransactionsTable> {
  $$TransactionsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get transactionType => $composableBuilder(
    column: $table.transactionType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get amountMinor => $composableBuilder(
    column: $table.amountMinor,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get category => $composableBuilder(
    column: $table.category,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get description => $composableBuilder(
    column: $table.description,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get transactionDate => $composableBuilder(
    column: $table.transactionDate,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get uuid => $composableBuilder(
    column: $table.uuid,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get createdAtMs => $composableBuilder(
    column: $table.createdAtMs,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get updatedAtMs => $composableBuilder(
    column: $table.updatedAtMs,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get deletedAtMs => $composableBuilder(
    column: $table.deletedAtMs,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get revision => $composableBuilder(
    column: $table.revision,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get originDeviceId => $composableBuilder(
    column: $table.originDeviceId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastModifiedBy => $composableBuilder(
    column: $table.lastModifiedBy,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncState => $composableBuilder(
    column: $table.syncState,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get accountUuid => $composableBuilder(
    column: $table.accountUuid,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get importHash => $composableBuilder(
    column: $table.importHash,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get externalRef => $composableBuilder(
    column: $table.externalRef,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get importBatchId => $composableBuilder(
    column: $table.importBatchId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get accountLabel => $composableBuilder(
    column: $table.accountLabel,
    builder: (column) => ColumnFilters(column),
  );
}

class $$TransactionsTableOrderingComposer
    extends Composer<_$AppDatabase, $TransactionsTable> {
  $$TransactionsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get transactionType => $composableBuilder(
    column: $table.transactionType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get amountMinor => $composableBuilder(
    column: $table.amountMinor,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get category => $composableBuilder(
    column: $table.category,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get description => $composableBuilder(
    column: $table.description,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get transactionDate => $composableBuilder(
    column: $table.transactionDate,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get uuid => $composableBuilder(
    column: $table.uuid,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get createdAtMs => $composableBuilder(
    column: $table.createdAtMs,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get updatedAtMs => $composableBuilder(
    column: $table.updatedAtMs,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get deletedAtMs => $composableBuilder(
    column: $table.deletedAtMs,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get revision => $composableBuilder(
    column: $table.revision,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get originDeviceId => $composableBuilder(
    column: $table.originDeviceId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastModifiedBy => $composableBuilder(
    column: $table.lastModifiedBy,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncState => $composableBuilder(
    column: $table.syncState,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get accountUuid => $composableBuilder(
    column: $table.accountUuid,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get importHash => $composableBuilder(
    column: $table.importHash,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get externalRef => $composableBuilder(
    column: $table.externalRef,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get importBatchId => $composableBuilder(
    column: $table.importBatchId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get accountLabel => $composableBuilder(
    column: $table.accountLabel,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$TransactionsTableAnnotationComposer
    extends Composer<_$AppDatabase, $TransactionsTable> {
  $$TransactionsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get transactionType => $composableBuilder(
    column: $table.transactionType,
    builder: (column) => column,
  );

  GeneratedColumn<int> get amountMinor => $composableBuilder(
    column: $table.amountMinor,
    builder: (column) => column,
  );

  GeneratedColumn<String> get category =>
      $composableBuilder(column: $table.category, builder: (column) => column);

  GeneratedColumn<String> get description => $composableBuilder(
    column: $table.description,
    builder: (column) => column,
  );

  GeneratedColumn<String> get transactionDate => $composableBuilder(
    column: $table.transactionDate,
    builder: (column) => column,
  );

  GeneratedColumn<String> get uuid =>
      $composableBuilder(column: $table.uuid, builder: (column) => column);

  GeneratedColumn<int> get createdAtMs => $composableBuilder(
    column: $table.createdAtMs,
    builder: (column) => column,
  );

  GeneratedColumn<int> get updatedAtMs => $composableBuilder(
    column: $table.updatedAtMs,
    builder: (column) => column,
  );

  GeneratedColumn<int> get deletedAtMs => $composableBuilder(
    column: $table.deletedAtMs,
    builder: (column) => column,
  );

  GeneratedColumn<int> get revision =>
      $composableBuilder(column: $table.revision, builder: (column) => column);

  GeneratedColumn<String> get originDeviceId => $composableBuilder(
    column: $table.originDeviceId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get lastModifiedBy => $composableBuilder(
    column: $table.lastModifiedBy,
    builder: (column) => column,
  );

  GeneratedColumn<String> get syncState =>
      $composableBuilder(column: $table.syncState, builder: (column) => column);

  GeneratedColumn<String> get accountUuid => $composableBuilder(
    column: $table.accountUuid,
    builder: (column) => column,
  );

  GeneratedColumn<String> get importHash => $composableBuilder(
    column: $table.importHash,
    builder: (column) => column,
  );

  GeneratedColumn<String> get externalRef => $composableBuilder(
    column: $table.externalRef,
    builder: (column) => column,
  );

  GeneratedColumn<String> get importBatchId => $composableBuilder(
    column: $table.importBatchId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get accountLabel => $composableBuilder(
    column: $table.accountLabel,
    builder: (column) => column,
  );
}

class $$TransactionsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $TransactionsTable,
          Transaction,
          $$TransactionsTableFilterComposer,
          $$TransactionsTableOrderingComposer,
          $$TransactionsTableAnnotationComposer,
          $$TransactionsTableCreateCompanionBuilder,
          $$TransactionsTableUpdateCompanionBuilder,
          (
            Transaction,
            BaseReferences<_$AppDatabase, $TransactionsTable, Transaction>,
          ),
          Transaction,
          PrefetchHooks Function()
        > {
  $$TransactionsTableTableManager(_$AppDatabase db, $TransactionsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$TransactionsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$TransactionsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$TransactionsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> transactionType = const Value.absent(),
                Value<int> amountMinor = const Value.absent(),
                Value<String> category = const Value.absent(),
                Value<String?> description = const Value.absent(),
                Value<String> transactionDate = const Value.absent(),
                Value<String> uuid = const Value.absent(),
                Value<int> createdAtMs = const Value.absent(),
                Value<int> updatedAtMs = const Value.absent(),
                Value<int?> deletedAtMs = const Value.absent(),
                Value<int> revision = const Value.absent(),
                Value<String> originDeviceId = const Value.absent(),
                Value<String> lastModifiedBy = const Value.absent(),
                Value<String> syncState = const Value.absent(),
                Value<String> accountUuid = const Value.absent(),
                Value<String?> importHash = const Value.absent(),
                Value<String?> externalRef = const Value.absent(),
                Value<String?> importBatchId = const Value.absent(),
                Value<String?> accountLabel = const Value.absent(),
              }) => TransactionsCompanion(
                id: id,
                transactionType: transactionType,
                amountMinor: amountMinor,
                category: category,
                description: description,
                transactionDate: transactionDate,
                uuid: uuid,
                createdAtMs: createdAtMs,
                updatedAtMs: updatedAtMs,
                deletedAtMs: deletedAtMs,
                revision: revision,
                originDeviceId: originDeviceId,
                lastModifiedBy: lastModifiedBy,
                syncState: syncState,
                accountUuid: accountUuid,
                importHash: importHash,
                externalRef: externalRef,
                importBatchId: importBatchId,
                accountLabel: accountLabel,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String transactionType,
                required int amountMinor,
                required String category,
                Value<String?> description = const Value.absent(),
                required String transactionDate,
                required String uuid,
                required int createdAtMs,
                required int updatedAtMs,
                Value<int?> deletedAtMs = const Value.absent(),
                Value<int> revision = const Value.absent(),
                required String originDeviceId,
                required String lastModifiedBy,
                Value<String> syncState = const Value.absent(),
                required String accountUuid,
                Value<String?> importHash = const Value.absent(),
                Value<String?> externalRef = const Value.absent(),
                Value<String?> importBatchId = const Value.absent(),
                Value<String?> accountLabel = const Value.absent(),
              }) => TransactionsCompanion.insert(
                id: id,
                transactionType: transactionType,
                amountMinor: amountMinor,
                category: category,
                description: description,
                transactionDate: transactionDate,
                uuid: uuid,
                createdAtMs: createdAtMs,
                updatedAtMs: updatedAtMs,
                deletedAtMs: deletedAtMs,
                revision: revision,
                originDeviceId: originDeviceId,
                lastModifiedBy: lastModifiedBy,
                syncState: syncState,
                accountUuid: accountUuid,
                importHash: importHash,
                externalRef: externalRef,
                importBatchId: importBatchId,
                accountLabel: accountLabel,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$TransactionsTable, Transaction>(table),
                  BaseReferences<
                    _$AppDatabase,
                    $TransactionsTable,
                    Transaction
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$TransactionsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $TransactionsTable,
      Transaction,
      $$TransactionsTableFilterComposer,
      $$TransactionsTableOrderingComposer,
      $$TransactionsTableAnnotationComposer,
      $$TransactionsTableCreateCompanionBuilder,
      $$TransactionsTableUpdateCompanionBuilder,
      (
        Transaction,
        BaseReferences<_$AppDatabase, $TransactionsTable, Transaction>,
      ),
      Transaction,
      PrefetchHooks Function()
    >;
typedef $$SyncChangesTableCreateCompanionBuilder =
    SyncChangesCompanion Function({
      Value<int> seq,
      required String entityType,
      required String entityUuid,
      required String operation,
      Value<int?> baseRevision,
      Value<int?> newRevision,
      required String payload,
      required String originDeviceId,
      required int recordedAtMs,
      Value<int> payloadVersion,
    });
typedef $$SyncChangesTableUpdateCompanionBuilder =
    SyncChangesCompanion Function({
      Value<int> seq,
      Value<String> entityType,
      Value<String> entityUuid,
      Value<String> operation,
      Value<int?> baseRevision,
      Value<int?> newRevision,
      Value<String> payload,
      Value<String> originDeviceId,
      Value<int> recordedAtMs,
      Value<int> payloadVersion,
    });

class $$SyncChangesTableFilterComposer
    extends Composer<_$AppDatabase, $SyncChangesTable> {
  $$SyncChangesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get seq => $composableBuilder(
    column: $table.seq,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get entityUuid => $composableBuilder(
    column: $table.entityUuid,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get operation => $composableBuilder(
    column: $table.operation,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get baseRevision => $composableBuilder(
    column: $table.baseRevision,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get newRevision => $composableBuilder(
    column: $table.newRevision,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get payload => $composableBuilder(
    column: $table.payload,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get originDeviceId => $composableBuilder(
    column: $table.originDeviceId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get recordedAtMs => $composableBuilder(
    column: $table.recordedAtMs,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get payloadVersion => $composableBuilder(
    column: $table.payloadVersion,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SyncChangesTableOrderingComposer
    extends Composer<_$AppDatabase, $SyncChangesTable> {
  $$SyncChangesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get seq => $composableBuilder(
    column: $table.seq,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get entityUuid => $composableBuilder(
    column: $table.entityUuid,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get operation => $composableBuilder(
    column: $table.operation,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get baseRevision => $composableBuilder(
    column: $table.baseRevision,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get newRevision => $composableBuilder(
    column: $table.newRevision,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get payload => $composableBuilder(
    column: $table.payload,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get originDeviceId => $composableBuilder(
    column: $table.originDeviceId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get recordedAtMs => $composableBuilder(
    column: $table.recordedAtMs,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get payloadVersion => $composableBuilder(
    column: $table.payloadVersion,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SyncChangesTableAnnotationComposer
    extends Composer<_$AppDatabase, $SyncChangesTable> {
  $$SyncChangesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get seq =>
      $composableBuilder(column: $table.seq, builder: (column) => column);

  GeneratedColumn<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => column,
  );

  GeneratedColumn<String> get entityUuid => $composableBuilder(
    column: $table.entityUuid,
    builder: (column) => column,
  );

  GeneratedColumn<String> get operation =>
      $composableBuilder(column: $table.operation, builder: (column) => column);

  GeneratedColumn<int> get baseRevision => $composableBuilder(
    column: $table.baseRevision,
    builder: (column) => column,
  );

  GeneratedColumn<int> get newRevision => $composableBuilder(
    column: $table.newRevision,
    builder: (column) => column,
  );

  GeneratedColumn<String> get payload =>
      $composableBuilder(column: $table.payload, builder: (column) => column);

  GeneratedColumn<String> get originDeviceId => $composableBuilder(
    column: $table.originDeviceId,
    builder: (column) => column,
  );

  GeneratedColumn<int> get recordedAtMs => $composableBuilder(
    column: $table.recordedAtMs,
    builder: (column) => column,
  );

  GeneratedColumn<int> get payloadVersion => $composableBuilder(
    column: $table.payloadVersion,
    builder: (column) => column,
  );
}

class $$SyncChangesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SyncChangesTable,
          SyncChange,
          $$SyncChangesTableFilterComposer,
          $$SyncChangesTableOrderingComposer,
          $$SyncChangesTableAnnotationComposer,
          $$SyncChangesTableCreateCompanionBuilder,
          $$SyncChangesTableUpdateCompanionBuilder,
          (
            SyncChange,
            BaseReferences<_$AppDatabase, $SyncChangesTable, SyncChange>,
          ),
          SyncChange,
          PrefetchHooks Function()
        > {
  $$SyncChangesTableTableManager(_$AppDatabase db, $SyncChangesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SyncChangesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SyncChangesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SyncChangesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> seq = const Value.absent(),
                Value<String> entityType = const Value.absent(),
                Value<String> entityUuid = const Value.absent(),
                Value<String> operation = const Value.absent(),
                Value<int?> baseRevision = const Value.absent(),
                Value<int?> newRevision = const Value.absent(),
                Value<String> payload = const Value.absent(),
                Value<String> originDeviceId = const Value.absent(),
                Value<int> recordedAtMs = const Value.absent(),
                Value<int> payloadVersion = const Value.absent(),
              }) => SyncChangesCompanion(
                seq: seq,
                entityType: entityType,
                entityUuid: entityUuid,
                operation: operation,
                baseRevision: baseRevision,
                newRevision: newRevision,
                payload: payload,
                originDeviceId: originDeviceId,
                recordedAtMs: recordedAtMs,
                payloadVersion: payloadVersion,
              ),
          createCompanionCallback:
              ({
                Value<int> seq = const Value.absent(),
                required String entityType,
                required String entityUuid,
                required String operation,
                Value<int?> baseRevision = const Value.absent(),
                Value<int?> newRevision = const Value.absent(),
                required String payload,
                required String originDeviceId,
                required int recordedAtMs,
                Value<int> payloadVersion = const Value.absent(),
              }) => SyncChangesCompanion.insert(
                seq: seq,
                entityType: entityType,
                entityUuid: entityUuid,
                operation: operation,
                baseRevision: baseRevision,
                newRevision: newRevision,
                payload: payload,
                originDeviceId: originDeviceId,
                recordedAtMs: recordedAtMs,
                payloadVersion: payloadVersion,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$SyncChangesTable, SyncChange>(table),
                  BaseReferences<_$AppDatabase, $SyncChangesTable, SyncChange>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SyncChangesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SyncChangesTable,
      SyncChange,
      $$SyncChangesTableFilterComposer,
      $$SyncChangesTableOrderingComposer,
      $$SyncChangesTableAnnotationComposer,
      $$SyncChangesTableCreateCompanionBuilder,
      $$SyncChangesTableUpdateCompanionBuilder,
      (
        SyncChange,
        BaseReferences<_$AppDatabase, $SyncChangesTable, SyncChange>,
      ),
      SyncChange,
      PrefetchHooks Function()
    >;
typedef $$SyncPeersTableCreateCompanionBuilder = SyncPeersCompanion Function({
  required String peerDeviceId,
  Value<int> lastAppliedSeq,
  Value<int> lastSentSeq,
  Value<int?> lastSyncAtMs,
  Value<int> rowid,
});
typedef $$SyncPeersTableUpdateCompanionBuilder = SyncPeersCompanion Function({
  Value<String> peerDeviceId,
  Value<int> lastAppliedSeq,
  Value<int> lastSentSeq,
  Value<int?> lastSyncAtMs,
  Value<int> rowid,
});

class $$SyncPeersTableFilterComposer
    extends Composer<_$AppDatabase, $SyncPeersTable> {
  $$SyncPeersTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get peerDeviceId => $composableBuilder(
    column: $table.peerDeviceId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get lastAppliedSeq => $composableBuilder(
    column: $table.lastAppliedSeq,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get lastSentSeq => $composableBuilder(
    column: $table.lastSentSeq,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get lastSyncAtMs => $composableBuilder(
    column: $table.lastSyncAtMs,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SyncPeersTableOrderingComposer
    extends Composer<_$AppDatabase, $SyncPeersTable> {
  $$SyncPeersTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get peerDeviceId => $composableBuilder(
    column: $table.peerDeviceId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get lastAppliedSeq => $composableBuilder(
    column: $table.lastAppliedSeq,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get lastSentSeq => $composableBuilder(
    column: $table.lastSentSeq,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get lastSyncAtMs => $composableBuilder(
    column: $table.lastSyncAtMs,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SyncPeersTableAnnotationComposer
    extends Composer<_$AppDatabase, $SyncPeersTable> {
  $$SyncPeersTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get peerDeviceId => $composableBuilder(
    column: $table.peerDeviceId,
    builder: (column) => column,
  );

  GeneratedColumn<int> get lastAppliedSeq => $composableBuilder(
    column: $table.lastAppliedSeq,
    builder: (column) => column,
  );

  GeneratedColumn<int> get lastSentSeq => $composableBuilder(
    column: $table.lastSentSeq,
    builder: (column) => column,
  );

  GeneratedColumn<int> get lastSyncAtMs => $composableBuilder(
    column: $table.lastSyncAtMs,
    builder: (column) => column,
  );
}

class $$SyncPeersTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SyncPeersTable,
          SyncPeer,
          $$SyncPeersTableFilterComposer,
          $$SyncPeersTableOrderingComposer,
          $$SyncPeersTableAnnotationComposer,
          $$SyncPeersTableCreateCompanionBuilder,
          $$SyncPeersTableUpdateCompanionBuilder,
          (SyncPeer, BaseReferences<_$AppDatabase, $SyncPeersTable, SyncPeer>),
          SyncPeer,
          PrefetchHooks Function()
        > {
  $$SyncPeersTableTableManager(_$AppDatabase db, $SyncPeersTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SyncPeersTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SyncPeersTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SyncPeersTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> peerDeviceId = const Value.absent(),
                Value<int> lastAppliedSeq = const Value.absent(),
                Value<int> lastSentSeq = const Value.absent(),
                Value<int?> lastSyncAtMs = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SyncPeersCompanion(
                peerDeviceId: peerDeviceId,
                lastAppliedSeq: lastAppliedSeq,
                lastSentSeq: lastSentSeq,
                lastSyncAtMs: lastSyncAtMs,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String peerDeviceId,
                Value<int> lastAppliedSeq = const Value.absent(),
                Value<int> lastSentSeq = const Value.absent(),
                Value<int?> lastSyncAtMs = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SyncPeersCompanion.insert(
                peerDeviceId: peerDeviceId,
                lastAppliedSeq: lastAppliedSeq,
                lastSentSeq: lastSentSeq,
                lastSyncAtMs: lastSyncAtMs,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$SyncPeersTable, SyncPeer>(table),
                  BaseReferences<_$AppDatabase, $SyncPeersTable, SyncPeer>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SyncPeersTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SyncPeersTable,
      SyncPeer,
      $$SyncPeersTableFilterComposer,
      $$SyncPeersTableOrderingComposer,
      $$SyncPeersTableAnnotationComposer,
      $$SyncPeersTableCreateCompanionBuilder,
      $$SyncPeersTableUpdateCompanionBuilder,
      (SyncPeer, BaseReferences<_$AppDatabase, $SyncPeersTable, SyncPeer>),
      SyncPeer,
      PrefetchHooks Function()
    >;
typedef $$SyncConflictsTableCreateCompanionBuilder =
    SyncConflictsCompanion Function({
      required String conflictId,
      required String entityUuid,
      Value<String?> peerDeviceId,
      Value<String?> localPayload,
      Value<String?> remotePayload,
      required String resolution,
      required int detectedAtMs,
      Value<int> rowid,
    });
typedef $$SyncConflictsTableUpdateCompanionBuilder =
    SyncConflictsCompanion Function({
      Value<String> conflictId,
      Value<String> entityUuid,
      Value<String?> peerDeviceId,
      Value<String?> localPayload,
      Value<String?> remotePayload,
      Value<String> resolution,
      Value<int> detectedAtMs,
      Value<int> rowid,
    });

class $$SyncConflictsTableFilterComposer
    extends Composer<_$AppDatabase, $SyncConflictsTable> {
  $$SyncConflictsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get conflictId => $composableBuilder(
    column: $table.conflictId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get entityUuid => $composableBuilder(
    column: $table.entityUuid,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get peerDeviceId => $composableBuilder(
    column: $table.peerDeviceId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get localPayload => $composableBuilder(
    column: $table.localPayload,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get remotePayload => $composableBuilder(
    column: $table.remotePayload,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get resolution => $composableBuilder(
    column: $table.resolution,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get detectedAtMs => $composableBuilder(
    column: $table.detectedAtMs,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SyncConflictsTableOrderingComposer
    extends Composer<_$AppDatabase, $SyncConflictsTable> {
  $$SyncConflictsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get conflictId => $composableBuilder(
    column: $table.conflictId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get entityUuid => $composableBuilder(
    column: $table.entityUuid,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get peerDeviceId => $composableBuilder(
    column: $table.peerDeviceId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get localPayload => $composableBuilder(
    column: $table.localPayload,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get remotePayload => $composableBuilder(
    column: $table.remotePayload,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get resolution => $composableBuilder(
    column: $table.resolution,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get detectedAtMs => $composableBuilder(
    column: $table.detectedAtMs,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SyncConflictsTableAnnotationComposer
    extends Composer<_$AppDatabase, $SyncConflictsTable> {
  $$SyncConflictsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get conflictId => $composableBuilder(
    column: $table.conflictId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get entityUuid => $composableBuilder(
    column: $table.entityUuid,
    builder: (column) => column,
  );

  GeneratedColumn<String> get peerDeviceId => $composableBuilder(
    column: $table.peerDeviceId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get localPayload => $composableBuilder(
    column: $table.localPayload,
    builder: (column) => column,
  );

  GeneratedColumn<String> get remotePayload => $composableBuilder(
    column: $table.remotePayload,
    builder: (column) => column,
  );

  GeneratedColumn<String> get resolution => $composableBuilder(
    column: $table.resolution,
    builder: (column) => column,
  );

  GeneratedColumn<int> get detectedAtMs => $composableBuilder(
    column: $table.detectedAtMs,
    builder: (column) => column,
  );
}

class $$SyncConflictsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SyncConflictsTable,
          SyncConflict,
          $$SyncConflictsTableFilterComposer,
          $$SyncConflictsTableOrderingComposer,
          $$SyncConflictsTableAnnotationComposer,
          $$SyncConflictsTableCreateCompanionBuilder,
          $$SyncConflictsTableUpdateCompanionBuilder,
          (
            SyncConflict,
            BaseReferences<_$AppDatabase, $SyncConflictsTable, SyncConflict>,
          ),
          SyncConflict,
          PrefetchHooks Function()
        > {
  $$SyncConflictsTableTableManager(_$AppDatabase db, $SyncConflictsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SyncConflictsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SyncConflictsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SyncConflictsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> conflictId = const Value.absent(),
                Value<String> entityUuid = const Value.absent(),
                Value<String?> peerDeviceId = const Value.absent(),
                Value<String?> localPayload = const Value.absent(),
                Value<String?> remotePayload = const Value.absent(),
                Value<String> resolution = const Value.absent(),
                Value<int> detectedAtMs = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SyncConflictsCompanion(
                conflictId: conflictId,
                entityUuid: entityUuid,
                peerDeviceId: peerDeviceId,
                localPayload: localPayload,
                remotePayload: remotePayload,
                resolution: resolution,
                detectedAtMs: detectedAtMs,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String conflictId,
                required String entityUuid,
                Value<String?> peerDeviceId = const Value.absent(),
                Value<String?> localPayload = const Value.absent(),
                Value<String?> remotePayload = const Value.absent(),
                required String resolution,
                required int detectedAtMs,
                Value<int> rowid = const Value.absent(),
              }) => SyncConflictsCompanion.insert(
                conflictId: conflictId,
                entityUuid: entityUuid,
                peerDeviceId: peerDeviceId,
                localPayload: localPayload,
                remotePayload: remotePayload,
                resolution: resolution,
                detectedAtMs: detectedAtMs,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$SyncConflictsTable, SyncConflict>(table),
                  BaseReferences<
                    _$AppDatabase,
                    $SyncConflictsTable,
                    SyncConflict
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SyncConflictsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SyncConflictsTable,
      SyncConflict,
      $$SyncConflictsTableFilterComposer,
      $$SyncConflictsTableOrderingComposer,
      $$SyncConflictsTableAnnotationComposer,
      $$SyncConflictsTableCreateCompanionBuilder,
      $$SyncConflictsTableUpdateCompanionBuilder,
      (
        SyncConflict,
        BaseReferences<_$AppDatabase, $SyncConflictsTable, SyncConflict>,
      ),
      SyncConflict,
      PrefetchHooks Function()
    >;
typedef $$ImportBatchesTableCreateCompanionBuilder =
    ImportBatchesCompanion Function({
      required String batchId,
      Value<String?> sourceFile,
      Value<String?> sourceType,
      Value<String?> bankFormat,
      required int importedAtMs,
      Value<int> importedCount,
      Value<int> skippedCount,
      Value<String?> deviceId,
      Value<int> rowid,
    });
typedef $$ImportBatchesTableUpdateCompanionBuilder =
    ImportBatchesCompanion Function({
      Value<String> batchId,
      Value<String?> sourceFile,
      Value<String?> sourceType,
      Value<String?> bankFormat,
      Value<int> importedAtMs,
      Value<int> importedCount,
      Value<int> skippedCount,
      Value<String?> deviceId,
      Value<int> rowid,
    });

class $$ImportBatchesTableFilterComposer
    extends Composer<_$AppDatabase, $ImportBatchesTable> {
  $$ImportBatchesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get batchId => $composableBuilder(
    column: $table.batchId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sourceFile => $composableBuilder(
    column: $table.sourceFile,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sourceType => $composableBuilder(
    column: $table.sourceType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get bankFormat => $composableBuilder(
    column: $table.bankFormat,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get importedAtMs => $composableBuilder(
    column: $table.importedAtMs,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get importedCount => $composableBuilder(
    column: $table.importedCount,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get skippedCount => $composableBuilder(
    column: $table.skippedCount,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get deviceId => $composableBuilder(
    column: $table.deviceId,
    builder: (column) => ColumnFilters(column),
  );
}

class $$ImportBatchesTableOrderingComposer
    extends Composer<_$AppDatabase, $ImportBatchesTable> {
  $$ImportBatchesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get batchId => $composableBuilder(
    column: $table.batchId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sourceFile => $composableBuilder(
    column: $table.sourceFile,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sourceType => $composableBuilder(
    column: $table.sourceType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get bankFormat => $composableBuilder(
    column: $table.bankFormat,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get importedAtMs => $composableBuilder(
    column: $table.importedAtMs,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get importedCount => $composableBuilder(
    column: $table.importedCount,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get skippedCount => $composableBuilder(
    column: $table.skippedCount,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get deviceId => $composableBuilder(
    column: $table.deviceId,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$ImportBatchesTableAnnotationComposer
    extends Composer<_$AppDatabase, $ImportBatchesTable> {
  $$ImportBatchesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get batchId =>
      $composableBuilder(column: $table.batchId, builder: (column) => column);

  GeneratedColumn<String> get sourceFile => $composableBuilder(
    column: $table.sourceFile,
    builder: (column) => column,
  );

  GeneratedColumn<String> get sourceType => $composableBuilder(
    column: $table.sourceType,
    builder: (column) => column,
  );

  GeneratedColumn<String> get bankFormat => $composableBuilder(
    column: $table.bankFormat,
    builder: (column) => column,
  );

  GeneratedColumn<int> get importedAtMs => $composableBuilder(
    column: $table.importedAtMs,
    builder: (column) => column,
  );

  GeneratedColumn<int> get importedCount => $composableBuilder(
    column: $table.importedCount,
    builder: (column) => column,
  );

  GeneratedColumn<int> get skippedCount => $composableBuilder(
    column: $table.skippedCount,
    builder: (column) => column,
  );

  GeneratedColumn<String> get deviceId =>
      $composableBuilder(column: $table.deviceId, builder: (column) => column);
}

class $$ImportBatchesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $ImportBatchesTable,
          ImportBatche,
          $$ImportBatchesTableFilterComposer,
          $$ImportBatchesTableOrderingComposer,
          $$ImportBatchesTableAnnotationComposer,
          $$ImportBatchesTableCreateCompanionBuilder,
          $$ImportBatchesTableUpdateCompanionBuilder,
          (
            ImportBatche,
            BaseReferences<_$AppDatabase, $ImportBatchesTable, ImportBatche>,
          ),
          ImportBatche,
          PrefetchHooks Function()
        > {
  $$ImportBatchesTableTableManager(_$AppDatabase db, $ImportBatchesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ImportBatchesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ImportBatchesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ImportBatchesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> batchId = const Value.absent(),
                Value<String?> sourceFile = const Value.absent(),
                Value<String?> sourceType = const Value.absent(),
                Value<String?> bankFormat = const Value.absent(),
                Value<int> importedAtMs = const Value.absent(),
                Value<int> importedCount = const Value.absent(),
                Value<int> skippedCount = const Value.absent(),
                Value<String?> deviceId = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => ImportBatchesCompanion(
                batchId: batchId,
                sourceFile: sourceFile,
                sourceType: sourceType,
                bankFormat: bankFormat,
                importedAtMs: importedAtMs,
                importedCount: importedCount,
                skippedCount: skippedCount,
                deviceId: deviceId,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String batchId,
                Value<String?> sourceFile = const Value.absent(),
                Value<String?> sourceType = const Value.absent(),
                Value<String?> bankFormat = const Value.absent(),
                required int importedAtMs,
                Value<int> importedCount = const Value.absent(),
                Value<int> skippedCount = const Value.absent(),
                Value<String?> deviceId = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => ImportBatchesCompanion.insert(
                batchId: batchId,
                sourceFile: sourceFile,
                sourceType: sourceType,
                bankFormat: bankFormat,
                importedAtMs: importedAtMs,
                importedCount: importedCount,
                skippedCount: skippedCount,
                deviceId: deviceId,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$ImportBatchesTable, ImportBatche>(table),
                  BaseReferences<
                    _$AppDatabase,
                    $ImportBatchesTable,
                    ImportBatche
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$ImportBatchesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $ImportBatchesTable,
      ImportBatche,
      $$ImportBatchesTableFilterComposer,
      $$ImportBatchesTableOrderingComposer,
      $$ImportBatchesTableAnnotationComposer,
      $$ImportBatchesTableCreateCompanionBuilder,
      $$ImportBatchesTableUpdateCompanionBuilder,
      (
        ImportBatche,
        BaseReferences<_$AppDatabase, $ImportBatchesTable, ImportBatche>,
      ),
      ImportBatche,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$AppMetaTableTableManager get appMeta =>
      $$AppMetaTableTableManager(_db, _db.appMeta);
  $$DevicesTableTableManager get devices =>
      $$DevicesTableTableManager(_db, _db.devices);
  $$AccountsTableTableManager get accounts =>
      $$AccountsTableTableManager(_db, _db.accounts);
  $$TransactionsTableTableManager get transactions =>
      $$TransactionsTableTableManager(_db, _db.transactions);
  $$SyncChangesTableTableManager get syncChanges =>
      $$SyncChangesTableTableManager(_db, _db.syncChanges);
  $$SyncPeersTableTableManager get syncPeers =>
      $$SyncPeersTableTableManager(_db, _db.syncPeers);
  $$SyncConflictsTableTableManager get syncConflicts =>
      $$SyncConflictsTableTableManager(_db, _db.syncConflicts);
  $$ImportBatchesTableTableManager get importBatches =>
      $$ImportBatchesTableTableManager(_db, _db.importBatches);
}
