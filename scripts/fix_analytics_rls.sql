-- Fix analytics_events RLS policy for anon INSERT
-- The existing policy validates event_type and event_data, but the table
-- has device_id NOT NULL which must also be checked in the policy.
-- Run this in the Supabase SQL Editor.

-- Drop and recreate the INSERT policy with correct validation
DROP POLICY IF EXISTS "ae_anon_insert" ON public.analytics_events;
DROP POLICY IF EXISTS ae_anon_insert ON public.analytics_events;

CREATE POLICY "ae_anon_insert" ON public.analytics_events
  FOR INSERT TO anon
  WITH CHECK (
    -- Required fields
    device_id IS NOT NULL AND
    length(device_id) <= 64 AND
    event_type IS NOT NULL AND
    length(event_type) <= 100 AND
    -- Validate event_data size if present
    (event_data IS NULL OR length(event_data::text) <= 10000)
  );

-- Ensure RLS is enabled
ALTER TABLE public.analytics_events ENABLE ROW LEVEL SECURITY;

-- Verify: should show ae_anon_insert for INSERT
SELECT policyname, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'analytics_events';
