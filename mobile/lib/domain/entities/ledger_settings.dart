import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';

/// Local-only preferences persisted in the existing `app_meta` table.
final class LedgerSettings {
  const LedgerSettings({
    required this.defaultCurrencyCode,
    this.defaultAccountUuid,
    required this.dateFormat,
    required this.themeMode,
  });

  final CurrencyCode defaultCurrencyCode;
  final Uuid? defaultAccountUuid;
  final LedgerDateFormat dateFormat;
  final LedgerThemeMode themeMode;

  LedgerSettings copyWith({
    CurrencyCode? defaultCurrencyCode,
    Uuid? defaultAccountUuid,
    bool clearDefaultAccount = false,
    LedgerDateFormat? dateFormat,
    LedgerThemeMode? themeMode,
  }) {
    return LedgerSettings(
      defaultCurrencyCode: defaultCurrencyCode ?? this.defaultCurrencyCode,
      defaultAccountUuid: clearDefaultAccount
          ? null
          : defaultAccountUuid ?? this.defaultAccountUuid,
      dateFormat: dateFormat ?? this.dateFormat,
      themeMode: themeMode ?? this.themeMode,
    );
  }
}

enum LedgerDateFormat {
  iso('iso', 'yyyy-MM-dd', 'YYYY-MM-DD'),
  slashDmy('slash_dmy', 'dd/MM/yyyy', 'DD/MM/YYYY'),
  dashDmy('dash_dmy', 'dd-MM-yyyy', 'DD-MM-YYYY'),
  shortDmy('short_dmy', 'dd/MM/yy', 'DD/MM/YY'),
  shortMonth('short_month', 'dd-MMM-yyyy', 'DD-Mon-YYYY'),
  longMonth('long_month', 'dd-MMMM-yyyy', 'DD-Month-YYYY'),
  spacedShortMonth('spaced_short_month', 'dd MMM yyyy', 'DD Mon YYYY'),
  spacedLongMonth('spaced_long_month', 'dd MMMM yyyy', 'DD Month YYYY');

  const LedgerDateFormat(this.id, this.pattern, this.label);

  final String id;
  final String pattern;
  final String label;

  static LedgerDateFormat fromId(String? id) {
    for (final format in values) {
      if (format.id == id) return format;
    }
    return LedgerDateFormat.iso;
  }
}

enum LedgerThemeMode {
  dark('dark'),
  system('system');

  const LedgerThemeMode(this.id);

  final String id;

  static LedgerThemeMode fromId(String? id) {
    for (final mode in values) {
      if (mode.id == id) return mode;
    }
    return LedgerThemeMode.dark;
  }
}
