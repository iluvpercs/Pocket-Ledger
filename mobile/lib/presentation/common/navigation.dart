import 'package:material_ui/material_ui.dart';
import 'package:go_router/go_router.dart';

/// Closes a pushed page when possible. Screens reached with `go` have no
/// stack entry, so they fall back to a known tab route instead of throwing
/// `GoError: There is nothing to pop`.
void closeOrGo(BuildContext context, String fallbackRoute) {
  if (!context.mounted) return;
  if (context.canPop()) {
    context.pop();
  } else {
    context.go(fallbackRoute);
  }
}
