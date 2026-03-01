import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import '../utils/logger_service.dart';

/// Service for syncing channel validation results with shared Supabase database
/// 
/// Features:
/// - Anonymous access (no user accounts required)
/// - Privacy-first: URLs are hashed with SHA256
/// - Cross-platform: Works with Android Flutter and Windows Python
/// - Efficient: Batch operations and 24h cache to skip re-scanning
/// 
/// Database Schema:
/// - url_hash (TEXT, PRIMARY KEY): SHA256 hash of channel URL
/// - status (TEXT): 'working' or 'failed'
/// - last_checked (TIMESTAMP): Last validation timestamp
/// - response_time_ms (INTEGER): Response time in milliseconds
class SharedDbService {
  // Supabase configuration
  // TODO: Replace with your actual Supabase project URL and anon key
  // Get these from: https://app.supabase.com/project/_/settings/api
  static const String _supabaseUrl = 'YOUR_SUPABASE_PROJECT_URL';
  static const String _supabaseAnonKey = 'YOUR_SUPABASE_ANON_KEY';
  static const String _tableName = 'channel_status';
  
  // Feature flag to enable/disable shared database
  // Set to false if you don't want to use the shared database
  static const bool _enabled = false; // TODO: Set to true after Supabase setup
  
  // Cache duration - only fetch results checked within last 24 hours
  static const Duration _cacheDuration = Duration(hours: 24);
  
  /// Hash a URL with SHA256 for privacy
  static String _hashUrl(String url) {
    final bytes = utf8.encode(url);
    final digest = sha256.convert(bytes);
    return digest.toString();
  }
  
  /// Check if the service is properly configured
  static bool get isConfigured {
    return _enabled && 
           _supabaseUrl != 'YOUR_SUPABASE_PROJECT_URL' &&
           _supabaseAnonKey != 'YOUR_SUPABASE_ANON_KEY';
  }
  
  /// Fetch recent channel validation results from shared database
  /// 
  /// Returns a Map of url_hash -> status for channels checked in last 24h
  /// Returns empty map if service is disabled or fetch fails
  Future<Map<String, ChannelStatusResult>> fetchRecentResults() async {
    if (!isConfigured) {
      logger.debug('SharedDbService: Service not configured or disabled');
      return {};
    }
    
    try {
      logger.info('Fetching recent channel results from shared database...');
      
      // Calculate timestamp for 24 hours ago
      final cutoffTime = DateTime.now().subtract(_cacheDuration).toUtc().toIso8601String();
      
      // Query Supabase REST API
      // Filter: last_checked > cutoff time
      final url = Uri.parse('$_supabaseUrl/rest/v1/$_tableName')
          .replace(queryParameters: {
        'last_checked': 'gte.$cutoffTime',
        'select': 'url_hash,status,last_checked,response_time_ms',
      });
      
      final response = await http.get(
        url,
        headers: {
          'apikey': _supabaseAnonKey,
          'Authorization': 'Bearer $_supabaseAnonKey',
        },
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        final results = <String, ChannelStatusResult>{};
        
        for (final item in data) {
          final urlHash = item['url_hash'] as String;
          final status = item['status'] as String;
          final lastChecked = DateTime.parse(item['last_checked'] as String);
          final responseTimeMs = item['response_time_ms'] as int?;
          
          results[urlHash] = ChannelStatusResult(
            status: status == 'working',
            lastChecked: lastChecked,
            responseTimeMs: responseTimeMs,
          );
        }
        
        logger.info('Fetched ${results.length} recent channel results from shared database');
        return results;
      } else {
        logger.warning('Failed to fetch shared database results: ${response.statusCode}');
        return {};
      }
    } catch (e, stackTrace) {
      logger.error('Error fetching from shared database', e, stackTrace);
      return {}; // Return empty map on error - don't block the app
    }
  }
  
  /// Upload channel validation results to shared database
  /// 
  /// Accepts a list of channel results to batch upload
  /// Returns true if upload succeeded, false otherwise
  Future<bool> uploadResults(List<ChannelResult> results) async {
    if (!isConfigured) {
      logger.debug('SharedDbService: Service not configured or disabled');
      return false;
    }
    
    if (results.isEmpty) {
      logger.debug('SharedDbService: No results to upload');
      return true;
    }
    
    try {
      logger.info('Uploading ${results.length} channel results to shared database...');
      
      // Prepare batch payload
      final payload = results.map((result) => {
        'url_hash': _hashUrl(result.url),
        'status': result.isWorking ? 'working' : 'failed',
        'last_checked': result.lastChecked.toUtc().toIso8601String(),
        'response_time_ms': result.responseTimeMs,
      }).toList();
      
      // Upsert to Supabase (insert or update on conflict)
      final url = Uri.parse('$_supabaseUrl/rest/v1/$_tableName');
      
      final response = await http.post(
        url,
        headers: {
          'apikey': _supabaseAnonKey,
          'Authorization': 'Bearer $_supabaseAnonKey',
          'Content-Type': 'application/json',
          'Prefer': 'resolution=merge-duplicates', // Upsert on conflict
        },
        body: json.encode(payload),
      ).timeout(const Duration(seconds: 30));
      
      if (response.statusCode == 201 || response.statusCode == 200) {
        logger.info('Successfully uploaded ${results.length} channel results');
        return true;
      } else {
        logger.warning('Failed to upload results: ${response.statusCode} - ${response.body}');
        return false;
      }
    } catch (e, stackTrace) {
      logger.error('Error uploading to shared database', e, stackTrace);
      return false; // Don't block on upload failure
    }
  }
  
  /// Get cached status for a specific URL
  /// 
  /// Returns the cached status if available and recent, null otherwise
  Future<ChannelStatusResult?> getCachedStatus(
    String url,
    Map<String, ChannelStatusResult> cache,
  ) async {
    final urlHash = _hashUrl(url);
    return cache[urlHash];
  }
  
  /// Check if a channel should be skipped based on cached results
  /// 
  /// Returns true if the channel was recently checked and is working
  bool shouldSkipValidation(
    String url,
    Map<String, ChannelStatusResult> cache,
  ) {
    final urlHash = _hashUrl(url);
    final cached = cache[urlHash];
    
    if (cached == null) return false;
    
    // Only skip if it's working and recently checked
    final age = DateTime.now().difference(cached.lastChecked);
    return cached.status && age < _cacheDuration;
  }
}

/// Result of a channel validation check
class ChannelResult {
  final String url;
  final bool isWorking;
  final DateTime lastChecked;
  final int? responseTimeMs;
  
  ChannelResult({
    required this.url,
    required this.isWorking,
    required this.lastChecked,
    this.responseTimeMs,
  });
}

/// Cached channel status from shared database
class ChannelStatusResult {
  final bool status;
  final DateTime lastChecked;
  final int? responseTimeMs;
  
  ChannelStatusResult({
    required this.status,
    required this.lastChecked,
    this.responseTimeMs,
  });
}
