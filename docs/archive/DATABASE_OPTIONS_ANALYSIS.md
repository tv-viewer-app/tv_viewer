# Database Options Analysis for Shared Channel Scan Results
**GitHub Issue #31** | TV Viewer Project  
**Date**: January 2026  
**Context**: Replacing PrivateBin with a real-time database for shared channel validation results

---

## Executive Summary

**Recommended Solution**: **Firebase Realtime Database**

Firebase offers the best balance of features for this use case:
- ✅ True anonymous access (no user accounts required)
- ✅ Generous free tier (50K concurrent connections, 1GB storage, 10GB/month download)
- ✅ Real-time synchronization out-of-the-box
- ✅ Mature SDKs for Flutter and Python
- ✅ Built-in TTL via Security Rules
- ✅ Global CDN with low latency
- ✅ Zero setup cost (managed service)

---

## 1. Detailed Comparison Table

| Feature | Firebase Realtime DB | Supabase | PocketBase | Cloudflare D1 | Upstash Redis |
|---------|---------------------|----------|------------|---------------|---------------|
| **Anonymous Access** | ✅ Yes (via Security Rules) | ⚠️ Requires API key management | ⚠️ Requires custom auth | ⚠️ Requires Workers setup | ✅ Yes (REST API) |
| **Free Tier Storage** | 1GB | 500MB | Self-hosted (unlimited) | 5GB | 256MB |
| **Free Tier Bandwidth** | 10GB/month | 2GB/month | Self-hosted (unlimited) | 10M reads/day | 10K commands/day |
| **Concurrent Connections** | 50K | 500 | Unlimited (self-hosted) | N/A (REST) | N/A (REST) |
| **Real-time Sync** | ✅ WebSocket/SSE | ✅ PostgreSQL realtime | ⚠️ Realtime subscriptions | ❌ REST only | ⚠️ Pub/Sub (separate) |
| **Flutter SDK** | ✅ Official (firebase_database) | ✅ Official (supabase_flutter) | ⚠️ Community (pocketbase_drift) | ❌ HTTP only | ⚠️ Community |
| **Python SDK** | ✅ firebase-admin | ✅ supabase-py | ✅ pocketbase-py | ✅ CloudFlare API | ✅ upstash-redis |
| **Setup Complexity** | ⭐ Low (Firebase Console) | ⭐⭐ Medium (Supabase Dashboard) | ⭐⭐⭐ High (self-host) | ⭐⭐⭐ High (Workers + bindings) | ⭐⭐ Medium (Upstash Console) |
| **Data TTL/Expiry** | ✅ Via Cloud Functions | ✅ Via pg_cron | ✅ Via SQLite triggers | ⚠️ Manual cleanup | ✅ Native TTL |
| **Global Latency** | <100ms (15 regions) | <150ms (9 regions) | Depends on host | <50ms (edge) | <100ms (global) |
| **Query Capabilities** | Basic (JSON tree) | ✅✅ Full SQL | ✅✅ SQLite queries | ✅✅ SQL (D1) | Basic (key-value) |
| **Offline Support** | ✅ Built-in | ✅ Built-in | ✅ Built-in | ❌ None | ❌ None |
| **Privacy/GDPR** | ✅ Compliant (Google) | ✅ Compliant (EU region) | ✅ Full control | ✅ Compliant (Cloudflare) | ✅ Compliant |
| **Cost at Scale** | Low (pay-as-you-go) | Medium | Infrastructure only | Very Low (Workers free tier) | Low |
| **Vendor Lock-in** | ⚠️ High (Google) | Low (open source) | None (self-hosted) | High (Cloudflare) | Medium |

---

## 2. Detailed Option Analysis

### Option 1: Firebase Realtime Database ⭐ RECOMMENDED

**Strengths:**
- **Zero Configuration**: Create project in Firebase Console, add config to apps
- **True Anonymous**: No API key exposure - Security Rules handle access control
- **Real-time by Design**: WebSocket connections with automatic reconnection
- **Mature Ecosystem**: 10+ years of development, extensive documentation
- **Automatic Scaling**: No infrastructure management required
- **Cross-platform**: Works identically on Flutter Android and Python Windows

**Weaknesses:**
- **Limited Queries**: No complex SQL - data must be denormalized
- **JSON Structure**: Forces tree-like data modeling (not relational)
- **Vendor Lock-in**: Tightly coupled to Google Cloud Platform
- **No Built-in TTL**: Requires Cloud Functions for automatic expiry

**Free Tier Limits:**
- Storage: 1GB
- Bandwidth: 10GB/month download
- Concurrent connections: 100 (Spark plan) / 200K (Blaze pay-as-you-go)
- Operations: Unlimited

**Best For**: Real-time apps needing simple data structures, minimal setup, and anonymous access.

---

### Option 2: Supabase

