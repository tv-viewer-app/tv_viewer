import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/logger_service.dart';

/// Parental controls service for TV Viewer.
///
/// Provides PIN-based locking, category blocking, and age-rating filtering
/// to restrict access to inappropriate channels.
///
/// Ported from Python: utils/parental.py
class ParentalControlsService extends ChangeNotifier {
  // Persistence keys
  static const String _keyEnabled = 'parental_enabled';
  static const String _keyPinHash = 'parental_pin_hash';
  static const String _keyBlockedCategories = 'parental_blocked_categories';
  static const String _keyMinAge = 'parental_min_age';

  // Lockout configuration
  static const int maxFailedAttempts = 3;
  static const int lockoutDurationSeconds = 30;

  // State
  bool _enabled = false;
  String? _pinHash;
  List<String> _blockedCategories = [];
  int _minAge = 0;

  // Lockout state (not persisted)
  int _failedAttempts = 0;
  DateTime? _lockoutUntil;

  // Getters
  bool get enabled => _enabled;
  bool get hasPin => _pinHash != null;
  List<String> get blockedCategories => List.unmodifiable(_blockedCategories);
  int get minAge => _minAge;
  int get failedAttempts => _failedAttempts;

  /// Singleton instance
  static ParentalControlsService? _instance;
  static ParentalControlsService get instance =>
      _instance ??= ParentalControlsService._();

  ParentalControlsService._();

  /// Factory constructor for testing
  @visibleForTesting
  factory ParentalControlsService.forTesting() => ParentalControlsService._();

  // ------------------------------------------------------------------
  // Initialization
  // ------------------------------------------------------------------

  /// Load persisted settings from SharedPreferences.
  Future<void> initialize() async {
    await _load();
    logger.info(
      'Parental controls initialized (enabled=$_enabled, '
      'categories=${_blockedCategories.length}, min_age=$_minAge)',
    );
  }

  // ------------------------------------------------------------------
  // PIN management
  // ------------------------------------------------------------------

  /// Hash [pin] with SHA-256 and return hex digest.
  static String _hashPin(String pin) {
    final bytes = utf8.encode(pin);
    final digest = sha256.convert(bytes);
    return digest.toString();
  }

  /// Validate that [pin] is exactly 4 digits.
  static bool validatePinFormat(String pin) {
    return pin.length == 4 && RegExp(r'^\d{4}$').hasMatch(pin);
  }

  /// Set up a new PIN, enable parental controls, and persist.
  ///
  /// Throws [ArgumentError] if [pin] is not exactly 4 digits.
  Future<void> setupPin(String pin) async {
    if (!validatePinFormat(pin)) {
      throw ArgumentError('PIN must be exactly 4 digits');
    }
    _pinHash = _hashPin(pin);
    _enabled = true;
    await _save();
    notifyListeners();
    logger.info('Parental controls PIN set and controls enabled');
  }

  /// Verify [pin] against the stored hash.
  ///
  /// Returns `false` when locked out (even if PIN is correct).
  /// Resets the attempt counter on success.
  bool verifyPin(String pin) {
    if (isLockedOut) {
      final remaining = lockoutRemaining;
      logger.warning(
        'PIN verification blocked — lockout active (${remaining}s remaining)',
      );
      return false;
    }

    if (_pinHash == null) return false;

    if (_hashPin(pin) == _pinHash) {
      _failedAttempts = 0;
      _lockoutUntil = null;
      return true;
    }

    _failedAttempts++;
    logger.warning(
      'Invalid PIN attempt $_failedAttempts/$maxFailedAttempts',
    );

    if (_failedAttempts >= maxFailedAttempts) {
      _lockoutUntil = DateTime.now().add(
        const Duration(seconds: lockoutDurationSeconds),
      );
      logger.warning(
        'Max PIN attempts reached — lockout for ${lockoutDurationSeconds}s',
      );
    }

    notifyListeners();
    return false;
  }

  /// Verify [oldPin] then set [newPin]. Returns success status.
  ///
  /// Throws [ArgumentError] if [newPin] is not exactly 4 digits.
  Future<bool> changePin(String oldPin, String newPin) async {
    if (!verifyPin(oldPin)) return false;
    if (!validatePinFormat(newPin)) {
      throw ArgumentError('PIN must be exactly 4 digits');
    }
    _pinHash = _hashPin(newPin);
    await _save();
    notifyListeners();
    logger.info('Parental controls PIN changed');
    return true;
  }

