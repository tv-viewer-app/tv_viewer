# Security Notes

## Supabase API Keys
- Publishable key (safe to embed): configured in config.py, docker-compose.yml
- Secret key (server-only): must be provided via SUPABASE_SERVICE_ROLE_KEY env var
- Never commit secret keys to source code

## GitHub Actions
- First-party actions (actions/*) use tag references — acceptable risk
- Third-party actions should be pinned to commit SHAs (in progress)
- Secret scanning enabled via CodeQL workflow

## Key Rotation
- Last rotation: 2026-07-01 (migrated from JWT to API keys)
- Publishable key: sb_publishable_hp_c_ek7bYv33-fLqmgvnw_KS9T33Oi
- Secret key: stored in GitHub Actions secrets only
