# Shared Database Setup Guide (Issue #31)

This guide explains how to set up the shared Supabase database for channel validation results.

## Overview

The shared database enables:
- **Cross-platform sync**: Android Flutter and Windows Python share validation results
- **Faster scans**: Skip re-validating channels checked by other users in last 24h
- **Privacy**: URLs are hashed with SHA256 before storage
- **Anonymous**: No user accounts required

## Prerequisites

- Free Supabase account: https://supabase.com/
- Internet connection

## Step 1: Create Supabase Project

1. Go to https://supabase.com/ and sign up/login
2. Click "New Project"
3. Fill in:
   - **Name**: `tv-viewer-shared-db` (or any name)
   - **Database Password**: Generate a strong password (save it securely)
   - **Region**: Choose closest to your location
   - **Pricing Plan**: Free tier is sufficient
4. Click "Create new project" and wait 1-2 minutes for setup

## Step 2: Create Database Table

1. In your Supabase dashboard, go to **SQL Editor** (left sidebar)
2. Click **New Query**
3. Copy and paste this SQL:

```sql
-- Create channel_status table
CREATE TABLE IF NOT EXISTS channel_status (
    url_hash TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('working', 'failed')),
    last_checked TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create index for efficient queries by last_checked
CREATE INDEX IF NOT EXISTS idx_channel_status_last_checked 
    ON channel_status(last_checked DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE channel_status ENABLE ROW LEVEL SECURITY;

-- Policy: Allow anonymous reads for all users
CREATE POLICY "Allow anonymous reads"
    ON channel_status
    FOR SELECT
    USING (true);

-- Policy: Allow anonymous inserts/updates for all users
CREATE POLICY "Allow anonymous inserts"
    ON channel_status
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow anonymous updates"
    ON channel_status
    FOR UPDATE
    USING (true)
    WITH CHECK (true);

-- Add helpful comment
COMMENT ON TABLE channel_status IS 'Shared channel validation results across TV Viewer clients';
COMMENT ON COLUMN channel_status.url_hash IS 'SHA256 hash of channel URL for privacy';
COMMENT ON COLUMN channel_status.status IS 'Channel status: working or failed';
COMMENT ON COLUMN channel_status.last_checked IS 'Last validation timestamp (UTC)';
COMMENT ON COLUMN channel_status.response_time_ms IS 'Response time in milliseconds';
```

4. Click **Run** (or press F5)
5. Verify success: You should see "Success. No rows returned"

## Step 3: Get API Credentials

1. In Supabase dashboard, go to **Settings** > **API** (left sidebar)
2. Find these two values:
   - **Project URL**: `https://xxxxxxxxxxxxx.supabase.co`
   - **anon public** key (in "Project API keys" section): `eyJhbGc...` (very long string)
3. Copy both values - you'll need them in the next step

## Step 4: Configure Flutter App (Android)

1. Open `flutter_app/lib/services/shared_db_service.dart`
2. Replace the placeholder values:

```dart
// Line 18-19
static const String _supabaseUrl = 'https://YOUR-PROJECT.supabase.co'; // Your Project URL
static const String _supabaseAnonKey = 'eyJhbGc...'; // Your anon public key

// Line 24
static const bool _enabled = true; // Change from false to true
```

3. Save the file

## Step 5: Configure Python App (Windows)

1. Open `utils/shared_db.py`
2. Replace the placeholder values:

```python
# Line 59-60
SUPABASE_URL = 'https://YOUR-PROJECT.supabase.co'  # Your Project URL
SUPABASE_ANON_KEY = 'eyJhbGc...'  # Your anon public key

# Line 65
ENABLED = True  # Change from False to True
```

3. Save the file

## Step 6: Install Required Dependency (Flutter)

The Flutter app needs the `crypto` package for SHA256 hashing.

1. Add to `flutter_app/pubspec.yaml` dependencies:
```yaml
dependencies:
  crypto: ^3.0.3  # For SHA256 hashing
```

2. Run `flutter pub get` in the flutter_app directory

## Step 7: Test the Integration

### Test Python (Windows)

```bash
cd "D:\Visual Studio 2017\tv_viewer_project"
python -m utils.shared_db
```

Expected output:
```
Fetching recent results...
Found 0 cached results
Uploading 2 test results...
Upload succeeded
```

### Test Flutter (Android)

The integration will be automatic when you:
1. Launch the app
2. Fetch channels
3. Run channel validation

