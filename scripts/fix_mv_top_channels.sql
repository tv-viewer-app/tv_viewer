-- =============================================================================
-- Fix #195: refresh_analytics_views() failing with duplicate-key on idx_mv_top
-- =============================================================================
-- Root cause: mv_top_channels groups by (channel_hash, country, category)
-- but the UNIQUE INDEX backing CONCURRENTLY refresh covers only channel_hash.
-- Same channel hash can legitimately appear under multiple (country, category)
-- pairs (e.g. a channel mis-tagged in two playlists), so the upsert phase
-- of CONCURRENTLY refresh blows up with 23505.
--
-- Fix: rebuild the MV with COALESCE on nullable group-by cols (so the unique
-- key stays NOT NULL — required for CONCURRENTLY refresh) and widen the
-- unique index to match the actual primary key of the result set.
-- =============================================================================

DROP MATERIALIZED VIEW IF EXISTS public.mv_top_channels CASCADE;

CREATE MATERIALIZED VIEW public.mv_top_channels AS
SELECT
    event_data->>'url_hash'                          AS channel_hash,
    COALESCE(NULLIF(event_data->>'country',  ''), 'XX') AS channel_country,
    COALESCE(NULLIF(event_data->>'category', ''), '')   AS channel_category,
    COUNT(*)                                         AS play_count,
    COUNT(DISTINCT device_id)                        AS unique_players,
    MAX(created_at)                                  AS last_played
FROM public.analytics_events
WHERE event_type = 'channel_play'
  AND event_data->>'url_hash' IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY play_count DESC
LIMIT 1000;

CREATE UNIQUE INDEX idx_mv_top
    ON public.mv_top_channels (channel_hash, channel_country, channel_category);

-- Refresh once so it's populated before the next CONCURRENTLY call (which
-- requires at least one prior REFRESH).
REFRESH MATERIALIZED VIEW public.mv_top_channels;

-- Sanity: refresh_analytics_views() should now succeed end-to-end.
SELECT public.refresh_analytics_views();
