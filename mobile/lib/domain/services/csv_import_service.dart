import 'package:csv/csv.dart';
import 'package:intl/intl.dart';

import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/csv_import.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/services/import_hash.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/currency_code.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/money.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/identifier.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

final class CsvFileInfo {
  const CsvFileInfo({
    required this.rows,
    required this.headers,
    required this.delimiter,
    required this.hasHeaderRow,
    required this.mapping,
    required this.suggestedDateFormat,
  });

  final List<List<String>> rows;
  final List<String> headers;
  final String delimiter;
  final bool hasHeaderRow;
  final CsvMapping mapping;
  final LedgerDateFormat suggestedDateFormat;

  String get delimiterLabel => switch (delimiter) {
        '\t' => 'Tab',
        ';' => 'Semicolon',
        '|' => 'Pipe',
        _ => 'Comma',
      };
}

/// Pure-Dart CSV parsing. It never touches the network or the file system;
/// the caller supplies text read through the system picker.
abstract final class CsvImportService {
  static CsvFileInfo inspect(String rawText) {
    final text = rawText.replaceFirst('\uFEFF', '');
    final delimiter = detectDelimiter(text);
    final decoded = Csv(
      fieldDelimiter: delimiter,
      autoDetect: false,
      skipEmptyLines: true,
    ).decode(text);
    final rows = decoded
        .map(
          (row) => row.map((cell) => cell?.toString().trim() ?? '').toList(),
        )
        .where((row) => row.any((cell) => cell.isNotEmpty))
        .toList();
    if (rows.isEmpty) {
      return CsvFileInfo(
        rows: const [],
        headers: const [],
        delimiter: delimiter,
        hasHeaderRow: false,
        mapping: const CsvMapping([]),
        suggestedDateFormat: LedgerDateFormat.iso,
      );
    }

    final first = rows.first;
    final recognised = CsvFieldKind.values
        .where(
          (kind) => kind.aliases.isNotEmpty && first.any(
            (cell) => kind.aliases.contains(_normaliseHeader(cell)),
          ),
        )
        .length;
    final hasHeaderRow = recognised >= 2;
    final headers = hasHeaderRow
        ? List<String>.from(first)
        : [
            for (var index = 0; index < first.length; index++)
              'Column ${index + 1}',
          ];
    final dataRows = hasHeaderRow ? rows.skip(1).toList() : rows;
    final mapping = CsvMapping.detect(headers);
    final dateIndex = mapping.indexOf(CsvFieldKind.date);

    return CsvFileInfo(
      rows: dataRows,
      headers: headers,
      delimiter: delimiter,
      hasHeaderRow: hasHeaderRow,
      mapping: mapping,
      suggestedDateFormat: _detectDateFormat(dataRows, dateIndex),
    );
  }

