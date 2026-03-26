# Decision: Repository Source Management for Android App

**Date:** 2025-01-27  
**Author:** Kaylee (Frontend Dev)  
**Status:** Implemented in PR #63

## Context

Issue #61 identified that Android app users were stuck in an error loop when channel loading failed. The app had hardcoded M3U repository URLs with no UI to change sources.

## Decision

Implemented a repository management system for the Flutter Android app with:

1. **RepositoryService** — SharedPreferences-backed service for managing custom M3U sources
2. **SettingsScreen** — Material Design UI for adding/editing/removing repositories
3. **Enhanced Error State** — "Change Source" button to escape error loops

## Architecture Rationale

### Why Static Methods (Not Singleton)?
- Followed existing `FavoritesService` pattern in codebase
- SharedPreferences is inherently singleton (provided by Flutter)
- Simpler testing (no dependency injection needed)
- Flutter-idiomatic for this use case

### Why No Provider for Settings?
- Settings screen uses local state only
- No need to share state across widgets
- `RepositoryService` changes take effect on next channel fetch
- Keeps architecture simple

### Integration Strategy
- Modified `M3UService.fetchAllChannels()` to call `RepositoryService.loadRepositories()`
- On first launch, initializes with default repos (backward compatible)
- Users can customize sources without breaking existing behavior

## Future Enhancements (Phase 2)

From Mal's triage in `.squad/decisions.md`:
- Quick source switcher in app bar (dropdown/bottom sheet)
- "Try Alternative Source" option in error state
- Show last successful source + timestamp
- Import from URL (e.g., channels_config.json)
- QR code sharing of repository configs

## Feature Parity

This brings Android app to parity with desktop Python app, which has `channels_config.json` for user-configurable repositories.

## Testing Required

- [ ] Unit tests for RepositoryService CRUD operations
- [ ] Widget tests for SettingsScreen
- [ ] Integration test: Add source → Fetch channels → Verify load
- [ ] Manual test: Error state → Change source → Success

## Related Issues

- Fixes #61 (immediate UX blocker)
- Desktop already has this feature (feature parity achieved)
