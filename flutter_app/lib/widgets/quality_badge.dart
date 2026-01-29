import 'package:flutter/material.dart';

/// Quality badge widget showing HD/SD/4K indicators (BL-016)
class QualityBadge extends StatelessWidget {
  final String? resolution;
  final bool compact;

  const QualityBadge({
    super.key,
    required this.resolution,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    final quality = _getQualityInfo(resolution);
    if (quality == null) return const SizedBox.shrink();

    return Container(
      padding: compact 
          ? const EdgeInsets.symmetric(horizontal: 4, vertical: 2)
          : const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
      decoration: BoxDecoration(
        color: quality.color,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        quality.label,
        style: TextStyle(
          color: Colors.white,
          fontSize: compact ? 9 : 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  /// Get quality information based on resolution
  _QualityInfo? _getQualityInfo(String? resolution) {
    if (resolution == null) return null;

    // Extract height from resolution (e.g., "1920x1080" -> 1080)
    final heightMatch = RegExp(r'x?(\d{3,4})p?').firstMatch(resolution);
    if (heightMatch == null) return null;

    final height = int.tryParse(heightMatch.group(1) ?? '0') ?? 0;

    if (height >= 2160) {
      return _QualityInfo(label: '4K', color: Colors.purple);
    } else if (height >= 1080) {
      return _QualityInfo(label: 'FHD', color: Colors.blue);
    } else if (height >= 720) {
      return _QualityInfo(label: 'HD', color: Colors.green);
    } else if (height > 0) {
      return _QualityInfo(label: 'SD', color: Colors.orange);
    }

    return null;
  }
}

class _QualityInfo {
  final String label;
  final Color color;

  _QualityInfo({required this.label, required this.color});
}
