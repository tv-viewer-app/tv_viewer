# TV Viewer Android App - Comprehensive Review & Recommendations

## Executive Summary

The TV Viewer app is a Flutter-based IPTV streaming application with decent Android configuration. However, there are **critical issues** and **significant optimization opportunities** for production deployment and enhanced user experience on Android devices.

---

## 1. AndroidManifest.xml Configuration

### ✅ Current Implementation
- ✓ Basic permissions (INTERNET, ACCESS_NETWORK_STATE)
- ✓ Hardware acceleration enabled
- ✓ Queries element for external players (VLC, MX Player)
- ✓ Network security config referenced
- ✓ Cleartext traffic enabled

### ❌ Critical Issues

#### 1.1 Missing Wake Lock Permission
**Issue**: Video playback will be interrupted when screen times out.

**Impact**: Poor user experience - screen will turn off during video playback.

**Fix**: Add to AndroidManifest.xml:
```xml
<uses-permission android:name="android.permission.WAKE_LOCK"/>
```

#### 1.2 Missing Activity Configuration for Picture-in-Picture
**Issue**: No PiP support configuration.

**Recommendation**: Add PiP support for better multitasking:
```xml
<activity
    android:name=".MainActivity"
    android:supportsPictureInPicture="true"
    android:resizeableActivity="true"
    android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
    ...>
```

#### 1.3 Incomplete External Player Queries
**Issue**: Missing popular Android video players.

**Recommendation**: Add more player packages:
```xml
<queries>
    <!-- Existing queries... -->
    
    <!-- Additional video players -->
    <package android:name="com.google.android.youtube" />
    <package android:name="is.xyz.mpv" /> <!-- MPV Player -->
    <package android:name="com.fgl27.twitch" /> <!-- Just Player -->
    <package android:name="org.schabi.newpipe" /> <!-- NewPipe -->
    <package android:name="org.videolan.vlc.betav7neon" /> <!-- VLC Beta -->
    
    <!-- Generic video intent -->
    <intent>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="http" />
    </intent>
    <intent>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="https" />
    </intent>
</queries>
```

#### 1.4 Missing Foreground Service Declaration (for background playback)
**Recommendation**: For future audio-only background playback:
```xml
<uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK"/>
```

---

## 2. Network Security Configuration

### ✅ Current Implementation
- ✓ Network security config file exists
- ✓ Cleartext traffic permitted (necessary for IPTV streams)

### ⚠️ Security Concerns

#### 2.1 Overly Permissive Configuration
**Issue**: All cleartext traffic is allowed, no domain restrictions.

**Security Risk**: App can communicate with any HTTP endpoint, increasing attack surface.

**Recommendation**: Implement domain-specific cleartext traffic:

**File**: `android/app/src/main/res/xml/network_security_config.xml`
```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <!-- Base config - HTTPS only by default -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system"/>
            <certificates src="user"/> <!-- For debugging with Charles/Fiddler -->
        </trust-anchors>
    </base-config>
    
    <!-- Allow cleartext for known IPTV sources -->
    <domain-config cleartextTrafficPermitted="true">
        <!-- GitHub IPTV repositories -->
        <domain includeSubdomains="true">iptv-org.github.io</domain>
        
        <!-- Common IPTV streaming domains - add as needed -->
        <!-- Uncomment domains you specifically use -->
        <!-- <domain includeSubdomains="true">example-iptv.com</domain> -->
    </domain-config>
    
    <!-- Debug config - only for development builds -->
    <debug-overrides>
        <trust-anchors>
            <certificates src="user"/>
            <certificates src="system"/>
        </trust-anchors>
    </debug-overrides>
</network-security-config>
```

**IMPORTANT**: For production, you may need `cleartextTrafficPermitted="true"` in base-config if IPTV streams use HTTP. However, document which domains require it.

#### 2.2 Certificate Pinning for API Endpoints
**Recommendation**: Add certificate pinning for GitHub IPTV-org API:
```xml
<domain-config>
    <domain includeSubdomains="true">iptv-org.github.io</domain>
    <pin-set expiration="2025-12-31">
        <!-- GitHub's certificate pins - update regularly -->
        <pin digest="SHA-256">base64_encoded_hash_here==</pin>
        <pin digest="SHA-256">backup_hash_here==</pin>
    </pin-set>
</domain-config>
```

To get certificate hashes:
```bash
openssl s_client -connect iptv-org.github.io:443 | openssl x509 -pubkey -noout | openssl pkey -pubin -outform der | openssl dgst -sha256 -binary | base64
```

---

## 3. Video Playback on Android

### ✅ Current Implementation
- ✓ Using official `video_player` plugin
- ✓ Hardware acceleration enabled in manifest
- ✓ Proper user-agent headers
- ✓ Aspect ratio handling

### ❌ Critical Issues

#### 3.1 No ExoPlayer Configuration
**Issue**: Flutter's `video_player` uses ExoPlayer on Android, but no optimization.

**Problem**: Default ExoPlayer settings may not handle IPTV streams optimally (buffering, codec support).

**Recommendation**: Create custom Android platform implementation with ExoPlayer configuration.

