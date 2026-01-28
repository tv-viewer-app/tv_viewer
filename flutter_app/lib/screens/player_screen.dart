import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:video_player/video_player.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/channel.dart';

class PlayerScreen extends StatefulWidget {
  final Channel channel;

  const PlayerScreen({super.key, required this.channel});

  @override
  State<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends State<PlayerScreen> {
  VideoPlayerController? _videoController;
  bool _isLoading = true;
  bool _isPlaying = false;
  bool _showControls = true;
  String? _error;
  String? _resolution;
  String? _bitrate;
  
  // Named listener for proper cleanup
  VoidCallback? _playerListener;

  @override
  void initState() {
    super.initState();
    _initializePlayer();
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

  Future<void> _initializePlayer() async {
    // Dispose existing controller before creating new one (fixes memory leak on retry)
    _disposeController();
    
    try {
      _videoController = VideoPlayerController.networkUrl(
        Uri.parse(widget.channel.url),
        httpHeaders: const {'User-Agent': 'TV Viewer/1.5.0'},
      );

      await _videoController!.initialize();
      _videoController!.play();
      
      // Get video info
      final value = _videoController!.value;
      if (value.isInitialized) {
        _resolution = '${value.size.width.toInt()}x${value.size.height.toInt()}';
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
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = e.toString();
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
    
    // Try various external player intents
    final players = [
      // VLC
      Uri.parse('vlc://$streamUrl'),
      // MX Player
      Uri.parse('intent:$streamUrl#Intent;package=com.mxtech.videoplayer.ad;type=video/*;end'),
      // Generic video intent
      Uri.parse(streamUrl),
    ];
    
    for (final playerUri in players) {
      try {
        if (await canLaunchUrl(playerUri)) {
          await launchUrl(
            playerUri,
            mode: LaunchMode.externalApplication,
          );
          return;
        }
      } catch (e) {
        debugPrint('Failed to launch $playerUri: $e');
      }
    }
    
    // Final fallback - try to launch with external non-browser app
    try {
      final uri = Uri.parse(streamUrl);
      final launched = await launchUrl(
        uri,
        mode: LaunchMode.externalNonBrowserApplication,
      );
      
      if (!launched) {
        // Try external application mode
        await launchUrl(
          uri,
          mode: LaunchMode.externalApplication,
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not open external player. Install VLC or MX Player.'),
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

  @override
  void dispose() {
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
                              Text(
                                widget.channel.name,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                              // Show resolution and bitrate
                              if (_resolution != null || widget.channel.resolution != null)
                                Text(
                                  [
                                    _resolution ?? widget.channel.resolution,
                                    widget.channel.formattedBitrate,
                                  ].where((e) => e != null).join(' • '),
                                  style: const TextStyle(
                                    color: Colors.white70,
                                    fontSize: 12,
                                  ),
                                ),
                            ],
                          ),
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
              
            // Bottom info bar
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
                      colors: [Colors.black54, Colors.transparent],
                    ),
                  ),
                  padding: const EdgeInsets.all(16),
                  child: Row(
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
      return Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 64, color: Colors.red),
          const SizedBox(height: 16),
          Text(
            'Could not load stream',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: Colors.white,
                ),
          ),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Text(
              _error!,
              style: const TextStyle(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _openInExternalPlayer,
            icon: const Icon(Icons.play_arrow),
            label: const Text('Open in External Player'),
          ),
          const SizedBox(height: 12),
          TextButton(
            onPressed: () {
              setState(() {
                _isLoading = true;
                _error = null;
              });
              _initializePlayer();
            },
            child: const Text('Retry'),
          ),
        ],
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
