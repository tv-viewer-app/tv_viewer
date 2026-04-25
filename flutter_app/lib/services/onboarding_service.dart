import 'package:shared_preferences/shared_preferences.dart';

/// Service for managing first-time user onboarding experience
class OnboardingService {
  static const String _onboardingKey = 'has_completed_onboarding';
  static const String _tooltipShownPrefix = 'tooltip_shown_';

  /// Check if the user has completed onboarding
  static Future<bool> hasCompletedOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_onboardingKey) ?? false;
  }

  /// Mark onboarding as complete
  static Future<void> completeOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_onboardingKey, true);
  }

  /// Reset onboarding (for testing or user request)
  static Future<void> resetOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_onboardingKey, false);
    
    // Clear all individual tooltip states
    final keys = prefs.getKeys();
    for (final key in keys) {
      if (key.startsWith(_tooltipShownPrefix)) {
        await prefs.remove(key);
      }
    }
  }

  /// Check if a specific tooltip has been shown
  static Future<bool> hasShownTooltip(String tooltipId) async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool('$_tooltipShownPrefix$tooltipId') ?? false;
  }

  /// Mark a specific tooltip as shown
  static Future<void> markTooltipAsShown(String tooltipId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('$_tooltipShownPrefix$tooltipId', true);
  }

  /// Get list of tooltips that should be shown on home screen
  /// Returns empty list if onboarding is complete
  static Future<List<String>> getTooltipsToShow() async {
    if (await hasCompletedOnboarding()) {
      return [];
    }

    final tooltips = <String>[];
    final allTooltips = ['scan_button', 'filter_area', 'favorite_button'];

    for (final tooltipId in allTooltips) {
      if (!await hasShownTooltip(tooltipId)) {
        tooltips.add(tooltipId);
      }
    }

    return tooltips;
  }

  /// Check if this is the first app launch
  static Future<bool> isFirstLaunch() async {
    return !await hasCompletedOnboarding();
  }
}
