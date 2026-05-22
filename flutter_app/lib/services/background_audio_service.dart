import 'package:audio_service/audio_service.dart';
import 'package:video_player/video_player.dart';
import '../utils/logger_service.dart';

/// Background audio handler that creates a foreground service notification
/// for media playback (like Chrome/Spotify). This keeps audio alive when
/// the app is in the background and shows media controls in the notification.
class BackgroundAudioHandler extends BaseAudioHandler with SeekHandler {
  VideoPlayerController? _videoController;
  String _channelName = '';
  String _channelCategory = '';
  bool _isPlaying = false;

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
      {required String channelName, String? category}) {
    _videoController = controller;
    _channelName = channelName;
    _channelCategory = category ?? 'Live TV';

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
    _isPlaying = true;
    _updatePlaybackState(playing: true);
    logger.info('Background audio attached: $channelName');
  }

  /// Detach the controller (when player screen is disposed).
  void detachController() {
    _videoController = null;
    _isPlaying = false;
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
    _videoController?.play();
    _isPlaying = true;
    _updatePlaybackState(playing: true);
  }

  @override
  Future<void> pause() async {
    _videoController?.pause();
    _isPlaying = false;
    _updatePlaybackState(playing: false);
  }

  @override
  Future<void> stop() async {
    _videoController?.pause();
    _isPlaying = false;
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
}

/// Initialize the audio service (call once in main.dart).
/// Returns the handler instance for use throughout the app.
Future<BackgroundAudioHandler> initAudioService() async {
  final handler = await AudioService.init(
    builder: () => BackgroundAudioHandler(),
    config: const AudioServiceConfig(
      androidNotificationChannelId: 'com.tvviewer.app.audio',
      androidNotificationChannelName: 'TV Viewer Playback',
      androidNotificationChannelDescription: 'Shows when TV/Radio is playing',
      androidNotificationOngoing: true,
      androidStopForegroundOnPause: false,
      androidNotificationIcon: 'drawable/ic_notification',
      // Keep notification while paused so user can resume
      fastForwardInterval: Duration.zero,
      rewindInterval: Duration.zero,
    ),
  );
  logger.info('Audio service initialized');
  return handler;
}
