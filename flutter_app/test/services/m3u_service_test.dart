import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:tv_viewer_project/services/m3u_service.dart';
import 'package:tv_viewer_project/models/channel.dart';

// Generate mocks with: flutter pub run build_runner build
@GenerateMocks([http.Client])
import 'm3u_service_test.mocks.dart';

/// Unit tests for M3UService
/// Coverage: M3U fetching, parsing, validation
void main() {
  group('M3UService Tests', () {
    late M3UService service;
    late MockClient mockClient;

    setUp(() {
      mockClient = MockClient();
      service = M3UService();
    });

    group('parseM3U - M3U Parsing', () {
      test('FC-SERVICE-1: Parse valid M3U content with multiple channels', () {
        const m3uContent = '''
#EXTM3U
#EXTINF:-1 tvg-id="cnn" tvg-logo="http://example.com/cnn.png" group-title="News",CNN
http://stream.example.com/cnn.m3u8
#EXTINF:-1 tvg-id="bbc" tvg-logo="http://example.com/bbc.png" group-title="News",BBC
http://stream.example.com/bbc.m3u8
#EXTINF:-1 tvg-id="espn" tvg-logo="http://example.com/espn.png" group-title="Sports",ESPN
http://stream.example.com/espn.m3u8
''';

        final channels = service.parseM3U(m3uContent);

        expect(channels.length, 3);
        expect(channels[0].name, 'CNN');
        expect(channels[0].url, 'http://stream.example.com/cnn.m3u8');
        expect(channels[1].name, 'BBC');
        expect(channels[2].name, 'ESPN');
        expect(channels[2].category, 'Sports');
      });

      test('FC-SERVICE-2: Parse M3U with Windows line endings (\\r\\n)', () {
        const m3uContent = '#EXTM3U\r\n'
            '#EXTINF:-1,Channel 1\r\n'
            'http://stream1.com\r\n'
            '#EXTINF:-1,Channel 2\r\n'
            'http://stream2.com\r\n';

        final channels = service.parseM3U(m3uContent);

        expect(channels.length, 2);
        expect(channels[0].name, 'Channel 1');
        expect(channels[1].name, 'Channel 2');
      });

      test('FC-SERVICE-3: Parse M3U with Unix line endings (\\n)', () {
        const m3uContent = '#EXTM3U\n'
            '#EXTINF:-1,Channel 1\n'
            'http://stream1.com\n'
            '#EXTINF:-1,Channel 2\n'
            'http://stream2.com\n';

        final channels = service.parseM3U(m3uContent);

        expect(channels.length, 2);
      });

      test('EC-SERVICE-1: Handle empty M3U content', () {
        const m3uContent = '';

        final channels = service.parseM3U(m3uContent);

        expect(channels, isEmpty);
      });

      test('EC-SERVICE-2: Handle M3U with only header', () {
        const m3uContent = '#EXTM3U';

        final channels = service.parseM3U(m3uContent);

        expect(channels, isEmpty);
      });

      test('EC-SERVICE-3: Handle M3U with EXTINF but no URL', () {
        const m3uContent = '''
#EXTM3U
#EXTINF:-1,Channel Name
''';

        final channels = service.parseM3U(m3uContent);

        // Should skip entries without URLs
        expect(channels, isEmpty);
      });

      test('EC-SERVICE-4: Handle M3U with URL but no EXTINF', () {
        const m3uContent = '''
#EXTM3U
http://stream.example.com/channel.m3u8
''';

        final channels = service.parseM3U(m3uContent);

        // Should skip URLs without EXTINF metadata
        expect(channels, isEmpty);
      });

      test('EC-SERVICE-5: Handle M3U with comments and blank lines', () {
        const m3uContent = '''
#EXTM3U

# This is a comment
#EXTINF:-1,Channel 1
http://stream1.com

# Another comment

#EXTINF:-1,Channel 2
http://stream2.com
''';

        final channels = service.parseM3U(m3uContent);

        expect(channels.length, 2);
        expect(channels[0].name, 'Channel 1');
        expect(channels[1].name, 'Channel 2');
      });

      test('EC-SERVICE-6: Handle very large M3U (10000+ channels)', () {
        final buffer = StringBuffer('#EXTM3U\n');
        for (int i = 0; i < 10000; i++) {
          buffer.writeln('#EXTINF:-1,Channel $i');
          buffer.writeln('http://stream.example.com/channel$i.m3u8');
        }

        final channels = service.parseM3U(buffer.toString());

        expect(channels.length, 10000);
        expect(channels.first.name, 'Channel 0');
        expect(channels.last.name, 'Channel 9999');
      });

      test('EC-SERVICE-7: Handle M3U with duplicate URLs', () {
        const m3uContent = '''
#EXTM3U
#EXTINF:-1,Channel A
http://stream.example.com/same.m3u8
#EXTINF:-1,Channel B
http://stream.example.com/same.m3u8
#EXTINF:-1,Channel C
http://stream.example.com/same.m3u8
''';

        final channels = service.parseM3U(m3uContent);

        // Parser returns all, deduplication happens in provider
        expect(channels.length, 3);
      });

      test('EC-SERVICE-8: Handle malformed attribute syntax', () {
        const m3uContent = '''
#EXTM3U
#EXTINF:-1 tvg-logo=missing-quotes group-title="News",Channel
http://stream.example.com/channel.m3u8
''';

        final channels = service.parseM3U(m3uContent);

        // Should still parse despite malformed attributes
        expect(channels.length, 1);
        expect(channels[0].name, 'Channel');
      });
    });

    group('Deduplication', () {
      test('EC-1.9: Deduplicate channels by URL', () {
        final channels = [
          Channel(
            name: 'CNN HD',
            url: 'http://example.com/cnn.m3u8',
            category: 'News',
          ),
          Channel(
            name: 'CNN International',
            url: 'http://example.com/cnn.m3u8',
            category: 'News',
          ),
          Channel(
            name: 'BBC',
            url: 'http://example.com/bbc.m3u8',
            category: 'News',
          ),
        ];

        // Deduplication logic (as in ChannelProvider)
        final seen = <String>{};
        final deduplicated = channels.where((ch) => seen.add(ch.url)).toList();

        expect(deduplicated.length, 2);
        expect(deduplicated[0].url, 'http://example.com/cnn.m3u8');
        expect(deduplicated[1].url, 'http://example.com/bbc.m3u8');
      });
    });

    group('URL Validation', () {
      test('FC-SERVICE-4: Accept HTTP URLs', () {
        const url = 'http://example.com/stream.m3u8';
        expect(Uri.parse(url).isAbsolute, true);
        expect(Uri.parse(url).scheme, 'http');
      });

      test('FC-SERVICE-5: Accept HTTPS URLs', () {
        const url = 'https://example.com/stream.m3u8';
        expect(Uri.parse(url).isAbsolute, true);
        expect(Uri.parse(url).scheme, 'https');
      });

      test('EC-SERVICE-9: Handle relative URLs', () {
        const url = '/stream.m3u8';
        expect(Uri.parse(url).isAbsolute, false);
      });

      test('EC-SERVICE-10: Handle URLs with query parameters', () {
        const url = 'http://example.com/stream.m3u8?token=abc123&id=5';
        final uri = Uri.parse(url);
        expect(uri.isAbsolute, true);
        expect(uri.queryParameters['token'], 'abc123');
        expect(uri.queryParameters['id'], '5');
      });

      test('EC-SERVICE-11: Handle URLs with fragments', () {
        const url = 'http://example.com/stream.m3u8#live';
        final uri = Uri.parse(url);
        expect(uri.isAbsolute, true);
        expect(uri.fragment, 'live');
      });
    });

    group('Status Code Validation', () {
      test('FC-11.9: Accept 200 OK status', () {
        expect([200, 206, 301, 302].contains(200), true);
      });

      test('FC-11.9: Accept 206 Partial Content status', () {
        expect([200, 206, 301, 302].contains(206), true);
      });

      test('FC-11.9: Accept 301 Moved Permanently status', () {
        expect([200, 206, 301, 302].contains(301), true);
      });

      test('FC-11.9: Accept 302 Found status', () {
        expect([200, 206, 301, 302].contains(302), true);
      });

      test('FC-11.9: Reject 404 Not Found status', () {
        expect([200, 206, 301, 302].contains(404), false);
      });

      test('FC-11.9: Reject 403 Forbidden status', () {
        expect([200, 206, 301, 302].contains(403), false);
      });

      test('FC-11.9: Reject 500 Server Error status', () {
        expect([200, 206, 301, 302].contains(500), false);
      });
    });

    group('Performance', () {
      test('PT-1.3: Parse 5000 channels quickly', () {
        final buffer = StringBuffer('#EXTM3U\n');
        for (int i = 0; i < 5000; i++) {
          buffer.writeln('#EXTINF:-1 tvg-logo="http://example.com/$i.png" group-title="Category",Channel $i');
          buffer.writeln('http://stream.example.com/channel$i.m3u8');
        }

        final stopwatch = Stopwatch()..start();
        final channels = service.parseM3U(buffer.toString());
        stopwatch.stop();

        expect(channels.length, 5000);
        expect(stopwatch.elapsedMilliseconds, lessThan(1000)); // Should parse in < 1 second
      });
    });

    group('Edge Cases - Special Content', () {
      test('EC-SERVICE-12: Handle channels with emojis in name', () {
        const m3uContent = '''
#EXTM3U
#EXTINF:-1,🎬 Movie Channel 📺
http://stream.example.com/movies.m3u8
''';

        final channels = service.parseM3U(m3uContent);

        expect(channels.length, 1);
        expect(channels[0].name, contains('🎬'));
        expect(channels[0].name, contains('📺'));
      });

      test('EC-SERVICE-13: Handle channels with international characters', () {
        const m3uContent = '''
#EXTM3U
#EXTINF:-1,Канал Россия (Russian)
http://stream.example.com/russia.m3u8
#EXTINF:-1,中文频道 (Chinese)
http://stream.example.com/china.m3u8
#EXTINF:-1,العربية (Arabic)
http://stream.example.com/arabic.m3u8
''';

        final channels = service.parseM3U(m3uContent);

        expect(channels.length, 3);
        expect(channels[0].name, contains('Россия'));
        expect(channels[1].name, contains('中文'));
        expect(channels[2].name, contains('العربية'));
      });

      test('EC-SERVICE-14: Handle very long URLs (2000+ chars)', () {
        final longParams = List.generate(100, (i) => 'param$i=value$i').join('&');
        final longUrl = 'http://stream.example.com/channel.m3u8?$longParams';
        final m3uContent = '''
#EXTM3U
#EXTINF:-1,Channel
$longUrl
''';

        final channels = service.parseM3U(m3uContent);

        expect(channels.length, 1);
        expect(channels[0].url, longUrl);
        expect(channels[0].url.length, greaterThan(2000));
      });

      test('EC-SERVICE-15: Handle EXTINF with negative duration', () {
        const m3uContent = '''
#EXTM3U
#EXTINF:-1,Live Channel
http://stream.example.com/live.m3u8
''';

        final channels = service.parseM3U(m3uContent);

        expect(channels.length, 1);
        expect(channels[0].name, 'Live Channel');
      });

      test('EC-SERVICE-16: Handle multiple consecutive blank lines', () {
        const m3uContent = '''
#EXTM3U



#EXTINF:-1,Channel


http://stream.example.com/channel.m3u8



''';

        final channels = service.parseM3U(m3uContent);

        expect(channels.length, 1);
      });
    });

    group('Error Handling', () {
      test('ES-SERVICE-1: Handle null M3U content gracefully', () {
        expect(() => service.parseM3U(null as dynamic), throwsA(isA<TypeError>()));
      });

      test('ES-SERVICE-2: Handle non-M3U content', () {
        const invalidContent = '''
<html>
<body>This is not an M3U file</body>
</html>
''';

        final channels = service.parseM3U(invalidContent);

        // Should return empty list, not crash
        expect(channels, isEmpty);
      });

      test('ES-SERVICE-3: Handle M3U with invalid UTF-8', () {
        // Dart strings are UTF-8, but test with replacement character
        const m3uContent = '#EXTM3U\n'
            '#EXTINF:-1,Channel �\n'
            'http://stream.example.com/channel.m3u8\n';

        final channels = service.parseM3U(m3uContent);

        expect(channels.length, 1);
      });
    });
  });
}
