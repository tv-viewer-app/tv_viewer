# Firebase Services Architecture Diagram

## 📊 System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TV Viewer Application                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ChannelList   │  │Player Screen │  │Settings      │  │Playlist Mgr  ││
│  │Screen        │  │              │  │Screen        │  │Screen        ││
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘│
│         │                 │                 │                 │         │
│         │ logScreenView() │ logChannelPlay()│ logSettings()  │ logScan()│
│         │                 │                 │                 │         │
│         └─────────────────┴─────────────────┴─────────────────┘         │
│                                    │                                    │
│                                    ▼                                    │
│         ┌──────────────────────────────────────────────────┐           │
│         │      Dependency Injection (GetIt)                │           │
│         │  getIt<AnalyticsService>()                       │           │
│         │  getIt<CrashlyticsService>()                     │           │
│         └──────────────────────────────────────────────────┘           │
│                                    │                                    │
│         ┌──────────────────────────┴────────────────────────┐          │
│         │                                                    │          │
│         ▼                                                    ▼          │
│  ┌─────────────────────────┐                   ┌─────────────────────┐ │
│  │  AnalyticsService       │                   │ CrashlyticsService  │ │
│  ├─────────────────────────┤                   ├─────────────────────┤ │
│  │ • logEvent()            │                   │ • recordError()     │ │
│  │ • logScreenView()       │                   │ • setCustomKey()    │ │
│  │ • logChannelPlay()      │                   │ • log()             │ │
│  │ • logScanStart()        │                   │ • setUserIdentifier │ │
│  │ • logFilterApplied()    │                   │ • crash() [test]    │ │
│  │ • setUserId()           │                   │                     │ │
│  │ • setUserProperty()     │                   │                     │ │
│  └───────────┬─────────────┘                   └──────────┬──────────┘ │
│              │                                             │            │
│              │ _firebaseAvailable?                        │            │
│              └────────────┬────────────────────────────────┘            │
│                           │                                             │
│                  ┌────────┴────────┐                                    │
│                  │ YES         NO  │                                    │
│                  ▼                 ▼                                    │
│    ┌─────────────────────┐  ┌────────────────────┐                    │
│    │ Firebase Analytics  │  │  LoggerService     │                    │
│    │ & Crashlytics       │  │  (Fallback)        │                    │
│    └─────────┬───────────┘  └──────────┬─────────┘                    │
│              │                          │                              │
└──────────────┼──────────────────────────┼──────────────────────────────┘
               │                          │
               ▼                          ▼
    ┌──────────────────────┐   ┌─────────────────────┐
    │  Firebase Console    │   │  Local Log Files    │
    ├──────────────────────┤   ├─────────────────────┤
    │ • Analytics Events   │   │ app_log_*.txt       │
    │ • Crashlytics        │   │ (Rotating logs)     │
    │ • User Behavior      │   │                     │
    │ • Error Trends       │   │ Files in:           │
    │                      │   │ /logs/              │
    │ Requires:            │   │                     │
    │ google-services.json │   │ ✅ Always works     │
    └──────────────────────┘   └─────────────────────┘
```

## 🔄 Request Flow

### Scenario 1: WITHOUT Firebase (Default)

```
User plays channel
       │
       ▼
┌─────────────────┐
│ Player Screen   │ analytics.logChannelPlay(...)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ AnalyticsService                            │
│ ├─ Check: _firebaseAvailable? ────> FALSE  │
│ └─ Route: Fallback mode                    │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ LoggerService                           │
│ ├─ Write to: app_log_20240101.txt      │
│ └─ Output: [INFO] [Analytics] Event... │
└─────────────────────────────────────────┘
         │
         ▼
   Local Files
   ✅ No network
   ✅ No Firebase needed
   ✅ Works offline
```

### Scenario 2: WITH Firebase (When Enabled)

```
User plays channel
       │
       ▼
┌─────────────────┐
│ Player Screen   │ analytics.logChannelPlay(...)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ AnalyticsService                            │
│ ├─ Check: _firebaseAvailable? ────> TRUE   │
│ └─ Route: Firebase mode                    │
└────────┬────────────────────────────────────┘
         │
         ├────────────────┬─────────────────┐
         ▼                ▼                 ▼
