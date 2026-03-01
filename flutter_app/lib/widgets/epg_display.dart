import 'package:flutter/material.dart';
import '../models/epg_info.dart';

/// Widget to display EPG (Electronic Program Guide) information
/// Shows current and next program with graceful degradation for missing data
class EpgDisplay extends StatelessWidget {
  final EpgInfo nowPlaying;
  final EpgInfo nextProgram;
  final bool isDataAvailable;
  
  const EpgDisplay({
    super.key,
    required this.nowPlaying,
    required this.nextProgram,
    this.isDataAvailable = false,
  });
  
  /// Factory constructor for when EPG data is available
  factory EpgDisplay.fromChannelEpg(ChannelEpg channelEpg) {
    final currentAndNext = channelEpg.getCurrentAndNext();
    return EpgDisplay(
      nowPlaying: currentAndNext['now']!,
      nextProgram: currentAndNext['next']!,
      isDataAvailable: channelEpg.programs.isNotEmpty,
    );
  }
  
  /// Factory constructor for placeholder when no EPG data
  factory EpgDisplay.placeholder() {
    return EpgDisplay(
      nowPlaying: EpgInfo.placeholder(isNow: true),
      nextProgram: EpgInfo.placeholder(isNow: false),
      isDataAvailable: false,
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.5),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header with EPG status indicator
          Row(
            children: [
              Icon(
                Icons.schedule,
                color: isDataAvailable ? Colors.greenAccent : Colors.grey,
                size: 16,
              ),
              const SizedBox(width: 6),
              Text(
                'SCHEDULE',
                style: TextStyle(
                  color: isDataAvailable ? Colors.greenAccent : Colors.grey,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
              if (!isDataAvailable) ...[
                const SizedBox(width: 6),
                Tooltip(
                  message: 'EPG data not available for this channel',
                  child: Icon(
                    Icons.info_outline,
                    color: Colors.grey.shade400,
                    size: 14,
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 12),
          
          // Now Playing
          _buildProgramCard(
            context,
            label: 'NOW PLAYING',
            labelColor: Colors.redAccent,
            program: nowPlaying,
            showProgress: nowPlaying.isCurrentlyAiring,
          ),
          
          const SizedBox(height: 8),
          
          // Next Program
          _buildProgramCard(
            context,
            label: 'NEXT',
            labelColor: Colors.blueAccent,
            program: nextProgram,
            showProgress: false,
          ),
        ],
      ),
    );
  }
  
  Widget _buildProgramCard(
    BuildContext context, {
    required String label,
    required Color labelColor,
    required EpgInfo program,
    required bool showProgress,
  }) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(
          color: labelColor.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Label and time
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: labelColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(3),
                ),
                child: Text(
                  label,
                  style: TextStyle(
                    color: labelColor,
                    fontSize: 9,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  program.timeRange,
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 11,
                  ),
                ),
              ),
              Text(
                program.duration,
                style: const TextStyle(
                  color: Colors.white54,
                  fontSize: 10,
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 6),
          
          // Program title
          Text(
            program.programTitle,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          
          // Description (if available)
          if (program.description != null && program.description!.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              program.description!,
              style: const TextStyle(
                color: Colors.white60,
                fontSize: 12,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          
          // Category (if available)
          if (program.category != null && program.category!.isNotEmpty) ...[
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(
                  Icons.category_outlined,
                  size: 12,
                  color: Colors.white54,
                ),
                const SizedBox(width: 4),
                Text(
                  program.category!,
                  style: const TextStyle(
                    color: Colors.white54,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ],
          
          // Progress bar for current program
          if (showProgress && program.isCurrentlyAiring) ...[
            const SizedBox(height: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(2),
                  child: LinearProgressIndicator(
                    value: program.progress,
                    backgroundColor: Colors.white12,
                    valueColor: AlwaysStoppedAnimation<Color>(labelColor),
                    minHeight: 3,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${program.remainingMinutes} min remaining',
                  style: const TextStyle(
                    color: Colors.white54,
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

/// Compact EPG display for use in smaller spaces (e.g., overlay)
class CompactEpgDisplay extends StatelessWidget {
  final EpgInfo nowPlaying;
  final bool isDataAvailable;
  
  const CompactEpgDisplay({
    super.key,
    required this.nowPlaying,
    this.isDataAvailable = false,
  });
  
  factory CompactEpgDisplay.fromChannelEpg(ChannelEpg channelEpg) {
    final currentAndNext = channelEpg.getCurrentAndNext();
    return CompactEpgDisplay(
      nowPlaying: currentAndNext['now']!,
      isDataAvailable: channelEpg.programs.isNotEmpty,
    );
  }
  
  factory CompactEpgDisplay.placeholder() {
    return CompactEpgDisplay(
      nowPlaying: EpgInfo.placeholder(isNow: true),
      isDataAvailable: false,
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.6),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 4,
                height: 4,
                decoration: BoxDecoration(
                  color: isDataAvailable ? Colors.redAccent : Colors.grey,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                'NOW: ${nowPlaying.programTitle}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
          if (nowPlaying.isCurrentlyAiring) ...[
            const SizedBox(height: 2),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const SizedBox(width: 10),
                Text(
                  nowPlaying.timeRange,
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 9,
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  '• ${nowPlaying.remainingMinutes} min left',
                  style: const TextStyle(
                    color: Colors.white54,
                    fontSize: 9,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
