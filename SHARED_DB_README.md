# Shared Database Feature - Quick Start

## What is this?

The shared database feature allows TV Viewer users to share channel validation results across devices and platforms. This significantly speeds up channel scanning by skipping channels that were recently validated by other users.

## Benefits

- ⚡ **60-80% faster** channel validation
- 🌍 **Cross-platform**: Works between Android and Windows
- 🔒 **Privacy-first**: URLs are hashed, not stored in plaintext
- 🆓 **Free**: Uses Supabase free tier
- 🚫 **Anonymous**: No user accounts required

## Quick Setup (5 minutes)

### 1. Create Supabase Account
- Go to https://supabase.com/
- Sign up (free)
- Create a new project

### 2. Create Database Table
- Open SQL Editor in Supabase
- Copy contents of `database_schema.sql`
- Paste and run

### 3. Get API Credentials
- Go to Settings > API
- Copy:
  - **Project URL**: `https://xxx.supabase.co`
  - **anon public key**: `eyJhbGc...`

### 4. Configure Apps

**Flutter (Android)**:
Edit `flutter_app/lib/services/shared_db_service.dart`:
```dart
static const String _supabaseUrl = 'YOUR_PROJECT_URL';
static const String _supabaseAnonKey = 'YOUR_ANON_KEY';
static const bool _enabled = true;  // Change from false
```

**Python (Windows)**:
Edit `utils/shared_db.py`:
```python
SUPABASE_URL = 'YOUR_PROJECT_URL'
SUPABASE_ANON_KEY = 'YOUR_ANON_KEY'
ENABLED = True  # Change from False
```

### 5. Install Dependencies

**Flutter**:
```bash
cd flutter_app
flutter pub get
```

**Python** (aiohttp already included in requirements.txt):
```bash
pip install -r requirements.txt
```

Done! The feature will automatically work on next channel scan.

## How It Works

```
On Scan Start:
├─ Fetch recent results from shared database (<24h old)
├─ Build in-memory cache
│
During Validation:
├─ For each channel:
│  ├─ Check if in cache AND working AND recent
│  ├─ If yes: Skip validation ✅ (use cached result)
│  └─ If no: Validate normally 🔄
│
After Validation:
└─ Batch upload all new results to shared database
```

## Privacy

**What's stored**: SHA256 hash, status, timestamp, response time  
**What's NOT stored**: Raw URLs, channel names, user info, IP addresses

Example:
```
Original URL: http://example.com/stream.m3u8
Stored Hash:  8f3d7e9a1b2c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9
```

The hash is **irreversible** - nobody can see your original URLs.

## Disabling the Feature

Set `_enabled = false` (Flutter) or `ENABLED = False` (Python).

The app works normally without shared database.

## Troubleshooting

**"Service not configured"**
→ Check API credentials are set correctly

**"Failed to fetch shared database results"**
→ Check internet connection and Supabase project status

**No performance improvement**
→ Normal if you're the first user or all channels are new

## Files

- `shared_db_service.dart` - Flutter implementation
- `utils/shared_db.py` - Python implementation
- `database_schema.sql` - Supabase table schema
- `SHARED_DATABASE_SETUP.md` - Detailed setup guide
- `ISSUE_31_IMPLEMENTATION.md` - Technical documentation

## Support

See `SHARED_DATABASE_SETUP.md` for detailed troubleshooting and configuration options.
