import 'package:flutter/material.dart';
import 'models/channel.dart';
import 'models/epg_info.dart';
import 'widgets/epg_display.dart';

/// Example demonstrations of EPG feature usage
/// This file shows various ways to use the EPG display components

/// Example 1: Using EPG with placeholder data (most common for free IPTV)
class EpgPlaceholderExample extends StatelessWidget {
  const EpgPlaceholderExample({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('EPG Placeholder Example')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Full EPG Display (Placeholder)',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            EpgDisplay.placeholder(),
            
            const SizedBox(height: 32),
            
            const Text(
              'Compact EPG Display (Placeholder)',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            CompactEpgDisplay.placeholder(),
          ],
        ),
      ),
    );
  }
}

/// Example 2: Using EPG with actual program data (future enhancement)
class EpgWithDataExample extends StatelessWidget {
  const EpgWithDataExample({super.key});

  @override
  Widget build(BuildContext context) {
    // Create sample EPG data
    final now = DateTime.now();
    final channelEpg = ChannelEpg(
      channelId: 'cnn',
      channelName: 'CNN International',
      programs: [
        // Current program (started 30 min ago, ends in 30 min)
        EpgInfo(
          programTitle: 'CNN Newsroom',
          description: 'Breaking news and analysis from around the world',
          startTime: now.subtract(const Duration(minutes: 30)),
          endTime: now.add(const Duration(minutes: 30)),
          category: 'News',
        ),
        // Next program (starts in 30 min, ends in 1h 30min)
        EpgInfo(
          programTitle: 'Anderson Cooper 360',
          description: 'In-depth reporting and analysis with Anderson Cooper',
          startTime: now.add(const Duration(minutes: 30)),
          endTime: now.add(const Duration(minutes: 90)),
          category: 'News',
        ),
        // Future program
        EpgInfo(
          programTitle: 'CNN Tonight',
          description: 'Latest news and interviews',
          startTime: now.add(const Duration(hours: 2)),
          endTime: now.add(const Duration(hours: 3)),
          category: 'News',
        ),
      ],
    );

    return Scaffold(
      appBar: AppBar(title: const Text('EPG With Data Example')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Full EPG Display (With Data)',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            EpgDisplay.fromChannelEpg(channelEpg),
            
            const SizedBox(height: 32),
            
            const Text(
              'Compact EPG Display (With Data)',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            CompactEpgDisplay.fromChannelEpg(channelEpg),
          ],
        ),
      ),
    );
  }
}

/// Example 3: EPG in video overlay (like in player screen)
class EpgInOverlayExample extends StatefulWidget {
  const EpgInOverlayExample({super.key});

  @override
  State<EpgInOverlayExample> createState() => _EpgInOverlayExampleState();
}

class _EpgInOverlayExampleState extends State<EpgInOverlayExample> {
  bool _showFullEpg = false;

  void _toggleEpg() {
    setState(() {
      _showFullEpg = !_showFullEpg;
    });
    
    // Auto-hide after 10 seconds
    if (_showFullEpg) {
      Future.delayed(const Duration(seconds: 10), () {
        if (mounted && _showFullEpg) {
          setState(() => _showFullEpg = false);
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('EPG Overlay Example')),
      body: Stack(
        children: [
          // Simulated video background
          Container(
            color: Colors.black,
            child: const Center(
              child: Icon(
                Icons.play_circle_outline,
                size: 100,
                color: Colors.white54,
              ),
            ),
          ),
          
          // Top overlay with compact EPG and controls
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Container(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Colors.black54, Colors.transparent],
                ),
              ),
              child: SafeArea(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        IconButton(
                          icon: const Icon(Icons.arrow_back, color: Colors.white),
                          onPressed: () => Navigator.pop(context),
                        ),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'CNN International',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 4),
                              // Compact EPG display
                              CompactEpgDisplay.placeholder(),
                            ],
                          ),
                        ),
                        // Info button to toggle full EPG
                        IconButton(
                          icon: Icon(
                            Icons.info_outline,
                            color: _showFullEpg ? Colors.blueAccent : Colors.white,
                          ),
                          onPressed: _toggleEpg,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
          
          // Full EPG overlay (shown when info button pressed)
          if (_showFullEpg)
            Positioned(
              left: 16,
              right: 16,
              bottom: 100,
              child: SafeArea(
                child: EpgDisplay.placeholder(),
              ),
            ),
        ],
      ),
    );
  }
}

