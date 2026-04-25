import 'package:flutter/material.dart';

/// Scan progress indicator widget (BL-015)
class ScanProgressBar extends StatelessWidget {
  final int progress;
  final int total;
  final int workingCount;
  final int failedCount;

  const ScanProgressBar({
    super.key,
    required this.progress,
    required this.total,
    required this.workingCount,
    required this.failedCount,
  });

  @override
  Widget build(BuildContext context) {
    final progressValue = total > 0 ? progress / total : 0.0;

    return Container(
      padding: const EdgeInsets.all(12),
      color: Theme.of(context).colorScheme.surfaceVariant,
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Scanning: $progress/$total',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              Text(
                '✓ $workingCount  ✗ $failedCount',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(value: progressValue),
        ],
      ),
    );
  }
}
