import 'package:material_ui/material_ui.dart';

import 'package:pocket_ledger_mobile/core/theme/app_colors.dart';
import 'package:pocket_ledger_mobile/domain/entities/dashboard_summary.dart';
import 'package:pocket_ledger_mobile/presentation/common/formatters.dart';

class SixMonthChart extends StatelessWidget {
  const SixMonthChart({super.key, required this.points});

  final List<MonthSeriesPoint> points;

  @override
  Widget build(BuildContext context) {
    final palette = Theme.of(context).colorScheme;
    final max = points.fold<int>(
      1,
      (current, point) => [
        point.incomeMinor,
        point.expenseMinor,
        current,
      ].reduce((a, b) => a > b ? a : b),
    );
    final hasData = points.any(
      (point) => point.incomeMinor > 0 || point.expenseMinor > 0,
    );
    if (!hasData) {
      return const Text('No income or expense in the last six months yet.');
    }

    return Column(
      children: [
        SizedBox(
          height: 170,
          child: CustomPaint(
            painter: _BarsPainter(points: points, max: max, outline: palette.outline),
            child: const SizedBox.expand(),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            for (final point in points)
              Expanded(
                child: Text(
                  shortMonthLabel(point.year, point.month),
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
          ],
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 16,
          children: [
            _Legend(color: AppColors.lime, label: 'Income'),
            _Legend(color: AppColors.violet, label: 'Expense'),
          ],
        ),
      ],
    );
  }
}

class _Legend extends StatelessWidget {
  const _Legend({required this.color, required this.label});

  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 12, height: 12, color: color),
        const SizedBox(width: 6),
        Text(label),
      ],
    );
  }
}

class _BarsPainter extends CustomPainter {
  const _BarsPainter({
    required this.points,
    required this.max,
    required this.outline,
  });

  final List<MonthSeriesPoint> points;
  final int max;
  final Color outline;

  @override
  void paint(Canvas canvas, Size size) {
    final baseline = size.height - 1;
    final linePaint = Paint()
      ..color = outline
      ..strokeWidth = 1;
    for (var row = 1; row <= 3; row++) {
      final y = baseline - (size.height * row / 4);
      canvas.drawLine(Offset(0, y), Offset(size.width, y), linePaint);
    }

    final groupWidth = size.width / points.length;
    final barWidth = groupWidth * 0.3;
    for (var index = 0; index < points.length; index++) {
      final point = points[index];
      final center = groupWidth * (index + 0.5);
      _drawBar(
        canvas,
        center - barWidth - 2,
        baseline,
        barWidth,
        point.incomeMinor / max * (size.height - 12),
        AppColors.lime,
      );
      _drawBar(
        canvas,
        center + 2,
        baseline,
        barWidth,
        point.expenseMinor / max * (size.height - 12),
        AppColors.violet,
      );
    }
  }

  void _drawBar(
    Canvas canvas,
    double left,
    double baseline,
    double width,
    double height,
    Color color,
  ) {
    final rect = RRect.fromRectAndRadius(
      Rect.fromLTWH(left, baseline - height, width, height),
      const Radius.circular(4),
    );
    canvas.drawRRect(rect, Paint()..color = color);
  }

  @override
  bool shouldRepaint(covariant _BarsPainter oldDelegate) =>
      oldDelegate.points != points || oldDelegate.max != max;
}
