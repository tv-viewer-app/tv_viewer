# Error Handling & Logging System

This document describes the comprehensive error handling and logging system implemented in the TV Viewer Flutter app.

## Overview

The system provides:
- **User-friendly error messages** - No more cryptic technical errors shown to users
- **Categorized error codes** - Easy identification and tracking of error types
- **Recovery suggestions** - Helpful guidance on how to fix issues
- **Persistent file logging** - All errors and events are logged to disk
- **Log rotation** - Automatic management of log files (max 5 files, 1MB each)
- **Export functionality** - Users can export logs for troubleshooting

---

## Components

### 1. Error Handler (`lib/utils/error_handler.dart`)

#### Error Codes

Errors are categorized with codes for easy identification:

| Category | Code Pattern | Examples |
|----------|--------------|----------|
| Network | `ERR_NET_xxx` | ERR_NET_001 (No Internet), ERR_NET_002 (Timeout) |
| Stream | `ERR_STREAM_xxx` | ERR_STREAM_001 (Not Available), ERR_STREAM_003 (Format Unsupported) |
| M3U/Playlist | `ERR_M3U_xxx` | ERR_M3U_001 (Invalid), ERR_M3U_004 (No Channels) |
| Storage | `ERR_STORAGE_xxx` | ERR_STORAGE_001 (Failed), ERR_STORAGE_002 (Cache Read Failed) |
| General | `ERR_GEN_xxx` | ERR_GEN_001 (Unknown), ERR_GEN_002 (Invalid Input) |

#### AppError Class

```dart
class AppError {
  final String code;              // e.g., "ERR_NET_001"
  final String userMessage;       // User-friendly message
  final String technicalDetails;  // Technical details for debugging
  final String recoverySuggestion; // How to fix the issue
  final Exception? originalException;
  final StackTrace? stackTrace;
}
```

#### Usage Examples

**Basic Error Handling:**
```dart
import 'package:tv_viewer/utils/error_handler.dart';
import 'package:tv_viewer/utils/logger_service.dart';

try {
  // Your code that might fail
  await someRiskyOperation();
} catch (e, stackTrace) {
  final appError = ErrorHandler.handle(e, stackTrace);
  
  // Log the error
  logger.error('Operation failed', e, stackTrace);
  
  // Show user-friendly message
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text(appError.userMessage)),
  );
  
  // Display recovery suggestion
  print(appError.recoverySuggestion);
}
```

**Custom Error Creation:**
```dart
// M3U errors
throw ErrorHandler.m3uError('empty', 'Playlist contains no channels');

// Stream errors
throw ErrorHandler.streamError('timeout', 'Stream took too long to load');

// Storage errors
throw ErrorHandler.storageError('read', 'Cannot read cache file');

// HTTP status code errors
throw ErrorHandler.handleHttpStatusCode(404, 'https://example.com/playlist.m3u');
```

#### Exception Mappings

The system automatically maps common Flutter/Dart exceptions to user-friendly messages:

| Exception Type | User Message | Recovery Suggestion |
|----------------|--------------|---------------------|
| `SocketException` | "Network connection problem" | Check WiFi/mobile data, restart router |
| `TimeoutException` | "Connection timed out" | Check internet speed, try again later |
| `FormatException` | "Invalid data format" | Verify M3U URL, try different source |
| `HttpException` | "Server communication error" | Server issue, try again later |
| `FileSystemException` | "Storage access failed" | Check storage space, verify permissions |
| `VideoPlayerPlatformException` | "Stream playback error" | Try different stream, check codec support |

---

### 2. Logger Service (`lib/utils/logger_service.dart`)

#### Features

- **Persistent file logging** - Logs written to disk, not just console
- **Log levels** - debug, info, warning, error
- **Automatic rotation** - Keeps last 5 log files, max 1MB each
- **Buffered writes** - Efficient batching of log entries
- **Export functionality** - Combine all logs into single file
- **Size management** - Track and report total log size

#### Log Levels

```dart
enum LogLevel {
  debug,   // Detailed diagnostic information (lowest priority)
  info,    // General informational messages
  warning, // Warning messages (potential issues)
  error,   // Error messages (highest priority)
}
```

