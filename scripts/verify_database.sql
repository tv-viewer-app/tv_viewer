-- =============================================================================
-- TV Viewer — Supabase Database Verification
-- Run in Supabase SQL Editor (Role: postgres)
-- =============================================================================

-- Check 1: RPC functions are SECURITY DEFINER
SELECT proname, pronargs, prosecdef as is_security_definer
FROM pg_proc
WHERE proname IN ('report_channel_working', 'report_channel_broken');
-- EXPECTED: both rows show is_security_definer = true

-- Check 2: Materialized views exist
SELECT schemaname, matviewname 
FROM pg_matviews 
WHERE matviewname IN ('mv_top_channels', 'mv_daily_active_users');
-- EXPECTED: 2 rows

-- Check 3: Anon role has SELECT on materialized views
SELECT grantee, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE table_name IN ('mv_top_channels', 'mv_daily_active_users')
  AND grantee = 'anon';
-- EXPECTED: 2 rows with privilege_type = SELECT

-- Check 4: Anon role can EXECUTE the RPC functions
SELECT grantee, routine_name, privilege_type
FROM information_schema.role_routine_grants
WHERE routine_name IN ('report_channel_working', 'report_channel_broken')
  AND grantee = 'anon';
-- EXPECTED: 2 rows with privilege_type = EXECUTE

-- Check 5: Views have data
SELECT 'mv_top_channels' as view_name, count(*) as rows FROM mv_top_channels
UNION ALL
SELECT 'mv_daily_active_users', count(*) FROM mv_daily_active_users;
-- EXPECTED: both have rows > 0
