import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../data/channel_descriptions.dart';
import '../models/channel.dart';
import '../models/epg_info.dart';
import '../providers/channel_provider.dart';
import '../services/shared_db_service.dart';
import 'quality_badge.dart';

/// Reusable channel list item widget (BL-015)
class ChannelTile extends StatelessWidget {
  final Channel channel;
  final VoidCallback onTap;
  /// When true, renders a denser tile for landscape grid use —
  /// hides info/EPG/quality icons, smaller avatar, single-line subtitle.
  final bool compact;

  const ChannelTile({
    super.key,
    required this.channel,
    required this.onTap,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    return Consumer<ChannelProvider>(
      builder: (context, provider, _) {
        // Build subtitle with category, quality, bitrate, country, and EPG
        final subtitleParts = <String>[];

        if (channel.category != null) {
          subtitleParts.add(channel.category!);
        }

        if (channel.formattedBitrate != null) {
          subtitleParts.add(channel.formattedBitrate!);
        }

        if (channel.country != null && channel.country != 'Unknown') {
          subtitleParts.add(channel.country!);
        }

        final metaLine = subtitleParts.join(' • ');

        // EPG current program subtitle
        final currentProgram = provider.getCurrentProgram(channel.name);
        final hasEpg = provider.hasEpgData(channel.name);

        return ListTile(
          dense: compact,
          visualDensity: compact ? VisualDensity.compact : null,
          leading: _buildLeading(),
          title: Text(
            channel.name,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: compact ? const TextStyle(fontSize: 13) : null,
          ),
          subtitle: compact
              ? (metaLine.isNotEmpty
                  ? Text(metaLine, maxLines: 1, overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(fontSize: 11))
                  : null)
              : _buildSubtitle(context, metaLine, currentProgram),
          trailing: _buildTrailing(context, provider, hasEpg),
          onTap: onTap,
          onLongPress: () => _showChannelContextMenu(context),
        );
      },
    );
  }

  /// Build a two-line subtitle: meta info + EPG current program.
  Widget? _buildSubtitle(
    BuildContext context,
    String metaLine,
    EpgInfo? currentProgram,
  ) {
    if (metaLine.isEmpty && currentProgram == null) return null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (metaLine.isNotEmpty)
          Text(
            metaLine,
            style: Theme.of(context).textTheme.bodySmall,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        if (currentProgram != null)
          Text(
            '▶ ${currentProgram.programTitle}',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.green.shade700,
                  fontSize: 11,
                ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
      ],
    );
  }

  Widget _buildLeading() {
    final size = compact ? 28.0 : 40.0;
    return CircleAvatar(
      radius: size / 2,
      backgroundColor: channel.isWorking ? Colors.green : Colors.grey,
      child: channel.logo != null
          ? ClipOval(
              child: Image.network(
                channel.logo!,
                width: size,
                height: size,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Icon(
                  channel.mediaType == 'Radio' ? Icons.radio : Icons.tv,
                  color: Colors.white,
                  size: compact ? 14 : 24,
                ),
              ),
            )
          : Icon(
              channel.mediaType == 'Radio' ? Icons.radio : Icons.tv,
              color: Colors.white,
              size: compact ? 14 : 24,
            ),
    );
  }

  Widget _buildTrailing(
    BuildContext context,
    ChannelProvider provider,
    bool hasEpg,
  ) {
    final isFavorite = provider.isFavorite(channel);
    final iconSize = compact ? 16.0 : 20.0;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Channel info (i) button — hidden in compact/landscape mode
        if (!compact)
          Builder(builder: (ctx) {
            final description =
                ChannelDescriptions.getDescription(channel.name);
            return InkWell(
              onTap: () => _showInfoSnackBar(
                ctx,
                description ?? '${channel.name} — no additional information available.',
              ),
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.all(4.0),
                child: Icon(
                  Icons.info_outline,
                  color: description != null
                      ? Colors.blue.shade400
                      : Colors.grey.shade500,
                  size: iconSize,
                ),
              ),
            );
          }),
        if (!compact) const SizedBox(width: 2),
        // EPG guide icon — hidden in compact mode
        if (!compact)
          InkWell(
            onTap: () => _showEpgSheet(context, provider),
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(4.0),
              child: Icon(
                Icons.schedule,
                color: hasEpg ? Colors.green : Colors.grey.shade400,
                size: iconSize,
              ),
            ),
          ),
        if (!compact) const SizedBox(width: 2),
        // Favorite toggle button — always visible
        InkWell(
          onTap: () => provider.toggleFavorite(channel),
          child: Padding(
            padding: EdgeInsets.all(compact ? 2.0 : 4.0),
            child: Icon(
              isFavorite ? Icons.favorite : Icons.favorite_border,
              color: isFavorite ? Colors.red : Colors.grey,
              size: iconSize,
            ),
          ),
        ),
        SizedBox(width: compact ? 2 : 4),
        // Quality badge — hidden in compact mode
        if (!compact && channel.resolution != null) ...[
          QualityBadge(resolution: channel.resolution, compact: true),
          const SizedBox(width: 4),
        ],
        // Media type indicator
        if (channel.mediaType == 'Radio')
          Icon(Icons.radio, size: compact ? 12 : 16, color: Colors.blue),
        SizedBox(width: compact ? 2 : 4),
        // Working status indicator
        Icon(
          channel.isWorking ? Icons.check_circle : Icons.error,
          color: channel.isWorking ? Colors.green : Colors.red,
          size: iconSize,
        ),
      ],
    );
  }

  /// Show a context menu on long-press with channel actions.
  void _showChannelContextMenu(BuildContext context) {
    final RenderBox? renderBox = context.findRenderObject() as RenderBox?;
    if (renderBox == null) return;

    final offset = renderBox.localToGlobal(Offset.zero);
    final size = renderBox.size;

    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(
        offset.dx + size.width / 2,
        offset.dy + size.height / 2,
        offset.dx + size.width,
        offset.dy + size.height,
      ),
      items: [
        const PopupMenuItem(
          value: 'report',
          child: Row(
            children: [
              Icon(Icons.report_problem, color: Colors.red, size: 20),
              SizedBox(width: 8),
              Text('Report Broken 🔴'),
            ],
          ),
        ),
      ],
    ).then((value) {
      if (value == 'report') {
        _reportBrokenChannel(context);
      }
    });
  }

  /// Report this channel as broken to the shared database.
  void _reportBrokenChannel(BuildContext context) {
    final urlHash = SharedDbService.hashUrl(channel.url);
    SharedDbService.reportBrokenChannel(urlHash);

    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: const Text('Channel reported. Thanks for helping! 🙏'),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          duration: const Duration(seconds: 3),
        ),
      );
  }

  /// Show a SnackBar with the channel's description.
  void _showInfoSnackBar(BuildContext context, String description) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            description,
            style: const TextStyle(fontSize: 14),
          ),
          duration: const Duration(seconds: 4),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          action: SnackBarAction(
            label: 'OK',
            onPressed: () {},
          ),
        ),
      );
  }

  /// Show the EPG bottom sheet with current & next program info.
  void _showEpgSheet(BuildContext context, ChannelProvider provider) {
    final epg = provider.getEpgForChannel(channel.name);
    final current = epg?.currentProgram;
    final next = epg?.nextProgram;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        final isSheetLandscape = MediaQuery.of(ctx).orientation == Orientation.landscape;
        return ConstrainedBox(
          constraints: BoxConstraints(
            maxHeight: MediaQuery.of(ctx).size.height * (isSheetLandscape ? 0.8 : 0.6),
          ),
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
              // Handle
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              // Channel name header
              Row(
                children: [
                  Icon(
                    Icons.live_tv,
                    color: Colors.green.shade700,
                    size: 22,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      channel.name,
                      style: Theme.of(ctx).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                'Program Guide',
                style: Theme.of(ctx).textTheme.bodySmall?.copyWith(
                      color: Colors.grey,
                    ),
              ),

              const Divider(height: 24),

              // "Now" section
              _EpgProgramRow(
                label: 'Now',
                labelColor: Colors.green,
                program: current,
                showProgress: true,
              ),

              const SizedBox(height: 16),

              // "Next" section
              _EpgProgramRow(
                label: 'Next',
                labelColor: Colors.blue,
                program: next,
                showProgress: false,
              ),

              if (current == null && next == null) ...[
                const SizedBox(height: 8),
                Text(
                  'No schedule available for this channel.',
                  style: Theme.of(ctx).textTheme.bodySmall?.copyWith(
                        color: Colors.grey,
                        fontStyle: FontStyle.italic,
                      ),
                ),
              ],
              ],
            ),
          ),
        );
      },
    );
  }
}

