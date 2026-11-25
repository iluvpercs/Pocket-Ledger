import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/domain/entities/csv_import.dart';
import 'package:pocket_ledger_mobile/presentation/common/navigation.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/empty_state_view.dart';

class CsvPreviewScreen extends ConsumerStatefulWidget {
  const CsvPreviewScreen({super.key, required this.preview});

  final CsvPreview preview;

  @override
  ConsumerState<CsvPreviewScreen> createState() => _CsvPreviewScreenState();
}

class _CsvPreviewScreenState extends ConsumerState<CsvPreviewScreen> {
  bool _importing = false;
  String? _summary;

  @override
  Widget build(BuildContext context) {
    final preview = widget.preview;
    return Scaffold(
      appBar: AppBar(
        title: const Text('CSV preview'),
        leading: Semantics(
          label: 'Back to CSV import',
          child: IconButton(
            tooltip: 'Back',
            icon: const Icon(Icons.arrow_back),
            onPressed: _importing ? null : () => closeOrGo(context, '/settings'),
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Import summary',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text('Ready: ${preview.validCount}'),
                  Text('Duplicates skipped: ${preview.duplicateCount}'),
                  Text('Rejected: ${preview.invalidCount}'),
                  Text(
                    'Rounding: ${preview.roundAmounts ? 'half away from zero' : 'strict'}',
                  ),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: _importing || preview.importableRows.isEmpty
                        ? null
                        : _import,
                    icon: const Icon(Icons.file_upload_outlined),
                    label: Text(
                      'Import ${preview.importableRows.length} rows',
                    ),
                  ),
                  if (_summary != null) ...[
                    const SizedBox(height: 12),
                    Text(_summary!),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (preview.rows.isEmpty)
            const EmptyStateView(
              icon: Icons.table_rows_outlined,
              title: 'No rows found',
              message: 'The selected file did not contain any CSV rows.',
            )
          else
            Card(
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(
                      'First ${preview.rows.take(20).length} rows',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  for (final row in preview.rows.take(20))
                    ListTile(
                      leading: Icon(
                        switch (row.status) {
                          CsvRowStatus.valid => Icons.check_circle_outline,
                          CsvRowStatus.duplicate => Icons.copy_outlined,
                          CsvRowStatus.invalid => Icons.error_outline,
                        },
                        color: row.status == CsvRowStatus.valid
                            ? Theme.of(context).colorScheme.primary
                            : Theme.of(context).colorScheme.error,
                      ),
                      title: Text(
                        'Line ${row.line}: ${row.dateIso ?? '—'} '
                        '${row.type?.name ?? ''} ${row.amountMinor ?? ''}',
                      ),
                      subtitle: Text(
                        row.error ??
                            '${row.category ?? ''} • ${row.description ?? ''}',
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Future<void> _import() async {
    setState(() {
      _importing = true;
      _summary = null;
    });
    try {
      await ref.read(ledgerRepositoryProvider).importRows(
            widget.preview.importableRows,
            sourceFile: widget.preview.sourceFile,
          );
      ref.invalidate(liveTransactionsProvider);
      ref.invalidate(accountSummariesProvider);
      ref.invalidate(dashboardProvider);
      if (!mounted) return;
      setState(() {
        _importing = false;
        _summary =
            'Imported ${widget.preview.validCount}; skipped '
            '${widget.preview.duplicateCount} duplicates; rejected '
            '${widget.preview.invalidCount}.';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('CSV imported')),
      );
      closeOrGo(context, '/settings');
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _importing = false;
        _summary = 'Import failed and nothing was saved: ${error.toString()}';
      });
    }
  }
}
