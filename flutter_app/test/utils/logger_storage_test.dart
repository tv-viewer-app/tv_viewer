import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tv_viewer/utils/logger_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('plugins.flutter.io/path_provider');
  late Directory directory;
  late File blockedTempDirectory;

  setUp(() async {
    directory = await Directory.systemTemp.createTemp('tv_viewer_logs_test_');
    final logs = await Directory('${directory.path}/logs').create();
    await File('${logs.path}/app_log_existing.txt').writeAsString('Existing log');
    blockedTempDirectory = await File('${directory.path}/not_a_directory')
        .writeAsString('Cannot export inside a regular file');
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      switch (call.method) {
        case 'getApplicationDocumentsDirectory':
          return directory.path;
        case 'getTemporaryDirectory':
          return blockedTempDirectory.path;
        default:
          throw MissingPluginException(call.method);
      }
    });
  });

  tearDown(() async {
    await logger.dispose();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
    await directory.delete(recursive: true);
  });

  test('export surfaces filesystem failure instead of claiming no logs', () async {
    await logger.initialize();

    await expectLater(logger.exportLogs(), throwsA(isA<FileSystemException>()));
    expect(
      await File('${directory.path}/logs/app_log_existing.txt').readAsString(),
      contains('Existing log'),
    );
  });
}
