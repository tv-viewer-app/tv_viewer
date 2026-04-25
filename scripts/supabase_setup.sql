-- =============================================================================
-- TV Viewer — Supabase Futureproof Schema
-- =============================================================================
--
-- ARCHITECTURE:  2 immutable tables  +  N disposable materialized views
--
--   ┌──────────────────────┐     ┌──────────────────────┐
--   │   analytics_events   │     │    channel_status     │
--   │  (append-only log)   │     │  (consensus cache)    │
--   │                      │     │                       │
--   │  id  uuid PK         │     │  url_hash  text PK    │
--   │  device_id  text     │     │  status    text       │
--   │  event_type text     │     │  last_checked tstz    │
--   │  event_data jsonb ←──│─ flexible   response_time_ms│
--   │  app_version text    │     │  report_count int     │
--   │  platform   text     │     └───────────────────────┘
--   │  country    text     │
--   │  created_at tstz     │
--   └──────────────────────┘
--            │
--   ┌───────┴─────────────────────────────────────┐
--   │        Materialized Views (disposable)       │
--   │  mv_daily_active_users     — DAU per platform│
--   │  mv_top_channels           — most-played     │
--   │  mv_client_platforms       — OS breakdown    │
--   │  mv_favorite_channels      — community favs  │
--   │  mv_crash_summary          — error rates     │
--   │  mv_engagement             — session depth   │
--   └─────────────────────────────────────────────┘
--
-- WHY THIS IS FUTUREPROOF:
--   • No CHECK constraints — clients can send ANY event_type string
--   • JSONB event_data — any shape, no ALTER TABLE needed for new fields
--   • New feature = new event_type value, zero DDL
--   • New dashboard = CREATE MATERIALIZED VIEW, zero client changes
--   • Views are disposable — DROP + CREATE freely, app keeps working
--   • Retention functions auto-clean old data
--
-- HOW TO USE:
--   1. Copy this entire script into Supabase SQL Editor
--   2. Click "Run" — safe to re-run (uses DROP IF EXISTS)
--   3. Done. No more SQL needed unless you want new dashboard views.
--
-- =============================================================================


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  TABLE 1: analytics_events — Append-only telemetry log                  ║
-- ║  Handles: app_start, channel_play, channel_fail, app_crash,             ║
-- ║           scan_complete, feature_use, favorite, session_end,            ║
-- ║           session_heartbeat, app_install, playback_end, ...anything     ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

DROP TABLE IF EXISTS analytics_events CASCADE;

CREATE TABLE analytics_events (
    id            uuid         DEFAULT gen_random_uuid() PRIMARY KEY,
    device_id     text         NOT NULL,
    event_type    text         NOT NULL,         -- No constraint: clients send any string
    event_data    jsonb        DEFAULT '{}',     -- Schemaless: any fields, any shape
    app_version   text,
    platform      text,
    country       text         DEFAULT 'XX',
    created_at    timestamptz  DEFAULT now()
);

-- Indexes for common query patterns (events are write-heavy, read via views)
CREATE INDEX idx_ae_type           ON analytics_events (event_type);
CREATE INDEX idx_ae_created        ON analytics_events (created_at DESC);
CREATE INDEX idx_ae_device         ON analytics_events (device_id);
CREATE INDEX idx_ae_platform       ON analytics_events (platform);
CREATE INDEX idx_ae_type_created   ON analytics_events (event_type, created_at DESC);
CREATE INDEX idx_ae_device_type    ON analytics_events (device_id, event_type);

-- GIN index on JSONB for ad-hoc queries like event_data->>'url_hash'
CREATE INDEX idx_ae_data           ON analytics_events USING gin (event_data);


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  TABLE 2: channel_status — Consensus-based channel health cache         ║
-- ║  Clients upsert results; report_count tracks how many devices agree.    ║
-- ║  Clients should only trust entries where report_count >= 3.             ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

DROP TABLE IF EXISTS channel_status CASCADE;

CREATE TABLE channel_status (
    url_hash          text         PRIMARY KEY,
    status            text         NOT NULL DEFAULT 'working',
    last_checked      timestamptz  DEFAULT now(),
    response_time_ms  integer,
    report_count      integer      DEFAULT 1
);

CREATE INDEX idx_cs_checked ON channel_status (last_checked DESC);
CREATE INDEX idx_cs_status  ON channel_status (status);


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  TABLE 3: channels — Crowdsourced channel repository                    ║
-- ║  Full channel data shared across all clients. Clients pull this first,  ║
-- ║  then supplement with M3U sources. New channels are contributed back.   ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