**File**: Create `android/app/src/main/kotlin/com/tvviewer/app/ExoPlayerManager.kt`
```kotlin
package com.tvviewer.app

import android.content.Context
import com.google.android.exoplayer2.DefaultLoadControl
import com.google.android.exoplayer2.ExoPlayer
import com.google.android.exoplayer2.LoadControl
import com.google.android.exoplayer2.upstream.DefaultAllocator

class ExoPlayerManager {
    companion object {
        fun createOptimizedPlayer(context: Context): ExoPlayer {
            // Optimize buffering for IPTV streams
            val loadControl: LoadControl = DefaultLoadControl.Builder()
                .setAllocator(DefaultAllocator(true, 16))
                .setBufferDurationsMs(
                    15000,  // Min buffer before playback: 15 seconds
                    50000,  // Max buffer: 50 seconds
                    2500,   // Buffer for playback: 2.5 seconds
                    5000    // Buffer for playback after rebuffer: 5 seconds
                )
                .setTargetBufferBytes(-1)
                .setPrioritizeTimeOverSizeThresholds(true)
                .build()
                
            return ExoPlayer.Builder(context)
                .setLoadControl(loadControl)
                .build()
        }
    }
}
```

**Note**: This requires adding ExoPlayer dependency (already included via video_player, but you may need specific version).

#### 3.2 Missing Codec Support Detection
**Issue**: No check for device codec capabilities before playback.

**Recommendation**: Add codec detection:
```kotlin
import android.media.MediaCodecList
import android.media.MediaCodecInfo

fun getSupportedCodecs(): List<String> {
    val codecList = MediaCodecList(MediaCodecList.ALL_CODECS)
    return codecList.codecInfos
        .filter { it.isEncoder.not() }
        .flatMap { it.supportedTypes.toList() }
        .distinct()
}

// Check for specific codec
fun supportsH265(): Boolean {
    return getSupportedCodecs().any { 
        it.contains("hevc", ignoreCase = true) || 
        it.contains("h265", ignoreCase = true) 
    }
}
```

#### 3.3 No Adaptive Bitrate Selection
**Issue**: Always plays the same stream URL regardless of network conditions.

**Recommendation**: 
1. Parse HLS manifests (.m3u8) to extract quality variants
2. Implement network speed detection
3. Switch streams based on bandwidth

**Dart Implementation** (in `lib/services/streaming_service.dart`):
```dart
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:http/http.dart' as http;

class StreamingService {
  // Detect network type
  Future<String> getNetworkType() async {
    final connectivity = await Connectivity().checkConnectivity();
    if (connectivity == ConnectivityResult.wifi) {
      return 'wifi';
    } else if (connectivity == ConnectivityResult.mobile) {
      return 'cellular';
    }
    return 'unknown';
  }
  
  // Parse HLS manifest for quality variants
  Future<List<StreamVariant>> parseHLSManifest(String manifestUrl) async {
    final response = await http.get(Uri.parse(manifestUrl));
    if (response.statusCode != 200) return [];
    
    final variants = <StreamVariant>[];
    final lines = response.body.split('\n');
    
    String? bandwidth;
    String? resolution;
    
    for (var i = 0; i < lines.length; i++) {
      final line = lines[i].trim();
      
      if (line.startsWith('#EXT-X-STREAM-INF:')) {
        // Extract bandwidth
        final bandwidthMatch = RegExp(r'BANDWIDTH=(\d+)').firstMatch(line);
        bandwidth = bandwidthMatch?.group(1);
        
        // Extract resolution
        final resolutionMatch = RegExp(r'RESOLUTION=(\d+x\d+)').firstMatch(line);
        resolution = resolutionMatch?.group(1);
        
        // Next line should be the URL
        if (i + 1 < lines.length) {
          final variantUrl = lines[i + 1].trim();
          if (variantUrl.isNotEmpty && !variantUrl.startsWith('#')) {
            variants.add(StreamVariant(
              url: variantUrl,
              bandwidth: int.tryParse(bandwidth ?? '0') ?? 0,
              resolution: resolution,
            ));
          }
        }
      }
    }
    
    return variants..sort((a, b) => a.bandwidth.compareTo(b.bandwidth));
  }
  
  // Select best stream based on network
  StreamVariant selectBestStream(List<StreamVariant> variants, String networkType) {
    if (variants.isEmpty) throw Exception('No variants available');
    
    // On WiFi, prefer highest quality
    if (networkType == 'wifi') {
      return variants.last; // Highest bandwidth
    }
    
    // On cellular, prefer medium quality (around 2-3 Mbps)
    final targetBandwidth = 2500000; // 2.5 Mbps
    return variants.reduce((a, b) {
      final diffA = (a.bandwidth - targetBandwidth).abs();
      final diffB = (b.bandwidth - targetBandwidth).abs();
      return diffA < diffB ? a : b;
    });
  }
}

class StreamVariant {
  final String url;
  final int bandwidth;
  final String? resolution;
  
  StreamVariant({required this.url, required this.bandwidth, this.resolution});
}
```

**Dependencies to add** (pubspec.yaml):
```yaml
dependencies:
  connectivity_plus: ^5.0.2
```

