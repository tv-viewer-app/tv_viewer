import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:video_player/video_player.dart';
import '../models/channel.dart';
import '../providers/channel_provider.dart';
import '../services/watch_history_service.dart';
import '../services/analytics_service.dart';
import '../utils/logger_service.dart';

/// Dedicated radio player screen with genre browsing and audio-focused UI.
class RadioScreen extends StatefulWidget {
  const RadioScreen({super.key});

  @override
  State<RadioScreen> createState() => _RadioScreenState();
}

class _RadioScreenState extends State<RadioScreen> {
  VideoPlayerController? _controller;
  Channel? _currentStation;
  bool _isPlaying = false;
  bool _isLoading = false;
  String? _error;
  double _volume = 1.0;
  String _selectedGenre = 'All';
  String _searchQuery = '';
  final TextEditingController _searchController = TextEditingController();

  List<Channel> get _radioChannels {
    final provider = context.read<ChannelProvider>();
    return provider.channels
        .where((c) => c.mediaType.toLowerCase() == 'radio')
        .toList();
  }

  List<Channel> get _filteredStations {
    var stations = _radioChannels;
    if (_selectedGenre != 'All') {
      stations = stations
          .where((c) =>
              (c.category ?? '').toLowerCase() == _selectedGenre.toLowerCase())
          .toList();
    }
    if (_searchQuery.isNotEmpty) {
      final q = _searchQuery.toLowerCase();
      stations = stations
          .where((c) =>
              c.name.toLowerCase().contains(q) ||
              (c.country ?? '').toLowerCase().contains(q) ||
              (c.language ?? '').toLowerCase().contains(q))
          .toList();
    }
    return stations;
  }

  List<String> get _genres {
    final cats = _radioChannels
        .map((c) => c.category ?? 'Other')
        .where((c) => c.isNotEmpty)
        .toSet()
        .toList()
      ..sort();
    return ['All', ...cats];
  }

