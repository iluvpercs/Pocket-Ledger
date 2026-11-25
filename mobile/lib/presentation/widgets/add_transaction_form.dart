import 'package:material_ui/material_ui.dart';
import 'package:intl/intl.dart';

import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/category.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/validation_exception.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_precision.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

final class TransactionDraft {
  const TransactionDraft({
    required this.type,
    required this.amountText,
    required this.accountUuid,
    required this.category,
    required this.description,
    required this.transactionDate,
    required this.transactionTimeMs,
  });

  final TransactionType type;
  final String amountText;
  final Uuid accountUuid;
  final String category;
  final String? description;
  final String transactionDate;
  final int transactionTimeMs;
}

/// Pure widget form so validation can be tested without a database.
class AddTransactionForm extends StatefulWidget {
  const AddTransactionForm({
    super.key,
    required this.accounts,
    required this.categories,
    required this.onSubmit,
    this.initialAccountUuid,
    this.initialTransaction,
    this.initialTimeMs,
    this.onDirtyChanged,
  });

  final List<Account> accounts;
  final List<LedgerCategory> categories;
  final Future<void> Function(TransactionDraft) onSubmit;
  final Uuid? initialAccountUuid;
  final LedgerTransaction? initialTransaction;
  final int? initialTimeMs;
  final ValueChanged<bool>? onDirtyChanged;

  @override
  State<AddTransactionForm> createState() => _AddTransactionFormState();
}

