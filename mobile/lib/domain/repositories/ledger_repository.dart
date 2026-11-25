import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/category.dart';
import 'package:pocket_ledger_mobile/domain/entities/csv_import.dart';
import 'package:pocket_ledger_mobile/domain/entities/dashboard_summary.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction_filter.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

/// Domain-facing contract. Implementations own local persistence and outbox.
abstract interface class LedgerRepository {
  /// Ensures the Android device identity and deterministic default account exist.
  Future<void> ensureBootstrapped();

  Future<Uuid> deviceId();

  Future<Account?> defaultAccount();

  Stream<Account?> watchDefaultAccount();

  Stream<List<Account>> watchAccounts();

  Stream<List<LedgerTransaction>> watchLiveTransactions();

  Stream<List<LedgerTransaction>> watchTransactions(
    TransactionFilter filter, {
    int limit = 50,
  });

  /// SQL-computed signed deltas, keyed by account UUID.
  Stream<Map<String, int>> watchAccountDeltas();

  /// SQL-computed dashboard inputs. No transaction rows are aggregated in Dart.
  Stream<DashboardAggregateData> watchDashboardAggregate({
    required DateTime month,
    required String chartCurrencyCode,
  });

  Future<LedgerTransaction?> transactionById(int id);

  Future<LedgerSettings> settings();

  Stream<LedgerSettings> watchSettings();

  Future<void> updateSettings(LedgerSettings settings);

  Future<List<LedgerCategory>> categories();

  Stream<List<LedgerCategory>> watchCategories();

  Future<void> saveCategories(List<LedgerCategory> categories);

  Future<Map<String, int>> openingBalances();

  Stream<Map<String, int>> watchOpeningBalances();

  Future<Map<String, int>> transactionTimes();

  Stream<Map<String, int>> transactionTimesStream();

  Future<Uuid> createAccount({
    required String name,
    required CurrencyCode currencyCode,
    int openingMinor = 0,
    bool isDefault = false,
  });

  Future<int> addTransaction({
    required TransactionType type,
    required Object amount,
    required String category,
    required String transactionDate,
    Uuid? accountUuid,
    String? description,
    String? importHash,
    String? externalRef,
    String? importBatchId,
    String? accountLabel,
    int? transactionTimeMs,
    bool roundAmounts = false,
  });

  Future<void> updateTransaction({
    required int id,
    required TransactionType type,
    required Object amount,
    required String category,
    required String transactionDate,
    required Uuid accountUuid,
    String? description,
    int? transactionTimeMs,
    bool roundAmounts = false,
  });

  Future<void> renameAccount(Uuid accountUuid, String name);

  Future<void> setDefaultAccount(Uuid accountUuid);

  /// Soft-deletes an account. [cascade] must be true when transactions exist.
  Future<void> softDeleteAccount(Uuid accountUuid, {required bool cascade});

  /// Marks a transaction deleted without removing the row.
  Future<void> softDeleteTransaction(int id);

  Future<void> restoreTransaction(int id);

  Future<void> softDeleteTransactions(List<int> ids);

  Future<void> restoreTransactions(List<int> ids);

  /// Existing live import hashes mapped to the account UUIDs that hold them.
  /// Desktop scopes uniqueness to `(account_uuid, import_hash)`.
  Future<Map<String, Set<String>>> importHashes();

  /// Commits all prepared rows, their outbox events and the batch row together.
  Future<void> importRows(
    List<ParsedCsvRow> rows, {
    required String sourceFile,
  });

  /// Soft-deletes all live data and resets mobile-only preferences. The device
  /// identity, outbox and historical rows are preserved.
  Future<void> deleteAllData();

  Future<UtcMs> now();
}
