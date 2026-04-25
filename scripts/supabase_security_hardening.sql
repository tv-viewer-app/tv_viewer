-- =============================================================================
-- TV Viewer — Supabase Security Hardening
-- =============================================================================
-- Run in Supabase SQL Editor: https://supabase.com/dashboard/project/cdtxpefohpwtusmqengu/sql
--
-- Fixes identified by Supabase Security Advisor + manual audit (2026-03-11):
--
--   [CRITICAL] v_channels_with_sources — SECURITY DEFINER view (Advisor error)
--   [CRITICAL] truncate_channels()     — SECURITY DEFINER callable by anon
--   [CRITICAL] channels_delete policy  — anon can DELETE any channel row
--   [HIGH]     ae_anon_select          — anon can read all analytics events
--   [HIGH]     refresh_analytics_views()— SECURITY DEFINER callable by anon
--   [HIGH]     cleanup_old_data()      — SECURITY DEFINER callable by anon
--   [HIGH]     db_health()             — SECURITY DEFINER callable by anon
--   [MEDIUM]   report_source_health()  — SECURITY DEFINER callable by anon
--
-- Safe to re-run (uses DROP IF EXISTS / DO blocks).
-- =============================================================================


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  FIX 1: v_channels_with_sources — SECURITY INVOKER (not DEFINER)        ║
-- ║  Supabase Security Advisor: security_definer_view error                  ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

CREATE OR REPLACE VIEW v_channels_with_sources
WITH (security_invoker = true)
AS
SELECT
    c.url_hash AS channel_hash,
    c.name,
    c.normalized_name,
    c.category,
    c.country,
    c.logo,
    c.description,
    c.epg_id,
    c.media_type,
    c.is_adult,
    COALESCE(
        (SELECT jsonb_agg(
            jsonb_build_object(
                'url', s.url,
                'url_hash', s.url_hash,
                'status', s.status,
                'reliability', s.reliability,
                'response_time_ms', s.response_time_ms,
                'last_checked', s.last_checked,
                'checked_by', s.checked_by
            ) ORDER BY
                CASE s.status WHEN 'working' THEN 0 WHEN 'unchecked' THEN 1 ELSE 2 END,
                s.reliability DESC,
                s.response_time_ms ASC NULLS LAST
        )
        FROM channel_sources s
        WHERE s.channel_hash = c.url_hash
        ),
        '[]'::jsonb
    ) AS sources
FROM channels c;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  FIX 2: Remove anon DELETE on channels table                            ║
-- ║  Only service_role (admin scripts) should delete channels.              ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

DROP POLICY IF EXISTS "channels_delete" ON channels;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  FIX 3: Remove anon SELECT on analytics_events (write-only for clients) ║
-- ║  Analytics data should only be readable by service_role (dashboards).    ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

DROP POLICY IF EXISTS "ae_anon_select" ON analytics_events;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  FIX 4: Restrict SECURITY DEFINER functions to service_role only        ║
-- ║  These functions bypass RLS — anon must not be able to call them.       ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- 4a. truncate_channels() — wipes channels + channel_sources
REVOKE EXECUTE ON FUNCTION truncate_channels() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION truncate_channels() TO service_role;

-- 4b. report_source_health() — updates channel_sources bypassing RLS
REVOKE EXECUTE ON FUNCTION report_source_health(text, text, integer) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION report_source_health(text, text, integer) TO service_role;

-- 4c. refresh_analytics_views() — refreshes materialized views
REVOKE EXECUTE ON FUNCTION refresh_analytics_views() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION refresh_analytics_views() TO service_role;

-- 4d. cleanup_old_data() — deletes old analytics/status rows
REVOKE EXECUTE ON FUNCTION cleanup_old_data() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION cleanup_old_data() TO service_role;

-- 4e. db_health() — exposes internal table counts
REVOKE EXECUTE ON FUNCTION db_health() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION db_health() TO service_role;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  VERIFICATION — Run after applying to confirm fixes                     ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- Check: no SECURITY DEFINER views remain in public schema
-- (Should return 0 rows after fix)
SELECT viewname
FROM pg_views
WHERE schemaname = 'public'
  AND definition LIKE '%security_barrier%';

-- Check: anon policies on analytics_events (should only be INSERT)
SELECT policyname, cmd
FROM pg_policies
WHERE tablename = 'analytics_events' AND roles @> ARRAY['anon']::name[];

-- Check: no DELETE policy on channels for anon
SELECT policyname, cmd
FROM pg_policies
WHERE tablename = 'channels' AND cmd = 'DELETE' AND roles @> ARRAY['anon']::name[];

-- Check: function privileges (should show only service_role)
SELECT routine_name, grantee, privilege_type
FROM information_schema.routine_privileges
WHERE routine_schema = 'public'
  AND routine_name IN (
    'truncate_channels', 'report_source_health',
    'refresh_analytics_views', 'cleanup_old_data', 'db_health'
  )
ORDER BY routine_name, grantee;


-- =============================================================================
-- DONE. After running:
--   1. Re-check Supabase Security Advisor — error should be cleared
--   2. populate_supabase.py must use SUPABASE_SERVICE_ROLE_KEY for --clean
--   3. App clients (anon key) are unaffected — they only INSERT + SELECT
-- =============================================================================
