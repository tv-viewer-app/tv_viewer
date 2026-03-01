import 'dart:async';
import 'package:flutter/foundation.dart';
import '../utils/logger_service.dart';

/// Crashlytics service that works with or without Firebase
/// 
/// When Firebase is not configured, falls back to logger_service.dart
/// This allows the app to function without Firebase setup
class CrashlyticsService {
  static CrashlyticsService? _instance;
  static CrashlyticsService get instance => _instance ??= CrashlyticsService._();
  
  CrashlyticsService._();
  
  bool _isInitialized = false;
  bool _firebaseAvailable = false;
  final LoggerService _logger = LoggerService.instance;
  
  // Firebase Crashlytics instance (will be null if Firebase not configured)
  // ignore: unused_field
  dynamic _crashlytics;
  
  /// Initialize Crashlytics service
  /// 
  /// Checks if Firebase is configured and available
  /// Falls back to logger if Firebase is not set up
  Future<void> initialize() async {
    if (_isInitialized) return;
    
    try {
      // Try to initialize Firebase Crashlytics
      // This will fail gracefully if Firebase is not configured
      _firebaseAvailable = await _initializeFirebase();
      
      if (_firebaseAvailable) {
        _logger.info('[Crashlytics] Firebase Crashlytics initialized successfully');
        
        // Set up Flutter error handler to catch framework errors
        _setupFlutterErrorHandler();
      } else {
        _logger.info('[Crashlytics] Running in fallback mode (no Firebase configured)');
        
        // Still set up basic error handler using logger
        _setupFallbackErrorHandler();
      }
      
      _isInitialized = true;
    } catch (e) {
      _logger.warning('[Crashlytics] Failed to initialize Firebase Crashlytics, using fallback mode', e);
      _firebaseAvailable = false;
      _setupFallbackErrorHandler();
      _isInitialized = true;
    }
  }
  
  /// Try to initialize Firebase Crashlytics
  /// Returns true if successful, false otherwise
  Future<bool> _initializeFirebase() async {
    try {
      // Check if Firebase core is available
      // This will be implemented when Firebase is set up
      // For now, return false to use fallback mode
      
      // Uncomment when Firebase is configured:
      // await Firebase.initializeApp();
      // _crashlytics = FirebaseCrashlytics.instance;
      // 
      // // Enable crash collection
      // await _crashlytics.setCrashlyticsCollectionEnabled(true);
      // 
      // return true;
      
      return false;
    } catch (e) {
      debugPrint('[Crashlytics] Firebase not available: $e');
      return false;
    }
  }
  
  /// Set up Flutter error handler for Firebase Crashlytics
  void _setupFlutterErrorHandler() {
    FlutterError.onError = (FlutterErrorDetails details) {
      // Log to Firebase Crashlytics
      recordFlutterError(details);
      
      // Also log to logger for local debugging
      _logger.error(
        '[Flutter Error] ${details.exception}',
        details.exception,
        details.stack,
      );
    };
    
    // Catch errors outside of Flutter framework
    PlatformDispatcher.instance.onError = (error, stack) {
      recordError(error, stack, fatal: true);
      return true;
    };
  }
  
  /// Set up fallback error handler using logger
  void _setupFallbackErrorHandler() {
    FlutterError.onError = (FlutterErrorDetails details) {
      _logger.error(
        '[Flutter Error] ${details.exception}',
        details.exception,
        details.stack,
      );
    };
    
    // Catch errors outside of Flutter framework
    PlatformDispatcher.instance.onError = (error, stack) {
      _logger.error(
        '[Platform Error] $error',
        error,
        stack,
      );
      return true;
    };
  }
  
