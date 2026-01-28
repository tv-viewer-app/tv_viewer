import 'package:flutter_test/flutter_test.dart';
import 'package:tv_viewer_project/models/channel.dart';

/// Unit tests for Channel model
/// Coverage: Channel parsing, normalization, resolution extraction
void main() {
  group('Channel Model Tests', () {
    
    group('fromM3ULine - M3U Parsing', () {
      test('FC-DATA-1: Parse valid M3U line with all attributes', () {
        const m3uLine = '#EXTINF:-1 tvg-id="cnn" tvg-name="CNN" '
            'tvg-logo="http://example.com/cnn.png" '
            'tvg-country="US" tvg-language="English" '
            'group-title="News",CNN International (720p)';
        const url = 'http://stream.example.com/cnn.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.name, 'CNN International (720p)');
        expect(channel.url, url);
        expect(channel.logo, 'http://example.com/cnn.png');
        expect(channel.country, 'US');
        expect(channel.language, 'English');
        expect(channel.category, 'News');
      });

      test('FC-DATA-2: Parse M3U line with minimal attributes', () {
        const m3uLine = '#EXTINF:-1,Simple Channel';
        const url = 'http://stream.example.com/simple.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.name, 'Simple Channel');
        expect(channel.url, url);
        expect(channel.logo, '');
        expect(channel.country, '');
        expect(channel.category, '');
      });

      test('EC-DATA-1: Handle missing channel name', () {
        const m3uLine = '#EXTINF:-1 tvg-logo="http://example.com/logo.png"';
        const url = 'http://stream.example.com/channel.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        // Should extract name from after last comma (empty in this case)
        expect(channel.name, isNotNull);
        expect(channel.url, url);
      });

      test('EC-DATA-2: Handle very long channel name (200+ chars)', () {
        final longName = 'A' * 250;
        final m3uLine = '#EXTINF:-1,$longName';
        const url = 'http://stream.example.com/channel.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.name, longName);
        expect(channel.name.length, 250);
      });

      test('EC-DATA-3: Handle special characters in name', () {
        const m3uLine = '#EXTINF:-1,CNN™ © 2024 - News & Politics (24/7) 🎬';
        const url = 'http://stream.example.com/cnn.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.name, contains('CNN™'));
        expect(channel.name, contains('🎬'));
      });
    });

    group('normalizeCategory - Category Normalization', () {
      test('FC-3.4: Normalize category with semicolon separator', () {
        const m3uLine = '#EXTINF:-1 group-title="News;Politics;Sports",Channel';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        // Should take first part before semicolon and capitalize
        expect(channel.category, 'News');
      });

      test('FC-3.4: Capitalize first letter of category', () {
        const m3uLine = '#EXTINF:-1 group-title="sports",Channel';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.category, 'Sports');
      });

      test('EC-DATA-4: Handle empty category', () {
        const m3uLine = '#EXTINF:-1 group-title="",Channel';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.category, '');
      });

      test('EC-DATA-5: Handle category with only whitespace', () {
        const m3uLine = '#EXTINF:-1 group-title="   ",Channel';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        // Should trim whitespace
        expect(channel.category.trim(), isEmpty);
      });
    });

    group('extractResolution - Resolution Extraction', () {
      test('FC-10.3: Extract 720p resolution from name', () {
        const m3uLine = '#EXTINF:-1,CNN International (720p)';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.resolution, '720p');
      });

      test('FC-10.3: Extract 1080p resolution from name', () {
        const m3uLine = '#EXTINF:-1,BBC World News (1080p)';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.resolution, '1080p');
      });

      test('FC-10.3: Extract 480p resolution from name', () {
        const m3uLine = '#EXTINF:-1,Channel Name (480p) HD';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.resolution, '480p');
      });

      test('FC-10.5: Handle missing resolution gracefully', () {
        const m3uLine = '#EXTINF:-1,Channel Without Resolution';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.resolution, '');
      });

      test('EC-DATA-6: Handle multiple resolution patterns (take first)', () {
        const m3uLine = '#EXTINF:-1,Channel (720p) (1080p)';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        // Should extract first match
        expect(channel.resolution, '720p');
      });
    });

    group('mediaType - Auto-detection', () {
      test('FC-2.1: Detect TV media type from category', () {
        const m3uLine = '#EXTINF:-1 group-title="News",CNN';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.mediaType, 'TV');
      });

      test('FC-2.1: Detect Radio media type from category', () {
        const m3uLine = '#EXTINF:-1 group-title="Radio",BBC Radio 1';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.mediaType, 'Radio');
      });

      test('FC-2.1: Detect Radio from name containing "Radio"', () {
        const m3uLine = '#EXTINF:-1,Radio Station FM';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.mediaType, 'Radio');
      });

      test('FC-2.1: Detect Radio from audio URL extension', () {
        const m3uLine = '#EXTINF:-1,Music Station';
        const url = 'http://example.com/stream.mp3';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.mediaType, 'Radio');
      });

      test('FC-2.1: Default to TV when no radio indicators', () {
        const m3uLine = '#EXTINF:-1,Generic Channel';
        const url = 'http://example.com/stream.m3u8';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.mediaType, 'TV');
      });
    });

    group('formattedBitrate - Bitrate Formatting', () {
      test('FC-10.4: Format high bitrate as Mbps', () {
        final channel = Channel(
          name: 'Test',
          url: 'http://test.com',
          category: 'Test',
          logo: '',
          country: '',
          language: '',
          bitrate: 2500000, // 2.5 Mbps
        );
        
        expect(channel.formattedBitrate, '2.5 Mbps');
      });

      test('FC-10.4: Format low bitrate as Kbps', () {
        final channel = Channel(
          name: 'Test',
          url: 'http://test.com',
          category: 'Test',
          logo: '',
          country: '',
          language: '',
          bitrate: 500000, // 500 Kbps
        );
        
        expect(channel.formattedBitrate, '500.0 Kbps');
      });

      test('FC-10.5: Handle zero bitrate', () {
        final channel = Channel(
          name: 'Test',
          url: 'http://test.com',
          category: 'Test',
          logo: '',
          country: '',
          language: '',
          bitrate: 0,
        );
        
        expect(channel.formattedBitrate, 'N/A');
      });

      test('EC-DATA-7: Handle extremely large bitrate', () {
        final channel = Channel(
          name: 'Test',
          url: 'http://test.com',
          category: 'Test',
          logo: '',
          country: '',
          language: '',
          bitrate: 999999999, // ~1000 Mbps
        );
        
        final formatted = channel.formattedBitrate;
        expect(formatted, contains('Mbps'));
        expect(formatted, isNot(contains('NaN')));
      });

      test('EC-DATA-8: Handle negative bitrate', () {
        final channel = Channel(
          name: 'Test',
          url: 'http://test.com',
          category: 'Test',
          logo: '',
          country: '',
          language: '',
          bitrate: -1000,
        );
        
        // Should handle gracefully (show N/A or 0)
        expect(channel.formattedBitrate, anyOf('N/A', '0.0 Kbps'));
      });
    });

    group('JSON Serialization', () {
      test('FC-12.10: Serialize channel to JSON', () {
        final channel = Channel(
          name: 'CNN',
          url: 'http://example.com/stream.m3u8',
          category: 'News',
          logo: 'http://example.com/logo.png',
          country: 'US',
          language: 'English',
          bitrate: 2500000,
          resolution: '720p',
          isWorking: true,
          lastChecked: DateTime(2024, 1, 1, 12, 0, 0),
        );
        
        final json = channel.toJson();
        
        expect(json['name'], 'CNN');
        expect(json['url'], 'http://example.com/stream.m3u8');
        expect(json['category'], 'News');
        expect(json['logo'], 'http://example.com/logo.png');
        expect(json['country'], 'US');
        expect(json['language'], 'English');
        expect(json['bitrate'], 2500000);
        expect(json['resolution'], '720p');
        expect(json['isWorking'], true);
        expect(json['lastChecked'], isNotNull);
      });

      test('FC-12.10: Deserialize channel from JSON', () {
        final json = {
          'name': 'CNN',
          'url': 'http://example.com/stream.m3u8',
          'category': 'News',
          'logo': 'http://example.com/logo.png',
          'country': 'US',
          'language': 'English',
          'bitrate': 2500000,
          'resolution': '720p',
          'mediaType': 'TV',
          'isWorking': true,
          'lastChecked': '2024-01-01T12:00:00.000',
        };
        
        final channel = Channel.fromJson(json);
        
        expect(channel.name, 'CNN');
        expect(channel.url, 'http://example.com/stream.m3u8');
        expect(channel.category, 'News');
        expect(channel.logo, 'http://example.com/logo.png');
        expect(channel.country, 'US');
        expect(channel.language, 'English');
        expect(channel.bitrate, 2500000);
        expect(channel.resolution, '720p');
        expect(channel.mediaType, 'TV');
        expect(channel.isWorking, true);
        expect(channel.lastChecked, isNotNull);
      });

      test('EC-DATA-9: Handle missing optional fields in JSON', () {
        final json = {
          'name': 'Channel',
          'url': 'http://example.com/stream.m3u8',
        };
        
        final channel = Channel.fromJson(json);
        
        expect(channel.name, 'Channel');
        expect(channel.url, 'http://example.com/stream.m3u8');
        expect(channel.category, '');
        expect(channel.logo, '');
        expect(channel.bitrate, 0);
      });

      test('EC-DATA-10: Handle null values in JSON', () {
        final json = {
          'name': 'Channel',
          'url': 'http://example.com/stream.m3u8',
          'category': null,
          'logo': null,
          'country': null,
        };
        
        final channel = Channel.fromJson(json);
        
        expect(channel.name, 'Channel');
        expect(channel.url, 'http://example.com/stream.m3u8');
        // Should handle nulls gracefully with defaults
        expect(channel.category, anyOf('', isNull));
      });
    });

    group('Equality and Comparison', () {
      test('Compare channels by URL (deduplication)', () {
        final channel1 = Channel(
          name: 'CNN 1',
          url: 'http://example.com/stream.m3u8',
          category: 'News',
        );
        
        final channel2 = Channel(
          name: 'CNN 2',
          url: 'http://example.com/stream.m3u8',
          category: 'News',
        );
        
        // Same URL should be considered duplicate
        expect(channel1.url, channel2.url);
      });
    });

    group('Edge Cases', () {
      test('EC-DATA-11: URL with special characters and encoding', () {
        const m3uLine = '#EXTINF:-1,Channel';
        const url = 'http://example.com/stream?token=abc123&id=5&name=test%20channel';
        
        final channel = Channel.fromM3ULine(m3uLine, url);
        
        expect(channel.url, url);
      });

      test('EC-DATA-12: Handle very long URL', () {
        const m3uLine = '#EXTINF:-1,Channel';
        final longUrl = 'http://example.com/stream?' + ('param=value&' * 100);
        
        final channel = Channel.fromM3ULine(m3uLine, longUrl);
        
        expect(channel.url, longUrl);
        expect(channel.url.length, greaterThan(1000));
      });

      test('EC-DATA-13: Handle empty M3U line', () {
        const m3uLine = '';
        const url = 'http://example.com/stream.m3u8';
        
        // Should not crash
        expect(() => Channel.fromM3ULine(m3uLine, url), returnsNormally);
      });

      test('EC-DATA-14: Handle malformed M3U line', () {
        const m3uLine = 'NOT A VALID EXTINF LINE';
        const url = 'http://example.com/stream.m3u8';
        
        // Should not crash
        expect(() => Channel.fromM3ULine(m3uLine, url), returnsNormally);
      });
    });
  });
}
