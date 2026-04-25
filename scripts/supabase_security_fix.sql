-- =============================================================================
-- TV Viewer — Supabase Security Hardening Migration
-- =============================================================================
-- Fixes 20 security warnings from Supabase linter:
--   • 6 functions: add search_path to prevent search path injection
--   • 6 materialized views: revoke anon/authenticated access
--   • 8 RLS policies: add field validation instead of bare WITH CHECK (true)
--
-- Safe to run multiple times (idempotent).
-- Run this in Supabase SQL Editor with service_role permissions.
-- =============================================================================


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  CATEGORY 1: Function Search Path Mutable (6 functions)                  ║
-- ║  FIX: Add SET search_path = public to prevent search path injection      ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- Function 1: report_source_health
ALTER FUNCTION public.report_source_health(text, text, integer)
    SET search_path = public;

-- Function 2: refresh_analytics_views
ALTER FUNCTION public.refresh_analytics_views()
    SET search_path = public;

-- Function 3: cleanup_old_data
ALTER FUNCTION public.cleanup_old_data()
    SET search_path = public;

-- Function 4: db_health
ALTER FUNCTION public.db_health()
    SET search_path = public;

-- Function 5: truncate_channels
ALTER FUNCTION public.truncate_channels()
    SET search_path = public;

-- Function 6: check_channel_status_rate (trigger function)
ALTER FUNCTION public.check_channel_status_rate()
    SET search_path = public;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  CATEGORY 2: Materialized Views in API (6 views)                        ║
-- ║  FIX: Revoke SELECT from anon and authenticated roles                    ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- These are internal analytics views — should not be exposed via REST API
REVOKE SELECT ON public.mv_daily_active_users FROM anon, authenticated;
REVOKE SELECT ON public.mv_top_channels FROM anon, authenticated;
REVOKE SELECT ON public.mv_client_platforms FROM anon, authenticated;
REVOKE SELECT ON public.mv_favorite_channels FROM anon, authenticated;
REVOKE SELECT ON public.mv_crash_summary FROM anon, authenticated;
REVOKE SELECT ON public.mv_engagement FROM anon, authenticated;

-- Grant to service_role only (for admin dashboards)
GRANT SELECT ON public.mv_daily_active_users TO service_role;
GRANT SELECT ON public.mv_top_channels TO service_role;
GRANT SELECT ON public.mv_client_platforms TO service_role;
GRANT SELECT ON public.mv_favorite_channels TO service_role;
GRANT SELECT ON public.mv_crash_summary TO service_role;
GRANT SELECT ON public.mv_engagement TO service_role;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  CATEGORY 3: RLS Policies Always True (8 policies)                      ║
-- ║  FIX: Add field validation and constraints instead of bare true          ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- ═════════════════════════════════════════════════════════════════════════════
-- TABLE: analytics_events
-- ═════════════════════════════════════════════════════════════════════════════

-- ae_anon_insert: Add validation for event_type and event_data
DROP POLICY IF EXISTS ae_anon_insert ON public.analytics_events;
CREATE POLICY ae_anon_insert ON public.analytics_events
  FOR INSERT TO anon
  WITH CHECK (
    -- Must provide required fields
    event_type IS NOT NULL AND
    length(event_type) <= 100 AND
    -- Validate event_data size if present
    (event_data IS NULL OR length(event_data::text) <= 10000)
  );


-- ═════════════════════════════════════════════════════════════════════════════
-- TABLE: channel_status
-- ═════════════════════════════════════════════════════════════════════════════

-- cs_anon_insert: Validate required fields and status values
DROP POLICY IF EXISTS cs_anon_insert ON public.channel_status;
CREATE POLICY cs_anon_insert ON public.channel_status
  FOR INSERT TO anon
  WITH CHECK (
    -- url_hash must be SHA-256 (64 hex chars)
    url_hash IS NOT NULL AND
    length(url_hash) = 64 AND
    url_hash ~ '^[a-f0-9]{64}$' AND
    -- status must be valid enum value
    status IS NOT NULL AND
    status IN ('working', 'failed', 'unchecked') AND
    -- response_time_ms must be reasonable (0-60 seconds)
    (response_time_ms IS NULL OR (response_time_ms >= 0 AND response_time_ms <= 60000))
  );

-- cs_anon_update: Only allow status updates, validate fields
DROP POLICY IF EXISTS cs_anon_update ON public.channel_status;
CREATE POLICY cs_anon_update ON public.channel_status
  FOR UPDATE TO anon
  USING (true)  -- Can see all rows for updates
  WITH CHECK (
    -- Same validation as INSERT
    url_hash IS NOT NULL AND
    length(url_hash) = 64 AND
    url_hash ~ '^[a-f0-9]{64}$' AND
    status IS NOT NULL AND
    status IN ('working', 'failed', 'unchecked') AND
    (response_time_ms IS NULL OR (response_time_ms >= 0 AND response_time_ms <= 60000))
  );


-- ═════════════════════════════════════════════════════════════════════════════
-- TABLE: channels
-- ═════════════════════════════════════════════════════════════════════════════

-- ch_anon_insert: Validate required fields
DROP POLICY IF EXISTS ch_anon_insert ON public.channels;
CREATE POLICY ch_anon_insert ON public.channels
  FOR INSERT TO anon
  WITH CHECK (
    -- url_hash must be SHA-256 (64 hex chars)
    url_hash IS NOT NULL AND
    length(url_hash) = 64 AND
    url_hash ~ '^[a-f0-9]{64}$' AND
    -- name must be present and reasonable length
    name IS NOT NULL AND
    length(name) >= 1 AND
    length(name) <= 500 AND
    -- urls should be present (jsonb array of stream URLs)
    urls IS NOT NULL AND
    -- Validate optional fields
    (category IS NULL OR length(category) <= 100) AND
    (country IS NULL OR length(country) <= 100) AND
    (logo IS NULL OR length(logo) <= 2048)
  );

-- Remove duplicate policies, keep one with validation
DROP POLICY IF EXISTS ch_anon_update ON public.channels;
DROP POLICY IF EXISTS channels_update ON public.channels;  -- Duplicate from v2.3.0 migration

CREATE POLICY ch_anon_update ON public.channels
  FOR UPDATE TO anon
  USING (true)  -- Can see all rows for updates
  WITH CHECK (
    -- Same validation as INSERT
    url_hash IS NOT NULL AND
    length(url_hash) = 64 AND
    url_hash ~ '^[a-f0-9]{64}$' AND
    name IS NOT NULL AND
    length(name) >= 1 AND
    length(name) <= 500 AND
    urls IS NOT NULL AND
    (category IS NULL OR length(category) <= 100) AND
    (country IS NULL OR length(country) <= 100) AND
    (logo IS NULL OR length(logo) <= 2048)
  );


-- ═════════════════════════════════════════════════════════════════════════════
-- TABLE: channel_sources
-- ═════════════════════════════════════════════════════════════════════════════

-- csrc_anon_insert: Validate required fields
DROP POLICY IF EXISTS csrc_anon_insert ON public.channel_sources;
CREATE POLICY csrc_anon_insert ON public.channel_sources
  FOR INSERT TO anon
  WITH CHECK (
    -- Both channel_hash and url_hash must be SHA-256 (64 hex chars)
    channel_hash IS NOT NULL AND
    length(channel_hash) = 64 AND
    channel_hash ~ '^[a-f0-9]{64}$' AND
    url_hash IS NOT NULL AND
    length(url_hash) = 64 AND
    url_hash ~ '^[a-f0-9]{64}$' AND
    -- url must be present
    url IS NOT NULL AND
    length(url) <= 2048 AND
    -- status must be valid if provided
    (status IS NULL OR status IN ('working', 'failed', 'unchecked')) AND
    -- Validate numeric fields
    (priority IS NULL OR (priority >= 0 AND priority <= 1000)) AND
    (response_time_ms IS NULL OR (response_time_ms >= 0 AND response_time_ms <= 60000)) AND
    (reliability IS NULL OR (reliability >= 0 AND reliability <= 1))
  );

-- csrc_anon_update: Validate fields on update
DROP POLICY IF EXISTS csrc_anon_update ON public.channel_sources;
CREATE POLICY csrc_anon_update ON public.channel_sources
  FOR UPDATE TO anon
  USING (true)  -- Can see all rows for updates
  WITH CHECK (
    -- Same validation as INSERT
    channel_hash IS NOT NULL AND
    length(channel_hash) = 64 AND
    channel_hash ~ '^[a-f0-9]{64}$' AND
    url_hash IS NOT NULL AND
    length(url_hash) = 64 AND
    url_hash ~ '^[a-f0-9]{64}$' AND
    url IS NOT NULL AND
    length(url) <= 2048 AND
    (status IS NULL OR status IN ('working', 'failed', 'unchecked')) AND
    (priority IS NULL OR (priority >= 0 AND priority <= 1000)) AND
    (response_time_ms IS NULL OR (response_time_ms >= 0 AND response_time_ms <= 60000)) AND
    (reliability IS NULL OR (reliability >= 0 AND reliability <= 1))
  );


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  DONE — All 20 Security Warnings Addressed                              ║
-- ║                                                                           ║
-- ║  Summary:                                                                ║
-- ║    ✓ 6 functions now have search_path = public                          ║
-- ║    ✓ 6 materialized views revoked from anon/authenticated               ║
-- ║    ✓ 8 RLS policies now validate input data                             ║
-- ║                                                                           ║
-- ║  Notes:                                                                  ║
-- ║    • Functions are protected against search path injection attacks       ║
-- ║    • Analytics views only accessible to service_role (admin dashboards)  ║
-- ║    • RLS policies validate data types, lengths, and enum values          ║
-- ║    • Removed duplicate channels_update policy                            ║
-- ║    • SHA-256 hashes validated with regex (64 hex chars)                  ║
-- ║    • All string fields have reasonable length limits                     ║
-- ║    • Numeric fields have valid ranges                                    ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
