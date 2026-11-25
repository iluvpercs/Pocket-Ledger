import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:pocket_ledger_mobile/data/database/daos/ledger_dao.dart';
import 'package:pocket_ledger_mobile/data/database/database.dart' show AppDatabase;
import 'package:pocket_ledger_mobile/data/repositories/drift_ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/account_summary.dart';
import 'package:pocket_ledger_mobile/domain/entities/category.dart';
import 'package:pocket_ledger_mobile/domain/entities/dashboard_summary.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_constants.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction.dart';
import 'package:pocket_ledger_mobile/domain/entities/transaction_filter.dart';
import 'package:pocket_ledger_mobile/domain/repositories/ledger_repository.dart';
import 'package:pocket_ledger_mobile/domain/services/csv_export_service.dart';
import 'package:pocket_ledger_mobile/domain/services/ledger_aggregates.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/utc_ms.dart';

final databaseProvider = Provider<AppDatabase>((ref) {
  final database = AppDatabase();
  ref.onDispose(() {
    database.close();
  });
  return database;
});

final ledgerRepositoryProvider = Provider<LedgerRepository>((ref) {
  return DriftLedgerRepository(
    LedgerDao(ref.watch(databaseProvider)),
  );
});

/// Local bootstrap only. It never contacts another device.
final bootstrapProvider = FutureProvider<UtcMs>((ref) async {
  await ref.watch(ledgerRepositoryProvider).ensureBootstrapped();
  return UtcMs.now();
});

final defaultAccountProvider = StreamProvider<Account?>((ref) {
  ref.watch(bootstrapProvider);
  return ref.watch(ledgerRepositoryProvider).watchDefaultAccount();
});

final deviceIdProvider = FutureProvider<Uuid>((ref) async {
  await ref.watch(bootstrapProvider.future);
  return ref.watch(ledgerRepositoryProvider).deviceId();
});

final settingsProvider = StreamProvider<LedgerSettings>((ref) {
  ref.watch(bootstrapProvider);
  return ref.watch(ledgerRepositoryProvider).watchSettings();
});

final accountsProvider = StreamProvider<List<Account>>((ref) {
  ref.watch(bootstrapProvider);
  return ref.watch(ledgerRepositoryProvider).watchAccounts();
});

final liveTransactionsProvider = StreamProvider<List<LedgerTransaction>>((ref) {
  ref.watch(bootstrapProvider);
  return ref.watch(ledgerRepositoryProvider).watchLiveTransactions();
});

final openingBalancesProvider = StreamProvider<Map<String, int>>((ref) {
  ref.watch(bootstrapProvider);
  return ref.watch(ledgerRepositoryProvider).watchOpeningBalances();
});

final transactionTimesProvider = StreamProvider<Map<String, int>>((ref) {
  ref.watch(bootstrapProvider);
  return ref.watch(ledgerRepositoryProvider).transactionTimesStream();
});

final categoriesProvider = StreamProvider<List<LedgerCategory>>((ref) {
  ref.watch(bootstrapProvider);
  return ref.watch(ledgerRepositoryProvider).watchCategories();
});

final transactionByIdProvider =
    FutureProvider.family<LedgerTransaction?, int>((ref, id) async {
  await ref.watch(bootstrapProvider.future);
  return ref.watch(ledgerRepositoryProvider).transactionById(id);
});

final accountSummariesProvider = StreamProvider<List<AccountSummary>>((ref) {
  ref.watch(bootstrapProvider);
  final repository = ref.watch(ledgerRepositoryProvider);
  return _combine3(
    repository.watchAccounts(),
    repository.watchOpeningBalances(),
    repository.watchAccountDeltas(),
    assembleAccountSummaries,
  );
});

class PageSizeNotifier extends Notifier<int> {
  @override
  int build() => 25;

  void loadMore() => state = state + 25;

  void reset() => state = 25;
}

final transactionPageSizeProvider =
    NotifierProvider<PageSizeNotifier, int>(PageSizeNotifier.new);

class TransactionFilterNotifier extends Notifier<TransactionFilter> {
  @override
  TransactionFilter build() => const TransactionFilter();

  void set(TransactionFilter filter) => state = filter;

