import 'dart:io';
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:intl/intl.dart';

/// Log levels for filtering and categorizing log messages
enum LogLevel {
  debug(0, 'DEBUG'),
  info(1, 'INFO'),
  warning(2, 'WARNING'),
  error(3, 'ERROR');

  final int value;
  final String label;
  const LogLevel(this.value, this.label);
}

/// Persistent file-based logging service with rotation
class LoggerService {
  static LoggerService? _instance;
  static LoggerService get instance => _instance ??= LoggerService._();
  
  LoggerService._();
  
  /// Configuration
  static const int maxLogFiles = 5;
  static const int maxLogSizeBytes = 1024 * 1024; // 1MB
  static const String logFilePrefix = 'app_log';
  static const String logFileExtension = '.txt';
  
  /// Current log level filter (logs below this level will not be written)
  LogLevel _minLogLevel = LogLevel.debug;
  
  /// Current log file
  File? _currentLogFile;
  int _currentLogSize = 0;
  
  /// Buffer for pending log writes
  final List<String> _logBuffer = [];
  Timer? _flushTimer;
  bool _isInitialized = false;
  
  /// Date formatter for log entries
  final DateFormat _timestampFormat = DateFormat('yyyy-MM-dd HH:mm:ss.SSS');
  final DateFormat _fileTimestampFormat = DateFormat('yyyyMMdd_HHmmss');
  
  /// Initialize the logger service
  Future<void> initialize({LogLevel minLogLevel = LogLevel.debug}) async {
    if (_isInitialized) return;
    
    _minLogLevel = minLogLevel;
    
    try {
      await _initializeLogFile();
      _isInitialized = true;
      
      // Schedule periodic flush
      _flushTimer = Timer.periodic(
        const Duration(seconds: 5),
        (_) => _flushLogs(),
      );
      
      info('Logger service initialized');
    } catch (e) {
      debugPrint('Failed to initialize logger: $e');
    }
  }
  
  /// Initialize or rotate log file
  Future<void> _initializeLogFile() async {
    final directory = await _getLogDirectory();
    
    // Create logs directory if it doesn't exist
    if (!await directory.exists()) {
      await directory.create(recursive: true);
    }
    
    // Find the most recent log file
    final logFiles = await _getLogFiles();
    
    if (logFiles.isNotEmpty) {
      final lastFile = logFiles.last;
      final fileSize = await lastFile.length();
      
      // Use existing file if it's not full
      if (fileSize < maxLogSizeBytes) {
        _currentLogFile = lastFile;
        _currentLogSize = fileSize;
        return;
      }
    }
    
    // Create new log file
    await _createNewLogFile();
    
    // Rotate old files if necessary
    await _rotateLogFiles();
  }
  
  /// Get logs directory
  Future<Directory> _getLogDirectory() async {
    final appDir = await getApplicationDocumentsDirectory();
    return Directory('${appDir.path}/logs');
  }
  
  /// Get all log files sorted by creation time
  Future<List<File>> _getLogFiles() async {
    final directory = await _getLogDirectory();
    
    if (!await directory.exists()) {
      return [];
    }
    
    final files = directory
        .listSync()
        .whereType<File>()
        .where((f) => f.path.contains(logFilePrefix) && f.path.endsWith(logFileExtension))
        .toList();
    
    // Sort by last modified time
    files.sort((a, b) => a.lastModifiedSync().compareTo(b.lastModifiedSync()));
    
    return files;
  }
  
  /// Create a new log file
  Future<void> _createNewLogFile() async {
    final directory = await _getLogDirectory();
    final timestamp = _fileTimestampFormat.format(DateTime.now());
    final filename = '${logFilePrefix}_$timestamp$logFileExtension';
    
    _currentLogFile = File('${directory.path}/$filename');
    _currentLogSize = 0;
    
    // Write header
    final header = '=' * 60 + '\n'
        'Log started: ${_timestampFormat.format(DateTime.now())}\n'
        'App: TV Viewer\n'
        '=' * 60 + '\n\n';
    
    await _currentLogFile!.writeAsString(header);
    _currentLogSize = header.length;
  }
  
  /// Rotate log files (delete oldest if exceeds maxLogFiles)
  Future<void> _rotateLogFiles() async {
    final logFiles = await _getLogFiles();
    
    // Remove oldest files if we exceed the limit
    while (logFiles.length > maxLogFiles) {
      final oldestFile = logFiles.removeAt(0);
      try {
        await oldestFile.delete();
        debugPrint('Deleted old log file: ${oldestFile.path}');
      } catch (e) {
        debugPrint('Failed to delete log file: $e');
      }
    }
  }
  
  /// Write a log entry
  Future<void> _log(LogLevel level, String message, [dynamic error, StackTrace? stackTrace]) async {
    if (!_isInitialized) {
      await initialize();
    }
    
    // Filter by log level
    if (level.value < _minLogLevel.value) {
      return;
    }
    
    final timestamp = _timestampFormat.format(DateTime.now());
    final logEntry = StringBuffer();
    logEntry.writeln('[$timestamp] [${level.label}] $message');
    
    if (error != null) {
      logEntry.writeln('Error: $error');
    }
    
    if (stackTrace != null) {
      logEntry.writeln('Stack trace:\n$stackTrace');
    }
    
    logEntry.writeln(); // Empty line for readability
    
    // Also print to debug console in debug mode
    if (kDebugMode) {
      debugPrint('[${level.label}] $message');
      if (error != null) {
        debugPrint('Error: $error');
      }
    }
    
    // Add to buffer
    _logBuffer.add(logEntry.toString());
    
    // Flush immediately for errors
    if (level == LogLevel.error) {
      await _flushLogs();
    }
  }
  