**Strengths:**
- **Open Source**: Can self-host if needed (PostgreSQL + PostgREST)
- **Full SQL**: Complex queries, joins, stored procedures
- **Realtime**: PostgreSQL WAL subscriptions for change notifications
- **Built-in Auth**: Row-level security with JWT tokens
- **Storage**: Built-in file storage (useful for future features)

**Weaknesses:**
- **API Key Required**: Flutter/Python must embed anon key (can be extracted)
- **Complex Setup**: Multiple services (PostgREST, Realtime, Storage)
- **Connection Limits**: 500 concurrent on free tier (may be limiting)
- **Learning Curve**: PostgreSQL + PostgREST + Security policies

**Free Tier Limits:**
- Storage: 500MB database
- Bandwidth: 2GB/month
- API requests: 50K/month
- Concurrent realtime connections: 500

**Best For**: Apps needing complex queries, already using PostgreSQL, or planning self-hosting.

---

### Option 3: PocketBase

**Strengths:**
- **Self-Hosted**: Complete control over data and infrastructure
- **Single Binary**: Entire backend in one Go executable (<15MB)
- **SQLite**: Fast, reliable, zero configuration database
- **Realtime Subscriptions**: WebSocket support for live updates
- **Admin Dashboard**: Built-in UI for data management

**Weaknesses:**
- **Hosting Required**: Need server/VPS (costs money or complexity)
- **Scaling**: SQLite has write concurrency limits
- **No CDN**: Single-server deployment (higher latency for global users)
- **Maintenance**: You handle backups, updates, security patches
- **Not "Anonymous"**: Still need API authentication

**Free Tier**: N/A (self-hosted - requires VPS ~$5-10/month)

**Best For**: Privacy-focused projects, existing server infrastructure, full control requirements.

---

### Option 4: Cloudflare D1

**Strengths:**
- **Edge Computing**: Runs on Cloudflare's global network (300+ cities)
- **Ultra-Low Latency**: <50ms anywhere in the world
- **Full SQL**: SQLite with D1's distributed consistency layer
- **Free Tier**: 5GB storage, 10M reads/day, 100K writes/day
- **Cost-Effective**: Workers free tier is generous

**Weaknesses:**
- **No Real-time**: REST API only (polling required)
- **Complex Setup**: Requires Cloudflare Workers knowledge
- **No Native SDKs**: HTTP requests only (Flutter/Python)
- **Beta Status**: Still evolving, breaking changes possible
- **Wrangler CLI**: Deploy via command line (no GUI)

**Free Tier Limits:**
- Storage: 5GB
- Read operations: 10M/day (unlimited databases)
- Write operations: 100K/day
- Workers requests: 100K/day

**Best For**: Edge-first apps, read-heavy workloads, already using Cloudflare.

---

### Option 5: Upstash Redis

**Strengths:**
- **Native TTL**: Built-in expiration (perfect for 4-hour requirement)
- **REST API**: Easy integration without persistent connections
- **Serverless**: Pay-per-request pricing model
- **Fast**: In-memory performance for reads
- **Simple**: Key-value model is easy to understand

**Weaknesses:**
- **No Real-time**: Polling required (or separate Pub/Sub)
- **Limited Queries**: Key-value only (no complex searches)
- **Small Free Tier**: 256MB storage (may be limiting)
- **No Offline**: REST-only means no offline support
- **Data Structure**: Redis data types may be overkill

**Free Tier Limits:**
- Storage: 256MB
- Commands: 10K/day
- Bandwidth: 200MB/day
- Max request size: 1MB

**Best For**: Caching layers, session storage, simple key-value with TTL needs.

---

## 3. Recommended Solution: Firebase Realtime Database

### Justification

**Primary Reasons:**
1. **Anonymous Access**: Security Rules allow writes without authentication - perfect for open-source project
2. **Real-time**: Native WebSocket sync means instant updates across all clients
3. **Free Tier**: 1GB storage + 10GB bandwidth covers thousands of users
4. **Developer Experience**: Official SDKs for Flutter and Python eliminate integration pain
5. **Reliability**: Google's infrastructure ensures 99.95% uptime SLA
6. **TTL Workaround**: Cloud Functions (free tier: 2M invocations/month) can clean old data

**Why Not Others?**
- **Supabase**: Requires API key management (security concern for open source)
- **PocketBase**: Self-hosting adds cost + maintenance burden
- **Cloudflare D1**: No real-time support (defeats the purpose)
- **Upstash Redis**: 256MB free tier may be insufficient, no real-time

### Security Considerations
- **No PII**: Only URL hashes and validation status stored
- **Public Read**: Anyone can read scan results (acceptable for open-source)
- **Rate Limiting**: Firebase Security Rules prevent abuse
- **No Deletion Tokens**: Like PrivateBin, we don't allow deletion (immutable scans)

---

## 4. Implementation Approach - Flutter Android App

