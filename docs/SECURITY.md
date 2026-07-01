# Security Notes

## Supabase API Keys
- Use the new Supabase API key format instead of legacy JWT-style keys.
- Publishable keys (`sb_publishable_*`) are client-safe and may be supplied via
  `SUPABASE_ANON_KEY` for backward compatibility with existing code paths.
- Secret keys are server-only and must be provided through
  `SUPABASE_SERVICE_ROLE_KEY`.
- Never commit secret keys, rotated secrets, or `.env` files to source control.

## Key Management Guidelines
- Store server-side secrets only in GitHub Actions secrets or local untracked
  environment configuration.
- Rotate keys immediately after any accidental exposure or suspected leak.
- Prefer environment variables over hardcoded values for operational secrets.
- Review workflow logs and release artifacts to ensure secrets are never echoed.

## GitHub Actions
- First-party actions (`actions/*`) use tag references — acceptable risk.
- Third-party actions should be pinned to commit SHAs whenever practical.
- Secret scanning remains enabled through repository security workflows.

## Rotation Status
- Last rotation completed: 2026-07-01.
- Legacy JWT-style tokens have been removed from tracked source files.
- Current server secret remains stored outside the repository.
