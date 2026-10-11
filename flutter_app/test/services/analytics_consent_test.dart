import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tv_viewer/services/analytics_service.dart';
import 'package:tv_viewer/services/settings_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('settings apply consent immediately and discard revoked upload retries',
      () async {
    SharedPreferences.setMockInitialValues({});
    final pending = Completer<http.Response>();
    var requests = 0;
    final client = MockClient((request) {
      requests++;
      return pending.future;
    });
    final analytics = AnalyticsService.instance;
    final settings = SettingsService.instance;

    await http.runWithClient(() async {
      await settings.initialize();
      await analytics.initialize();
      expect(analytics.isOptedIn, isFalse);

      await settings.setAnalyticsEnabled(true);
      expect(analytics.isOptedIn, isTrue);
      await analytics.trackEvent('test_event');
      expect(analytics.queueLength, 1);
      final upload = analytics.flush();
      await Future<void>.delayed(Duration.zero);

      await analytics.trackEvent('queued_event');
      await settings.setAnalyticsEnabled(false);
      expect(analytics.isOptedIn, isFalse);
      expect(await settings.getAnalyticsEnabled(), isFalse);
      expect(analytics.queueLength, 0);
      await analytics.trackEvent('must_not_collect');
      expect(analytics.queueLength, 0);

      await settings.setAnalyticsEnabled(true);
      pending.complete(http.Response('', 500));
      await upload;
      expect(analytics.queueLength, 0);
      expect(requests, 1);
      await settings.setAnalyticsEnabled(false);
      await analytics.dispose();
    }, () => client);
  });
}