/// A single row in the EPG bottom sheet showing a program's details.
class _EpgProgramRow extends StatelessWidget {
  final String label;
  final Color labelColor;
  final EpgInfo? program;
  final bool showProgress;

  const _EpgProgramRow({
    required this.label,
    required this.labelColor,
    required this.program,
    required this.showProgress,
  });

  @override
  Widget build(BuildContext context) {
    if (program == null) {
      return Row(
        children: [
          _buildLabel(context),
          const SizedBox(width: 12),
          Text(
            'No data available',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.grey,
                  fontStyle: FontStyle.italic,
                ),
          ),
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildLabel(context),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    program!.programTitle,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    program!.timeRange,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey.shade600,
                        ),
                  ),
                  if (program!.description != null &&
                      program!.description!.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      program!.description!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey,
                            fontSize: 11,
                          ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ],
              ),
            ),
            // Duration / remaining badge
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: labelColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                showProgress && program!.isCurrentlyAiring
                    ? '${program!.remainingMinutes}m left'
                    : program!.duration,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: labelColor,
                      fontWeight: FontWeight.w500,
                      fontSize: 11,
                    ),
              ),
            ),
          ],
        ),
        // Progress bar for currently-airing program
        if (showProgress && program!.isCurrentlyAiring) ...[
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: program!.progress,
              backgroundColor: Colors.grey.shade200,
              valueColor: AlwaysStoppedAnimation<Color>(labelColor),
              minHeight: 4,
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildLabel(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: labelColor,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
