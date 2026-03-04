import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:video_player/video_player.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import 'package:floating/floating.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:io' show Platform;
import '../models/channel.dart';
import '../services/pip_service.dart';
import '../services/analytics_service.dart';
import '../widgets/live_badge.dart';
import '../widgets/quality_badge.dart';
import '../utils/error_handler.dart';
import '../utils/logger_service.dart';

class PlayerScreen extends StatefulWidget {
  final Channel channel;
  final List<Channel>? channelList;
  final int? channelIndex;

  const PlayerScreen({
    super.key,
    required this.channel,
    this.channelList,
    this.channelIndex,
  });

  @override
  State<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends State<PlayerScreen> with WidgetsBindingObserver {
  VideoPlayerController? _videoController;
  bool _isLoading = true;
  bool _isPlaying = false;
  bool _showControls = true;
  AppError? _error; // Changed to AppError for better error handling
  String? _resolution;
  String? _bitrate;
  double _volume = 1.0; // BL-018: Volume control
  
  // Named listener for proper cleanup
  VoidCallback? _playerListener;
  
  // PiP service
  final PipService _pipService = PipService();
  bool _isPipMode = false;
  bool _isPipSupported = false;

  // Channel navigation
  bool get _hasChannelList =>
      widget.channelList != null && widget.channelList!.length > 1;
  bool get _hasPrevious =>
      _hasChannelList && widget.channelIndex != null && widget.channelIndex! > 0;
  bool get _hasNext =>
      _hasChannelList &&
      widget.channelIndex != null &&
      widget.channelIndex! < widget.channelList!.length - 1;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    
    _initializePlayer();
    _initializeWakeLock();
    _initializePip();
    
    // Allow auto-rotation (portrait + landscape) for video playback
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.portraitUp,
      DeviceOrientation.portraitDown,
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersive);
    