### 4.1 Dependencies

**pubspec.yaml:**
```yaml
dependencies:
  firebase_core: ^3.3.0          # Firebase initialization
  firebase_database: ^11.0.0     # Realtime Database
  connectivity_plus: ^6.0.0      # Network status
```

### 4.2 Firebase Configuration

**1. Firebase Console Setup:**
- Create Firebase project at https://console.firebase.google.com
- Add Android app with package name `com.tvviewer.app`
- Download `google-services.json` → `android/app/`
- Enable Realtime Database in Firebase Console

**2. Android Build Configuration:**

**android/build.gradle:**
```gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.1'
    }
}
```

**android/app/build.gradle:**
```gradle
apply plugin: 'com.google.gms.google-services'
```

### 4.3 Database Service Implementation

**lib/services/firebase_scan_service.dart:**
```dart
import 'package:firebase_database/firebase_database.dart';
import 'package:firebase_core/firebase_core.dart';
import 'dart:convert';
import '../models/channel.dart';

class FirebaseScanService {
  static final FirebaseScanService _instance = FirebaseScanService._internal();
  factory FirebaseScanService() => _instance;
  FirebaseScanService._internal();

  final DatabaseReference _database = FirebaseDatabase.instance.ref();
  static const int SCAN_EXPIRY_HOURS = 4;

  /// Initialize Firebase
  Future<void> initialize() async {
    await Firebase.initializeApp();
    // Enable offline persistence
    FirebaseDatabase.instance.setPersistenceEnabled(true);
  }

  /// Upload scan results to Firebase
  Future<String> uploadScanResults({
    required List<Channel> channels,
    required String appVersion,
  }) async {
    try {
      final scanId = DateTime.now().millisecondsSinceEpoch.toString();
      final timestamp = DateTime.now().toUtc().toIso8601String();

      final scanData = {
        'timestamp': timestamp,
        'app_version': appVersion,
        'expires_at': DateTime.now()
            .add(Duration(hours: SCAN_EXPIRY_HOURS))
            .millisecondsSinceEpoch,
        'channel_count': channels.length,
        'channels': channels.map((channel) => {
          'url': channel.url,
          'name': channel.name,
          'is_working': channel.isWorking ?? false,
          'last_checked': channel.lastChecked?.toIso8601String(),
          'resolution': channel.resolution,
          'bitrate': channel.bitrate,
        }).toList(),
      };

      await _database.child('scans/$scanId').set(scanData);
      
      // Update latest scan reference
      await _database.child('latest_scan').set({
        'scan_id': scanId,
        'timestamp': timestamp,
      });

      print('✅ Uploaded scan $scanId with ${channels.length} channels');
      return scanId;
    } catch (e) {
      print('❌ Failed to upload scan: $e');
      rethrow;
    }
  }

  /// Download recent scan results (within SCAN_EXPIRY_HOURS)
  Future<Map<String, dynamic>?> downloadRecentScan() async {
    try {
      final latestSnapshot = await _database.child('latest_scan').get();
      
      if (!latestSnapshot.exists) {
        print('ℹ️ No shared scans available');
        return null;
      }

      final latestData = latestSnapshot.value as Map<dynamic, dynamic>;
      final scanId = latestData['scan_id'];
      final timestamp = DateTime.parse(latestData['timestamp']);

      // Check if scan is still valid
      final age = DateTime.now().difference(timestamp);
      if (age.inHours >= SCAN_EXPIRY_HOURS) {
        print('⏰ Latest scan expired (${age.inHours}h old)');
        return null;
      }

      // Fetch full scan data
      final scanSnapshot = await _database.child('scans/$scanId').get();
      
      if (!scanSnapshot.exists) {
        print('⚠️ Scan data not found for $scanId');
        return null;
      }

      final scanData = Map<String, dynamic>.from(
        scanSnapshot.value as Map<dynamic, dynamic>
      );
      
      print('✅ Downloaded scan $scanId (${age.inMinutes}m old)');
      return scanData;
    } catch (e) {
      print('❌ Failed to download scan: $e');
      return null;
    }
  }

  /// Listen to real-time updates for latest scan
  Stream<Map<String, dynamic>?> watchLatestScan() {
    return _database.child('latest_scan').onValue.asyncMap((event) async {
      if (!event.snapshot.exists) return null;

      final latestData = event.snapshot.value as Map<dynamic, dynamic>;
      final scanId = latestData['scan_id'];

      // Fetch full scan
      final scanSnapshot = await _database.child('scans/$scanId').get();
      if (!scanSnapshot.exists) return null;

      return Map<String, dynamic>.from(
        scanSnapshot.value as Map<dynamic, dynamic>
      );
    });
  }

  /// Parse channels from scan data
  List<Channel> parseChannels(Map<String, dynamic> scanData) {
    final channelsList = scanData['channels'] as List<dynamic>;
    
    return channelsList.map((channelData) {
      final data = Map<String, dynamic>.from(channelData);
      return Channel(
        name: data['name'] ?? '',
        url: data['url'] ?? '',
        category: 'Shared',
        isWorking: data['is_working'] as bool?,
        lastChecked: data['last_checked'] != null
            ? DateTime.parse(data['last_checked'])
            : null,
        resolution: data['resolution'],
        bitrate: data['bitrate'],
      );
    }).toList();
  }

  /// Clean up expired scans (called by Cloud Function in production)
  Future<void> cleanupExpiredScans() async {
    try {
      final now = DateTime.now().millisecondsSinceEpoch;
      final scansSnapshot = await _database.child('scans').get();

      if (!scansSnapshot.exists) return;

      final scans = Map<String, dynamic>.from(
        scansSnapshot.value as Map<dynamic, dynamic>
      );

      int deletedCount = 0;
      for (final entry in scans.entries) {
        final scanData = entry.value as Map<dynamic, dynamic>;
        final expiresAt = scanData['expires_at'] as int?;

        if (expiresAt != null && expiresAt < now) {
          await _database.child('scans/${entry.key}').remove();
          deletedCount++;
        }
      }

      print('🧹 Cleaned up $deletedCount expired scans');
    } catch (e) {
      print('❌ Failed to cleanup scans: $e');
    }
  }
}
```