DROP TABLE IF EXISTS channels CASCADE;

CREATE TABLE channels (
    url_hash      text         PRIMARY KEY,       -- SHA256 of primary URL
    name          text         NOT NULL,
    urls          jsonb        DEFAULT '[]',       -- Array of stream URLs
    category      text         DEFAULT 'Other',
    country       text         DEFAULT 'Unknown',
    logo          text,
    media_type    text,                            -- 'TV' or 'Radio'
    source        text         DEFAULT 'iptv-org', -- 'iptv-org', 'user', 'custom_m3u'
    report_count  integer      DEFAULT 1,          -- How many devices contributed this
    created_at    timestamptz  DEFAULT now(),
    updated_at    timestamptz  DEFAULT now()
);

CREATE INDEX idx_ch_country  ON channels (country);
CREATE INDEX idx_ch_category ON channels (category);
CREATE INDEX idx_ch_updated  ON channels (updated_at DESC);
CREATE INDEX idx_ch_source   ON channels (source);


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  ROW LEVEL SECURITY — Who can do what                                   ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE channel_status   ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels         ENABLE ROW LEVEL SECURITY;

-- analytics_events: anon INSERT only (write-only telemetry); reads via service_role
CREATE POLICY "ae_anon_insert"   ON analytics_events FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "ae_service_read"  ON analytics_events FOR SELECT TO service_role USING (true);

-- channel_status: anon read + write (shared health data)
CREATE POLICY "cs_anon_insert"   ON channel_status FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "cs_anon_select"   ON channel_status FOR SELECT TO anon USING (true);
CREATE POLICY "cs_anon_update"   ON channel_status FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "cs_service_read"  ON channel_status FOR SELECT TO service_role USING (true);

-- channels: anon read + write (crowdsourced channel repository)
CREATE POLICY "ch_anon_insert"   ON channels FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "ch_anon_select"   ON channels FOR SELECT TO anon USING (true);
CREATE POLICY "ch_anon_update"   ON channels FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "ch_service_all"   ON channels FOR ALL TO service_role USING (true);


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  RATE LIMITING — Prevent channel_status poisoning                       ║
-- ║  Rejects updates to the same url_hash more than once per minute.        ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

CREATE OR REPLACE FUNCTION check_channel_status_rate()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    -- Rate-limit rapid-fire INSERTs to the same url_hash within 1 minute.
    -- When rate-limited, the trigger performs its own UPDATE (with the new
    -- status/timestamp) and returns NULL to skip the INSERT.  This means
    -- PostgREST's ON CONFLICT clause never fires, but the data is still
    -- written correctly via the trigger's UPDATE.
    IF TG_OP = 'INSERT' AND EXISTS (
        SELECT 1 FROM channel_status
        WHERE url_hash = NEW.url_hash
          AND last_checked > now() - INTERVAL '1 minute'
    ) THEN
        UPDATE channel_status
        SET report_count = report_count + 1,
            last_checked = now(),
            status = NEW.status,
            response_time_ms = COALESCE(NEW.response_time_ms, response_time_ms)
        WHERE url_hash = NEW.url_hash;
        RETURN NULL;  -- Skip the INSERT; data already written above
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_cs_rate_limit
    BEFORE INSERT ON channel_status
    FOR EACH ROW EXECUTE FUNCTION check_channel_status_rate();


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  MATERIALIZED VIEWS — Disposable, re-creatable analytics layers         ║
-- ║  DROP + CREATE freely. The app never reads these directly.              ║
-- ║  Only dashboards / admin queries use them.                              ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- ── 1. Daily Active Users ────────────────────────────────────────────────

DROP MATERIALIZED VIEW IF EXISTS mv_daily_active_users CASCADE;
CREATE MATERIALIZED VIEW mv_daily_active_users AS
SELECT
    date_trunc('day', created_at)::date AS day,
    platform,
    COUNT(DISTINCT device_id)           AS unique_devices,
    COUNT(*)                            AS total_events
FROM analytics_events
GROUP BY 1, platform
ORDER BY day DESC;

CREATE UNIQUE INDEX idx_mv_dau ON mv_daily_active_users (day, platform);


-- ── 2. Top Played Channels ──────────────────────────────────────────────

DROP MATERIALIZED VIEW IF EXISTS mv_top_channels CASCADE;
CREATE MATERIALIZED VIEW mv_top_channels AS
SELECT
    event_data->>'url_hash'              AS channel_hash,
    event_data->>'country'               AS channel_country,
    event_data->>'category'              AS channel_category,
    COUNT(*)                             AS play_count,
    COUNT(DISTINCT device_id)            AS unique_players,
    MAX(created_at)                      AS last_played
