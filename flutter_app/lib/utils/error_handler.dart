import 'dart:io';
import 'dart:async';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:video_player/video_player.dart';

/// Error codes for categorizing different types of errors
class ErrorCode {
  // Network errors (ERR_NET_xxx)
  static const String noInternet = 'ERR_NET_001';
  static const String timeout = 'ERR_NET_002';
  static const String serverError = 'ERR_NET_003';
  static const String notFound = 'ERR_NET_004';
  static const String unauthorized = 'ERR_NET_005';
  static const String forbidden = 'ERR_NET_006';
  static const String connectionRefused = 'ERR_NET_007';
  
  // Stream errors (ERR_STREAM_xxx)
  static const String streamNotAvailable = 'ERR_STREAM_001';
  static const String streamTimeout = 'ERR_STREAM_002';
  static const String streamFormatUnsupported = 'ERR_STREAM_003';
  static const String streamInitFailed = 'ERR_STREAM_004';
  static const String streamPlaybackError = 'ERR_STREAM_005';
  static const String streamCodecError = 'ERR_STREAM_006';
  
  // M3U/Playlist errors (ERR_M3U_xxx)
  static const String m3uInvalid = 'ERR_M3U_001';
  static const String m3uEmpty = 'ERR_M3U_002';
  static const String m3uParseFailed = 'ERR_M3U_003';
  static const String m3uNoChannels = 'ERR_M3U_004';
  
  // Storage errors (ERR_STORAGE_xxx)
  static const String storageFailed = 'ERR_STORAGE_001';
  static const String cacheReadFailed = 'ERR_STORAGE_002';
  static const String cacheWriteFailed = 'ERR_STORAGE_003';
  
  // General errors (ERR_GEN_xxx)
  static const String unknown = 'ERR_GEN_001';
  static const String invalidInput = 'ERR_GEN_002';
  static const String permissionDenied = 'ERR_GEN_003';
}

/// Application-specific error class with user-friendly messages and recovery suggestions
class AppError implements Exception {
  final String code;
  final String userMessage;
  final String technicalDetails;
  final String recoverySuggestion;
  final Exception? originalException;
  final StackTrace? stackTrace;
  
  AppError({
    required this.code,
    required this.userMessage,
    required this.technicalDetails,
    required this.recoverySuggestion,
    this.originalException,
    this.stackTrace,
  });
  
  @override
  String toString() {
    return 'AppError($code): $userMessage';
  }
  
  /// Get formatted details for logging
  String getDetailedLog() {
    final buffer = StringBuffer();
    buffer.writeln('Error Code: $code');
    buffer.writeln('User Message: $userMessage');
    buffer.writeln('Technical Details: $technicalDetails');
    buffer.writeln('Recovery Suggestion: $recoverySuggestion');
    
    if (originalException != null) {
      buffer.writeln('Original Exception: $originalException');
    }
    
    if (stackTrace != null) {
      buffer.writeln('Stack Trace:\n$stackTrace');
    }
    
    return buffer.toString();
  }
}

/// Main error handler service
class ErrorHandler {
  /// Convert any exception to an AppError with user-friendly message
  static AppError handle(dynamic error, [StackTrace? stackTrace]) {
    if (error is AppError) {
      return error;
    }
    
    // Network errors
    if (error is SocketException) {
      return _handleSocketException(error, stackTrace);
    }
    
    if (error is TimeoutException) {
      return _handleTimeoutException(error, stackTrace);
    }
    
    if (error is http.ClientException) {
      return _handleClientException(error, stackTrace);
    }
    
    if (error is HttpException) {
      return _handleHttpException(error, stackTrace);
    }
    
    // Format errors
    if (error is FormatException) {
      return _handleFormatException(error, stackTrace);
    }
    
    // File system errors
    if (error is FileSystemException) {
      return _handleFileSystemException(error, stackTrace);
    }
    
    // Video player errors (PlatformException from video_player)
    if (error is PlatformException) {
      return _handleVideoPlayerException(error, stackTrace);
    }
    
    // Generic error
    return AppError(
      code: ErrorCode.unknown,
      userMessage: 'An unexpected error occurred',
      technicalDetails: error.toString(),
      recoverySuggestion: 'Please try again. If the problem persists, restart the app.',
      originalException: error is Exception ? error : null,
      stackTrace: stackTrace,
    );
  }
  
