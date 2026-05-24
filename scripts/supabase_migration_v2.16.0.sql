-- ╔═══════════════════════════════════════════════════════════════════════════╗
-- ║  TV Viewer — Supabase migration v2.16.0                                  ║
-- ║                                                                           ║
-- ║  Goal: replace fragile read-modify-write client paths with atomic        ║
-- ║  SECURITY DEFINER RPCs, add a per-device vote audit trail, and lock      ║
-- ║  down RLS so the anonymous APK key cannot mass-corrupt the catalog.     ║
-- ║                                                                           ║
-- ║  This file is IDEMPOTENT — safe to re-run.                               ║
-- ║                                                                           ║
-- ║  Run AFTER supabase_setup.sql and supabase_security_hardening.sql.      ║
-- ║  Apply via Supabase SQL editor or `psql $DATABASE_URL -f`.              ║
-- ╚═══════════════════════════════════════════════════════════════════════════╝


-- ── 1. channel_votes — per-device audit trail ────────────────────────────

CREATE TABLE IF NOT EXISTS channel_votes (
    id          BIGSERIAL    PRIMARY KEY,
    url_hash    TEXT         NOT NULL,
    device_id   TEXT         NOT NULL,
    vote        TEXT         NOT NULL CHECK (vote IN ('working', 'broken')),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- One active vote per (device, channel, kind) — collapses duplicates.
CREATE UNIQUE INDEX IF NOT EXISTS uq_channel_votes_device_hash_vote
    ON channel_votes (device_id, url_hash, vote);

CREATE INDEX IF NOT EXISTS idx_channel_votes_hash_created
    ON channel_votes (url_hash, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_channel_votes_device_created
    ON channel_votes (device_id, created_at DESC);

ALTER TABLE channel_votes ENABLE ROW LEVEL SECURITY;

-- No direct DML from anon. Writes happen exclusively through RPCs below.
DROP POLICY IF EXISTS cv_anon_select ON channel_votes;
DROP POLICY IF EXISTS cv_anon_insert ON channel_votes;
DROP POLICY IF EXISTS cv_anon_update ON channel_votes;
DROP POLICY IF EXISTS cv_anon_delete ON channel_votes;

REVOKE ALL ON channel_votes FROM anon, authenticated;
GRANT SELECT (url_hash, vote, created_at) ON channel_votes TO anon;  -- aggregate-friendly read


-- ── 2. RPC: report_channel_broken ────────────────────────────────────────
--
-- Atomic alternative to GET-then-PATCH on channels.report_count.
-- Records the vote, then refreshes the cached counter on `channels`.
-- Rate-limits each device to one broken vote per channel per 10 minutes.

CREATE OR REPLACE FUNCTION report_channel_broken(
    p_url_hash  TEXT,
    p_device_id TEXT
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_recent_broken INT;
    v_total_broken  INT;
    v_total_working INT;
BEGIN
    IF p_url_hash IS NULL OR length(p_url_hash) < 8 THEN
        RETURN jsonb_build_object('ok', false, 'error', 'invalid_hash');
    END IF;
    IF p_device_id IS NULL OR length(p_device_id) < 8 THEN
        RETURN jsonb_build_object('ok', false, 'error', 'invalid_device');
    END IF;

    -- Per-device throttle: max 1 broken vote per channel per 10 minutes.
    SELECT COUNT(*) INTO v_recent_broken
    FROM channel_votes
    WHERE device_id = p_device_id
      AND url_hash  = p_url_hash
      AND vote      = 'broken'
      AND created_at > now() - INTERVAL '10 minutes';

    IF v_recent_broken > 0 THEN
        RETURN jsonb_build_object('ok', true, 'throttled', true);
    END IF;

    -- Per-device abuse cap: max 100 votes/hour across the whole catalog.
    IF (SELECT COUNT(*) FROM channel_votes
        WHERE device_id = p_device_id
          AND created_at > now() - INTERVAL '1 hour') >= 100 THEN
        RETURN jsonb_build_object('ok', false, 'error', 'rate_limited');
    END IF;

    INSERT INTO channel_votes (url_hash, device_id, vote)
    VALUES (p_url_hash, p_device_id, 'broken')
    ON CONFLICT (device_id, url_hash, vote)
        DO UPDATE SET created_at = now();

    -- Recompute consensus counters from the audit trail (last 30 days).
    SELECT
        COUNT(*) FILTER (WHERE vote = 'broken'),
        COUNT(*) FILTER (WHERE vote = 'working')
    INTO v_total_broken, v_total_working
    FROM channel_votes
    WHERE url_hash = p_url_hash
      AND created_at > now() - INTERVAL '30 days';

    UPDATE channels
       SET report_count = v_total_broken,
           updated_at   = now()
     WHERE url_hash = p_url_hash;

    RETURN jsonb_build_object(
        'ok', true,
        'broken_count', v_total_broken,
        'working_count', v_total_working
    );
END;
$$;

REVOKE ALL ON FUNCTION report_channel_broken(TEXT, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION report_channel_broken(TEXT, TEXT) TO anon, authenticated;


-- ── 3. RPC: report_channel_working ───────────────────────────────────────
--
-- Records a positive vote and upserts channel_status with a real
-- report_count, finally making the `report_count >= 3` consensus rule fire.

CREATE OR REPLACE FUNCTION report_channel_working(
    p_url_hash  TEXT,
    p_device_id TEXT,
    p_response_time_ms INT DEFAULT NULL
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_recent_working INT;
    v_total_working  INT;
BEGIN
    IF p_url_hash IS NULL OR length(p_url_hash) < 8 THEN
        RETURN jsonb_build_object('ok', false, 'error', 'invalid_hash');
    END IF;
    IF p_device_id IS NULL OR length(p_device_id) < 8 THEN
        RETURN jsonb_build_object('ok', false, 'error', 'invalid_device');
    END IF;

    -- Per-device throttle: max 1 working vote per channel per 5 minutes.
    SELECT COUNT(*) INTO v_recent_working
    FROM channel_votes
    WHERE device_id = p_device_id
      AND url_hash  = p_url_hash
      AND vote      = 'working'
      AND created_at > now() - INTERVAL '5 minutes';

    IF v_recent_working = 0 THEN
        IF (SELECT COUNT(*) FROM channel_votes
            WHERE device_id = p_device_id
              AND created_at > now() - INTERVAL '1 hour') >= 200 THEN
            RETURN jsonb_build_object('ok', false, 'error', 'rate_limited');
        END IF;

        INSERT INTO channel_votes (url_hash, device_id, vote)
        VALUES (p_url_hash, p_device_id, 'working')
        ON CONFLICT (device_id, url_hash, vote)
            DO UPDATE SET created_at = now();
    END IF;

    SELECT COUNT(*) INTO v_total_working
    FROM channel_votes
    WHERE url_hash = p_url_hash
      AND vote = 'working'
      AND created_at > now() - INTERVAL '30 days';

    -- Sync the cache table the app actually reads.
    INSERT INTO channel_status (url_hash, status, last_checked,
                                response_time_ms, report_count)
    VALUES (p_url_hash, 'working', now(),
            p_response_time_ms, v_total_working)
    ON CONFLICT (url_hash) DO UPDATE
        SET status           = 'working',
            last_checked     = now(),
            response_time_ms = COALESCE(EXCLUDED.response_time_ms,
                                        channel_status.response_time_ms),
            report_count     = v_total_working;

    RETURN jsonb_build_object('ok', true, 'working_count', v_total_working);
END;
$$;

REVOKE ALL ON FUNCTION report_channel_working(TEXT, TEXT, INT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION report_channel_working(TEXT, TEXT, INT) TO anon, authenticated;


-- ── 4. RPC: promote_channel_source ───────────────────────────────────────
--
-- Atomic replacement for the GET-then-PATCH dance in
-- web/server.py::_promote_source_supabase. Looks up by url_hash (the new
-- working URL's hash) — no name escaping needed, no race on urls[].

CREATE OR REPLACE FUNCTION promote_channel_source(
    p_channel_name TEXT,
    p_working_url  TEXT,
    p_working_hash TEXT
) RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_urls    JSONB;
    v_new_urls JSONB;
BEGIN
    IF p_channel_name IS NULL OR length(p_channel_name) = 0 THEN
        RETURN jsonb_build_object('ok', false, 'error', 'invalid_name');
    END IF;
    IF p_working_url IS NULL OR p_working_hash IS NULL THEN
        RETURN jsonb_build_object('ok', false, 'error', 'invalid_url');
    END IF;

    -- Case-insensitive single-row match by exact name.
    SELECT urls INTO v_urls
    FROM channels
    WHERE lower(name) = lower(p_channel_name)
    LIMIT 1
    FOR UPDATE;

    IF v_urls IS NULL THEN
        RETURN jsonb_build_object('ok', false, 'error', 'not_found');
    END IF;

    -- Only promote if the URL is already in the list and not already first.
    IF NOT (v_urls ? p_working_url) THEN
        RETURN jsonb_build_object('ok', true, 'changed', false,
                                  'reason', 'url_not_in_list');
    END IF;

    IF v_urls->>0 = p_working_url THEN
        RETURN jsonb_build_object('ok', true, 'changed', false,
                                  'reason', 'already_primary');
    END IF;

    -- Build new array: [working_url, *(others without working_url)]
    SELECT jsonb_build_array(p_working_url) ||
           COALESCE(jsonb_agg(elem) FILTER (WHERE elem::text <> to_jsonb(p_working_url)::text),
                    '[]'::jsonb)
      INTO v_new_urls
      FROM jsonb_array_elements(v_urls) elem;

    UPDATE channels
       SET urls       = v_new_urls,
           url_hash   = p_working_hash,
           updated_at = now()
     WHERE lower(name) = lower(p_channel_name);

    RETURN jsonb_build_object('ok', true, 'changed', true);
END;
$$;

REVOKE ALL ON FUNCTION promote_channel_source(TEXT, TEXT, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION promote_channel_source(TEXT, TEXT, TEXT) TO anon, authenticated;


-- ── 5. RLS lockdown — revoke direct write access from anon ───────────────
--
-- Anon key ships inside every APK and every Docker image.  Direct UPDATE/
-- DELETE on `channels` lets any attacker rewrite the catalog.  After this
-- migration:
--   • channels       → anon may SELECT and INSERT (new contributions only).
--                       UPDATEs go through RPCs.
--   • channel_status → anon may SELECT and INSERT (existing rate-limited
--                       trigger handles updates).  Direct UPDATE removed.
--   • channel_votes  → anon may SELECT only.  All writes via RPCs.

-- channels
DROP POLICY IF EXISTS ch_anon_update ON channels;
DROP POLICY IF EXISTS ch_anon_delete ON channels;

-- channel_status (drop any over-broad UPDATE policy if present)
DROP POLICY IF EXISTS cs_anon_update ON channel_status;
DROP POLICY IF EXISTS cs_anon_delete ON channel_status;

-- Make sure SELECT + INSERT policies still exist (idempotent re-create).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'channels'
          AND policyname = 'ch_anon_select'
    ) THEN
        EXECUTE 'CREATE POLICY ch_anon_select ON channels FOR SELECT TO anon USING (true)';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'channels'
          AND policyname = 'ch_anon_insert'
    ) THEN
        EXECUTE 'CREATE POLICY ch_anon_insert ON channels FOR INSERT TO anon WITH CHECK (true)';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'channel_status'
          AND policyname = 'cs_anon_select'
    ) THEN
        EXECUTE 'CREATE POLICY cs_anon_select ON channel_status FOR SELECT TO anon USING (true)';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'channel_status'
          AND policyname = 'cs_anon_insert'
    ) THEN
        EXECUTE 'CREATE POLICY cs_anon_insert ON channel_status FOR INSERT TO anon WITH CHECK (true)';
    END IF;
END $$;


-- ── 6. Cleanup: drop stale votes nightly (≥90 days) ──────────────────────
-- A scheduled job is not created here; run via pg_cron if available:
--   SELECT cron.schedule('purge_old_votes', '0 3 * * *',
--     $$ DELETE FROM channel_votes WHERE created_at < now() - INTERVAL '90 days' $$);


-- ── 7. Marker row for the doctor script ──────────────────────────────────

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'tv_viewer_schema_version') THEN
        EXECUTE $f$
            CREATE OR REPLACE FUNCTION tv_viewer_schema_version()
            RETURNS TEXT LANGUAGE sql IMMUTABLE AS 'SELECT ''2.16.0''::text'
        $f$;
    ELSE
        EXECUTE 'CREATE OR REPLACE FUNCTION tv_viewer_schema_version()
                 RETURNS TEXT LANGUAGE sql IMMUTABLE AS ''SELECT ''''2.16.0''''::text''';
    END IF;
END $$;

GRANT EXECUTE ON FUNCTION tv_viewer_schema_version() TO anon, authenticated;