┌────────────────┐ ┌──────────────┐ ┌───────────────┐
│Firebase        │ │LoggerService │ │Local Debug    │
│Analytics       │ │(also logged) │ │Print          │
│                │ │              │ │               │
│→ Remote        │ │→ Local file  │ │→ Console      │
│  Dashboard     │ │              │ │               │
└────────────────┘ └──────────────┘ └───────────────┘
```

## 🏗️ Service Architecture

### AnalyticsService Internal

```
┌─────────────────────────────────────────────────────────────┐
│ AnalyticsService (Singleton)                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  State:                                                      │
│  ├─ _isInitialized: bool                                    │
│  ├─ _firebaseAvailable: bool                                │
│  ├─ _analytics: dynamic (Firebase instance or null)         │
│  └─ _logger: LoggerService                                  │
│                                                              │
│  Initialization:                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │ initialize()                                      │      │
│  │   ├─> _initializeFirebase()                      │      │
│  │   │    ├─ Try: Firebase.initializeApp()          │      │
│  │   │    ├─ Success: _firebaseAvailable = true     │      │
│  │   │    └─ Failure: _firebaseAvailable = false    │      │
│  │   └─> _isInitialized = true                      │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  Public Methods:                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │ logEvent(name, parameters)                        │      │
│  │   ├─ if (_firebaseAvailable)                     │      │
│  │   │     Firebase.logEvent()                       │      │
│  │   └─ else                                         │      │
│  │         Logger.info()                             │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  Convenience Methods:                                        │
│  ├─ logAppStart()         → logEvent('app_start')           │
│  ├─ logChannelPlay()      → logEvent('channel_play', ...)   │
│  ├─ logScanStart()        → logEvent('scan_start', ...)     │
│  ├─ logScanComplete()     → logEvent('scan_complete', ...)  │
│  ├─ logFilterApplied()    → logEvent('filter_applied', ...) │
│  └─ logError()            → logEvent('error_occurred', ...) │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### CrashlyticsService Internal

```
┌─────────────────────────────────────────────────────────────┐
│ CrashlyticsService (Singleton)                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  State:                                                      │
│  ├─ _isInitialized: bool                                    │
│  ├─ _firebaseAvailable: bool                                │
│  ├─ _crashlytics: dynamic (Firebase instance or null)       │
│  └─ _logger: LoggerService                                  │
│                                                              │
│  Initialization:                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │ initialize()                                      │      │
│  │   ├─> _initializeFirebase()                      │      │
│  │   │    ├─ Try: Firebase.initializeApp()          │      │
│  │   │    │       FirebaseCrashlytics.instance       │      │
│  │   │    ├─ Success: _firebaseAvailable = true     │      │
│  │   │    └─ Failure: _firebaseAvailable = false    │      │
│  │   ├─> if (_firebaseAvailable)                    │      │
│  │   │      _setupFlutterErrorHandler()              │      │
│  │   │   else                                         │      │
│  │   │      _setupFallbackErrorHandler()             │      │
│  │   └─> _isInitialized = true                      │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  Error Handlers:                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │ FlutterError.onError = (details) {                │      │
│  │   recordFlutterError(details)                     │      │
│  │ }                                                  │      │
│  │                                                    │      │
│  │ PlatformDispatcher.instance.onError = (e, s) {    │      │
│  │   recordError(e, s, fatal: true)                  │      │
│  │ }                                                  │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  Public Methods:                                             │
│  ├─ recordError()          → Log error (fatal/non-fatal)    │
│  ├─ recordFlutterError()   → Log Flutter framework error    │
│  ├─ setCustomKey()         → Add context to crashes         │
│  ├─ setUserIdentifier()    → Set user ID                    │
│  ├─ log()                  → Log breadcrumb                 │
│  └─ crash()                → Test crash [DEV ONLY]          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🔀 Decision Flow

### Should Firebase be Enabled?

```
                    Start
                      │
                      ▼
        ┌─────────────────────────────┐
        │ Do you need remote          │
        │ analytics/crash reports?    │
        └─────────┬────────┬──────────┘
                  │        │
              YES │        │ NO
                  │        │
                  ▼        ▼
        ┌─────────────┐  ┌──────────────────┐
        │Enable       │  │Use fallback mode │
        │Firebase     │  │(current state)   │
        │             │  │                  │
        │Follow       │  │✅ No setup       │
        │FIREBASE_    │  │✅ Works now      │
        │SETUP.md     │  │✅ Local logs     │
        │             │  │                  │
        │Time: 30min  │  │Ready: Now        │
        └─────────────┘  └──────────────────┘
