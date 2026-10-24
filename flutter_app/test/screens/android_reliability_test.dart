import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tv_viewer/screens/repo_management_screen.dart';
import 'package:tv_viewer/screens/statistics_screen.dart';
import 'package:tv_viewer/utils/logger_service.dart';
import 'package:tv_viewer/utils/prefs_lock.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('plugins.flutter.io/shared_preferences');
  const cacheKey = 'stats_cache_public_v3';
  const cacheTimeKey = 'stats_cache_public_v3_time';
  late Map<String, Object> stored;
  bool failWrites = false;

  setUp(() {
    SharedPreferences.resetStatic();
    stored = {};
    failWrites = false;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      final arguments = call.arguments as Map?;
      switch (call.method) {
        case 'getAll':
          return Map<String, Object>.from(stored);
        case 'remove':
          stored.remove(arguments!['key']);
          return true;
        case 'setString':
        case 'setInt':
          if (failWrites) {
            throw PlatformException(
              code: 'write_failed',
              message: 'No space left on device',
            );
          }
          stored[arguments!['key'] as String] = arguments['value'] as Object;
          return true;
        default:
          throw MissingPluginException(call.method);
      }
    });
  });

  tearDown(() async {
    await logger.dispose();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });

  Future<void> showStatistics(
    WidgetTester tester,
    http.Client client,
  ) async {
    await http.runWithClient(() async {
      await tester.pumpWidget(
        const MaterialApp(home: StatisticsScreen()),
      );
      await tester.pumpAndSettle();
    }, () => client);
  }

  http.Client statisticsClient() => MockClient((request) async {
        if (request.url.path.endsWith('mv_daily_active_users')) {
          return http.Response(
            '[{"platform":"android","total_events":7,"unique_devices":1}]',
            200,
          );
        }
        return http.Response('[]', 200);
      });

  for (final raw in ['', '{', '[]', 'null', '{"total_events":"invalid"}']) {
    testWidgets('recovers from a fresh invalid statistics cache: $raw',
        (tester) async {
      stored['flutter.$cacheKey'] = raw;
      stored['flutter.$cacheTimeKey'] = DateTime.now().millisecondsSinceEpoch;

      await showStatistics(tester, statisticsClient());

      expect(tester.takeException(), isNull);
      expect(find.text('7'), findsOneWidget);
      expect(find.text('Unable to load statistics'), findsNothing);
      expect(jsonDecode(stored['flutter.$cacheKey']! as String), isA<Map>());
    });
  }

  testWidgets('invalid stale cache does not throw during network failure',
      (tester) async {
    stored['flutter.$cacheKey'] = '';
    stored['flutter.$cacheTimeKey'] = 0;

    await showStatistics(
      tester,
      MockClient((_) async => throw const SocketException('Offline')),
    );

    expect(tester.takeException(), isNull);
    expect(find.text('Unable to load statistics'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);
    expect(stored.containsKey('flutter.$cacheKey'), isFalse);
  });

  testWidgets('valid stale cache remains available offline', (tester) async {
    stored['flutter.$cacheKey'] = '{"total_events":17,"total_plays":0}';
    stored['flutter.$cacheTimeKey'] = 0;

    await showStatistics(
      tester,
      MockClient((_) async => throw const SocketException('Offline')),
    );

    expect(tester.takeException(), isNull);
    expect(find.text('17'), findsOneWidget);
    expect(find.text('Unable to load statistics'), findsNothing);
  });

  testWidgets('valid fresh cache does not require a network request',
      (tester) async {
    stored['flutter.$cacheKey'] = '{"total_events":17,"total_plays":0}';
    stored['flutter.$cacheTimeKey'] = DateTime.now().millisecondsSinceEpoch;
    var requests = 0;

    await showStatistics(tester, MockClient((_) async {
      requests++;
      return http.Response('', 500);
    }));

    expect(tester.takeException(), isNull);
    expect(find.text('17'), findsOneWidget);
    expect(requests, 0);
  });

  testWidgets('empty server response shows retry instead of throwing',
      (tester) async {
    await showStatistics(
      tester,
      MockClient((_) async => http.Response('', 200)),
    );

    expect(tester.takeException(), isNull);
    expect(find.text('Unable to load statistics'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);
  });

  testWidgets('statistics remain visible when cache writes run out of space',
      (tester) async {
    failWrites = true;

    await showStatistics(tester, statisticsClient());

    expect(tester.takeException(), isNull);
    expect(find.text('7'), findsOneWidget);
    expect(
      find.text('Statistics loaded, but could not be saved on this device.'),
      findsOneWidget,
    );
  });

  testWidgets('repository save finishing after disposal does not setState',
      (tester) async {
    stored['flutter.custom_repos'] =
        '["https://example.test/a.m3u","https://example.test/b.m3u"]';
    await tester.pumpWidget(
      const MaterialApp(home: RepoManagementScreen()),
    );
    await tester.pumpAndSettle();

    final release = Completer<void>();
    final locked = PrefsLock.instance.synchronized(() => release.future);
    try {
      await tester.tap(find.byIcon(Icons.delete_outline).first);
      await tester.pump();
      await tester.pumpWidget(const MaterialApp(home: SizedBox.shrink()));
    } finally {
      release.complete();
      await locked;
    }
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(
      jsonDecode(stored['flutter.custom_repos']! as String),
      ['https://example.test/b.m3u'],
    );
  });

  testWidgets('repository undo left in messenger is safe after route disposal',
      (tester) async {
    stored['flutter.custom_repos'] =
        '["https://example.test/a.m3u","https://example.test/b.m3u"]';
    final navigatorKey = GlobalKey<NavigatorState>();
    await tester.pumpWidget(MaterialApp(
      navigatorKey: navigatorKey,
      home: const Scaffold(body: Text('Home')),
    ));
    navigatorKey.currentState!.push(MaterialPageRoute<void>(
      builder: (_) => const RepoManagementScreen(),
    ));
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.delete_outline).first);
    await tester.pumpAndSettle();
    navigatorKey.currentState!.pop();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Undo'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(
      jsonDecode(stored['flutter.custom_repos']! as String),
      ['https://example.test/b.m3u'],
    );
  });
}
