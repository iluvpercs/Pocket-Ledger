import 'package:material_ui/material_ui.dart';

import 'package:pocket_ledger_mobile/core/theme/app_colors.dart';
import 'package:pocket_ledger_mobile/domain/entities/dashboard_summary.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/presentation/common/formatters.dart';

class CategorySpendingChart extends StatelessWidget {
  const CategorySpendingChart({
    super.key,
    required this.totals,
    required this.currency,
  });

  final List<CategoryTotal> totals;
  final CurrencyCode currency;

  @override
  Widget build(BuildContext context) {
    final visible = totals.take(6).toList();
    if (visible.isEmpty) {
      return const Text('No spending in this month yet.');
    }
    final max = visible.fold<int>(
      1,
      (current, item) => item.amountMinor > current ? item.amountMinor : current,
    );

    return Column(
      children: [
        for (final total in visible)
          Padding(
            padding: const EdgeInsets.only(bottom: 14),
            child: Semantics(
              label:
                  '${total.category}: ${formatMoney(total.amountMinor, currency)}',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(child: Text(total.category)),
                      Text(formatMoney(total.amountMinor, currency)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: LinearProgressIndicator(
                      value: total.amountMinor / max,
                      minHeight: 10,
                      backgroundColor: Theme.of(context).colorScheme.outline,
                      color: total.amountMinor == max
                          ? AppColors.violet
                          : AppColors.lime,
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}