  /// Flush buffered logs to file
  Future<void> _flushLogs() async {
    if (_logBuffer.isEmpty || _currentLogFile == null) {
      return;
    }
    
    try {
      final content = _logBuffer.join();
      _logBuffer.clear();
      
      // Check if we need to rotate
      final newSize = _currentLogSize + content.length;
      if (newSize > maxLogSizeBytes) {
        await _createNewLogFile();
        await _rotateLogFiles();
      }
      
      // Append to file
      await _currentLogFile!.writeAsString(content, mode: FileMode.append);
      _currentLogSize = await _currentLogFile!.length();
    } catch (e) {
      debugPrint('Failed to flush logs: $e');
    }
  }
  
  /// Public logging methods
  
  /// Log debug message (lowest priority)
  void debug(String message) {
    _log(LogLevel.debug, message);
  }
  
  /// Log info message
  void info(String message) {
    _log(LogLevel.info, message);
  }
  
  /// Log warning message
  void warning(String message, [dynamic error]) {
    _log(LogLevel.warning, message, error);
  }
  
  /// Log error message (highest priority)
  void error(String message, [dynamic error, StackTrace? stackTrace]) {
    _log(LogLevel.error, message, error, stackTrace);
  }
  
  /// Set minimum log level
  void setMinLogLevel(LogLevel level) {
    _minLogLevel = level;
    info('Log level changed to: ${level.label}');
  }
  
  /// Get all log files
  Future<List<File>> getAllLogFiles() async {
    return await _getLogFiles();
  }
  
  /// Export logs to a single file
  Future<File?> exportLogs() async {
    try {
      await _flushLogs(); // Ensure all logs are written
      
      final logFiles = await _getLogFiles();
      if (logFiles.isEmpty) {
        warning('No log files to export');
        return null;
      }
      
      final tempDir = await getTemporaryDirectory();
      final exportFile = File('${tempDir.path}/tv_viewer_logs_export_${_fileTimestampFormat.format(DateTime.now())}.txt');
      
      final exportBuffer = StringBuffer();
      exportBuffer.writeln('TV Viewer - Exported Logs');
      exportBuffer.writeln('Export Date: ${_timestampFormat.format(DateTime.now())}');
      exportBuffer.writeln('=' * 60);
      exportBuffer.writeln();
      
      // Combine all log files
      for (final logFile in logFiles) {
        exportBuffer.writeln('--- Log File: ${logFile.uri.pathSegments.last} ---');
        final content = await logFile.readAsString();
        exportBuffer.writeln(content);
        exportBuffer.writeln();
      }
      
      await exportFile.writeAsString(exportBuffer.toString());
      info('Logs exported to: ${exportFile.path}');
      
      return exportFile;
    } catch (e, stackTrace) {
      error('Failed to export logs', e, stackTrace);
      return null;
    }
  }
  
  /// Get logs as string (useful for displaying in UI)
  Future<String> getLogsAsString({int? maxLines}) async {
    try {
      final logFiles = await _getLogFiles();
      if (logFiles.isEmpty) {
        return 'No logs available';
      }
      
      final buffer = StringBuffer();
      
      // Read from newest to oldest
      for (final logFile in logFiles.reversed) {
        final content = await logFile.readAsString();
        buffer.write(content);
        buffer.writeln();
      }
      
      String result = buffer.toString();
      
      // Limit to maxLines if specified
      if (maxLines != null && maxLines > 0) {
        final lines = result.split('\n');
        if (lines.length > maxLines) {
          result = lines.sublist(lines.length - maxLines).join('\n');
        }
      }
      
      return result;
    } catch (e) {
      return 'Error reading logs: $e';
    }
  }
  
  /// Clear all logs
  Future<void> clearLogs() async {
    try {
      await _flushLogs();
      
      final logFiles = await _getLogFiles();
      for (final file in logFiles) {
        await file.delete();
      }
      
      _currentLogFile = null;
      _currentLogSize = 0;
      _logBuffer.clear();
      
      // Reinitialize with a fresh file
      await _initializeLogFile();
      info('All logs cleared');
    } catch (e) {
      error('Failed to clear logs', e);
    }
  }
  
  /// Get total size of all log files
  Future<int> getTotalLogSize() async {
    try {
      final logFiles = await _getLogFiles();
      int totalSize = 0;
      
      for (final file in logFiles) {
        totalSize += await file.length();
      }
      
      return totalSize;
    } catch (e) {
      error('Failed to calculate log size', e);
      return 0;
    }
  }
  
  /// Get formatted log size string
  Future<String> getFormattedLogSize() async {
    final bytes = await getTotalLogSize();
    
    if (bytes < 1024) {
      return '$bytes B';
    } else if (bytes < 1024 * 1024) {
      return '${(bytes / 1024).toStringAsFixed(2)} KB';
    } else {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(2)} MB';
    }
  }
  
  /// Dispose the logger service
  Future<void> dispose() async {
    _flushTimer?.cancel();
    await _flushLogs();
    _isInitialized = false;
  }
}

/// Global logger instance (convenience)
final logger = LoggerService.instance;
