-- =============================================================================
-- TV Viewer v2.3.0 — Schema Migration: channel_sources + cleanup
-- =============================================================================
-- Run this AFTER the base supabase_setup.sql has been applied.
-- Safe to re-run (uses IF NOT EXISTS / DROP IF EXISTS).
--
-- CHANGES:
--   1. Adds DELETE RLS policy on `channels` for cleanup
--   2. Adds enrichment columns to `channels` table
--   3. Creates `channel_sources` table — per-URL health + reliability tracking
--   4. Adds RLS policies for channel_sources
--   5. Adds function for atomic health reporting
--   6. Adds view for client consumption
--   7. Adds cleanup function for repopulation
-- =============================================================================


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  STEP 0: Add DELETE policy on channels (needed for repopulation)        ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

-- Allow anon to delete channels (for populate script cleanup)
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'channels' AND policyname = 'channels_delete'
    ) THEN
        CREATE POLICY "channels_delete" ON channels FOR DELETE TO anon USING (true);
    END IF;
END $$;

-- Also add UPDATE policy if missing
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'channels' AND policyname = 'channels_update'
    ) THEN
        CREATE POLICY "channels_update" ON channels FOR UPDATE TO anon USING (true) WITH CHECK (true);
    END IF;
END $$;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  STEP 1: Enrich `channels` table with metadata columns                  ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

ALTER TABLE channels ADD COLUMN IF NOT EXISTS normalized_name text;
ALTER TABLE channels ADD COLUMN IF NOT EXISTS description text;
ALTER TABLE channels ADD COLUMN IF NOT EXISTS epg_id text;
ALTER TABLE channels ADD COLUMN IF NOT EXISTS language text;
ALTER TABLE channels ADD COLUMN IF NOT EXISTS is_adult boolean DEFAULT false;

-- Index on normalized_name for consolidation lookups
CREATE INDEX IF NOT EXISTS idx_ch_normalized ON channels (normalized_name);
CREATE INDEX IF NOT EXISTS idx_ch_adult ON channels (is_adult);


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  STEP 2: Create `channel_sources` table                                 ║
-- ║  Per-URL health tracking with reliability scoring.                       ║
-- ║  Each channel has N source URLs; clients try them in reliability order.  ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

CREATE TABLE IF NOT EXISTS channel_sources (
    id              uuid         DEFAULT gen_random_uuid() PRIMARY KEY,
    channel_hash    text         NOT NULL,           -- FK to channels.url_hash
    url             text         NOT NULL,
    url_hash        text         NOT NULL,           -- SHA256 of url (for health lookups)
    priority        integer      DEFAULT 100,        -- Manual priority (lower = preferred)
    status          text         DEFAULT 'unchecked', -- working / failed / unchecked
    last_checked    timestamptz,
    response_time_ms integer,
    success_count   integer      DEFAULT 0,
    fail_count      integer      DEFAULT 0,
    reliability     real         DEFAULT 0.5,        -- success / (success + fail)
    checked_by      integer      DEFAULT 0,          -- How many clients checked this
    source_origin   text,                            -- Which M3U repo contributed this URL
    created_at      timestamptz  DEFAULT now(),
    updated_at      timestamptz  DEFAULT now(),

    UNIQUE (url_hash)                                -- One entry per URL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_csrc_channel   ON channel_sources (channel_hash);
CREATE INDEX IF NOT EXISTS idx_csrc_status    ON channel_sources (status);
CREATE INDEX IF NOT EXISTS idx_csrc_reliable  ON channel_sources (channel_hash, reliability DESC);
CREATE INDEX IF NOT EXISTS idx_csrc_stale     ON channel_sources (last_checked ASC NULLS FIRST);


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  STEP 3: RLS policies for channel_sources                               ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

ALTER TABLE channel_sources ENABLE ROW LEVEL SECURITY;

CREATE POLICY "csrc_anon_select" ON channel_sources FOR SELECT TO anon USING (true);
CREATE POLICY "csrc_anon_insert" ON channel_sources FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "csrc_anon_update" ON channel_sources FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "csrc_service_all" ON channel_sources FOR ALL TO service_role USING (true);


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  STEP 4: Function to report a health check result                       ║
-- ║  Clients call this instead of raw INSERT to get proper reliability calc. ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

CREATE OR REPLACE FUNCTION report_source_health(
    p_url_hash text,
    p_status text,                -- 'working' or 'failed'
    p_response_time_ms integer DEFAULT NULL
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    UPDATE channel_sources
    SET status = p_status,
        last_checked = now(),
        response_time_ms = COALESCE(p_response_time_ms, response_time_ms),
        success_count = CASE WHEN p_status = 'working'
                             THEN success_count + 1 ELSE success_count END,
        fail_count = CASE WHEN p_status = 'failed'
                          THEN fail_count + 1 ELSE fail_count END,
        reliability = CASE
            WHEN p_status = 'working'
            THEN (success_count + 1)::real / (success_count + fail_count + 1)::real
            ELSE success_count::real / (success_count + fail_count + 1)::real
        END,
        checked_by = checked_by + 1,
        updated_at = now()
    WHERE url_hash = p_url_hash;
END;
$$;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  STEP 5: View for clients — channels with best source URL               ║
-- ║  Returns each channel with its sources pre-sorted by reliability.        ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

CREATE OR REPLACE VIEW v_channels_with_sources AS
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
-- ║  STEP 6: Cleanup function for repopulation                             ║
-- ║  Clients call truncate_channels() before batch repopulation.           ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝

CREATE OR REPLACE FUNCTION truncate_channels()
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    DELETE FROM channel_sources;
    DELETE FROM channels;
END;
$$;


-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  DONE. Run this migration once.                                         ║
-- ║  Clients should:                                                        ║
-- ║    1. SELECT * FROM v_channels_with_sources (to get channels + sources)  ║
-- ║    2. Call report_source_health() after each stream check                ║
-- ║    3. Never check URLs that were checked < 1h ago (use last_checked)    ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝
