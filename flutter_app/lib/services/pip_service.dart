import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:floating/floating.dart';

/// Service to handle Picture-in-Picture mode for Android
/// 
/// Requirements:
/// - Android API 26+ (Android 8.0)
/// - supportsPictureInPicture="true" in AndroidManifest.xml
/// - resizeableActivity="true" in AndroidManifest.xml
class PipService {
  static final PipService _instance = PipService._internal();
  factory PipService() => _instance;
  PipService._internal();

  /// Floating instance for PiP management
  Floating? _floating;
  
  /// Whether PiP is supported on this device
  bool _isSupported = false;
  
  /// Whether PiP mode is currently active
  bool _isPipActive = false;
  
  /// Initialize PiP service
  Future<void> initialize() async {
    // PiP is only supported on Android
    if (!Platform.isAndroid) {
      debugPrint('PiP: Not supported on ${Platform.operatingSystem}');
      return;
    }

    try {
      _floating = Floating();
      
      // Check if PiP is supported (requires Android 8.0+)
      final supportCheck = await _floating?.isPipAvailable;
      _isSupported = supportCheck ?? false;
      
      if (_isSupported) {
        debugPrint('PiP: Supported and initialized');
      } else {
        debugPrint('PiP: Not supported on this device (requires Android 8.0+)');
      }
    } catch (e) {
      debugPrint('PiP: Failed to initialize: $e');
      _isSupported = false;
    }
  }

  /// Check if PiP is supported
  bool get isSupported => _isSupported;
  
  /// Check if PiP is currently active
  bool get isPipActive => _isPipActive;

  /// Enable PiP mode
  /// 
  /// [aspectRatio] - The aspect ratio for the PiP window (default: 16/9)
  /// Returns true if PiP was successfully enabled
  Future<bool> enablePip({Rational aspectRatio = const Rational(16, 9)}) async {
    if (!_isSupported || _floating == null) {
      debugPrint('PiP: Cannot enable - not supported');
      return false;
    }

    try {
      // Enable PiP mode
      final result = await _floating!.enable();
      
      if (result == PiPStatus.enabled) {
        _isPipActive = true;
        debugPrint('PiP: Enabled successfully');
        return true;
      } else {
        debugPrint('PiP: Failed to enable - status: $result');
        return false;
      }
    } catch (e) {
      debugPrint('PiP: Error enabling: $e');
      return false;
    }
  }

  /// Disable PiP mode and return to full screen
  Future<void> disablePip() async {
    if (_floating == null) return;

    try {
      _floating!.dispose();
      _isPipActive = false;
      debugPrint('PiP: Disabled');
    } catch (e) {
      debugPrint('PiP: Error disabling: $e');
    }
  }

  /// Listen to PiP status changes
  /// 
  /// Returns a stream of PiP status updates
  /// Get current PiP status
  Future<PiPStatus>? get pipStatusFuture => _floating?.pipStatus;

  /// Toggle PiP mode
  Future<bool> togglePip({Rational aspectRatio = const Rational(16, 9)}) async {
    if (_isPipActive) {
      await disablePip();
      return false;
    } else {
      return await enablePip(aspectRatio: aspectRatio);
    }
  }

  /// Calculate aspect ratio from video dimensions
  Rational calculateAspectRatio(Size videoSize) {
    final width = videoSize.width.toInt();
    final height = videoSize.height.toInt();
    
    if (width <= 0 || height <= 0) {
      return const Rational(16, 9); // Default
    }
    
    // Common aspect ratios
    final ratio = width / height;
    
    if ((ratio - 16 / 9).abs() < 0.1) {
      return const Rational(16, 9);
    } else if ((ratio - 4 / 3).abs() < 0.1) {
      return const Rational(4, 3);
    } else if ((ratio - 21 / 9).abs() < 0.1) {
      return const Rational(21, 9);
    } else {
      // Use actual dimensions
      return Rational(width, height);
    }
  }

  /// Update PiP window with new parameters
  /// Useful when video aspect ratio changes during playback
  Future<void> updatePipParams(Rational aspectRatio) async {
    if (!_isPipActive || _floating == null) return;

    try {
      // Re-enable with new parameters
      await _floating!.enable();
      debugPrint('PiP: Updated aspect ratio to $aspectRatio');
    } catch (e) {
      debugPrint('PiP: Error updating params: $e');
    }
  }

  /// Dispose resources
  void dispose() {
    _floating?.dispose();
    _floating = null;
    _isPipActive = false;
  }
}