  /// Record a non-fatal error
  /// 
  /// If Firebase is available, logs to Firebase Crashlytics
  /// Otherwise, logs to logger_service.dart
  Future<void> recordError(
    dynamic exception,
    StackTrace? stack, {
    String? reason,
    bool fatal = false,
    Iterable<Object> information = const [],
  }) async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _crashlytics != null) {
        // Log to Firebase Crashlytics
        // await _crashlytics.recordError(
        //   exception,
        //   stack,
        //   reason: reason,
        //   fatal: fatal,
        //   information: information,
        // );
        
        _logger.error(
          '[Crashlytics] ${fatal ? 'FATAL' : 'Error'}: ${reason ?? exception.toString()}',
          exception,
          stack,
        );
      } else {
        // Fallback: Log to logger service
        final fatalLabel = fatal ? 'FATAL ' : '';
        final reasonText = reason != null ? '$reason: ' : '';
        _logger.error(
          '[Crashlytics Fallback] $fatalLabel${reasonText}$exception',
          exception,
          stack,
        );
        
        // Log additional information
        if (information.isNotEmpty) {
          _logger.info('[Crashlytics] Additional info: ${information.join(', ')}');
        }
      }
    } catch (e) {
      _logger.warning('[Crashlytics] Failed to record error', e);
    }
  }
  
  /// Record a Flutter error
  Future<void> recordFlutterError(FlutterErrorDetails details) async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _crashlytics != null) {
        // Log to Firebase Crashlytics
        // await _crashlytics.recordFlutterError(details);
        
        _logger.error(
          '[Flutter Error] ${details.exception}',
          details.exception,
          details.stack,
        );
      } else {
        // Fallback: Log to logger service
        _logger.error(
          '[Flutter Error] ${details.exception}',
          details.exception,
          details.stack,
        );
        
        if (details.context != null) {
          _logger.info('[Flutter Error Context] ${details.context}');
        }
      }
    } catch (e) {
      _logger.warning('[Crashlytics] Failed to record Flutter error', e);
    }
  }
  
  /// Set custom key-value pair for crash reports
  /// 
  /// Useful for adding context to crashes
  Future<void> setCustomKey(String key, dynamic value) async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _crashlytics != null) {
        // Set Firebase custom key
        // await _crashlytics.setCustomKey(key, value);
        _logger.debug('[Crashlytics] Custom key: $key = $value');
      } else {
        // Fallback: Log to logger service
        _logger.debug('[Crashlytics] Custom key: $key = $value');
      }
    } catch (e) {
      _logger.warning('[Crashlytics] Failed to set custom key: $key', e);
    }
  }
  
  /// Set user identifier for crash reports
  Future<void> setUserIdentifier(String identifier) async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _crashlytics != null) {
        // Set Firebase user identifier
        // await _crashlytics.setUserIdentifier(identifier);
        _logger.debug('[Crashlytics] User identifier set: $identifier');
      } else {
        // Fallback: Log to logger service
        _logger.info('[Crashlytics] User identifier: $identifier');
      }
    } catch (e) {
      _logger.warning('[Crashlytics] Failed to set user identifier', e);
    }
  }
  
  /// Log a message to crash reports
  Future<void> log(String message) async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _crashlytics != null) {
        // Log to Firebase Crashlytics
        // await _crashlytics.log(message);
        _logger.debug('[Crashlytics] $message');
      } else {
        // Fallback: Log to logger service
        _logger.info('[Crashlytics] $message');
      }
    } catch (e) {
      _logger.warning('[Crashlytics] Failed to log message', e);
    }
  }
  
  /// Enable or disable crash collection
  Future<void> setCrashlyticsCollectionEnabled(bool enabled) async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _crashlytics != null) {
        // Set Firebase crash collection
        // await _crashlytics.setCrashlyticsCollectionEnabled(enabled);
        _logger.info('[Crashlytics] Collection ${enabled ? 'enabled' : 'disabled'}');
      } else {
        // Fallback: Log to logger service
        _logger.info('[Crashlytics] Collection ${enabled ? 'enabled' : 'disabled'} (fallback mode)');
      }
    } catch (e) {
      _logger.warning('[Crashlytics] Failed to set collection enabled state', e);
    }
  }
  
  /// Check for unsent crash reports
  Future<bool> checkForUnsentReports() async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _crashlytics != null) {
        // Check Firebase for unsent reports
        // return await _crashlytics.checkForUnsentReports();
        return false;
      } else {
        // Fallback: Always return false
        return false;
      }
    } catch (e) {
      _logger.warning('[Crashlytics] Failed to check for unsent reports', e);
      return false;
    }
  }
  
  /// Send unsent crash reports
  Future<void> sendUnsentReports() async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _crashlytics != null) {
        // Send Firebase unsent reports
        // await _crashlytics.sendUnsentReports();
        _logger.info('[Crashlytics] Sent unsent reports');
      } else {
        // Fallback: No-op
        _logger.debug('[Crashlytics] No unsent reports (fallback mode)');
      }
    } catch (e) {
      _logger.warning('[Crashlytics] Failed to send unsent reports', e);
    }
  }
  
  /// Delete unsent crash reports
  Future<void> deleteUnsentReports() async {
    if (!_isInitialized) {
      await initialize();
    }
    
    try {
      if (_firebaseAvailable && _crashlytics != null) {
        // Delete Firebase unsent reports
        // await _crashlytics.deleteUnsentReports();
        _logger.info('[Crashlytics] Deleted unsent reports');
      } else {
        // Fallback: No-op
        _logger.debug('[Crashlytics] No unsent reports to delete (fallback mode)');
      }
    } catch (e) {
      _logger.warning('[Crashlytics] Failed to delete unsent reports', e);
    }
  }
  
  /// Test crash (for testing purposes only)
  /// 
  /// DO NOT USE IN PRODUCTION CODE
  @visibleForTesting
  Future<void> crash() async {
    if (!_isInitialized) {
      await initialize();
    }
    
    _logger.warning('[Crashlytics] Test crash triggered!');
    
    if (_firebaseAvailable && _crashlytics != null) {
      // Trigger Firebase test crash
      // _crashlytics.crash();
      throw Exception('Test crash from Crashlytics');
    } else {
      // Fallback: Just throw an exception
      throw Exception('Test crash (fallback mode)');
    }
  }
  
  /// Check if Firebase is available
  bool get isFirebaseAvailable => _firebaseAvailable;
  
  /// Check if Crashlytics is initialized
  bool get isInitialized => _isInitialized;
}

/// Global crashlytics instance (convenience)
final crashlytics = CrashlyticsService.instance;
