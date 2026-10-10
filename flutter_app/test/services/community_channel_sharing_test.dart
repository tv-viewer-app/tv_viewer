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