class _AddTransactionFormState extends State<AddTransactionForm> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _amount;
  late final TextEditingController _note;
  late TransactionType _type;
  late Uuid? _accountUuid;
  late String? _category;
  late DateTime _when;
  String? _amountError;
  bool _saving = false;
  bool _dirty = false;

  late final String _initialAmount;
  late final String _initialNote;
  late final TransactionType _initialType;
  late final Uuid? _initialAccountUuid;
  late final String? _initialCategory;
  late final DateTime _initialWhen;

  @override
  void initState() {
    super.initState();
    final initial = widget.initialTransaction;
    _amount = TextEditingController(
      text: initial == null
          ? ''
          : initial.amount
              .toMajorDecimal(
                initialAccount()?.precision ?? CurrencyPrecision.from(2),
              )
              .toStringAsFixed((initialAccount()?.precision.value ?? 2)),
    );
    _note = TextEditingController(text: initial?.description ?? '');
    _type = initial?.type ?? TransactionType.expense;
    _accountUuid = widget.initialAccountUuid ??
        initial?.accountUuid ??
        (widget.accounts.isEmpty ? null : widget.accounts.first.uuid);
    _category = initial?.category ??
        (widget.categories.isEmpty ? null : widget.categories.first.name);
    final timeMs = widget.initialTimeMs ?? DateTime.now().millisecondsSinceEpoch;
    _when = DateTime.fromMillisecondsSinceEpoch(timeMs);
    _initialAmount = _amount.text;
    _initialNote = _note.text;
    _initialType = _type;
    _initialAccountUuid = _accountUuid;
    _initialCategory = _category;
    _initialWhen = _when;
    _amount.addListener(_syncDirty);
    _note.addListener(_syncDirty);
  }

  Account? initialAccount() {
    final uuid = widget.initialTransaction?.accountUuid;
    if (uuid == null) return null;
    for (final account in widget.accounts) {
      if (account.uuid == uuid) return account;
    }
    return null;
  }

  void _syncDirty() {
    final dirty = _amount.text != _initialAmount ||
        _note.text != _initialNote ||
        _type != _initialType ||
        _accountUuid != _initialAccountUuid ||
        _category != _initialCategory ||
        _when.millisecondsSinceEpoch != _initialWhen.millisecondsSinceEpoch;
    if (dirty == _dirty) return;
    setState(() => _dirty = dirty);
    widget.onDirtyChanged?.call(dirty);
  }

  @override
  void dispose() {
    _amount.removeListener(_syncDirty);
    _note.removeListener(_syncDirty);
    _amount.dispose();
    _note.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.accounts.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(20),
          child: Text('Create an account before adding a transaction.'),
        ),
      );
    }

    final categoryNames = [
      for (final category in widget.categories) category.name,
      if (_category != null && !widget.categories.any((c) => c.name == _category))
        _category!,
    ];

    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            SegmentedButton<TransactionType>(
              segments: const [
                ButtonSegment(
                  value: TransactionType.expense,
                  label: Text('Expense'),
                  icon: Icon(Icons.arrow_upward),
                ),
                ButtonSegment(
                  value: TransactionType.income,
                  label: Text('Income'),
                  icon: Icon(Icons.arrow_downward),
                ),
              ],
              selected: {_type},
              onSelectionChanged: (selection) {
                setState(() => _type = selection.first);
                _syncDirty();
              },
            ),
            const SizedBox(height: 20),
            TextFormField(
              controller: _amount,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(
                labelText: 'Amount',
                border: const OutlineInputBorder(),
                errorText: _amountError,
                helperText:
                    'Use up to ${_selectedAccount()?.precision.value ?? 2} '
                    'decimal places. No rounding is applied.',
              ),
              onChanged: (_) {
                if (_amountError != null) {
                  setState(() => _amountError = null);
                }
              },
              validator: (value) => _validateAmount(value),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<Uuid>(
              initialValue: _accountUuid,
              decoration: const InputDecoration(
                labelText: 'Account',
                border: OutlineInputBorder(),
              ),
              items: [
                for (final account in widget.accounts)
                  DropdownMenuItem(
                    value: account.uuid,
                    child: Text('${account.name} (${account.currencyCode.value})'),
                  ),
              ],
              onChanged: (value) {
                setState(() => _accountUuid = value);
                _syncDirty();
              },
              validator: (value) => value == null ? 'Choose an account.' : null,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: _category,
              decoration: const InputDecoration(
                labelText: 'Category',
                border: OutlineInputBorder(),
              ),
              items: [
                for (final name in categoryNames)
                  DropdownMenuItem(value: name, child: Text(name)),
              ],
              onChanged: (value) {
                setState(() => _category = value);
                _syncDirty();
              },
              validator: (value) =>
                  value == null || value.trim().isEmpty ? 'Choose a category.' : null,
            ),
            const SizedBox(height: 16),
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(
                'Date & time: ${DateFormat('yyyy-MM-dd HH:mm').format(_when)}',
              ),
              trailing: Semantics(
                label: 'Choose date and time',
                child: const Icon(Icons.event),
              ),
              onTap: _pickDateTime,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _note,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: 'Note (optional)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _saving ? null : _submit,
              child: Text(
                _saving
                    ? 'Saving…'
                    : widget.initialTransaction == null
                        ? 'Add transaction'
                        : 'Save changes',
              ),
            ),
          ],
        ),
      ),
    );
  }

  Account? _selectedAccount() {
    for (final account in widget.accounts) {
      if (account.uuid == _accountUuid) return account;
    }
    return null;
  }

  String? _validateAmount(String? value) {
    final account = _selectedAccount();
    if (account == null) return null;
    try {
      MinorAmount.positive(
        value?.replaceAll(',', '').trim() ?? '',
        account.precision,
        strict: true,
      );
      return null;
    } on DomainValidationException catch (error) {
      return error.message;
    }
  }

  Future<void> _pickDateTime() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _when,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_when),
    );
    if (time == null || !mounted) return;
    setState(() {
      _when = DateTime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
      );
    });
    _syncDirty();
  }

  Future<void> _submit() async {
    if (_saving) return;
    final error = _validateAmount(_amount.text);
    setState(() => _amountError = error);
    if (!_formKey.currentState!.validate() || error != null) return;
    final account = _selectedAccount()!;
    final utc = _when.toUtc();
    final draft = TransactionDraft(
      type: _type,
      amountText: _amount.text.replaceAll(',', '').trim(),
      accountUuid: account.uuid,
      category: _category!.trim(),
      description: _note.text.trim().isEmpty ? null : _note.text.trim(),
      transactionDate: DateFormat('yyyy-MM-dd').format(utc),
      transactionTimeMs: utc.millisecondsSinceEpoch,
    );
    setState(() => _saving = true);
    try {
      await widget.onSubmit(draft);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }
}