### 4.4 Integration with Existing Code

**lib/screens/home_screen.dart (example usage):**
```dart
import '../services/firebase_scan_service.dart';

class HomeScreen extends StatefulWidget {
  // ... existing code ...
}

class _HomeScreenState extends State<HomeScreen> {
  final _firebaseScanService = FirebaseScanService();
  StreamSubscription? _scanSubscription;

  @override
  void initState() {
    super.initState();
    _initializeFirebase();
    _listenToScans();
  }

  Future<void> _initializeFirebase() async {
    try {
      await _firebaseScanService.initialize();
      await _loadRecentScan();
    } catch (e) {
      print('Failed to initialize Firebase: $e');
    }
  }

  Future<void> _loadRecentScan() async {
    final scanData = await _firebaseScanService.downloadRecentScan();
    if (scanData != null) {
      final channels = _firebaseScanService.parseChannels(scanData);
      setState(() {
        // Update UI with shared channels
        _sharedChannels = channels;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Loaded ${channels.length} shared channels'),
          backgroundColor: Colors.green,
        ),
      );
    }
  }

  void _listenToScans() {
    _scanSubscription = _firebaseScanService.watchLatestScan().listen((scanData) {
      if (scanData != null && mounted) {
        final channels = _firebaseScanService.parseChannels(scanData);
        setState(() {
          _sharedChannels = channels;
        });
        
        // Show notification
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('🔄 New scan available: ${channels.length} channels'),
            duration: Duration(seconds: 3),
          ),
        );
      }
    });
  }

  Future<void> _uploadOurScan() async {
    try {
      final scanId = await _firebaseScanService.uploadScanResults(
        channels: _validatedChannels,
        appVersion: '1.4.0',
      );
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('✅ Scan uploaded: $scanId'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ Upload failed: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  void dispose() {
    _scanSubscription?.cancel();
    super.dispose();
  }

  // ... rest of existing code ...
}
```

---

## 5. Implementation Approach - Windows Python App

### 5.1 Dependencies

**requirements.txt:**
```txt
firebase-admin==6.4.0      # Firebase Admin SDK
python-dotenv==1.0.0       # Environment variables
aiohttp==3.9.0             # Async HTTP (existing)
```

### 5.2 Firebase Configuration

**1. Service Account Setup:**
- Go to Firebase Console → Project Settings → Service Accounts
- Click "Generate New Private Key" → Save as `firebase-credentials.json`
- **IMPORTANT**: Add to `.gitignore` (never commit!)

**2. Environment Configuration:**

**.env:**
```env
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_DATABASE_URL=https://tv-viewer-xyz.firebaseio.com
```

### 5.3 Database Service Implementation

