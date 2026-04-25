# Mal - Lead Agent History

## Role
Lead architect and decision-maker for TV Viewer. Responsible for architecture, code review, triage, and release decisions.

## Learnings

### 2026-03-26: Version 2.4.0 Planning & Analysis

**Context:** Conducted comprehensive analysis of TV Viewer project to generate next version work items.

**Findings:**

1. **Desktop (Python) v1.9.0 State:**
   - Modern UI components (nav_rail, channel_card, channel_grid, top_bar, status_bar) fully designed but NOT integrated into MainWindow
   - Still using legacy list-based UI from v1.0
   - Code quality excellent: 7,265 lines, 50 passing tests, zero TODOs/FIXMEs in core/ui
   - CI/CD pipeline mature and comprehensive (11 workflows)
   - 6 open security issues (#49-54) need addressing

2. **Flutter (Android) v2.3.3 State:**
   - Version number ahead of desktop (2.3.3 vs 1.9.0) - causes user confusion
   - 10 critical UX bugs open, mostly Android-specific
   - Good architecture (DI pattern with get_it, service layer)
   - 46 Dart files, clean codebase
   - Critical gap: No repository selector (users stuck if default sources fail) - Issue #61

3. **Critical Issues Identified:**
   - **#61 (P0):** Can't change sources when channel error - no recovery path for users
   - **#39 (P0):** PiP crashes due to null safety violations
   - **#46 (P0):** Israeli channels not working (Channel 10, i24News, KAN)
   - **#35 (P0):** Segfault during scan (already fixed in v1.8.1, needs verification)
   - **#44, #45 (P1):** No favorites/working channels filters - major UX gap
   - **#43 (P1):** Radio channels not showing (media type filter issue)

4. **Version Decision Rationale:**
   - Chose v2.4.0 (not v3.0.0) because changes are evolutionary, not revolutionary
   - Aligned both platforms to same version (2.4.0) to reduce confusion
   - Minor version bump appropriate: multiple bug fixes + significant UX improvements, no breaking changes

5. **Architecture Insights:**
   - Flutter app has good User-Agent centralization (`constants.dart`) - version updates propagate automatically
   - Desktop UI components were designed in v1.9.0 but never integrated - ITEM-10 addresses this
   - Security posture improving: hardcoded credentials moved to secrets, daily CVE scans active
   - Threading safety critical on desktop: root.after() pattern for UI updates from background threads

6. **Agent Workload Planning:**
   - Kaylee (Flutter): 32 hours - Heavy Android bug fixing
   - Wash (Backend): 15 hours - Security + desktop core
   - Zoe (Testing): 5 hours - Regression tests
   - Mal (Lead): 10 hours - Architecture review + docs

7. **Release Complexity:**
   - 20 work items: 4 P0, 10 P1, 6 P2
   - Critical path: PiP fix → Repository selector → Israeli channels → Desktop UI integration
   - Estimated 10-day release cycle with parallelized agent work
   - Risk: MainWindow refactor (#10) is 8-hour task touching core UI

**Key Learnings:**

- **UX Debt Accumulates:** Desktop designed modern UI in v1.9.0 but never integrated - tech debt compounds
- **Version Misalignment Confuses Users:** Desktop 1.9.0 vs Flutter 2.3.3 makes support harder
- **Repository Flexibility Critical:** Issue #61 shows importance of source configurability for resilience
- **Flutter Architecture Solid:** DI pattern, service layer, constants centralization all working well
- **Security Automation Working:** Daily CVE scans catching issues early (5 recent scan issues)
- **Issue Triage Essential:** 30+ closed issues, patterns emerging (Android UX gaps, security hardening)

**Decisions Made:**

1. Version 2.4.0 for both platforms (alignment + minor version bump)
2. P0 focus: Android critical bugs (PiP, Israeli channels, repository selector, segfault verification)
3. P1 focus: Android UX gaps (filters for favorites/working/radio) + Desktop UI integration
4. P2 polish: Documentation, test coverage, minor security hardening
5. Deferred to v2.5.0: Shared database (#31), feedback system (#23), complex player race conditions (#42)

**Process Insights:**

- GitHub Issues well-organized with P0/P1/P2/P3 labels and v2.0.0 milestone
- BUG_ANALYSIS.md from v1.8.2 still relevant - segfault and VLC hang patterns
- BACKLOG.md deprecated in favor of GitHub Issues (good move)
- ANDROID_BUGS.md shows completed work (v1.5.0 features)

**Next Actions:**

1. Get approval from Ariel (Product Owner) on v2.4.0 plan
2. Create GitHub milestone for v2.4.0
3. Create issues for all P0/P1 items
4. Assign issues to agents (Kaylee, Wash, Zoe)
5. Begin P0 work (PiP fix, repository selector, Israeli channels)

---

*Last Updated: 2026-03-26 by Mal*

---

## 2026-03-26: FRESH v2.3.3 Codebase Audit (Corrected Analysis)

**Context:** Performed comprehensive audit of TV Viewer project at v2.3.3. Previous analysis mistakenly focused on v1.9.0 state. Project has evolved significantly with 21 releases between v1.9.0 (Feb 24) and v2.3.3 (Mar 5).

### Critical Correction
The previous history entry analyzed v1.9.0 state (desktop not yet updated). **Actual current state:**
- **Desktop:** v2.3.3 (config.py) — fully updated with Supabase, map view, source selector
- **Android:** v2.3.3+26 (pubspec.yaml) — in sync with desktop
- **Both platforms feature-complete** with map view, favorites, EPG, analytics, crash reporting

### Key Findings (v2.3.3 Reality)

#### Architecture Evolution (v2.0.0 → v2.3.3)
1. **Supabase integration complete** — Analytics events, channel health sharing, crowd-sourced database all operational
2. **Channel consolidation working** — v2.3.3 fixed country prefix stripping and cross-country merging
3. **Health cache optimization** — 56% scan reduction (9,201 of 16,397 channels skipped via SharedDb cache)
4. **Multi-URL failover robust** — Health-based URL ordering with automatic fallback on play failure
5. **Desktop UI fully modernized** — nav_rail, channel_grid, map_window, source selector all integrated

#### Critical Issues (v2.3.3)
1. **Israeli channel URLs broken** (Issue #46, P0) — KAN 11, i24News, KAN Kids not playing
2. **CVE Scanner failing** — 2 consecutive daily runs failed (dependency vulnerabilities)
3. **CI disabled** — 0.5GB GitHub Actions storage limit exhausted
4. **Android filters broken:**
   - Radio channels not showing (#43) — media_type filter issue
   - Favorites filter not working (#44) — UI exists but doesn't filter
   - Working-only filter missing (#45) — no status filter dropdown
   - Language dropdown broken (#47) — only shows "All"
5. **Channel database bloated** — 17,948 channels (up from 13,353 in v2.3.0), likely many dead

#### Code Quality (v2.3.3)
- **Python:** 4 test files, 23 tests total — good core coverage
- **Flutter:** Sparse tests (dirs exist but minimal coverage)
- **No integration tests** — Critical flows (load → play → failover) not tested end-to-end
- **TODOs scattered** — Mostly in Flutter services (feedback_service, channel_provider)

#### Security Posture
- **Supabase anon keys hardcoded** — RLS-protected but should be env vars (Issue #51)
- **VLC URL validation needs verification** — SSRF protection exists but coverage uncertain (Issue #50)
- **PrivateBin dead code** — Disabled in v2.1.2 but code still present (Issue #52)
- **Config editor unsafe** — Uses os.startfile (SEC-005, Issue #53)

### Updated v2.4.0 Plan

Created comprehensive release plan in `.squad/decisions/inbox/mal-next-version.md`:

**P0 (MUST ship):**
1. Fix Israeli channel URLs (#46) — Primary user base blocked
2. Fix CVE vulnerabilities — Security compliance requirement
3. Clean up GitHub Actions storage and re-enable CI — Restore automated quality gates

**P1 (SHOULD ship):**
1. Fix Android radio channels not showing (#43)
2. Fix Android favorites filter (#44)
3. Fix Android working-only filter (#45)
4. Refresh channel database (17k → ~12k working channels)
5. Validate VLC URL security (#50)

**P2 (NICE to have):**
1. Fix Android language filter (#47)
2. Fix source selector on error screen (#61)
3. Migrate Supabase credentials to env vars (#51)
4. Remove dead PrivateBin code (#52)
5. Add Windows diagnostics window (parity with Android)
6. Add integration tests
7. Fix config editor security (#53)

### Key Learnings (Corrected)

#### What Changed Since v1.9.0
1. **Rapid iteration** — 21 releases in 9 days shows active development cycle
2. **Feature completeness** — Both platforms have map view, EPG, analytics, crash reporting
3. **Supabase as backbone** — Centralized analytics, health sharing, channel database
4. **Multi-platform parity** — Windows and Android now have equivalent features (except broken filters)

#### Technical Debt Identified
1. **Test coverage gaps** — Flutter tests minimal, no integration tests
2. **Android filter regressions** — Multiple filters broken suggests insufficient Android testing
3. **Dead PrivateBin code** — Should be fully removed, not just disabled
4. **Hardcoded credentials** — Supabase keys should be env vars
5. **CVE monitoring noise** — Daily scanner creates duplicate issues

#### Process Improvements Needed
1. **GitHub Actions storage monitoring** — Hit 0.5GB limit without warning
2. **Integration test suite** — No automated testing of critical user flows
3. **Android regression testing** — Multiple filters broken after consolidation refactors
4. **CVE scan cadence** — Move from daily to weekly with automatic triage

### Agent Collaboration Strategy

**Recommended agents for v2.4.0:**
- `@security-reviewer` — CVE fixes, VLC URL validation, credential migration
- `@android-expert` — Radio channels, favorites filter, working filter, language filter, source selector
- `@backend-developer` — Israeli channel URLs, channel database refresh, PrivateBin cleanup
- `@github-operations` — Actions storage cleanup, CI re-enable, cache management
- `@frontend-developer` — Windows diagnostics window, config editor safety
- `@qa-automation` — Integration test suite creation

### Next Actions
1. Share v2.4.0 plan with Ariel for approval
2. Create GitHub milestone for v2.4.0 if not exists
3. Create/update issues for P0/P1 items
4. Begin P0 work immediately (Israeli channels, CVE scanner, CI storage)
5. Target v2.4.0 release in 2-3 weeks

### Lessons Learned

#### Architecture
- **Supabase RLS policies working well** — Anonymous analytics with proper protection
- **Multi-URL failover robust** — Health-based ordering prevents dead stream frustration
- **Channel consolidation complex** — Country prefixes, Hebrew/Latin variants, quality suffixes all require careful normalization
- **Threading model critical** — `root.after(0, ...)` pattern prevents segfaults on Windows

#### Development Process
- **CHANGELOG.md discipline pays off** — Every release documented, easy to trace feature evolution
- **Version sync automation working** — Flutter local.properties synced with pubspec.yaml
- **GitHub Actions storage is finite** — Need proactive monitoring and cleanup
- **Android filter UI fragile** — Multiple regressions suggest insufficient test coverage

#### User Impact
- **Israeli channels critical** — Many custom channels in Israeli category, primary user base
- **Android filters essential** — Users need to filter 17k channels by radio/favorites/working status
- **Source configurability important** — Issue #61 shows users need fallback when default repos fail

---

*Last Updated: 2026-03-26 by Mal (Corrected Analysis)*