  /// Whether too many wrong attempts have triggered a lockout.
  bool get isLockedOut {
    if (_failedAttempts >= maxFailedAttempts && _lockoutUntil != null) {
      if (DateTime.now().isBefore(_lockoutUntil!)) {
        return true;
      }
      // Auto-clear expired lockout
      _failedAttempts = 0;
      _lockoutUntil = null;
    }
    return false;
  }

  /// Seconds remaining on the current lockout (0 if not locked out).
  int get lockoutRemaining {
    if (isLockedOut && _lockoutUntil != null) {
      final remaining = _lockoutUntil!.difference(DateTime.now()).inSeconds;
      return remaining > 0 ? remaining : 0;
    }
    return 0;
  }

  // ------------------------------------------------------------------
  // Channel filtering
  // ------------------------------------------------------------------

  /// Return `true` if a channel should be hidden/blocked.
  ///
  /// A channel is blocked when **any** of the following apply
  /// (and parental controls are enabled):
  /// 1. Its category is in [blockedCategories] (case-insensitive).
  /// 2. Its minimum_age exceeds [minAge] (when minAge > 0).
  ///
  /// [channel] should be a Map with keys: 'category', 'minimum_age'.
  /// This also accepts the Channel model fields directly via named params.
  bool isChannelBlocked({
    String? category,
    int minimumAge = 0,
  }) {
    if (!_enabled) return false;

    // Category check (case-insensitive)
    if (_blockedCategories.isNotEmpty && category != null) {
      final cat = category.trim().toLowerCase();
      if (cat.isNotEmpty) {
        final blockedLower = _blockedCategories
            .map((c) => c.toLowerCase())
            .toSet();
        if (blockedLower.contains(cat)) {
          return true;
        }
      }
    }

    // Age-rating check
    if (_minAge > 0 && minimumAge > _minAge) {
      return true;
    }

    return false;
  }

  // ------------------------------------------------------------------
  // Settings management
  // ------------------------------------------------------------------

  /// Update the blocked categories list and persist.
  Future<void> setBlockedCategories(List<String> categories) async {
    _blockedCategories = List<String>.from(categories);
    await _save();
    notifyListeners();
    logger.info('Blocked categories updated: $_blockedCategories');
  }

  /// Set the minimum age threshold (clamped 0–18) and persist.
  Future<void> setMinAge(int age) async {
    _minAge = age.clamp(0, 18);
    await _save();
    notifyListeners();
    logger.info('Min age rating set to $_minAge');
  }

  /// Enable or disable parental controls (requires PIN to be set).
  Future<void> setEnabled(bool value) async {
    if (value && _pinHash == null) {
      throw StateError('Cannot enable parental controls without a PIN');
    }
    _enabled = value;
    await _save();
    notifyListeners();
    logger.info('Parental controls ${_enabled ? "enabled" : "disabled"}');
  }

  /// Reset all parental controls (requires valid PIN).
  Future<bool> reset(String pin) async {
    if (!verifyPin(pin)) return false;
    _enabled = false;
    _pinHash = null;
    _blockedCategories = [];
    _minAge = 0;
    _failedAttempts = 0;
    _lockoutUntil = null;
    await _save();
    notifyListeners();
    logger.info('Parental controls have been reset');
    return true;
  }

  // ------------------------------------------------------------------
  // Persistence
  // ------------------------------------------------------------------

  Future<void> _save() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_keyEnabled, _enabled);
      if (_pinHash != null) {
        await prefs.setString(_keyPinHash, _pinHash!);
      } else {
        await prefs.remove(_keyPinHash);
      }
      await prefs.setStringList(_keyBlockedCategories, _blockedCategories);
      await prefs.setInt(_keyMinAge, _minAge);
      logger.debug('Parental settings saved');
    } catch (e, stackTrace) {
      logger.error('Failed to save parental settings', e, stackTrace);
    }
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _enabled = prefs.getBool(_keyEnabled) ?? false;
      _pinHash = prefs.getString(_keyPinHash);
      _blockedCategories = prefs.getStringList(_keyBlockedCategories) ?? [];
      _minAge = prefs.getInt(_keyMinAge) ?? 0;
    } catch (e, stackTrace) {
      logger.error('Failed to load parental settings', e, stackTrace);
    }
  }
}
