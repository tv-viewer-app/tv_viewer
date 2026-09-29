import 'package:flutter_test/flutter_test.dart';
import 'package:tv_viewer/config/app_distribution.dart';
import 'package:tv_viewer/services/m3u_service.dart';

void main() {
  test('standard builds retain standard distribution capabilities', () {
    expect(AppDistribution.isFdroid, isFalse);
    expect(AppDistribution.allowsSelfUpdate, isTrue);
    expect(AppDistribution.allowsSupabase, isTrue);
    expect(AppDistribution.requiresAgeConfirmation, isTrue);
    expect(M3UService.defaultRepositories.length, greaterThan(1));
    expect(M3UService.adultRepositories, isNotEmpty);
    expect(M3UService.customChannels, isNotEmpty);
  });
}