#### 3.4 Missing Wake Lock Implementation
**Issue**: Screen will turn off during video playback.

**Recommendation**: Add `wakelock_plus` package:

**pubspec.yaml**:
```yaml
dependencies:
  wakelock_plus: ^1.1.4
```

**Update player_screen.dart**:
```dart
import 'package:wakelock_plus/wakelock_plus.dart';

@override
void initState() {
  super.initState();
  WakelockPlus.enable(); // Keep screen on
  _initializePlayer();
  // ... rest of init
}

@override
void dispose() {
  WakelockPlus.disable(); // Allow screen to sleep
  // ... rest of dispose
}
```

#### 3.5 No Audio Focus Handling
**Issue**: Audio continues playing when phone call arrives or other apps need audio.

**Recommendation**: Add audio focus handling via platform channel:

**File**: `android/app/src/main/kotlin/com/tvviewer/app/AudioFocusHandler.kt`
```kotlin
package com.tvviewer.app

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.os.Build

class AudioFocusHandler(private val context: Context) {
    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private var focusRequest: AudioFocusRequest? = null
    
    fun requestAudioFocus(onFocusLoss: () -> Unit): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val audioAttributes = AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_MOVIE)
                .build()
                
            focusRequest = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
                .setAudioAttributes(audioAttributes)
                .setOnAudioFocusChangeListener { focusChange ->
                    when (focusChange) {
                        AudioManager.AUDIOFOCUS_LOSS,
                        AudioManager.AUDIOFOCUS_LOSS_TRANSIENT -> onFocusLoss()
                    }
                }
                .build()
                
            audioManager.requestAudioFocus(focusRequest!!) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
        } else {
            @Suppress("DEPRECATION")
            audioManager.requestAudioFocus(
                { onFocusLoss() },
                AudioManager.STREAM_MUSIC,
                AudioManager.AUDIOFOCUS_GAIN
            ) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
        }
    }
    
    fun abandonAudioFocus() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            focusRequest?.let { audioManager.abandonAudioFocusRequest(it) }
        } else {
            @Suppress("DEPRECATION")
            audioManager.abandonAudioFocus(null)
        }
    }
}
```

---

## 4. Intent Handling for External Video Players

### ✅ Current Implementation
- ✓ Basic URL launcher for external players
- ✓ VLC and MX Player intent URIs

### ⚠️ Issues & Improvements

#### 4.1 Incorrect VLC Intent Format
**Issue**: `vlc://$streamUrl` is incorrect VLC intent format.

**Fix**: Use proper VLC intent:
```dart
void _openInVLC(String streamUrl) async {
  // Proper VLC intent
  final vlcIntent = Uri.parse(
    'vlc://$streamUrl'
  );
  
  // Better approach - explicit intent
  final androidIntent = AndroidIntent(
    action: 'android.intent.action.VIEW',
    data: streamUrl,
    package: 'org.videolan.vlc',
    arguments: {
      'title': widget.channel.name,
      'from_start': false,
      'position': 0,
    },
  );
  
  await androidIntent.launch();
}
```

**Required Dependency**:
```yaml
dependencies:
  android_intent_plus: ^4.0.3
```

