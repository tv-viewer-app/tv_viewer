# Next Version Plan: v2.4.0

**Prepared by:** Mal (Project Lead)  
**Date:** 2026-03-26  
**Current Version:** 2.3.3  
**Target:** v2.4.0  

---

## Current State Summary

### Version Status
- **Desktop (Python):** 2.3.3 (config.py)
- **Android (Flutter):** 2.3.3+26 (pubspec.yaml, local.properties)
- **Channels Database:** 17,948 total channels (channels.json)
- **Last Release:** v2.3.2 (2026-03-05)

### Infrastructure
- **Database:** Supabase — fully operational
  - `analytics_events` table (anonymous usage tracking)
  - `channel_status` table (crowd-sourced health sharing)
  - Embedded credentials in config.py (anon key, RLS-protected)
- **CI/CD Status:** 
  - 6 workflows active (CI, Build, Release, CVE Scanner, Supabase Keep-Alive, Copilot)
  - CVE Scanner failing (last 2 runs) — dependency vulnerabilities detected
  - CI disabled to save Actions storage (0.5GB limit reached)
- **Crash Reporting:** GitHub Issues (via utils/crash_reporter.py) + Supabase analytics

### Platform Comparison
| Feature | Windows (Python) | Android (Flutter) | Gap |
|---------|-----------------|-------------------|-----|
| UI Framework | CustomTkinter | Material 3 | ✅ Native |
| Video Player | VLC (python-vlc) | video_player | ✅ Different tech |
| Channel Count | 17,948 | Same (via Supabase) | ✅ Synced |
| Map View | tkintermapview | flutter_map | ✅ Both |
| Favorites | ✅ | ✅ | ✅ |
| Source Selector | ✅ | ✅ | ✅ |
| Adult Content Toggle | ✅ (Settings dialog) | ✅ (Help screen) | ✅ |
| Language Filter | ❌ | ✅ (BUG #47 — only shows "All") | 🔴 Android broken |
| Radio Channels | ✅ | ❌ (BUG #43 — not shown) | 🔴 Android missing |
| EPG/Schedule | ✅ | ✅ (epg_service.dart) | ✅ |
| PiP Support | N/A | ✅ (pip_service.dart) | ✅ Android-only |
| Diagnostics | Basic | ✅ (diagnostics_screen.dart) | 🟡 Windows basic |
| Telemetry | ✅ (utils/telemetry.py) | ✅ (analytics_service.dart) | ✅ |
| Crashlytics | ✅ (crash_reporter.py) | ✅ (crashlytics_service.dart) | ✅ |

### Key Findings from Audit

#### 1. **Critical Bugs (Open Issues)**
- **#61 (P2)** — Can't change sources when "Channel error" screen is displayed (Android UX issue)
- **#47 (P2)** — Language dropdown only shows "All" — cannot filter by language (Android)
- **#46 (P0)** — Israeli channels not working (KAN 11, i24News) — needs URL refresh
- **#45 (P1)** — No way to filter and show only working channels (Android) — filter UI missing
- **#44 (P1)** — No way to filter and show only favorite channels (Android) — favorites filter broken
- **#43 (P1)** — Radio channels not shown in Android app (e.g., Glglz, 100FM subs)

#### 2. **Security Issues (Open)**
- **CVE Scanner failing** — Dependency vulnerabilities in requirements.txt (Python) or pubspec.yaml (Flutter)
- **#52 (P1)** — PrivateBin upload sends unencrypted data (disabled in v2.1.2, but code still present)
- **#50 (P1)** — Validate stream URL before subprocess launch (VLC) — SSRF protection may have gaps
- **#51 (P2)** — Move Supabase credentials to environment variables (currently hardcoded in config.py)
- **#53 (P2)** — Use explicit editor instead of os.startfile for config (SEC-005)
- **#54 (P2)** — Restrict Android cleartext traffic to streaming domains only (SEC-007)
- **#55 (P2)** — Add content size limit to Flutter M3U fetcher (SEC-010)

#### 3. **Code Quality Issues**
- **TODOs/FIXMEs found:**
  - `scripts/fmstream_integration_example.py` — integration example code, not production
  - `flutter_app/lib/providers/channel_provider.dart` — TODOs in state management
  - `flutter_app/lib/services/feedback_service.dart` — incomplete feedback submission logic
  - `flutter_app/test/repositories/*.dart` — test TODOs
  
- **Test Coverage:**
  - **Python:** 4 test files (test_core.py, test_fmstream.py, test_channel_urls.py, validate_build.py)
  - **Flutter:** Minimal tests (models, providers, repositories dirs exist, but sparse)
  - **No integration tests** for critical flows (channel load → play → failover)

#### 4. **Channel Database Status**
- **17,948 channels** in channels.json (was 13,353 in v2.3.0 after consolidation)
- **Likely many dead channels** — no full scan since v1.9.0 channel cleanup
- **Consolidation working** — v2.3.3 fixed country prefix stripping and cross-country merging
- **Multi-source channels** — proper failover with health-based URL ordering
- **Supabase health cache** — 10,048 working results fetched in ~5s on startup (56% scan reduction)

#### 5. **CI/CD Storage Exhausted**
- **0.5GB Actions storage limit reached** — CI workflow disabled to prevent auto-runs
- **CVE Scanner creating daily issues** — automated security monitoring active but failing
- **Release workflow** — functional, created 5 releases in March 2026
- **Android build workflow** — Flutter APK builds via GitHub Actions, pushes to dist/android/

---

## Work Items (Priority Order)

### 🔴 P0 — MUST Ship Before v2.4.0

#### P0-1: Fix Israeli channels (Issue #46) 
**Owner:** `@backend-developer`  
**Files:** `channels_config.json`, `flutter_app/lib/services/m3u_service.dart`  
**Task:** Re-verify KAN 11, i24News, KAN Kids stream URLs. Update CDN endpoints if changed. Test with VLC directly.  
**Acceptance:** All Israeli channels play on both Windows and Android without errors.

#### P0-2: Fix CVE Scanner failures (Security)
**Owner:** `@security-reviewer`  
**Files:** `requirements.txt`, `flutter_app/pubspec.yaml`, `.github/workflows/cve-scanner.yml`  
**Task:** 
1. Run `pip-audit` locally to identify vulnerable Python packages
2. Run `flutter pub outdated --mode=security` for Dart packages
3. Update dependencies to patched versions
4. Re-run CVE Scanner workflow to confirm green
**Acceptance:** CVE Scanner workflow passes, no HIGH severity vulnerabilities.

#### P0-3: Re-enable CI workflow (GitHub Actions storage)
**Owner:** `@github-operations`  
**Files:** `.github/workflows/ci.yml`, GitHub repo settings  
**Task:**
1. Review Actions storage usage: `gh api /repos/tv-viewer-app/tv_viewer/actions/cache/usage`
2. Clean up old workflow artifacts: `gh run list --limit 100 --json databaseId -q '.[].databaseId' | xargs -I {} gh api repos/tv-viewer-app/tv_viewer/actions/runs/{} -X DELETE`
3. Re-enable CI workflow (remove `workflow_dispatch` only trigger, restore push/PR triggers)
4. Add cache size monitoring to prevent future exhaustion
**Acceptance:** CI runs on push/PR without manual dispatch. Storage usage <400MB.

---

### 🟡 P1 — SHOULD Ship (High Value)

#### P1-1: Fix Android radio channel display (Issue #43)
**Owner:** `@android-expert`  
**Files:** `flutter_app/lib/providers/channel_provider.dart`, `flutter_app/lib/services/m3u_service.dart`  
**Task:** Debug why radio channels (media_type: "Radio") are not appearing in Android channel list. Check:
- M3U parsing for `tvg-type="radio"` or category="Radio"
- Channel provider filtering logic
- Default media type filter (may be excluding Radio)
**Acceptance:** Glglz, 100FM sub-channels visible in Android app under Radio category.

#### P1-2: Fix Android favorites filter (Issue #44)
**Owner:** `@android-expert`  
**Files:** `flutter_app/lib/screens/home_screen.dart`, `flutter_app/lib/providers/channel_provider.dart`  
**Task:** Wire up "Favorites only" filter chip to actually filter channels by `isFavorite` flag. Currently UI exists but doesn't apply filter.  
**Acceptance:** Tapping "Favorites only" chip shows only starred channels.

#### P1-3: Fix Android working channels filter (Issue #45)
**Owner:** `@android-expert`  
**Files:** `flutter_app/lib/screens/home_screen.dart`, `flutter_app/lib/providers/channel_provider.dart`  
**Task:** Add status filter dropdown (Working/Failed/Unchecked) to Android home screen. Filter channels by `is_working` and `scan_status` fields.  
**Acceptance:** User can select "Working only" and see only validated working channels.

#### P1-4: Channel scan health refresh
**Owner:** `@backend-developer`  
**Files:** `scripts/populate_supabase.py`, `channels.json`  
**Task:**
1. Run `scripts/populate_supabase.py --clean` to refresh channel database from scratch
2. Perform full health check scan on all 17,948 channels (will take ~30-60 minutes)
3. Upload results to Supabase `channel_status` table
4. Commit cleaned `channels.json` (expect reduction to ~12-14k working channels)
**Acceptance:** `channels.json` contains only validated working channels with fresh health data.

#### P1-5: Validate VLC URL security (Issue #50)
**Owner:** `@security-reviewer`  
**Files:** `ui/player_window.py`, `core/stream_checker.py`, `utils/helpers.py`  
**Task:** 
1. Review all URL validation before VLC subprocess launch
2. Ensure `ipaddress` module SSRF checks are applied to ALL stream URLs (not just scan phase)
3. Add URL scheme whitelist (http, https, rtmp, rtsp ONLY — no file://, ftp://)
4. Add unit tests for malicious URL rejection
**Acceptance:** Malicious URLs (file://, ftp://, private IPs) rejected before VLC launch.

---

### 🟢 P2 — NICE TO Have (Quality of Life)

#### P2-1: Fix Android language filter (Issue #47)
**Owner:** `@android-expert`  
**Files:** `flutter_app/lib/screens/home_screen.dart`, `flutter_app/lib/providers/channel_provider.dart`  
**Task:** Debug language dropdown only showing "All". Likely broken during v2.2.0 consolidation. Check:
- Channel model `language` field population
- Language list generation from loaded channels
- Dropdown initialization logic
**Acceptance:** Language dropdown shows Hebrew, English, Arabic, etc. Filter works correctly.

#### P2-2: Fix source selector on error screen (Issue #61)
**Owner:** `@android-expert`  
**Files:** `flutter_app/lib/screens/player_screen.dart`  
**Task:** When channel error screen appears, ensure source selector dropdown remains enabled. Currently all sources are disabled after auto-failover exhausts them.  
**Acceptance:** User can manually select alternative source even after all auto-failovers fail.

#### P2-3: Migrate Supabase credentials to env vars (Issue #51)
**Owner:** `@security-reviewer`  
**Files:** `config.py`, `flutter_app/lib/services/analytics_service.dart`, `flutter_app/lib/services/shared_db_service.dart`, `README.md`  
**Task:**
1. Change config.py to read from env vars ONLY (no hardcoded fallback)
2. Update Flutter to use `--dart-define` for build-time injection
3. Document in README how to set SUPABASE_URL and SUPABASE_ANON_KEY
4. Update GitHub Actions workflows to use repository secrets
**Acceptance:** No Supabase credentials in source code. App fails gracefully if env vars missing.

#### P2-4: Remove dead PrivateBin code (Issue #52)
**Owner:** `@backend-developer`  
**Files:** All files with "privatebin" references (grep search)  
**Task:** 
1. Search codebase for all PrivateBin references
2. Delete dead code (was disabled in v2.1.2)
3. Remove imports, config entries, UI buttons
**Acceptance:** Zero references to "privatebin" in codebase.

#### P2-5: Improve Windows diagnostics screen
**Owner:** `@frontend-developer`  
**Files:** New file `ui/diagnostics_window.py`  
**Task:** Create diagnostics dialog matching Android's diagnostics_screen.dart:
- App version, platform, Python version
- VLC version, available codecs
- Network connectivity status
- Channel count (total, working, cached)
- Supabase connection status
- Last scan timestamp
**Acceptance:** Help → Diagnostics opens window with system info like Android.

#### P2-6: Add integration tests
**Owner:** `@qa-automation`  
**Files:** New `tests/integration/` directory  
**Task:** Create end-to-end tests for critical flows:
1. App startup → channel load → display
2. Select channel → play → source failover → success
3. Favorite channel → restart app → favorites persist
4. Offline mode → cached channels load → network error handling
**Tools:** pytest + pytest-asyncio (Python), flutter_test (Dart)  
**Acceptance:** 4 integration tests passing in CI.

#### P2-7: Add explicit editor for config (Issue #53)
**Owner:** `@frontend-developer`  
**Files:** `ui/main_window.py` (Settings dialog)  
**Task:** Replace `os.startfile(channels_config.json)` with platform-specific editors:
- Windows: `subprocess.run(['notepad.exe', path])`
- macOS: `subprocess.run(['open', '-t', path])`
- Linux: `subprocess.run(['xdg-open', path])` or `gedit`
**Acceptance:** Config file opens in safe text editor, not untrusted default handler.

---

### 🔵 P3 — Future Backlog (Not v2.4.0)

- **Issue #23 (P3)** — Add feedback/rating system (low priority, nice to have)
- **Issue #20 (P3)** — Add channel EPG/schedule info (already exists in epg_service.dart, needs UI wiring)
- **Issue #19 (P3)** — Add animated LIVE badge (cosmetic)
- **Issue #21 (P3)** — Automated release notes generation (CI/CD improvement)
- **Issue #24 (P3)** — Add Firebase Crashlytics (already have Supabase crash reporting)
- **Issue #25 (P3)** — Add Firebase Analytics (already have Supabase analytics)
- **SEC-007 (P2)** — Restrict Android cleartext traffic (requires network_security_config.xml updates)
- **SEC-010 (P2)** — Add content size limit to Flutter M3U fetcher (security hardening)

---

## Channel Database Status

### Current State (v2.3.3)
- **Total channels:** 17,948 (channels.json)
- **Structure:** Dict with keys: `channels` (list), `version` (str), `last_updated` (timestamp)
- **Consolidation:** Working as of v2.3.3 (country prefix stripping, cross-country merging)
- **Multi-source:** Channels with multiple URLs have health-based ordering
- **Supabase health cache:** 10,048 working results fetched on startup (56% scan skip rate)

### Recommended Action: Full Channel Refresh
**Reason:** 17,948 is suspiciously high (was 13,353 after v2.3.0 consolidation). Likely contains many dead streams.

**Steps:**
1. Run `python scripts/populate_supabase.py --clean` (deletes all channels from Supabase, re-fetches from M3U repos)
2. Perform full health check scan (30-60 min for 17k channels with MAX_CONCURRENT_CHECKS=30)
3. Upload validated results to Supabase
4. Download cleaned channel list to `channels.json`
5. Commit updated channels.json with ~12-14k working channels

**Expected outcome:** Reduction to ~12-14k working channels (based on historical scan results showing ~60-70% working rate)

---

## Version Bump Locations

All files requiring version updates for v2.4.0:

1. **config.py** (line 24)
   ```python
   APP_VERSION = "2.4.0"
   ```

2. **flutter_app/pubspec.yaml** (line 4)
   ```yaml
   version: 2.4.0+27
   ```
   Note: +27 is build number (increment from +26)

3. **flutter_app/android/local.properties** (lines 4-5)
   ```properties
   flutter.versionName=2.4.0
   flutter.versionCode=27
   ```

4. **CHANGELOG.md** (line 8)
   Add new section:
   ```markdown
   ## [2.4.0] - 2026-03-XX
   
   ### Added
   - ...
   
   ### Fixed
   - ...
   
   ### Changed
   - ...
   ```

5. **README.md** (if version mentioned in badges or installation section)

---

## Release Checklist (v2.4.0)

### Pre-Release
- [ ] All P0 issues closed and verified
- [ ] All P1 issues closed OR explicitly deferred to v2.4.1
- [ ] Version bumped in all 4 locations (config.py, pubspec.yaml, local.properties, CHANGELOG.md)
- [ ] CHANGELOG.md updated with all changes since v2.3.3
- [ ] Full test suite passing: `python -m pytest tests/ -v`
- [ ] Flutter analyze clean: `cd flutter_app && flutter analyze`
- [ ] CVE Scanner workflow green (no HIGH vulnerabilities)
- [ ] Build validation: `python tests/validate_build.py` (passes all 5 gates)

### Build
- [ ] Desktop build: `python build.py --onefile` (creates dist/TV_Viewer.exe)
- [ ] Test Windows executable on clean VM (no Python installed)
- [ ] Android APK: `cd android && buildozer android debug` OR trigger GitHub Actions build workflow
- [ ] Test Android APK on real device (not emulator)

### Release
- [ ] Create Git tag: `git tag v2.4.0 -m "Release v2.4.0"`
- [ ] Push tag: `git push origin v2.4.0`
- [ ] GitHub release workflow automatically triggers (creates draft release)
- [ ] Attach Windows .exe to GitHub release
- [ ] Attach Android .apk to GitHub release
- [ ] Publish release (converts draft to public)

### Post-Release
- [ ] Announce on project README (Latest Release badge updates automatically)
- [ ] Monitor GitHub Issues for crash reports or user feedback
- [ ] Monitor Supabase analytics dashboard for anomalies
- [ ] Plan v2.4.1 or v2.5.0 based on feedback

---

## Risk Assessment

### High Risk
1. **Israeli channel URLs may have changed** — #46 is critical for Israeli users (primary user base). Need fresh URLs.
2. **CVE vulnerabilities unknown severity** — could include RCE or data leaks. Must fix before release.
3. **CI disabled = no automated quality gates** — manual testing burden increased until storage issue resolved.

### Medium Risk
1. **Channel database refresh may cause regressions** — 17k → 12k reduction means some channels removed. Test with real users.
2. **Android radio channels bug root cause unknown** — may be deeper architectural issue with media type filtering.
3. **Supabase credentials in code** — anon key is RLS-protected but should still move to env vars for best practice.

### Low Risk
1. **Language filter broken** — affects usability but not critical functionality.
2. **Diagnostics window missing on Windows** — quality of life, not blocking.

---

## Testing Strategy (v2.4.0)

### Manual Testing Required
1. **Israeli channels** (all variants): KAN 11, KAN Kids, i24News, Reshet 13
2. **Android radio channels**: Glglz, 100FM sub-channels (Hip Hop, Dance, etc.)
3. **Android filters**: Favorites only, Working only, Language dropdown
4. **Source failover**: Pick channel with 3+ sources, disable primary URL, verify auto-failover
5. **Offline mode**: Disable network, launch app, verify cached channels load
6. **VLC security**: Attempt to play `file:///etc/passwd`, verify rejection

### Automated Testing (CI)
1. Python tests: `pytest tests/ -v` (23 tests)
2. Flutter analyze: `flutter analyze` (0 errors, warnings allowed)
3. CVE Scanner: `pip-audit` + `flutter pub outdated --mode=security`
4. Build validation: `python tests/validate_build.py` (5 checks)

### Performance Testing
1. Startup time with 17k channels (should be <10s with Supabase health cache)
2. Scan time for 17k channels (with MAX_CONCURRENT_CHECKS=30, should be ~30-40 min)
3. Map view with 200+ country pins (should render <2s)
4. Channel list scroll performance with 17k items (Windows CustomTkinter, Android ListView)

---

## Post-v2.4.0 Roadmap Preview

### v2.4.1 (Patch) — Target: 1 week after v2.4.0
- Fix any critical bugs reported by users after v2.4.0 release
- Address remaining P2 items if time permits

### v2.5.0 (Minor) — Target: 2-4 weeks after v2.4.0
- **Feature:** Multi-device sync via Supabase (favorites, last played, preferences)
- **Feature:** Chromecast support (Android)
- **Feature:** Dark mode toggle (Windows — currently always dark)
- **Feature:** EPG UI integration (schedule icon in channel list)
- **Enhancement:** Improved search (fuzzy matching, instant results)
- **Security:** Complete SEC-007 (cleartext traffic restrictions) and SEC-010 (M3U size limits)

### v3.0.0 (Major) — Target: 2-3 months
- **Architecture:** Migrate Windows app to Electron or Flutter Desktop for UI parity
- **Feature:** User accounts (optional) for cloud sync
- **Feature:** Channel recommendations based on watch history
- **Feature:** Recording/DVR functionality (local cache of streams)
- **Infrastructure:** Self-hosted backend option (for privacy-focused users)
- **Internationalization:** Multi-language UI (Hebrew, Arabic, Spanish, French)

---

## Agent Assignments Summary

| Priority | Issue | Agent | Status |
|----------|-------|-------|--------|
| P0 | #46 (Israeli channels) | @backend-developer | Not started |
| P0 | CVE Scanner | @security-reviewer | Not started |
| P0 | CI storage | @github-operations | Not started |
| P1 | #43 (Radio Android) | @android-expert | Not started |
| P1 | #44 (Favorites Android) | @android-expert | Not started |
| P1 | #45 (Working filter Android) | @android-expert | Not started |
| P1 | Channel scan refresh | @backend-developer | Not started |
| P1 | #50 (VLC URL security) | @security-reviewer | Not started |
| P2 | #47 (Language filter) | @android-expert | Not started |
| P2 | #61 (Source selector) | @android-expert | Not started |
| P2 | #51 (Supabase env vars) | @security-reviewer | Not started |
| P2 | #52 (Remove PrivateBin) | @backend-developer | Not started |
| P2 | Windows diagnostics | @frontend-developer | Not started |
| P2 | Integration tests | @qa-automation | Not started |
| P2 | #53 (Config editor) | @frontend-developer | Not started |

---

## Conclusion

Version 2.4.0 should focus on **stability, security, and Android feature parity**. The project is in good shape at v2.3.3 with a solid Supabase backend and healthy CI/CD (once storage is fixed). The main gaps are Android UI bugs (#43-#47, #61) and security hardening (CVE scanner, VLC URL validation).

**Estimated timeline:** 2-3 weeks
- Week 1: P0 items (Israeli channels, CVE fixes, CI storage)
- Week 2: P1 items (Android bugs, channel refresh, VLC security)
- Week 3: P2 items (if time), testing, release prep

**Success criteria:**
1. All Israeli channels working on both platforms
2. Android feature parity with Windows (radio, favorites, filters)
3. Zero HIGH CVE vulnerabilities
4. CI re-enabled and passing
5. Clean channel database with <15k validated working channels

---

**Next steps:** Review this plan with @security-reviewer, @android-expert, @backend-developer, and @github-operations. Assign tickets and begin P0 work immediately.
