-- TV Viewer - Supabase analytics_events RLS setup
-- Run this script in the Supabase SQL Editor for a new project where
-- public.analytics_events already exists but anon access is blocked by RLS.
--
-- This script is safe to re-run.
-- It also avoids naming collisions with scripts\supabase_security_fix.sql,
-- which updates functions and view permissions rather than analytics policies.

BEGIN;

-- Step 1: Ensure the analytics table has the columns expected by the app.
-- channel_name is used by some analytics events for easier aggregation.
ALTER TABLE public.analytics_events
    ADD COLUMN IF NOT EXISTS channel_name text;

-- Step 2: Ensure the country column exists and defaults to 'XX' when omitted.
ALTER TABLE public.analytics_events
    ADD COLUMN IF NOT EXISTS country text;

ALTER TABLE public.analytics_events
    ALTER COLUMN country SET DEFAULT 'XX';

-- Step 3: Grant table privileges to anon.
-- RLS policies are required, but table privileges must also allow INSERT/SELECT.
GRANT INSERT, SELECT ON TABLE public.analytics_events TO anon;

-- Step 4: Keep RLS enabled on the table.
-- Re-enabling RLS is harmless and makes the script self-contained.
ALTER TABLE public.analytics_events ENABLE ROW LEVEL SECURITY;

-- Step 5: Allow the anon role to insert analytics events.
-- WITH CHECK (true) accepts any row submitted by the client.
DROP POLICY IF EXISTS analytics_events_anon_insert ON public.analytics_events;
CREATE POLICY analytics_events_anon_insert
    ON public.analytics_events
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Step 6: Allow the anon role to read analytics events for aggregation queries.
DROP POLICY IF EXISTS analytics_events_anon_select ON public.analytics_events;
CREATE POLICY analytics_events_anon_select
    ON public.analytics_events
    FOR SELECT
    TO anon
    USING (true);

COMMIT;

-- Optional verification query: confirm anon INSERT/SELECT policies exist.
SELECT policyname, cmd, roles, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename = 'analytics_events'
ORDER BY policyname;
