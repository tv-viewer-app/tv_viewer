# Error Handling System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TV VIEWER APP                               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
  │ Player Screen│      │ M3U Service  │      │ Other Files  │
  └──────────────┘      └──────────────┘      └──────────────┘
          │                       │                       │
          │  try-catch            │  try-catch            │  try-catch
          ▼                       ▼                       ▼
  ┌────────────────────────────────────────────────────────────┐
  │                    ErrorHandler.handle()                   │
  │  • SocketException    → ERR_NET_001                       │
  │  • TimeoutException   → ERR_NET_002                       │
  │  • FormatException    → ERR_M3U_001                       │
  │  • HttpException      → ERR_NET_003                       │
  │  • VideoPlayer...     → ERR_STREAM_001                    │
  └────────────────────────────────────────────────────────────┘
          │
          │  Returns AppError
          ▼
  ┌────────────────────────────────────────────────────────────┐
  │                        AppError                            │
  │  • code: "ERR_NET_001"                                    │
  │  • userMessage: "Network connection problem"              │
  │  • recoverySuggestion: "Check WiFi..."                    │
  │  • technicalDetails: "SocketException..."                 │
  │  • originalException: SocketException                     │
  │  • stackTrace: ...                                         │
  └────────────────────────────────────────────────────────────┘
          │
          ├─────────────────┬─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ Log to File  │  │ Show to User │  │ Track Error  │
  │ logger.error │  │ setState     │  │ Analytics    │
  └──────────────┘  └──────────────┘  └──────────────┘
```

---

## Error Flow Example: Network Error

```
User Action: Opens channel
      │
      ▼
┌──────────────────────────────────────────────────────────┐
│ 1. PlayerScreen._initializePlayer()                      │
│    try {                                                  │
│      await VideoPlayerController.initialize()            │
│    }                                                      │
└──────────────────────────────────────────────────────────┘
      │
      │ Network unavailable
      ▼
┌──────────────────────────────────────────────────────────┐
│ 2. Exception thrown: SocketException                     │
│    "Network is unreachable"                              │
└──────────────────────────────────────────────────────────┘
      │
      │ catch (e, stackTrace)
      ▼
┌──────────────────────────────────────────────────────────┐
│ 3. ErrorHandler.handle(e, stackTrace)                    │
│    • Detects: SocketException                            │
│    • Maps to: ERR_NET_001                                │
│    • Creates: AppError with friendly message             │
└──────────────────────────────────────────────────────────┘
      │
      │ Returns AppError
      ▼
┌──────────────────────────────────────────────────────────┐
│ 4. Log error                                             │
│    logger.error('Player init failed', e, stackTrace)     │
│    → Writes to: app_log_20250615_143205.txt             │
└──────────────────────────────────────────────────────────┘
      │
      │ setState
      ▼
