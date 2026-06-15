import 'dart:async';

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
}
