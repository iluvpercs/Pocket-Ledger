import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/presentation/common/navigation.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/add_transaction_form.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/async_value_view.dart';

class TransactionEditorScreen extends ConsumerStatefulWidget {
  const TransactionEditorScreen({
    super.key,
    this.id,
    this.initialAccountUuid,
  });

  final int? id;
  final Uuid? initialAccountUuid;

  @override
  ConsumerState<TransactionEditorScreen> createState() =>
      _TransactionEditorScreenState();
}

class _TransactionEditorScreenState extends ConsumerState<TransactionEditorScreen> {
  bool _dirty = false;
  bool _saving = false;

  Future<void> _confirmDiscard() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Discard changes?'),
        content: const Text('This transaction has unsaved changes.'),
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
    setState(() => _dirty = false);
    closeOrGo(context, '/transactions');
  }

  Future<void> _cancel() async {
    if (_saving) return;
    if (_dirty) {
      await _confirmDiscard();
      return;
    }
    closeOrGo(context, '/transactions');
  }

  Future<void> _onPopInvoked(bool didPop, Object? result) async {
    if (didPop || _saving || !_dirty) return;
    await _confirmDiscard();
  }

  @override
  Widget build(BuildContext context) {
    final accounts = ref.watch(accountsProvider);
    final categories = ref.watch(categoriesProvider);
    final times = ref.watch(transactionTimesProvider);
    final existing = widget.id == null
        ? null
        : ref.watch(transactionByIdProvider(widget.id!));

    return PopScope<Object?>(
      onPopInvokedWithResult: _onPopInvoked,
      child: Scaffold(
        appBar: AppBar(
          title: Text(
            widget.id == null ? 'Add transaction' : 'Edit transaction',
          ),
          leading: Semantics(
            label: 'Back to transactions',
            child: IconButton(
              tooltip: 'Back',
              icon: const Icon(Icons.arrow_back),
              onPressed: _saving ? null : _cancel,
            ),
          ),
          actions: [
            Semantics(
              label: 'Close transaction editor',
              child: IconButton(
                tooltip: 'Close',
                icon: const Icon(Icons.close),
                onPressed: _saving ? null : _cancel,
              ),
            ),
          ],
        ),
        body: AsyncValueView(
          value: accounts,
          builder: (accountList) {
            return AsyncValueView(
              value: categories,
              builder: (categoryList) {
                return AsyncValueView(
                  value: times,
                  builder: (timeMap) {
                    Widget form(LedgerTransaction? transaction) {
                      return AddTransactionForm(
                        accounts: accountList,
                        categories: categoryList,
                        initialAccountUuid: widget.initialAccountUuid,
                        initialTransaction: transaction,
                        initialTimeMs: transaction == null
                            ? null
                            : timeMap[transaction.uuid.value],
                        onDirtyChanged: (dirty) {
                          if (!mounted) return;
                          setState(() => _dirty = dirty);
                        },
                        onSubmit: (draft) => _save(draft, transaction?.id),
                      );
                    }

                    if (existing == null) return form(null);
                    return AsyncValueView(value: existing, builder: form);
                  },
                );
              },
            );
          },
        ),
      ),
    );
  }

  Future<void> _save(TransactionDraft draft, int? existingId) async {
    if (_saving) return;
    setState(() => _saving = true);
    final repository = ref.read(ledgerRepositoryProvider);
    try {
      if (existingId == null) {
        await repository.addTransaction(
          type: draft.type,
          amount: draft.amountText,
          category: draft.category,
          transactionDate: draft.transactionDate,
          accountUuid: draft.accountUuid,
          description: draft.description,
          transactionTimeMs: draft.transactionTimeMs,
        );
      } else {
        await repository.updateTransaction(
          id: existingId,
          type: draft.type,
          amount: draft.amountText,
          category: draft.category,
          transactionDate: draft.transactionDate,
          accountUuid: draft.accountUuid,
          description: draft.description,
          transactionTimeMs: draft.transactionTimeMs,
        );
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            existingId == null ? 'Transaction added' : 'Transaction updated',
          ),
        ),
      );
      setState(() {
        _dirty = false;
        _saving = false;
      });
      closeOrGo(context, '/transactions');
    } catch (error) {
      if (!mounted) return;
      setState(() => _saving = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    }
  }
}
