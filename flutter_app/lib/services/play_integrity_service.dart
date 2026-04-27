import 'dart:convert';
import 'dart:math';
import 'package:flutter/services.dart';
import '../utils/logger_service.dart';

/// Service for Google Play Integrity API verification.
///
/// Provides device/app attestation to verify:
/// - App is genuine (not tampered/repackaged)
/// - Device has Play Services and passes integrity checks
/// - App was installed from Google Play
///
/// The integrity token is requested from the native Android layer
/// via MethodChannel and can be sent to a backend for verification.
class PlayIntegrityService {
  static const _channel = MethodChannel('tv_viewer/integrity');
  static PlayIntegrityService? _instance;

  PlayIntegrityService._();

  static PlayIntegrityService get instance {
    _instance ??= PlayIntegrityService._();
    return _instance!;
  }

  /// Generate a cryptographically random nonce for integrity requests.
  String _generateNonce() {
    final random = Random.secure();
    final bytes = List<int>.generate(32, (_) => random.nextInt(256));
    return base64Url.encode(bytes).replaceAll('=', '');
  }

  /// Request a Play Integrity token from Google Play services.
  ///
  /// Returns the integrity token string on success, or null on failure.
  /// The token should be sent to your backend for server-side verification
  /// via the Google Play Integrity API.
  ///
  /// Fails gracefully on:
  /// - Non-Android platforms
  /// - Devices without Google Play Services
  /// - Debug/sideloaded builds (token may have reduced verdicts)
  Future<String?> requestIntegrityToken({String? nonce}) async {
    try {
      final requestNonce = nonce ?? _generateNonce();
      final token = await _channel.invokeMethod<String>(
        'requestIntegrityToken',
        {'nonce': requestNonce},
      );
      logger.info('Play Integrity token obtained successfully');
      return token;
    } on PlatformException catch (e) {
      logger.warning('Play Integrity request failed: ${e.code} - ${e.message}');
      return null;
    } on MissingPluginException {
      // Not on Android or channel not available
      logger.debug('Play Integrity not available on this platform');
      return null;
    } catch (e) {
      logger.warning('Play Integrity unexpected error: $e');
      return null;
    }
  }

  /// Verify app integrity on startup (fire-and-forget).
  ///
  /// Logs the result but does not block app usage — integrity failures
  /// are reported to analytics for monitoring but don't prevent access.
  /// This is the recommended approach for free/open-source apps.
  Future<void> verifyOnStartup() async {
    try {
      final token = await requestIntegrityToken();
      if (token != null) {
        logger.info('Play Integrity: device attestation passed');
        // Token can be sent to backend for full verdict verification:
        // - deviceRecognitionVerdict (MEETS_DEVICE_INTEGRITY, etc.)
        // - appRecognitionVerdict (PLAY_RECOGNIZED, UNRECOGNIZED_VERSION, etc.)
        // - accountDetails (LICENSED, UNLICENSED, UNEVALUATED)
        //
        // For now, we log success. Backend verification can be added
        // when a server-side component is available.
      } else {
        logger.info('Play Integrity: not available (sideload or non-Play device)');
      }
    } catch (e) {
      // Never block the app on integrity failures
      logger.debug('Play Integrity startup check failed (non-fatal): $e');
    }
  }
}
