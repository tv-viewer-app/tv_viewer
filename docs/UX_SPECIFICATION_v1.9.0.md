# TV Viewer v1.9.0 — New Ubuntu UX Design Specification

## Design Philosophy
**"Turn on the TV, not a dashboard."**

Shift from IT monitoring dashboard → living room TV experience.
Hide the plumbing. Show the channels.

---

## The 5 Big Changes

### 1. Single-Window Embedded Player (kills dual-window)
```
┌─────────────────────────────────────────────────────────┐
│ 🔍 Search...          [☰ Filters]  [⚙]    [🌙 Dark]   │ ← Top Bar (48px)
├────────┬────────────────────────────────────────────────┤
│ ★ Favs │                                                │
│ 📺 All │  ┌──────────────────────────────────────────┐  │
│ 📰News │  │                                          │  │
│ ⚽Sport│  │           EMBEDDED VLC PLAYER             │  │
│ 🎬Ent  │  │           (or Channel Grid)               │  │
│ 🌍Cntry│  │                                          │  │
│ 📻Radio│  └──────────────────────────────────────────┘  │
│        │  ▶ Channel Name    🔊━━━━━●  ⛶ Fullscreen    │ ← Controls (40px)
│        ├────────────────────────────────────────────────┤
│        │  [CNN] [BBC] [Sport5] [Kan11] [+15 more ▸]    │ ← Channel Strip
├────────┴────────────────────────────────────────────────┤
│ ✓ 3,421 channels  •  Scanning... 67%  •  v1.8.2        │ ← Status Bar (24px)
└─────────────────────────────────────────────────────────┘
```

**Modes:**
- **Browse Mode** (default on launch): Channel grid fills main area
- **Watch Mode** (click a channel): VLC player fills main area, channel strip below
- **Pop-out**: Button to detach player to separate window (keeps current PlayerWindow)

### 2. Navigation Rail (56px collapsed → 200px expanded)
Replaces the 300px sidebar. Icons only by default:
- ★ Favorites (pinned at top, always visible)
- 📺 All Channels
- 📰 📻 ⚽ 🎬 Category icons
- 🌍 Countries (expandable)
- ⚙ Settings

Click hamburger (☰) or hover to expand with text labels.
On wide screens (≥1800px): auto-expand.

### 3. Channel Cards Instead of Spreadsheet
Replace `ttk.TreeView` with `CTkScrollableFrame` containing channel cards:

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ [CNN Logo]       │  │ [BBC Logo]       │  │ [Sport 5 Logo]  │
│                  │  │                  │  │                  │
│ CNN International│  │ BBC World News   │  │ Sport 5          │
│ News • 🟢 Live  │  │ News • 🟢 Live   │  │ Sports • 🟢 Live │
│ United States    │  │ United Kingdom   │  │ Israel            │
│         [★] [▶] │  │         [★] [▶] │  │         [★] [▶]  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Card size:** ~180×140px (fits 5-6 per row on 1200px)
**Shows:** Logo (from M3U `tvg-logo`), name, category, status badge, country
**Actions:** Click = play, ★ = favorite, right-click = details

### 4. Instant Launch with Cached Channels
- Show cached working channels IMMEDIATELY on startup
- Background scan is invisible (just a thin progress bar in status bar)
- "Hide Failed" and "Hide Checking" ON by default (show only working)
- First-run: auto-detect locale, pre-filter to user's country

