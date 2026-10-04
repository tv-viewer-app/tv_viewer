/// Public Supabase client configuration.
///
/// These values are intentionally included in the app. The publishable key is
/// not a secret; Supabase row-level security is the authorization boundary.
abstract final class BackendConfig {
  static const String supabaseUrl =
      'https://cdtxpefohpwtusmqengu.supabase.co';
  static const String supabasePublishableKey =
      'sb_publishable_hp_c_ek7bYv33-fLqmgvnw_KS9T33Oi';
}
