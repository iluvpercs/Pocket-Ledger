import 'package:material_ui/material_ui.dart';

import 'package:pocket_ledger_mobile/domain/entities/account_summary.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/money_text.dart';

/// Natural-height account row. A plain ListTile gave the trailing balance +
/// menu column a fixed height, which overflowed at larger font scales.
class AccountCard extends StatelessWidget {
  const AccountCard({
    super.key,
    required this.summary,
    required this.hasTransactions,
    required this.onTap,
    required this.onAction,
  });

  final AccountSummary summary;
  final bool hasTransactions;
  final VoidCallback onTap;
  final ValueChanged<String> onAction;

  @override
  Widget build(BuildContext context) {
    final account = summary.account;
    final subtitle = <String>[
      account.currencyCode.value,
      if (account.isDefault) 'Default',
      if (hasTransactions) 'Has transactions',
    ].join('  •  ');

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              CircleAvatar(
                child: Icon(
                  account.isDefault
                      ? Icons.star
                      : Icons.account_balance_wallet_outlined,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      account.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 160),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    MoneyText(
                      minor: summary.balanceMinor,
                      currency: account.currencyCode,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    PopupMenuButton<String>(
                      tooltip: 'Account actions',
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints.tightFor(height: 40),
                      itemBuilder: (_) => [
                        if (!account.isDefault)
                          const PopupMenuItem(
                            value: 'default',
                            child: Text('Set as default'),
                          ),
                        const PopupMenuItem(
                          value: 'rename',
                          child: Text('Rename'),
                        ),
                        const PopupMenuItem(
                          value: 'archive',
                          child: Text('Archive'),
                        ),
                      ],
                      onSelected: onAction,
                      child: const Icon(Icons.more_vert),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
