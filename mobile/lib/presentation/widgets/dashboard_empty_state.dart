import 'package:material_ui/material_ui.dart';

import 'empty_state_view.dart';

class DashboardEmptyState extends StatelessWidget {
  const DashboardEmptyState({super.key, required this.onAdd});

  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    return EmptyStateView(
      icon: Icons.receipt_long_outlined,
      title: 'Your ledger is ready',
      message: 'Add your first transaction to see balances, trends and '
          'spending by category.',
      actionLabel: 'Add your first transaction',
      onAction: onAdd,
    );
  }
}
