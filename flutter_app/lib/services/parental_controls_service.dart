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
  static const String _keyIsOver18 = 'user_is_over_18';

  /// Legacy key – used only for backward-compatible migration.
  static const String _legacyKeyMinAge = 'parental_min_age';

  // Lockout configuration
  static const int maxFailedAttempts = 3;
  static const int lockoutDurationSeconds = 30;

  // State
  bool _enabled = false;
  String? _pinHash;
  List<String> _blockedCategories = [];
  bool _isOver18 = false;

  // Lockout state (persisted to SharedPreferences)
  int _failedAttempts = 0;
  DateTime? _lockoutUntil;

  // Getters
  bool get enabled => _enabled;
  bool get hasPin => _pinHash != null;
  List<String> get blockedCategories => List.unmodifiable(_blockedCategories);
  bool get isOver18 => _isOver18;
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
      'categories=${_blockedCategories.length}, isOver18=$_isOver18)',
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
      _save(); // Persist lockout state
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

  /// Category names that indicate adult/NSFW content.
  static const _adultCategories = {
    'Xxx', 'XXX', 'xxx', 'Adult', 'adult', 'NSFW', 'nsfw',
  };

  /// Return `true` if a channel should be hidden/blocked.
  ///
  /// A channel is blocked when **any** of the following apply
  /// (and parental controls are enabled):
  /// 1. Its category is in [blockedCategories] (case-insensitive).
  /// 2. The user is NOT over 18 and the channel has an adult-flagged category.
  ///
  /// [category] is the channel's group/category string.
  bool isChannelBlocked({
    String? category,
    // Kept for API compatibility; no longer used for filtering.
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

    // Adult-content check: block adult categories when user is not over 18
    if (!_isOver18 && category != null) {
      if (_adultCategories.contains(category.trim())) {
        return true;
      }
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

  /// Set whether the user is 18 or older, persist, and notify listeners.
  Future<void> setOver18(bool value) async {
    _isOver18 = value;
    await _save();
    notifyListeners();
    logger.info('User over-18 flag set to $_isOver18');
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
    _isOver18 = false;
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
      await prefs.setBool(_keyIsOver18, _isOver18);
      // Persist lockout state
      await prefs.setInt('parental_failed_attempts', _failedAttempts);
      if (_lockoutUntil != null) {
        await prefs.setInt('parental_lockout_until', _lockoutUntil!.millisecondsSinceEpoch);
      } else {
        await prefs.remove('parental_lockout_until');
      }
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

      // Load new boolean key; fall back to legacy int key for migration.
      if (prefs.containsKey(_keyIsOver18)) {
        _isOver18 = prefs.getBool(_keyIsOver18) ?? false;
      } else if (prefs.containsKey(_legacyKeyMinAge)) {
        // Backward compatibility: old parental_min_age == 18 → over 18.
        _isOver18 = (prefs.getInt(_legacyKeyMinAge) ?? 0) >= 18;
        // Persist as new key so next load is clean.
        await prefs.setBool(_keyIsOver18, _isOver18);
        await prefs.remove(_legacyKeyMinAge);
      } else {
        _isOver18 = false;
      }

      // Restore lockout state
      _failedAttempts = prefs.getInt('parental_failed_attempts') ?? 0;
      final lockoutMs = prefs.getInt('parental_lockout_until');
      if (lockoutMs != null) {
        _lockoutUntil = DateTime.fromMillisecondsSinceEpoch(lockoutMs);
        // Clear expired lockout
        if (DateTime.now().isAfter(_lockoutUntil!)) {
          _failedAttempts = 0;
          _lockoutUntil = null;
        }
      }
    } catch (e, stackTrace) {
      logger.error('Failed to load parental settings', e, stackTrace);
    }
  }
}
