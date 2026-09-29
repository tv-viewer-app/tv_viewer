/// Compile-time distribution policy.
///
/// F-Droid builds pass `--dart-define=FDROID_BUILD=true`. Keeping these
/// restrictions in one place prevents store-specific behavior from drifting.
abstract final class AppDistribution {
  static const bool isFdroid = bool.fromEnvironment(
    'FDROID_BUILD',
    defaultValue: false,
  );

  static const bool allowsSelfUpdate = !isFdroid;
  static const bool allowsSupabase = !isFdroid;
  static const bool requiresAgeConfirmation = !isFdroid;
}
