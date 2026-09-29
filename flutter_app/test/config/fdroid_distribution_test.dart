import 'package:flutter_test/flutter_test.dart';
import 'package:tv_viewer/config/app_distribution.dart';
import 'package:tv_viewer/services/m3u_service.dart';

void main() {
  test(
    'F-Droid build disables restricted services and sources',
    () {
      expect(AppDistribution.isFdroid, isTrue);
      expect(AppDistribution.allowsSelfUpdate, isFalse);
      expect(AppDistribution.allowsSupabase, isFalse);
      expect(AppDistribution.requiresAgeConfirmation, isFalse);
      expect(
        M3UService.defaultRepositories,
        const ['https://iptv-org.github.io/iptv/index.m3u'],
      );
      expect(M3UService.adultRepositories, isEmpty);
      expect(M3UService.customChannels, isEmpty);
    },
    skip: AppDistribution.isFdroid
        ? false
        : 'Run with --dart-define=FDROID_BUILD=true',
  );
}
