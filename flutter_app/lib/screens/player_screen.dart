import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:video_player/video_player.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import 'package:floating/floating.dart';
import '../models/channel.dart';
import '../services/pip_service.dart';
import '../widgets/live_badge.dart';
import '../widgets/quality_badge.dart';
import '../utils/error_handler.dart';
import '../utils/logger_service.dart';

class PlayerScreen extends StatefulWidget {
  final Channel channel;

  const PlayerScreen({super.key, required this.channel});

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

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    
    _initializePlayer();
    _initializeWakeLock();
    _initializePip();
    
    // Lock to landscape for video
    SystemChrome.setPreferredOrientations([
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
      
      // Listen to PiP status changes
      _pipService.pipStatusStream?.listen((status) {
        if (mounted) {
          setState(() {
            _isPipMode = status == PiPStatus.enabled;
          });
          
          // Handle PiP lifecycle
          if (status == PiPStatus.enabled) {
            logger.info('Entered PiP mode for ${widget.channel.name}');
          } else if (status == PiPStatus.disabled) {
            logger.info('Exited PiP mode');
          }
        }
      });
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

  Future<void> _initializePlayer() async {
    // Dispose existing controller before creating new one (fixes memory leak on retry)
    _disposeController();
    
    logger.info('Initializing player for ${widget.channel.name} (${widget.channel.url})');
    
    try {
      _videoController = VideoPlayerController.networkUrl(
        Uri.parse(widget.channel.url),
        httpHeaders: const {'User-Agent': 'TV Viewer/1.5.0'},
      );

      // Add timeout to initialization
      await _videoController!.initialize().timeout(
        const Duration(seconds: 30),
        onTimeout: () {
          throw ErrorHandler.streamError(
            'timeout',
            'Stream initialization timeout after 30 seconds for ${widget.channel.name}',
          );
        },
      );
      
      _videoController!.play();
      _videoController!.setVolume(_volume); // Set initial volume
      
      // Get video info
      final value = _videoController!.value;
      if (value.isInitialized) {
        _resolution = '${value.size.width.toInt()}x${value.size.height.toInt()}';
        logger.info('Stream initialized successfully - Resolution: $_resolution');
      }

      setState(() {
        _isLoading = false;
        _isPlaying = true;
      });

      // Create named listener for proper cleanup
      _playerListener = () {
        if (mounted && _videoController != null) {
          setState(() {
            _isPlaying = _videoController!.value.isPlaying;
          });
        }
      };
      _videoController!.addListener(_playerListener!);
    } catch (e, stackTrace) {
      final appError = ErrorHandler.handle(e, stackTrace);
      logger.error('Player initialization failed for ${widget.channel.name}', e, stackTrace);
      logger.error('Error details: ${appError.getDetailedLog()}');
      
      setState(() {
        _isLoading = false;
        _error = appError;
      });
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
    setState(() {
      _volume = volume;
    });
    _videoController?.setVolume(volume);
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
    logger.info('Opening ${widget.channel.name} in external player');
    
    // Try various external player intents directly (Issue #26)
    // Don't wait for canLaunchUrl - just try to launch
    final players = [
      // VLC - try custom scheme first
      {'uri': 'vlc://$streamUrl', 'name': 'VLC (custom scheme)'},
      // MX Player - use intent scheme
      {'uri': 'intent:$streamUrl#Intent;package=com.mxtech.videoplayer.ad;type=video/*;end', 'name': 'MX Player'},
      // VLC package intent
      {'uri': 'intent:$streamUrl#Intent;package=org.videolan.vlc;type=video/*;end', 'name': 'VLC (intent)'},
      // Generic - let Android choose
      {'uri': streamUrl, 'name': 'System default'},
    ];
    
    bool launched = false;
    
    for (final player in players) {
      try {
        final uri = Uri.parse(player['uri'] as String);
        logger.debug('Trying ${player['name']}: ${player['uri']}');
        
        await launchUrl(
          uri,
          mode: LaunchMode.externalApplication,
        );
        
        launched = true;
        logger.info('Successfully opened with ${player['name']}');
        
        // Show success message
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Opening in ${player['name']}'),
              duration: const Duration(seconds: 1),
            ),
          );
        }
        return;
      } catch (e) {
        logger.debug('Failed to launch with ${player['name']}: $e');
        // Continue to next player
      }
    }
    
    // If all failed, show error with URL copy option
    if (!launched && mounted) {
      logger.warning('All external player attempts failed');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Could not open external player. Install VLC or MX Player.'),
          duration: const Duration(seconds: 4),
          action: SnackBarAction(
            label: 'Copy URL',
            onPressed: () {
              Clipboard.setData(ClipboardData(text: streamUrl));
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('URL copied to clipboard')),
              );
            },
          ),
        ),
      );
    }
  }
  
  void _showCastDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.cast),
            SizedBox(width: 8),
            Text('Cast to Device'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Cast support requires Google Cast SDK.'),
            const SizedBox(height: 16),
            const Text(
              'To cast this stream:\n'
              '1. Open in VLC/MX Player\n'
              '2. Use their built-in cast feature',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.pop(context);
                _openInExternalPlayer();
              },
              icon: const Icon(Icons.open_in_new),
              label: const Text('Open in External Player'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
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
