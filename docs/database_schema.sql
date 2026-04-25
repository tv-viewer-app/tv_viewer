-- Supabase Database Schema for TV Viewer Shared Channel Status
-- Issue #31: Shared online database for channel scan results
--
-- This schema creates a table to store channel validation results
-- that can be shared across all TV Viewer clients (Android + Windows)
--
-- Usage:
-- 1. Open Supabase SQL Editor
-- 2. Copy and paste this entire file
-- 3. Click "Run" (or press F5)
-- 4. Verify "Success. No rows returned"

-- ============================================================================
-- Table: channel_status
-- ============================================================================
-- Stores validation results for IPTV channels
-- Primary key: url_hash (SHA256 hash of channel URL for privacy)

CREATE TABLE IF NOT EXISTS channel_status (
    -- SHA256 hash of the channel URL (64 chars, hex)
    -- Privacy: Raw URLs are never stored
    url_hash TEXT PRIMARY KEY,
    
    -- Channel status: 'working' or 'failed'
    -- Constrained to these two values only
    status TEXT NOT NULL CHECK (status IN ('working', 'failed')),
    
    -- When this channel was last validated (UTC)
    -- Default: Current timestamp
    last_checked TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Response time in milliseconds (optional)
    -- NULL if channel failed or timed out
    response_time_ms INTEGER,
    
    -- When this record was first created (UTC)
    -- Useful for analytics and cleanup
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- Indexes
-- ============================================================================
-- Speed up queries that filter by last_checked
-- Enables efficient "fetch channels checked in last 24h" queries

CREATE INDEX IF NOT EXISTS idx_channel_status_last_checked 
    ON channel_status(last_checked DESC);

-- Optional: Index for status filtering (uncomment if needed)
-- CREATE INDEX IF NOT EXISTS idx_channel_status_status 
--     ON channel_status(status);

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================
-- Enable RLS to control access with policies

ALTER TABLE channel_status ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all users to read (SELECT)
-- Anonymous users can fetch recent validation results
CREATE POLICY "Allow anonymous reads"
    ON channel_status
    FOR SELECT
    USING (true);

-- Policy: Allow all users to insert (INSERT)
-- Anonymous users can contribute new validation results
CREATE POLICY "Allow anonymous inserts"
    ON channel_status
    FOR INSERT
    WITH CHECK (true);

-- Policy: Allow all users to update (UPDATE)
-- Enables upsert (insert or update on conflict)
CREATE POLICY "Allow anonymous updates"
    ON channel_status
    FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- Note: DELETE is not allowed - records persist until manual cleanup

-- ============================================================================
-- Comments (Documentation)
-- ============================================================================
-- Add helpful comments for database schema documentation

COMMENT ON TABLE channel_status IS 
    'Shared channel validation results across TV Viewer clients (Issue #31). ' ||
    'URLs are hashed with SHA256 for privacy. Anonymous read/write access enabled.';

COMMENT ON COLUMN channel_status.url_hash IS 
    'SHA256 hash of channel URL for privacy (64 hex characters)';

COMMENT ON COLUMN channel_status.status IS 
    'Channel validation status: ''working'' or ''failed''';

COMMENT ON COLUMN channel_status.last_checked IS 
    'Last validation timestamp in UTC. Used for 24h cache TTL.';

COMMENT ON COLUMN channel_status.response_time_ms IS 
    'HTTP response time in milliseconds. NULL for failed/timeout channels.';

COMMENT ON COLUMN channel_status.created_at IS 
    'Record creation timestamp. Useful for analytics and cleanup.';

-- ============================================================================
-- Verification Queries (Optional)
-- ============================================================================
-- Uncomment and run these to verify the setup

-- View table structure
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'channel_status'
-- ORDER BY ordinal_position;

-- Check indexes
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'channel_status';

-- Check RLS policies
-- SELECT policyname, permissive, roles, cmd, qual, with_check
-- FROM pg_policies
-- WHERE tablename = 'channel_status';

-- ============================================================================
-- Maintenance (Optional)
-- ============================================================================
-- Uncomment these for manual database maintenance

-- Delete records older than 7 days (run periodically to keep DB lean)
-- DELETE FROM channel_status 
-- WHERE last_checked < NOW() - INTERVAL '7 days';

-- View statistics
-- SELECT 
--     status,
--     COUNT(*) as count,
--     AVG(response_time_ms) as avg_response_ms,
--     MAX(last_checked) as most_recent
-- FROM channel_status
-- GROUP BY status;

-- ============================================================================
-- Setup Complete!
-- ============================================================================
-- Next steps:
-- 1. Go to Settings > API in Supabase dashboard
-- 2. Copy your "Project URL" and "anon public" API key
-- 3. Update the TV Viewer app configurations:
--    - Flutter: shared_db_service.dart
--    - Python: shared_db.py
-- 4. Set enabled flags to true
-- 5. Test the integration!
--
-- For detailed instructions, see: SHARED_DATABASE_SETUP.md