  @override
  void dispose() {
    _controller?.dispose();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _playStation(Channel station) async {
    // Dispose previous
    _controller?.dispose();
    _controller = null;

    setState(() {
      _currentStation = station;
      _isLoading = true;
      _isPlaying = false;
      _error = null;
    });

    try {
      final url = station.url;
      if (url.isEmpty) {
        setState(() {
          _isLoading = false;
          _error = 'No stream URL';
        });
        return;
      }

      _controller = VideoPlayerController.networkUrl(Uri.parse(url));
      await _controller!.initialize();
      _controller!.setVolume(_volume);
      await _controller!.play();

      _controller!.addListener(() {
        if (!mounted) return;
        final playing = _controller?.value.isPlaying ?? false;
        if (playing != _isPlaying) {
          setState(() => _isPlaying = playing);
        }
        if (_controller?.value.hasError == true && _error == null) {
          setState(() {
            _error = 'Playback error';
            _isLoading = false;
            _isPlaying = false;
          });
        }
      });

      setState(() => _isLoading = false);

      // Record play history
      WatchHistoryService.recordPlay({
        'name': station.name,
        'url': url,
        'category': station.category ?? 'Radio',
        'country': station.country ?? '',
        'mediaType': 'Radio',
      });
      AnalyticsService.instance.trackFeature('radio_play');
    } catch (e) {
      logger.warning('Radio playback error', e);
      setState(() {
        _isLoading = false;
        _error = 'Failed to play station';
      });
    }
  }

  void _togglePlayPause() {
    if (_controller == null) return;
    if (_controller!.value.isPlaying) {
      _controller!.pause();
    } else {
      _controller!.play();
    }
  }

  void _stop() {
    _controller?.pause();
    _controller?.dispose();
    _controller = null;
    setState(() {
      _isPlaying = false;
      _isLoading = false;
      _error = null;
      _currentStation = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final stations = _filteredStations;

    return Scaffold(
      appBar: AppBar(
        title: const Text('📻 Radio'),
        actions: [
          if (_genres.length > 2)
            PopupMenuButton<String>(
              icon: const Icon(Icons.filter_list),
              tooltip: 'Filter by genre',
              onSelected: (genre) => setState(() => _selectedGenre = genre),
              itemBuilder: (_) => _genres
                  .map((g) => PopupMenuItem(
                        value: g,
                        child: Row(
                          children: [
                            if (g == _selectedGenre)
                              Icon(Icons.check,
                                  size: 18, color: theme.colorScheme.primary),
                            if (g == _selectedGenre)
                              const SizedBox(width: 8),
                            Text(g),
                          ],
                        ),
                      ))
                  .toList(),
            ),
        ],
      ),
      body: Column(
        children: [
          // Now Playing bar
          if (_currentStation != null) _buildNowPlaying(theme),

          // Search bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search radio stations...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          setState(() => _searchQuery = '');
                        },
                      )
                    : null,
                isDense: true,
              ),
              onChanged: (v) => setState(() => _searchQuery = v),
            ),
          ),

          // Genre chips
          if (_genres.length > 2)
            SizedBox(
              height: 40,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                itemCount: _genres.length,
                separatorBuilder: (_, __) => const SizedBox(width: 6),
                itemBuilder: (_, i) {
                  final genre = _genres[i];
                  final selected = genre == _selectedGenre;
                  return FilterChip(
                    label: Text(genre, style: const TextStyle(fontSize: 12)),
                    selected: selected,
                    onSelected: (_) =>
                        setState(() => _selectedGenre = genre),
                    visualDensity: VisualDensity.compact,
                  );
                },
              ),
            ),

          const SizedBox(height: 4),

          // Station list
          Expanded(
            child: stations.isEmpty
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.radio, size: 64,
                            color: theme.colorScheme.onSurface.withOpacity(0.3)),
                        const SizedBox(height: 12),
                        Text(
                          _radioChannels.isEmpty
                              ? 'No radio stations found.\nScan channels to discover stations.'
                              : 'No stations match your filter.',
                          textAlign: TextAlign.center,
                          style: theme.textTheme.bodyLarge?.copyWith(
                            color: theme.colorScheme.onSurface.withOpacity(0.5),
                          ),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    itemCount: stations.length,
                    itemBuilder: (_, i) =>
                        _buildStationTile(stations[i], theme),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildNowPlaying(ThemeData theme) {
    return Container(
      color: theme.colorScheme.primaryContainer.withOpacity(0.3),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: [
          // Station logo/icon
          CircleAvatar(
            radius: 22,
            backgroundColor: theme.colorScheme.primary.withOpacity(0.2),
            child: _currentStation?.logo != null &&
                    _currentStation!.logo!.isNotEmpty
                ? ClipOval(
                    child: Image.network(
                      _currentStation!.logo!,
                      width: 44,
                      height: 44,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) =>
                          const Icon(Icons.radio, size: 24),
                    ),
                  )
                : const Icon(Icons.radio, size: 24),
          ),
          const SizedBox(width: 12),

          // Station info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _currentStation!.name,
                  style: theme.textTheme.titleSmall
                      ?.copyWith(fontWeight: FontWeight.bold),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  [
                    if (_currentStation!.country != null)
                      _currentStation!.country!,
                    if (_currentStation!.category != null)
                      _currentStation!.category!,
                  ].join(' · '),
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.6),
                  ),
                  maxLines: 1,
                ),
              ],
            ),
          ),

          // Loading indicator
          if (_isLoading)
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),

          // Error indicator
          if (_error != null)
            Tooltip(
              message: _error!,
              child: Icon(Icons.error_outline,
                  color: theme.colorScheme.error, size: 24),
            ),

          // Volume slider (compact)
          SizedBox(
            width: 80,
            child: Slider(
              value: _volume,
              onChanged: (v) {
                setState(() => _volume = v);
                _controller?.setVolume(v);
              },
              min: 0,
              max: 1,
            ),
          ),

          // Play/Pause
          IconButton(
            icon: Icon(
              _isPlaying ? Icons.pause_circle_filled : Icons.play_circle_filled,
              size: 36,
            ),
            onPressed: _togglePlayPause,
          ),

          // Stop
          IconButton(
            icon: const Icon(Icons.stop_circle_outlined, size: 28),
            onPressed: _stop,
          ),
        ],
      ),
    );
  }

  Widget _buildStationTile(Channel station, ThemeData theme) {
    final isActive = _currentStation?.name == station.name;
    return ListTile(
      leading: CircleAvatar(
        backgroundColor: isActive
            ? theme.colorScheme.primary.withOpacity(0.3)
            : theme.colorScheme.surfaceContainerHighest,
        child: station.logo != null && station.logo!.isNotEmpty
            ? ClipOval(
                child: Image.network(
                  station.logo!,
                  width: 40,
                  height: 40,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) =>
                      const Icon(Icons.radio, size: 20),
                ),
              )
            : const Icon(Icons.radio, size: 20),
      ),
      title: Text(
        station.name,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: isActive
            ? TextStyle(
                fontWeight: FontWeight.bold, color: theme.colorScheme.primary)
            : null,
      ),
      subtitle: Text(
        [
          if (station.country != null && station.country!.isNotEmpty)
            station.country!,
          if (station.language != null && station.language!.isNotEmpty)
            station.language!,
          if (station.category != null && station.category!.isNotEmpty)
            station.category!,
        ].join(' · '),
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: theme.textTheme.bodySmall,
      ),
      trailing: isActive && _isPlaying
          ? Icon(Icons.equalizer, color: theme.colorScheme.primary)
          : station.isWorking
              ? const Icon(Icons.play_arrow, size: 20)
              : Icon(Icons.error_outline,
                  size: 16, color: theme.colorScheme.error),
      selected: isActive,
      onTap: () => _playStation(station),
    );
  }
}