/// Example 4: Channel list with EPG info
class ChannelListWithEpgExample extends StatelessWidget {
  const ChannelListWithEpgExample({super.key});

  @override
  Widget build(BuildContext context) {
    // Sample channels with tvg-id
    final channels = [
      Channel(
        name: 'CNN International',
        url: 'http://example.com/cnn.m3u8',
        category: 'News',
        logo: 'http://example.com/cnn.png',
        country: 'US',
      ),
      Channel(
        name: 'BBC World News',
        url: 'http://example.com/bbc.m3u8',
        category: 'News',
        logo: 'http://example.com/bbc.png',
        country: 'UK',
      ),
      Channel(
        name: 'ESPN',
        url: 'http://example.com/espn.m3u8',
        category: 'Sports',
        logo: 'http://example.com/espn.png',
        country: 'US',
      ),
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Channels with EPG Info')),
      body: ListView.builder(
        itemCount: channels.length,
        itemBuilder: (context, index) {
          final channel = channels[index];
          return Card(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: InkWell(
              onTap: () {
                // Navigate to player with EPG
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const EpgInOverlayExample(),
                  ),
                );
              },
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        // Channel logo
                        if (channel.logo != null)
                          Container(
                            width: 50,
                            height: 50,
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(8),
                              color: Colors.grey.shade200,
                            ),
                            child: const Icon(Icons.tv),
                          ),
                        const SizedBox(width: 12),
                        // Channel info
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                channel.name,
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              if (channel.category != null)
                                Text(
                                  channel.category!,
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                              if (channel.country != null)
                                Text(
                                  'Country: ${channel.country}',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: Colors.grey.shade500,
                                    fontStyle: FontStyle.italic,
                                  ),
                                ),
                            ],
                          ),
                        ),
                        const Icon(Icons.play_circle_outline),
                      ],
                    ),
                    const SizedBox(height: 8),
                    // Compact EPG preview
                    CompactEpgDisplay.placeholder(),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

/// Main example app to demonstrate all EPG features
class EpgExamplesApp extends StatelessWidget {
  const EpgExamplesApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EPG Feature Examples',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const EpgExamplesHome(),
    );
  }
}

class EpgExamplesHome extends StatelessWidget {
  const EpgExamplesHome({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('EPG Feature Examples'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildExampleCard(
            context,
            title: '1. Placeholder EPG',
            description: 'Shows placeholder when EPG data not available',
            icon: Icons.live_tv,
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => const EpgPlaceholderExample(),
              ),
            ),
          ),
          _buildExampleCard(
            context,
            title: '2. EPG With Data',
            description: 'Shows actual program schedule',
            icon: Icons.schedule,
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => const EpgWithDataExample(),
              ),
            ),
          ),
          _buildExampleCard(
            context,
            title: '3. Video Overlay',
            description: 'EPG in video player overlay',
            icon: Icons.video_label,
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => const EpgInOverlayExample(),
              ),
            ),
          ),
          _buildExampleCard(
            context,
            title: '4. Channel List',
            description: 'Channels with EPG preview',
            icon: Icons.list,
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => const ChannelListWithEpgExample(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExampleCard(
    BuildContext context, {
    required String title,
    required String description,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(icon, size: 40, color: Theme.of(context).primaryColor),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      description,
                      style: TextStyle(
                        fontSize: 13,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}
