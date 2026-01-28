import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/channel.dart';
import '../providers/channel_provider.dart';
import 'quality_badge.dart';

/// Reusable channel list item widget (BL-015)
class ChannelTile extends StatelessWidget {
  final Channel channel;
  final VoidCallback onTap;

  const ChannelTile({
    super.key,
    required this.channel,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    // Build subtitle with category, quality, bitrate, and country
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
    
    final subtitle = subtitleParts.join(' • ');
    
    return ListTile(
      leading: _buildLeading(),
      title: Text(
        channel.name,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: subtitle.isNotEmpty
          ? Text(
              subtitle,
              style: Theme.of(context).textTheme.bodySmall,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            )
          : null,
      trailing: _buildTrailing(context),
      onTap: onTap,
    );
  }

  Widget _buildLeading() {
    return CircleAvatar(
      backgroundColor: channel.isWorking ? Colors.green : Colors.grey,
      child: channel.logo != null
          ? ClipOval(
              child: Image.network(
                channel.logo!,
                width: 40,
                height: 40,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Icon(
                  channel.mediaType == 'Radio' ? Icons.radio : Icons.tv,
                  color: Colors.white,
                ),
              ),
            )
          : Icon(
              channel.mediaType == 'Radio' ? Icons.radio : Icons.tv,
              color: Colors.white,
            ),
    );
  }

  Widget _buildTrailing(BuildContext context) {
    return Consumer<ChannelProvider>(
      builder: (context, provider, _) {
        final isFavorite = provider.isFavorite(channel);
        
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Favorite toggle button
            InkWell(
              onTap: () => provider.toggleFavorite(channel),
              child: Padding(
                padding: const EdgeInsets.all(4.0),
                child: Icon(
                  isFavorite ? Icons.favorite : Icons.favorite_border,
                  color: isFavorite ? Colors.red : Colors.grey,
                  size: 20,
                ),
              ),
            ),
            const SizedBox(width: 4),
            // Quality badge (replaces raw resolution)
            if (channel.resolution != null) ...[
              QualityBadge(resolution: channel.resolution, compact: true),
              const SizedBox(width: 4),
            ],
            // Media type indicator
            if (channel.mediaType == 'Radio')
              const Icon(Icons.radio, size: 16, color: Colors.blue),
            const SizedBox(width: 4),
            // Working status indicator
            Icon(
              channel.isWorking ? Icons.check_circle : Icons.error,
              color: channel.isWorking ? Colors.green : Colors.red,
              size: 20,
            ),
          ],
        );
      },
    );
  }
}
