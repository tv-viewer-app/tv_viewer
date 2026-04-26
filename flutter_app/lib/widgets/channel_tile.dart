import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
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

        return Dismissible(
          key: ValueKey('dismiss_${channel.url}'),
          direction: DismissDirection.endToStart,
          confirmDismiss: (_) async {
            _reportBrokenChannel(context);
            return false; // don't remove the tile
          },
          background: Container(
            alignment: Alignment.centerRight,
            padding: const EdgeInsets.only(right: 20),
            color: Colors.red.shade700,
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Report Broken', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                SizedBox(width: 8),
                Icon(Icons.report_problem, color: Colors.white),
              ],
            ),
          ),
          child: ListTile(
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
          ),
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
          value: 'misclassified',
          child: Row(
            children: [
              Icon(Icons.label_off, color: Colors.orange, size: 20),
              SizedBox(width: 8),
              Text('Wrong Info 🏷️'),
            ],
          ),
        ),
      ],
    ).then((value) {
      if (value == 'misclassified') {
        _reportMisclassified(context);
      }
    });
  }

  /// Report this channel as broken to the shared database.
  void _reportBrokenChannel(BuildContext context) {
    final urlHash = SharedDbService.hashUrl(channel.url);
    SharedDbService.reportBrokenChannel(urlHash);

    // Mark channel as not working locally via provider
    try {
      final provider = Provider.of<ChannelProvider>(context, listen: false);
      provider.markChannelFailed(channel);
    } catch (_) {
      // Provider not available in this context — skip local update
    }

    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: const Text('Channel reported as broken. Thanks! 🙏'),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          duration: const Duration(seconds: 3),
        ),
      );
  }

  /// Show a dialog to report misclassified channel info (wrong country, category, etc.)
  void _reportMisclassified(BuildContext context) {
    String selectedField = 'Country';
    final correctionController = TextEditingController();
    final fields = ['Country', 'Category', 'Name', 'Language', 'Other'];

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setDialogState) {
            final currentValue = selectedField == 'Country'
                ? (channel.country ?? 'Unknown')
                : selectedField == 'Category'
                    ? (channel.category ?? 'Unknown')
                    : selectedField == 'Name'
                        ? channel.name
                        : selectedField == 'Language'
                            ? (channel.language ?? 'Unknown')
                            : '';

            return AlertDialog(
              title: const Text('Report Wrong Info'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      channel.name,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 16),
                    const Text('What\'s wrong?', style: TextStyle(fontWeight: FontWeight.w500)),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: fields.map((f) => ChoiceChip(
                        label: Text(f),
                        selected: selectedField == f,
                        onSelected: (_) => setDialogState(() => selectedField = f),
                      )).toList(),
                    ),
                    if (currentValue.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(
                        'Current: $currentValue',
                        style: TextStyle(color: Colors.grey.shade400, fontSize: 13),
                      ),
                    ],
                    const SizedBox(height: 12),
                    TextField(
                      controller: correctionController,
                      decoration: InputDecoration(
                        labelText: 'Correct value (optional)',
                        hintText: selectedField == 'Country'
                            ? 'e.g. United States'
                            : selectedField == 'Category'
                                ? 'e.g. Sports'
                                : 'Leave blank for "doesn\'t belong"',
                        border: const OutlineInputBorder(),
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancel'),
                ),
                FilledButton.icon(
                  onPressed: () {
                    Navigator.pop(ctx);
                    _submitMisclassificationReport(
                      context,
                      selectedField,
                      correctionController.text.trim(),
                    );
                  },
                  icon: const Icon(Icons.send, size: 18),
                  label: const Text('Submit'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  /// Submit the misclassification report as a GitHub issue.
  void _submitMisclassificationReport(
    BuildContext context,
    String field,
    String correction,
  ) {
    final currentValue = field == 'Country'
        ? (channel.country ?? 'Unknown')
        : field == 'Category'
            ? (channel.category ?? 'Unknown')
            : field == 'Name'
                ? channel.name
                : field == 'Language'
                    ? (channel.language ?? 'Unknown')
                    : 'N/A';

    final correctionText = correction.isEmpty
        ? "doesn't belong to this $field"
        : correction;

    final title = Uri.encodeComponent(
      '[Channel] ${channel.name} — wrong $field',
    );
    final body = Uri.encodeComponent(
      '### Issue type\n\nChannel name or category is wrong\n\n'
      '### Channel name\n\n${channel.name}\n\n'
      '### Country / Region\n\n${channel.country ?? "Unknown"}\n\n'
      '### Additional details\n\n'
      '**Field:** $field\n'
      '**Current value:** $currentValue\n'
      '**Suggested correction:** $correctionText\n\n'
      '_Reported from TV Viewer app_',
    );

    final url = Uri.parse(
      'https://github.com/tv-viewer-app/tv_viewer/issues/new'
      '?title=$title&body=$body&labels=channel-issue,community',
    );

    launchUrl(url, mode: LaunchMode.externalApplication).then((_) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: const Text('Opening GitHub to submit report... 📝'),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
            duration: const Duration(seconds: 3),
          ),
        );
    }).catchError((_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(
            SnackBar(
              content: const Text('Could not open browser. Report at github.com/tv-viewer-app/tv_viewer'),
              behavior: SnackBarBehavior.floating,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
              duration: const Duration(seconds: 5),
            ),
          );
      }
    });
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
