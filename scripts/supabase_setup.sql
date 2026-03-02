-- =============================================================================
-- TV Viewer — Supabase Analytics Database Schema
-- =============================================================================
--
-- Run this entire script in the Supabase SQL Editor (https://supabase.com/dashboard)
-- to set up the analytics and shared channel health tables.
--
-- PRIVACY NOTICE:
--   This schema is designed to be Google Play compliant and privacy-first:
--   - NO personally identifiable information (PII) is stored
--   - Device IDs are SHA-256 hashed (anonymous, irreversible)
--   - Channel URLs are SHA-256 hashed (cannot be reconstructed)
--   - Row Level Security (RLS) ensures clients can only INSERT, not read analytics
--   - Channel health data is readable by all for shared functionality
--
-- Tables:
--   1. analytics_events  — App usage, crashes, errors (write-only from clients)
--   2. channel_status    — Shared channel health data (read/write from clients)
--
-- Materialized Views:
--   3. mv_daily_active_users  — DAU aggregation for dashboard
--   4. mv_top_channels        — Most-played channels
--   5. mv_crash_summary       — Crash rate aggregation
--
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 1. analytics_events — Stores all app telemetry (anonymous, write-only)
-- ---------------------------------------------------------------------------
-- Clients INSERT events but CANNOT read them back (one-way analytics).
-- Only the service_role (admin/dashboard) can SELECT from this table.

CREATE TABLE IF NOT EXISTS analytics_events (
    id            uuid         DEFAULT gen_random_uuid() PRIMARY KEY,
    device_id     text         NOT NULL,        -- SHA-256 hashed device identifier (anonymous, irreversible)
    event_type    text         NOT NULL,        -- Event category: 'app_open', 'channel_play', 'channel_fail',
                                                --   'app_crash', 'error', 'scan_complete', 'filter_used'
    event_data    jsonb        DEFAULT '{}',    -- Flexible JSON payload (varies by event_type)
    app_version   text,                         -- Semantic version, e.g. '2.1.0'
    platform      text,                         -- 'android', 'windows', 'linux', 'macos'
    created_at    timestamptz  DEFAULT now()    -- Server-side timestamp (UTC)
);

-- Add a CHECK constraint to enforce known event types (optional, prevents garbage data)
ALTER TABLE analytics_events
    ADD CONSTRAINT chk_event_type CHECK (
        event_type IN (
            'app_launch', 'channel_play', 'channel_fail',
            'app_crash', 'error', 'scan_complete', 'filter_used'
        )
    );

COMMENT ON TABLE analytics_events IS
    'Privacy-first analytics events. All identifiers are SHA-256 hashed. No PII stored.';
COMMENT ON COLUMN analytics_events.device_id IS
    'SHA-256 hash of device UUID — anonymous, cannot be reversed to identify a user.';
COMMENT ON COLUMN analytics_events.event_data IS
    'Flexible JSON payload. Contents vary by event_type. Never contains PII.';


-- ---------------------------------------------------------------------------
-- 2. channel_status — Shared channel health/validation data
-- ---------------------------------------------------------------------------
-- Clients can both INSERT new results and SELECT existing ones.
-- This enables cross-device channel validation sharing — if one device
-- recently verified a channel works, other devices can skip re-scanning it.

CREATE TABLE IF NOT EXISTS channel_status (
    id               uuid         DEFAULT gen_random_uuid() PRIMARY KEY,
    channel_url_hash text         NOT NULL,        -- SHA-256 hash of the channel URL (privacy-safe)
    is_working       boolean      NOT NULL,        -- true = channel responded successfully
    checked_by       text         NOT NULL,        -- SHA-256 hashed device ID of the reporter
    checked_at       timestamptz  DEFAULT now(),   -- When the check was performed
    app_version      text,                         -- App version that performed the check
    response_time_ms integer                       -- Response latency in milliseconds (NULL if failed)
);

COMMENT ON TABLE channel_status IS
    'Shared channel health data. URLs and device IDs are SHA-256 hashed. No PII stored.';
COMMENT ON COLUMN channel_status.channel_url_hash IS
    'SHA-256 hash of the full channel URL — cannot be reversed to the original URL.';
COMMENT ON COLUMN channel_status.checked_by IS
    'SHA-256 hashed device ID of the device that performed the check.';


-- ---------------------------------------------------------------------------
-- 3. Indexes for query performance
-- ---------------------------------------------------------------------------

-- analytics_events indexes
CREATE INDEX IF NOT EXISTS idx_analytics_event_type
    ON analytics_events(event_type);

CREATE INDEX IF NOT EXISTS idx_analytics_created
    ON analytics_events(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_device
    ON analytics_events(device_id);

CREATE INDEX IF NOT EXISTS idx_analytics_platform
    ON analytics_events(platform);

-- Composite index for dashboard queries (event type + time range)
CREATE INDEX IF NOT EXISTS idx_analytics_type_created
    ON analytics_events(event_type, created_at DESC);

-- channel_status indexes
CREATE INDEX IF NOT EXISTS idx_channel_status_hash
    ON channel_status(channel_url_hash);

CREATE INDEX IF NOT EXISTS idx_channel_status_checked
    ON channel_status(checked_at DESC);

-- Composite index for "latest status per channel" queries
CREATE INDEX IF NOT EXISTS idx_channel_status_hash_checked
    ON channel_status(channel_url_hash, checked_at DESC);


-- ---------------------------------------------------------------------------
-- 4. Row Level Security (RLS) — Critical for privacy
-- ---------------------------------------------------------------------------
-- RLS ensures that anonymous (anon) API key users:
--   - CAN insert analytics events (write-only telemetry)
--   - CANNOT read other users' analytics data
--   - CAN read/write channel_status (shared health data)
--
-- Only the service_role (used by admin dashboards) can read analytics.

ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE channel_status ENABLE ROW LEVEL SECURITY;

-- analytics_events: anon can INSERT only (one-way, write-only)
CREATE POLICY "anon_insert_analytics"
    ON analytics_events
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- analytics_events: service_role can read everything (admin/dashboard)
CREATE POLICY "service_read_analytics"
    ON analytics_events
    FOR SELECT
    TO service_role
    USING (true);

-- channel_status: anon can INSERT new check results
CREATE POLICY "anon_insert_channel_status"
    ON channel_status
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- channel_status: anon can READ all channel health data (shared functionality)
CREATE POLICY "anon_read_channel_status"
    ON channel_status
    FOR SELECT
    TO anon
    USING (true);

-- channel_status: anon can UPDATE existing records (required for upsert)
CREATE POLICY "anon_update_channel_status"
    ON channel_status
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);

-- channel_status: service_role can read everything (admin/dashboard)
CREATE POLICY "service_read_channel_status"
    ON channel_status
    FOR SELECT
    TO service_role
    USING (true);


-- ---------------------------------------------------------------------------
-- 5. Materialized Views — Pre-aggregated data for the analytics dashboard
-- ---------------------------------------------------------------------------
-- These views are queried by scripts/analytics_dashboard.py and avoid
-- expensive full-table scans on every dashboard load.
--
-- Refresh them periodically with:
--   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_active_users;
--   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_channels;
--   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_crash_summary;

-- 5a. Daily Active Users (DAU) — unique devices per day per platform
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_active_users AS
SELECT
    date_trunc('day', created_at)::date AS day,
    platform,
    COUNT(DISTINCT device_id)           AS unique_devices,
    COUNT(*)                            AS total_events
FROM analytics_events
GROUP BY date_trunc('day', created_at)::date, platform
ORDER BY day DESC;

-- Unique index required for CONCURRENTLY refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dau_day_platform
    ON mv_daily_active_users(day, platform);

COMMENT ON MATERIALIZED VIEW mv_daily_active_users IS
    'Daily active users by platform. Refresh periodically for dashboard.';


-- 5b. Top Channels — most-played channel URL hashes
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_channels AS
SELECT
    event_data->>'url_hash'  AS channel_hash,
    COUNT(*)                 AS play_count,
    COUNT(DISTINCT device_id) AS unique_players,
    MAX(created_at)          AS last_played
FROM analytics_events
WHERE event_type = 'channel_play'
  AND event_data->>'url_hash' IS NOT NULL
GROUP BY event_data->>'url_hash'
ORDER BY play_count DESC
LIMIT 500;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_top_channels_hash
    ON mv_top_channels(channel_hash);

COMMENT ON MATERIALIZED VIEW mv_top_channels IS
    'Top 500 most-played channels by play count. Refresh periodically.';


-- 5c. Crash Summary — crash/error rates per version per platform
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_crash_summary AS
SELECT
    app_version,
    platform,
    COALESCE(event_data->>'error_type', 'unknown') AS error_type,
    COUNT(*)                     AS crash_count,
    MIN(created_at)              AS first_seen,
    MAX(created_at)              AS last_seen,
    COUNT(DISTINCT device_id)    AS affected_devices
FROM analytics_events
WHERE event_type IN ('app_crash', 'error')
GROUP BY app_version, platform, COALESCE(event_data->>'error_type', 'unknown')
ORDER BY crash_count DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_crash_summary
    ON mv_crash_summary(app_version, platform, error_type);

COMMENT ON MATERIALIZED VIEW mv_crash_summary IS
    'Crash/error rates per version and platform. Refresh periodically.';


-- ---------------------------------------------------------------------------
-- 6. Utility: Scheduled refresh function (optional — use with pg_cron)
-- ---------------------------------------------------------------------------
-- If you have pg_cron enabled in your Supabase project, you can schedule
-- automatic refreshes of the materialized views.
--
-- To enable pg_cron, go to Supabase Dashboard > Database > Extensions > pg_cron
--
-- Then run:
--   SELECT cron.schedule(
--       'refresh-analytics-views',
--       '0 */6 * * *',  -- Every 6 hours
--       $$
--           REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_active_users;
--           REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_channels;
--           REFRESH MATERIALIZED VIEW CONCURRENTLY mv_crash_summary;
--       $$
--   );

CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS void
LANGUAGE sql
SECURITY DEFINER
AS $$
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_active_users;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_channels;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_crash_summary;
$$;

COMMENT ON FUNCTION refresh_analytics_views IS
    'Refreshes all analytics materialized views. Call periodically or via pg_cron.';


-- ---------------------------------------------------------------------------
-- 7. Data retention policy (optional cleanup)
-- ---------------------------------------------------------------------------
-- Uncomment and schedule to auto-delete old analytics data.
-- Channel status older than 7 days is stale and can be safely removed.
--
-- DELETE FROM analytics_events WHERE created_at < now() - interval '90 days';
-- DELETE FROM channel_status WHERE checked_at < now() - interval '7 days';


-- ---------------------------------------------------------------------------
-- Setup complete!
-- ---------------------------------------------------------------------------
-- Next steps:
--   1. Copy your Supabase URL and anon key from Project Settings > API
--   2. Run: python scripts/supabase_setup.py
--   3. Add SUPABASE_URL and SUPABASE_ANON_KEY to GitHub Secrets for CI builds
--   4. The Flutter app will automatically connect using --dart-define at build time
-- ---------------------------------------------------------------------------
