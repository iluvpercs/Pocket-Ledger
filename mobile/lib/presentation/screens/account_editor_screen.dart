import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/presentation/common/navigation.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/async_value_view.dart';

/// Pushed account editor. The wrapper resolves the account from the live
/// accounts stream so a deep link works even before that stream has emitted.
class AccountEditorScreen extends ConsumerWidget {
  const AccountEditorScreen({super.key, this.accountUuid});

  final Uuid? accountUuid;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final accounts = ref.watch(accountsProvider);
    return AsyncValueView(
      value: accounts,
      builder: (items) {
        if (accountUuid == null) {
          return const AccountEditorForm();
        }
        final account = items.where(
          (item) => item.uuid == accountUuid,
        ).firstOrNull;
        if (account == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Edit account')),
            body: const Center(child: Text('Account not found.')),
          );
        }
        return AccountEditorForm(account: account);
      },
    );
  }
}

class AccountEditorForm extends ConsumerStatefulWidget {
  const AccountEditorForm({super.key, this.account});

  final Account? account;

  @override
  ConsumerState<AccountEditorForm> createState() => _AccountEditorFormState();
}

class _AccountEditorFormState extends ConsumerState<AccountEditorForm> {
  late final TextEditingController _name;
  late final TextEditingController _opening;
  late CurrencyCode _currency;
  late bool _isDefault;
  String? _error;
  bool _saving = false;
  bool _dirty = false;

  late final String _initialName;
  late final String _initialOpening;
  late final CurrencyCode _initialCurrency;
  late final bool _initialDefault;

  @override
  void initState() {
    super.initState();
    _name = TextEditingController(text: widget.account?.name ?? '');
    _opening = TextEditingController(text: '0');
    _currency = widget.account?.currencyCode ?? CurrencyCode.inr;
    _isDefault = widget.account?.isDefault ?? false;
    _initialName = _name.text;
    _initialOpening = _opening.text;
    _initialCurrency = _currency;
    _initialDefault = _isDefault;
    _name.addListener(_syncDirty);
    _opening.addListener(_syncDirty);
  }

  @override
  void dispose() {
    _name.removeListener(_syncDirty);
    _opening.removeListener(_syncDirty);
    _name.dispose();
    _opening.dispose();
    super.dispose();
  }

  void _syncDirty() {
    final dirty = _name.text != _initialName ||
        _opening.text != _initialOpening ||
        _currency != _initialCurrency ||
        _isDefault != _initialDefault;
    if (dirty == _dirty) return;
    setState(() => _dirty = dirty);
  }

  Future<void> _confirmDiscard() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Discard changes?'),
        content: const Text('Your edits to this account will be lost.'),
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
    closeOrGo(context, '/accounts');
  }

  Future<void> _cancel() async {
    if (_saving) return;
    if (_dirty) {
      await _confirmDiscard();
      return;
    }
    closeOrGo(context, '/accounts');
  }

  Future<void> _onPopInvoked(bool didPop, Object? result) async {
    if (didPop || _saving || !_dirty) return;
    await _confirmDiscard();
  }

  @override
  Widget build(BuildContext context) {
    final codes = CurrencyCode.supportedCodes();
    return PopScope<Object?>(
      onPopInvokedWithResult: _onPopInvoked,
      child: Scaffold(
        appBar: AppBar(
          title: Text(widget.account == null ? 'Add account' : 'Edit account'),
          leading: Semantics(
            label: 'Back to accounts',
            child: IconButton(
              tooltip: 'Back',
              icon: const Icon(Icons.arrow_back),
              onPressed: _saving ? null : _cancel,
            ),
          ),
          actions: [
            Semantics(
              label: 'Close account editor',
              child: IconButton(
                tooltip: 'Close',
                icon: const Icon(Icons.close),
                onPressed: _saving ? null : _cancel,
              ),
            ),
          ],
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
                      TextField(
                        controller: _name,
                        enabled: !_saving,
                        decoration: const InputDecoration(
                          labelText: 'Account name',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<CurrencyCode>(
                        initialValue: _currency,
                        isExpanded: true,
                        items: [
                          for (final code in codes)
                            DropdownMenuItem(
                              value: CurrencyCode.parse(code),
                              child: Text(
                                '$code — ${CurrencyCode.parse(code).symbol}',
                              ),
                            ),
                        ],
                        onChanged: _saving
                            ? null
                            : (value) => setState(() {
                                  _currency = value!;
                                  _syncDirty();
                                }),
                        decoration: const InputDecoration(
                          labelText: 'Currency',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      if (widget.account == null) ...[
                        const SizedBox(height: 16),
                        TextField(
                          controller: _opening,
                          enabled: !_saving,
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          decoration: InputDecoration(
                            labelText: 'Opening balance',
                            helperText:
                                'Up to ${_currency.precision.value} decimals, '
                                'no rounding.',
                            border: const OutlineInputBorder(),
                          ),
                        ),
                      ],
                      SwitchListTile(
                        value: _isDefault,
                        title: const Text('Use as default account'),
                        onChanged: _saving
                            ? null
                            : (value) => setState(() {
                                  _isDefault = value;
                                  _syncDirty();
                                }),
                      ),
                      if (_error != null) ...[
                        const SizedBox(height: 8),
                        Text(
                          _error!,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.error,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: _saving ? null : _save,
                child: Text(
                  widget.account == null ? 'Add account' : 'Save changes',
                ),
              ),
              const SizedBox(height: 8),
              OutlinedButton(
                onPressed: _saving ? null : _cancel,
                child: const Text('Cancel'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    final repository = ref.read(ledgerRepositoryProvider);
    try {
      final name = _name.text.trim();
      if (name.isEmpty) {
        throw StateError('Account name cannot be empty.');
      }
      if (widget.account != null) {
        await repository.renameAccount(widget.account!.uuid, name);
        if (_isDefault && !widget.account!.isDefault) {
          await repository.setDefaultAccount(widget.account!.uuid);
        }
      } else {
        final minor = MinorAmount.parse(
          _opening.text.replaceAll(',', '').trim(),
          _currency.precision,
          strict: true,
        ).minor;
        await repository.createAccount(
          name: name,
          currencyCode: _currency,
          openingMinor: minor,
          isDefault: _isDefault,
        );
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            widget.account == null ? 'Account added' : 'Account updated',
          ),
        ),
      );
      setState(() => _dirty = false);
      closeOrGo(context, '/accounts');
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = error.toString().replaceFirst('StateError: ', '');
      });
    }
  }
}
