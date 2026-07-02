-- Mark channels as stale if they have been broken long enough to auto-hide.
-- Run this in the Supabase SQL editor once, then invoke the RPC weekly from
-- .github/workflows/channel-cleanup.yml.

ALTER TABLE channel_status
    ADD COLUMN IF NOT EXISTS stale BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN channel_status.stale IS
    'True when a channel has been broken for 7+ days with 10+ broken reports and should be hidden from default browsing.';

CREATE INDEX IF NOT EXISTS idx_channel_status_stale_true
    ON channel_status (stale)
    WHERE stale = TRUE;

CREATE OR REPLACE FUNCTION mark_stale_channels()
RETURNS TABLE(marked_stale INTEGER, cleared_stale INTEGER, total_stale INTEGER)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_marked  INTEGER := 0;
    v_cleared INTEGER := 0;
    v_total   INTEGER := 0;
BEGIN
    UPDATE channel_status
       SET stale = TRUE
     WHERE stale IS DISTINCT FROM TRUE
       AND status IN ('broken', 'failed', 'offline', 'stale')
       AND report_count >= 10
       AND last_checked < NOW() - INTERVAL '7 days';
    GET DIAGNOSTICS v_marked = ROW_COUNT;

    UPDATE channel_status
       SET stale = FALSE
     WHERE stale IS DISTINCT FROM FALSE
       AND NOT (
           status IN ('broken', 'failed', 'offline', 'stale')
           AND report_count >= 10
           AND last_checked < NOW() - INTERVAL '7 days'
       );
    GET DIAGNOSTICS v_cleared = ROW_COUNT;

    SELECT COUNT(*)
      INTO v_total
      FROM channel_status
     WHERE stale = TRUE;

    RETURN QUERY
    SELECT v_marked, v_cleared, v_total;
END;
$$;

REVOKE ALL ON FUNCTION mark_stale_channels() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mark_stale_channels() TO authenticated, service_role;

-- Preview stale channels after the RPC runs.
SELECT url_hash, status, report_count, last_checked, stale
FROM channel_status
WHERE stale = TRUE
ORDER BY report_count DESC, last_checked ASC;
