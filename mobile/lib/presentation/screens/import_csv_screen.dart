import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/domain/entities/csv_import.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/services/csv_import_service.dart';
import 'package:pocket_ledger_mobile/presentation/common/navigation.dart';

class ImportCsvScreen extends ConsumerStatefulWidget {
  const ImportCsvScreen({super.key});

  @override
  ConsumerState<ImportCsvScreen> createState() => _ImportCsvScreenState();
}

class _ImportCsvScreenState extends ConsumerState<ImportCsvScreen> {
  CsvFileInfo? _file;
  late CsvMapping _mapping;
  late LedgerDateFormat _dateFormat;
  bool _roundAmounts = false;
  String? _fileName;
  String? _error;
  bool _busy = false;

  bool get _hasChanges => _file != null || _roundAmounts;

  Future<void> _confirmDiscard() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Discard CSV selection?'),
        content: const Text('The selected file and mapping will be lost.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Keep editing'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Discard'),
          ),
        ],
      ),
    );
    if (!mounted || confirmed != true) return;
    setState(() {
      _file = null;
      _roundAmounts = false;
      _fileName = null;
      _error = null;
    });
    closeOrGo(context, '/settings');
  }

  Future<void> _cancel() async {
    if (_busy) return;
    if (_hasChanges) {
      await _confirmDiscard();
      return;
    }
    closeOrGo(context, '/settings');
  }

  Future<void> _onPopInvoked(bool didPop, Object? result) async {
    if (didPop || _busy || !_hasChanges) return;
    await _confirmDiscard();
  }

  @override
  Widget build(BuildContext context) {
    final file = _file;
    return PopScope<Object?>(
      onPopInvokedWithResult: _onPopInvoked,
      child: Scaffold(
      appBar: AppBar(
        title: const Text('Import CSV'),
        leading: Semantics(
          label: 'Back to settings',
          child: IconButton(
            tooltip: 'Back',
            icon: const Icon(Icons.arrow_back),
            onPressed: _busy ? null : _cancel,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'Manual import only',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Choose a CSV file with the system picker. Nothing is '
                      'uploaded, scanned automatically or sent over a network.',
                    ),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      onPressed: _busy ? null : _pickFile,
                      icon: const Icon(Icons.folder_open),
                      label: const Text('Choose CSV file'),
                    ),
                    if (_fileName != null) ...[
                      const SizedBox(height: 12),
                      Text('File: $_fileName'),
                    ],
                  ],
                ),
              ),
            ),
            if (file != null) ...[
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Column mapping',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Delimiter: ${file.delimiterLabel}  •  '
                        '${file.hasHeaderRow ? 'Header detected' : 'No header'}',
                      ),
                      const SizedBox(height: 12),
                      for (var index = 0; index < file.headers.length; index++)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  file.headers[index],
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: DropdownButton<CsvFieldKind>(
                                  isExpanded: true,
                                  value: _mapping[index],
                                  items: [
                                    for (final kind in CsvFieldKind.values)
                                      DropdownMenuItem(
                                        value: kind,
                                        child: Text(kind.label),
                                      ),
                                  ],
                                  onChanged: (value) => setState(() {
                                    _mapping =
                                        _mapping.withColumn(index, value!);
                                  }),
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      DropdownButtonFormField<LedgerDateFormat>(
                        initialValue: _dateFormat,
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
                        onChanged: (value) =>
                            setState(() => _dateFormat = value!),
                      ),
                      SwitchListTile(
                        value: _roundAmounts,
                        title: const Text('Round surplus precision'),
                        subtitle: const Text(
                          'Off = strict; surplus decimals are rejected. '
                          'On = round half away from zero.',
                        ),
                        onChanged: (value) =>
                            setState(() => _roundAmounts = value),
                      ),
                      const SizedBox(height: 8),
                      FilledButton.icon(
                        onPressed: _busy ? null : _preview,
                        icon: const Icon(Icons.visibility),
                        label: const Text('Preview rows'),
                      ),
                    ],
                  ),
                ),
              ),
            ],
            if (_error != null) ...[
              const SizedBox(height: 16),
              Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
          ],
        ),
      ),
      ),
    );
  }

  Future<void> _pickFile() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final picked = await FilePicker.pickFile(
        dialogTitle: 'Choose a CSV file',
        type: FileType.custom,
        allowedExtensions: ['csv', 'txt', 'tsv'],
      );
      if (picked == null) return;
      final bytes = await picked.readAsBytes();
      final text = utf8.decode(bytes, allowMalformed: true);
      final info = CsvImportService.inspect(text);
      if (!mounted) return;
      setState(() {
        _file = info;
        _mapping = info.mapping;
        _dateFormat = info.suggestedDateFormat;
        _fileName = picked.name;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _preview() async {
    final file = _file;
    if (file == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final accounts = await ref.read(accountsProvider.future);
      final preferences = await ref.read(settingsProvider.future);
      if (accounts.isEmpty) {
        throw StateError('Create an account before importing CSV.');
      }
      final uuid = preferences.defaultAccountUuid;
      final defaultAccount = uuid == null
          ? accounts.first
          : accounts.firstWhere(
              (account) => account.uuid == uuid,
              orElse: () => accounts.first,
            );
      final hashes = await ref.read(ledgerRepositoryProvider).importHashes();
      final preview = CsvImportService.preview(
        file: file,
        mapping: _mapping,
        dateFormat: _dateFormat,
        defaultAccount: defaultAccount,
        defaultCurrency: preferences.defaultCurrencyCode,
        accounts: accounts,
        roundAmounts: _roundAmounts,
        sourceFile: _fileName ?? 'import.csv',
        existingImportHashAccounts: hashes,
      );
      if (!mounted) return;
      context.push('/import/preview', extra: preview);
    } catch (error) {
      if (!mounted) return;
      setState(
        () => _error = error.toString().replaceFirst('StateError: ', ''),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }
}
