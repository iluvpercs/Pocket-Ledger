import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/core/theme/app_colors.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/app_error_view.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/brand_logo.dart';

/// Deliberately a shell, not a dashboard. CRUD and import arrive later.
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bootstrap = ref.watch(bootstrapProvider);
    final account = ref.watch(defaultAccountProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Pocket Ledger'),
        actions: [
          IconButton(
            tooltip: 'Retry local startup',
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(bootstrapProvider);
              ref.invalidate(defaultAccountProvider);
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 520),
              child: switch (bootstrap) {
                AsyncData() => _buildReady(context, account),
                AsyncError(:final error) => AppErrorView(
                  message: error.toString(),
                  onRetry: () => ref.invalidate(bootstrapProvider),
                ),
                _ => const Card(
                  child: Padding(
                    padding: EdgeInsets.all(32),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        CircularProgressIndicator(color: AppColors.lime),
                        SizedBox(height: 16),
                        Text('Preparing local ledger…'),
                      ],
                    ),
                  ),
                ),
              },
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildReady(BuildContext context, AsyncValue account) {
    final date = DateFormat.yMMMd().format(DateTime.now().toUtc());

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const BrandLogo(size: 132),
        const SizedBox(height: 24),
        Text(
          'Private by design',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w700,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        Text(
          'Offline ledger foundation ready on this device.',
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 32),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: switch (account) {
              AsyncData(:final value) => Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Default account',
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: AppColors.lime,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    value?.name ?? 'No default account',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    value == null
                        ? 'Seeding pending'
                        : '${value.currencyCode.value} · precision '
                            '${value.precision.value}',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
              AsyncError(:final error) => Text('Account error: $error'),
              _ => const SizedBox(
                height: 72,
                child: Center(
                  child: CircularProgressIndicator(color: AppColors.lime),
                ),
              ),
            },
          ),
        ),
        const SizedBox(height: 16),
        Text(
          'Local SQLite v4 · $date · no network, no telemetry',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }
}
