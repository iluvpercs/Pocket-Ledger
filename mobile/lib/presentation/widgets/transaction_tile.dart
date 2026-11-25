import 'package:material_ui/material_ui.dart';

import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/presentation/common/formatters.dart';
import 'money_text.dart';

class TransactionTile extends StatelessWidget {
  const TransactionTile({
    super.key,
    required this.transaction,
    required this.currency,
    required this.dateFormat,
    required this.selected,
    this.onTap,
    this.onLongPress,
  });

  final LedgerTransaction transaction;
  final CurrencyCode currency;
  final LedgerDateFormat dateFormat;
  final bool selected;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;

  @override
  Widget build(BuildContext context) {
    final title = transaction.description?.trim().isNotEmpty == true
        ? transaction.description!
        : transaction.category;
    final subtitle =
        '${formatDate(transaction.transactionDate, dateFormat)}  •  '
        '${transaction.category}';
    final amount = formatMoney(
      transaction.amount.minor,
      currency,
      type: transaction.type,
    );

    return Semantics(
      label: '$title, $subtitle, $amount',
      child: Card(
        margin: const EdgeInsets.symmetric(vertical: 4),
        child: ListTile(
          selected: selected,
          selectedTileColor: Theme.of(context).colorScheme.primaryContainer,
          leading: CircleAvatar(
            child: Icon(
              transaction.type.name == 'income'
                  ? Icons.arrow_downward
                  : Icons.arrow_upward,
            ),
          ),
          title: Text(title),
          subtitle: Text(subtitle),
          trailing: MoneyText(
            minor: transaction.amount.minor,
            currency: currency,
            type: transaction.type,
          ),
          onTap: onTap,
          onLongPress: onLongPress,
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        ),
      ),
    );
  }
}
