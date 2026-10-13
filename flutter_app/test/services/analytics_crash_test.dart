import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tv_viewer/services/analytics_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('crashes report a sanitized frame rather than the release stack banner',
      () async {
    SharedPreferences.setMockInitialValues({});
    final uploads = <Map<String, dynamic>>[];
    final client = MockClient((request) async {
      final batch = jsonDecode(request.body) as List<dynamic>;
      uploads.addAll(batch.cast<Map<String, dynamic>>());
      return http.Response('', 201);
    });
    final analytics = AnalyticsService.instance;

    await http.runWithClient(() async {
      await analytics.initialize();
      await analytics.trackCrash(StateError('test'), StackTrace.empty);
      expect(uploads, isEmpty);
      await analytics.setEnabled(true);

      final stacks = [
        '\n*** *** *** ***\n#00 pc 00001234 /private/libapp.so\n#01 pc 00005678',
        '#0 Player.build (https://private.example/source.dart:12)\n#1 main',
        'single diagnostic line',
        '',
      ];
      for (final stack in stacks) {
        await analytics.trackCrash(
          StateError('test'),
          StackTrace.fromString(stack),
        );
      }

      final frames = uploads.map(
        (event) => (event['event_data'] as Map<String, dynamic>)['stack_first_line'],
      ).toList();
      expect(frames[0], startsWith('#00 pc 00001234'));
      expect(frames[0], isNot(contains('/private/')));
      expect(frames[1], startsWith('#0 Player.build'));
      expect(frames[1], isNot(contains('private.example')));
      expect(frames[2], 'single diagnostic line');
      expect(frames[3], '');
      await analytics.setEnabled(false);
      await analytics.dispose();
    }, () => client);
  });
}
