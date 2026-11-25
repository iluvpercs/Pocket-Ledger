/// A local category suggestion. Desktop v4 stores category as free text on
/// each transaction; this catalog is only a convenience for entry and search.
final class LedgerCategory {
  const LedgerCategory({
    required this.id,
    required this.name,
    required this.isDefault,
  });

  final String id;
  final String name;
  final bool isDefault;

  LedgerCategory copyWith({String? name}) => LedgerCategory(
        id: id,
        name: name ?? this.name,
        isDefault: isDefault,
      );
}

abstract final class LedgerDefaults {
  static const List<String> categories = [
    'Food',
    'Groceries',
    'Transport',
    'Rent',
    'Utilities',
    'Salary',
    'Shopping',
    'Health',
    'Entertainment',
    'Education',
    'Travel',
    'Other',
  ];
}
