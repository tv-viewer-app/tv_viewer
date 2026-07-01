-- Grant publishable/anon role access to analytics materialized views
-- Run this in Supabase SQL Editor

-- Allow anon to read pre-aggregated analytics views (no raw data exposed)
GRANT SELECT ON public.mv_top_channels TO anon;
GRANT SELECT ON public.mv_daily_active_users TO anon;

-- Also add SELECT policy on analytics_events for anon
-- This allows the statistics endpoint to work with publishable key
ALTER TABLE public.analytics_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS anon_read_analytics ON public.analytics_events;
CREATE POLICY anon_read_analytics ON public.analytics_events FOR SELECT TO anon USING (true);

-- Verify
SELECT 'mv_top_channels' as view_name, count(*) from mv_top_channels
UNION ALL
SELECT 'mv_daily_active_users', count(*) from mv_daily_active_users;