  static CsvPreview preview({
    required CsvFileInfo file,
    required CsvMapping mapping,
    required LedgerDateFormat dateFormat,
    required Account defaultAccount,
    required CurrencyCode defaultCurrency,
    required Iterable<Account> accounts,
    required bool roundAmounts,
    required String sourceFile,
    required Map<String, Set<String>> existingImportHashAccounts,
  }) {
    final liveAccounts = accounts.where((account) => account.isLive).toList();
    final byName = <String, Account>{};
    for (final account in liveAccounts) {
      byName[account.name.toLowerCase()] = account;
    }
    final byCurrency = <String, Account>{};
    for (final account in liveAccounts) {
      byCurrency.putIfAbsent(account.currencyCode.value, () => account);
    }

    final drafts = <_DraftRow>[];
    for (var index = 0; index < file.rows.length; index++) {
      final row = file.rows[index];
      final line = file.hasHeaderRow ? index + 2 : index + 1;
      drafts.add(
        _parseRow(
          row: row,
          line: line,
          mapping: mapping,
          dateFormat: dateFormat,
          defaultAccount: defaultAccount,
          defaultCurrency: defaultCurrency,
          accountsByName: byName,
          accountsByCurrency: byCurrency,
          roundAmounts: roundAmounts,
        ),
      );
    }

    final occurrenceKeys = [
      for (final draft in drafts)
        if (draft.error == null)
          '${draft.dateIso}|${draft.signedMinor}|${normaliseDescription(draft.description)}',
    ];
    final occurrences = assignOccurrences(occurrenceKeys);
    var occurrenceIndex = 0;
    final seenHashes = <String, Set<String>>{};
    final parsedRows = <ParsedCsvRow>[];

    for (final draft in drafts) {
      if (draft.error != null) {
        parsedRows.add(
          ParsedCsvRow(
            line: draft.line,
            status: CsvRowStatus.invalid,
            error: draft.error,
          ),
        );
        continue;
      }

      final occurrence = occurrences[occurrenceIndex++];
      final hash = buildImportHash(
        dateIso: draft.dateIso!,
        signedMinor: draft.signedMinor!,
        description: draft.description,
        occurrence: occurrence,
      );
      final accountUuid = draft.accountUuid!.value;
      final existingAccounts = existingImportHashAccounts[hash];
      final seenAccounts = seenHashes[hash];
      final isDuplicate = existingAccounts?.contains(accountUuid) == true ||
          seenAccounts?.contains(accountUuid) == true;

      parsedRows.add(
        ParsedCsvRow(
          line: draft.line,
          status: isDuplicate ? CsvRowStatus.duplicate : CsvRowStatus.valid,
          dateIso: draft.dateIso,
          amountMinor: draft.amountMinor,
          type: draft.type,
          category: draft.category,
          description: draft.description,
          accountUuid: draft.accountUuid,
          currencyCode: draft.currencyCode,
          signedMinor: draft.signedMinor,
          importHash: hash,
          reference: draft.reference,
          accountLabel: draft.account?.name,
          error: isDuplicate ? 'Already imported' : null,
        ),
      );
      if (!isDuplicate) {
        seenHashes.putIfAbsent(hash, () => <String>{}).add(accountUuid);
      }
    }

    return CsvPreview(
      headers: file.headers,
      delimiterLabel: file.delimiterLabel,
      hasHeaderRow: file.hasHeaderRow,
      mapping: mapping,
      dateFormat: dateFormat,
      roundAmounts: roundAmounts,
      sourceFile: sourceFile,
      rows: parsedRows,
    );
  }

  static String detectDelimiter(String rawText) {
    final text = rawText.replaceFirst('\uFEFF', '');
    final firstLine = text.split(RegExp(r'\r?\n')).first;
    final candidates = [',', ';', '\t', '|'];
    var best = ',';
    var bestCount = 0;
    var inQuotes = false;
    final counts = <String, int>{for (final candidate in candidates) candidate: 0};
    for (var index = 0; index < firstLine.length; index++) {
      final character = firstLine[index];
      if (character == '"') {
        if (inQuotes && index + 1 < firstLine.length && firstLine[index + 1] == '"') {
          index++;
        } else {
          inQuotes = !inQuotes;
        }
        continue;
      }
      if (inQuotes) continue;
      if (counts.containsKey(character)) counts[character] = counts[character]! + 1;
    }
    for (final candidate in candidates) {
      if (counts[candidate]! > bestCount) {
        best = candidate;
        bestCount = counts[candidate]!;
      }
    }
    return best;
  }

  static LedgerDateFormat _detectDateFormat(
    List<List<String>> rows,
    int? dateIndex,
  ) {
    if (dateIndex == null) return LedgerDateFormat.iso;
    final samples = rows
        .map((row) => dateIndex < row.length ? row[dateIndex] : '')
        .where((value) => value.isNotEmpty)
        .take(20)
        .toList();
    if (samples.isEmpty) return LedgerDateFormat.iso;
    for (final format in LedgerDateFormat.values) {
      if (samples.every((value) => _parseDate(value, format) != null)) {
        return format;
      }
    }
    return LedgerDateFormat.iso;
  }

  static String? _parseDate(String value, LedgerDateFormat format) {
    try {
      final parsed = DateFormat(format.pattern, 'en_US').parseStrict(value);
      return DateFormat('yyyy-MM-dd').format(parsed);
    } catch (_) {
      return null;
    }
  }