  void reset() {
    state = const TransactionFilter();
    ref.read(transactionPageSizeProvider.notifier).reset();
  }
}

final transactionFilterProvider =
    NotifierProvider<TransactionFilterNotifier, TransactionFilter>(
  TransactionFilterNotifier.new,
);

final filteredTransactionsProvider =
    StreamProvider.family<List<LedgerTransaction>, TransactionFilter>((
  ref,
  filter,
) {
  final limit = ref.watch(transactionPageSizeProvider);
  return ref
      .watch(ledgerRepositoryProvider)
      .watchTransactions(filter, limit: limit);
});

class SelectedMonthNotifier extends Notifier<DateTime> {
  @override
  DateTime build() {
    final now = DateTime.now();
    return DateTime(now.year, now.month);
  }

  void previous() => state = DateTime(state.year, state.month - 1);

  void next() => state = DateTime(state.year, state.month + 1);
}

final selectedMonthProvider =
    NotifierProvider<SelectedMonthNotifier, DateTime>(
  SelectedMonthNotifier.new,
);

final dashboardProvider = StreamProvider<DashboardSummary>((ref) {
  ref.watch(bootstrapProvider);
  final repository = ref.watch(ledgerRepositoryProvider);
  final month = ref.watch(selectedMonthProvider);
  final chartCurrency = ref.watch(
    settingsProvider.select(
      (state) =>
          state.value?.defaultCurrencyCode.value ??
          LedgerConstants.defaultCurrencyCode,
    ),
  );

  return _combine3(
    repository.watchAccounts(),
    repository.watchOpeningBalances(),
    repository.watchDashboardAggregate(
      month: month,
      chartCurrencyCode: chartCurrency,
    ),
    (accounts, opening, aggregate) => assembleDashboardSummary(
      accounts: accounts,
      openingBalances: opening,
      aggregate: aggregate,
      chartCurrencyCode: chartCurrency,
    ),
  );
});

final exportCsvProvider = FutureProvider<String>((ref) async {
  final accounts = await ref.read(accountsProvider.future);
  final transactions = await ref.read(liveTransactionsProvider.future);
  return CsvExportService.encode(transactions, accounts);
});

/// Riverpod 3 no longer exposes `.stream` on a [StreamProvider], so derived
/// providers combine the repository streams directly. This avoids another
/// package dependency and keeps the streams lazy.
Stream<R> _combine3<A, B, C, R>(
  Stream<A> first,
  Stream<B> second,
  Stream<C> third,
  R Function(A, B, C) combine,
) {
  late final StreamController<R> controller;
  late final StreamSubscription<A> firstSubscription;
  late final StreamSubscription<B> secondSubscription;
  late final StreamSubscription<C> thirdSubscription;

  A? firstValue;
  B? secondValue;
  C? thirdValue;
  var hasFirst = false;
  var hasSecond = false;
  var hasThird = false;
  var doneCount = 0;

  void emitIfReady() {
    if (!hasFirst || !hasSecond || !hasThird || controller.isClosed) return;
    controller.add(combine(firstValue as A, secondValue as B, thirdValue as C));
  }

  void markDone() {
    doneCount++;
    if (doneCount == 3 && !controller.isClosed) controller.close();
  }

  controller = StreamController<R>(
    onListen: () {
      firstSubscription = first.listen(
        (value) {
          firstValue = value;
          hasFirst = true;
          emitIfReady();
        },
        onError: controller.addError,
        onDone: markDone,
      );
      secondSubscription = second.listen(
        (value) {
          secondValue = value;
          hasSecond = true;
          emitIfReady();
        },
        onError: controller.addError,
        onDone: markDone,
      );
      thirdSubscription = third.listen(
        (value) {
          thirdValue = value;
          hasThird = true;
          emitIfReady();
        },
        onError: controller.addError,
        onDone: markDone,
      );
    },
    onPause: () {
      firstSubscription.pause();
      secondSubscription.pause();
      thirdSubscription.pause();
    },
    onResume: () {
      firstSubscription.resume();
      secondSubscription.resume();
      thirdSubscription.resume();
    },
    onCancel: () async {
      await firstSubscription.cancel();
      await secondSubscription.cancel();
      await thirdSubscription.cancel();
    },
  );

  return controller.stream;
}
