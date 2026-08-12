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
  // Credentials must be provided via --dart-define at build time.
  // No hardcoded defaults — shared DB stays off until explicitly configured.
  static String get _supabaseUrl =>
      const String.fromEnvironment('SUPABASE_URL', defaultValue: '');
  static String get _supabaseAnonKey =>
      const String.fromEnvironment('SUPABASE_ANON_KEY', defaultValue: '');
  static const String _tableName = 'channel_status';
  
  // Automatically enabled when environment variables are set
  static bool get _enabled => _supabaseUrl.isNotEmpty && _supabaseAnonKey.isNotEmpty;
  
  // Cache duration - only fetch results checked within last 24 hours
  static const Duration _cacheDuration = Duration(hours: 24);
  
  /// Hash a URL with SHA256 for privacy
  static String hashUrl(String url) {
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

  /// Fetch aggregated play counts keyed by channel hash from mv_top_channels.
  Future<Map<String, int>> fetchTopChannelPlayCounts({int limit = 100}) async {
    if (!isConfigured) {
      logger.debug('SharedDbService: Popularity view unavailable (service not configured)');
      return {};
    }

    try {
      final url = Uri.parse('$_supabaseUrl/rest/v1/mv_top_channels').replace(
        queryParameters: {
          'select': 'channel_hash,play_count',
          'order': 'play_count.desc',
          'limit': '$limit',
        },
      );

      final response = await http.get(
        url,
        headers: {
          'apikey': _supabaseAnonKey,
          'Authorization': '******',
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode != 200) {
        logger.warning('Failed to fetch top channel play counts: ${response.statusCode}');
        return {};
      }

      final List<dynamic> data = json.decode(response.body);
      final playCounts = <String, int>{};
      for (final item in data) {
        final row = Map<String, dynamic>.from(item as Map);
        final channelHash = (row['channel_hash'] as String? ?? '').trim();
        if (channelHash.isEmpty) continue;
        playCounts[channelHash] = (row['play_count'] as num?)?.toInt() ?? 0;
      }
      logger.info('Fetched ${playCounts.length} channel popularity rows');
      return playCounts;
    } catch (e, stackTrace) {
      logger.error('Error fetching top channel play counts', e, stackTrace);
      return {};
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
        'url_hash': hashUrl(result.url),
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
  
  /// Fetch consolidated channels from shared Supabase database
  /// 
  /// Returns channels with name, urls (multi-source), category, country, etc.
  /// Both platforms share this same database for consistent channel lists.
  Future<List<Map<String, dynamic>>> fetchChannels({int limit = 20000}) async {
    if (!isConfigured) {
      logger.debug('SharedDbService: Service not configured for channels fetch');
      return [];
    }

    try {
      logger.info('Fetching channels from shared database...');

      final url = Uri.parse('$_supabaseUrl/rest/v1/channels')
          .replace(queryParameters: {
        'select': 'url_hash,name,urls,category,country,logo,media_type,source',
        'limit': '$limit',
      });

      final response = await http.get(
        url,
        headers: {
          'apikey': _supabaseAnonKey,
          'Authorization': 'Bearer $_supabaseAnonKey',
        },
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        // Security: Guard against oversized responses
        if (response.bodyBytes.length > 50 * 1024 * 1024) {
          logger.warning('Supabase response too large (>${response.bodyBytes.length} bytes)');
          return [];
        }
        final List<dynamic> data = json.decode(response.body);
        final channels = data
            .map((item) => Map<String, dynamic>.from(item as Map))
            .toList();

        for (final channel in channels) {
          channel.putIfAbsent('status', () => 'unchecked');
          channel.putIfAbsent('report_count', () => 0);
        }

        try {
          final selectVariants = <String>[
            'url_hash,status,report_count,working_reports,broken_reports,failed_reports',
            'url_hash,status,report_count',
          ];
          http.Response? healthResp;
          String? selectedFields;

          for (final fields in selectVariants) {
            final probeUrl = Uri.parse('$_supabaseUrl/rest/v1/channel_status').replace(
              queryParameters: {
                'select': fields,
                'limit': '1',
              },
            );
            final probeResp = await http.get(
              probeUrl,
              headers: {
                'apikey': _supabaseAnonKey,
                'Authorization': '******',
              },
            ).timeout(const Duration(seconds: 10));
            if (probeResp.statusCode == 200) {
              selectedFields = fields;
              break;
            }
          }

          if (selectedFields != null) {
            final healthUrl = Uri.parse('$_supabaseUrl/rest/v1/channel_status').replace(
              queryParameters: {
                'select': selectedFields,
              },
            );
            healthResp = await http.get(
              healthUrl,
              headers: {
                'apikey': _supabaseAnonKey,
                'Authorization': '******',
              },
            ).timeout(const Duration(seconds: 15));
          }

          if (healthResp?.statusCode == 200) {
            final List<dynamic> healthList = json.decode(healthResp!.body);
            final healthMap = <String, Map<String, dynamic>>{
              for (final item in healthList)
                (item['url_hash'] as String? ?? ''): Map<String, dynamic>.from(item as Map),
            };

            for (final channel in channels) {
              final urlHash = channel['url_hash'] as String?;
              if (urlHash == null || urlHash.isEmpty) continue;
              final health = healthMap[urlHash];
              if (health == null) continue;
              channel['status'] = health['status'] ?? channel['status'] ?? 'unchecked';
              channel['report_count'] = health['report_count'] ?? channel['report_count'] ?? 0;
              channel['working_reports'] = health['working_reports'] ?? channel['working_reports'] ?? 0;
              channel['broken_reports'] = health['broken_reports'] ?? channel['broken_reports'] ?? 0;
              channel['failed_reports'] = health['failed_reports'] ?? channel['failed_reports'] ?? 0;
            }
            logger.info('Merged health metadata into ${channels.length} channels');
          } else if (selectedFields == null) {
            logger.warning('Failed to resolve supported channel health metadata fields');
          } else {
            logger.warning('Failed to fetch channel health metadata: ${healthResp?.statusCode}');
          }
        } catch (e, stackTrace) {
          logger.error('Failed to merge channel health metadata', e, stackTrace);
        }

        logger.info('Fetched ${channels.length} channels from shared database');
        return channels;
      } else {
        logger.warning('Failed to fetch channels: ${response.statusCode}');
        return [];
      }
    } catch (e, stackTrace) {
      logger.error('Error fetching channels from shared database', e, stackTrace);
      return [];
    }
  }

  /// Contribute discovered channels back to the shared database
  /// 
  /// Performs upsert so existing channels get updated, new ones added.
  Future<int> contributeChannels(List<Map<String, dynamic>> channels) async {
    if (!isConfigured || channels.isEmpty) return 0;

    try {
      final payload = <Map<String, dynamic>>[];
      for (final ch in channels) {
        final primaryUrl = ch['url'] as String? ?? '';
        if (primaryUrl.isEmpty) continue;

        var urls = ch['urls'];
        if (urls is String) {
          urls = json.decode(urls);
        }
        urls ??= [primaryUrl];
        if (urls is List && !urls.contains(primaryUrl)) {
          urls = [primaryUrl, ...urls];
        }

        payload.add({
          'url_hash': hashUrl(primaryUrl),
          'name': (ch['name'] as String? ?? '').substring(
              0, (ch['name'] as String? ?? '').length.clamp(0, 200)),
          'urls': urls,
          'category': ch['category'] ?? 'Other',
          'country': ch['country'] ?? 'Unknown',
          'logo': (ch['logo'] as String? ?? '').substring(
              0, (ch['logo'] as String? ?? '').length.clamp(0, 500)),
          'media_type': ch['media_type'],
          'source': ch['source'] ?? 'flutter-app',
          'updated_at': DateTime.now().toUtc().toIso8601String(),
        });
      }

      if (payload.isEmpty) return 0;

      int contributed = 0;
      const batchSize = 500;
      for (int i = 0; i < payload.length; i += batchSize) {
        final batch = payload.sublist(
            i, (i + batchSize).clamp(0, payload.length));
        final url = Uri.parse('$_supabaseUrl/rest/v1/channels');

        final response = await http.post(
          url,
          headers: {
            'apikey': _supabaseAnonKey,
            'Authorization': 'Bearer $_supabaseAnonKey',
            'Content-Type': 'application/json',
            'Prefer': 'resolution=merge-duplicates',
          },
          body: json.encode(batch),
        ).timeout(const Duration(seconds: 30));

        if (response.statusCode == 200 || response.statusCode == 201) {
          contributed += batch.length;
        } else {
          logger.warning(
              'Channel contribute batch failed: ${response.statusCode}');
        }
      }

      if (contributed > 0) {
        logger.info('Contributed $contributed channels to shared database');
      }
      return contributed;
    } catch (e, stackTrace) {
      logger.error('Error contributing channels', e, stackTrace);
      return 0;
    }
  }

  /// Get cached status for a specific URL
  /// 
  /// Returns the cached status if available and recent, null otherwise
  Future<ChannelStatusResult?> getCachedStatus(
    String url,
    Map<String, ChannelStatusResult> cache,
  ) async {
    final urlHash = hashUrl(url);
    return cache[urlHash];
  }
  
  /// Check if a channel should be skipped based on cached results
  /// 
  /// Returns true if the channel was recently checked and is working
  bool shouldSkipValidation(
    String url,
    Map<String, ChannelStatusResult> cache,
  ) {
    final urlHash = hashUrl(url);
    final cached = cache[urlHash];
    
    if (cached == null) return false;
    
    // Only skip if it's working and recently checked
    final age = DateTime.now().difference(cached.lastChecked);
    return cached.status && age < _cacheDuration;
  }
  
  /// Report a single channel status to Supabase (fire-and-forget)
  /// 
  /// Used when a user plays a channel and it fails, to update the shared cache
  /// for other clients. This is a fire-and-forget operation that never blocks the UI.
  static Future<void> reportChannelStatus({
    required String url,
    required String status, // 'working' or 'failed'
    int? responseTimeMs,
  }) async {
    if (!isConfigured) return;
    
    try {
      final urlHash = hashUrl(url);
      final payload = {
        'url_hash': urlHash,
        'status': status,
        'last_checked': DateTime.now().toUtc().toIso8601String(),
        'response_time_ms': responseTimeMs,
      };
      
      final apiUrl = Uri.parse('$_supabaseUrl/rest/v1/$_tableName');
      
      // Fire-and-forget with 5 second timeout
      http.post(
        apiUrl,
        headers: {
          'apikey': _supabaseAnonKey,
          'Authorization': 'Bearer $_supabaseAnonKey',
          'Content-Type': 'application/json',
          'Prefer': 'resolution=merge-duplicates',
        },
        body: json.encode(payload),
      ).timeout(
        const Duration(seconds: 5),
        onTimeout: () {
          // Silently ignore timeout
          return http.Response('', 408);
        },
      ).catchError((_) {
        return http.Response('', 500);
      });
    } catch (_) {
      // Silently ignore all errors - never block the UI
    }
  }

  /// Report a broken channel by incrementing its report_count in Supabase.
  /// Uses Supabase RPC or a PATCH with headers to increment the count.
  /// Fire-and-forget: never blocks the UI.
  static Future<void> reportBrokenChannel(String urlHash) async {
    if (!isConfigured) return;
    
    try {
      // First, try to get current report_count
      final getUrl = Uri.parse('$_supabaseUrl/rest/v1/channels')
          .replace(queryParameters: {
        'url_hash': 'eq.$urlHash',
        'select': 'report_count',
      });
      
      final getResponse = await http.get(
        getUrl,
        headers: {
          'apikey': _supabaseAnonKey,
          'Authorization': 'Bearer $_supabaseAnonKey',
        },
      ).timeout(const Duration(seconds: 5));
      
      int currentCount = 0;
      if (getResponse.statusCode == 200) {
        final List<dynamic> data = json.decode(getResponse.body);
        if (data.isNotEmpty) {
          currentCount = (data.first['report_count'] as int?) ?? 0;
        }
      }
      
      // Then PATCH with incremented count
      final patchUrl = Uri.parse('$_supabaseUrl/rest/v1/channels?url_hash=eq.$urlHash');
      
      await http.patch(
        patchUrl,
        headers: {
          'apikey': _supabaseAnonKey,
          'Authorization': 'Bearer $_supabaseAnonKey',
          'Content-Type': 'application/json',
          'Prefer': 'return=minimal',
        },
        body: json.encode({
          'report_count': currentCount + 1,
        }),
      ).timeout(const Duration(seconds: 5));
      
      logger.info('Reported broken channel: $urlHash (count: ${currentCount + 1})');
    } catch (e) {
      logger.debug('Report broken channel error (non-critical): $e');
      // Silently ignore - never block the UI
    }
  }

  /// Contribute a single channel to the shared database.
  /// Convenience wrapper around [contributeChannels].
  Future<bool> contributeChannel(Map<String, dynamic> channel) async {
    final count = await contributeChannels([channel]);
    return count > 0;
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
