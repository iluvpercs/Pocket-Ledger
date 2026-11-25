import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';

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

/// Mobile-only keys stored in the same desktop-compatible `app_meta` table.
/// No v4 columns or tables are added.
abstract final class MobileMetaKeys {
  static const String defaultCurrency = 'mobile.default_currency';
  static const String defaultAccountUuid = 'mobile.default_account_uuid';
  static const String dateFormat = 'mobile.date_format';
  static const String themeMode = 'mobile.theme_mode';
  static const String categories = 'mobile.categories';
  static const String openingBalancePrefix = 'mobile.opening_balance.';
  static const String transactionTimePrefix = 'mobile.transaction_time.';

  static String openingBalance(Uuid accountUuid) =>
      '$openingBalancePrefix${accountUuid.value}';

  static String transactionTime(Uuid transactionUuid) =>
      '$transactionTimePrefix${transactionUuid.value}';
}
