import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

/// Domain-facing contract. Implementations own local persistence and outbox.
abstract interface class LedgerRepository {
  /// Ensures the Android device identity and deterministic default account exist.
  Future<void> ensureBootstrapped();

  Future<Account?> defaultAccount();

  Stream<Account?> watchDefaultAccount();

  Future<Uuid> createAccount({
    required String name,
    required CurrencyCode currencyCode,
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
  });

  Future<void> renameAccount(Uuid accountUuid, String name);

  /// Marks a transaction deleted without removing the row.
  Future<void> softDeleteTransaction(int id);
}
