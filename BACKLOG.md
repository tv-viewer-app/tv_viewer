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

## Priority Levels

- **P0 - Critical**: Blocking, security vulnerabilities, data loss
- **P1 - High**: Major functionality broken, significant UX issues
- **P2 - Medium**: Minor bugs, feature enhancements
- **P3 - Low**: Nice-to-have, cosmetic issues

---

## 🚀 Active Backlog

### P1 - High Priority

| ID | Type | Title | Source | Assigned | Target Version |
|----|------|-------|--------|----------|----------------|
| BL-001 | ✨ | Implement native Google Cast SDK | end-user review | - | 1.6.0 |
| BL-002 | ✨ | Add favorites/bookmarks for channels | end-user review | - | 1.6.0 |
| BL-003 | 🔧 | Improve filter discoverability (clear filters button) | end-user review | - | 1.6.0 |
| BL-004 | 📝 | Add in-app onboarding/tooltips for new users | end-user review | - | 1.6.0 |

### P2 - Medium Priority

| ID | Type | Title | Source | Assigned | Target Version |
|----|------|-------|--------|----------|----------------|
| BL-005 | ⚡ | Add stream quality badges (HD/SD) instead of raw resolution | end-user review | - | 1.7.0 |
| BL-006 | ✨ | Add language filter dropdown | feature request | - | 1.7.0 |
| BL-007 | ✨ | Add channel EPG (Electronic Program Guide) | feature request | - | 1.8.0 |
| BL-008 | 🔧 | Add volume slider in player controls | end-user review | - | 1.7.0 |
| BL-009 | 🔒 | Add certificate pinning for API calls | security review | - | 1.7.0 |
| BL-010 | 🧪 | Add Flutter widget tests | code review | - | 1.7.0 |

### P3 - Low Priority

| ID | Type | Title | Source | Assigned | Target Version |
|----|------|-------|--------|----------|----------------|
| BL-011 | 🔧 | Add "LIVE" badge indicator in player | end-user review | - | 1.8.0 |
| BL-012 | 📝 | Create user documentation/FAQ | support review | - | 1.8.0 |
| BL-013 | 🏗️ | Add automated release notes generation | infrastructure | - | 1.8.0 |

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
| Total Open Items | 13 |
| P1 - High | 4 |
| P2 - Medium | 6 |
| P3 - Low | 3 |
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
- **GitHub Issues** - github-issues-monitor agent
- **Performance Reviews** - pm-manager, product-manager agents

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

*Next HR Team Review: Version 2.5.0*
