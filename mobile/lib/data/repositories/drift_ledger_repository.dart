import 'package:pocket_ledger_mobile/data/database/daos/ledger_dao.dart';
import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/repositories/ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/validation_exception.dart';
import 'package:pocket_ledger_mobile/domain/validators/input_validators.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

class DriftLedgerRepository implements LedgerRepository {
  DriftLedgerRepository(this._dao);

  final LedgerDao _dao;

  @override
  Future<void> ensureBootstrapped() => _dao.ensureBootstrapped();

  @override
  Future<Account?> defaultAccount() => _dao.defaultAccount();

  @override
  Stream<Account?> watchDefaultAccount() => _dao.watchDefaultAccount();

  @override
  Future<Uuid> createAccount({
    required String name,
    required CurrencyCode currencyCode,
    bool isDefault = false,
  }) {
    return _dao.insertAccount(
      name: name,
      currencyCode: currencyCode,
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
  }) async {
    final account = accountUuid == null
        ? await defaultAccount()
        : await _dao.accountByUuid(accountUuid);
    if (account == null) {
      throw const DomainValidationException('No live account is available.');
    }

    // Manual entry is strict: no silent rounding and no binary float input.
    final minor = MinorAmount.positive(amount, account.precision);
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
    );
  }

  @override
  Future<void> renameAccount(Uuid accountUuid, String name) =>
      _dao.renameAccount(accountUuid, name);

  @override
  Future<void> softDeleteTransaction(int id) =>
      _dao.softDeleteTransaction(id);
}