```

## 📱 Integration Points

### Where to Add Analytics

```
┌───────────────────────────────────────────────────────────┐
│ App Lifecycle                                             │
├───────────────────────────────────────────────────────────┤
│ main.dart                                                 │
│   └─> logAppStart()                           [PRIORITY]  │
└───────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│ Navigation                                                │
├───────────────────────────────────────────────────────────┤
│ Every screen's initState()                                │
│   └─> logScreenView()                         [PRIORITY]  │
└───────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│ User Actions                                              │
├───────────────────────────────────────────────────────────┤
│ Player Screen                                             │
│   └─> logChannelPlay()                        [CRITICAL]  │
│                                                            │
│ Playlist Manager                                          │
│   ├─> logScanStart()                          [IMPORTANT] │
│   └─> logScanComplete()                       [IMPORTANT] │
│                                                            │
│ Filter Usage                                              │
│   └─> logFilterApplied()                      [IMPORTANT] │
│                                                            │
│ Favorites                                                 │
│   └─> logFavoritesToggled()                   [NICE]      │
│                                                            │
│ Settings                                                  │
│   └─> logSettingsChanged()                    [NICE]      │
└───────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│ Error Handling                                            │
├───────────────────────────────────────────────────────────┤
│ Global Error Handler                                      │
│   ├─> crashlytics.recordError()               [CRITICAL]  │
│   └─> analytics.logError()                    [CRITICAL]  │
└───────────────────────────────────────────────────────────┘
```

## 🎯 Data Flow

### Analytics Event Journey

```
User Action
    │
    ├─> [App Code] analytics.logChannelPlay(...)
    │                     │
    │                     ▼
    │        [AnalyticsService] Check Firebase available?
    │                     │
    │         ┌───────────┴────────────┐
    │         │                        │
    │     Firebase                  Fallback
    │         │                        │
    │         ▼                        ▼
    │   Firebase SDK            LoggerService
    │         │                        │
    │         ├─> Queue locally        ├─> Write to file
    │         ├─> Batch send           │   app_log_*.txt
    │         └─> Upload when online   │
    │                  │               │
    │                  ▼               ▼
    │         Firebase Console    Local Storage
    │         • Analytics Tab     • /logs/ directory
    │         • Real-time         • Can export/share
    │         • Aggregated        • Immediate access
    │         • 1-24h delay       • No delay
    └─────────────────────────────────────────
```

### Crash Report Journey

```
Exception Thrown
    │
    ├─> [Error Handler] crashlytics.recordError(e, stack)
    │                          │
    │                          ▼
    │         [CrashlyticsService] Check Firebase available?
    │                          │
    │              ┌───────────┴────────────┐
    │              │                        │
    │          Firebase                  Fallback
    │              │                        │
    │              ▼                        ▼
    │      Firebase SDK              LoggerService
    │              │                        │
    │              ├─> Symbolicate          ├─> Log error
    │              ├─> Add context          │   with stack trace
    │              ├─> Queue for send       │
    │              └─> Upload                │
    │                     │                  │
    │                     ▼                  ▼
    │         Firebase Console         Local Log File
    │         • Crashlytics Tab        • Full error details
    │         • Stack traces           • Stack trace
    │         • Affected users         • Timestamp
    │         • Crash trends           • Custom context
    └───────────────────────────────────────────────
```

## 🔐 Security Model

```
┌─────────────────────────────────────────────────────────┐
│ Configuration Files                                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  google-services.json                                   │
│  ├─ Location: android/app/                              │
│  ├─ Contains: API keys, Project IDs                     │
│  ├─ Security: Keys restricted by package name           │
│  ├─ Private Repos: ✅ Safe to commit                    │
│  └─ Public Repos: ❌ Add to .gitignore                  │
│                                                          │
│  pubspec.yaml                                            │
│  ├─ Contains: Package dependencies only                 │
│  ├─ No secrets                                           │
│  └─ Safe to commit: ✅                                  │
│                                                          │
│  Service Code                                            │
│  ├─ No hardcoded keys                                    │
│  ├─ Firebase code commented (not active)                │
│  └─ Safe to commit: ✅                                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 📊 Current vs. Firebase Enabled

```
┌────────────────────┬─────────────────────┬──────────────────────┐
│ Feature            │ Without Firebase    │ With Firebase        │
│                    │ (Current)           │ (Optional)           │
├────────────────────┼─────────────────────┼──────────────────────┤
│ Analytics tracking │ ✅ Local files      │ ✅ Firebase Console  │
│ Crash reporting    │ ✅ Local files      │ ✅ Firebase Console  │
│ Remote monitoring  │ ❌ Not available    │ ✅ Available         │
│ Real-time data     │ ❌ Not available    │ ✅ Available         │
│ User segmentation  │ ❌ Manual           │ ✅ Automatic         │
│ Error aggregation  │ ❌ Manual           │ ✅ Automatic         │
│ Setup required     │ ✅ None             │ ⚠️ 30 minutes       │
│ Works offline      │ ✅ Yes              │ ✅ Yes (queues)      │
│ Cost               │ ✅ Free             │ ✅ Free (tier)       │
│ Data ownership     │ ✅ 100% local       │ ⚠️ Stored in Cloud  │
└────────────────────┴─────────────────────┴──────────────────────┘
```

---

**Diagram Version**: 1.0  
**Last Updated**: 2024  
**Related**: FIREBASE_IMPLEMENTATION_COMPLETE.md
