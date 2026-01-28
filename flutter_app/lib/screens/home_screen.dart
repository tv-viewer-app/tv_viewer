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

          // Category Filter
          Consumer<ChannelProvider>(
            builder: (context, provider, _) {
              return SizedBox(
                height: 50,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  itemCount: provider.categories.length,
                  itemBuilder: (context, index) {
                    final category = provider.categories[index];
                    final isSelected = category == provider.selectedCategory;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: FilterChip(
                        label: Text(category),
                        selected: isSelected,
                        onSelected: (_) => provider.setCategory(category),
                      ),
                    );
                  },
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
                  errorBuilder: (_, __, ___) => const Icon(
                    Icons.tv,
                    color: Colors.white,
                  ),
                ),
              )
            : const Icon(Icons.tv, color: Colors.white),
      ),
      title: Text(
        channel.name,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Text(
        channel.category ?? 'Other',
        style: Theme.of(context).textTheme.bodySmall,
      ),
      trailing: Icon(
        channel.isWorking ? Icons.check_circle : Icons.error,
        color: channel.isWorking ? Colors.green : Colors.red,
        size: 20,
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
