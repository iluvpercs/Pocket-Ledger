import 'package:pocket_ledger_mobile/domain/entities/account.dart';

/// An account together with its signed ledger balance in minor units.
final class AccountSummary {
  const AccountSummary({
    required this.account,
    required this.balanceMinor,
  });

  final Account account;
  final int balanceMinor;
}