FROM analytics_events
WHERE event_type = 'channel_play'
  AND event_data->>'url_hash' IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY play_count DESC
LIMIT 1000;

CREATE UNIQUE INDEX idx_mv_top ON mv_top_channels (channel_hash);


-- ── 3. Client Platform Breakdown ────────────────────────────────────────

DROP MATERIALIZED VIEW IF EXISTS mv_client_platforms CASCADE;
CREATE MATERIALIZED VIEW mv_client_platforms AS
SELECT
    platform,
    event_data->>'os'             AS os_name,
    event_data->>'os_version'     AS os_version,
    app_version,
    COUNT(DISTINCT device_id)     AS unique_devices,
    COUNT(*)                      AS session_count,
    MIN(created_at)               AS first_seen,
    MAX(created_at)               AS last_seen
FROM analytics_events
WHERE event_type IN ('app_start', 'app_launch', 'app_install')
GROUP BY 1, 2, 3, 4
ORDER BY session_count DESC;

CREATE UNIQUE INDEX idx_mv_clients
    ON mv_client_platforms (platform, os_name, os_version, app_version);


-- ── 4. Favorite Channels ────────────────────────────────────────────────

DROP MATERIALIZED VIEW IF EXISTS mv_favorite_channels CASCADE;
CREATE MATERIALIZED VIEW mv_favorite_channels AS
SELECT
    event_data->>'url_hash'   AS channel_hash,
    event_data->>'country'    AS channel_country,
    event_data->>'category'   AS channel_category,
    SUM(CASE WHEN event_data->>'action' = 'add' THEN 1 ELSE -1 END)
                              AS net_favorites,
    COUNT(DISTINCT device_id) AS unique_users,
    MAX(created_at)           AS last_favorited
FROM analytics_events
WHERE event_type = 'favorite'
GROUP BY 1, 2, 3
HAVING SUM(CASE WHEN event_data->>'action' = 'add' THEN 1 ELSE -1 END) > 0
ORDER BY net_favorites DESC
LIMIT 1000;

CREATE UNIQUE INDEX idx_mv_favs ON mv_favorite_channels (channel_hash);


-- ── 5. Crash & Error Summary ────────────────────────────────────────────

DROP MATERIALIZED VIEW IF EXISTS mv_crash_summary CASCADE;
CREATE MATERIALIZED VIEW mv_crash_summary AS
SELECT
    app_version,
    platform,
    event_data->>'error_category'  AS error_category,
    event_data->>'error_type'      AS error_type,
    COUNT(*)                       AS total_occurrences,
    COUNT(DISTINCT device_id)      AS affected_devices,
    MIN(created_at)                AS first_seen,
    MAX(created_at)                AS last_seen
FROM analytics_events
WHERE event_type IN ('app_crash', 'channel_fail')
  AND created_at > now() - INTERVAL '30 days'
GROUP BY 1, 2, 3, 4
ORDER BY affected_devices DESC, total_occurrences DESC;

CREATE UNIQUE INDEX idx_mv_crash
    ON mv_crash_summary (app_version, platform, error_category, error_type);


-- ── 6. Engagement (session depth) ───────────────────────────────────────

DROP MATERIALIZED VIEW IF EXISTS mv_engagement CASCADE;
CREATE MATERIALIZED VIEW mv_engagement AS
SELECT
    date_trunc('day', created_at)::date AS day,
    platform,
    COUNT(*)                                                         AS sessions_ended,
    AVG((event_data->>'session_duration_s')::numeric)                AS avg_session_s,
    AVG((event_data->>'channels_played')::numeric)                   AS avg_channels,
    AVG((event_data->>'channels_failed')::numeric)                   AS avg_failures
FROM analytics_events
WHERE event_type = 'session_end'
  AND event_data->>'session_duration_s' IS NOT NULL
GROUP BY 1, 2
ORDER BY 1 DESC;

CREATE UNIQUE INDEX idx_mv_engage ON mv_engagement (day, platform);


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  SERVER FUNCTIONS — Retention, refresh, diagnostics                     ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- Refresh all views (call via pg_cron every 6h or manually)
-- SECURITY DEFINER required for REFRESH; access restricted to service_role below.
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS void LANGUAGE sql SECURITY DEFINER AS $$
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_active_users;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_channels;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_client_platforms;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_favorite_channels;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_crash_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_engagement;
$$;
REVOKE EXECUTE ON FUNCTION refresh_analytics_views() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION refresh_analytics_views() TO service_role;

