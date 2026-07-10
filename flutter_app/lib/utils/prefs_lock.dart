import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Simple mutex to serialize SharedPreferences writes and prevent SQLITE_BUSY.
class PrefsLock {
  static final PrefsLock instance = PrefsLock._();
  PrefsLock._();

  Completer<void>? _lock;

  Future<T> synchronized<T>(Future<T> Function() action) async {
    while (_lock != null) {
      await _lock!.future;
    }
    _lock = Completer<void>();
    try {
      return await action();
    } finally {
      final l = _lock;
      _lock = null;
      l?.complete();
    }
  }

  static bool isClosingError(Object error) {
    final message = error.toString().toLowerCase();
    return message.contains('database_closed') ||
        message.contains('database closed') ||
        message.contains('database is closed');
  }

  Future<void> guardWrite(
    Future<void> Function() action, {
    String operation = 'prefs write',
  }) async {
    try {
      await synchronized(action);
    } catch (error) {
      if (isClosingError(error)) {
        debugPrint('Prefs write ignored (app closing) during $operation: $error');
        return;
      }
      rethrow;
    }
  }
}

extension SafeSharedPreferencesWrites on SharedPreferences {
  Future<bool> safeSetString(String key, String value) async {
    var success = false;
    await PrefsLock.instance.guardWrite(() async {
      success = await setString(key, value);
    }, operation: 'setString($key)');
    return success;
  }

  Future<bool> safeSetBool(String key, bool value) async {
    var success = false;
    await PrefsLock.instance.guardWrite(() async {
      success = await setBool(key, value);
    }, operation: 'setBool($key)');
    return success;
  }

  Future<bool> safeSetInt(String key, int value) async {
    var success = false;
    await PrefsLock.instance.guardWrite(() async {
      success = await setInt(key, value);
    }, operation: 'setInt($key)');
    return success;
  }

  Future<bool> safeSetDouble(String key, double value) async {
    var success = false;
    await PrefsLock.instance.guardWrite(() async {
      success = await setDouble(key, value);
    }, operation: 'setDouble($key)');
    return success;
  }

  Future<bool> safeSetStringList(String key, List<String> value) async {
    var success = false;
    await PrefsLock.instance.guardWrite(() async {
      success = await setStringList(key, value);
    }, operation: 'setStringList($key)');
    return success;
  }

  Future<bool> safeRemove(String key) async {
    var success = false;
    await PrefsLock.instance.guardWrite(() async {
      success = await remove(key);
    }, operation: 'remove($key)');
    return success;
  }

  Future<bool> safeClear() async {
    var success = false;
    await PrefsLock.instance.guardWrite(() async {
      success = await clear();
    }, operation: 'clear()');
    return success;
  }
}
