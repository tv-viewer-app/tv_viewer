import '../models/channel.dart';

/// Repository interface for M3U playlist operations
/// 
/// This interface defines operations for fetching and parsing M3U playlists
/// from various sources. It abstracts the playlist format details from
/// the rest of the application.
abstract class PlaylistRepository {
  /// Fetch and parse M3U playlist from a URL
  /// 
  /// Downloads the playlist content and parses it into Channel objects.
  /// Throws exceptions if the URL is unreachable or content is invalid.
  Future<List<Channel>> fetchFromUrl(String url);

  /// Parse M3U content into Channel objects
  /// 
  /// Converts raw M3U text format into structured Channel objects.
  /// Throws exceptions if content cannot be parsed.
  List<Channel> parseM3U(String content);

  /// Fetch channels from all configured playlist sources
  /// 
  /// Aggregates channels from multiple playlist URLs with deduplication.
  /// Returns combined results even if some sources fail.
  Future<List<Channel>> fetchAllChannels({
    void Function(int current, int total)? onProgress,
  });

  /// Deduplicate channels with the same stream URL
  /// 
  /// Removes duplicate entries, keeping the one with most complete metadata.
  /// Useful when aggregating from multiple sources.
  List<Channel> deduplicateChannels(List<Channel> channels);

  /// Export channels as M3U format
  /// 
  /// Converts a list of channels back to M3U playlist text format.
  /// Useful for creating custom playlists or backups.
  String exportAsM3U(List<Channel> channels);
}
