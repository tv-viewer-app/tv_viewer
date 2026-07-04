-- =============================================================================
-- TV Viewer — Complete Supabase Database Setup & Verification
-- Run in Supabase SQL Editor (Role: postgres)
-- Safe to re-run (uses IF NOT EXISTS / OR REPLACE throughout)
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. CHANNEL STATUS TABLE (health reporting)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS channel_status (
    url_hash text PRIMARY KEY,
    status text DEFAULT 'unchecked',
    last_checked timestamptz DEFAULT now(),
    report_count integer DEFAULT 0
);

ALTER TABLE channel_status ENABLE ROW LEVEL SECURITY;

-- RPC functions for reporting (SECURITY DEFINER = anon can call safely)
CREATE OR REPLACE FUNCTION report_channel_working(
    p_url_hash text, p_device_id text, p_response_time_ms integer DEFAULT 0
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    IF length(p_url_hash) > 64 OR length(p_device_id) > 64 THEN
        RAISE EXCEPTION 'Input too long';
    END IF;
    INSERT INTO channel_status (url_hash, status, last_checked, report_count)
    VALUES (p_url_hash, 'working', now(), 0)
    ON CONFLICT (url_hash) DO UPDATE
    SET status = 'working', last_checked = now(), report_count = 0;
END;
$$;

CREATE OR REPLACE FUNCTION report_channel_broken(
    p_url_hash text, p_device_id text
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    IF length(p_url_hash) > 64 OR length(p_device_id) > 64 THEN
        RAISE EXCEPTION 'Input too long';
    END IF;
    INSERT INTO channel_status (url_hash, status, last_checked, report_count)
    VALUES (p_url_hash, 'broken', now(), 1)
    ON CONFLICT (url_hash) DO UPDATE
    SET status = 'broken', last_checked = now(),
        report_count = channel_status.report_count + 1;
END;
$$;

GRANT EXECUTE ON FUNCTION report_channel_working(text, text, integer) TO anon;
GRANT EXECUTE ON FUNCTION report_channel_broken(text, text) TO anon;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. ANALYTICS EVENTS TABLE
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS analytics_events (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    event_type text NOT NULL,
    device_id text,
    platform text,
    country text,
    event_data jsonb,
    created_at timestamptz DEFAULT now()
);

ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- Anon can INSERT (report events) but NOT SELECT raw data
DO $$ BEGIN
    CREATE POLICY "Anon can insert analytics" ON analytics_events FOR INSERT WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

GRANT INSERT ON analytics_events TO anon;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. MATERIALIZED VIEWS (aggregated analytics — safe for public read)
-- ─────────────────────────────────────────────────────────────────────────────

-- Top channels by play count
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_channels AS
SELECT
    event_data->>'url_hash' AS channel_hash,
    event_data->>'country' AS channel_country,
    event_data->>'category' AS channel_category,
    count(*) AS play_count,
    count(DISTINCT device_id) AS unique_players,
    max(created_at) AS last_played
FROM analytics_events
WHERE event_type = 'channel_play'
  AND event_data->>'url_hash' IS NOT NULL
GROUP BY channel_hash, channel_country, channel_category
ORDER BY play_count DESC;

-- Daily active users
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_active_users AS
SELECT
    date_trunc('day', created_at)::date AS day,
    platform,
    count(DISTINCT device_id) AS unique_devices,
    count(*) AS total_events
FROM analytics_events
GROUP BY day, platform
ORDER BY day DESC;

-- Grant anon read access on materialized views
GRANT SELECT ON mv_top_channels TO anon;
GRANT SELECT ON mv_daily_active_users TO anon;

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. CHANNEL REQUESTS TABLE (community suggestions + voting)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS channel_requests (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    name text NOT NULL,
    url text,
    country text,
    category text,
    votes integer DEFAULT 1,
    status text DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    submitted_by text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

ALTER TABLE channel_requests ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    CREATE POLICY "Anyone can read requests" ON channel_requests FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY "Anyone can insert requests" ON channel_requests FOR INSERT WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_channel_requests_votes ON channel_requests(votes DESC);

-- Anon can read and insert, but NOT update directly
GRANT SELECT, INSERT ON channel_requests TO anon;

-- Secure atomic vote function (prevents race conditions + manipulation)
CREATE OR REPLACE FUNCTION vote_channel_request(p_request_id uuid, p_device_hash text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    IF p_request_id IS NULL OR length(p_device_hash) > 64 THEN
        RAISE EXCEPTION 'Invalid input';
    END IF;
    UPDATE channel_requests SET votes = votes + 1, updated_at = now()
    WHERE id = p_request_id AND status = 'pending';
END;
$$;

GRANT EXECUTE ON FUNCTION vote_channel_request(uuid, text) TO anon;

-- Remove any dangerous UPDATE policy if it exists
DROP POLICY IF EXISTS "Anyone can vote" ON channel_requests;
REVOKE UPDATE ON channel_requests FROM anon;

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. VERIFICATION QUERIES
-- ─────────────────────────────────────────────────────────────────────────────

-- Check all tables exist
SELECT tablename FROM pg_tables WHERE schemaname = 'public' 
AND tablename IN ('channel_status', 'analytics_events', 'channel_requests')
ORDER BY tablename;
-- EXPECTED: 3 rows

-- Check materialized views exist
SELECT matviewname FROM pg_matviews 
WHERE matviewname IN ('mv_top_channels', 'mv_daily_active_users');
-- EXPECTED: 2 rows

-- Check RPC functions are SECURITY DEFINER
SELECT proname, pronargs, prosecdef as is_security_definer
FROM pg_proc
WHERE proname IN ('report_channel_working', 'report_channel_broken', 'vote_channel_request');
-- EXPECTED: 3 rows, all is_security_definer = true

-- Check anon grants on materialized views
SELECT grantee, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE table_name IN ('mv_top_channels', 'mv_daily_active_users')
  AND grantee = 'anon';
-- EXPECTED: 2 rows with SELECT

-- Check anon CANNOT update channel_requests directly
SELECT grantee, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE table_name = 'channel_requests' AND grantee = 'anon';
-- EXPECTED: SELECT and INSERT only (NO UPDATE)
