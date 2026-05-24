-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  TV Viewer — Supabase migration v2.16.1 (linter cleanup)                ║
-- ║                                                                           ║
-- ║  Addresses the Supabase database-linter findings raised after v2.16.0:  ║
-- ║                                                                           ║
-- ║   1. channel_votes: RLS enabled but no policy → add explicit SELECT      ║
-- ║      policy for anon (column-level GRANT still hides device_id, id).    ║
-- ║   2. tv_viewer_schema_version(): missing SET search_path → add it.      ║
-- ║   3. channel_sources.csrc_anon_update used USING (true) for UPDATE →    ║
-- ║      revoke entirely (no client writes this table; only the admin       ║
-- ║      populate_supabase.py with service_role does).                      ║
-- ║   4. Admin SECURITY DEFINER functions (cleanup_old_data, db_health,    ║
-- ║      refresh_analytics_views, truncate_channels, report_source_health) ║
-- ║      callable by authenticated role → revoke, keep service_role only.  ║
-- ║                                                                           ║
-- ║  NOT changed (intentional, accepted risk):                              ║
-- ║   • report_channel_broken / report_channel_working /                    ║
-- ║     promote_channel_source remain anon-executable — this is by design   ║
-- ║     (anonymous IPTV app, no user accounts). The functions enforce      ║
-- ║     per-device rate limits internally.                                  ║
-- ║                                                                           ║
-- ║  This file is IDEMPOTENT — safe to re-run.                              ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝


-- ── 1. channel_votes: add explicit SELECT policy for anon ────────────────
-- Column-level GRANT on (url_hash, vote, created_at) restricts which columns
-- come back; this policy unlocks row visibility. device_id and id remain
-- hidden because they were never granted at the column level.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'channel_votes'
          AND policyname = 'cv_anon_select'
    ) THEN
        EXECUTE 'CREATE POLICY cv_anon_select ON channel_votes FOR SELECT TO anon USING (true)';
    END IF;
END $$;


-- ── 2. tv_viewer_schema_version: lock down search_path ───────────────────
-- Mutable search_path on a function (esp. one callable by anon) lets a
-- privileged caller temporarily change search_path and trick the function
-- into hitting an attacker-controlled object. Pin it to a fixed schema list.

CREATE OR REPLACE FUNCTION tv_viewer_schema_version()
RETURNS TEXT
LANGUAGE sql
IMMUTABLE
SET search_path = pg_catalog, public
AS $$ SELECT '2.16.1'::text $$;

REVOKE ALL ON FUNCTION tv_viewer_schema_version() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tv_viewer_schema_version() TO anon, authenticated;


-- ── 3. channel_sources: revoke the unused anon UPDATE policy ─────────────
-- No client code writes channel_sources directly. The admin script
-- (scripts/populate_supabase.py) uses the service_role key, which bypasses
-- RLS entirely. The csrc_anon_update policy with USING (true) was a
-- catalog-wide write vector exposed to every APK and Docker image.

DROP POLICY IF EXISTS csrc_anon_update ON public.channel_sources;

-- Also drop INSERT/DELETE if they exist anon-side — service_role bypasses RLS
-- and is the only legitimate writer.
DROP POLICY IF EXISTS csrc_anon_insert ON public.channel_sources;
DROP POLICY IF EXISTS csrc_anon_delete ON public.channel_sources;

-- Keep SELECT for anon: clients need to read source health data.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'channel_sources'
          AND policyname = 'csrc_anon_select'
    ) THEN
        EXECUTE 'CREATE POLICY csrc_anon_select ON channel_sources FOR SELECT TO anon USING (true)';
    END IF;
END $$;


-- ── 4. Admin SECURITY DEFINER functions: revoke from authenticated ───────
-- These functions were granted to `authenticated` at some point in the
-- migration history, but they are admin-only (truncate data, refresh
-- materialized views, etc.). Anon was already revoked; remove authenticated
-- so only service_role (used by GitHub Actions, populate scripts, dashboards)
-- can call them.

DO $$
DECLARE
    fn_signature TEXT;
    admin_fns TEXT[] := ARRAY[
        'cleanup_old_data()',
        'db_health()',
        'refresh_analytics_views()',
        'truncate_channels()',
        'report_source_health(text, text, integer)'
    ];
BEGIN
    FOREACH fn_signature IN ARRAY admin_fns LOOP
        BEGIN
            EXECUTE format('REVOKE EXECUTE ON FUNCTION public.%s FROM PUBLIC, anon, authenticated', fn_signature);
            EXECUTE format('GRANT EXECUTE ON FUNCTION public.%s TO service_role', fn_signature);
        EXCEPTION WHEN undefined_function THEN
            -- Function not present in this database; skip silently.
            NULL;
        END;
    END LOOP;
END $$;


-- ── 5. Bump the schema version marker ────────────────────────────────────
-- The doctor script will report 2.16.1 once this migration is applied.
-- (Already updated above when we recreated tv_viewer_schema_version.)
