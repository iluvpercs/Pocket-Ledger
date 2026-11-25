import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';

enum TransactionTypeFilter {
  all('all'),
  income('income'),
  expense('expense');

  const TransactionTypeFilter(this.id);
  final String id;
}

/// Immutable query description used by Riverpod family providers.
final class TransactionFilter {
  const TransactionFilter({
    this.search = '',
    this.accountUuid,
    this.type = TransactionTypeFilter.all,
    this.category,
    this.fromDate,
    this.toDate,
  });

  final String search;
  final Uuid? accountUuid;
  final TransactionTypeFilter type;
  final String? category;
  final DateTime? fromDate;
  final DateTime? toDate;

  TransactionFilter copyWith({
    String? search,
    Uuid? accountUuid,
    bool clearAccount = false,
    TransactionTypeFilter? type,
    String? category,
    bool clearCategory = false,
    DateTime? fromDate,
    bool clearFromDate = false,
    DateTime? toDate,
    bool clearToDate = false,
  }) {
    return TransactionFilter(
      search: search ?? this.search,
      accountUuid: clearAccount ? null : accountUuid ?? this.accountUuid,
      type: type ?? this.type,
      category: clearCategory ? null : category ?? this.category,
      fromDate: clearFromDate ? null : fromDate ?? this.fromDate,
      toDate: clearToDate ? null : toDate ?? this.toDate,
    );
  }

  bool get isEmpty =>
      search.trim().isEmpty &&
      accountUuid == null &&
      type == TransactionTypeFilter.all &&
      category == null &&
      fromDate == null &&
      toDate == null;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TransactionFilter &&
          search == other.search &&
          accountUuid == other.accountUuid &&
          type == other.type &&
          category == other.category &&
          fromDate == other.fromDate &&
          toDate == other.toDate;

  @override
  int get hashCode => Object.hash(
        search,
        accountUuid,
        type,
        category,
        fromDate,
        toDate,
      );
}
