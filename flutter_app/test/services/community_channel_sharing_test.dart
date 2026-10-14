import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tv_viewer/services/shared_db_service.dart';
import 'package:tv_viewer/services/settings_service.dart';

void main() {
  final settings = SettingsService.instance;

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    await settings.initialize();
  });

  test('community channel sharing is off by default', () async {
    expect(await settings.getCommunityChannelSharingEnabled(), isFalse);
  });

  test('community channel sharing preference can be changed', () async {
    await settings.setCommunityChannelSharingEnabled(true);
    expect(await settings.getCommunityChannelSharingEnabled(), isTrue);

    await settings.setCommunityChannelSharingEnabled(false);
    expect(await settings.getCommunityChannelSharingEnabled(), isFalse);
  });

  test('analytics is off by default', () async {
    expect(await settings.getAnalyticsEnabled(), isFalse);
  });

  test('community health and playlist writes do not send requests by default',
      () async {
    expect(SharedDbService.isConfigured, isTrue);
    var requestCount = 0;
    final client = MockClient((_) async {
      requestCount++;
      return http.Response('[]', 200);
    });

    await http.runWithClient(() async {
      await SharedDbService.reportChannelStatus(
        url: 'https://example.test/live.m3u8',
        status: 'working',
      );
      await SharedDbService.reportBrokenChannel(
        SharedDbService.hashUrl('https://example.test/live.m3u8'),
      );
      final uploaded = await SharedDbService().uploadResults([
        ChannelResult(
          url: 'https://example.test/live.m3u8',
          isWorking: true,
          lastChecked: DateTime.utc(2026),
        ),
      ]);
      final contributed = await SharedDbService().contributeChannels([
        {
          'name': 'Example',
          'url': 'https://example.test/live.m3u8',
        },
      ]);

      expect(uploaded, isFalse);
      expect(contributed, 0);
    }, () => client);

    expect(requestCount, 0);
  });

  test('shared health reads are disabled by default', () async {
    var requestCount = 0;
    final client = MockClient((request) async {
      requestCount++;
      return http.Response(
        '[{"url_hash":"hash","status":"working",'
        '"last_checked":"2026-10-14T12:00:00Z","response_time_ms":120}]',
        200,
      );
    });

    final results = await http.runWithClient(
      () => SharedDbService().fetchRecentResults(),
      () => client,
    );

    expect(results, isEmpty);
    expect(requestCount, 0);
  });

  test('shared health results are available when community sharing is enabled',
      () async {
    await settings.setCommunityChannelSharingEnabled(true);
    final client = MockClient((request) async {
      expect(request.url.path, endsWith('/rest/v1/channel_status'));
      return http.Response(
        '[{"url_hash":"hash","status":"working",'
        '"last_checked":"2026-10-14T12:00:00Z","response_time_ms":120}]',
        200,
      );
    });

    final results = await http.runWithClient(
      () => SharedDbService().fetchRecentResults(),
      () => client,
    );

    expect(results.keys, contains('hash'));
    expect(results['hash']!.status, isTrue);
    expect(results['hash']!.responseTimeMs, 120);
  });

  test('public channel catalog remains available without community sharing',
      () async {
    var requestCount = 0;
    final client = MockClient((request) async {
      requestCount++;
      expect(request.url.path, endsWith('/rest/v1/channels'));
      return http.Response(
        '[{"url_hash":"hash","name":"Example","urls":'
        '["https://example.test/live.m3u8"],"category":"News",'
        '"country":"US","media_type":"TV","source":"test"}]',
        200,
      );
    });

    final channels = await http.runWithClient(
      () => SharedDbService().fetchChannels(),
      () => client,
    );

    expect(channels, hasLength(1));
    expect(channels.single['status'], 'unchecked');
    expect(channels.single['report_count'], 0);
    expect(requestCount, 1);
  });

  test('shared health feedback is fetched when community sharing is enabled',
      () async {
    await settings.setCommunityChannelSharingEnabled(true);
    final client = MockClient((request) async {
      if (request.url.path.endsWith('/channels')) {
        return http.Response(
          '[{"url_hash":"hash","name":"Example","urls":'
          '["https://example.test/live.m3u8"],"category":"News",'
          '"country":"US","media_type":"TV","source":"test"}]',
          200,
        );
      }
      expect(request.url.path, endsWith('/channel_status'));
      return http.Response(
        '[{"url_hash":"hash","status":"working","report_count":7,'
        '"working_reports":6,"broken_reports":1,"failed_reports":0}]',
        200,
      );
    });

    final channels = await http.runWithClient(
      () => SharedDbService().fetchChannels(),
      () => client,
    );

    expect(channels, hasLength(1));
    expect(channels.single['status'], 'working');
    expect(channels.single['report_count'], 7);
    expect(channels.single['working_reports'], 6);
  });

  test('explicit channel submission works while automatic sharing is off',
      () async {
    expect(await settings.getCommunityChannelSharingEnabled(), isFalse);
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path, endsWith('/rest/v1/channels'));
      expect(request.body, contains('https://example.test/live.m3u8'));
      return http.Response('', 201);
    });

    final submitted = await http.runWithClient(
      () => SharedDbService().contributeChannel({
        'name': 'Example',
        'url': 'https://example.test/live.m3u8',
      }),
      () => client,
    );

    expect(submitted, isTrue);
  });
}
