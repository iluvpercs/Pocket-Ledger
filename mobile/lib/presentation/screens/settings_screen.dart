import 'dart:convert';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_constants.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/async_value_view.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/brand_logo.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    final accounts = ref.watch(accountsProvider);
    final device = ref.watch(deviceIdProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: AsyncValueView(
        value: settings,
        onRetry: () => ref.invalidate(settingsProvider),
        builder: (preferences) {
          return AsyncValueView(
            value: accounts,
            builder: (accountList) {
              return ListView(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            'Preferences',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 12),
                          DropdownButtonFormField<CurrencyCode>(
                            initialValue: preferences.defaultCurrencyCode,
                            isExpanded: true,
                            decoration: const InputDecoration(
                              labelText: 'Default currency',
                              border: OutlineInputBorder(),
                            ),
                            items: [
                              for (final code
                                  in CurrencyCode.supportedCodes())
                                DropdownMenuItem(
                                  value: CurrencyCode.parse(code),
                                  child: Text(code),
                                ),
                            ],
                            onChanged: (value) => _update(
                              ref,
                              context,
                              preferences.copyWith(
                                defaultCurrencyCode: value!,
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          DropdownButtonFormField<String?>(
                            initialValue:
                                preferences.defaultAccountUuid?.value,
                            isExpanded: true,
                            decoration: const InputDecoration(
                              labelText: 'Default account',
                              border: OutlineInputBorder(),
                            ),
                            items: [
                              const DropdownMenuItem<String?>(
                                value: null,
                                child: Text('Use account marked default'),
                              ),
                              for (final account in accountList)
                                DropdownMenuItem<String?>(
                                  value: account.uuid.value,
                                  child: Text(account.name),
                                ),
                            ],
                            onChanged: (value) {
                              final uuid = value == null ? null : Uuid.parse(value);
                              _update(
                                ref,
                                context,
                                preferences.copyWith(
                                  defaultAccountUuid: uuid,
                                  clearDefaultAccount: uuid == null,
                                ),
                              );
                            },
                          ),
                          const SizedBox(height: 12),
                          DropdownButtonFormField<LedgerDateFormat>(
                            initialValue: preferences.dateFormat,
                            isExpanded: true,
                            decoration: const InputDecoration(
                              labelText: 'Date format',
                              border: OutlineInputBorder(),
                            ),
                            items: [
                              for (final format in LedgerDateFormat.values)
                                DropdownMenuItem(
                                  value: format,
                                  child: Text(format.label),
                                ),
                            ],
                            onChanged: (value) => _update(
                              ref,
                              context,
                              preferences.copyWith(dateFormat: value!),
                            ),
                          ),
                          const SizedBox(height: 12),
                          SegmentedButton<LedgerThemeMode>(
                            segments: const [
                              ButtonSegment(
                                value: LedgerThemeMode.dark,
                                label: Text('Dark'),
                              ),
                              ButtonSegment(
                                value: LedgerThemeMode.system,
                                label: Text('System'),
                              ),
                            ],
                            selected: {preferences.themeMode},
                            onSelectionChanged: (selection) => _update(
                              ref,
                              context,
                              preferences.copyWith(themeMode: selection.first),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Card(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                          child: Text(
                            'Categories',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                        ),
                        ListTile(
                          leading: const Icon(Icons.label_outline),
                          title: const Text('Manage categories'),
                          subtitle: const Text(
                            'Local suggestions used for entry and filtering.',
                          ),
                          onTap: () => context.push('/categories'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  Card(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                          child: Text(
                            'Data',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                        ),
                        ListTile(
                          leading: const Icon(Icons.file_upload_outlined),
                          title: const Text('Import CSV'),
                          subtitle: const Text('Manual import via system picker.'),
                          onTap: () => context.push('/import'),
                        ),
                        ListTile(
                          leading: const Icon(Icons.file_download_outlined),
                          title: const Text('Export CSV'),
                          subtitle: const Text('Save a compatible backup.'),
                          onTap: () => _export(ref, context),
                        ),
                        ListTile(
                          leading: Icon(
                            Icons.delete_forever,
                            color: Theme.of(context).colorScheme.error,
                          ),
                          title: const Text('Delete all data'),
                          subtitle: const Text(
                            'Soft-deletes accounts and transactions.',
                          ),
                          onTap: () => _deleteAll(ref, context),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          const BrandLogo(size: 72),
                          const SizedBox(height: 12),
                          Text(
                            'Private by design',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 16),
                          const Text('Version 0.5.0+1'),
                          Text(
                            'Schema v${LedgerConstants.schemaVersion}',
                          ),
                          device.when(
                            data: (uuid) => Text('Device ID: ${uuid.value}'),
                            loading: () => const Text('Device ID: loading…'),
                            error: (error, _) =>
                                Text('Device ID: ${error.toString()}'),
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            'No network. No telemetry. No automatic import.',
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              );
            },
          );
        },
      ),
    );
  }

  Future<void> _update(
    WidgetRef ref,
    BuildContext context,
    LedgerSettings settings,
  ) async {
    try {
      await ref.read(ledgerRepositoryProvider).updateSettings(settings);
    } catch (error) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    }
  }

  Future<void> _export(WidgetRef ref, BuildContext context) async {
    try {
      final csv = await ref.read(exportCsvProvider.future);
      final uri = await FilePicker.saveFile(
        dialogTitle: 'Save Pocket Ledger CSV',
        fileName: 'pocket-ledger-export.csv',
        mimeType: 'text/csv',
        bytes: Uint8List.fromList(utf8.encode(csv)),
      );
      if (!context.mounted || uri == null) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Saved CSV to ${uri.toString()}.')),
      );
    } catch (error) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    }
  }

  Future<void> _deleteAll(WidgetRef ref, BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => const _DeleteAllDialog(),
    );
    if (confirmed != true) return;
    try {
      await ref.read(ledgerRepositoryProvider).deleteAllData();
      ref.invalidate(accountSummariesProvider);
      ref.invalidate(dashboardProvider);
      ref.invalidate(liveTransactionsProvider);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('All ledger data was archived.')),
      );
    } catch (error) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    }
  }
}

class _DeleteAllDialog extends StatefulWidget {
  const _DeleteAllDialog();

  @override
  State<_DeleteAllDialog> createState() => _DeleteAllDialogState();
}

class _DeleteAllDialogState extends State<_DeleteAllDialog> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Delete all data?'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            'Type DELETE to archive every account and transaction. '
            'Rows remain in the local database and outbox.',
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _controller,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(
              labelText: 'Type DELETE',
              border: OutlineInputBorder(),
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: _controller.text.trim() == 'DELETE'
              ? () => Navigator.of(context).pop(true)
              : null,
          child: const Text('Delete all'),
        ),
      ],
    );
  }
}