#### Initialization

In `main.dart`:
```dart
import 'package:tv_viewer/utils/logger_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize logger (production: LogLevel.info, debug: LogLevel.debug)
  await logger.initialize(minLogLevel: LogLevel.info);
  
  runApp(const TVViewerApp());
}
```

#### Usage Examples

**Basic Logging:**
```dart
import 'package:tv_viewer/utils/logger_service.dart';

// Debug messages (only in debug builds)
logger.debug('Detailed debug information');

// Info messages
logger.info('User opened player screen');

// Warning messages
logger.warning('Stream quality degraded', exception);

// Error messages (includes stack trace)
logger.error('Failed to load playlist', exception, stackTrace);
```

**Log Management:**
```dart
// Get all log files
final logFiles = await logger.getAllLogFiles();
print('Found ${logFiles.length} log files');

// Get total log size
final sizeString = await logger.getFormattedLogSize(); // "2.45 MB"
print('Total logs: $sizeString');

// Export all logs to single file
final exportFile = await logger.exportLogs();
if (exportFile != null) {
  print('Logs exported to: ${exportFile.path}');
}

// Get logs as string (for display in UI)
final logsText = await logger.getLogsAsString(maxLines: 100);

// Clear all logs
await logger.clearLogs();

// Change log level at runtime
logger.setMinLogLevel(LogLevel.warning); // Only log warnings and errors
```

#### Log File Format

```
============================================================
Log started: 2025-06-15 14:32:05.123
App: TV Viewer
============================================================

[2025-06-15 14:32:05.456] [INFO] Logger service initialized

[2025-06-15 14:32:06.789] [INFO] TV Viewer app starting...

[2025-06-15 14:32:10.234] [ERROR] Player initialization failed for BBC News
Error: SocketException: Network is unreachable
Stack trace:
#0      _rootRun (dart:async/zone.dart:1418:13)
...
```

#### Log Storage

Logs are stored in:
- **Android**: `/data/data/com.example.tv_viewer/app_flutter/logs/`
- **iOS**: `<Application Documents>/logs/`

Files are named: `app_log_YYYYMMDD_HHMMSS.txt`

---

## Implementation Details

### Player Screen Error Handling

The player screen now:
1. Shows **user-friendly error messages** instead of raw exceptions
2. Displays **recovery suggestions** in a formatted box
3. Provides **error code** for support purposes
4. Offers **Retry** and **External Player** options
5. Adds **30-second timeout** for stream initialization
6. Logs all errors with full context

**Before:**
```
Could not load stream
Exception: SocketException: Network is unreachable
```

**After:**
```
┌─────────────────────────────────────┐
│ Network connection problem          │
├─────────────────────────────────────┤
│ What to do:                         │
│ • Check WiFi or mobile data         │
│ • Try restarting your router        │
│ • Check if other apps can connect   │
└─────────────────────────────────────┘
Error Code: ERR_NET_001

[Retry]  [External Player]
```

### M3U Service Error Handling

The M3U service now:
1. Validates response before parsing
2. Handles HTTP status codes properly
3. Provides specific errors for empty/invalid playlists
4. Continues fetching from other repos if one fails
5. Logs detailed information about each fetch operation
6. Throws meaningful errors instead of returning empty lists

### Benefits

#### For Users
- **Clear error messages** - Understand what went wrong
- **Actionable suggestions** - Know how to fix the issue
- **Better support** - Can share error codes with developers

#### For Developers
- **Detailed logs** - Complete diagnostic information
- **Error tracking** - Categorized error codes for analytics
- **Debugging** - Full stack traces and context
- **Production debugging** - Users can export logs for support

---

## Error Handling Best Practices

### 1. Always Use ErrorHandler

```dart
// ✅ Good
try {
  await riskyOperation();
} catch (e, stackTrace) {
  final error = ErrorHandler.handle(e, stackTrace);
  logger.error('Operation failed', e, stackTrace);
  setState(() => _error = error);
}

// ❌ Bad
try {
  await riskyOperation();
} catch (e) {
  setState(() => _error = e.toString());
}
```

