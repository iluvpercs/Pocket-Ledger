import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:pocket_ledger_mobile/application/providers/ledger_providers.dart';
import 'package:pocket_ledger_mobile/domain/entities/category.dart';
import 'package:pocket_ledger_mobile/presentation/common/navigation.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/async_value_view.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/empty_state_view.dart';

class CategoriesScreen extends ConsumerWidget {
  const CategoriesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final categories = ref.watch(categoriesProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Categories'),
        leading: Semantics(
          label: 'Back to settings',
          child: IconButton(
            tooltip: 'Back',
            icon: const Icon(Icons.arrow_back),
            onPressed: () => closeOrGo(context, '/settings'),
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => showDialog<void>(
          context: context,
          builder: (_) => const CategoryDialog(),
        ),
        icon: const Icon(Icons.add),
        label: const Text('Category'),
      ),
      body: AsyncValueView(
        value: categories,
        onRetry: () => ref.invalidate(categoriesProvider),
        builder: (items) {
          if (items.isEmpty) {
            return const Padding(
              padding: EdgeInsets.all(16),
              child: EmptyStateView(
                icon: Icons.label_outline,
                title: 'No categories',
                message: 'Add a category to use it when entering transactions.',
              ),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
            itemCount: items.length,
            itemBuilder: (context, index) {
              final category = items[index];
              return ListTile(
                leading: Icon(
                  category.isDefault ? Icons.lock_outline : Icons.label_outlined,
                ),
                title: Text(category.name),
                subtitle: Text(category.isDefault ? 'Default suggestion' : 'Custom'),
                trailing: category.isDefault
                    ? null
                    : PopupMenuButton<String>(
                        tooltip: 'Category actions',
                        itemBuilder: (_) => const [
                          PopupMenuItem(value: 'edit', child: Text('Edit')),
                          PopupMenuItem(value: 'delete', child: Text('Delete')),
                        ],
                        onSelected: (action) => _handleAction(
                          ref,
                          context,
                          items,
                          category,
                          action,
                        ),
                      ),
              );
            },
          );
        },
      ),
    );
  }

  Future<void> _handleAction(
    WidgetRef ref,
    BuildContext context,
    List<LedgerCategory> all,
    LedgerCategory category,
    String action,
  ) async {
    final repository = ref.read(ledgerRepositoryProvider);
    if (action == 'delete') {
      final updated =
          all.where((item) => item.id != category.id).toList();
      await repository.saveCategories(updated);
      return;
    }
    if (!context.mounted) return;
    final result = await showDialog<String>(
      context: context,
      builder: (_) => CategoryDialog(initialName: category.name),
    );
    if (result == null || result.trim().isEmpty) return;
    final updated = [
      for (final item in all)
        if (item.id == category.id) item.copyWith(name: result.trim()) else item,
    ];
    await repository.saveCategories(updated);
  }
}

class CategoryDialog extends StatefulWidget {
  const CategoryDialog({super.key, this.initialName});

  final String? initialName;

  @override
  State<CategoryDialog> createState() => _CategoryDialogState();
}

class _CategoryDialogState extends State<CategoryDialog> {
  final _controller = TextEditingController();

  @override
  void initState() {
    super.initState();
    _controller.text = widget.initialName ?? '';
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(
        widget.initialName == null ? 'Add category' : 'Edit category',
      ),
      content: TextField(
        controller: _controller,
        autofocus: true,
        decoration: const InputDecoration(
          labelText: 'Category name',
          border: OutlineInputBorder(),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context).pop(_controller.text.trim()),
          child: const Text('Save'),
        ),
      ],
    );
  }
}
