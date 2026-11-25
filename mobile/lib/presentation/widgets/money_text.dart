import 'package:material_ui/material_ui.dart';

import 'package:pocket_ledger_mobile/core/theme/app_colors.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';
import 'package:pocket_ledger_mobile/presentation/common/formatters.dart';

class MoneyText extends StatelessWidget {
  const MoneyText({
    super.key,
    required this.minor,
    required this.currency,
    this.type,
    this.style,
    this.maxLines,
    this.overflow,
  });

  final int minor;
  final CurrencyCode currency;
  final TransactionType? type;
  final TextStyle? style;
  final int? maxLines;
  final TextOverflow? overflow;

  @override
  Widget build(BuildContext context) {
    final color = switch (type) {
      TransactionType.income => AppColors.positive,
      TransactionType.expense => AppColors.negative,
      null => null,
    };
    final text = formatMoney(minor, currency, type: type);
    return Semantics(
      label: text,
      child: Text(
        text,
        style: (style ?? Theme.of(context).textTheme.bodyLarge)?.copyWith(
          color: color,
          fontWeight: FontWeight.w700,
        ),
        textAlign: TextAlign.end,
        maxLines: maxLines,
        overflow: overflow,
      ),
    );
  }
}
