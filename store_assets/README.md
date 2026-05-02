# Play Store assets — TV Viewer

Generated mockups ready to upload to Google Play Console. All assets meet
Play Store dimension and aspect-ratio requirements.

| File | Dimensions | Format | Where to upload |
|------|-----------|--------|-----------------|
| `feature_graphic.png` | 1024 × 500 | PNG | Store listing → **Feature graphic** |
| `phone/*.png` (×5) | 1080 × 1920 | PNG, 9:16 | Store listing → **Phone screenshots** (5 shots — promotion-eligible: ≥4 at ≥1080 px) |
| `tablet_7/*.png` (×4) | 1080 × 1920 | PNG, 9:16 | Store listing → **7-inch tablet screenshots** |
| `tablet_10/*.png` (×4) | 1440 × 2560 | PNG, 9:16 | Store listing → **10-inch tablet screenshots** (both sides ≥1080) |
| `chromebook/*.png` (×5) | 1920 × 1080 | PNG, 16:9 | Store listing → **Chromebook screenshots** |

All PNGs are well under the 8 MB per-file limit. Total folder size ≈ 2 MB.

## Mockup themes

Each screenshot showcases one core scenario:

1. **Channels** — the TV-style channel grid with country/category filter chips
2. **Now Playing** — video player with OSD controls, channel info, "Up next"
3. **Search & Filter** — country / category / language filtering UI
4. **Privacy** — "no account, no ads, opt-in analytics, MIT-licensed" panel
5. **Submit Channel** — community contribution form (phone/Chromebook only)

## Regenerating

If the brand or messaging changes, edit `generate_assets.py` and re-run:

```powershell
python store_assets/generate_assets.py
```

The script is deterministic (`random.seed(7)`) so output is stable across runs.

## Not generated (optional Play Store fields)

- **Android XR screenshots** — TV Viewer does not target XR devices
- **Promo video** — produce separately if/when a YouTube trailer exists
- **Spatial / non-spatial XR video** — N/A

## Brand palette

Mockups use the TV Viewer brand colours from `docs/index.html`:

| Token | Hex | Use |
|-------|-----|-----|
| `BG` | `#0d1117` | Page background |
| `SURFACE` | `#161b22` | Cards |
| `SURFACE_2` | `#21262d` | Inputs / chips |
| `BORDER` | `#30363d` | Hairlines |
| `TEXT` | `#e6edf3` | Primary text |
| `TEXT_MUTED` | `#8b949e` | Secondary text |
| `ACCENT` | `#58a6ff` | Brand blue |
| `ACCENT_2` | `#79c0ff` | Hover / highlight |
| `SUCCESS` | `#3fb950` | LIVE indicator, ✓ |
| `DANGER` | `#f85149` | LIVE badge background |
