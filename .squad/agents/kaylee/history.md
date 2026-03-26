# Kaylee — Frontend Dev History

## Learnings

### Issue #61: Flutter Repository Source Management (2025-01-27)

**Pattern:** Flutter service + UI separation
- Created `RepositoryService` as a stateless service class for data operations
- SharedPreferences pattern similar to `FavoritesService` for persistence
- Separated business logic (service) from UI (screen)

**Flutter Conventions Used:**
- `StatefulWidget` for settings screen with mutable state
- `TextEditingController` for text input management
- `showDialog` for modal confirmations
- `ScaffoldMessenger.of(context).showSnackBar` for user feedback
- Material Design widgets: `Card`, `ListTile`, `PopupMenuButton`

**UI State Management:**
- No Provider needed for settings screen (local state only)
- Settings changes propagate via `RepositoryService` static methods
- M3UService reads fresh config on each `fetchAllChannels()` call

**Error Recovery UX Pattern:**
- Added "Change Source" button alongside "Refresh" in error state
- Settings accessible via app bar menu (global access)
- Prevents error loop by giving users control over data sources

**Architecture Decision:**
- Used static methods in RepositoryService (like FavoritesService pattern)
- No singleton or dependency injection needed
- Simple, testable, Flutter-idiomatic approach

**Integration Points:**
- Modified `M3UService.fetchAllChannels()` to load from `RepositoryService`
- Updated `HomeScreen` to navigate to `SettingsScreen`
- Maintained backward compatibility (defaults on first launch)

**Key Insight:**
Flutter app had feature parity gap with desktop app - desktop had `channels_config.json` for custom repos, mobile had hardcoded sources. This fix brings feature parity and better UX for channel loading failures.