┌──────────────────────────────────────────────────────────┐
│ 5. Display to user                                       │
│    ┌────────────────────────────────────────┐           │
│    │ 🔴 Network connection problem          │           │
│    │ ────────────────────────────────────── │           │
│    │ 💡 What to do:                         │           │
│    │ • Check WiFi or mobile data            │           │
│    │ • Try restarting your router           │           │
│    │ • Check if other apps can connect      │           │
│    │                                         │           │
│    │ Error Code: ERR_NET_001                │           │
│    │                                         │           │
│    │ [Retry]  [External Player]             │           │
│    └────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────┘
```

---

## Logging System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application                              │
│  • PlayerScreen                                                 │
│  • M3UService                                                   │
│  • ChannelProvider                                              │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │ logger.debug()
                          │ logger.info()
                          │ logger.warning()
                          │ logger.error()
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LoggerService (Singleton)                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Log Buffer                                             │    │
│  │ • Entry 1: [2025-06-15 14:32:05] [INFO] App started   │    │
│  │ • Entry 2: [2025-06-15 14:32:10] [ERROR] Failed...    │    │
│  │ • Entry 3: [2025-06-15 14:32:15] [DEBUG] Debug...     │    │
│  └────────────────────────────────────────────────────────┘    │
│                          │                                       │
│                          │ Flush every 5 seconds                │
│                          │ (immediately for errors)              │
│                          ▼                                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Current Log File: app_log_20250615_143205.txt        │    │
│  │ Size: 850 KB / 1024 KB                                │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │ Rotation when full
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Device Storage: /logs/                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ app_log_20250615_143205.txt  (1.0 MB) ← Current       │    │
│  │ app_log_20250615_120000.txt  (1.0 MB)                 │    │
│  │ app_log_20250614_180000.txt  (0.8 MB)                 │    │
│  │ app_log_20250614_140000.txt  (1.0 MB)                 │    │
│  │ app_log_20250613_220000.txt  (0.5 MB)                 │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  When 6th file created → Delete oldest                          │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │ Export / View
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LogViewerScreen                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Files: 5  │  Size: 4.3 MB  │  Lines: 12,543         │    │
│  └────────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ [2025-06-15 14:32:05.123] [INFO] App started          │    │
│  │ [2025-06-15 14:32:06.456] [DEBUG] Loading channels... │    │
│  │ [2025-06-15 14:32:10.789] [ERROR] Network failed      │    │
│  │ Error: SocketException: Network unreachable            │    │
│  │ Stack trace: ...                                       │    │
│  └────────────────────────────────────────────────────────┘    │
│  [Export] [Copy] [Clear]                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Error Code Categories

```
┌─────────────────────────────────────────────────────────────┐
│                     Error Codes                             │
└─────────────────────────────────────────────────────────────┘
      │
      ├─── ERR_NET_xxx (Network Errors)
      │    ├── ERR_NET_001: No Internet
      │    ├── ERR_NET_002: Timeout
      │    ├── ERR_NET_003: Server Error
      │    ├── ERR_NET_004: Not Found (404)
      │    ├── ERR_NET_005: Unauthorized (401)
      │    ├── ERR_NET_006: Forbidden (403)
      │    └── ERR_NET_007: Connection Refused
      │
      ├─── ERR_STREAM_xxx (Stream Errors)
      │    ├── ERR_STREAM_001: Not Available
      │    ├── ERR_STREAM_002: Timeout
      │    ├── ERR_STREAM_003: Format Unsupported
      │    ├── ERR_STREAM_004: Init Failed
      │    ├── ERR_STREAM_005: Playback Error
      │    └── ERR_STREAM_006: Codec Error
      │
      ├─── ERR_M3U_xxx (Playlist Errors)
      │    ├── ERR_M3U_001: Invalid Format
      │    ├── ERR_M3U_002: Empty
      │    ├── ERR_M3U_003: Parse Failed
      │    └── ERR_M3U_004: No Channels
      │
      ├─── ERR_STORAGE_xxx (Storage Errors)
      │    ├── ERR_STORAGE_001: Storage Failed
      │    ├── ERR_STORAGE_002: Cache Read Failed
      │    └── ERR_STORAGE_003: Cache Write Failed
      │
      └─── ERR_GEN_xxx (General Errors)
           ├── ERR_GEN_001: Unknown
           ├── ERR_GEN_002: Invalid Input
           └── ERR_GEN_003: Permission Denied
```

---

## Exception to AppError Mapping

```
┌──────────────────────────┐
│  Dart/Flutter Exception  │
└──────────────────────────┘
           │
           ▼
┌──────────────────────────┐       ┌────────────────────────┐
│  SocketException         │ ───→  │ ERR_NET_001            │
└──────────────────────────┘       │ "Network problem"      │
                                    │ "Check WiFi..."        │
┌──────────────────────────┐       └────────────────────────┘
│  TimeoutException        │ ───→  │ ERR_NET_002            │
└──────────────────────────┘       │ "Connection timeout"   │
                                    │ "Check speed..."       │
