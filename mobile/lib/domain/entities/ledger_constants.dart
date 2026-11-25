/// Values that must stay compatible with the desktop schema v4 database.
abstract final class LedgerConstants {
  static const int schemaVersion = 4;
  static const String databaseFileName = 'pocket_ledger_mobile.db';
  static const String defaultAccountUuid =
      'dff7dc53-25f6-5624-a477-cc7c569910f2';
  static const String defaultAccountName = 'Default INR account';
  static const String defaultCurrencyCode = 'INR';
  static const String androidPlatform = 'android';
  static const String appMetaDeviceIdKey = 'local_device_id';
  static const String appMetaDeviceNameKey = 'device_name';
  static const String appMetaDevicePlatformKey = 'device_platform';
}