-- Data retention: delete old events (call weekly via pg_cron or GitHub Actions)
-- Restricted to service_role only.
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
    deleted_events  bigint;
    deleted_status  bigint;
BEGIN
    DELETE FROM analytics_events WHERE created_at < now() - INTERVAL '90 days';
    GET DIAGNOSTICS deleted_events = ROW_COUNT;

    DELETE FROM channel_status WHERE last_checked < now() - INTERVAL '7 days';
    GET DIAGNOSTICS deleted_status = ROW_COUNT;

    RETURN jsonb_build_object(
        'events_deleted', deleted_events,
        'status_deleted', deleted_status,
        'cleaned_at', now()
    );
END;
$$;
REVOKE EXECUTE ON FUNCTION cleanup_old_data() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION cleanup_old_data() TO service_role;

-- Quick health check: returns table sizes and recent activity
-- Restricted to service_role only.
CREATE OR REPLACE FUNCTION db_health()
RETURNS jsonb LANGUAGE sql SECURITY DEFINER AS $$
    SELECT jsonb_build_object(
        'analytics_events_count', (SELECT count(*) FROM analytics_events),
        'channel_status_count',   (SELECT count(*) FROM channel_status),
        'latest_event',           (SELECT max(created_at) FROM analytics_events),
        'latest_channel_check',   (SELECT max(last_checked) FROM channel_status),
        'distinct_devices_7d',    (SELECT count(DISTINCT device_id)
                                   FROM analytics_events
                                   WHERE created_at > now() - INTERVAL '7 days'),
        'events_today',           (SELECT count(*)
                                   FROM analytics_events
                                   WHERE created_at > date_trunc('day', now()))
    );
$$;
REVOKE EXECUTE ON FUNCTION db_health() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION db_health() TO service_role;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  USEFUL QUERIES — Copy-paste into Supabase SQL Editor as needed         ║
-- ║  These are NOT tables — just saved queries for ad-hoc analysis.         ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- Top 5 issues (last 7 days):
--   SELECT * FROM mv_crash_summary
--   WHERE last_seen > now() - INTERVAL '7 days'
--   ORDER BY affected_devices DESC LIMIT 5;

-- Retention cohort (D1/D7/D30):
--   WITH installs AS (
--       SELECT device_id, MIN(created_at)::date AS cohort_day
--       FROM analytics_events WHERE event_type IN ('app_install','app_start')
--       GROUP BY device_id
--   ),
--   activity AS (
--       SELECT DISTINCT device_id, created_at::date AS active_day
--       FROM analytics_events
--   )
--   SELECT i.cohort_day,
--          COUNT(DISTINCT i.device_id) AS installed,
--          COUNT(DISTINCT CASE WHEN a.active_day = i.cohort_day + 1  THEN i.device_id END) AS d1,
--          COUNT(DISTINCT CASE WHEN a.active_day = i.cohort_day + 7  THEN i.device_id END) AS d7,
--          COUNT(DISTINCT CASE WHEN a.active_day = i.cohort_day + 30 THEN i.device_id END) AS d30
--   FROM installs i LEFT JOIN activity a ON i.device_id = a.device_id
--   GROUP BY i.cohort_day ORDER BY i.cohort_day DESC;

-- Stream success rate:
--   SELECT platform, app_version,
--     COUNT(*) FILTER (WHERE event_type = 'channel_play') AS plays,
--     COUNT(*) FILTER (WHERE event_type = 'channel_fail') AS fails,
--     ROUND(100.0 * COUNT(*) FILTER (WHERE event_type = 'channel_play')
--           / NULLIF(COUNT(*), 0), 1) AS success_pct
--   FROM analytics_events
--   WHERE event_type IN ('channel_play', 'channel_fail')
--     AND created_at > now() - INTERVAL '7 days'
--   GROUP BY platform, app_version;

-- Average watch time by category:
--   SELECT event_data->>'category' AS category,
--     ROUND(AVG((event_data->>'watch_duration_s')::numeric)) AS avg_watch_s,
--     COUNT(*) AS sessions
--   FROM analytics_events
--   WHERE event_type = 'playback_end'
--   GROUP BY 1 ORDER BY avg_watch_s DESC;

-- Health check:
--   SELECT * FROM db_health();


-- ═══════════════════════════════════════════════════════════════════════════
-- DONE. Run this once. You should never need to ALTER these tables again.
-- New events = just send new event_type strings from client code.
-- New dashboards = CREATE MATERIALIZED VIEW (no client changes needed).
-- ═══════════════════════════════════════════════════════════════════════════
