/// Android distribution policy shared by GitHub, Google Play, and F-Droid.
///
/// Store-specific signing and packaging must not change product behavior.
abstract final class AppDistribution {
  static const bool allowsSelfUpdate = false;
  static const bool allowsSupabase = true;
  static const bool requiresAgeConfirmation = true;
}
