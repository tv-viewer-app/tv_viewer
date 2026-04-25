import 'dart:io';
import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:tv_viewer/utils/error_handler.dart';
import 'package:tv_viewer/utils/logger_service.dart';

/// Example usage and tests for error handling system
/// 
/// This file demonstrates how to use the error handling and logging system
/// in the TV Viewer app. Run with: flutter test test/error_handling_examples_test.dart

void main() {
  group('ErrorHandler Examples', () {
    test('Handle SocketException - No Internet', () {
      final exception = SocketException('Network is unreachable');
      final appError = ErrorHandler.handle(exception);
      
      print('=== SocketException Example ===');
      print('Code: ${appError.code}');
      print('User Message: ${appError.userMessage}');
      print('Recovery: ${appError.recoverySuggestion}');
      print('');
      
      expect(appError.code, equals(ErrorCode.noInternet));
      expect(appError.userMessage, contains('Network'));
      expect(appError.recoverySuggestion, contains('WiFi'));
    });
    
    test('Handle TimeoutException', () {
      final exception = TimeoutException('Operation timeout', const Duration(seconds: 30));
      final appError = ErrorHandler.handle(exception);
      
      print('=== TimeoutException Example ===');
      print('Code: ${appError.code}');
      print('User Message: ${appError.userMessage}');
      print('Recovery: ${appError.recoverySuggestion}');
      print('');
      
      expect(appError.code, equals(ErrorCode.timeout));
      expect(appError.userMessage, contains('timed out'));
    });
    
    test('Handle FormatException', () {
      final exception = FormatException('Invalid M3U format');
      final appError = ErrorHandler.handle(exception);
      
      print('=== FormatException Example ===');
      print('Code: ${appError.code}');
      print('User Message: ${appError.userMessage}');
      print('Recovery: ${appError.recoverySuggestion}');
      print('');
      
      expect(appError.code, equals(ErrorCode.m3uInvalid));
      expect(appError.userMessage, contains('format'));
    });
    
    test('Handle HTTP Status Codes', () {
      final errors = [
        ErrorHandler.handleHttpStatusCode(404, 'https://example.com/playlist.m3u'),
        ErrorHandler.handleHttpStatusCode(401, 'https://example.com/stream'),
        ErrorHandler.handleHttpStatusCode(500, 'https://example.com/api'),
      ];
      
      print('=== HTTP Status Code Examples ===');
      for (final error in errors) {
        print('Code: ${error.code} - ${error.userMessage}');
      }
      print('');
      
      expect(errors[0].code, equals(ErrorCode.notFound));
      expect(errors[1].code, equals(ErrorCode.unauthorized));
      expect(errors[2].code, equals(ErrorCode.serverError));
    });
    
    test('Create custom M3U errors', () {
      final errors = [
        ErrorHandler.m3uError('empty', 'Playlist has no content'),
        ErrorHandler.m3uError('invalid', 'Not a valid M3U file'),
        ErrorHandler.m3uError('no_channels', 'All channels are offline'),
      ];
      
      print('=== Custom M3U Error Examples ===');
      for (final error in errors) {
        print('${error.code}: ${error.userMessage}');
        print('  → ${error.recoverySuggestion.split('\n').first}');
      }
      print('');
      
      expect(errors[0].code, equals(ErrorCode.m3uEmpty));
      expect(errors[1].code, equals(ErrorCode.m3uInvalid));
      expect(errors[2].code, equals(ErrorCode.m3uNoChannels));
    });
    
    test('Create custom stream errors', () {
      final errors = [
        ErrorHandler.streamError('not_available', 'Channel is offline'),
        ErrorHandler.streamError('timeout', 'Stream took too long'),
        ErrorHandler.streamError('format', 'Codec not supported'),
      ];
      
      print('=== Custom Stream Error Examples ===');
      for (final error in errors) {
        print('${error.code}: ${error.userMessage}');
      }
      print('');
      
      expect(errors[0].code, equals(ErrorCode.streamNotAvailable));
      expect(errors[1].code, equals(ErrorCode.streamTimeout));
      expect(errors[2].code, equals(ErrorCode.streamFormatUnsupported));
    });
  });
  
  group('Usage Examples', () {
    test('Example 1: Try-catch with error handling', () {
      print('=== Example 1: Basic Error Handling ===');
      print('''
try {
  await fetchM3UPlaylist(url);
} catch (e, stackTrace) {
  final appError = ErrorHandler.handle(e, stackTrace);
  logger.error('Failed to fetch playlist', e, stackTrace);
  
  // Show to user
  showSnackBar(appError.userMessage);
  
  // Display recovery suggestion
  showDialog(appError.recoverySuggestion);
}
''');
    });
    
    test('Example 2: Display error in UI', () {
      print('=== Example 2: UI Error Display ===');
      print('''
if (_error != null) {
  return Column(
    children: [
      Icon(Icons.error_outline, size: 64, color: Colors.red),
      Text(_error!.userMessage, style: TextStyle(fontSize: 18)),
      Container(
        padding: EdgeInsets.all(16),
        child: Text(_error!.recoverySuggestion),
      ),
      Text('Error Code: \${_error!.code}', style: TextStyle(fontSize: 11)),
      ElevatedButton(
        onPressed: () => retry(),
        child: Text('Retry'),
      ),
    ],
  );
}
''');
    });
    
    test('Example 3: Logging different levels', () {
      print('=== Example 3: Logging ===');
      print('''
// Debug information
logger.debug('Parsing M3U: \${content.length} bytes');

// Info messages
logger.info('User opened channel: \${channel.name}');

// Warnings
logger.warning('Stream quality degraded', exception);

// Errors (with stack trace)
logger.error('Playback failed', exception, stackTrace);
''');
    });
    
    test('Example 4: Custom error creation', () {
      print('=== Example 4: Custom Errors ===');
      print('''
// M3U errors
if (channels.isEmpty) {
  throw ErrorHandler.m3uError('empty', 'No channels in playlist');
}

// Stream errors
if (!streamAvailable) {
  throw ErrorHandler.streamError('not_available', 'Channel offline');
}

// HTTP errors
if (response.statusCode != 200) {
  throw ErrorHandler.handleHttpStatusCode(response.statusCode, url);
}
''');
    });
    
    test('Example 5: Log management', () {
      print('=== Example 5: Log Management ===');
      print('''
// Get log statistics
final size = await logger.getFormattedLogSize(); // "2.45 MB"
final files = await logger.getAllLogFiles();     // List<File>

// Export logs
final exportFile = await logger.exportLogs();
if (exportFile != null) {
  Share.shareFiles([exportFile.path]);
}

// Clear old logs
await logger.clearLogs();

// Change log level
logger.setMinLogLevel(LogLevel.warning); // Only warnings and errors
''');
    });
  });
  
  group('Error Code Reference', () {
    test('Print all error codes', () {
      print('=== Error Code Reference ===');
      print('');
      print('Network Errors:');
      print('  ERR_NET_001 - No Internet Connection');
      print('  ERR_NET_002 - Connection Timeout');
      print('  ERR_NET_003 - Server Error');
      print('  ERR_NET_004 - Content Not Found (404)');
      print('  ERR_NET_005 - Unauthorized (401)');
      print('  ERR_NET_006 - Forbidden (403)');
      print('  ERR_NET_007 - Connection Refused');
      print('');
      print('Stream Errors:');
      print('  ERR_STREAM_001 - Stream Not Available');
      print('  ERR_STREAM_002 - Stream Timeout');
      print('  ERR_STREAM_003 - Format Unsupported');
      print('  ERR_STREAM_004 - Initialization Failed');
      print('  ERR_STREAM_005 - Playback Error');
      print('  ERR_STREAM_006 - Codec Error');
      print('');
      print('M3U/Playlist Errors:');
      print('  ERR_M3U_001 - Invalid Format');
      print('  ERR_M3U_002 - Empty Playlist');
      print('  ERR_M3U_003 - Parse Failed');
      print('  ERR_M3U_004 - No Valid Channels');
      print('');
      print('Storage Errors:');
      print('  ERR_STORAGE_001 - Storage Access Failed');
      print('  ERR_STORAGE_002 - Cache Read Failed');
      print('  ERR_STORAGE_003 - Cache Write Failed');
      print('');
      print('General Errors:');
      print('  ERR_GEN_001 - Unknown Error');
      print('  ERR_GEN_002 - Invalid Input');
      print('  ERR_GEN_003 - Permission Denied');
      print('');
    });
  });
  
  group('Best Practices', () {
    test('Best Practice 1: Always catch with stackTrace', () {
      print('=== Best Practice 1 ===');
      print('✅ Good:');
      print('try { ... } catch (e, stackTrace) { ... }');
      print('');
      print('❌ Bad:');
      print('try { ... } catch (e) { ... }');
      print('');
    });
    
    test('Best Practice 2: Use ErrorHandler for all errors', () {
      print('=== Best Practice 2 ===');
      print('✅ Good:');
      print('final error = ErrorHandler.handle(e, stackTrace);');
      print('');
      print('❌ Bad:');
      print('final error = e.toString();');
      print('');
    });
    
    test('Best Practice 3: Log before showing to user', () {
      print('=== Best Practice 3 ===');
      print('✅ Good:');
      print('''
catch (e, stackTrace) {
  final error = ErrorHandler.handle(e, stackTrace);
  logger.error('Operation failed', e, stackTrace);
  setState(() => _error = error);
}
''');
      print('');
    });
    
    test('Best Practice 4: Display recovery suggestions', () {
      print('=== Best Practice 4 ===');
      print('Always show users what they can do:');
      print('  • User message (what went wrong)');
      print('  • Recovery suggestion (how to fix it)');
      print('  • Error code (for support)');
      print('  • Action buttons (Retry, External Player, etc.)');
      print('');
    });
  });
}

