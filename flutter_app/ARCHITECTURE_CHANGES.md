# Architecture Changes - Advanced Features

## Overview Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         TV Viewer App                            │
│                         Version 1.5.0                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │  UI Layer    │ │ State Layer  │ │Service Layer │
        └──────────────┘ └──────────────┘ └──────────────┘
```

---

## Component Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                            SCREENS                                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐      │
│  │  HomeScreen    │  │ DiagnosticsScr │  │  PlayerScreen  │      │
│  │   (Modified)   │  │    (NEW)       │  │   (Existing)   │      │
│  │                │  │                │  │                │      │
│  │ • Language     │  │ • Device Info  │  │ • Video Player │      │
│  │   Filter ✨    │  │ • Network Test │  │ • Controls     │      │
│  │ • Menu Options │  │ • URL Tester   │  │                │      │
│  │ • Rating Prompt│  │ • Export Report│  │                │      │
│  └────────────────┘  └────────────────┘  └────────────────┘      │
│         │                     │                   │                │
└─────────┼─────────────────────┼───────────────────┼────────────────┘
          │                     │                   │
          ▼                     ▼                   ▼
┌────────────────────────────────────────────────────────────────────┐
│                           PROVIDERS                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              ChannelProvider (Modified)                       │ │
│  │                                                               │ │
│  │  State:                        Methods:                       │ │
│  │  • _languages ✨               • setLanguage() ✨            │ │
│  │  • _selectedLanguage ✨        • validateChannels()          │ │
│  │  • _channels (immutable) ✨    • loadChannels()              │ │
│  │  • _filteredChannels           • applyFilters()              │ │
│  │  • _categories                 • setCategory()               │ │
│  │  • _countries                  • setCountry()                │ │
│  │                                                               │ │
│  │  Uses: Immutable Channel Model with copyWith() ✨            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────────────────┐
│                            MODELS                                   │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Channel Model (Immutable) ✨                     │ │
│  │                                                               │ │
│  │  final String name;                                          │ │
│  │  final String url;                                           │ │
│  │  final String? category;                                     │ │
│  │  final String? language; ✨                                  │ │
│  │  final String? country;                                      │ │
│  │  final bool isWorking; ← Now final! ✨                       │ │
│  │  final DateTime? lastChecked; ← Now final! ✨                │ │
│  │                                                               │ │
│  │  Channel copyWith({...}) ✨                                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────────────────┐
│                           SERVICES                                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────┐  ┌────────────────────┐                   │
│  │  M3UService        │  │ FeedbackService ✨ │                   │
│  │   (Existing)       │  │      (NEW)         │                   │
│  │                    │  │                    │                   │
│  │ • fetchChannels()  │  │ • shouldShowRating │                   │
│  │ • parseM3U()       │  │   Prompt()         │                   │
│  │ • checkStream()    │  │ • showRatingPrompt │                   │
│  │                    │  │ • showFeedbackDlg  │                   │
│  │                    │  │ • openAppStore()   │                   │
│  └────────────────────┘  └────────────────────┘                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL PACKAGES                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  • device_info_plus ✨    → Device information                    │
│  • connectivity_plus ✨   → Network monitoring                    │
│  • package_info_plus ✨   → App version                           │
│  • share_plus ✨          → Share functionality                   │
│  • shared_preferences      → Session tracking                      │
│  • url_launcher            → Open external URLs                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Language Filter Flow (BL-017)

```
User Action                Provider                    Model
    │                          │                          │
    │  Select Language         │                          │
    ├────────────────────────► │                          │
    │                          │                          │
    │                          │  setLanguage()           │
    │                          │                          │
    │                          │  _applyFilters()         │
    │                          │                          │
    │                          │  Filter channels         │
    │                          │  where language ==       │
    │                          │  selected or "All"       │
    │                          │                          │
    │                          │  notifyListeners()       │
    │                          │                          │
    │  Update UI               │                          │
    │◄──────────────────────── │                          │
    │                          │                          │
    │  Show filtered           │                          │
    │  channels                │                          │
