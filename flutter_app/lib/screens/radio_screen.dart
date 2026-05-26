import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:video_player/video_player.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import '../models/channel.dart';
import '../providers/channel_provider.dart';
import '../services/background_audio_service.dart';
import '../services/settings_service.dart';
import '../services/watch_history_service.dart';
import '../services/analytics_service.dart';
import '../utils/logger_service.dart';
import '../widgets/safe_channel_logo.dart';

/// Dedicated radio player screen with genre browsing and audio-focused UI.
class RadioScreen extends StatefulWidget {
  const RadioScreen({super.key});

  @override
  State<RadioScreen> createState() => _RadioScreenState();
}

class _RadioScreenState extends State<RadioScreen> with WidgetsBindingObserver {
  VideoPlayerController? _controller;
  Channel? _currentStation;
  bool _isPlaying = false;
  bool _isLoading = false;
  String? _error;
  double _volume = 1.0;
  String _selectedGenre = 'All';
  String _searchQuery = '';
  bool _backgroundPlayback = false;
  bool _showFavoritesOnly = false;
  final TextEditingController _searchController = TextEditingController();

  List<Channel> get _radioChannels {
    final provider = context.read<ChannelProvider>();
    return provider.allChannels
        .where((c) => c.mediaType.toLowerCase() == 'radio')
        .toList();
  }

  List<Channel> get _filteredStations {
    var stations = _radioChannels;
    if (_showFavoritesOnly) {
      final provider = context.read<ChannelProvider>();
      stations = stations.where((c) => provider.isFavorite(c)).toList();
    }
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
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _loadBackgroundPlaybackSetting();
  }

  Future<void> _loadBackgroundPlaybackSetting() async {
    _backgroundPlayback = await SettingsService.instance.getBackgroundPlayback();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    if (_controller == null || !_isPlaying) return;

    switch (state) {
      case AppLifecycleState.paused:
        // Keep audio playing if background playback is enabled
        if (!_backgroundPlayback) {
          _controller?.pause();
        } else {
          // Switch to just_audio for reliable background playback
          final url = _currentStation?.url;
          if (url != null && url.isNotEmpty) {
            BackgroundAudioHandler.instance?.activateBackgroundAudio(url);
          }
        }
        break;
      case AppLifecycleState.resumed:
        if (BackgroundAudioHandler.instance?.isBackgroundActive == true) {
          BackgroundAudioHandler.instance?.deactivateBackgroundAudio();
        } else if (!_backgroundPlayback) {
          _controller?.play();
        }
        break;
      default:
        break;
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    BackgroundAudioHandler.instance?.detachController();
    _controller?.dispose();
    _searchController.dispose();
    // Release wake lock when leaving radio screen
    WakelockPlus.disable();
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
      // #196: widget can be disposed during async initialize; bail out
      // before touching state on a defunct State object.
      if (!mounted) {
        _controller?.dispose();
        _controller = null;
        return;
      }
      _controller!.setVolume(_volume);
      await _controller!.play();
      if (!mounted) {
        _controller?.dispose();
        _controller = null;
        return;
      }

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

      // Keep screen/CPU awake for audio playback when background playback enabled
      if (_backgroundPlayback) {
        WakelockPlus.enable();
        // Attach to audio service for notification + background persistence
        BackgroundAudioHandler.instance?.attachController(
          _controller!,
          channelName: station.name,
          category: station.category ?? 'Radio',
          streamUrl: url,
        );
      }

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
      if (!mounted) return;
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
    BackgroundAudioHandler.instance?.detachController();
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
          // Favorites toggle
          Consumer<ChannelProvider>(
            builder: (context, provider, _) {
              final favCount = _radioChannels.where((c) => provider.isFavorite(c)).length;
              return IconButton(
                icon: Icon(
                  _showFavoritesOnly ? Icons.favorite : Icons.favorite_border,
                  color: _showFavoritesOnly ? Colors.red : null,
                ),
                tooltip: _showFavoritesOnly
                    ? 'Show all stations'
                    : 'Show favorites ($favCount)',
                onPressed: () => setState(() => _showFavoritesOnly = !_showFavoritesOnly),
              );
            },
          ),
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

          // Genre chips + Favorites chip
          SizedBox(
            height: 40,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _genres.length + 1,
              separatorBuilder: (_, __) => const SizedBox(width: 6),
              itemBuilder: (_, i) {
                // First chip is Favorites toggle
                if (i == 0) {
                  return FilterChip(
                    avatar: Icon(
                      _showFavoritesOnly ? Icons.favorite : Icons.favorite_border,
                      size: 16,
                      color: _showFavoritesOnly ? Colors.red : null,
                    ),
                    label: const Text('Favorites', style: TextStyle(fontSize: 12)),
                    selected: _showFavoritesOnly,
                    onSelected: (_) =>
                        setState(() => _showFavoritesOnly = !_showFavoritesOnly),
                    visualDensity: VisualDensity.compact,
                  );
                }
                final genre = _genres[i - 1];
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
                        Icon(
                            _showFavoritesOnly ? Icons.favorite_border : Icons.radio,
                            size: 64,
                            color: theme.colorScheme.onSurface.withOpacity(0.3)),
                        const SizedBox(height: 12),
                        Text(
                          _showFavoritesOnly
                              ? 'No favorite radio stations yet.\nTap the ♥ on a station to add it.'
                              : _radioChannels.isEmpty
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
            child: ClipOval(
              child: SafeChannelLogo(
                url: _currentStation?.logo,
                size: 44,
                fallbackIcon: Icons.radio,
              ),
            ),
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
    final provider = context.read<ChannelProvider>();
    final isFav = provider.isFavorite(station);
    return ListTile(
      leading: CircleAvatar(
        backgroundColor: isActive
            ? theme.colorScheme.primary.withOpacity(0.3)
            : theme.colorScheme.surfaceContainerHighest,
        child: ClipOval(
          child: SafeChannelLogo(
            url: station.logo,
            size: 40,
            fallbackIcon: Icons.radio,
          ),
        ),
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
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(
            icon: Icon(
              isFav ? Icons.favorite : Icons.favorite_border,
              color: isFav ? Colors.red : theme.colorScheme.onSurface.withOpacity(0.4),
              size: 20,
            ),
            tooltip: isFav ? 'Remove from favorites' : 'Add to favorites',
            onPressed: () {
              provider.toggleFavorite(station);
              setState(() {});
            },
            visualDensity: VisualDensity.compact,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
          ),
          if (isActive && _isPlaying)
            Icon(Icons.equalizer, color: theme.colorScheme.primary)
          else if (station.isWorking)
            const Icon(Icons.play_arrow, size: 20)
          else
            Icon(Icons.error_outline,
                size: 16, color: theme.colorScheme.error),
        ],
      ),
      selected: isActive,
      onTap: () => _playStation(station),
    );
  }
}
