# TV Viewer Project Backlog

> **Maintained by:** project-manager, product-manager, pm-manager agents  
> **Last Updated:** 2026-01-28  
> **Current Version:** 1.5.0

## Backlog Categories

- 🐛 **Bug** - Defects and issues
- ✨ **Feature** - New functionality
- 🔧 **Enhancement** - Improvements to existing features
- 🔒 **Security** - Security-related items
- 📝 **Documentation** - Docs, README, guides
- ⚡ **Performance** - Performance optimizations
- 🏗️ **Infrastructure** - CI/CD, GitHub maintenance, DevOps
- 🧪 **Testing** - Test coverage and quality
- 🎨 **UX** - User experience improvements
- 📱 **Android** - Android-specific items

## Priority Levels

- **P0 - Critical**: Blocking, security vulnerabilities, data loss
- **P1 - High**: Major functionality broken, significant UX issues
- **P2 - Medium**: Minor bugs, feature enhancements
- **P3 - Low**: Nice-to-have, cosmetic issues

---

## 🚀 Active Backlog

### P0 - Critical (Must Fix Before Launch)

| ID | Type | Title | Source | Target Version |
|----|------|-------|--------|----------------|
| BL-001 | 📝 | User-friendly error messages (not technical stack traces) | support-engineer | 1.6.0 |
| BL-002 | 🏗️ | Add persistent logging service (not just debugPrint) | support-engineer | 1.6.0 |
| BL-003 | 🏗️ | Integrate Firebase Crashlytics for crash reporting | support-engineer | 1.6.0 |
| BL-004 | 📱 | Generate release keystore for APK signing | android-expert | 1.6.0 |
| BL-005 | 📱 | Add ProGuard rules (prevents release crashes) | android-expert | 1.6.0 |

### P1 - High Priority

| ID | Type | Title | Source | Target Version |
|----|------|-------|--------|----------------|
| BL-006 | ✨ | Implement native Google Cast SDK | end-user | 1.6.0 |
| BL-007 | ✨ | Add favorites/bookmarks for channels | end-user | 1.6.0 |
| BL-008 | 🎨 | Add "Clear Filters" button for filter discoverability | end-user | 1.6.0 |
| BL-009 | 📝 | Add in-app onboarding/tooltips for new users | end-user | 1.6.0 |
| BL-010 | 📝 | Create USER_GUIDE.md end-user documentation | support-engineer | 1.6.0 |
| BL-011 | 📝 | Create FAQ.md with top 20 questions | support-engineer | 1.6.0 |
| BL-012 | ✨ | Add in-app Help screen with FAQ | support-engineer | 1.6.0 |
| BL-013 | 📱 | Add wake lock permission for video playback | android-expert | 1.6.0 |
| BL-014 | 🧪 | Add unit tests (target 40% coverage) | developer, qa-engineer | 1.6.0 |
| BL-015 | 🔧 | Extract widgets (ChannelTile, FilterDropdown, ScanProgressBar) | developer | 1.6.0 |

### P2 - Medium Priority

| ID | Type | Title | Source | Target Version |
|----|------|-------|--------|----------------|
| BL-016 | 🎨 | Stream quality badges (HD/SD) instead of raw resolution | end-user | 1.7.0 |
| BL-017 | ✨ | Add language filter dropdown | feature request | 1.7.0 |
| BL-018 | 🔧 | Add volume slider in player controls | end-user | 1.7.0 |
| BL-019 | 🔒 | Add certificate pinning for API calls | security review | 1.7.0 |
| BL-020 | 🧪 | Add widget tests and integration tests | qa-engineer | 1.7.0 |
| BL-021 | ⚡ | Implement repository pattern for data layer | developer | 1.7.0 |
| BL-022 | ⚡ | Add dependency injection (get_it) | developer | 1.7.0 |
| BL-023 | 📱 | Add PiP (Picture-in-Picture) support | android-expert | 1.7.0 |
| BL-024 | ✨ | Add diagnostics screen (device info, network tests) | support-engineer | 1.7.0 |
| BL-025 | 🏗️ | Add Firebase Analytics for usage tracking | support-engineer | 1.7.0 |
| BL-026 | 📱 | Use enhanced ExternalPlayerService (6+ players) | android-expert | 1.7.0 |