/// Example: How to use in a real service
class ExampleM3UService {
  static Future<List<String>> fetchPlaylist(String url) async {
    try {
      // This might throw SocketException, TimeoutException, etc.
      final response = await HttpClient()
          .getUrl(Uri.parse(url))
          .timeout(const Duration(seconds: 30));
      
      // Handle HTTP errors
      final statusCode = 200; // example
      if (statusCode != 200) {
        throw ErrorHandler.handleHttpStatusCode(statusCode, url);
      }
      
      // Parse and validate
      final content = 'parsed content'; // example
      if (content.isEmpty) {
        throw ErrorHandler.m3uError('empty', 'Playlist is empty');
      }
      
      return ['channel1', 'channel2'];
      
    } catch (e, stackTrace) {
      final error = ErrorHandler.handle(e, stackTrace);
      logger.error('Failed to fetch playlist from $url', e, stackTrace);
      throw error; // Rethrow as AppError
    }
  }
}

/// Example: How to use in a widget
class ExamplePlayerWidget {
  // ignore: unused_field
  AppError? _error;
  
  Future<void> initializePlayer(String url) async {
    try {
      // Initialize video player
      final controller = null; // VideoPlayerController example
      await controller?.initialize().timeout(
        const Duration(seconds: 30),
        onTimeout: () {
          throw ErrorHandler.streamError('timeout', 'Stream timeout after 30s');
        },
      );
      
      logger.info('Player initialized successfully');
      
    } catch (e, stackTrace) {
      final error = ErrorHandler.handle(e, stackTrace);
      logger.error('Player initialization failed', e, stackTrace);
      
      _error = error;
      // Show error in UI
    }
  }
}