**utils/firebase_scan_service.py:**
```python
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
from pathlib import Path

class FirebaseScanService:
    """Firebase Realtime Database service for shared channel scans."""
    
    SCAN_EXPIRY_HOURS = 4
    
    def __init__(self):
        self._initialized = False
        self._database = None
    
    def initialize(self):
        """Initialize Firebase Admin SDK."""
        if self._initialized:
            return
        
        try:
            # Load credentials from environment
            creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
            database_url = os.getenv('FIREBASE_DATABASE_URL')
            
            if not os.path.exists(creds_path):
                raise FileNotFoundError(f"Firebase credentials not found: {creds_path}")
            
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
            
            self._database = db.reference()
            self._initialized = True
            print("✅ Firebase initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize Firebase: {e}")
            raise
    
    def upload_scan_results(
        self, 
        channels: List[Dict[str, any]], 
        app_version: str
    ) -> str:
        """
        Upload channel scan results to Firebase.
        
        Args:
            channels: List of channel dictionaries with 'url', 'name', 'is_working', etc.
            app_version: Application version string
        
        Returns:
            str: Scan ID
        """
        if not self._initialized:
            self.initialize()
        
        try:
            scan_id = str(int(datetime.now().timestamp() * 1000))
            timestamp = datetime.utcnow().isoformat() + 'Z'
            expires_at = int((datetime.now() + timedelta(hours=self.SCAN_EXPIRY_HOURS)).timestamp() * 1000)
            
            scan_data = {
                'timestamp': timestamp,
                'app_version': app_version,
                'expires_at': expires_at,
                'channel_count': len(channels),
                'channels': [
                    {
                        'url': ch.get('url', ''),
                        'name': ch.get('name', ''),
                        'is_working': ch.get('is_working', False),
                        'last_checked': ch.get('last_checked', timestamp),
                        'resolution': ch.get('resolution'),
                        'bitrate': ch.get('bitrate'),
                    }
                    for ch in channels
                ]
            }
            
            # Upload scan
            self._database.child('scans').child(scan_id).set(scan_data)
            
            # Update latest scan reference
            self._database.child('latest_scan').set({
                'scan_id': scan_id,
                'timestamp': timestamp,
            })
            
            print(f"✅ Uploaded scan {scan_id} with {len(channels)} channels")
            return scan_id
            
        except Exception as e:
            print(f"❌ Failed to upload scan: {e}")
            raise
    
    def download_recent_scan(self) -> Optional[Dict[str, any]]:
        """
        Download the most recent scan if it's within SCAN_EXPIRY_HOURS.
        
        Returns:
            Optional[Dict]: Scan data or None if no recent scan available
        """
        if not self._initialized:
            self.initialize()
        
        try:
            # Get latest scan reference
            latest_ref = self._database.child('latest_scan').get()
            
            if not latest_ref:
                print("ℹ️ No shared scans available")
                return None
            
            scan_id = latest_ref.get('scan_id')
            timestamp_str = latest_ref.get('timestamp')
            
            # Parse timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age = datetime.now(timestamp.tzinfo) - timestamp
            
            # Check if expired
            if age.total_seconds() >= self.SCAN_EXPIRY_HOURS * 3600:
                print(f"⏰ Latest scan expired ({age.total_seconds() / 3600:.1f}h old)")
                return None
            
            # Fetch full scan data
            scan_data = self._database.child('scans').child(scan_id).get()
            
            if not scan_data:
                print(f"⚠️ Scan data not found for {scan_id}")
                return None
            
            print(f"✅ Downloaded scan {scan_id} ({age.total_seconds() / 60:.0f}m old)")
            return scan_data
            
        except Exception as e:
            print(f"❌ Failed to download scan: {e}")
            return None
    
    def parse_channels(self, scan_data: Dict[str, any]) -> List[Dict[str, any]]:
        """
        Parse channels from scan data.
        
        Args:
            scan_data: Raw scan data from Firebase
        
        Returns:
            List[Dict]: List of channel dictionaries
        """
        channels = scan_data.get('channels', [])
        return [
            {
                'url': ch.get('url', ''),
                'name': ch.get('name', ''),
                'is_working': ch.get('is_working', False),
                'last_checked': ch.get('last_checked'),
                'resolution': ch.get('resolution'),
                'bitrate': ch.get('bitrate'),
            }
            for ch in channels
        ]
    
    def cleanup_expired_scans(self) -> int:
        """
        Clean up expired scans from the database.
        
        Returns:
            int: Number of scans deleted
        """
        if not self._initialized:
            self.initialize()
        
        try:
            now_ms = int(datetime.now().timestamp() * 1000)
            scans_ref = self._database.child('scans')
            scans = scans_ref.get() or {}
            
            deleted_count = 0
            for scan_id, scan_data in scans.items():
                expires_at = scan_data.get('expires_at', 0)
                
                if expires_at < now_ms:
                    scans_ref.child(scan_id).delete()
                    deleted_count += 1
            
            print(f"🧹 Cleaned up {deleted_count} expired scans")
            return deleted_count
            
        except Exception as e:
            print(f"❌ Failed to cleanup scans: {e}")
            return 0
    
    def listen_to_scans(self, callback):
        """
        Listen to real-time updates for latest scan.
        
        Args:
            callback: Function to call when new scan is available
                      Signature: callback(scan_data: Dict[str, any])
        """
        if not self._initialized:
            self.initialize()
        
        def on_change(event):
            if event.data:
                scan_id = event.data.get('scan_id')
                scan_data = self._database.child('scans').child(scan_id).get()
                if scan_data:
                    callback(scan_data)
        
        # Subscribe to changes
        self._database.child('latest_scan').listen(on_change)
        print("👂 Listening for scan updates...")


# Singleton instance
_firebase_service = None

def get_firebase_service() -> FirebaseScanService:
    """Get singleton FirebaseScanService instance."""
    global _firebase_service
    if _firebase_service is None:
        _firebase_service = FirebaseScanService()
    return _firebase_service
```