  /// Handle SocketException (no internet, connection refused, etc.)
  static AppError _handleSocketException(SocketException error, StackTrace? stackTrace) {
    String code;
    String userMessage;
    String recoverySuggestion;
    
    if (error.osError?.errorCode == 7 || error.osError?.errorCode == 8) {
      // No address associated with hostname / nodename nor servname provided
      code = ErrorCode.noInternet;
      userMessage = 'No internet connection detected';
      recoverySuggestion = 'Check your WiFi or mobile data connection and try again.';
    } else if (error.osError?.errorCode == 111 || error.osError?.errorCode == 61) {
      // Connection refused
      code = ErrorCode.connectionRefused;
      userMessage = 'Cannot connect to the server';
      recoverySuggestion = 'The server may be down. Try again later or contact support.';
    } else {
      code = ErrorCode.noInternet;
      userMessage = 'Network connection problem';
      recoverySuggestion = 'Check your internet connection:\n'
          '• Verify WiFi or mobile data is enabled\n'
          '• Try restarting your router\n'
          '• Check if other apps can connect';
    }
    
    return AppError(
      code: code,
      userMessage: userMessage,
      technicalDetails: 'SocketException: ${error.message} (OS Error: ${error.osError})',
      recoverySuggestion: recoverySuggestion,
      originalException: error,
      stackTrace: stackTrace,
    );
  }
  
  /// Handle TimeoutException
  static AppError _handleTimeoutException(TimeoutException error, StackTrace? stackTrace) {
    return AppError(
      code: ErrorCode.timeout,
      userMessage: 'Connection timed out',
      technicalDetails: 'TimeoutException: ${error.message}',
      recoverySuggestion: 'The server is taking too long to respond:\n'
          '• Check your internet speed\n'
          '• Try again in a moment\n'
          '• The server may be overloaded',
      originalException: error,
      stackTrace: stackTrace,
    );
  }
  
  /// Handle HTTP ClientException
  static AppError _handleClientException(http.ClientException error, StackTrace? stackTrace) {
    return AppError(
      code: ErrorCode.serverError,
      userMessage: 'Failed to communicate with server',
      technicalDetails: 'ClientException: ${error.message}',
      recoverySuggestion: 'Check your internet connection and try again.',
      originalException: error,
      stackTrace: stackTrace,
    );
  }
  
  /// Handle HttpException
  static AppError _handleHttpException(HttpException error, StackTrace? stackTrace) {
    return AppError(
      code: ErrorCode.serverError,
      userMessage: 'Server communication error',
      technicalDetails: 'HttpException: ${error.message}',
      recoverySuggestion: 'The server encountered an issue. Try again later.',
      originalException: error,
      stackTrace: stackTrace,
    );
  }
  
  /// Handle FormatException (parsing errors)
  static AppError _handleFormatException(FormatException error, StackTrace? stackTrace) {
    return AppError(
      code: ErrorCode.m3uInvalid,
      userMessage: 'Invalid data format',
      technicalDetails: 'FormatException: ${error.message}',
      recoverySuggestion: 'The playlist or stream format is not supported:\n'
          '• Verify the M3U URL is correct\n'
          '• Try a different playlist source',
      originalException: error,
      stackTrace: stackTrace,
    );
  }
  
  /// Handle FileSystemException
  static AppError _handleFileSystemException(FileSystemException error, StackTrace? stackTrace) {
    return AppError(
      code: ErrorCode.storageFailed,
      userMessage: 'Storage access failed',
      technicalDetails: 'FileSystemException: ${error.message}',
      recoverySuggestion: 'Cannot access device storage:\n'
          '• Check available storage space\n'
          '• Verify app permissions\n'
          '• Try clearing app cache',
      originalException: error,
      stackTrace: stackTrace,
    );
  }
  
  /// Handle video player PlatformException
  static AppError _handleVideoPlayerException(
    PlatformException error,
    StackTrace? stackTrace,
  ) {
    String code;
    String userMessage;
    String recoverySuggestion;
    
    final errorMessage = error.toString().toLowerCase();
    
    if (errorMessage.contains('format') || errorMessage.contains('codec')) {
      code = ErrorCode.streamCodecError;
      userMessage = 'Stream format not supported';
      recoverySuggestion = 'This video format cannot be played:\n'
          '• Try a different stream\n'
          '• The codec may not be supported on your device';
    } else if (errorMessage.contains('network') || errorMessage.contains('source')) {
      code = ErrorCode.streamNotAvailable;
      userMessage = 'Stream is not available';
      recoverySuggestion = 'Cannot load the stream:\n'
          '• The stream may be offline\n'
          '• Try another channel\n'
          '• Check your internet connection';
    } else {
      code = ErrorCode.streamPlaybackError;
      userMessage = 'Playback error occurred';
      recoverySuggestion = 'The stream cannot be played:\n'
          '• Try restarting playback\n'
          '• Select a different stream\n'
          '• Check if the stream is still active';
    }
    
    return AppError(
      code: code,
      userMessage: userMessage,
      technicalDetails: 'VideoPlayerPlatformException: ${error.toString()}',
      recoverySuggestion: recoverySuggestion,
      originalException: error,
      stackTrace: stackTrace,
    );
  }
  