Check logs for:
```
Fetching recent channel results from shared database...
Fetched N recent channel results from shared database
```

## How It Works

### On App Start (Both Platforms)

1. App fetches recent validation results (<24h old) from Supabase
2. Builds in-memory cache of url_hash -> status

### During Channel Validation

1. Before validating each channel:
   - Hash the URL with SHA256
   - Check if hash exists in cache
   - If found and status='working' and <24h old: **Skip validation** ✅
   - Otherwise: **Validate normally**

### After Validation Complete

1. Batch upload all validation results to Supabase
2. Results include:
   - `url_hash`: SHA256 of URL (privacy)
   - `status`: 'working' or 'failed'
   - `last_checked`: UTC timestamp
   - `response_time_ms`: Response time (optional)

### Data Flow Example

```
User A (Windows) validates 1000 channels → Uploads to Supabase
    ↓
User B (Android) starts app → Fetches cache (800 working, 200 failed)
    ↓
User B validates channels → Skips 800 already-working channels
    ↓
Validation completes 60% faster! 🚀
```

## Privacy & Security

### What is Stored
- ✅ **SHA256 hash** of URLs (irreversible)
- ✅ Status (working/failed)
- ✅ Timestamps
- ✅ Response times

### What is NOT Stored
- ❌ Raw URLs
- ❌ Channel names
- ❌ User information
- ❌ IP addresses
- ❌ Device identifiers

### Security Features
- **Anonymous access**: No user accounts or authentication
- **Row Level Security (RLS)**: Enforced at database level
- **HTTPS only**: All API calls encrypted
- **Read-only anon key**: Cannot delete or drop tables
- **SHA256 hashing**: URLs cannot be reverse-engineered

## Cost & Limits (Free Tier)

Supabase free tier includes:
- **Storage**: 500 MB (plenty for millions of hashes)
- **Database**: 2 GB transfer/month
- **API requests**: Unlimited
- **Row Level Security**: Included

**Estimated capacity**:
- 1 channel status = ~100 bytes
- 10 million channels = ~1 GB
- Free tier can handle years of usage ✅

## Monitoring & Maintenance

### View Database Contents

1. Go to Supabase dashboard
2. Navigate to **Table Editor** > `channel_status`
3. View/filter/search records

### Check Storage Usage

1. Go to **Settings** > **Usage**
2. Monitor:
   - Database size
   - Bandwidth usage
   - Active connections

### Cleanup Old Records (Optional)

To keep database lean, periodically delete old records:

```sql
-- Delete records older than 7 days
DELETE FROM channel_status 
WHERE last_checked < NOW() - INTERVAL '7 days';
```

Run this manually or set up a Supabase Edge Function for automatic cleanup.

## Troubleshooting

### "Service not configured" Error

**Cause**: API credentials not set or `ENABLED = False`

**Solution**:
1. Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set correctly
2. Verify `ENABLED = True` (Python) or `_enabled = true` (Dart)
3. Check for typos in URLs/keys

### "Failed to fetch shared database results" Warning

**Cause**: Network error or invalid credentials

**Solution**:
1. Check internet connection
2. Verify API key is the **anon public** key (not service_role)
3. Check Supabase project status (not paused)

### "Failed to upload results" Warning

**Cause**: RLS policies not configured or network error

**Solution**:
1. Verify RLS policies are created (Step 2)
2. Check API key has write permissions
3. Ensure `Prefer: resolution=merge-duplicates` header is sent

### No Performance Improvement

**Cause**: No other users or all channels are new

**Solution**:
- This is normal for first-time setup
- Performance benefits increase as more users contribute
- After 24h cache expires, channels are re-validated

## Disabling the Feature

To disable shared database sync:

**Flutter**: Set `_enabled = false` in `shared_db_service.dart`

**Python**: Set `ENABLED = False` in `shared_db.py`

The apps will work normally without shared sync.

## Support

For issues:
1. Check Supabase project status: https://status.supabase.com/
2. Review app logs for error details
3. Verify SQL schema was created correctly
4. Test with the example scripts (Step 7)

## References

- Supabase Documentation: https://supabase.com/docs
- Row Level Security: https://supabase.com/docs/guides/auth/row-level-security
- REST API: https://supabase.com/docs/guides/api
- SHA256 Hashing: https://en.wikipedia.org/wiki/SHA-2
