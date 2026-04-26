import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:video_player/video_player.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import 'package:floating/floating.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'dart:io' show Platform;
import '../models/channel.dart';
import '../services/pip_service.dart';
import '../services/analytics_service.dart';
import '../services/shared_db_service.dart';
import '../services/parental_controls_service.dart';
import '../services/watch_history_service.dart';
import '../widgets/live_badge.dart';
import '../widgets/pin_dialog.dart';
import '../widgets/quality_badge.dart';
import '../utils/error_handler.dart';
import '../utils/logger_service.dart';
import '../constants.dart';

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
  bool _reportSent = false; // Debounce: one report per player session

  /// Guard wrapper: only call setState when the widget is still mounted.
  /// Prevents "setState() called after dispose()" crashes (fixes #82).
  void _safeSetState(VoidCallback fn) {
    if (mounted) setState(fn);
  }

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
        _safeSetState(() => _showControls = false);
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
      _safeSetState(() {
        _isPipSupported = _pipService.isSupported;
      });
      logger.info('PiP initialized - Supported: $_isPipSupported');
      
      // Check current PiP status
      try {
        final status = await _pipService.pipStatusFuture;
        if (status != null && mounted) {
          _safeSetState(() {
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
      _safeSetState(() {
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
          httpHeaders: const {'User-Agent': appUserAgent},
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
        
        _safeSetState(() {
          _isLoading = false;
          _isPlaying = true;
          _error = null;
        });

        // Record play in watch history
        WatchHistoryService.recordPlay({
          'name': widget.channel.name,
          'url': widget.channel.url,
          'country': widget.channel.country ?? '',
          'category': widget.channel.category ?? '',
          'logo': widget.channel.logo,
        });

        // Create named listener for proper cleanup
        _playerListener = () {
          if (mounted && _videoController != null) {
            final vc = _videoController!.value;
            _safeSetState(() {
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
    
    _safeSetState(() {
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
      _safeSetState(() {
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
  
  void _reportHealth(String url, bool isWorking, [String? error]) async {
    // Fire-and-forget health reporting
    try {
      logger.info('Health report: ${widget.channel.name} url=${url.substring(0, url.length.clamp(0, 40))} working=$isWorking');
      
      // 1. ALWAYS save to LOCAL cache FIRST (primary source of truth)
      final prefs = await SharedPreferences.getInstance();
      final json = prefs.getString('channel_health_cache');
      Map<String, dynamic> healthMap = {};
      
      if (json != null) {
        healthMap = jsonDecode(json) as Map<String, dynamic>;
      }
      
      final urlHash = SharedDbService.hashUrl(url);
      healthMap[urlHash] = {
        'status': isWorking ? 'working' : 'failed',
        'lastChecked': DateTime.now().toUtc().toIso8601String(),
        'responseTimeMs': null,
      };
      
      await prefs.setString('channel_health_cache', jsonEncode(healthMap));
      logger.debug('Saved health status to LOCAL cache: working=$isWorking');
      
      // 2. THEN report to Supabase (SECONDARY, optional, fire-and-forget)
      SharedDbService.reportChannelStatus(
        url: url,
        status: isWorking ? 'working' : 'failed',
        responseTimeMs: null,
      );
    } catch (e) {
      // Silently ignore errors - never block playback
      logger.debug('Health report error (non-critical): $e');
    }
  }
  
  /// Report current channel as broken to Supabase. Debounced: one per session.
  void _reportBroken() {
    if (_reportSent) return;
    _safeSetState(() => _reportSent = true);
    
    final urlHash = SharedDbService.hashUrl(widget.channel.url);
    SharedDbService.reportBrokenChannel(urlHash);
    
    if (mounted) {
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
    _safeSetState(() {
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
    _safeSetState(() {
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
    // Check parental controls before navigating to the next/previous channel
    final parentalService = ParentalControlsService.instance;
    if (parentalService.isChannelBlocked(category: channel.category)) {
      _showParentalBlockForNavigation(channel, index);
      return;
    }

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

  /// Show PIN dialog when navigating to a blocked channel.
  Future<void> _showParentalBlockForNavigation(Channel channel, int index) async {
    final verified = await PinDialog.show(
      context,
      title: 'Content Blocked',
      subtitle: 'This channel is restricted by parental controls.\nEnter PIN to watch.',
      onSubmit: (pin) async {
        return ParentalControlsService.instance.verifyPin(pin);
      },
    );
    if (verified && mounted) {
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
  }

  /// Initialize player with a specific URL (used by source switcher)
  Future<void> _initializePlayerWithUrl(String streamUrl) async {
    try {
      final controller = VideoPlayerController.networkUrl(
        Uri.parse(streamUrl),
        httpHeaders: const {'User-Agent': appUserAgent},
      );
      
      await controller.initialize();
      
      if (!mounted) {
        controller.dispose();
        return;
      }
      
      _videoController = controller;
      _playerListener = () {
        if (mounted) {
          _safeSetState(() {
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
      
      _safeSetState(() {
        _isLoading = false;
        _isPlaying = true;
        _error = null;
      });
    } catch (e) {
      logger.error('Failed to play source: $streamUrl', e);
      _safeSetState(() {
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
    _safeSetState(() {
      _showControls = !_showControls;
    });
    
    if (_showControls) {
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted && _isPlaying) {
          _safeSetState(() => _showControls = false);
        }
      });
    }
  }

  void _openInExternalPlayer() async {
    final streamUrl = widget.channel.url;
    final channelName = widget.channel.name;
    logger.info('Opening $channelName in external player');

    // Security: Validate URL scheme before launching external player
    const allowedSchemes = ['http', 'https', 'rtmp', 'rtsp', 'mms'];
    final uri = Uri.tryParse(streamUrl);
    if (uri == null || !allowedSchemes.contains(uri.scheme.toLowerCase())) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Invalid or unsupported stream URL')),
        );
      }
      return;
    }

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
      _safeSetState(() {
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
                                        fontFamilyFallback: ['Roboto', 'Noto Sans', 'Noto Sans Hebrew', 'sans-serif'],
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
                        // Report broken channel button
                        IconButton(
                          icon: Icon(
                            _reportSent ? Icons.check_circle : Icons.report_problem,
                            color: _reportSent ? Colors.green : Colors.amber,
                          ),
                          tooltip: _reportSent ? 'Reported' : 'Report broken',
                          onPressed: _reportSent ? null : _reportBroken,
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
                            const Icon(Icons.stream, color: Colors.white70, size: 18),
                            const SizedBox(width: 10),
                            const Text(
                              'Source:',
                              style: TextStyle(
                                color: Colors.white70,
                                fontSize: 13,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: SizedBox(
                                height: 32,
                                child: ListView.builder(
                                  scrollDirection: Axis.horizontal,
                                  itemCount: widget.channel.urls.length,
                                  itemBuilder: (context, index) {
                                    final isActive = index == _currentUrlIndex;
                                    return Padding(
                                      padding: const EdgeInsets.only(right: 8),
                                      child: Material(
                                        color: Colors.transparent,
                                        child: InkWell(
                                          onTap: () => _switchSource(index),
                                          borderRadius: BorderRadius.circular(16),
                                          child: Container(
                                            padding: const EdgeInsets.symmetric(
                                              horizontal: 14,
                                              vertical: 6,
                                            ),
                                            decoration: BoxDecoration(
                                              color: isActive
                                                  ? Colors.white
                                                  : Colors.white.withOpacity(0.15),
                                              borderRadius: BorderRadius.circular(16),
                                              border: Border.all(
                                                color: isActive
                                                    ? Colors.white
                                                    : Colors.white.withOpacity(0.3),
                                                width: 1.5,
                                              ),
                                            ),
                                            child: Text(
                                              '${index + 1}',
                                              style: TextStyle(
                                                color: isActive
                                                    ? Colors.black87
                                                    : Colors.white,
                                                fontSize: 13,
                                                fontWeight: FontWeight.w600,
                                              ),
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
      return Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 72,
            height: 72,
            child: CircularProgressIndicator(
              color: Colors.white,
              strokeWidth: 5,
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'Loading stream...',
            style: TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Please wait',
            style: TextStyle(
              color: Colors.white60,
              fontSize: 13,
            ),
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
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.15),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.error_outline,
                  size: 72,
                  color: Colors.red,
                ),
              ),
              const SizedBox(height: 24),
              Text(
                _error!.userMessage,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: Colors.white.withOpacity(0.15),
                    width: 1,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(
                            Icons.lightbulb_outline,
                            size: 18,
                            color: Colors.white70,
                          ),
                        ),
                        const SizedBox(width: 12),
                        const Text(
                          'What to do:',
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w600,
                            fontSize: 15,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _error!.recoverySuggestion,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                        height: 1.6,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
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
                const SizedBox(height: 28),
                const Text(
                  'Try a different source:',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  height: 44,
                  child: ListView.builder(
                    shrinkWrap: true,
                    scrollDirection: Axis.horizontal,
                    itemCount: widget.channel.urls.length,
                    itemBuilder: (context, index) {
                      final isCurrent = index == _currentUrlIndex;
                      return Padding(
                        padding: const EdgeInsets.only(right: 10),
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: isCurrent ? null : () {
                              // Clear failed state and try this source
                              _failedIndices.clear();
                              _switchSource(index);
                            },
                            borderRadius: BorderRadius.circular(22),
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 20,
                                vertical: 10,
                              ),
                              decoration: BoxDecoration(
                                color: isCurrent
                                    ? Colors.red.withOpacity(0.2)
                                    : Colors.white.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(22),
                                border: Border.all(
                                  color: isCurrent
                                      ? Colors.red.withOpacity(0.5)
                                      : Colors.white.withOpacity(0.3),
                                  width: 1.5,
                                ),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    isCurrent ? Icons.close : Icons.play_arrow,
                                    size: 18,
                                    color: isCurrent
                                        ? Colors.white38
                                        : Colors.white,
                                  ),
                                  const SizedBox(width: 6),
                                  Text(
                                    'Source ${index + 1}',
                                    style: TextStyle(
                                      color: isCurrent
                                          ? Colors.white38
                                          : Colors.white,
                                      fontSize: 14,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
              const SizedBox(height: 32),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                alignment: WrapAlignment.center,
                children: [
                  FilledButton.icon(
                    onPressed: () {
                      _safeSetState(() {
                        _isLoading = true;
                        _error = null;
                      });
                      _initializePlayer();
                    },
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry'),
                    style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 28,
                        vertical: 14,
                      ),
                    ),
                  ),
                  OutlinedButton.icon(
                    onPressed: _openInExternalPlayer,
                    icon: const Icon(Icons.open_in_new),
                    label: const Text('External Player'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white,
                      side: BorderSide(
                        color: Colors.white.withOpacity(0.5),
                        width: 1.5,
                      ),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 28,
                        vertical: 14,
                      ),
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
      // Radio channels: show channel name + radio icon instead of black video
      if (widget.channel.mediaType == 'Radio') {
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(28),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.08),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  _isPlaying ? Icons.radio : Icons.radio_outlined,
                  size: 72,
                  color: Colors.white70,
                ),
              ),
              const SizedBox(height: 24),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 32),
                child: Text(
                  widget.channel.name,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    fontFamilyFallback: ['Roboto', 'Noto Sans', 'Noto Sans Hebrew', 'sans-serif'],
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (widget.channel.country != null) ...[
                const SizedBox(height: 8),
                Text(
                  widget.channel.country!,
                  style: const TextStyle(
                    color: Colors.white54,
                    fontSize: 14,
                  ),
                ),
              ],
              const SizedBox(height: 16),
              if (_isPlaying)
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: List.generate(5, (i) => Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 2),
                    child: Container(
                      width: 4,
                      height: 12.0 + (i % 3) * 8,
                      decoration: BoxDecoration(
                        color: Colors.white54,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  )),
                ),
            ],
          ),
        );
      }

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