### 5.4 Integration with Existing Code

**Replace PrivateBin integration in main app:**

**tv_viewer_app.py (example integration):**
```python
from utils.firebase_scan_service import get_firebase_service
import threading

class TVViewerApp:
    def __init__(self):
        # ... existing initialization ...
        self.firebase_service = get_firebase_service()
        self.firebase_service.initialize()
        
        # Load shared scan on startup
        self.load_shared_scan()
    
    def load_shared_scan(self):
        """Load recent shared scan results on app startup."""
        try:
            scan_data = self.firebase_service.download_recent_scan()
            
            if scan_data:
                channels = self.firebase_service.parse_channels(scan_data)
                working_channels = [ch for ch in channels if ch['is_working']]
                
                print(f"✅ Loaded {len(channels)} shared channels "
                      f"({len(working_channels)} working)")
                
                # Update UI
                self.display_shared_channels(channels)
                
                # Show notification
                self.show_notification(
                    f"Loaded {len(working_channels)} working channels from shared scan"
                )
            else:
                print("ℹ️ No recent shared scans available, will perform full scan")
                
        except Exception as e:
            print(f"⚠️ Failed to load shared scan: {e}")
    
    def upload_scan_results(self, channels: list):
        """Upload completed scan results to Firebase."""
        try:
            # Prepare channel data
            channel_data = [
                {
                    'url': ch.url,
                    'name': ch.name,
                    'is_working': ch.is_working,
                    'last_checked': datetime.now().isoformat() + 'Z',
                    'resolution': getattr(ch, 'resolution', None),
                    'bitrate': getattr(ch, 'bitrate', None),
                }
                for ch in channels
            ]
            
            # Upload in background thread
            def upload_thread():
                try:
                    scan_id = self.firebase_service.upload_scan_results(
                        channels=channel_data,
                        app_version=self.app_version
                    )
                    self.show_notification(f"✅ Scan uploaded: {scan_id}")
                except Exception as e:
                    print(f"❌ Upload failed: {e}")
            
            thread = threading.Thread(target=upload_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"⚠️ Failed to upload scan: {e}")
    
    def enable_realtime_updates(self):
        """Enable real-time listening for new scans."""
        def on_new_scan(scan_data):
            channels = self.firebase_service.parse_channels(scan_data)
            print(f"🔄 New scan received: {len(channels)} channels")
            
            # Update UI on main thread
            self.after(0, lambda: self.display_shared_channels(channels))
            self.after(0, lambda: self.show_notification(
                f"🔄 New scan: {len(channels)} channels available"
            ))
        
        # Start listener in background thread
        thread = threading.Thread(
            target=lambda: self.firebase_service.listen_to_scans(on_new_scan),
            daemon=True
        )
        thread.start()
```

---

## 6. Data Schema Design

### 6.1 Firebase Database Structure

```
tv-viewer-database/
│
├── scans/
│   ├── 1738012345678/                    # Scan ID (Unix timestamp)
│   │   ├── timestamp: "2026-01-27T10:30:00Z"
│   │   ├── app_version: "1.4.0"
│   │   ├── expires_at: 1738026745678     # Unix timestamp (4 hours later)
│   │   ├── channel_count: 1234
│   │   └── channels: [
│   │         {
│   │           url: "https://stream.example.com/live.m3u8",
│   │           name: "Example TV",
│   │           is_working: true,
│   │           last_checked: "2026-01-27T10:25:00Z",
│   │           resolution: "1920x1080",
│   │           bitrate: 5000
│   │         },
│   │         ...
│   │       ]
│   │
│   ├── 1738015678901/                    # Another scan
│   │   └── ...
│   │
│   └── ...
│
├── latest_scan/                          # Reference to most recent scan
│   ├── scan_id: "1738015678901"
│   └── timestamp: "2026-01-27T11:30:00Z"
│
└── metadata/                             # App-wide metadata
    ├── total_scans: 42
    ├── last_cleanup: "2026-01-27T08:00:00Z"
    └── schema_version: "1.0"
```

### 6.2 Security Rules

**Firebase Console → Realtime Database → Rules:**

