# Supabase Security Hardening — Migration Guide

## Overview

This migration fixes **20 security warnings** identified by the Supabase linter across 3 critical categories:

| Category | Count | Severity | Fix |
|----------|-------|----------|-----|
| **Function Search Path Mutable** | 6 | HIGH | Add `SET search_path = public` |
| **Materialized Views in API** | 6 | MEDIUM | Revoke anon/authenticated access |
| **RLS Policies Always True** | 8 | HIGH | Add field validation constraints |

## Impact Assessment

### ✅ Safe Changes (No App Impact)
- **Search path fixes** — Internal security hardening, no behavioral change
- **Materialized view access** — These were never used by the app, only for admin dashboards
- **Duplicate policy removal** — `channels_update` was redundant with `ch_anon_update`

### ⚠️ Changes Requiring Testing
- **RLS policy tightening** — Adds validation constraints to INSERT/UPDATE operations
  - **analytics_events**: Validates `event_type` length (≤100), `event_data` size (≤10k)
  - **channel_status**: Validates `url_hash` format (64-char SHA-256), `status` enum values
  - **channels**: Validates `url_hash` format, `name` length (1-500), URL length (≤2048)
  - **channel_sources**: Validates hash formats, numeric ranges, enum values

### Expected Behavior
- **Before**: All anon INSERTs/UPDATEs succeeded (even with invalid data)
- **After**: Invalid data is rejected at the database level
- **App impact**: None — the app already sends valid data, constraints just formalize this

## How to Apply

### Option 1: Supabase SQL Editor (RECOMMENDED)

1. Open Supabase SQL Editor:
   ```
   https://cdtxpefohpwtusmqengu.supabase.co/project/cdtxpefohpwtusmqengu/sql
   ```

2. Copy/paste the entire contents of `scripts/supabase_security_fix.sql`

3. Click **Run** — the migration is idempotent (safe to run multiple times)

4. Verify success (should see no errors)

### Option 2: Python Script (Requires service_role key)

If you have the Supabase service_role key:

```bash
export SUPABASE_SERVICE_KEY="your-service-role-key-here"
python scripts/apply_security_fix.py
```

⚠️ **Note**: The anon key (in `config.py`) cannot execute DDL statements. You need the service_role key.

## Verification Steps

### 1. Check Functions Have search_path

```sql
SELECT 
    p.proname AS function_name,
    pg_get_function_identity_arguments(p.oid) AS args,
    (SELECT setting FROM pg_settings WHERE name = 'search_path') AS current_search_path,
    p.proconfig AS function_config
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname IN (
    'report_source_health',
    'refresh_analytics_views',
    'cleanup_old_data',
    'db_health',
    'truncate_channels',
    'check_channel_status_rate'
  );
```

Expected: Each function should have `proconfig = {search_path=public}` or similar.

### 2. Check Materialized Views Are Not in API

Try accessing as anon (should fail):

```bash
curl "https://cdtxpefohpwtusmqengu.supabase.co/rest/v1/mv_daily_active_users" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Expected: `403 Forbidden` or similar permission error.

### 3. Check RLS Policies Have Validation

```sql
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE tablename IN ('analytics_events', 'channel_status', 'channels', 'channel_sources')
  AND policyname LIKE '%anon%'
ORDER BY tablename, policyname;
```

Expected: `with_check` column should contain validation logic (not just `true`).

### 4. Test App Functionality

Run the app and verify:
- ✅ Analytics events are still recorded (check `analytics_events` table)
- ✅ Channel status updates still work (check `channel_status` table)
- ✅ Channel data can be inserted/updated (check `channels` table)
- ✅ No new errors in app logs related to database operations

## Rollback Plan

If issues occur, you can revert by:

1. **Functions**: Remove search_path setting:
   ```sql
   ALTER FUNCTION public.report_source_health(text, text, integer) RESET search_path;
   -- Repeat for other 5 functions
   ```

2. **Materialized views**: Re-grant access:
   ```sql
   GRANT SELECT ON public.mv_daily_active_users TO anon, authenticated;
   -- Repeat for other 5 views
   ```

3. **RLS policies**: Revert to bare `WITH CHECK (true)`:
   ```sql
   DROP POLICY IF EXISTS ae_anon_insert ON public.analytics_events;
   CREATE POLICY ae_anon_insert ON public.analytics_events
     FOR INSERT TO anon WITH CHECK (true);
   -- Repeat for other 7 policies
   ```

## Security Benefits

### 1. Search Path Injection Prevention
**Before**: Functions could be tricked into calling malicious functions from user-controlled schemas.
**After**: Functions always use `public` schema, ignoring `search_path` session variable.

**Attack scenario prevented**:
```sql
-- Attacker creates malicious schema
CREATE SCHEMA malicious;
CREATE FUNCTION malicious.now() RETURNS timestamptz AS $$
  SELECT '2099-01-01'::timestamptz;  -- Return fake timestamp
