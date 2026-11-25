import 'package:flutter_test/flutter_test.dart';

import 'package:pocket_ledger_mobile/domain/entities/account.dart';
import 'package:pocket_ledger_mobile/domain/entities/csv_import.dart';
import 'package:pocket_ledger_mobile/domain/entities/ledger_settings.dart';
import 'package:pocket_ledger_mobile/domain/services/csv_export_service.dart';
import 'package:pocket_ledger_mobile/domain/services/csv_import_service.dart';
import 'package:pocket_ledger_mobile/domain/services/import_hash.dart';
import 'package:pocket_ledger_mobile/domain/value_objects/transaction_type.dart';

import '../support/test_data.dart';

CsvPreview _preview(
  CsvFileInfo file, {
  required Account account,
  LedgerDateFormat? dateFormat,
  bool roundAmounts = false,
  Map<String, Set<String>> existing = const {},
}) {
  return CsvImportService.preview(
    file: file,
    mapping: file.mapping,
    dateFormat: dateFormat ?? file.suggestedDateFormat,
    defaultAccount: account,
    defaultCurrency: account.currencyCode,
    accounts: [account],
    roundAmounts: roundAmounts,
    sourceFile: 'test.csv',
    existingImportHashAccounts: existing,
  );
}

void main() {
  group('import hash', () {
    test('matches desktop sha256 payload exactly', () {
      expect(
        buildImportHash(
          dateIso: '2026-11-25',
          signedMinor: -1234,
          description: 'Lunch',
        ),
        'deaeeaf91f55d2353ef5b240d42f292f6fc4631bea87388b309343ce518726bd',
      );
      expect(normaliseDescription('  LUNCH   today '), 'lunch today');
    });

    test('assigns zero-based occurrence per identical key', () {
      expect(
        assignOccurrences(['a', 'b', 'a', 'a']),
        [0, 0, 1, 2],
      );
    });
  });

  group('CsvImportService', () {
    test('detects delimiter, headers, mapping and suggested date format', () {
      const text = 'Date;Description;Amount;Category\n'
          '25/11/2026;Lunch;-12.34;Food\n';
      final file = CsvImportService.inspect(text);

      expect(file.delimiter, ';');
      expect(file.delimiterLabel, 'Semicolon');
      expect(file.hasHeaderRow, isTrue);
      expect(file.headers, ['Date', 'Description', 'Amount', 'Category']);
      expect(file.mapping.indexOf(CsvFieldKind.date), 0);
      expect(file.mapping.indexOf(CsvFieldKind.description), 1);
      expect(file.mapping.indexOf(CsvFieldKind.amount), 2);
      expect(file.mapping.indexOf(CsvFieldKind.category), 3);
      expect(file.suggestedDateFormat, LedgerDateFormat.slashDmy);
      expect(file.rows, hasLength(1));
    });

    test('detects tab and pipe delimiters', () {
      expect(CsvImportService.detectDelimiter('a\tb\nc\td'), '\t');
      expect(CsvImportService.detectDelimiter('a|b\nc|d'), '|');
    });

    test('parses signed amount into positive minor units and direction', () {
      final account = testAccount();
      final file = CsvImportService.inspect(
        'date,description,amount,category\n'
        '25/11/2026,Lunch,-12.34,Food\n',
      );
      final row = _preview(file, account: account).rows.single;

      expect(row.status, CsvRowStatus.valid);
      expect(row.dateIso, '2026-11-25');
      expect(row.signedMinor, -1234);
      expect(row.amountMinor, 1234);
      expect(row.type, TransactionType.expense);
      expect(row.category, 'Food');
      expect(row.description, 'Lunch');
      expect(
        row.importHash,
        'deaeeaf91f55d2353ef5b240d42f292f6fc4631bea87388b309343ce518726bd',
      );
    });

    test('credit cell becomes income and debit cell becomes expense', () {
      final account = testAccount();
      final creditFile = CsvImportService.inspect(
        'date,narration,debit,credit\n25/11/2026,Refund,,50.00\n',
      );
      final debitFile = CsvImportService.inspect(
        'date,narration,debit,credit\n25/11/2026,Fee,5.00,\n',
      );

      final credit = _preview(creditFile, account: account).rows.single;
      final debit = _preview(debitFile, account: account).rows.single;
      expect(credit.type, TransactionType.income);
      expect(credit.amountMinor, 5_000);
      expect(debit.type, TransactionType.expense);
      expect(debit.amountMinor, 500);
    });

    test('strict preview rejects surplus precision and rounding accepts it',
        () {
      final account = testAccount();
      final file = CsvImportService.inspect(
        'date,description,amount\n25/11/2026,Coffee,-12.345\n',
      );

      final strictRow = _preview(file, account: account).rows.single;
      expect(strictRow.status, CsvRowStatus.invalid);
      expect(strictRow.error, contains('more than 2 decimal places'));

      final roundedRow =
          _preview(file, account: account, roundAmounts: true).rows.single;
      expect(roundedRow.status, CsvRowStatus.valid);
      expect(roundedRow.amountMinor, 1_235);
    });

    test('duplicate hashes are scoped to the target account', () {
      final account = testAccount();
      final other = testAccount(name: 'Other');
      final file = CsvImportService.inspect(
        'date,description,amount\n2026-11-25,Coffee,-5.00\n'
        '2026-11-25,Coffee,-5.00\n',
      );
      final firstHash = buildImportHash(
        dateIso: '2026-11-25',
        signedMinor: -500,
        description: 'Coffee',
        occurrence: 0,
      );

      final sameAccount = _preview(
        file,
        account: account,
        existing: {firstHash: {account.uuid.value}},
      );
      expect(
        sameAccount.rows.map((row) => row.status).toList(),
        [CsvRowStatus.duplicate, CsvRowStatus.valid],
      );

      final otherAccount = _preview(
        file,
        account: account,
        existing: {firstHash: {other.uuid.value}},
      );
      expect(
        otherAccount.rows.map((row) => row.status).toList(),
        [CsvRowStatus.valid, CsvRowStatus.valid],
      );
    });

    test('exported CSV imports back into the same signed minor values', () {
      final account = testAccount();
      final transaction = testTransaction(
        account: account,
        id: 1,
        amountMinor: 1_250,
        category: 'Food',
        description: 'Coffee',
      );

      final csv = CsvExportService.encode([transaction], [account]);
      final file = CsvImportService.inspect(csv);
      final row = _preview(
        file,
        account: account,
        dateFormat: LedgerDateFormat.iso,
      ).rows.single;

      expect(row.status, CsvRowStatus.valid);
      expect(row.dateIso, transaction.transactionDate);
      expect(row.amountMinor, 1_250);
      expect(row.type, TransactionType.expense);
      expect(row.description, 'Coffee');
      expect(
        row.importHash,
        buildImportHash(
          dateIso: transaction.transactionDate,
          signedMinor: -1_250,
          description: 'Coffee',
        ),
      );
    });
  });
}
