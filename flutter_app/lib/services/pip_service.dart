import 'dart:ui' show Size;

/// Stub PiP service — Picture-in-Picture temporarily disabled
/// pending floating package update for Flutter 3.32 compatibility.
class PipService {
  static final PipService _instance = PipService._internal();
  factory PipService() => _instance;
  PipService._internal();

  bool _isSupported = false;
  bool _isPipActive = false;

  Future<void> initialize() async {
    _isSupported = false;
  }

  bool get isSupported => _isSupported;
  bool get isPipActive => _isPipActive;

  Future<bool> enablePip({Rational aspectRatio = const Rational(16, 9)}) async {
    return false;
  }

  Future<void> disablePip() async {
    _isPipActive = false;
  }

  Future<PiPStatus>? get pipStatusFuture => null;

  Future<bool> togglePip({Rational aspectRatio = const Rational(16, 9)}) async {
    return false;
  }

  Rational calculateAspectRatio(Size videoSize) {
    return const Rational(16, 9);
  }

  Future<void> updatePipParams(Rational aspectRatio) async {}

  void dispose() {}
}

/// Stub for PiPStatus enum (was from floating package)
enum PiPStatus { enabled, disabled, unavailable }

/// Stub for Rational (was from floating package)
class Rational {
  final int numerator;
  final int denominator;
  const Rational(this.numerator, this.denominator);
}
