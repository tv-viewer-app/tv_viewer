# Android App Bugs & Feature Requests

## Completed in v1.5.0

### ✅ 1. Open in External App - FIXED
- **Status**: Completed
- **Description**: Added proper Android intent queries for VLC and MX Player, improved fallback handling with URL copy option

### ✅ 2. Add Cast Button - IMPLEMENTED
- **Status**: Completed
- **Description**: Added cast button in player with dialog explaining how to cast via external players

### ✅ 3. Show Resolution and Bitrate of Channel - IMPLEMENTED
- **Status**: Completed
- **Description**: Displays resolution (extracted from channel name or stream metadata) and bitrate in channel list and player

### ✅ 4. Consolidate Categories (Remove Semicolons) - FIXED
- **Status**: Completed
- **Description**: Added normalizeCategory() function that splits on semicolons and takes first meaningful category

### ✅ 5. Category Selector with Dropdown - IMPLEMENTED
- **Status**: Completed
- **Description**: Replaced horizontal filter chips with dropdown selector for better UX

### ✅ 6. Allow to Choose Country - IMPLEMENTED
- **Status**: Completed
- **Description**: Added country dropdown filter that extracts unique countries from channels

### ✅ 7. Allow to Choose Radio Stations - IMPLEMENTED
- **Status**: Completed
- **Description**: Added mediaType field (TV/Radio) with detection logic and filter dropdown

---

## Additional Fixes (from Code Review)

### ✅ Memory Leak Fix
- Fixed VideoPlayerController listener not being removed on dispose
- Fixed controller not being disposed on retry

### ✅ Race Condition Fix
- Fixed concurrent notifyListeners() calls in channel validation
- Now batches state updates to prevent UI inconsistencies

---

*Completed: 2026-01-28 | Version: 1.5.0*
