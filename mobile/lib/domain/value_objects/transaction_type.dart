import 'package:pocket_ledger_mobile/domain/validation_exception.dart';

/// Direction stored in `transactions.transaction_type`.
enum TransactionType {
  income('income'),
  expense('expense');

  const TransactionType(this.dbValue);

  final String dbValue;

  factory TransactionType.parse(Object? input) {
    final text = input?.toString().trim().toLowerCase() ?? '';
    return switch (text) {
      'income' => TransactionType.income,
      'expense' => TransactionType.expense,
      _ => throw DomainValidationException(
        "Transaction type must be 'income' or 'expense'.",
      ),
    };
  }
}
