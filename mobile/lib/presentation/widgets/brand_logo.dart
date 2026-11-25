import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import 'package:pocket_ledger_mobile/core/theme/app_colors.dart';

/// Renders the unchanged approved SVG. The theme sets `currentColor` without
/// applying a blanket colour filter, so the lime accents are preserved.
class BrandLogo extends StatelessWidget {
  const BrandLogo({super.key, this.size = 96});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: 'Pocket Ledger logo',
      child: SvgPicture(
        const SvgAssetLoader(
          'assets/icons/Mobile.svg',
          theme: SvgTheme(currentColor: AppColors.white),
        ),
        width: size,
        height: size,
      ),
    );
  }
}