$$ LANGUAGE sql;

-- Without search_path fix, attacker could do:
SET search_path = malicious, public;
SELECT report_source_health('abc...', 'working', 100);
-- This would use malicious.now() instead of public.now()
```

### 2. API Surface Reduction
**Before**: 6 materialized views exposed via REST API (auto_rest_api enabled by default).
**After**: Views only accessible to service_role (admin dashboards).

**Impact**: Reduces attack surface — anonymous users can't query aggregate analytics data.

### 3. Data Validation at Database Level
**Before**: App could insert invalid data (wrong formats, excessive lengths, out-of-range values).
**After**: Database enforces constraints — invalid data rejected at the boundary.

**Example**: Prevents attacks like:
```python
# Before: This would succeed (storing garbage)
supabase.table('channels').insert({
    'url_hash': 'x' * 1000,  # Wrong length
    'name': 'A' * 10000,     # Excessive length
    'url': 'x' * 50000       # Excessive length
})

# After: Database rejects with constraint violation
```

## Technical Details

### Function Signatures Fixed

```sql
-- All now have SET search_path = public
public.report_source_health(text, text, integer)
public.refresh_analytics_views()
public.cleanup_old_data()
public.db_health()
public.truncate_channels()
public.check_channel_status_rate()  -- Trigger function
```

### Materialized Views Secured

```sql
-- Access revoked from anon/authenticated, granted to service_role only
public.mv_daily_active_users
public.mv_top_channels
public.mv_client_platforms
public.mv_favorite_channels
public.mv_crash_summary
public.mv_engagement
```

### RLS Policies Updated

| Table | Policy | Before | After |
|-------|--------|--------|-------|
| analytics_events | ae_anon_insert | `WITH CHECK (true)` | Validates event_type, event_data size |
| channel_status | cs_anon_insert | `WITH CHECK (true)` | Validates url_hash format, status enum |
| channel_status | cs_anon_update | `USING (true) WITH CHECK (true)` | Validates url_hash, status, response_time |
| channels | ch_anon_insert | `WITH CHECK (true)` | Validates url_hash, name, url lengths |
| channels | ch_anon_update | `USING (true) WITH CHECK (true)` | Same as INSERT + removes duplicate |
| channels | channels_update | Duplicate policy | **REMOVED** |
| channel_sources | csrc_anon_insert | `WITH CHECK (true)` | Validates hashes, url, numeric ranges |
| channel_sources | csrc_anon_update | `USING (true) WITH CHECK (true)` | Same as INSERT validation |

## Compliance & Standards

This migration aligns with:
- **OWASP Top 10**: A01:2021 - Broken Access Control
- **CWE-89**: SQL Injection (search path variant)
- **Supabase Best Practices**: Documented at https://supabase.com/docs/guides/database/security
- **Principle of Least Privilege**: Minimal necessary permissions for anon role

## Questions?

- **Why not use CHECK constraints instead of RLS policies?**  
  RLS policies are evaluated per-role, allowing different constraints for anon vs authenticated vs service_role.

- **Will this break existing data in the database?**  
  No — these are constraints on new INSERTs/UPDATEs only. Existing data is unchanged.

- **Can I run this migration multiple times?**  
  Yes — it's idempotent. Uses `DROP IF EXISTS` before `CREATE`, and `ALTER` is safe to repeat.

- **What if my app breaks after applying?**  
  Use the rollback plan above. File an issue with error logs so we can investigate.

## Change Log

- **2025-01-13**: Initial migration created (fixes 20 Supabase linter warnings)

---

**Status**: ✅ Ready to apply  
**Risk Level**: Low (no behavioral changes, adds safety constraints)  
**Testing Required**: Verify app telemetry still works after applying  
**Rollback**: Available (see Rollback Plan section)