  /// Handle HTTP status code errors
  static AppError handleHttpStatusCode(int statusCode, String url) {
    String code;
    String userMessage;
    String recoverySuggestion;
    
    switch (statusCode) {
      case 400:
        code = ErrorCode.invalidInput;
        userMessage = 'Invalid request';
        recoverySuggestion = 'The request format is incorrect. Please verify the URL.';
        break;
      case 401:
        code = ErrorCode.unauthorized;
        userMessage = 'Authentication required';
        recoverySuggestion = 'This content requires authentication:\n'
            '• Check if credentials are needed\n'
            '• Verify the URL is correct';
        break;
      case 403:
        code = ErrorCode.forbidden;
        userMessage = 'Access denied';
        recoverySuggestion = 'You do not have permission to access this content.';
        break;
      case 404:
        code = ErrorCode.notFound;
        userMessage = 'Content not found';
        recoverySuggestion = 'The requested content does not exist:\n'
            '• Verify the URL is correct\n'
            '• The content may have been removed';
        break;
      case 500:
      case 502:
      case 503:
      case 504:
        code = ErrorCode.serverError;
        userMessage = 'Server error';
        recoverySuggestion = 'The server is experiencing issues:\n'
            '• Try again in a few minutes\n'
            '• The server may be under maintenance';
        break;
      default:
        code = ErrorCode.serverError;
        userMessage = 'Server returned error $statusCode';
        recoverySuggestion = 'An unexpected server error occurred. Try again later.';
    }
    
    return AppError(
      code: code,
      userMessage: userMessage,
      technicalDetails: 'HTTP $statusCode for URL: $url',
      recoverySuggestion: recoverySuggestion,
    );
  }
  
  /// Create custom M3U error
  static AppError m3uError(String type, String details) {
    String code;
    String userMessage;
    String recoverySuggestion;
    
    switch (type) {
      case 'empty':
        code = ErrorCode.m3uEmpty;
        userMessage = 'Playlist is empty';
        recoverySuggestion = 'The M3U playlist contains no channels:\n'
            '• Verify the playlist URL\n'
            '• Try a different playlist';
        break;
      case 'invalid':
        code = ErrorCode.m3uInvalid;
        userMessage = 'Invalid playlist format';
        recoverySuggestion = 'The playlist format is not valid:\n'
            '• Ensure it is a valid M3U file\n'
            '• Check the file encoding\n'
            '• Try downloading it to verify content';
        break;
      case 'parse':
        code = ErrorCode.m3uParseFailed;
        userMessage = 'Failed to parse playlist';
        recoverySuggestion = 'Cannot read the playlist:\n'
            '• The file may be corrupted\n'
            '• Try a different source';
        break;
      case 'no_channels':
        code = ErrorCode.m3uNoChannels;
        userMessage = 'No valid channels found';
        recoverySuggestion = 'No playable channels in the playlist:\n'
            '• All channels may be offline\n'
            '• Try a different playlist';
        break;
      default:
        code = ErrorCode.m3uParseFailed;
        userMessage = 'Playlist error';
        recoverySuggestion = 'Cannot process the playlist. Try again.';
    }
    
    return AppError(
      code: code,
      userMessage: userMessage,
      technicalDetails: details,
      recoverySuggestion: recoverySuggestion,
    );
  }
  
  /// Create custom stream error
  static AppError streamError(String type, String details) {
    String code;
    String userMessage;
    String recoverySuggestion;
    
    switch (type) {
      case 'not_available':
        code = ErrorCode.streamNotAvailable;
        userMessage = 'Stream is not available';
        recoverySuggestion = 'This stream cannot be accessed:\n'
            '• The channel may be offline\n'
            '• Try another channel';
        break;
      case 'timeout':
        code = ErrorCode.streamTimeout;
        userMessage = 'Stream loading timed out';
        recoverySuggestion = 'The stream took too long to load:\n'
            '• Check your internet speed\n'
            '• The stream server may be slow\n'
            '• Try again later';
        break;
      case 'format':
        code = ErrorCode.streamFormatUnsupported;
        userMessage = 'Stream format not supported';
        recoverySuggestion = 'This stream format cannot be played on your device:\n'
            '• Try a different channel\n'
            '• The codec may not be supported';
        break;
      case 'init_failed':
        code = ErrorCode.streamInitFailed;
        userMessage = 'Failed to initialize stream';
        recoverySuggestion = 'Cannot start the stream:\n'
            '• Try restarting playback\n'
            '• Select a different stream';
        break;
      default:
        code = ErrorCode.streamPlaybackError;
        userMessage = 'Stream playback error';
        recoverySuggestion = 'Cannot play the stream. Try another channel.';
    }
    
    return AppError(
      code: code,
      userMessage: userMessage,
      technicalDetails: details,
      recoverySuggestion: recoverySuggestion,
    );
  }
  
  /// Create storage error
  static AppError storageError(String operation, String details) {
    return AppError(
      code: ErrorCode.storageFailed,
      userMessage: 'Storage operation failed',
      technicalDetails: '$operation: $details',
      recoverySuggestion: 'Cannot access storage:\n'
          '• Check available storage space\n'
          '• Verify app permissions\n'
          '• Try clearing cache in settings',
    );
  }
}