### 2. Log All Significant Events

```dart
// Log user actions
logger.info('User opened channel: ${channel.name}');

// Log state changes
logger.debug('Player state changed: playing=$isPlaying');

// Log warnings
logger.warning('Stream quality degraded', exception);

// Log errors with stack traces
logger.error('Failed operation', exception, stackTrace);
```

### 3. Use Appropriate Error Types

```dart
// Network operations
if (statusCode != 200) {
  throw ErrorHandler.handleHttpStatusCode(statusCode, url);
}

// M3U parsing
if (channels.isEmpty) {
  throw ErrorHandler.m3uError('no_channels', 'Playlist is empty');
}

// Stream operations
if (!streamAvailable) {
  throw ErrorHandler.streamError('not_available', 'Stream offline');
}
```

### 4. Display Recovery Suggestions

```dart
// Show user-friendly error with suggestions
if (_error != null) {
  return Column(
    children: [
      Text(_error!.userMessage),
      Text(_error!.recoverySuggestion),
      ElevatedButton(
        onPressed: retry,
        child: Text('Retry'),
      ),
    ],
  );
}
```

---

## Testing Error Handling

### Simulating Errors

```dart
// Test network errors
throw SocketException('Network unreachable');

// Test timeout errors
throw TimeoutException('Operation timeout');

// Test format errors
throw FormatException('Invalid JSON');

// Test custom errors
throw ErrorHandler.streamError('timeout', 'Test timeout');
```

### Verifying Logs

```dart
// Check logs were written
final logs = await logger.getLogsAsString();
expect(logs, contains('ERROR'));

// Verify error handling
try {
  throw SocketException('Test');
} catch (e) {
  final error = ErrorHandler.handle(e);
  expect(error.code, equals(ErrorCode.noInternet));
  expect(error.userMessage, contains('Network'));
}
```

---

## Future Enhancements

### Planned Features

1. **Error Analytics** - Track error frequency and types
2. **Crash Reporting** - Automatic crash report generation
3. **Remote Logging** - Optional upload to server for diagnosis
4. **Error Recovery** - Automatic retry with exponential backoff
5. **User Feedback** - Allow users to report errors in-app
6. **Error Dashboard** - Visual display of error statistics

### Configuration

Future config options in `main.dart`:
```dart
await logger.initialize(
  minLogLevel: LogLevel.info,
  maxLogFiles: 10,
  maxLogSizeBytes: 2 * 1024 * 1024, // 2MB
  enableRemoteLogging: false,
  enableCrashReporting: true,
);
```

---

## Troubleshooting

### Common Issues

**Problem:** Logs not being written
- **Solution:** Ensure logger is initialized in `main()`
- **Check:** Verify app has storage permissions

**Problem:** Log files too large
- **Solution:** Reduce `maxLogFiles` or `maxLogSizeBytes`
- **Check:** Call `logger.clearLogs()` periodically

**Problem:** Errors not caught properly
- **Solution:** Always use try-catch with `ErrorHandler.handle()`
- **Check:** Ensure error is rethrown after logging

### Debug Commands

```dart
// Enable debug logging
logger.setMinLogLevel(LogLevel.debug);

// Check log configuration
print('Log files: ${await logger.getAllLogFiles().length}');
print('Log size: ${await logger.getFormattedLogSize()}');

// Export logs for inspection
final file = await logger.exportLogs();
```

---

## Dependencies

Required packages (already in `pubspec.yaml`):
- `path_provider: ^2.1.2` - For log file storage
- `intl: ^0.19.0` - For timestamp formatting
- `http: ^1.2.0` - For network error handling
- `video_player: ^2.8.2` - For player error handling

---

## Support

For issues or questions about error handling:
1. Check logs: `await logger.exportLogs()`
2. Look for error codes in logs
3. Refer to error code table above
4. Report with error code and logs

---

## Version History

- **1.5.0** - Initial implementation
  - Error handler with categorized error codes
  - Persistent file logging with rotation
  - User-friendly error messages
  - Recovery suggestions
  - Export functionality
