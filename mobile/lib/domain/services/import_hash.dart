import 'dart:convert';

import 'package:crypto/crypto.dart';

/// Exact desktop v4 dedupe hash. Category, account and reference are not
/// inputs; this keeps exported and re-imported rows recognisable.
String normaliseDescription(Object? description) =>
    description.toString().toLowerCase().trim().split(RegExp(r'\s+')).join(' ');

String buildImportHash({
  required String dateIso,
  required int signedMinor,
  required String description,
  int occurrence = 0,
}) {
  final payload = [
    dateIso,
    signedMinor.toString(),
    normaliseDescription(description),
    occurrence.toString(),
  ].join('|');
  return sha256.convert(utf8.encode(payload)).toString();
}

/// Groups identical `(date, signed minor amount, normalised description)`
/// keys in file order and returns the zero-based occurrence for each row.
List<int> assignOccurrences(List<String> keys) {
  final seen = <String, int>{};
  return [
    for (final key in keys)
      () {
        final next = seen[key] ?? 0;
        seen[key] = next + 1;
        return next;
      }(),
  ];
}
