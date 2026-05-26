import 'package:audio_service/audio_service.dart';
import 'package:just_audio/just_audio.dart';
import 'package:video_player/video_player.dart';
import '../utils/logger_service.dart';

/// Background audio handler that creates a foreground service notification
/// for media playback (like Chrome/Spotify). This keeps audio alive when
/// the app is in the background and shows media controls in the notification.
///
/// Uses just_audio for actual background playback because video_player's
/// ExoPlayer surface is destroyed when the app goes to background on Android 14+.
class BackgroundAudioHandler extends BaseAudioHandler with SeekHandler {
  VideoPlayerController? _videoController;
  final AudioPlayer _audioPlayer = AudioPlayer();
  String _channelName = '';
  String _channelCategory = '';
  String? _currentUrl;
  bool _isBackgroundActive = false;

  static BackgroundAudioHandler? _instance;

  /// Singleton access — initialized via AudioService.init() in main.dart
  static BackgroundAudioHandler? get instance => _instance;

  BackgroundAudioHandler() {
    _instance = this;
    // Set initial playback state
    playbackState.add(PlaybackState(
      controls: [MediaControl.play, MediaControl.stop],
      processingState: AudioProcessingState.idle,
      playing: false,
    ));
  }

  /// Attach a VideoPlayerController to this handler for background control.
  void attachController(VideoPlayerController controller,
      {required String channelName, String? category, String? streamUrl}) {
    _videoController = controller;
    _channelName = channelName;
    _channelCategory = category ?? 'Live TV';
    _currentUrl = streamUrl;

    // Update media item metadata (shown in notification)
    mediaItem.add(MediaItem(
      id: channelName,
      title: channelName,
      artist: _channelCategory,
      album: 'TV Viewer',
      displayTitle: channelName,
      displaySubtitle: _channelCategory,
      playable: true,
    ));

    // Mark as playing
    _updatePlaybackState(playing: true);
    logger.info('Background audio attached: $channelName (url: ${streamUrl != null ? "provided" : "none"})');
  }

  /// Activate background-only audio playback via just_audio.
  /// Call when app goes to background with background playback enabled.
  Future<void> activateBackgroundAudio(String url) async {
    if (_isBackgroundActive) return;
    _isBackgroundActive = true;
    _currentUrl = url;
    
    try {
      // Pause video player (surface will be destroyed anyway)
      _videoController?.pause();
      
      // Start audio-only playback via just_audio
      await _audioPlayer.setUrl(url);
      await _audioPlayer.play();
      _updatePlaybackState(playing: true);
      logger.info('Background audio activated for: $_channelName');
    } catch (e) {
      logger.error('Failed to activate background audio: $e');
      _isBackgroundActive = false;
    }
  }

  /// Deactivate background audio and resume video player.
  /// Call when app returns to foreground.
  Future<void> deactivateBackgroundAudio() async {
    if (!_isBackgroundActive) return;
    _isBackgroundActive = false;
    
    try {
      await _audioPlayer.stop();
      // Resume video player now that surface is available again
      _videoController?.play();
      logger.info('Background audio deactivated, video resumed');
    } catch (e) {
      logger.error('Failed to deactivate background audio: $e');
    }
  }

  /// Whether background audio-only mode is currently active
  bool get isBackgroundActive => _isBackgroundActive;

  /// Detach the controller (when player screen is disposed).
  void detachController() {
    _videoController = null;
    _currentUrl = null;
    if (_isBackgroundActive) {
      _audioPlayer.stop();
      _isBackgroundActive = false;
    }
    _updatePlaybackState(playing: false, state: AudioProcessingState.idle);
    mediaItem.add(const MediaItem(id: '', title: ''));
    logger.info('Background audio detached');
  }

  /// Update the channel name in the notification (e.g., when switching channels).
  void updateMetadata({required String channelName, String? category}) {
    _channelName = channelName;
    _channelCategory = category ?? 'Live TV';
    mediaItem.add(MediaItem(
      id: channelName,
      title: channelName,
      artist: _channelCategory,
      album: 'TV Viewer',
      displayTitle: channelName,
      displaySubtitle: _channelCategory,
      playable: true,
    ));
  }

  @override
  Future<void> play() async {
    if (_isBackgroundActive) {
      _audioPlayer.play();
    } else {
      _videoController?.play();
    }
    _updatePlaybackState(playing: true);
  }

  @override
  Future<void> pause() async {
    if (_isBackgroundActive) {
      _audioPlayer.pause();
    } else {
      _videoController?.pause();
    }
    _updatePlaybackState(playing: false);
  }

  @override
  Future<void> stop() async {
    if (_isBackgroundActive) {
      await _audioPlayer.stop();
      _isBackgroundActive = false;
    }
    _videoController?.pause();
    _updatePlaybackState(playing: false, state: AudioProcessingState.idle);
    await super.stop();
  }

  void _updatePlaybackState({
    required bool playing,
    AudioProcessingState state = AudioProcessingState.ready,
  }) {
    playbackState.add(PlaybackState(
      controls: [
        if (playing) MediaControl.pause else MediaControl.play,
        MediaControl.stop,
      ],
      systemActions: const {
        MediaAction.play,
        MediaAction.pause,
        MediaAction.stop,
      },
      processingState: state,
      playing: playing,
    ));
  }

  /// Dispose the just_audio player (call on app termination)
  Future<void> disposeAudioPlayer() async {
    await _audioPlayer.dispose();
  }
}

/// Initialize the audio service (call once in main.dart).
/// Returns the handler instance for use throughout the app.
Future<BackgroundAudioHandler> initAudioService() async {
  final handler = await AudioService.init(
    builder: () => BackgroundAudioHandler(),
    config: AudioServiceConfig(
      androidNotificationChannelId: 'com.tvviewer.app.audio',
      androidNotificationChannelName: 'TV Viewer Playback',
      androidNotificationChannelDescription: 'Shows when TV/Radio is playing',
      androidNotificationOngoing: true,
      androidStopForegroundOnPause: false,
      androidNotificationIcon: 'drawable/ic_notification',
    ),
  );
  logger.info('Audio service initialized');
  return handler;
}
