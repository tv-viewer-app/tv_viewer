# Next Version Plan: v2.4.0

**Author:** Mal (Lead)  
**Date:** 2026-03-26  
**Current Version:** Desktop 1.9.0, Flutter 2.3.3  
**Proposed Version:** 2.4.0 (aligned across both platforms)

## Executive Summary

Based on comprehensive analysis of the codebase, GitHub issues, and recent commit history, the project is in good health but has critical Android UX gaps and security issues that need resolution. The desktop Python app (v1.9.0) has modern UI components designed but not integrated. The Flutter Android app (v2.3.3) is ahead in versioning but suffers from critical UX bugs affecting usability.

**Version Rationale:** v2.4.0 is appropriate because we're addressing multiple high-priority bugs, implementing substantial UX improvements, and closing security issues. This is a minor version bump with significant user-facing improvements.

## Current State Analysis

### Desktop (Python) - v1.9.0
- ✅ **Strengths:** Stable, modern UI components designed (nav_rail, channel_card, channel_grid, top_bar), CI/CD pipeline mature
- ❌ **Weaknesses:** Modern UI components not integrated into MainWindow, still using legacy list-based UI
- 📊 **Code Quality:** 7,265 lines of Python code, 50 pytest tests passing, zero TODOs/FIXMEs in core/ui
- 🔒 **Security:** 6 open security issues (#49-#54), daily CVE scans running

### Flutter (Android) - v2.3.3
- ✅ **Strengths:** Feature-rich (PiP, wake lock, favorites, diagnostics, EPG), good architecture with DI
- ❌ **Weaknesses:** 10 critical UX bugs open (#39-#48), no repository selector (#61)
- 📊 **Code Quality:** 46 Dart files, TODOs in channel_provider.dart and feedback_service.dart
- 🔒 **Security:** Hardcoded credentials moved to secrets (good), cleartext traffic needs restriction (#54)

### Open Issues Summary
- **P0-Critical:** 3 issues (#35 segfault, #39 PiP crashes, #46 Israeli channels broken)
- **P1-High:** 6 issues (#40 list mutation, #41 offline handling, #43 radio channels, #44 favorites filter, #45 working channels filter, #50 VLC URL validation)
- **P2-Medium:** 9 issues (security, UX improvements, repository selector)
- **CVE Scan Issues:** 5 automated security issues (#56-#57-#60-#62) - ongoing daily scans

## Work Items (Priority Order)

### P0 — Must Have (Release Blockers)

#### Android Critical Fixes

**[ITEM-01]** Fix PiP null safety crashes (#39)
- **Description:** PiP service has null safety violations causing app crashes on Android 8.0+
- **Technical Approach:** Add null checks in pip_service.dart, add defensive guards for controller lifecycle
- **Files:** `flutter_app/lib/services/pip_service.dart`, `flutter_app/lib/screens/player_screen.dart`
- **Testing:** Test PiP enter/exit on Android 8.0, 9.0, 12+ devices
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 2 hours

**[ITEM-02]** Fix Israeli channels not working (#46)
- **Description:** Channel 10 Economic, i24News, KAN 11, KAN Kids fail to play on Android
- **Technical Approach:** Debug stream URLs, check URL validation logic, test with VLC Android
- **Root Cause:** Likely URL validation too strict or User-Agent issues
- **Files:** `flutter_app/lib/services/m3u_service.dart`, `flutter_app/lib/screens/player_screen.dart`
- **Testing:** Manual test with each channel, verify playback starts
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 3 hours

**[ITEM-03]** Add repository selector for Android (#61)
- **Description:** No way to change channel sources when default repositories fail or are blocked
- **Technical Approach:** 
  - Create `RepositoryService` to manage sources (SharedPreferences storage)
  - Create Settings screen with repository list editor
  - Update M3UService to use RepositoryService
  - Add "Change Source" button in error screen
- **Files:** 
  - `flutter_app/lib/services/repository_service.dart` (new)
  - `flutter_app/lib/screens/settings_screen.dart` (new)
  - `flutter_app/lib/services/m3u_service.dart` (update)
  - `flutter_app/lib/screens/home_screen.dart` (add menu item)
- **Testing:** Add source, remove source, load channels from custom source, persist across restarts
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 6 hours

#### Desktop Critical Fixes

**[ITEM-04]** Fix segmentation fault during scan (#35)
- **Description:** Segfault when scanning channels on Linux - background thread modifying tkinter UI
- **Root Cause:** Already fixed in v1.8.1 (root.after() pattern), issue needs verification closure
- **Action:** Verify fix works, add regression test, close issue
- **Files:** `tests/test_core.py` (add threading safety test)
- **Assigned to:** Zoe (Testing)
- **Estimate:** 1 hour

### P1 — Should Have (High Value)

#### Android UX Improvements

**[ITEM-05]** Add favorites filter (#44)
- **Description:** No way to show only favorite channels - users can favorite but can't filter by them
- **Technical Approach:** Add "Favorites" option to filter dropdowns, modify ChannelProvider.filteredChannels
- **Files:** `flutter_app/lib/screens/home_screen.dart`, `flutter_app/lib/providers/channel_provider.dart`
- **Testing:** Star channels, select favorites filter, verify only favorites shown
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 2 hours

**[ITEM-06]** Add working channels filter (#45)
- **Description:** No way to filter out offline/broken channels - users see many non-working channels
- **Technical Approach:** Add channel status tracking, add "Working Only" filter toggle in UI
- **Files:** `flutter_app/lib/providers/channel_provider.dart`, `flutter_app/lib/screens/home_screen.dart`
- **Testing:** Validate channels, toggle filter, verify only working channels shown
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 3 hours

**[ITEM-07]** Add radio channels support (#43)
- **Description:** Radio channels like Glglz not shown in Android app - filter excludes them
- **Root Cause:** Media type filter defaulting to TV only, radio channels filtered out
- **Technical Approach:** Fix default filter to include radio, add media type badge in UI
- **Files:** `flutter_app/lib/providers/channel_provider.dart`, `flutter_app/lib/widgets/channel_tile.dart`
- **Testing:** Load channels, verify radio stations appear, test playback
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 2 hours

**[ITEM-08]** Fix offline/connectivity handling (#41)
- **Description:** No user feedback when device is offline during channel loading
- **Technical Approach:** Check connectivity before fetch, show offline indicator, queue retry when online
- **Files:** `flutter_app/lib/providers/channel_provider.dart`, `flutter_app/lib/screens/home_screen.dart`
- **Testing:** Turn off WiFi, launch app, verify offline message, turn on WiFi, verify auto-retry
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 3 hours

**[ITEM-09]** Fix channel provider list mutation (#40)
- **Description:** Direct list mutation breaks UI state notifications, causes flicker/inconsistency
- **Technical Approach:** Use copy-on-write for channel list updates, batch notifyListeners calls
- **Files:** `flutter_app/lib/providers/channel_provider.dart`
- **Testing:** Load channels, filter, search - verify no UI flicker or state loss
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 2 hours

#### Desktop UX Improvements

**[ITEM-10]** Integrate modern UI components into MainWindow
- **Description:** UX components (nav_rail, channel_card, channel_grid, top_bar, status_bar) designed but not integrated
- **Technical Approach:** 
  - Replace MainWindow sidebar with NavRail
  - Replace channel list with ChannelGrid
  - Add TopBar with search/filters
  - Add StatusBar at bottom
  - Migrate favorites.py integration
- **Files:** 
  - `ui/main_window.py` (major refactor)
  - `ui/nav_rail.py`, `ui/channel_card.py`, `ui/channel_grid.py`, `ui/top_bar.py`, `ui/status_bar.py` (integrate)
- **Testing:** Manual UI test - search, filter, play channels, verify all features work
- **Assigned to:** Wash (Backend/Core) + Mal (Architecture review)
- **Estimate:** 8 hours

#### Security Fixes

**[ITEM-11]** Validate stream URL before VLC subprocess (#50)
- **Description:** No URL scheme validation before launching external VLC with user-supplied URLs
- **Security Impact:** Command injection risk if malicious URLs provided
- **Technical Approach:** Add URL scheme whitelist (http/https/rtmp/rtsp), sanitize before subprocess
- **Files:** `ui/player_window.py`, `utils/helpers.py`
- **Testing:** Try file://, javascript:, other schemes - verify blocked
- **Assigned to:** Wash (Backend/Core)
- **Estimate:** 2 hours

**[ITEM-12]** Restrict Android cleartext traffic to streaming domains (#54)
- **Description:** AndroidManifest allows all cleartext HTTP traffic - overly permissive
- **Technical Approach:** Add network_security_config.xml with domain whitelist for IPTV servers
- **Files:** 
  - `flutter_app/android/app/src/main/res/xml/network_security_config.xml` (new)
  - `flutter_app/android/app/src/main/AndroidManifest.xml` (reference config)
- **Testing:** Verify IPTV streams still work, verify non-streaming HTTP blocked
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 2 hours

**[ITEM-13]** Move Supabase credentials to env vars (#51)
- **Description:** Some Supabase references may remain in code after recent migration
- **Action:** Audit codebase, verify all credentials from environment, document .env.example
- **Files:** `flutter_app/lib/services/shared_db_service.dart`, `.env.example` (create)
- **Assigned to:** Wash (Backend/Core)
- **Estimate:** 1 hour

### P2 — Nice to Have (Polish)

**[ITEM-14]** Add FMStream.org radio streams (#32)
- **Description:** Add FMStream.org as additional radio station source
- **Technical Approach:** Add repository URL to default sources, test M3U parsing compatibility
- **Files:** `config.py`, `channels_config.json`, `flutter_app/lib/services/repository_service.dart`
- **Testing:** Fetch FMStream.org playlist, verify radio stations appear and play
- **Assigned to:** Wash (Backend/Core)
- **Estimate:** 1 hour

**[ITEM-15]** Resolve TODOs in Flutter code
- **Description:** TODOs exist in channel_provider.dart and feedback_service.dart
- **Action:** Review TODOs, implement or remove, improve code comments
- **Files:** `flutter_app/lib/providers/channel_provider.dart`, `flutter_app/lib/services/feedback_service.dart`
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 2 hours

**[ITEM-16]** Populate language filter dropdown (#47)
- **Description:** Language dropdown only shows "All" - cannot filter by language
- **Root Cause:** Language extraction not working from channel metadata
- **Technical Approach:** Parse language field from M3U, populate dropdown with unique values
- **Files:** `flutter_app/lib/providers/channel_provider.dart`, `flutter_app/lib/services/m3u_service.dart`
- **Testing:** Load channels, verify languages populated, filter by language
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 2 hours

**[ITEM-17]** Fix iconbitmap error (#37)
- **Description:** Tkinter iconbitmap() error on Linux due to version incompatibility
- **Technical Approach:** Try both Tk 8.6+ and legacy syntax with nested try-except
- **Files:** `icon.py`
- **Testing:** Test on Ubuntu 22.04/24.04 with different Tk versions
- **Assigned to:** Wash (Backend/Core)
- **Estimate:** 1 hour

**[ITEM-18]** Add content size limit to Flutter M3U fetcher (#55)
- **Description:** No size limit on M3U downloads - DoS risk from huge playlists
- **Technical Approach:** Add max content length check (10MB), reject oversized responses
- **Files:** `flutter_app/lib/services/m3u_service.dart`
- **Testing:** Mock huge response, verify rejection with error message
- **Assigned to:** Kaylee (Flutter/UI)
- **Estimate:** 1 hour

**[ITEM-19]** Enhanced test coverage
- **Description:** Add tests for critical paths: channel loading, filtering, player lifecycle
- **Technical Approach:** 
  - Add widget tests for home_screen, player_screen
  - Add unit tests for channel_provider filter logic
  - Add integration test: load → filter → play workflow
- **Files:** `flutter_app/test/` (new tests)
- **Assigned to:** Zoe (Testing)
- **Estimate:** 4 hours

**[ITEM-20]** Update documentation for v2.4.0
- **Description:** Update README, CHANGELOG, USER_GUIDE with new features
- **Technical Approach:** 
  - Document repository selector feature
  - Document new filters (favorites, working channels, radio)
  - Update screenshots
  - Add troubleshooting for new features
- **Files:** `README.md`, `CHANGELOG.md`, `docs/USER_GUIDE.md`
- **Assigned to:** Mal (Lead)
- **Estimate:** 2 hours

## Version Bump Locations

**Desktop (Python):**
- `config.py`: `APP_VERSION = "2.4.0"`

**Flutter (Android):**
- `flutter_app/pubspec.yaml`: `version: 2.4.0+24`
- `flutter_app/lib/constants.dart`: `appVersion = '2.4.0'`
- `flutter_app/android/local.properties`: `flutter.versionName=2.4.0`, `flutter.versionCode=24`

**Note:** User-Agent strings automatically updated via `appUserAgent` constant in `constants.dart` (good architecture).

## Release Checklist

### Pre-Development
- [ ] Create GitHub milestone for v2.4.0
- [ ] Create GitHub issues for all P0 and P1 items
- [ ] Assign issues to agents (Wash, Kaylee, Zoe, Mal)

### Development Phase
- [ ] All P0 items complete and tested
- [ ] All P1 items complete and tested
- [ ] P2 items implemented (best effort)
- [ ] Version bumped in all locations
- [ ] CHANGELOG.md updated with all changes

### Testing Phase
- [ ] Desktop: `python3 tests/validate_build.py` passes
- [ ] Desktop: All 50 pytest tests pass
- [ ] Android: Widget tests pass
- [ ] Android: Manual test on Android 8.0, 9.0, 12+ devices
- [ ] Test Israeli channels play on Android
- [ ] Test repository selector with custom sources
- [ ] Test offline handling

### Build Phase
- [ ] Windows executable builds successfully
- [ ] Android APK builds successfully (CI workflow)
- [ ] No security warnings from Bandit
- [ ] No HIGH severity CVEs

### Release Phase
- [ ] Create git tag v2.4.0
- [ ] Release gate workflow passes (5 gates)
- [ ] GitHub Release created with binaries
- [ ] Release notes published
- [ ] Close all P0/P1 issues

### Post-Release
- [ ] Monitor for crash reports
- [ ] Triage new issues
- [ ] Plan v2.5.0 based on feedback

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| MainWindow refactor breaks desktop UX | Medium | High | Thorough manual testing, keep old UI as fallback branch |
| Repository selector complexity underestimated | Low | Medium | MVP first (add/remove sources), polish later |
| Israeli channel fix requires deep debugging | Medium | High | Test with VLC desktop first, isolate URL/codec issues |
| Security fixes break backward compatibility | Low | Medium | Test with existing config files, add migration logic |
| Testing timeline slips | Medium | Medium | Parallelize agent work, focus on P0 first |

## Success Metrics

**User Experience:**
- ✅ Android users can change sources when default fails
- ✅ Android users can filter favorites and working channels
- ✅ Israeli channels play successfully on Android
- ✅ Desktop users have modern card-based UI
- ✅ Zero P0 bugs remain open

**Quality:**
- ✅ All CI tests pass (Ubuntu + Windows)
- ✅ Security gate passes with no HIGH findings
- ✅ Build validation passes
- ✅ Manual testing checklist 100% complete

**Velocity:**
- 🎯 P0 complete in 2 days (15 hours total)
- 🎯 P1 complete in 5 days (29 hours total)
- 🎯 P2 complete best effort (13 hours total)
- 🎯 Total release cycle: 10 days from start to GitHub Release

## Agent Workload Distribution

| Agent | P0 Items | P1 Items | P2 Items | Total Hours | Focus Area |
|-------|----------|----------|----------|-------------|------------|
| **Kaylee** (Flutter) | 3 | 5 | 4 | 32 hours | Android bugs, UX, filters |
| **Wash** (Backend) | 0 | 1 + partial #10 | 3 | 15 hours | Security, desktop core, integrations |
| **Zoe** (Testing) | 1 | 0 | 1 | 5 hours | Regression tests, test coverage |
| **Mal** (Lead) | 0 | partial #10 | 1 | 10 hours | Architecture review, documentation |

## Dependencies & Sequencing

**Critical Path:**
1. ITEM-01 (PiP crashes) → Unblocks Android testing
2. ITEM-03 (Repository selector) → Foundational for issue #61
3. ITEM-02 (Israeli channels) → High user impact
4. ITEM-10 (Desktop UI integration) → Longest task, start early

**Parallel Tracks:**
- Kaylee: ITEM-01 → ITEM-02 → ITEM-03 → ITEM-05/06/07/08/09 → ITEM-12 → ITEM-15/16/18
- Wash: ITEM-11 → ITEM-13 → assist ITEM-10 → ITEM-14 → ITEM-17
- Zoe: ITEM-04 → ITEM-19 (after features stabilize)
- Mal: Review ITEM-10 → ITEM-20 documentation

## Notes

**Why v2.4.0 and not v3.0.0?**
- No breaking API changes
- No major architecture rewrite
- Fixes and improvements within current design
- Desktop UI refresh is evolutionary, not revolutionary

**Why align versions?**
- Simplifies communication (one version for TV Viewer)
- Easier for users to understand (not "1.9.0 vs 2.3.3")
- Desktop was behind (1.9.0), Flutter ahead (2.3.3)
- 2.4.0 is next logical minor version

**CVE Scanner Issues (#56-62):**
- Not included in work items (automated daily process)
- Dependency updates handled separately from feature work
- Monitor for HIGH severity, address in hotfixes if needed

**Deferred to v2.5.0:**
- Shared online database (#31) - requires backend infrastructure
- Feedback/rating system (#23) - low priority nice-to-have
- Player screen race conditions (#42) - needs deeper investigation
- Non-consolidated channels (#58) - needs reproduction case

---

**Approval Required:** Ariel (Product Owner)  
**Next Step:** Create GitHub issues and milestone, assign to agents, begin P0 work
