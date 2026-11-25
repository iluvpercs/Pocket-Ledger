import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';

import 'package:pocket_ledger_mobile/presentation/widgets/app_error_view.dart';
import 'package:pocket_ledger_mobile/presentation/widgets/brand_logo.dart';

void main() {
  testWidgets('brand logo renders the approved SVG asset', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: BrandLogo(size: 64)),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(SvgPicture), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('error view shows a local failure message', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: AppErrorView(message: 'Local database failed')),
      ),
    );

    expect(find.text('Local database failed'), findsOneWidget);
    expect(find.text('Could not open the local ledger'), findsOneWidget);
  });
}