```

### 2. Diagnostics Flow (BL-024)

```
User                DiagnosticsScreen         External Packages
 │                         │                          │
 │  Open Menu             │                          │
 │  → Diagnostics         │                          │
 ├───────────────────────►│                          │
 │                        │                          │
 │                        │  Load Device Info        │
 │                        ├─────────────────────────►│
 │                        │                          │
 │                        │  device_info_plus        │
 │                        │  package_info_plus       │
 │                        │                          │
 │                        │◄─────────────────────────┤
 │                        │  Return device data      │
 │                        │                          │
 │  Display Device Info   │                          │
 │◄───────────────────────┤                          │
 │                        │                          │
 │  Enter Stream URL      │                          │
 │  → Test Stream         │                          │
 ├───────────────────────►│                          │
 │                        │                          │
 │                        │  HTTP HEAD Request       │
 │                        │  (10s timeout)           │
 │                        │                          │
 │                        │  Response or Error       │
 │                        │                          │
 │  Show Results          │                          │
 │◄───────────────────────┤                          │
 │                        │                          │
 │  Export Report         │                          │
 ├───────────────────────►│                          │
 │                        │                          │
 │                        │  Generate Report Text    │
 │                        │                          │
 │                        │  share_plus              │
 │                        ├─────────────────────────►│
 │                        │                          │
 │  Share Dialog          │                          │
 │◄───────────────────────┴─────────────────────────┤
```

### 3. Immutable Model Flow (BL-031)

```
Provider                   Old Model              New Model (Immutable)
   │                          │                          │
   │  Validate Channel        │                          │
   │                          │                          │
   │  OLD WAY:                │                          │
   │  channel.isWorking=true  │                          │
   │  ❌ Mutates state        │                          │
   │                          │                          │
   │  NEW WAY:                │                          │
   │  newChannel =            │                          │
   │  channel.copyWith(       │                          │
   │    isWorking: true       │                          │
   │  )                       │                          │
   │                          │                          │
   │                          │  Create new instance     │
   │                          │  with updated values     │
   │                          │                          │
   │  Replace in list         │                          │
   │  channels[i] = newChannel│                          │
   │                          │                          │
   │  ✅ Immutable            │                          │
   │  ✅ Thread-safe          │                          │
   │  ✅ No mutations         │                          │
```

### 4. Feedback System Flow (BL-032)

```
App Launch              FeedbackService         SharedPreferences
    │                          │                          │
    │  initState()             │                          │
    ├─────────────────────────►│                          │
    │                          │                          │
    │                          │  shouldShowRatingPrompt  │
    │                          ├─────────────────────────►│
    │                          │                          │
    │                          │  Get session count       │
    │                          │◄─────────────────────────┤
    │                          │  Count = 5?              │
    │                          │                          │
    │  If count >= 5           │                          │
    │  Wait 2 seconds          │                          │
    │                          │                          │
    │  Show Rating Prompt      │                          │
    │◄─────────────────────────┤                          │
    │                          │                          │
    │  User clicks:            │                          │
    │  ┌────────────┐          │                          │
    │  │ Rate Now   ├─────────►│  openAppStore()          │
    │  └────────────┘          │  markAsRated()           │
    │                          ├─────────────────────────►│
    │                          │  Set has_rated = true    │
    │                          │                          │
    │  ┌────────────┐          │                          │
    │  │ Later      ├─────────►│  markPromptShown()       │
    │  └────────────┘          ├─────────────────────────►│
    │                          │  Set last_prompt_date    │
    │                          │                          │
    │  ┌────────────┐          │                          │
    │  │ No Thanks  ├─────────►│  markAsRated()           │
    │  └────────────┘          ├─────────────────────────►│
    │                          │  Set has_rated = true    │
    │                          │                          │
    │                          │                          │
    │  Menu → Send Feedback    │                          │
    ├─────────────────────────►│  showFeedbackDialog()    │
    │                          │                          │
    │  Feedback Form           │                          │
    │◄─────────────────────────┤                          │
    │                          │                          │
    │  User submits            │                          │
    ├─────────────────────────►│  Open email app          │
    │                          │  with pre-filled data    │
    │                          │                          │
    │  Email app opens         │                          │
    │◄─────────────────────────┤                          │
```

---

## State Management Changes

### Before (Mutable)
```dart
class Channel {
  bool isWorking;          // ❌ Mutable
  DateTime? lastChecked;   // ❌ Mutable
  
