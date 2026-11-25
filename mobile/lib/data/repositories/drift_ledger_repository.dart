import 'package:pocket_ledger_mobile/data/database/daos/ledger_dao.dart';
import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/category.dart';
import 'package:pocket_ledger_mobile/domain/entities/csv_import.dart';
import 'package:pocket_ledger_mobile/domain/entities/dashboard_summary.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction_filter.dart';
import 'package:pocket_ledger_mobile/domain/repositories/ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/validation_exception.dart';
import 'package:pocket_ledger_mobile/domain/validators/input_validators.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

class DriftLedgerRepository implements LedgerRepository {
  DriftLedgerRepository(this._dao);

  final LedgerDao _dao;

  @override
  Future<void> ensureBootstrapped() => _dao.ensureBootstrapped();

  @override
  Future<Uuid> deviceId() => _dao.deviceId();

  @override
  Future<Account?> defaultAccount() => _dao.defaultAccount();

  @override
  Stream<Account?> watchDefaultAccount() => _dao.watchDefaultAccount();

  @override
  Stream<List<Account>> watchAccounts() => _dao.watchAccounts();

  @override
  Stream<List<LedgerTransaction>> watchLiveTransactions() =>
      _dao.watchLiveTransactions();

  @override
  Stream<List<LedgerTransaction>> watchTransactions(
    TransactionFilter filter, {
    int limit = 50,
  }) =>
      _dao.watchTransactions(filter, limit: limit);

  @override
  Stream<Map<String, int>> watchAccountDeltas() => _dao.watchAccountDeltas();

  @override
  Stream<DashboardAggregateData> watchDashboardAggregate({
    required DateTime month,
    required String chartCurrencyCode,
  }) {
    return _dao.watchDashboardAggregate(
      month: month,
      chartCurrencyCode: chartCurrencyCode,
    );
  }

  @override
  Future<LedgerTransaction?> transactionById(int id) =>
      _dao.transactionById(id);

  @override
  Future<LedgerSettings> settings() => _dao.settings();

  @override
  Stream<LedgerSettings> watchSettings() => _dao.watchSettings();

  @override
  Future<void> updateSettings(LedgerSettings settings) =>
      _dao.writeSettings(settings);

  @override
  Future<List<LedgerCategory>> categories() => _dao.categories();

  @override
  Stream<List<LedgerCategory>> watchCategories() => _dao.watchCategories();

  @override
  Future<void> saveCategories(List<LedgerCategory> categories) =>
      _dao.saveCategories(categories);

  @override
  Future<Map<String, int>> openingBalances() => _dao.openingBalances();

  @override
  Stream<Map<String, int>> watchOpeningBalances() =>
      _dao.watchOpeningBalances();

  @override
  Future<Map<String, int>> transactionTimes() => _dao.transactionTimes();

  @override
  Stream<Map<String, int>> transactionTimesStream() =>
      _dao.transactionTimesStream();

  @override
  Future<Uuid> createAccount({
    required String name,
    required CurrencyCode currencyCode,
    int openingMinor = 0,
    bool isDefault = false,
  }) {
    return _dao.insertAccount(
      name: name,
      currencyCode: currencyCode,
      openingMinor: openingMinor,
      isDefault: isDefault,
    );
  }

  @override
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
  }) async {
    final account = await _resolveAccount(accountUuid);

    // Manual entry is strict by default: no silent rounding and no float input.
    final minor = MinorAmount.positive(
      amount,
      account.precision,
      strict: !roundAmounts,
    );
    final cleanCategory = InputValidators.requiredText(category, 'Category');
    final cleanDate = InputValidators.isoDate(transactionDate);

    return _dao.insertTransaction(
      type: type,
      amountMinor: minor.minor,
      accountUuid: account.uuid,
      category: cleanCategory,
      transactionDate: cleanDate,
      description: InputValidators.optionalText(description),
      importHash: InputValidators.optionalText(importHash),
      externalRef: InputValidators.optionalText(externalRef),
      importBatchId: InputValidators.optionalText(importBatchId),
      accountLabel: InputValidators.optionalText(accountLabel),
      transactionTimeMs: transactionTimeMs,
    );
  }

  @override
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
  }) async {
    final account = await _dao.accountByUuid(accountUuid);
    if (account == null) {
      throw const DomainValidationException('No live account is available.');
    }
    final minor = MinorAmount.positive(
      amount,
      account.precision,
      strict: !roundAmounts,
    );
    await _dao.updateTransaction(
      id: id,
      type: type,
      amountMinor: minor.minor,
      accountUuid: accountUuid,
      category: InputValidators.requiredText(category, 'Category'),
      transactionDate: InputValidators.isoDate(transactionDate),
      description: InputValidators.optionalText(description),
      transactionTimeMs: transactionTimeMs,
    );
  }

  @override
  Future<void> renameAccount(Uuid accountUuid, String name) =>
      _dao.renameAccount(accountUuid, name);

  @override
  Future<void> setDefaultAccount(Uuid accountUuid) =>
      _dao.setDefaultAccount(accountUuid);

  @override
  Future<void> softDeleteAccount(Uuid accountUuid, {required bool cascade}) =>
      _dao.softDeleteAccount(accountUuid, cascade: cascade);

  @override
  Future<void> softDeleteTransaction(int id) =>
      _dao.softDeleteTransaction(id);

  @override
  Future<void> restoreTransaction(int id) => _dao.restoreTransaction(id);

  @override
  Future<void> softDeleteTransactions(List<int> ids) =>
      _dao.softDeleteTransactions(ids);

  @override
  Future<void> restoreTransactions(List<int> ids) =>
      _dao.restoreTransactions(ids);

  @override
  Future<Map<String, Set<String>>> importHashes() => _dao.importHashes();

  @override
  Future<void> importRows(
    List<ParsedCsvRow> rows, {
    required String sourceFile,
  }) =>
      _dao.importRows(rows, sourceFile: sourceFile);

  @override
  Future<void> deleteAllData() => _dao.deleteAllData();

  @override
  Future<UtcMs> now() async => UtcMs.now();

  Future<Account> _resolveAccount(Uuid? accountUuid) async {
    final account = accountUuid == null
        ? await defaultAccount()
        : await _dao.accountByUuid(accountUuid);
    if (account == null) {
      throw const DomainValidationException('No live account is available.');
    }
    return account;
  }
}