#### 4.2 MX Player Intent Incorrect
**Current**: Using custom URI scheme (doesn't work reliably)

**Fix**: Use proper MX Player intent:
```dart
void _openInMXPlayer(String streamUrl) async {
  final intent = AndroidIntent(
    action: 'android.intent.action.VIEW',
    data: Uri.parse(streamUrl).toString(),
    package: 'com.mxtech.videoplayer.ad', // or .pro
    type: 'video/*',
    arguments: {
      'title': widget.channel.name,
      'decode_mode': 2, // HW+ decoder
      'secure_uri': true,
    },
  );
  
  await intent.launch();
}
```

#### 4.3 Enhanced External Player Support
**Recommendation**: Create comprehensive external player manager:

**File**: `lib/services/external_player_service.dart`
```dart
import 'package:android_intent_plus/android_intent.dart';
import 'package:flutter/foundation.dart';

enum VideoPlayer {
  vlc('org.videolan.vlc', 'VLC'),
  vlcBeta('org.videolan.vlc.betav7neon', 'VLC Beta'),
  mxPlayerFree('com.mxtech.videoplayer.ad', 'MX Player Free'),
  mxPlayerPro('com.mxtech.videoplayer.pro', 'MX Player Pro'),
  mpv('is.xyz.mpv', 'MPV Player'),
  justPlayer('com.brouken.player', 'Just Player'),
  systemDefault('', 'System Default');

  final String packageName;
  final String displayName;
  
  const VideoPlayer(this.packageName, this.displayName);
}

class ExternalPlayerService {
  // Check if player is installed
  static Future<bool> isPlayerInstalled(VideoPlayer player) async {
    if (player == VideoPlayer.systemDefault) return true;
    
    try {
      final intent = AndroidIntent(
        action: 'android.intent.action.MAIN',
        package: player.packageName,
      );
      // This will throw if package doesn't exist
      return true; // If no error, package exists
    } catch (e) {
      return false;
    }
  }
  
  // Get list of installed players
  static Future<List<VideoPlayer>> getInstalledPlayers() async {
    final installedPlayers = <VideoPlayer>[];
    
    for (final player in VideoPlayer.values) {
      if (await isPlayerInstalled(player)) {
        installedPlayers.add(player);
      }
    }
    
    return installedPlayers;
  }
  
  // Open stream in specific player
  static Future<bool> openInPlayer({
    required String streamUrl,
    required VideoPlayer player,
    String? title,
    Map<String, dynamic>? headers,
  }) async {
    try {
      if (player == VideoPlayer.systemDefault) {
        return await _openWithSystemDefault(streamUrl);
      }
      
      final intent = AndroidIntent(
        action: 'android.intent.action.VIEW',
        data: streamUrl,
        package: player.packageName,
        type: 'video/*',
        arguments: _getPlayerSpecificArguments(player, title, headers),
      );
      
      await intent.launch();
      return true;
    } catch (e) {
      debugPrint('Failed to open in ${player.displayName}: $e');
      return false;
    }
  }
  
  static Map<String, dynamic> _getPlayerSpecificArguments(
    VideoPlayer player,
    String? title,
    Map<String, dynamic>? headers,
  ) {
    final args = <String, dynamic>{};
    
    if (title != null) {
      args['title'] = title;
    }
    
    switch (player) {
      case VideoPlayer.mxPlayerFree:
      case VideoPlayer.mxPlayerPro:
        args['decode_mode'] = 2; // Hardware acceleration
        args['secure_uri'] = true;
        if (headers != null) {
          args['headers'] = headers.entries
              .map((e) => '${e.key}: ${e.value}')
              .join('\n');
        }
        break;
        
      case VideoPlayer.vlc:
      case VideoPlayer.vlcBeta:
        args['from_start'] = false;
        args['position'] = 0;
        break;
        
      case VideoPlayer.justPlayer:
        args['secure_uri'] = true;
        break;
        
      default:
        break;
    }
    
    return args;
  }
  
  static Future<bool> _openWithSystemDefault(String streamUrl) async {
    try {
      final uri = Uri.parse(streamUrl);
      return await launchUrl(
        uri,
        mode: LaunchMode.externalApplication,
      );
    } catch (e) {
      return false;
    }
  }
  
  // Show player selection dialog
  static Future<VideoPlayer?> showPlayerSelectionDialog(
    BuildContext context,
    List<VideoPlayer> players,
  ) async {
    return await showDialog<VideoPlayer>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Select Player'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: players.map((player) {
              return ListTile(
                leading: _getPlayerIcon(player),
                title: Text(player.displayName),
                onTap: () => Navigator.pop(context, player),
              );
            }).toList(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
        ],
      ),
    );
  }
  
  static Widget _getPlayerIcon(VideoPlayer player) {
    IconData iconData;
    switch (player) {
      case VideoPlayer.vlc:
      case VideoPlayer.vlcBeta:
        iconData = Icons.play_circle;
        break;
      case VideoPlayer.mxPlayerFree:
      case VideoPlayer.mxPlayerPro:
        iconData = Icons.movie;
        break;
      default:
        iconData = Icons.videocam;
    }
    return Icon(iconData);
  }
}
```

**Update player_screen.dart**:
```dart
void _openInExternalPlayer() async {
  final availablePlayers = await ExternalPlayerService.getInstalledPlayers();
  
  if (availablePlayers.isEmpty) {
    _showNoPlayersDialog();
    return;
  }
  
  final selectedPlayer = await ExternalPlayerService.showPlayerSelectionDialog(
    context,
    availablePlayers,
  );
  
  if (selectedPlayer != null) {
    final success = await ExternalPlayerService.openInPlayer(
      streamUrl: widget.channel.url,
      player: selectedPlayer,
      title: widget.channel.name,
      headers: {'User-Agent': 'TV Viewer/1.5.0'},
    );
    
    if (!success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to open in ${selectedPlayer.displayName}')),
      );
    }
  }
}
```

---

## 5. Cast Functionality Implementation

### ❌ Current Implementation
**Issue**: No actual cast support - just shows info dialog.

### 📋 Recommendations

#### 5.1 Google Cast Integration (Complex but Complete)
**Approach**: Integrate official Google Cast SDK

**Pros**:
- Official support
- Wide device compatibility
- ChromeCast, Android TV support

**Cons**:
- Requires Google Play Services
- Complex setup
- Limited free tier

**Implementation**:

1. **Add Google Cast dependency** (`build.gradle`):
```gradle
dependencies {
    implementation "org.jetbrains.kotlin:kotlin-stdlib:1.9.22"
    implementation 'com.google.android.gms:play-services-cast-framework:21.4.0'
}
```

2. **Create Cast Options Provider** (`CastOptionsProvider.kt`):
```kotlin
package com.tvviewer.app

import android.content.Context
import com.google.android.gms.cast.framework.CastOptions
import com.google.android.gms.cast.framework.OptionsProvider
import com.google.android.gms.cast.framework.SessionProvider
import com.google.android.gms.cast.framework.media.CastMediaOptions
import com.google.android.gms.cast.framework.media.NotificationOptions

class CastOptionsProvider : OptionsProvider {
    override fun getCastOptions(context: Context): CastOptions {
        return CastOptions.Builder()
            .setReceiverApplicationId("CC1AD845") // Default Media Receiver
            .setCastMediaOptions(
                CastMediaOptions.Builder()
                    .setNotificationOptions(
                        NotificationOptions.Builder()
                            .setActions(
                                listOf(
                                    MediaIntentReceiver.ACTION_TOGGLE_PLAYBACK,
                                    MediaIntentReceiver.ACTION_STOP_CASTING
                                ),
                                intArrayOf(0, 1)
                            )
                            .build()
                    )
                    .build()
            )
            .build()
    }
    
    override fun getAdditionalSessionProviders(context: Context): List<SessionProvider>? {
        return null
    }
}
```

3. **Declare in AndroidManifest.xml**:
```xml
<application>
    <!-- ... existing config ... -->
    
    <meta-data
        android:name="com.google.android.gms.cast.framework.OPTIONS_PROVIDER_CLASS_NAME"
        android:value="com.tvviewer.app.CastOptionsProvider" />
</application>
```

4. **Create Method Channel for Flutter**:
```kotlin
// In MainActivity.kt
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import com.google.android.gms.cast.MediaInfo
import com.google.android.gms.cast.MediaMetadata
import com.google.android.gms.cast.framework.CastContext
import com.google.android.gms.cast.framework.CastSession
import com.google.android.gms.common.images.WebImage
import android.net.Uri

class MainActivity: FlutterActivity() {
    private val CHANNEL = "com.tvviewer.app/cast"
    private var castSession: CastSession? = null
    
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "castVideo" -> {
                    val url = call.argument<String>("url")
                    val title = call.argument<String>("title")
                    val imageUrl = call.argument<String>("imageUrl")
                    
                    if (url != null) {
                        castVideo(url, title, imageUrl)
                        result.success(true)
                    } else {
                        result.error("INVALID_ARGS", "URL is required", null)
                    }
                }
                "isCastConnected" -> {
                    result.success(isCastConnected())
                }
                "stopCasting" -> {
                    stopCasting()
                    result.success(true)
                }
                else -> result.notImplemented()
            }
        }
    }
    
    private fun castVideo(url: String, title: String?, imageUrl: String?) {
        castSession = CastContext.getSharedInstance(this).sessionManager.currentCastSession
        
        if (castSession == null || !castSession!!.isConnected) {
            return
        }
        
        val metadata = MediaMetadata(MediaMetadata.MEDIA_TYPE_MOVIE).apply {
            putString(MediaMetadata.KEY_TITLE, title ?: "TV Stream")
            if (imageUrl != null) {
                addImage(WebImage(Uri.parse(imageUrl)))
            }
        }
        
        val mediaInfo = MediaInfo.Builder(url)
            .setStreamType(MediaInfo.STREAM_TYPE_LIVE)
            .setContentType("video/mp4") // Adjust based on stream type
            .setMetadata(metadata)
            .build()
        
        val remoteMediaClient = castSession?.remoteMediaClient
        remoteMediaClient?.load(mediaInfo)
    }
    
    private fun isCastConnected(): Boolean {
        castSession = CastContext.getSharedInstance(this).sessionManager.currentCastSession
        return castSession?.isConnected == true
    }
    
    private fun stopCasting() {
        castSession?.remoteMediaClient?.stop()
    }
}
```

5. **Flutter Implementation** (`lib/services/cast_service.dart`):
```dart
import 'package:flutter/services.dart';

class CastService {
  static const platform = MethodChannel('com.tvviewer.app/cast');
  
  static Future<bool> castVideo({
    required String url,
    String? title,
    String? imageUrl,
  }) async {
    try {
      final result = await platform.invokeMethod('castVideo', {
        'url': url,
        'title': title,
        'imageUrl': imageUrl,
      });
      return result as bool;
    } catch (e) {
      debugPrint('Cast error: $e');
      return false;
    }
  }
  
  static Future<bool> isCastConnected() async {
    try {
      final result = await platform.invokeMethod('isCastConnected');
      return result as bool;
    } catch (e) {
      return false;
    }
  }
  
  static Future<void> stopCasting() async {
    try {
      await platform.invokeMethod('stopCasting');
    } catch (e) {
      debugPrint('Stop cast error: $e');
    }
  }
}
```

#### 5.2 Simpler Alternative: DLNA/UPnP Casting
**Approach**: Use DLNA for local network casting (no Google dependency)

**Recommendation**: Use `flutter_upnp` or `dlna_dart` packages for simpler implementation.

---

## 6. APK Build Configuration

### ✅ Current Configuration
- ✓ ProGuard enabled for release builds
- ✓ Resource shrinking enabled
- ✓ MultiDex enabled
- ✓ Modern Gradle (8.2) and AGP (8.2.0)
- ✓ Kotlin 1.9.22
- ✓ Compile/Target SDK 34 (Android 14)

### ⚠️ Critical Issues

#### 6.1 Missing ProGuard Rules File
**Issue**: ProGuard enabled but no custom rules file exists!

**Impact**: App may crash in release mode due to code stripping of essential classes (video_player, networking, etc.)

**CRITICAL FIX**: Create ProGuard rules file:

**File**: `android/app/proguard-rules.pro`
```proguard
# Flutter wrapper
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.**  { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# Video Player - ExoPlayer
-keep class com.google.android.exoplayer2.** { *; }
-keep interface com.google.android.exoplayer2.** { *; }
-dontwarn com.google.android.exoplayer2.**

# HTTP Client (OkHttp - used by video_player and http package)
-dontwarn okhttp3.**
-dontwarn okio.**
-keepnames class okhttp3.internal.publicsuffix.PublicSuffixDatabase
-keep class okhttp3.** { *; }
-keep interface okhttp3.** { *; }

# URL Launcher
-keep class io.flutter.plugins.urllauncher.** { *; }

# Shared Preferences
-keep class io.flutter.plugins.sharedpreferences.** { *; }

# Path Provider
-keep class io.flutter.plugins.pathprovider.** { *; }

# Prevent stripping of native methods
-keepclasseswithmembernames class * {
    native <methods>;
}

# Keep Kotlin metadata
-keep class kotlin.Metadata { *; }
-keepclassmembers class ** {
    @kotlin.Metadata *;
}

# Keep Google Fonts (if used)
-keep class com.google.fonts.** { *; }

# Keep Provider classes
-keep class * extends androidx.lifecycle.ViewModel { *; }
-keep class * extends androidx.lifecycle.AndroidViewModel { *; }

# Prevent obfuscation of model classes (JSON serialization)
-keepclassmembers class com.tvviewer.app.** {
    <init>(...);
    <fields>;
}

# Crashlytics (if added later)
-keepattributes SourceFile,LineNumberTable
-keep public class * extends java.lang.Exception

# General Android
-keep class androidx.** { *; }
-keep interface androidx.** { *; }

# Remove logging in release (optional - reduces APK size)
-assumenosideeffects class android.util.Log {
    public static *** d(...);
    public static *** v(...);
    public static *** i(...);
}

# Keep R8 compatible
-dontwarn org.bouncycastle.**
-dontwarn org.conscrypt.**
-dontwarn org.openjsse.**
```

#### 6.2 Using Debug Signing in Release Build
**CRITICAL SECURITY ISSUE**: Release build uses debug signing!

```gradle
release {
    signingConfig signingConfigs.debug  // ❌ NEVER DO THIS IN PRODUCTION
    minifyEnabled true
    shrinkResources true
    proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
}
```

**Fix**: Create proper release signing:

1. **Generate release keystore**:
```bash
keytool -genkey -v -keystore ~/upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

2. **Create `android/key.properties`** (DO NOT commit to git!):
```properties
storePassword=your_keystore_password
keyPassword=your_key_password
keyAlias=upload
storeFile=C:/path/to/upload-keystore.jks
```

3. **Update `.gitignore`**:
```gitignore
**/android/key.properties
**/android/*.jks
**/android/*.keystore
```

4. **Update `android/app/build.gradle`**:
```gradle
// Load keystore properties
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    // ... existing config ...
    
    signingConfigs {
        release {
            if (keystorePropertiesFile.exists()) {
                keyAlias keystoreProperties['keyAlias']
                keyPassword keystoreProperties['keyPassword']
                storeFile file(keystoreProperties['storeFile'])
                storePassword keystoreProperties['storePassword']
            }
        }
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release  // ✅ Use release signing
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
        
        debug {
            signingConfig signingConfigs.debug
            applicationIdSuffix ".debug"
            versionNameSuffix "-DEBUG"
        }
    }
}
```

#### 6.3 Missing Build Flavors
**Recommendation**: Add build flavors for different environments:

```gradle
android {
    // ... existing config ...
    
    flavorDimensions = ["environment"]
    
    productFlavors {
        production {
            dimension "environment"
            applicationIdSuffix ""
            versionNameSuffix ""
        }
        
        staging {
            dimension "environment"
            applicationIdSuffix ".staging"
            versionNameSuffix "-staging"
        }
        
        development {
            dimension "environment"
            applicationIdSuffix ".dev"
            versionNameSuffix "-dev"
        }
    }
}
```

Build commands:
```bash
flutter build apk --release --flavor production
flutter build apk --release --flavor staging
```

#### 6.4 APK Optimization
**Add App Bundles support** for smaller downloads:

```bash
flutter build appbundle --release
```

**Split APKs by ABI** (reduces APK size by 30-40%):

```gradle
android {
    // ... existing config ...
    
    splits {
        abi {
            enable true
            reset()
            include 'armeabi-v7a', 'arm64-v8a', 'x86_64'
            universalApk true
        }
    }
}
```

This creates:
- `app-armeabi-v7a-release.apk` (~20 MB)
- `app-arm64-v8a-release.apk` (~25 MB)  
- `app-x86_64-release.apk` (~27 MB)
- `app-universal-release.apk` (~50 MB) - fallback

#### 6.5 Gradle Build Performance
**Add to `gradle.properties`**:
```properties
org.gradle.jvmargs=-Xmx4G
android.useAndroidX=true
android.enableJetifier=true

# Performance optimizations
org.gradle.daemon=true
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.configureondemand=true

# Kotlin compiler optimizations
kotlin.code.style=official
kotlin.incremental=true
kotlin.incremental.java=true
kotlin.incremental.js=true

# R8 optimizations
android.enableR8.fullMode=true
```

#### 6.6 Version Management
**Issue**: Version hardcoded in `build.gradle`, inconsistent with `pubspec.yaml`

**Fix**: Read version from pubspec.yaml:

```gradle
def flutterVersionCode = localProperties.getProperty('flutter.versionCode')
if (flutterVersionCode == null) {
    flutterVersionCode = '1'
}

def flutterVersionName = localProperties.getProperty('flutter.versionName')
if (flutterVersionName == null) {
    // Read from pubspec.yaml instead
    def pubspecFile = file("$rootDir/../pubspec.yaml")
    def pubspecContent = pubspecFile.text
    def versionMatch = (pubspecContent =~ /version:\s*(\S+)/)
    flutterVersionName = versionMatch ? versionMatch[0][1].split('\\+')[0] : '1.5.0'
}
```

---

## 7. Additional Critical Issues

### 7.1 minSdk 24 (Android 7.0) Too High
**Issue**: Excludes 5-10% of Android devices

**Current**: `minSdk 24` (Android 7.0, 2016)

**Recommendation**: Lower to `minSdk 21` (Android 5.0, 2014) for wider compatibility:

```gradle
defaultConfig {
    applicationId "com.tvviewer.app"
    minSdk 21  // Android 5.0+ (covers 99%+ of devices)
    targetSdk 34
    // ...
}
```

**Required Changes**:
- Test on Android 5.0/6.0 devices
- Check ExoPlayer minimum SDK requirement (it supports 21+)

### 7.2 Missing Crash Reporting
**Recommendation**: Add Firebase Crashlytics or Sentry

**Firebase Crashlytics** (recommended for Android):

1. Add to `build.gradle` (project level):
```gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.0'
        classpath 'com.google.firebase:firebase-crashlytics-gradle:2.9.9'
    }
}
```

2. Add to `build.gradle` (app level):
```gradle
plugins {
    id 'com.android.application'
    id 'kotlin-android'
    id 'dev.flutter.flutter-gradle-plugin'
    id 'com.google.gms.google-services'
    id 'com.google.firebase.crashlytics'
}

dependencies {
    implementation platform('com.google.firebase:firebase-bom:32.7.0')
    implementation 'com.google.firebase:firebase-crashlytics'
    implementation 'com.google.firebase:firebase-analytics'
}
```

3. Flutter dependency:
```yaml
dependencies:
  firebase_core: ^2.24.2
  firebase_crashlytics: ^3.4.8
```

4. Initialize in `main.dart`:
```dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterError;
  runApp(const TVViewerApp());
}
```

### 7.3 No Analytics
**Recommendation**: Add analytics to track:
- Most-watched channels
- Playback errors
- External player usage
- Network quality issues

### 7.4 Missing App Size Reporting
**Add to `build.gradle`**:
```gradle
android {
    buildTypes {
        release {
            // ... existing config ...
            
            // Enable size reporting
            postprocessing {
                removeUnusedCode true
                removeUnusedResources true
                obfuscate true
                optimizeCode true
            }
        }
    }
}
```

### 7.5 No Battery Optimization Handling
**Issue**: System may kill app during background streaming

**Add to AndroidManifest.xml**:
```xml
<uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS"/>
```

**Request exemption in code** (player_screen.dart):
```dart
import 'package:battery_plus/battery_plus.dart';

Future<void> _requestBatteryOptimizationExemption() async {
  if (Platform.isAndroid) {
    final battery = Battery();
    // Check and request exemption
    // This requires platform channel implementation
  }
}
```

---

## 8. Performance Optimizations

### 8.1 Enable Impeller (Flutter 3.16+)
**Add to AndroidManifest.xml**:
```xml
<application>
    <meta-data
        android:name="io.flutter.embedding.android.EnableImpeller"
        android:value="true" />
</application>
```

This enables Flutter's new rendering engine (2-3x faster on Android).

### 8.2 Optimize Image Loading
**Issue**: Channel logos loaded without caching

**Recommendation**: Add `cached_network_image`:

```yaml
dependencies:
  cached_network_image: ^3.3.1
```

Replace logo loading with:
```dart
CachedNetworkImage(
  imageUrl: channel.logo!,
  placeholder: (context, url) => Icon(Icons.tv),
  errorWidget: (context, url, error) => Icon(Icons.tv),
  cacheManager: CacheManager(
    Config(
      'channelLogos',
      stalePeriod: const Duration(days: 7),
      maxNrOfCacheObjects: 200,
    ),
  ),
)
```

### 8.3 Lazy Loading Channels
**Issue**: All channels loaded at once

**Recommendation**: Implement pagination with `ListView.builder` or use `flutter_pagewise`.

---

## 9. Security Recommendations

### 9.1 Add Certificate Transparency
**Protect against MITM attacks**:

```xml
<network-security-config>
    <base-config>
        <trust-anchors>
            <certificates src="system"/>
        </trust-anchors>
        <!-- Enforce certificate transparency -->
        <pin-set>
            <pin digest="SHA-256">base64_pin_here==</pin>
        </pin-set>
    </base-config>
</network-security-config>
```

### 9.2 Prevent Screenshot/Screen Recording
**For DRM-protected content**:

```dart
// In player_screen.dart
import 'package:flutter/services.dart';

@override
void initState() {
  super.initState();
  // Prevent screenshots
  SystemChrome.setEnabledSystemUIMode(
    SystemUiMode.immersive,
    overlays: [],
  );
  
  // This requires platform channel to set FLAG_SECURE
}
```

**Android implementation**:
```kotlin
// In MainActivity.kt
override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    window.setFlags(
        WindowManager.LayoutParams.FLAG_SECURE,
        WindowManager.LayoutParams.FLAG_SECURE
    )
}
```

### 9.3 Obfuscate Dart Code
**Build with obfuscation**:
```bash
flutter build apk --release --obfuscate --split-debug-info=build/debug-info
```

This makes reverse engineering harder.

---

## 10. Testing Recommendations

### 10.1 Add Integration Tests
**Create**: `integration_test/app_test.dart`
```dart
import 'package:integration_test/integration_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tv_viewer/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  
  testWidgets('Load and play channel', (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle();
    
    // Find and tap first channel
    final firstChannel = find.byType(ListTile).first;
    await tester.tap(firstChannel);
    await tester.pumpAndSettle();
    
    // Verify player screen opened
    expect(find.byType(VideoPlayer), findsOneWidget);
  });
}
```

### 10.2 Test on Multiple Android Versions
**Recommended test matrix**:
- Android 5.0 (API 21) - minSdk
- Android 7.0 (API 24) - current minSdk
- Android 10.0 (API 29) - scoped storage
- Android 11.0 (API 30) - package visibility
- Android 14.0 (API 34) - targetSdk

### 10.3 Test Different Network Conditions
Use Android Studio's Network Profiler to simulate:
- Slow 3G
- Fast 4G
- WiFi
- Network interruptions

---

## 11. Summary of Critical Fixes (Priority Order)

### 🔴 **CRITICAL** (Fix Immediately)
1. ✅ **Create ProGuard rules file** - App will crash in release mode without it
2. ✅ **Fix release signing** - Using debug keystore is a security vulnerability
3. ✅ **Add WAKE_LOCK permission** - Screen turns off during playback
4. ✅ **Fix external player intents** - Current implementation doesn't work properly

### 🟠 **HIGH PRIORITY** (Fix Before Production)
5. ✅ Add wakelock implementation (package)
6. ✅ Improve network security config (domain-specific cleartext)
7. ✅ Add ExoPlayer buffer optimization
8. ✅ Implement proper external player service
9. ✅ Add crash reporting (Firebase Crashlytics)
10. ✅ Lower minSdk to 21 for wider compatibility

### 🟡 **MEDIUM PRIORITY** (Enhance UX)
11. ✅ Add audio focus handling
12. ✅ Implement PiP support
13. ✅ Add adaptive bitrate selection
14. ✅ Implement cast functionality (Google Cast or DLNA)
15. ✅ Add image caching for channel logos
16. ✅ Add build flavors

### 🟢 **LOW PRIORITY** (Nice to Have)
17. ✅ Add analytics
18. ✅ Enable Impeller rendering
19. ✅ Add integration tests
20. ✅ Implement APK splitting by ABI

---

## 12. Build Commands

### Development Build
```bash
flutter build apk --debug --flavor development
```

### Release Build (after implementing signing)
```bash
# Full APK
flutter build apk --release --flavor production

# App Bundle (for Play Store)
flutter build appbundle --release --flavor production

# With obfuscation
flutter build apk --release --obfuscate --split-debug-info=build/debug-info
```

### Testing Release Build
```bash
# Install release APK
flutter install --release

# Or manually
adb install build/app/outputs/flutter-apk/app-production-release.apk
```

---

## 13. Next Steps

1. **Week 1**: Fix critical issues (ProGuard, signing, wake lock)
2. **Week 2**: Implement high-priority items (ExoPlayer optimization, external players)
3. **Week 3**: Add medium-priority enhancements (PiP, cast, adaptive streaming)
4. **Week 4**: Testing, analytics, and optimization
5. **Week 5**: Production release preparation

---

## Additional Resources

- **Flutter Video Player**: https://pub.dev/packages/video_player
- **ExoPlayer Documentation**: https://exoplayer.dev/
- **Android Network Security**: https://developer.android.com/training/articles/security-config
- **ProGuard Rules**: https://www.guardsquare.com/manual/configuration/examples
- **Google Cast SDK**: https://developers.google.com/cast/docs/android_sender
- **Flutter Performance**: https://docs.flutter.dev/perf

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Reviewed By**: Senior Android Developer  
**Status**: Comprehensive Review Complete