┌──────────────────────────┐       └────────────────────────┘
│  FormatException         │ ───→  │ ERR_M3U_001            │
└──────────────────────────┘       │ "Invalid format"       │
                                    │ "Verify M3U..."        │
┌──────────────────────────┐       └────────────────────────┘
│  HttpException           │ ───→  │ ERR_NET_003            │
└──────────────────────────┘       │ "Server error"         │
                                    │ "Try later..."         │
┌──────────────────────────┐       └────────────────────────┘
│  FileSystemException     │ ───→  │ ERR_STORAGE_001        │
└──────────────────────────┘       │ "Storage failed"       │
                                    │ "Check space..."       │
┌──────────────────────────┐       └────────────────────────┘
│  VideoPlayerPlatform...  │ ───→  │ ERR_STREAM_001/003/005 │
└──────────────────────────┘       │ "Stream error"         │
                                    │ "Try another..."       │
┌──────────────────────────┐       └────────────────────────┘
│  Unknown Exception       │ ───→  │ ERR_GEN_001            │
└──────────────────────────┘       │ "Unexpected error"     │
                                    │ "Try again..."         │
                                    └────────────────────────┘
```

---

## User Experience Flow

```
┌─────────────────────────────────────────────────────────────┐
│  WITHOUT Error Handling (Before)                           │
└─────────────────────────────────────────────────────────────┘
User opens channel
      │
      ▼
Exception: SocketException: Network is unreachable
OS Error: Network is unreachable, errno = 101
      │
      ▼
User confused: What does this mean? How do I fix it?
      │
      ▼
User gives up or contacts support


┌─────────────────────────────────────────────────────────────┐
│  WITH Error Handling (After)                               │
└─────────────────────────────────────────────────────────────┘
User opens channel
      │
      ▼
┌────────────────────────────────────────┐
│ 🔴 Network connection problem          │
│ ────────────────────────────────────── │
│ 💡 What to do:                         │
│ • Check WiFi or mobile data            │
│ • Try restarting your router           │
│ • Check if other apps can connect      │
│                                         │
│ Error Code: ERR_NET_001                │
│                                         │
│ [Retry]  [External Player]             │
└────────────────────────────────────────┘
      │
      ▼
User understands problem and follows suggestion
      │
      ▼
User fixes WiFi → Retries → Success! ✅
```

---

## File Structure

```
lib/
├── main.dart (initialize logger)
├── utils/
│   ├── error_handler.dart ← ErrorCode, AppError, ErrorHandler
│   └── logger_service.dart ← LoggerService, LogLevel, logger instance
├── screens/
│   ├── player_screen.dart (uses AppError, logs events)
│   └── log_viewer_screen.dart ← View/export/clear logs
└── services/
    └── m3u_service.dart (uses ErrorHandler, logs operations)

Documentation/
├── ERROR_HANDLING_README.md (complete guide)
├── ERROR_HANDLING_QUICKSTART.md (quick start)
└── ERROR_HANDLING_COMPLETE.md (implementation summary)

test/
└── error_handling_examples_test.dart (usage examples)
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────┐
│                  ERROR HANDLING SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Exception occurs                                        │
│     ↓                                                        │
│  2. ErrorHandler.handle() maps to AppError                  │
│     ↓                                                        │
│  3. logger.error() writes to file                           │
│     ↓                                                        │
│  4. User sees friendly message + suggestions                │
│     ↓                                                        │
│  5. User can:                                               │
│     • Retry the operation                                   │
│     • Use external player                                   │
│     • View logs for debugging                               │
│     • Export logs for support                               │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  BENEFITS:                                                   │
│  ✅ Users understand what went wrong                        │
│  ✅ Users know how to fix it                                │
│  ✅ Developers get detailed logs                            │
│  ✅ Support team has error codes                            │
└─────────────────────────────────────────────────────────────┘
```

---

**See ERROR_HANDLING_README.md for complete documentation!**
