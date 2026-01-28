import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/channel_provider.dart';
import '../models/channel.dart';
import 'player_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Load channels on startup
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ChannelProvider>().loadChannels();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('📺 TV Viewer'),
        actions: [
          Consumer<ChannelProvider>(
            builder: (context, provider, _) {
              if (provider.isScanning) {
                return IconButton(
                  icon: const Icon(Icons.stop),
                  tooltip: 'Stop Scan',
                  onPressed: () => provider.stopValidation(),
                );
              }
              return IconButton(
                icon: const Icon(Icons.refresh),
                tooltip: 'Scan Channels',
                onPressed: () => provider.validateChannels(),
              );
            },
          ),
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'about') {
                _showAboutDialog();
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'about',
                child: Text('About'),
              ),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          // Scan Progress
          Consumer<ChannelProvider>(
            builder: (context, provider, _) {
              if (provider.isScanning) {
                return _buildScanProgress(provider);
              }
              return const SizedBox.shrink();
            },
          ),

          // Search Bar
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search channels...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          context.read<ChannelProvider>().setSearchQuery('');
                        },
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
              ),
              onChanged: (value) {
                context.read<ChannelProvider>().setSearchQuery(value);
              },
            ),
          ),

          // Filter Row with Dropdowns
          Consumer<ChannelProvider>(
            builder: (context, provider, _) {
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
                child: Row(
                  children: [
                    // Media Type Filter (TV/Radio)
                    Expanded(
                      child: _buildDropdown(
                        value: provider.selectedMediaType,
                        items: provider.mediaTypes,
                        hint: 'Type',
                        icon: Icons.live_tv,
                        onChanged: (value) => provider.setMediaType(value!),
                      ),
                    ),
                    const SizedBox(width: 8),
                    // Category Dropdown
                    Expanded(
                      flex: 2,
                      child: _buildDropdown(
                        value: provider.selectedCategory,
                        items: provider.categories,
                        hint: 'Category',
                        icon: Icons.category,
                        onChanged: (value) => provider.setCategory(value!),
                      ),
                    ),
                    const SizedBox(width: 8),
                    // Country Dropdown
                    Expanded(
                      flex: 2,
                      child: _buildDropdown(
                        value: provider.selectedCountry,
                        items: provider.countries,
                        hint: 'Country',
                        icon: Icons.flag,
                        onChanged: (value) => provider.setCountry(value!),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),

          // Stats Bar
          Consumer<ChannelProvider>(
            builder: (context, provider, _) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '${provider.channels.length} channels',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    Text(
                      '${provider.workingCount} working',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.green,
                          ),
                    ),
                  ],
                ),
              );
            },
          ),

          // Channel List
          Expanded(
            child: Consumer<ChannelProvider>(
              builder: (context, provider, _) {
                if (provider.isLoading) {
                  return const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 16),
                        Text('Loading channels...'),
                      ],
                    ),
                  );
                }

                if (provider.channels.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.tv_off, size: 64, color: Colors.grey),
                        const SizedBox(height: 16),
                        const Text('No channels found'),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          onPressed: () => provider.fetchChannels(),
                          icon: const Icon(Icons.refresh),
                          label: const Text('Refresh'),
                        ),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  itemCount: provider.channels.length,
                  itemBuilder: (context, index) {
                    final channel = provider.channels[index];
                    return _buildChannelTile(channel);
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildDropdown({
    required String value,
    required List<String> items,
    required String hint,
    required IconData icon,
    required void Function(String?) onChanged,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Theme.of(context).dividerColor),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          isExpanded: true,
          icon: Icon(icon, size: 18),
          hint: Text(hint),
          items: items.map((item) {
            return DropdownMenuItem<String>(
              value: item,
              child: Text(
                item,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 13),
              ),
            );
          }).toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }

  Widget _buildScanProgress(ChannelProvider provider) {
    final progress = provider.scanTotal > 0
        ? provider.scanProgress / provider.scanTotal
        : 0.0;

    return Container(
      padding: const EdgeInsets.all(12),
      color: Theme.of(context).colorScheme.surfaceVariant,
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Scanning: ${provider.scanProgress}/${provider.scanTotal}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              Text(
                '✓ ${provider.workingCount}  ✗ ${provider.failedCount}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(value: progress),
        ],
      ),
    );
  }

  Widget _buildChannelTile(Channel channel) {
    // Build subtitle with resolution/bitrate info
    String subtitle = channel.category ?? 'Other';
    if (channel.resolution != null) {
      subtitle += ' • ${channel.resolution}';
    }
    if (channel.formattedBitrate != null) {
      subtitle += ' • ${channel.formattedBitrate}';
    }
    if (channel.country != null && channel.country != 'Unknown') {
      subtitle += ' • ${channel.country}';
    }
    
    return ListTile(
      leading: CircleAvatar(
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
      ),
      title: Text(
        channel.name,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Text(
        subtitle,
        style: Theme.of(context).textTheme.bodySmall,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (channel.mediaType == 'Radio')
            const Icon(Icons.radio, size: 16, color: Colors.blue),
          const SizedBox(width: 4),
          Icon(
            channel.isWorking ? Icons.check_circle : Icons.error,
            color: channel.isWorking ? Colors.green : Colors.red,
            size: 20,
          ),
        ],
      ),
      onTap: () => _playChannel(channel),
    );
  }

  void _playChannel(Channel channel) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => PlayerScreen(channel: channel),
      ),
    );
  }

  void _showAboutDialog() {
    showAboutDialog(
      context: context,
      applicationName: 'TV Viewer',
      applicationVersion: '1.4.4',
      applicationIcon: const Icon(Icons.tv, size: 48),
      children: [
        const Text(
          'A free IPTV streaming app that discovers and validates '
          'publicly available TV streams from open repositories.',
        ),
        const SizedBox(height: 16),
        const Text(
          'Built with Flutter for Android.',
          style: TextStyle(fontStyle: FontStyle.italic),
        ),
      ],
    );
  }
}