```json
{
  "rules": {
    "scans": {
      ".read": true,
      ".write": true,
      "$scan_id": {
        ".validate": "newData.hasChildren(['timestamp', 'app_version', 'channels'])",
        "timestamp": {
          ".validate": "newData.isString() && newData.val().length > 0"
        },
        "app_version": {
          ".validate": "newData.isString() && newData.val().matches(/^\\d+\\.\\d+\\.\\d+$/)"
        },
        "expires_at": {
          ".validate": "newData.isNumber() && newData.val() > now"
        },
        "channel_count": {
          ".validate": "newData.isNumber() && newData.val() >= 0"
        },
        "channels": {
          ".validate": "newData.isArray()",
          "$channel": {
            "url": {
              ".validate": "newData.isString() && newData.val().length > 0"
            },
            "name": {
              ".validate": "newData.isString()"
            },
            "is_working": {
              ".validate": "newData.isBoolean()"
            }
          }
        }
      }
    },
    "latest_scan": {
      ".read": true,
      ".write": true,
      ".validate": "newData.hasChildren(['scan_id', 'timestamp'])"
    },
    "metadata": {
      ".read": true,
      ".write": false
    }
  }
}
```

### 6.3 Data Indexing

**Firebase Console → Realtime Database → Add Index:**

```json
{
  "rules": {
    "scans": {
      ".indexOn": ["timestamp", "expires_at"]
    }
  }
}
```

This enables efficient querying by timestamp and expiration.

### 6.4 Data Size Estimation

**Per Channel:**
- URL: ~100 bytes
- Name: ~50 bytes
- Metadata: ~50 bytes
- **Total: ~200 bytes per channel**

**Per Scan:**
- 10,000 channels × 200 bytes = **~2 MB**
- Metadata: ~500 bytes

**Free Tier Capacity:**
- Storage: 1GB = **~500 scans** (plenty for 4-hour rotation)
- Bandwidth: 10GB/month = **5,000 downloads/month**

**Expected Usage:**
- Active users: ~100/day
- Scans generated: ~5/day (rotated every 4 hours)
- Downloads: ~100/day × 2MB = **200MB/day** = **6GB/month** ✅ Within free tier

---

## 7. Migration Plan from PrivateBin

### Phase 1: Parallel Implementation (Week 1)
1. ✅ Add Firebase dependencies to Flutter and Python apps
2. ✅ Implement FirebaseScanService alongside existing PrivateBin code
3. ✅ Add feature flag: `USE_FIREBASE` (default: false)
4. ✅ Test Firebase upload/download in development

### Phase 2: Gradual Rollout (Week 2)
1. ✅ Enable Firebase for 10% of users (A/B test)
2. ✅ Monitor latency, errors, and user feedback
3. ✅ Compare scan availability: PrivateBin vs Firebase
4. ✅ Increase to 50% of users if successful

### Phase 3: Full Cutover (Week 3)
1. ✅ Enable Firebase for 100% of users
2. ✅ Remove PrivateBin code (`utils/privatebin.py`)
3. ✅ Update documentation and README
4. ✅ Deploy to production

### Rollback Plan
- Keep PrivateBin code until Phase 3 complete
- Feature flag allows instant revert if Firebase fails
- Monitor error rates and have on-call engineer ready

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Flutter (test/services/firebase_scan_service_test.dart):**
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';

void main() {
  group('FirebaseScanService', () {
    test('parseChannels extracts channel data correctly', () {
      final scanData = {
        'channels': [
          {'url': 'http://test.com', 'name': 'Test', 'is_working': true}
        ]
      };
      
      final channels = FirebaseScanService().parseChannels(scanData);
      
      expect(channels.length, 1);
      expect(channels[0].url, 'http://test.com');
      expect(channels[0].isWorking, true);
    });
    
    test('uploadScanResults includes expiry timestamp', () async {
      // Test implementation
    });
  });
}
```

**Python (tests/test_firebase_scan_service.py):**
```python
import unittest
from unittest.mock import Mock, patch
from utils.firebase_scan_service import FirebaseScanService

class TestFirebaseScanService(unittest.TestCase):
    
    def setUp(self):
        self.service = FirebaseScanService()
    
    def test_parse_channels(self):
        scan_data = {
            'channels': [
                {'url': 'http://test.com', 'name': 'Test', 'is_working': True}
            ]
        }
        
        channels = self.service.parse_channels(scan_data)
        
        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0]['url'], 'http://test.com')
        self.assertTrue(channels[0]['is_working'])
    
    @patch('firebase_admin.db.reference')
    def test_upload_scan_results(self, mock_db):
        # Test implementation
        pass