### 5. Favorites & Recently Watched
- ★ Favorites section pinned at top of channel grid
- Recently Watched (last 10) shown on home screen
- Stored in local JSON (like Flutter version's favorites_service)

---

## Component Specifications

### Top Bar (48px)
| Element | Widget | Width | Behavior |
|---------|--------|-------|----------|
| Search | CTkEntry | flex | Filters channels in real-time, searches name + country + category |
| Filters | CTkButton | 90px | Opens filter popover (category, country, media type, status) |
| Settings | CTkButton | 36px | Opens settings panel |
| Theme | CTkSwitch | 36px | Dark/light toggle |

### Navigation Rail (56px / 200px)
| State | Width | Content |
|-------|-------|---------|
| Collapsed | 56px | Icons only, tooltip on hover |
| Expanded | 200px | Icons + text labels |
| Categories | nested | Expandable accordion under each section |

### Channel Grid (main area)
| Property | Value |
|----------|-------|
| Widget | CTkScrollableFrame |
| Card size | 180×140px |
| Gap | 8px |
| Columns | auto (fill available width) |
| Loading | Batch 50 at a time, lazy scroll |
| Logo | CTkImage from tvg-logo URL, 64×64 fallback icon |
| Status | 🟢 green dot = working, hide others by default |

### Embedded Player (Watch Mode)
| Property | Value |
|----------|-------|
| Widget | tk.Canvas (VLC embed) |
| Min height | 360px |
| Controls | CTkFrame with play/pause, volume CTkSlider, fullscreen, cast, pop-out |
| Channel strip | Horizontal CTkScrollableFrame below player, showing nearby channels as mini-cards |

### Status Bar (24px)
| Element | Content |
|---------|---------|
| Left | Channel count: "✓ 3,421 working channels" |
| Center | Scan progress (if active): thin CTkProgressBar + "67%" |
| Right | App version |

---

## Interaction Flows

### First Launch
1. App opens → shows "Welcome! Select your region" (CTkOptionMenu with countries)
2. Pre-loads cached channels for selected region
3. Shows channel card grid filtered to region
4. Background scan starts silently

### Daily Use
1. App opens → Favorites shown at top → Recently Watched below
2. Click any channel → switches to Watch Mode (embedded player)
3. ↑↓ keys or channel strip to surf channels while watching
4. ★ button to favorite current channel

### Channel Surfing (Watch Mode)
1. Player fills main area, channel strip shows horizontally scrollable cards below
2. Click next channel in strip → player switches instantly (VLC set_media)
3. Arrow keys (↑↓) cycle through channels in current filter
4. Escape → back to Browse Mode

---

## Responsive Breakpoints

| Breakpoint | Window Width | Layout |
|------------|-------------|--------|
| Compact | 960–1100px | Nav rail collapsed (56px), no channel strip, player pops out |
| Standard | 1100–1600px | Nav rail collapsed, full grid/player, channel strip |
| Wide | 1600–1800px | Nav rail expanded (200px), full layout |
| Ultra-wide | 1800px+ | Nav rail expanded, larger cards (220×160) |

---

## Performance Improvements

| Problem | Solution |
|---------|----------|
| 14,000 TreeView rows lag | Card grid loads 50 at a time, lazy scroll |
| Scan animation redraws every 400ms | Replace with 4px CTkProgressBar (no canvas) |
| Category buttons recreated on switch | pack_forget/reuse instead of destroy/create |
| Thumbnail capture per-click | 500ms debounce, cache aggressively |
| Full channel list re-render on filter | Filter in-memory, update only visible cards |

---

## Visual Language

### Typography (Ubuntu-native)
| Role | Font | Size | Weight |
|------|------|------|--------|
| Card title | Ubuntu / Cantarell | 13px | Medium |
| Card subtitle | Ubuntu / Cantarell | 11px | Regular |
| Section header | Ubuntu / Cantarell | 16px | Bold |
| Status bar | Ubuntu / Cantarell | 11px | Regular |

### Colors (extend FluentColors)
| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| BG_PRIMARY | #F3F3F3 | #1E1E1E | Window background |
| BG_CARD | #FFFFFF | #2D2D2D | Channel cards |
| BG_CARD_HOVER | #F0F0F0 | #383838 | Card hover state |
| ACCENT | #0078D4 | #4CC2FF | Selected/active |
| LIVE_BADGE | #107C10 | #6CCB5F | Working/Live indicator |
| NAV_RAIL | #EBEBEB | #252525 | Navigation background |

### Spacing
| Token | Value | Usage |
|-------|-------|-------|
| CARD_GAP | 8px | Between channel cards |
| CARD_PADDING | 12px | Inside channel cards |
| SECTION_GAP | 16px | Between sections |
| NAV_ITEM_HEIGHT | 40px | Navigation rail items |

---

## Migration Path

### Phase 1: Layout restructure (main_window.py)
- Replace sidebar with NavigationRail component
- Add top bar with search
- Keep TreeView temporarily but add card view toggle

### Phase 2: Embedded player
- Add Watch Mode to MainWindow
- Keep pop-out option (existing PlayerWindow)
- Add channel strip component

### Phase 3: Channel cards
- Create ChannelCard widget
- Create ChannelGrid (CTkScrollableFrame with cards)
- Lazy loading + logo fetching

### Phase 4: Favorites & smart defaults
- Add FavoritesManager (JSON storage)
- Recently Watched tracking
- First-run country detection
- Default filters (hide failed/checking)

### Phase 5: Polish & performance
- Responsive breakpoints
- Dark mode support
- Keyboard navigation (channel surfing)
- Animation cleanup (remove scan canvas)
