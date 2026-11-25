import 'package:material_ui/material_ui.dart';

import 'app_colors.dart';

/// Material 3 themes using the existing brand palette.
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
    );

    return _theme(
      colorScheme: colorScheme,
      background: background,
      surface: surface,
      outline: outline,
    );
  }

  static ThemeData get light {
    const background = Color(0xFFF7F7FA);
    const surface = Color(0xFFFFFFFF);
    const outline = Color(0xFFD8D8E0);

    final colorScheme = ColorScheme.light(
      primary: AppColors.violet,
      onPrimary: AppColors.white,
      primaryContainer: Color(0xFFEDE3FF),
      onPrimaryContainer: Color(0xFF25104A),
      secondary: Color(0xFF4B6B00),
      onSecondary: AppColors.white,
      secondaryContainer: Color(0xFFE4FFA8),
      onSecondaryContainer: Color(0xFF1F2B00),
      tertiary: Color(0xFF4B6B00),
      onTertiary: AppColors.white,
      error: Color(0xFFB3261E),
      onError: AppColors.white,
      surface: surface,
      onSurface: Color(0xFF101014),
      surfaceContainerHighest: background,
      onSurfaceVariant: Color(0xFF4E4E57),
      outline: outline,
    );

    return _theme(
      colorScheme: colorScheme,
      background: background,
      surface: surface,
      outline: outline,
    );
  }

  static ThemeData _theme({
    required ColorScheme colorScheme,
    required Color background,
    required Color surface,
    required Color outline,
  }) {
    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: background,
      appBarTheme: AppBarTheme(
        backgroundColor: background,
        foregroundColor: colorScheme.onSurface,
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
          side: BorderSide(color: outline),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: colorScheme.primary,
          foregroundColor: colorScheme.onPrimary,
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      iconTheme: IconThemeData(color: colorScheme.onSurface),
      dividerTheme: DividerThemeData(color: outline, space: 1),
    );
  }
}