### P3 - Low Priority

| ID | Type | Title | Source | Target Version |
|----|------|-------|--------|----------------|
| BL-027 | 🎨 | Add "LIVE" badge indicator in player | end-user | 1.8.0 |
| BL-028 | ✨ | Add channel EPG (Electronic Program Guide) | feature request | 1.8.0 |
| BL-029 | 📝 | Create video tutorials for app features | support-engineer | 1.8.0 |
| BL-030 | 🏗️ | Add automated release notes generation | infrastructure | 1.8.0 |
| BL-031 | ⚡ | Make Channel model immutable (copyWith) | developer | 1.8.0 |
| BL-032 | 🔧 | Add feedback/rating system in-app | support-engineer | 1.8.0 |

---

## ✅ Completed Items

### Version 1.5.0 (2026-01-28)

| ID | Type | Title | Completed |
|----|------|-------|-----------|
| DONE-001 | 🐛 | Fix external app launch for VLC/MX Player | 2026-01-28 |
| DONE-002 | ✨ | Add cast button with external player dialog | 2026-01-28 |
| DONE-003 | ✨ | Show resolution and bitrate in channel list | 2026-01-28 |
| DONE-004 | 🐛 | Consolidate categories (semicolon normalization) | 2026-01-28 |
| DONE-005 | ✨ | Replace category chips with dropdown selector | 2026-01-28 |
| DONE-006 | ✨ | Add country filter dropdown | 2026-01-28 |
| DONE-007 | ✨ | Add radio station support (media type filter) | 2026-01-28 |
| DONE-008 | 🐛 | Fix VideoPlayerController memory leak | 2026-01-28 |
| DONE-009 | ⚡ | Fix race condition in channel validation | 2026-01-28 |

---

## 📊 Backlog Metrics

| Metric | Count |
|--------|-------|
| Total Open Items | 32 |
| P0 - Critical | 5 |
| P1 - High | 10 |
| P2 - Medium | 11 |
| P3 - Low | 6 |
| Completed (1.5.0) | 9 |

---

## 📋 Review Sources

Items are added from:
- **Code Reviews** - code-review, developer agents
- **Security Reviews** - security-reviewer agent
- **QA Reviews** - qa-engineer, qa-automation agents
- **User Feedback** - end-user agent
- **Support Analysis** - support-engineer agent
- **Market Analysis** - gartner-analyst, compete-expert agents
- **Sales Feedback** - security-sales agent
- **Android Review** - android-expert agent
- **GitHub Issues** - github-issues-monitor agent
- **PM Reviews** - pm-manager, product-manager agents

---

## 🗓️ Version Planning

### v1.6.0 - Supportability & Stability (Target: 2 weeks)
Focus: Error handling, documentation, critical Android fixes
- All P0 items
- P1 items BL-006 through BL-015

### v1.7.0 - Architecture & Quality (Target: 3 weeks)
Focus: Code quality, testing, performance
- P2 items BL-016 through BL-026

### v1.8.0 - Features & Polish (Target: 4 weeks)
Focus: New features, UX enhancements
- P3 items BL-027 through BL-032

---

## 🔄 Backlog Management Process

1. **Add Items**: Any agent can propose items during reviews
2. **Triage**: pm-manager assigns priority and target version
3. **Planning**: project-manager includes items in sprint/release planning
4. **Implementation**: developer, android-expert implement
5. **Review**: qa-engineer, security-reviewer validate
6. **Completion**: Item moved to Completed, CHANGELOG.md updated
7. **Metrics**: hr-manager reviews team effectiveness every 10 releases

---

## 👥 HR Team Review Schedule

| Review | Version Range | Status |
|--------|---------------|--------|
| Review #1 | v1.0 - v2.5 | Next: v2.5.0 |
| Review #2 | v2.5 - v3.5 | Scheduled |
| Review #3 | v3.5 - v4.5 | Scheduled |

*Next HR Team Review: Version 2.5.0*

---

*Last updated: 2026-01-28 by copilot agent team*