```

### 8.2 Integration Tests

**Test Scenarios:**
1. ✅ Upload scan → Download same scan → Verify data integrity
2. ✅ Upload scan → Wait 4+ hours → Verify scan expired
3. ✅ Upload from Python → Download from Flutter → Cross-platform verification
4. ✅ Real-time listener → Upload new scan → Verify callback triggered
5. ✅ Network offline → Upload fails gracefully → Retry on reconnect

### 8.3 Load Testing

**Firebase Simulator:**
- Simulate 100 concurrent users downloading scans
- Measure latency: Expect <500ms for 2MB download
- Verify rate limiting prevents abuse
- Test bandwidth limits (10GB/month = ~5,000 downloads)

---

## 9. Cost Analysis

### 9.1 Free Tier Breakdown

| Resource | Free Tier | Expected Usage | Headroom |
|----------|-----------|----------------|----------|
| **Storage** | 1GB | ~20MB (10 scans) | 50x |
| **Bandwidth** | 10GB/month | ~6GB/month | 1.6x |
| **Concurrent Connections** | 100 (Spark) | ~20 typical | 5x |
| **Cloud Functions** | 2M invocations/month | ~720/month (cleanup) | 2777x |

### 9.2 Paid Tier (Blaze - Pay-as-you-go)

**If project scales beyond free tier:**

| Resource | Cost | At 10K Users/Month |
|----------|------|---------------------|
| Storage | $5/GB/month | $5 (1GB total) |
| Bandwidth | $1/GB | $50 (50GB downloads) |
| Concurrent Connections | $1/100K | $2 (200K connections) |
| **TOTAL** | | **~$57/month** |

**Cost Optimization:**
- Use gzip compression (reduce bandwidth by ~70%)
- Implement client-side caching (reduce redundant downloads)
- Clean up expired scans aggressively (reduce storage)

---

## 10. Privacy & Compliance

### 10.1 Data Privacy
✅ **No Personally Identifiable Information (PII)**
- No user accounts, emails, names, or IP addresses stored
- Only channel URLs (public data), validation status, and timestamps
- Anonymous access model aligns with GDPR "privacy by design"

### 10.2 GDPR Compliance
- **Data Minimization**: Only essential data stored (URLs, status)
- **Purpose Limitation**: Data only used for channel validation sharing
- **Storage Limitation**: Automatic 4-hour expiry
- **Right to Access**: Data is publicly readable
- **Right to Erasure**: Not applicable (no user accounts)

### 10.3 Terms of Service
Firebase's ToS allows this use case:
- ✅ Open-source project (non-commercial)
- ✅ No abuse/spam (rate-limited uploads)
- ✅ Public data only (IPTV URLs are publicly available)

---

## 11. Monitoring & Observability

### 11.1 Firebase Analytics

**Key Metrics to Track:**
- Upload success rate (target: >99%)
- Download latency (target: <500ms p95)
- Scan age when downloaded (target: <2 hours median)
- Number of active scans (target: 5-10)
- Storage usage (alert at 800MB)

### 11.2 Application Logging

**Flutter App:**
```dart
// Log Firebase operations
FirebaseCrashlytics.instance.log('Uploaded scan: $scanId');
FirebaseCrashlytics.instance.recordError(error, stackTrace);
```

**Python App:**
```python
import logging

logging.info(f"✅ Uploaded scan {scan_id}")
logging.error(f"❌ Firebase error: {error}", exc_info=True)
```

### 11.3 Alerts

**Set up Firebase Console alerts:**
- Storage usage > 80% (800MB)
- Bandwidth usage > 80% (8GB/month)
- Error rate > 1% (P1 incident)
- Latency p95 > 1s (performance degradation)

---

## 12. Alternative: Hybrid Approach (Future Consideration)

If Firebase becomes expensive or has limitations, consider:

### Option A: Firebase (real-time) + Cloudflare R2 (storage)
- Firebase for real-time notifications (~1KB metadata)
- Cloudflare R2 for bulk scan data (~2MB per scan)
- Cost: R2 is cheaper for storage ($0.015/GB vs $5/GB)

### Option B: Supabase (managed) + PocketBase (self-hosted fallback)
- Supabase as primary (ease of use)
- PocketBase as backup if free tier exhausted
- Requires migration logic between databases

---

## 13. Conclusion

**Firebase Realtime Database is the optimal choice for Issue #31** because:

1. ✅ **Zero Friction**: Official SDKs, comprehensive docs, instant setup
2. ✅ **True Real-time**: WebSocket sync beats PrivateBin's static paste model
3. ✅ **Anonymous**: No user accounts needed, Security Rules handle access control
4. ✅ **Free Tier**: 1GB + 10GB/month covers thousands of users
5. ✅ **Proven**: Battle-tested by millions of apps over 10+ years
6. ✅ **Cross-platform**: Identical experience on Flutter and Python

**Next Steps:**
1. Create Firebase project and configure Security Rules
2. Implement `FirebaseScanService` in Flutter and Python
3. Add feature flag for gradual rollout
4. Monitor metrics for 2 weeks before full cutover
5. Remove PrivateBin code once stable

**Total Implementation Time**: ~2 weeks (1 week development + 1 week testing/rollout)

---

**Document Version**: 1.0  
**Last Updated**: January 27, 2026  
**Author**: TV Viewer Development Team