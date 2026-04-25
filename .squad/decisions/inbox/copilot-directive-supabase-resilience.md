### 2026-03-26T21:45:00Z: User directive — Supabase resilience model
**By:** tv-viewer-app (via Copilot)
**What:** Supabase is an accelerator, NOT a dependency. The app must function fully if the database is down — scan channels locally and save to local cache. Supabase only helps reduce wasteful re-scans of channels already known-working by other clients. Clients should: (1) fetch known-working from Supabase on startup, (2) background scan only non-working/unchecked channels, (3) report channel failures back to Supabase. If Supabase is unreachable, fall back to full local scanning.
**Why:** User request — core architectural principle for reliability
