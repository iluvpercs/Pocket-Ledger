import 'package:flutter/material.dart';

import 'app_colors.dart';

/// Minimal dark Material 3 theme using the existing brand palette.
abstract final class AppTheme {
  static ThemeData get dark {
    const background = Color(0xFF0B0B0D);
    const surface = Color(0xFF151519);
    const outline = Color(0xFF2E2E35);

    final colorScheme = ColorScheme.dark(
      primary: AppColors.violet,
      onPrimary: AppColors.white,
      primaryContainer: AppColors.violet,
      onPrimaryContainer: AppColors.white,
      secondary: AppColors.lime,
      onSecondary: AppColors.onLime,
      secondaryContainer: AppColors.lime,
      onSecondaryContainer: AppColors.onLime,
      tertiary: AppColors.lime,
      onTertiary: AppColors.onLime,
      error: AppColors.violet,
      onError: AppColors.white,
      surface: surface,
      onSurface: AppColors.white,
      surfaceContainerHighest: surface,
      onSurfaceVariant: Color(0xFFB8B8C0),
      outline: outline,
      background: background,
      onBackground: AppColors.white,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: background,
      appBarTheme: const AppBarTheme(
        backgroundColor: background,
        foregroundColor: AppColors.white,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
      ),
      cardTheme: CardThemeData(
        color: surface,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: outline),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.violet,
          foregroundColor: AppColors.white,
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      iconTheme: const IconThemeData(color: AppColors.white),
      dividerTheme: const DividerThemeData(color: outline, space: 1),
    );
  }
}
