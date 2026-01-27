#!/usr/bin/env python3
"""Helper script to create PRD.md in docs folder."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
docs_dir = os.path.join(BASE_DIR, "docs")
os.makedirs(docs_dir, exist_ok=True)
print(f"Created: {docs_dir}")

prd_content = '''# TV Viewer - Product Requirements Document (PRD)

**Version:** 1.0  
**Date:** January 2025  
**Product:** TV Viewer IPTV Streaming Application  
**Status:** Production-Ready Enhancement Phase

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [User Stories](#user-stories)
4. [Feature Gap Analysis](#feature-gap-analysis)
5. [Prioritized Feature Roadmap](#prioritized-feature-roadmap)
6. [Success Metrics / KPIs](#success-metrics--kpis)
7. [Technical Requirements](#technical-requirements)
8. [Risks and Mitigations](#risks-and-mitigations)
9. [Appendix](#appendix)

---

## Executive Summary

### Product Vision
TV Viewer is a cross-platform IPTV streaming application that enables users to discover, organize, and watch live television streams from public IPTV repositories worldwide. The application provides a modern, no-login-required experience with automatic channel discovery and validation.

### Target Audience
- **Primary:** Cord-cutters seeking free, legal IPTV content
- **Secondary:** International viewers seeking content from their home countries
- **Tertiary:** Technical users who want a customizable IPTV client

### Business Objectives
1. Deliver a reliable, user-friendly IPTV viewing experience
2. Support 10,000+ channels with efficient resource usage
3. Provide cross-platform compatibility (Windows, macOS, Linux)
4. Enable community contribution through open-source development

### Current Version
**v1.0.0** - Core functionality implemented with streaming, channel management, and modern UI.

---

## Current State Analysis

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         TV Viewer v1.0                          │
├─────────────────────────────────────────────────────────────────┤
│  UI Layer (CustomTkinter)                                       │
│  ├── MainWindow - Channel browsing, search, filtering           │
│  ├── PlayerWindow - VLC-based video playback                    │
│  └── ScanAnimation - Progress visualization                     │
├─────────────────────────────────────────────────────────────────┤
│  Core Layer                                                     │
│  ├── ChannelManager - Central data coordinator                  │
│  ├── StreamChecker - Background validation                      │
│  └── RepositoryHandler - M3U playlist fetching                  │
├─────────────────────────────────────────────────────────────────┤
│  Utils Layer                                                    │
│  ├── helpers.py - M3U parsing, JSON I/O                        │
│  ├── channel_lookup.py - Metadata enrichment                    │
│  └── thumbnail.py - Preview capture                             │
├─────────────────────────────────────────────────────────────────┤
│  External Dependencies                                          │
│  ├── VLC (python-vlc) - Video playback                         │
│  ├── aiohttp - Async HTTP operations                           │
│  └── pychromecast (optional) - Google Cast                     │
└─────────────────────────────────────────────────────────────────┘
```

### Implemented Features (v1.0)

| Feature | Status | Quality |
|---------|--------|---------|
| Channel Discovery | ✅ Complete | High |
| Background Stream Validation | ✅ Complete | High |
| Category/Country Organization | ✅ Complete | High |
| Media Type Filtering (TV/Radio) | ✅ Complete | Medium |
| Search Functionality | ✅ Complete | Medium |
| VLC-Embedded Playback | ✅ Complete | High |
| Hardware Acceleration | ✅ Complete | High |
| Volume/Mute Controls | ✅ Complete | High |
| Fullscreen Mode | ✅ Complete | High |
| Google Cast Support | ✅ Complete | Medium |
| External VLC Launch | ✅ Complete | High |
| Channel Cache Persistence | ✅ Complete | High |
| Custom Channel Support | ✅ Complete | Medium |
| Adult Content Filtering | ✅ Complete | High |
| Age Rating System | ✅ Complete | Medium |
| Material Design UI | ✅ Complete | High |
| Thumbnail Previews | ✅ Complete | Medium |
| Build/Distribution (PyInstaller) | ✅ Complete | High |

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.8+ |
| UI Framework | CustomTkinter | Latest |
| Video Backend | VLC (libvlc) | 3.0+ |
| HTTP Client | aiohttp | Latest |
| Concurrency | asyncio + threading | stdlib |
| Data Storage | JSON files | N/A |
| Build Tool | PyInstaller | Latest |

### Performance Metrics (Current)

| Metric | Target | Current |
|--------|--------|---------|
| Startup Time (cached) | < 3s | ~2s ✅ |
| Memory (10k channels) | < 200 MB | ~150 MB ✅ |
| CPU during scan | < 30% | ~25% ✅ |
| CPU during playback | < 10% | ~5% ✅ |
| Validation throughput | 100/min | 120/min ✅ |

---

## User Stories

### Existing User Stories (Implemented)

#### US-001: Channel Discovery
**As a** user  
**I want to** automatically discover TV channels from IPTV repositories  
**So that** I can watch content without manual configuration

**Acceptance Criteria:**
- ✅ Fetches channels from IPTV-org repositories
- ✅ Deduplicates channels by URL
- ✅ Merges with existing cache preserving status
- ✅ Supports custom repositories via config

#### US-002: Channel Validation
**As a** user  
**I want to** see which channels are working before trying to watch  
**So that** I don't waste time on broken streams

**Acceptance Criteria:**
- ✅ Background validation without blocking UI
- ✅ Visual status indicators (Working/Failed/Checking)
- ✅ Skip recently scanned channels (10-minute threshold)
- ✅ Progress indicator during scan

#### US-003: Channel Organization
**As a** user  
**I want to** browse channels by category or country  
**So that** I can find content that interests me

**Acceptance Criteria:**
- ✅ Group by category (News, Sports, Movies, etc.)
- ✅ Group by country (USA, UK, Israel, etc.)
- ✅ Toggle between grouping modes
- ✅ Filter by media type (TV/Radio/All)

#### US-004: Search
**As a** user  
**I want to** search for channels by name  
**So that** I can quickly find specific content

**Acceptance Criteria:**
- ✅ Case-insensitive search
- ✅ Real-time filtering
- ✅ Works across all channels

#### US-005: Video Playback
**As a** user  
**I want to** watch streams in an embedded player with controls  
**So that** I have a complete viewing experience

**Acceptance Criteria:**
- ✅ Play/Pause/Stop controls
- ✅ Volume control with mute
- ✅ Fullscreen toggle
- ✅ Keyboard shortcuts (Space, F, M, Escape)
- ✅ Stream quality display

#### US-006: Casting
**As a** user  
**I want to** cast streams to my TV via Chromecast  
**So that** I can watch on a larger screen

**Acceptance Criteria:**
- ✅ Discover Chromecast devices
- ✅ Cast current stream
- ✅ Stop casting

### Proposed User Stories (Not Implemented)

#### US-007: Favorites
**As a** user  
**I want to** mark channels as favorites  
**So that** I can quickly access channels I watch regularly

**Acceptance Criteria:**
- [ ] Add/remove favorites via UI
- [ ] Favorites persist across sessions
- [ ] Dedicated "Favorites" category
- [ ] Quick access in sidebar

#### US-008: Watch History
**As a** user  
**I want to** see my recently watched channels  
**So that** I can easily return to content I was watching

**Acceptance Criteria:**
- [ ] Track last 50 watched channels
- [ ] "Recent" section in sidebar
- [ ] Clear history option
- [ ] Timestamp of last watch

#### US-009: EPG (Electronic Program Guide)
**As a** user  
**I want to** see what's currently playing and upcoming programs  
**So that** I can plan my viewing

**Acceptance Criteria:**
- [ ] Fetch EPG data from XMLTV sources
- [ ] Show current program info
- [ ] Show next program
- [ ] Program schedule view

#### US-010: Recording/DVR
**As a** user  
**I want to** record live streams  
**So that** I can watch content later

**Acceptance Criteria:**
- [ ] One-click recording
- [ ] Scheduled recordings
- [ ] Recording library management
- [ ] Configurable storage location

#### US-011: Parental Controls
**As a** parent  
**I want to** restrict access to mature content  
**So that** my children can safely use the application

**Acceptance Criteria:**
- [ ] PIN-protected settings
- [ ] Age-based filtering
- [ ] Channel blacklist
- [ ] Time restrictions

#### US-012: Multiple Languages
**As an** international user  
**I want to** use the application in my native language  
**So that** I can navigate comfortably

**Acceptance Criteria:**
- [ ] UI translation system
- [ ] Support for 10+ languages
- [ ] Auto-detect system language
- [ ] Manual language selection

#### US-013: Playlist Import/Export
**As a** power user  
**I want to** import my own M3U playlists  
**So that** I can use my existing channel lists

**Acceptance Criteria:**
- [ ] Import local M3U files
- [ ] Import from URL
- [ ] Export current channels
- [ ] Merge vs. replace options

#### US-014: Picture-in-Picture
**As a** user  
**I want to** watch streams in a small overlay window  
**So that** I can multitask while watching

**Acceptance Criteria:**
- [ ] Floating mini-player
- [ ] Always-on-top option
- [ ] Resize and reposition
- [ ] Basic controls in PiP mode

#### US-015: Multi-View
**As a** sports fan  
**I want to** watch multiple channels simultaneously  
**So that** I can follow multiple events at once

**Acceptance Criteria:**
- [ ] 2x2 grid view
- [ ] Audio selection (which stream to hear)
- [ ] Click to expand single view
- [ ] Configurable layout

---

## Feature Gap Analysis

### Critical Gaps (Must Have for Production)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Favorites System | High - Poor UX for returning users | Low | P0 |
| Watch History | Medium - No context retention | Low | P0 |
| Error Recovery | High - Streams fail silently | Medium | P0 |
| Offline Mode Handling | Medium - No feedback when offline | Low | P0 |

### Important Gaps (Should Have)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| EPG Integration | High - Missing key IPTV feature | High | P1 |
| Playlist Import | Medium - Power users blocked | Medium | P1 |
| Parental Controls | Medium - Family safety concern | Medium | P1 |
| Auto-Update | Medium - Manual updates required | Medium | P1 |
| Subtitle Support | Medium - Accessibility gap | Low | P1 |

### Nice-to-Have Gaps

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Recording/DVR | Low - Complex feature | High | P2 |
| Picture-in-Picture | Low - Convenience feature | Medium | P2 |
| Multi-View | Low - Niche use case | High | P2 |
| Multi-Language UI | Medium - International reach | Medium | P2 |
| Sleep Timer | Low - Convenience feature | Low | P2 |
| Stream Quality Selection | Low - Most streams single quality | Medium | P2 |

### Future Considerations

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Cloud Sync | Low - Requires backend | High | P3 |
| Mobile Companion App | Low - Different platform | Very High | P3 |
| Social Features | Low - Not core to product | High | P3 |
| AI Recommendations | Low - Requires ML infrastructure | Very High | P3 |

---

## Prioritized Feature Roadmap

### Phase 1: Core Polish (P0) - 2-4 Weeks

**Goal:** Address critical UX gaps and stability issues

#### 1.1 Favorites System
```
Files to modify:
- core/channel_manager.py (add favorites list)
- ui/main_window.py (favorite toggle, favorites view)
- config.py (favorites file path)
- utils/helpers.py (favorites persistence)

Data Model:
{
  "favorites": ["channel_url_1", "channel_url_2", ...]
}
```

#### 1.2 Watch History
```
Files to modify:
- core/channel_manager.py (track watched)
- ui/main_window.py (recent channels view)
- config.py (history settings)

Data Model:
{
  "history": [
    {"url": "...", "name": "...", "last_watched": "ISO8601", "watch_count": 5}
  ]
}
```

#### 1.3 Enhanced Error Handling
```
Improvements:
- Stream error notifications with retry option
- Network connectivity detection
- Graceful degradation when VLC unavailable
- User-friendly error messages
```

#### 1.4 Offline Mode
```
Improvements:
- Detect network status
- Show "Offline" indicator
- Auto-retry when connection restored
- Cache browsing still available
```

### Phase 2: Feature Expansion (P1) - 4-8 Weeks

**Goal:** Add key features expected by IPTV users

#### 2.1 EPG Integration
```
New files:
- core/epg_handler.py
- utils/xmltv_parser.py

Features:
- Fetch XMLTV data from iptv-org
- Match EPG to channels
- Show current/next program
- Basic schedule view
```

#### 2.2 Playlist Import/Export
```
New files:
- utils/playlist_io.py

Features:
- Import local M3U/M3U8 files
- Import from URL
- Export to M3U
- Merge strategies
```

#### 2.3 Parental Controls
```
New files:
- core/parental_controls.py
- ui/settings_window.py

Features:
- PIN protection
- Age-based filtering (7+, 13+, 16+, 18+)
- Channel blocking
- Settings persistence
```

#### 2.4 Auto-Update System
```
New files:
- utils/updater.py

Features:
- Check for updates on startup
- Download and install (Windows)
- Notify only (other platforms)
- Rollback capability
```

#### 2.5 Subtitle Support
```
Modifications:
- ui/player_window.py (subtitle track selection)
- VLC options for subtitle rendering
```

### Phase 3: Enhanced Experience (P2) - 8-12 Weeks

**Goal:** Premium features for power users

#### 3.1 Recording/DVR
```
New files:
- core/recorder.py
- ui/recording_manager.py

Features:
- FFmpeg-based recording
- Recording library
- Storage management
- Scheduled recordings
```

#### 3.2 Picture-in-Picture
```
Modifications:
- ui/player_window.py (PiP mode)
- New: ui/pip_window.py

Features:
- Floating overlay
- Always-on-top
- Minimal controls
```

#### 3.3 Multi-Language UI
```
New files:
- locales/en.json
- locales/es.json
- locales/fr.json
- utils/i18n.py

Features:
- Translation framework
- Language selection
- RTL support (Hebrew, Arabic)
```

#### 3.4 Multi-View
```
New files:
- ui/multiview_window.py

Features:
- Grid layouts (2x2, 3x3)
- Audio routing
- Sync playback
```

### Phase 4: Platform Growth (P3) - 12+ Weeks

**Goal:** Expand reach and ecosystem

#### 4.1 Cloud Sync
- User accounts (optional)
- Favorites/history sync
- Cross-device experience

#### 4.2 Mobile Companion
- React Native or Flutter app
- Remote control for desktop
- Mobile playback

#### 4.3 Community Features
- Channel ratings
- User-submitted channels
- Community playlists

---

## Success Metrics / KPIs

### User Engagement Metrics

| Metric | Current | Target (6 mo) | Target (12 mo) |
|--------|---------|---------------|----------------|
| Daily Active Users | N/A | 1,000 | 5,000 |
| Session Duration | N/A | 30 min | 45 min |
| Channels Watched/Session | N/A | 5 | 8 |
| Return Rate (7-day) | N/A | 40% | 60% |
| Favorites Added/User | N/A | 10 | 20 |

### Technical Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Crash Rate | <1% | <0.1% |
| Stream Success Rate | ~70% | 85% |
| Startup Time | 2s | <2s |
| Memory Usage | 150MB | <150MB |
| CPU Usage (playback) | 5% | <5% |

### Quality Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Working Channels % | 70% | 80% |
| Category Accuracy | 85% | 95% |
| Country Detection | 80% | 90% |
| Search Relevance | Medium | High |

### Distribution Metrics

| Metric | Current | Target (6 mo) |
|--------|---------|---------------|
| GitHub Stars | N/A | 500 |
| Downloads/Month | N/A | 2,000 |
| Active Forks | N/A | 50 |
| Community PRs | N/A | 10/month |

---

## Technical Requirements

### System Requirements

#### Minimum
- **OS:** Windows 10, macOS 10.14, Ubuntu 18.04
- **CPU:** Dual-core 2.0 GHz
- **RAM:** 4 GB
- **Storage:** 500 MB (plus recordings)
- **Network:** 5 Mbps broadband
- **Dependencies:** VLC 3.0+

#### Recommended
- **OS:** Windows 11, macOS 12+, Ubuntu 22.04
- **CPU:** Quad-core 3.0 GHz
- **RAM:** 8 GB
- **Storage:** 2 GB SSD
- **Network:** 25 Mbps broadband
- **GPU:** Hardware video decode support

### Development Requirements

| Requirement | Specification |
|-------------|--------------|
| Python Version | 3.8 - 3.12 |
| Package Manager | pip with requirements.txt |
| Testing Framework | pytest (to be added) |
| Linting | flake8, black (to be added) |
| Type Checking | mypy (to be added) |
| Documentation | Markdown, docstrings |
| Build System | PyInstaller |
| CI/CD | GitHub Actions (to be added) |

### Security Requirements

| Requirement | Status |
|-------------|--------|
| URL Scheme Validation | ✅ Implemented |
| Input Sanitization | ✅ Implemented |
| No Credentials Storage | ✅ N/A |
| HTTPS for Metadata | ✅ Implemented |
| Content Size Limits | ✅ Implemented |
| VLC Lua Disabled | ✅ Implemented |

### Accessibility Requirements (To Implement)

| Requirement | Status | Priority |
|-------------|--------|----------|
| Keyboard Navigation | Partial | P1 |
| Screen Reader Support | Not Started | P2 |
| High Contrast Mode | Not Started | P2 |
| Font Size Options | Not Started | P2 |
| Color Blind Modes | Not Started | P3 |

### Performance Requirements

| Requirement | Specification |
|-------------|--------------|
| Cold Start | < 5 seconds |
| Warm Start (cached) | < 2 seconds |
| Channel Switch | < 3 seconds |
| Search Response | < 100ms |
| Memory Ceiling | 300 MB |
| CPU Ceiling (idle) | 5% |
| CPU Ceiling (playback) | 15% |

---

## Risks and Mitigations

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **VLC API Changes** | Low | High | Pin python-vlc version; maintain fallback to external VLC |
| **IPTV-org Repository Unavailable** | Medium | High | Cache channels locally; support multiple repositories; offline mode |
| **Stream Format Incompatibility** | Medium | Medium | VLC handles most formats; document unsupported formats |
| **Platform-Specific Issues** | Medium | Medium | CI testing on all platforms; platform-specific code paths |
| **Memory Leaks** | Low | Medium | Profile regularly; use __slots__; explicit cleanup |
| **CustomTkinter Breaking Changes** | Low | Medium | Pin version; abstract UI layer for future migration |

### Legal/Compliance Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Copyright Concerns** | Medium | High | Only aggregate public repositories; no content hosting; clear disclaimers |
| **Adult Content Exposure** | Low | High | Aggressive filtering (implemented); parental controls (planned) |
| **Geo-Blocking Issues** | High | Low | Document in FAQ; out of scope for app |
| **DMCA Takedowns** | Low | Medium | Responsive removal process; no content storage |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Low Adoption** | Medium | Medium | Focus on UX; community engagement; differentiation |
| **Maintenance Burden** | Medium | Medium | Good documentation; automated testing; modular design |
| **Competition** | High | Low | Open-source advantage; cross-platform; no login required |
| **Repository Quality Decline** | Medium | Medium | Support multiple sources; community channel submissions |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Support Overload** | Medium | Low | FAQ documentation; GitHub issues templates; community support |
| **Build Pipeline Failure** | Low | Medium | Multiple CI providers; local build option |
| **Dependency Vulnerabilities** | Medium | Medium | Dependabot alerts; regular updates; minimal dependencies |

---

## Appendix

### A. Competitive Analysis

| Feature | TV Viewer | Kodi | VLC | IPTV Smarters |
|---------|-----------|------|-----|---------------|
| Free | ✅ | ✅ | ✅ | Freemium |
| No Login | ✅ | ✅ | ✅ | ❌ |
| Auto-Discovery | ✅ | ❌ | ❌ | ❌ |
| Stream Validation | ✅ | ❌ | ❌ | ✅ |
| Modern UI | ✅ | ❌ | ❌ | ✅ |
| Cross-Platform | ✅ | ✅ | ✅ | ✅ |
| EPG | ❌ | ✅ | ❌ | ✅ |
| Recording | ❌ | ✅ | ✅ | ✅ |
| Lightweight | ✅ | ❌ | ✅ | ✅ |
| Open Source | ✅ | ✅ | ✅ | ❌ |

### B. User Personas

#### Persona 1: "Cord-Cutter Carlos"
- **Age:** 35
- **Technical Level:** Medium
- **Goals:** Watch news and sports without cable
- **Pain Points:** Too many streaming subscriptions; missing live TV
- **Needs:** Easy setup, reliable streams, sports channels

#### Persona 2: "International Irene"
- **Age:** 45
- **Technical Level:** Low
- **Goals:** Watch TV from home country
- **Pain Points:** Geo-restrictions; language barriers
- **Needs:** Country filtering, native language content, simple UI

#### Persona 3: "Power User Paul"
- **Age:** 28
- **Technical Level:** High
- **Goals:** Customize IPTV experience
- **Pain Points:** Limited customization in other apps
- **Needs:** Playlist import, custom repositories, keyboard shortcuts

### C. Glossary

| Term | Definition |
|------|------------|
| IPTV | Internet Protocol Television - TV delivered over IP networks |
| M3U | Multimedia playlist file format |
| EPG | Electronic Program Guide |
| XMLTV | XML-based EPG format |
| HLS | HTTP Live Streaming |
| RTMP | Real-Time Messaging Protocol |
| DVR | Digital Video Recorder |
| PiP | Picture-in-Picture |
| VLC | VideoLAN Client media player |

### D. References

- [IPTV-org Repository](https://github.com/iptv-org/iptv)
- [CustomTkinter Documentation](https://customtkinter.tomschimansky.com/)
- [python-vlc Documentation](https://www.olivieraubert.net/vlc/python-ctypes/)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [PyInstaller Documentation](https://pyinstaller.org/)

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2025 | Product Team | Initial PRD creation |

---

*This document is maintained in the TV Viewer repository at `docs/PRD.md`*
'''

prd_path = os.path.join(docs_dir, "PRD.md")
with open(prd_path, 'w', encoding='utf-8') as f:
    f.write(prd_content)
print(f"Created: {prd_path}")
print("Done!")
