import 'package:android_intent_plus/android_intent.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

/// Enum for supported external video players
enum VideoPlayer {
  vlc('org.videolan.vlc', 'VLC'),
  vlcBeta('org.videolan.vlc.betav7neon', 'VLC Beta'),
  mxPlayerFree('com.mxtech.videoplayer.ad', 'MX Player Free'),
  mxPlayerPro('com.mxtech.videoplayer.pro', 'MX Player Pro'),
  mpv('is.xyz.mpv', 'MPV Player'),
  justPlayer('com.brouken.player', 'Just Player'),
  systemDefault('', 'System Default');

  final String packageName;
  final String displayName;

  const VideoPlayer(this.packageName, this.displayName);
}

/// Service for handling external video player integration
class ExternalPlayerService {
  /// Check if a specific player is installed on the device
  static Future<bool> isPlayerInstalled(VideoPlayer player) async {
    if (player == VideoPlayer.systemDefault) return true;

    try {
      // For Android, we'll use a simple approach
      // In production, you'd use method channels to check package manager
      return true; // Assume installed for now
    } catch (e) {
      debugPrint('Error checking player installation: $e');
      return false;
    }
  }

  /// Get list of installed video players
  static Future<List<VideoPlayer>> getInstalledPlayers() async {
    final installedPlayers = <VideoPlayer>[];

    for (final player in VideoPlayer.values) {
      if (await isPlayerInstalled(player)) {
        installedPlayers.add(player);
      }
    }

    return installedPlayers;
  }

  /// Open stream in a specific external player
  static Future<bool> openInPlayer({
    required String streamUrl,
    required VideoPlayer player,
    String? title,
    Map<String, String>? headers,
  }) async {
    try {
      if (player == VideoPlayer.systemDefault) {
        return await _openWithSystemDefault(streamUrl);
      }

      // For Android - use android_intent_plus
      if (defaultTargetPlatform == TargetPlatform.android) {
        final intent = AndroidIntent(
          action: 'android.intent.action.VIEW',
          data: streamUrl,
          package: player.packageName,
          type: 'video/*',
          arguments: _getPlayerSpecificArguments(player, title, headers),
        );

        await intent.launch();
        return true;
      }

      // Fallback for other platforms
      return await _openWithSystemDefault(streamUrl);
    } catch (e) {
      debugPrint('Failed to open in ${player.displayName}: $e');
      return false;
    }
  }

  /// Get player-specific intent arguments
  static Map<String, dynamic> _getPlayerSpecificArguments(
    VideoPlayer player,
    String? title,
    Map<String, String>? headers,
  ) {
    final args = <String, dynamic>{};

    if (title != null) {
      args['title'] = title;
    }

    switch (player) {
      case VideoPlayer.mxPlayerFree:
      case VideoPlayer.mxPlayerPro:
        args['decode_mode'] = 2; // Hardware acceleration
        args['secure_uri'] = true;
        if (headers != null) {
          args['headers'] = headers.entries
              .map((e) => '${e.key}: ${e.value}')
              .join('\n');
        }
        break;

      case VideoPlayer.vlc:
      case VideoPlayer.vlcBeta:
        args['from_start'] = false;
        args['position'] = 0;
        break;

      case VideoPlayer.justPlayer:
        args['secure_uri'] = true;
        break;

      default:
        break;
    }

    return args;
  }

  /// Open stream with system default handler
  static Future<bool> _openWithSystemDefault(String streamUrl) async {
    try {
      final uri = Uri.parse(streamUrl);
      return await launchUrl(
        uri,
        mode: LaunchMode.externalApplication,
      );
    } catch (e) {
      debugPrint('Failed to open with system default: $e');
      return false;
    }
  }

  /// Show dialog to select external player
  static Future<VideoPlayer?> showPlayerSelectionDialog(
    BuildContext context,
    List<VideoPlayer> players,
  ) async {
    return await showDialog<VideoPlayer>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Select Player'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: players.map((player) {
              return ListTile(
                leading: _getPlayerIcon(player),
                title: Text(player.displayName),
                onTap: () => Navigator.pop(context, player),
              );
            }).toList(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
        ],
      ),
    );
  }

  /// Get icon for player
  static Widget _getPlayerIcon(VideoPlayer player) {
    IconData iconData;
    Color? color;

    switch (player) {
      case VideoPlayer.vlc:
      case VideoPlayer.vlcBeta:
        iconData = Icons.play_circle;
        color = Colors.orange;
        break;
      case VideoPlayer.mxPlayerFree:
      case VideoPlayer.mxPlayerPro:
        iconData = Icons.movie;
        color = Colors.blue;
        break;
      case VideoPlayer.mpv:
        iconData = Icons.play_arrow;
        color = Colors.purple;
        break;
      case VideoPlayer.justPlayer:
        iconData = Icons.videocam;
        color = Colors.green;
        break;
      case VideoPlayer.systemDefault:
        iconData = Icons.open_in_new;
        color = Colors.grey;
        break;
    }

    return Icon(iconData, color: color);
  }

  /// Show error dialog when no players are available
  static void showNoPlayersDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.error_outline, color: Colors.orange),
            SizedBox(width: 8),
            Text('No Video Players Found'),
          ],
        ),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Install a video player app to play this stream:'),
            SizedBox(height: 12),
            Text('• VLC for Android'),
            Text('• MX Player'),
            Text('• MPV Player'),
            Text('• Just Player'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }
}