    // Auto-hide controls after 3 seconds
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted && _isPlaying) {
        setState(() => _showControls = false);
      }
    });
  }
  
  /// Initialize wake lock to prevent screen from sleeping during playback
  Future<void> _initializeWakeLock() async {
    try {
      await WakelockPlus.enable();
      logger.info('Wake lock enabled for ${widget.channel.name}');
    } catch (e) {
      logger.warning('Failed to enable wake lock', e);
    }
  }
  
  /// Initialize PiP service
  Future<void> _initializePip() async {
    try {
      await _pipService.initialize();
      setState(() {
        _isPipSupported = _pipService.isSupported;
      });
      logger.info('PiP initialized - Supported: $_isPipSupported');
      
      // Check current PiP status
      try {
        final status = await _pipService.pipStatusFuture;
        if (status != null && mounted) {
          setState(() {
            _isPipMode = status == PiPStatus.enabled;
          });
        }
      } catch (_) {
        // PiP status check failed, ignore
      }
    } catch (e, stackTrace) {
      logger.error('Failed to initialize PiP', e, stackTrace);
    }
  }
  
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    
    // Handle app lifecycle changes
    switch (state) {
      case AppLifecycleState.paused:
        // App is in background (possibly in PiP)
        if (!_isPipMode) {
          _videoController?.pause();
        }
        break;
      case AppLifecycleState.resumed:
        // App is back in foreground
        if (!_isPipMode) {
          _videoController?.play();
        }
        break;
      default:
        break;
    }
  }

  int _currentUrlIndex = 0;
  final Set<int> _failedIndices = {}; // Track indices that failed this session
  bool _isFallingBack = false; // Prevent re-entrant fallback from listener
  
  Future<void> _initializePlayer({int? startIndex}) async {
    // Dispose existing controller before creating new one (fixes memory leak on retry)
    _disposeController();
    
    final urls = widget.channel.urls;
    if (urls.isEmpty) {
      setState(() {
        _isLoading = false;
        _error = ErrorHandler.streamError('no_url', 'No stream URL available');
      });
      return;
    }
    
    // Use explicit startIndex (from fallback), or load preferred source
    if (startIndex != null) {
      _currentUrlIndex = startIndex.clamp(0, urls.length - 1);
    } else {
      final preferred = await loadPreferredSource(widget.channel);
      _currentUrlIndex = preferred.clamp(0, urls.length - 1);
      _failedIndices.clear(); // Fresh start — clear failed tracking
    }
    
    // Try each URL in order, starting from current index
    for (int attempt = 0; attempt < urls.length; attempt++) {
      final idx = (_currentUrlIndex + attempt) % urls.length;
      final streamUrl = urls[idx];
      
      logger.info('Trying URL $idx/${urls.length} for ${widget.channel.name}: $streamUrl');
      
      try {
        _disposeController();
        _videoController = VideoPlayerController.networkUrl(
          Uri.parse(streamUrl),
          httpHeaders: const {'User-Agent': 'TV Viewer/2.2.2'},
        );

        await _videoController!.initialize().timeout(
          const Duration(seconds: 15),
          onTimeout: () {
            throw ErrorHandler.streamError(
              'timeout',
              'Stream timeout after 15s for URL $idx',
            );
          },
        );
        
        _videoController!.play();
        _videoController!.setVolume(_volume);
        
        // Get video info
        final value = _videoController!.value;
        if (value.isInitialized) {
          _resolution = '${value.size.width.toInt()}x${value.size.height.toInt()}';
          logger.info('Stream initialized - URL $idx, Resolution: $_resolution');
        }

        _currentUrlIndex = idx;
        
        setState(() {
          _isLoading = false;
          _isPlaying = true;
          _error = null;
        });

        // Create named listener for proper cleanup
        _playerListener = () {
          if (mounted && _videoController != null) {
            final vc = _videoController!.value;
            setState(() {
              _isPlaying = vc.isPlaying;
            });
            // Detect playback failure mid-stream
            if (vc.hasError && !_isLoading && !_isFallingBack) {
              _onPlaybackError(idx, vc.errorDescription ?? 'unknown');
            }
          }
        };
        _videoController!.addListener(_playerListener!);
        
        // Report success
        _reportHealth(streamUrl, true);
        return; // Success — stop trying URLs
        
      } catch (e, stackTrace) {
        logger.warning('URL $idx failed for ${widget.channel.name}: $e');
        _failedIndices.add(idx);
        _reportHealth(streamUrl, false, e.toString());
        // Continue to next URL
      }
    }
    
    // All URLs failed — track failure telemetry
    AnalyticsService.instance.trackChannelFail(
      urls.first,
      'all_urls_failed',
      country: widget.channel.country ?? '',
      category: widget.channel.category ?? '',
    );
    final appError = ErrorHandler.streamError(
      'all_failed',
      'All ${urls.length} sources failed for ${widget.channel.name}',
    );
    logger.error('All URLs failed for ${widget.channel.name}');
    
    setState(() {
      _isLoading = false;
      _error = appError;
    });
  }
  
  void _onPlaybackError(int failedIndex, String error) {
    final urls = widget.channel.urls;
    _failedIndices.add(failedIndex);
    _reportHealth(urls[failedIndex], false, error);
    
    if (urls.length <= 1) return;
    
    // Find next untried source
    final nextIdx = (failedIndex + 1) % urls.length;
    if (_failedIndices.length >= urls.length) {
      // All sources have failed — show error with source selector
      logger.error('All sources exhausted for ${widget.channel.name}');
      setState(() {
        _isLoading = false;
        _error = ErrorHandler.streamError(
          'all_failed',
          'All ${urls.length} sources failed',
        );
      });
      return;
    }
    
    logger.info('Auto-fallback: source #${failedIndex + 1} → #${nextIdx + 1} for ${widget.channel.name}');
    _isFallingBack = true;
    _initializePlayer(startIndex: nextIdx).then((_) {
      _isFallingBack = false;
    });
  }
  
  void _reportHealth(String url, bool isWorking, [String? error]) {
    // Fire-and-forget analytics report
    try {
      // Use the analytics service if available
      logger.info('Health report: ${widget.channel.name} url=${url.substring(0, url.length.clamp(0, 40))} working=$isWorking');
    } catch (_) {}
  }
  
  void _disposeController() {
    if (_videoController != null) {
      if (_playerListener != null) {
        _videoController!.removeListener(_playerListener!);
        _playerListener = null;
      }
      _videoController!.dispose();
      _videoController = null;
    }
  }

  void _togglePlayPause() {
    if (_videoController == null) return;

    if (_videoController!.value.isPlaying) {
      _videoController!.pause();
    } else {
      _videoController!.play();
    }
  }

  void _setVolume(double volume) {
    setState(() {
      _volume = volume;
    });
    _videoController?.setVolume(volume);
  }

  /// Switch to a specific source URL by index and save as preferred
  void _switchSource(int index) {
    if (index == _currentUrlIndex) return;
    if (index < 0 || index >= widget.channel.urls.length) return;
    
    logger.info('Switching to source #${index + 1} for ${widget.channel.name}');
    AnalyticsService.instance.trackFeature('switch_source');
    
    _currentUrlIndex = index;
    
    // Save preferred source via SharedPreferences
    _savePreferredSource(index);
    
    // Reinitialize player with the selected URL
    _disposeController();
    setState(() {
      _isLoading = true;
      _error = null;
    });
    _initializePlayerWithUrl(widget.channel.urls[index]);
  }

  /// Navigate to the previous channel in the list
  void _previousChannel() {
    if (!_hasPrevious) return;
    final newIndex = widget.channelIndex! - 1;
    final newChannel = widget.channelList![newIndex];
    _navigateToChannel(newChannel, newIndex);
  }

  /// Navigate to the next channel in the list
  void _nextChannel() {
    if (!_hasNext) return;
    final newIndex = widget.channelIndex! + 1;
    final newChannel = widget.channelList![newIndex];
    _navigateToChannel(newChannel, newIndex);
  }

  void _navigateToChannel(Channel channel, int index) {
    _disposeController();
    Navigator.pushReplacement(
      context,
      PageRouteBuilder(
        pageBuilder: (_, __, ___) => PlayerScreen(
          channel: channel,
          channelList: widget.channelList,
          channelIndex: index,
        ),
        transitionDuration: const Duration(milliseconds: 200),
        transitionsBuilder: (_, anim, __, child) =>
            FadeTransition(opacity: anim, child: child),
      ),
    );
  }

  /// Initialize player with a specific URL (used by source switcher)
  Future<void> _initializePlayerWithUrl(String streamUrl) async {
    try {
      final controller = VideoPlayerController.networkUrl(
        Uri.parse(streamUrl),
        httpHeaders: const {'User-Agent': 'TV Viewer/2.2.2'},
      );
      
      await controller.initialize();
      
      if (!mounted) {
        controller.dispose();
        return;
      }
      
      _videoController = controller;
      _playerListener = () {
        if (mounted) {
          setState(() {
            _isPlaying = controller.value.isPlaying;
          });
          if (controller.value.hasError) {
            final idx = widget.channel.urls.indexOf(streamUrl);
            _onPlaybackError(idx >= 0 ? idx : _currentUrlIndex, controller.value.errorDescription ?? 'Unknown');
          }
        }
      };
      controller.addListener(_playerListener!);
      controller.setVolume(_volume);
      controller.play();
      
      _reportHealth(streamUrl, true);
      
      setState(() {
        _isLoading = false;
        _isPlaying = true;
        _error = null;
      });
    } catch (e) {
      logger.error('Failed to play source: $streamUrl', e);
      setState(() {
        _isLoading = false;
        _error = ErrorHandler.streamError('source_fail', e.toString());
      });
    }
  }

  Future<void> _savePreferredSource(int index) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final key = 'preferred_source_${widget.channel.name.toLowerCase().hashCode}';
      await prefs.setInt(key, index);
    } catch (_) {}
  }

  static Future<int> loadPreferredSource(Channel channel) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final key = 'preferred_source_${channel.name.toLowerCase().hashCode}';
      return prefs.getInt(key) ?? channel.workingUrlIndex;
    } catch (_) {
      return channel.workingUrlIndex;
    }
  }
  
  void _toggleControls() {
    setState(() {
      _showControls = !_showControls;
    });
    
    if (_showControls) {
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted && _isPlaying) {
          setState(() => _showControls = false);
        }
      });
    }
  }

  void _openInExternalPlayer() async {
    final streamUrl = widget.channel.url;
    final channelName = widget.channel.name;
    logger.info('Opening $channelName in external player');

    if (Platform.isAndroid) {
      // Use Android intent with video/* MIME type to open in VLC/media player (not browser)
      try {
        const platform = MethodChannel('tv_viewer/intent');
        final result = await platform.invokeMethod('openInVideoPlayer', {
          'url': streamUrl,
          'title': channelName,
          'package': 'org.videolan.vlc', // Try VLC first
        });
        if (result == true) {
          logger.info('Opened in VLC');
          return;
        }
      } catch (e) {
        logger.debug('VLC intent failed: $e');
      }

      // Fallback: open with any video player via ACTION_VIEW + video/* MIME type
      try {
        const platform = MethodChannel('tv_viewer/intent');
        final result = await platform.invokeMethod('openInVideoPlayer', {
          'url': streamUrl,
          'title': channelName,
        });
        if (result == true) {
          logger.info('Opened in video player via chooser');
          return;
        }
      } catch (e) {
        logger.debug('Video intent failed: $e');
      }

      // Last resort: vlc:// custom scheme
      try {
        final vlcUri = Uri.parse('vlc://$streamUrl');
        if (await launchUrl(vlcUri, mode: LaunchMode.externalApplication)) {
          return;
        }
      } catch (_) {}
    } else {
      // Non-Android: use url_launcher
      try {
        await launchUrl(Uri.parse(streamUrl), mode: LaunchMode.externalApplication);
        return;
      } catch (_) {}
    }

    // All methods failed
    if (mounted) {
      Clipboard.setData(ClipboardData(text: streamUrl));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No video player found. URL copied to clipboard. Install VLC.'),
          duration: Duration(seconds: 4),
        ),
      );
    }
  }
  
  void _showCastDialog() {
    final streamUrl = widget.channel.url;
    final channelName = widget.channel.name;
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.grey[900],
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 40, height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[600],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 16),
            Text('Cast "$channelName"',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: Colors.white),
            ),
            const SizedBox(height: 20),
            // Open in VLC (which has built-in cast)
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () async {
                  Navigator.pop(context);
                  // Open in VLC — user can cast from VLC's Renderer menu
                  if (Platform.isAndroid) {
                    try {
                      const platform = MethodChannel('tv_viewer/intent');
                      await platform.invokeMethod('openInVideoPlayer', {
                        'url': streamUrl,
                        'title': channelName,
                        'package': 'org.videolan.vlc',
                      });
                      return;
                    } catch (_) {}
                    // Fallback to vlc:// scheme
                    try {
                      await launchUrl(Uri.parse('vlc://$streamUrl'), mode: LaunchMode.externalApplication);
                      return;
                    } catch (_) {}
                  }
                  if (mounted) {
                    ScaffoldMessenger.of(this.context).showSnackBar(
                      const SnackBar(content: Text('VLC not found. Install VLC for casting.')),
                    );
                  }
                },
                icon: const Icon(Icons.cast),
                label: const Text('Cast via VLC'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  backgroundColor: Colors.blue[700],
                ),
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'Opens stream in VLC → tap ≡ Menu → Renderer → select Chromecast',
              style: TextStyle(fontSize: 12, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            // Open in any video player
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () async {
                  Navigator.pop(context);
                  if (Platform.isAndroid) {
                    try {
                      const platform = MethodChannel('tv_viewer/intent');
                      await platform.invokeMethod('openInVideoPlayer', {
                        'url': streamUrl,
                        'title': channelName,
                      });
                      return;
                    } catch (_) {}
                  }
                  try {
                    await launchUrl(Uri.parse(streamUrl), mode: LaunchMode.externalNonBrowserApplication);
                  } catch (_) {
                    Clipboard.setData(ClipboardData(text: streamUrl));
                    if (mounted) {
                      ScaffoldMessenger.of(this.context).showSnackBar(
                        const SnackBar(content: Text('Stream URL copied — paste in your cast app')),
                      );
                    }
                  }
                },
                icon: const Icon(Icons.open_in_new),
                label: const Text('Open in Other Player'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            ),
            const SizedBox(height: 10),
            // Copy URL
            SizedBox(
              width: double.infinity,
              child: TextButton.icon(
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: streamUrl));
                  Navigator.pop(context);
                  ScaffoldMessenger.of(this.context).showSnackBar(
                    const SnackBar(content: Text('Stream URL copied to clipboard')),
                  );
                },
                icon: const Icon(Icons.copy, size: 18),
                label: const Text('Copy Stream URL'),
              ),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  /// Enable PiP mode
  Future<void> _enablePip() async {
    if (!_isPipSupported) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Picture-in-Picture not supported (requires Android 8.0+)'),
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }
    
    // Calculate aspect ratio from video
    Rational aspectRatio = const Rational(16, 9); // Default
    if (_videoController != null && _videoController!.value.isInitialized) {
      final videoSize = _videoController!.value.size;
      aspectRatio = _pipService.calculateAspectRatio(videoSize);
    }
    
    // Enter PiP mode
    final success = await _pipService.enablePip(aspectRatio: aspectRatio);
    
    if (success) {
      // Hide controls in PiP mode
      setState(() {
        _showControls = false;
      });
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to enter Picture-in-Picture mode'),
            duration: Duration(seconds: 2),
          ),
        );
      }
    }
  }
  
  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    
    // Disable wake lock
    WakelockPlus.disable();
    
    // Restore orientation
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.portraitUp,
      DeviceOrientation.portraitDown,
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
    
    _disposeController();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: GestureDetector(
        onTap: _toggleControls,
        onDoubleTap: _togglePlayPause,
        child: Stack(
          children: [
            // Video or error
            Center(child: _buildVideoWidget()),

            // Top bar with controls
            if (_showControls)
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
                    child: Row(
                      children: [
                        IconButton(
                          icon: const Icon(Icons.arrow_back, color: Colors.white),
                          onPressed: () => Navigator.pop(context),
                        ),
                        // Previous channel button
                        if (_hasChannelList)
                          IconButton(
                            icon: Icon(Icons.skip_previous,
                                color: _hasPrevious ? Colors.white : Colors.white24),
                            tooltip: 'Previous channel',
                            onPressed: _hasPrevious ? _previousChannel : null,
                          ),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Row(
                                children: [
                                  // LIVE badge (BL-027)
                                  const LiveBadge(),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      widget.channel.name,
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                      ),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ],
                              ),
                              // Show quality badge and bitrate
                              Row(
                                children: [
                                  if (_resolution != null || widget.channel.resolution != null) ...[
                                    QualityBadge(
                                      resolution: _resolution ?? widget.channel.resolution,
                                    ),
                                    const SizedBox(width: 8),
                                  ],
                                  if (widget.channel.formattedBitrate != null)
                                    Text(
                                      widget.channel.formattedBitrate!,
                                      style: const TextStyle(
                                        color: Colors.white70,
                                        fontSize: 12,
                                      ),
                                    ),
                                ],
                              ),
                            ],
                          ),
                        ),
                        // Next channel button
                        if (_hasChannelList)
                          IconButton(
                            icon: Icon(Icons.skip_next,
                                color: _hasNext ? Colors.white : Colors.white24),
                            tooltip: 'Next channel',
                            onPressed: _hasNext ? _nextChannel : null,
                          ),
                        // PiP button (only show if supported and not in PiP mode)
                        if (_isPipSupported && !_isPipMode)
                          IconButton(
                            icon: const Icon(Icons.picture_in_picture_alt, color: Colors.white),
                            tooltip: 'Picture in Picture',
                            onPressed: _enablePip,
                          ),
                        // Cast button
                        IconButton(
                          icon: const Icon(Icons.cast, color: Colors.white),
                          tooltip: 'Cast',
                          onPressed: _showCastDialog,
                        ),
                        // External player button
                        IconButton(
                          icon: const Icon(Icons.open_in_new, color: Colors.white),
                          tooltip: 'Open in External App',
                          onPressed: _openInExternalPlayer,
                        ),
                      ],
                    ),
                  ),
                ),
              ),

            // Play/Pause indicator
            if (!_isLoading && _error == null && _showControls)
              Center(
                child: AnimatedOpacity(
                  opacity: _isPlaying ? 0.0 : 1.0,
                  duration: const Duration(milliseconds: 300),
                  child: Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.black54,
                      borderRadius: BorderRadius.circular(50),
                    ),
                    child: Icon(
                      _isPlaying ? Icons.pause : Icons.play_arrow,
                      color: Colors.white,
                      size: 50,
                    ),
                  ),
                ),
              ),
               
            // Bottom control bar with volume slider (BL-018)
            if (_showControls && !_isLoading && _error == null)
              Positioned(
                bottom: 0,
                left: 0,
                right: 0,
                child: Container(
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.bottomCenter,
                      end: Alignment.topCenter,
                      colors: [Colors.black87, Colors.transparent],
                    ),
                  ),
                  padding: const EdgeInsets.fromLTRB(16, 24, 16, 16),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Volume control
                      Row(
                        children: [
                          Icon(
                            _volume == 0
                                ? Icons.volume_off
                                : _volume < 0.5
                                    ? Icons.volume_down
                                    : Icons.volume_up,
                            color: Colors.white,
                            size: 20,
                          ),
                          Expanded(
                            child: Slider(
                              value: _volume,
                              min: 0.0,
                              max: 1.0,
                              onChanged: _setVolume,
                              activeColor: Colors.white,
                              inactiveColor: Colors.white30,
                            ),
                          ),
                          Text(
                            '${(_volume * 100).round()}%',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      // Source selector (when multiple URLs available)
                      if (widget.channel.urls.length > 1)
                        Row(
                          children: [
                            const Icon(Icons.stream, color: Colors.white70, size: 16),
                            const SizedBox(width: 8),
                            const Text('Source:', style: TextStyle(color: Colors.white70, fontSize: 12)),
                            const SizedBox(width: 8),
                            Expanded(
                              child: SizedBox(
                                height: 28,
                                child: ListView.builder(
                                  scrollDirection: Axis.horizontal,
                                  itemCount: widget.channel.urls.length,
                                  itemBuilder: (context, index) {
                                    final isActive = index == _currentUrlIndex;
                                    return Padding(
                                      padding: const EdgeInsets.only(right: 6),
                                      child: GestureDetector(
                                        onTap: () => _switchSource(index),
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                          decoration: BoxDecoration(
                                            color: isActive ? Colors.blue : Colors.white12,
                                            borderRadius: BorderRadius.circular(14),
                                            border: isActive ? null : Border.all(color: Colors.white24),
                                          ),
                                          child: Text(
                                            '#${index + 1}',
                                            style: TextStyle(
                                              color: isActive ? Colors.white : Colors.white60,
                                              fontSize: 12,
                                              fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
                                            ),
                                          ),
                                        ),
                                      ),
                                    );
                                  },
                                ),
                              ),
                            ),
                          ],
                        ),
                      if (widget.channel.urls.length > 1) const SizedBox(height: 8),
                      // Info text
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.info_outline, color: Colors.white54, size: 14),
                          const SizedBox(width: 4),
                          Text(
                            'Tap to hide controls • Double-tap to play/pause',
                            style: TextStyle(color: Colors.white54, fontSize: 12),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildVideoWidget() {
    if (_isLoading) {
      return const Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(color: Colors.white),
          SizedBox(height: 16),
          Text(
            'Loading stream...',
            style: TextStyle(color: Colors.white),
          ),
        ],
      );
    }

    if (_error != null) {
      return SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              Text(
                _error!.userMessage,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.black26,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.white24),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.info_outline, size: 16, color: Colors.white70),
                        const SizedBox(width: 8),
                        const Text(
                          'What to do:',
                          style: TextStyle(
                            color: Colors.white70,
                            fontWeight: FontWeight.bold,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _error!.recoverySuggestion,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 13,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Error Code: ${_error!.code}',
                style: const TextStyle(
                  color: Colors.white30,
                  fontSize: 11,
                  fontFamily: 'monospace',
                ),
              ),
              // Issue #61: Source selector on error screen
              if (widget.channel.urls.length > 1) ...[
                const SizedBox(height: 20),
                const Text(
                  'Try a different source:',
                  style: TextStyle(color: Colors.white70, fontSize: 13),
                ),
                const SizedBox(height: 8),
                SizedBox(
                  height: 36,
                  child: ListView.builder(
                    shrinkWrap: true,
                    scrollDirection: Axis.horizontal,
                    itemCount: widget.channel.urls.length,
                    itemBuilder: (context, index) {
                      final isCurrent = index == _currentUrlIndex;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: GestureDetector(
                          onTap: isCurrent ? null : () {
                            // Clear failed state and try this source
                            _failedIndices.clear();
                            _switchSource(index);
                          },
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                            decoration: BoxDecoration(
                              color: isCurrent
                                  ? Colors.red.withOpacity(0.3)
                                  : Colors.white12,
                              borderRadius: BorderRadius.circular(18),
                              border: Border.all(
                                color: isCurrent ? Colors.red.withOpacity(0.5) : Colors.white24,
                              ),
                            ),
                            child: Text(
                              'Source #${index + 1}${isCurrent ? ' (failed)' : ''}',
                              style: TextStyle(
                                color: isCurrent ? Colors.white38 : Colors.white,
                                fontSize: 13,
                                fontWeight: FontWeight.normal,
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ElevatedButton.icon(
                    onPressed: () {
                      setState(() {
                        _isLoading = true;
                        _error = null;
                      });
                      _initializePlayer();
                    },
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    ),
                  ),
                  const SizedBox(width: 12),
                  OutlinedButton.icon(
                    onPressed: _openInExternalPlayer,
                    icon: const Icon(Icons.open_in_new),
                    label: const Text('External Player'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white,
                      side: const BorderSide(color: Colors.white54),
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      );
    }

    if (_videoController != null && _videoController!.value.isInitialized) {
      return AspectRatio(
        aspectRatio: _videoController!.value.aspectRatio,
        child: VideoPlayer(_videoController!),
      );
    }

    return const Text(
      'Player not initialized',
      style: TextStyle(color: Colors.white),
    );
  }
}