  // Direct mutation
  channel.isWorking = true;
}
```

### After (Immutable) ✨
```dart
class Channel {
  final bool isWorking;         // ✅ Immutable
  final DateTime? lastChecked;  // ✅ Immutable
  
  // Update via copyWith
  final updated = channel.copyWith(isWorking: true);
}
```

---

## Integration Points

```
┌──────────────────────────────────────────────────────────┐
│                      Main App                             │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  main.dart                                                │
│    └─► ChangeNotifierProvider(ChannelProvider)           │
│          └─► MaterialApp                                 │
│                └─► HomeScreen                            │
│                      │                                    │
│         ┌────────────┼────────────┬────────────┐         │
│         ▼            ▼            ▼            ▼         │
│                                                           │
│  Player Screen  Diagnostics  Feedback     About          │
│  (Existing)     (NEW) ✨    (NEW) ✨     (Modified)      │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## Menu Structure

```
Home Screen AppBar
    │
    ├─► [Scan Button]
    │     └─► Validates channels with immutable updates ✨
    │
    └─► [Menu Button ⋮]
          │
          ├─► Diagnostics ✨
          │     ├─ Device Info
          │     ├─ Network Status
          │     ├─ Stream Tester
          │     └─ Export Report
          │
          ├─► Send Feedback ✨
          │     ├─ Feedback Type
          │     ├─ Message Input
          │     └─ Submit (Email)
          │
          ├─► Rate App ✨
          │     └─ Opens Play Store
          │
          └─► About
                └─ App Info (v1.5.0)
```

---

## Filter UI Layout

```
┌─────────────────────────────────────────────────────┐
│              Home Screen Filters                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [🔍 Search Bar...]                                 │
│                                                      │
│  ┌───────┐ ┌─────────────┐ ┌─────────────┐        │
│  │ Type  │ │  Category   │ │   Country   │        │
│  │  TV ▼ │ │   News ▼    │ │    USA ▼    │        │
│  └───────┘ └─────────────┘ └─────────────┘        │
│                                                      │
│  ┌──────────────────────────────────────────┐      │
│  │ 🌐 Language: English ▼         (NEW) ✨  │      │
│  └──────────────────────────────────────────┘      │
│                                                      │
│  [❌ Clear Filters] (if any active)                │
│                                                      │
│  📊 25 channels | ❤️ 3 | ✅ 20 working             │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  📺 BBC News (English)                     │    │
│  │  📺 CNN International (English)            │    │
│  │  📺 France 24 (French)                     │    │
│  │  ...                                       │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Dependency Graph

```
home_screen.dart
    ├── channel_provider.dart
    │     ├── channel.dart (Immutable Model) ✨
    │     ├── m3u_service.dart
    │     └── shared_preferences
    │
    ├── diagnostics_screen.dart ✨
    │     ├── device_info_plus ✨
    │     ├── connectivity_plus ✨
    │     ├── package_info_plus ✨
    │     ├── share_plus ✨
    │     └── http
    │
    ├── feedback_service.dart ✨
    │     ├── shared_preferences
    │     └── url_launcher
    │
    └── player_screen.dart
          └── video_player
```

---

## Version History

```
v1.4.4  ─┐
         │  + BL-017: Language Filter
         │  + BL-024: Diagnostics Screen
         │  + BL-031: Immutable Model
         │  + BL-032: Feedback System
         ▼
v1.5.0  ─┐  ← Current Version ✨
         │
         ▼
        Future versions...
```

---

## Performance Impact

```
Feature              Impact         Notes
────────────────────────────────────────────────────
Language Filter      Minimal        Integrated into existing filter
Diagnostics Screen   None           Only loads when opened
Immutable Model      Improved       Better memory management
Feedback System      Minimal        Lightweight SharedPreferences
Overall              ✅ Positive    Cleaner architecture
```

---

## Testing Flow

```
1. Install Dependencies
   flutter pub get
      │
      ▼
2. Analyze Code
   flutter analyze
      │
      ▼
3. Run App
   flutter run
      │
      ▼
4. Test Features
   ├─► Language Filter
   ├─► Diagnostics
   ├─► Immutable Model
   └─► Feedback System
      │
      ▼
5. Build Release
   flutter build apk --release
      │
      ▼
6. Deploy 🚀
```

---

✨ = New or Modified Component

This architecture maintains clean separation of concerns while adding powerful new features!