  static _DraftRow _parseRow({
    required List<String> row,
    required int line,
    required CsvMapping mapping,
    required LedgerDateFormat dateFormat,
    required Account defaultAccount,
    required CurrencyCode defaultCurrency,
    required Map<String, Account> accountsByName,
    required Map<String, Account> accountsByCurrency,
    required bool roundAmounts,
  }) {
    String cell(CsvFieldKind kind) {
      final index = mapping.indexOf(kind);
      if (index == null || index >= row.length) return '';
      return row[index].trim();
    }

    final rawDate = cell(CsvFieldKind.date);
    final dateIso = rawDate.isEmpty ? null : _parseDate(rawDate, dateFormat);
    if (dateIso == null) {
      return _DraftRow(line: line, error: 'Date is missing or has the wrong format.');
    }

    final accountName = cell(CsvFieldKind.account);
    final rawCurrency = cell(CsvFieldKind.currency);
    CurrencyCode currencyCode;
    try {
      currencyCode = rawCurrency.isEmpty
          ? defaultCurrency
          : CurrencyCode.parse(rawCurrency);
    } catch (error) {
      return _DraftRow(line: line, error: 'Currency is not supported: $rawCurrency');
    }

    Account? account;
    if (accountName.isNotEmpty) account = accountsByName[accountName.toLowerCase()];
    account ??= accountsByCurrency[currencyCode.value];
    account ??= defaultAccount;

    final precision = account.precision;
    final rawDebit = cell(CsvFieldKind.debit);
    final rawCredit = cell(CsvFieldKind.credit);
    int signedMinor;
    try {
      if (rawDebit.isNotEmpty && rawCredit.isNotEmpty) {
        throw const FormatException('Both debit and credit cells are filled.');
      }
      if (rawDebit.isNotEmpty || rawCredit.isNotEmpty) {
        final magnitude = MinorAmount.parse(
          rawDebit.isNotEmpty ? rawDebit : rawCredit,
          precision,
          strict: !roundAmounts,
        ).minor.abs();
        signedMinor = rawDebit.isNotEmpty ? -magnitude : magnitude;
      } else {
        final rawAmount = cell(CsvFieldKind.amount);
        if (rawAmount.isEmpty) {
          throw const FormatException('Amount is missing.');
        }
        signedMinor = MinorAmount.parse(
          rawAmount,
          precision,
          strict: !roundAmounts,
        ).minor;
      }
      if (signedMinor == 0) {
        throw const FormatException('Amount must not be zero.');
      }
    } catch (error) {
      return _DraftRow(line: line, error: _cleanError(error));
    }

    final category = cell(CsvFieldKind.category);
    final description = cell(CsvFieldKind.description);
    return _DraftRow(
      line: line,
      dateIso: dateIso,
      signedMinor: signedMinor,
      amountMinor: signedMinor.abs(),
      type: signedMinor > 0 ? TransactionType.income : TransactionType.expense,
      category: category.isEmpty ? 'Imported' : category,
      description: description.isEmpty ? category : description,
      account: account,
      accountUuid: account.uuid,
      currencyCode: account.currencyCode,
      reference: cell(CsvFieldKind.reference).isEmpty
          ? null
          : cell(CsvFieldKind.reference),
    );
  }

  static String _cleanError(Object error) => error.toString().replaceFirst(
        'Exception: ',
        '',
      );

  static String _normaliseHeader(String value) =>
      value.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '');
}

class _DraftRow {
  const _DraftRow({
    required this.line,
    this.error,
    this.dateIso,
    this.signedMinor,
    this.amountMinor,
    this.type,
    this.category,
    this.description = '',
    this.account,
    this.accountUuid,
    this.currencyCode,
    this.reference,
  });

  final int line;
  final String? error;
  final String? dateIso;
  final int? signedMinor;
  final int? amountMinor;
  final TransactionType? type;
  final String? category;
  final String description;
  final Account? account;
  final Uuid? accountUuid;
  final CurrencyCode? currencyCode;
  final String? reference;
}
