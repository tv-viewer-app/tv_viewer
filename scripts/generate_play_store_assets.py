"""Generate Google Play Store listing artifacts for TV Viewer.

Outputs everything to ./play_store_assets/.

Required for upload:
  - feature_graphic.png  (1024x500)
  - phone/*.png          (5 screens, 1080x1920, 9:16)
  - tablet_7/*.png       (5 screens, 1200x2133, 9:16)
  - tablet_10/*.png      (5 screens, 1600x2844, 9:16)

Optional:
  - chromebook/*.png     (4 screens, 1920x1080, 16:9)
  - android_xr/*.png     (4 screens, 1920x1080, 16:9)
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# -----------------------------------------------------------------------------
# Brand
# -----------------------------------------------------------------------------
BRAND = "#1565C0"            # primary
BRAND_LIGHT = "#42A5F5"
BRAND_DARK = "#0D47A1"
BG = "#0E1116"               # near black
SURFACE = "#1A1F26"
SURFACE_2 = "#252B33"
BORDER = "#2F3640"
TEXT = "#FFFFFF"
TEXT_DIM = "#B8C2CC"
TEXT_MUTED = "#7A8693"
ACCENT = "#FFB300"           # favorite star
LIVE = "#E53935"

OUT = Path(__file__).resolve().parent.parent / "play_store_assets"
OUT.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# Font loader (Windows)
# -----------------------------------------------------------------------------
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def gradient(size, c1, c2, vertical=True):
    img = Image.new("RGB", size, c1)
    d = ImageDraw.Draw(img)
    w, h = size
    r1, g1, b1 = Image.new("RGB", (1, 1), c1).getpixel((0, 0))
    r2, g2, b2 = Image.new("RGB", (1, 1), c2).getpixel((0, 0))
    n = h if vertical else w
    for i in range(n):
        t = i / max(n - 1, 1)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        if vertical:
            d.line([(0, i), (w, i)], fill=(r, g, b))
        else:
            d.line([(i, 0), (i, h)], fill=(r, g, b))
    return img


def rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text_centered(draw, xy_box, text, fnt, fill=TEXT):
    x0, y0, x1, y1 = xy_box
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((x0 + x1 - tw) / 2, (y0 + y1 - th) / 2 - bbox[1]), text, font=fnt, fill=fill)


def logo_mark(size: int) -> Image.Image:
    """A stylised TV-with-play-button glyph."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # tv body
    pad = int(size * 0.08)
    rounded_rect(d, (pad, pad, size - pad, int(size * 0.78)),
                 radius=int(size * 0.12), fill=BRAND, outline=BRAND_LIGHT, width=max(2, size // 80))
    # screen
    sp = int(size * 0.16)
    rounded_rect(d, (sp, sp, size - sp, int(size * 0.70)),
                 radius=int(size * 0.06), fill=BG)
    # play triangle
    cx, cy = size // 2, int(size * 0.42)
    tri = int(size * 0.12)
    d.polygon([(cx - tri, cy - tri), (cx - tri, cy + tri), (cx + int(tri * 1.3), cy)], fill=BRAND_LIGHT)
    # stand
    d.rectangle((int(size * 0.42), int(size * 0.78), int(size * 0.58), int(size * 0.86)), fill=BRAND_DARK)
    d.rectangle((int(size * 0.32), int(size * 0.86), int(size * 0.68), int(size * 0.92)), fill=BRAND_DARK)
    return img


# =============================================================================
# 1. FEATURE GRAPHIC  1024x500
# =============================================================================
def make_feature_graphic():
    W, H = 1024, 500
    img = gradient((W, H), BRAND_DARK, BG)
    d = ImageDraw.Draw(img)

    # subtle radial highlight
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-200, -300, 700, 600), fill=(21, 101, 192, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(img)

    # logo
    lg = logo_mark(220)
    img.paste(lg, (60, (H - 220) // 2), lg)

    # title
    d.text((310, 130), "TV Viewer", font=font(78, bold=True), fill=TEXT)
    d.text((312, 220), "Stream IPTV. Anywhere.", font=font(34), fill=TEXT_DIM)

    # bullets
    bullets = ["Live TV  •  EPG Guide  •  Favorites  •  Cast & Map  •  Privacy-first"]
    d.text((312, 290), bullets[0], font=font(22), fill=BRAND_LIGHT)

    # device mockup on right
    mock_w, mock_h = 280, 380
    mx, my = W - mock_w - 60, (H - mock_h) // 2
    rounded_rect(d, (mx, my, mx + mock_w, my + mock_h), radius=24,
                 fill=SURFACE, outline=BORDER, width=2)
    rounded_rect(d, (mx + 14, my + 24, mx + mock_w - 14, my + mock_h - 24), radius=12, fill=BG)
    # play btn in centre
    cx, cy = mx + mock_w // 2, my + mock_h // 2
    d.ellipse((cx - 36, cy - 36, cx + 36, cy + 36), fill=BRAND)
    d.polygon([(cx - 12, cy - 18), (cx - 12, cy + 18), (cx + 18, cy)], fill=TEXT)
    # mock channel rows below play
    for i in range(3):
        ry = cy + 60 + i * 28
        d.rectangle((mx + 30, ry, mx + mock_w - 30, ry + 18), fill=SURFACE_2)
        d.rectangle((mx + 30, ry, mx + 50, ry + 18), fill=BRAND_LIGHT)

    img.save(OUT / "feature_graphic.png", "PNG", optimize=True)
    print(f"  feature_graphic.png  {W}x{H}")


# =============================================================================
# Screen renderers — drawn into an arbitrary canvas
# =============================================================================
def _draw_status_bar(d, W, top=0):
    # status bar
    d.rectangle((0, top, W, top + 36), fill=BG)
    d.text((24, top + 8), "9:41", font=font(18, bold=True), fill=TEXT)
    d.text((W - 80, top + 8), "100%", font=font(16), fill=TEXT_DIM)


def _draw_app_bar(d, W, title, top, action_icons=("⋮",)):
    h = 64
    d.rectangle((0, top, W, top + h), fill=SURFACE)
    d.rectangle((0, top + h - 1, W, top + h), fill=BORDER)
    d.text((24, top + 18), title, font=font(26, bold=True), fill=TEXT)
    # accent underline on title
    bbox = d.textbbox((24, top + 18), title, font=font(26, bold=True))
    d.rectangle((bbox[0], bbox[3] + 2, bbox[0] + 40, bbox[3] + 5), fill=BRAND_LIGHT)
    return top + h


def _draw_bottom_nav(d, W, H, active=0):
    nh = 72
    top = H - nh
    d.rectangle((0, top, W, H), fill=SURFACE)
    d.rectangle((0, top, W, top + 1), fill=BORDER)
    items = [("Channels", "▦"), ("Guide", "▤"), ("Favorites", "★"), ("Settings", "⚙")]
    iw = W / len(items)
    for i, (label, icon) in enumerate(items):
        cx = int(iw * i + iw / 2)
        col = BRAND_LIGHT if i == active else TEXT_MUTED
        d.text((cx - 8, top + 12), icon, font=font(24), fill=col)
        bbox = d.textbbox((0, 0), label, font=font(13))
        tw = bbox[2] - bbox[0]
        d.text((cx - tw // 2, top + 44), label, font=font(13), fill=col)


def render_channel_list(W, H):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    _draw_status_bar(d, W)
    y = _draw_app_bar(d, W, "TV Viewer", 36)
    # search
    sb_h = 48
    rounded_rect(d, (16, y + 12, W - 16, y + 12 + sb_h), 10, fill=SURFACE_2, outline=BORDER)
    d.text((44, y + 25), "🔍  Search channels…", font=font(18), fill=TEXT_MUTED)
    y += sb_h + 32

    # category chips
    chips = [("All", True), ("News", False), ("Sports", False), ("Movies", False), ("Kids", False)]
    cx = 16
    for label, active in chips:
        bbox = d.textbbox((0, 0), label, font=font(15, bold=True))
        tw = bbox[2] - bbox[0] + 28
        fill = BRAND if active else SURFACE_2
        rounded_rect(d, (cx, y, cx + tw, y + 36), 18, fill=fill,
                     outline=BORDER if not active else BRAND, width=1)
        d.text((cx + 14, y + 8), label, font=font(15, bold=True),
               fill=TEXT if active else TEXT_DIM)
        cx += tw + 10
    y += 56

    # channel rows
    channels = [
        ("BBC News", "News", LIVE, True),
        ("Sky Sports HD", "Sports", BRAND_LIGHT, False),
        ("Discovery", "Documentary", "#43A047", True),
        ("Cartoon Network", "Kids", "#8E24AA", False),
        ("Movie Central", "Movies", "#FB8C00", False),
        ("Al Jazeera", "News", LIVE, False),
        ("ESPN", "Sports", BRAND_LIGHT, False),
        ("History HD", "Documentary", "#43A047", False),
    ]
    row_h = 88
    bottom_limit = H - 90
    for name, cat, swatch, live in channels:
        if y + row_h > bottom_limit:
            break
        rounded_rect(d, (16, y, W - 16, y + row_h - 12), 12, fill=SURFACE)
        # logo box
        rounded_rect(d, (28, y + 12, 28 + 56, y + 12 + 56), 8, fill=swatch)
        d.text((40, y + 26), name[0], font=font(28, bold=True), fill=TEXT)
        # text
        d.text((104, y + 16), name, font=font(20, bold=True), fill=TEXT)
        d.text((104, y + 44), cat, font=font(14), fill=TEXT_MUTED)
        if live:
            rounded_rect(d, (W - 90, y + 18, W - 28, y + 42), 6, fill=LIVE)
            d.text((W - 78, y + 20), "LIVE", font=font(14, bold=True), fill=TEXT)
        # play icon
        d.text((W - 60, y + 52), "▶", font=font(18), fill=BRAND_LIGHT)
        y += row_h

    _draw_bottom_nav(d, W, H, active=0)
    return img


def render_player(W, H):
    img = Image.new("RGB", (W, H), "#000000")
    d = ImageDraw.Draw(img)
    # fake video: gradient + content silhouette
    video = gradient((W, int(H * 0.7)), "#102030", "#1A2A40")
    img.paste(video, (0, int(H * 0.15)))
    d = ImageDraw.Draw(img)
    # studio silhouette
    cx = W // 2
    d.ellipse((cx - 80, int(H * 0.35), cx + 80, int(H * 0.55)), fill="#2A3A55")
    d.rectangle((cx - 130, int(H * 0.5), cx + 130, int(H * 0.7)), fill="#1F2D45")
    # NEWS chyron
    d.rectangle((40, int(H * 0.62), W - 40, int(H * 0.70)), fill=LIVE)
    d.text((60, int(H * 0.635)), "BREAKING NEWS  •  LIVE", font=font(22, bold=True), fill=TEXT)

    # top OSD bar
    osd_top = Image.new("RGBA", (W, 100), (0, 0, 0, 180))
    img.paste(osd_top, (0, 36), osd_top)
    d = ImageDraw.Draw(img)
    d.text((24, 50), "← BBC News", font=font(22, bold=True), fill=TEXT)
    d.text((24, 84), "News  •  Channel 101", font=font(15), fill=TEXT_DIM)
    rounded_rect(d, (W - 90, 56, W - 24, 96), 8, fill=LIVE)
    d.text((W - 76, 64), "LIVE", font=font(18, bold=True), fill=TEXT)

    # bottom OSD controls
    osd_h = 200
    osd = Image.new("RGBA", (W, osd_h), (0, 0, 0, 200))
    img.paste(osd, (0, H - osd_h), osd)
    d = ImageDraw.Draw(img)

    # progress
    py = H - osd_h + 30
    d.rectangle((40, py, W - 40, py + 6), fill="#3A4A60")
    d.rectangle((40, py, 40 + int((W - 80) * 0.6), py + 6), fill=BRAND_LIGHT)
    d.ellipse((40 + int((W - 80) * 0.6) - 8, py - 5, 40 + int((W - 80) * 0.6) + 8, py + 11), fill=BRAND_LIGHT)
    d.text((40, py + 18), "00:42:13", font=font(13), fill=TEXT_DIM)
    d.text((W - 110, py + 18), "01:10:00", font=font(13), fill=TEXT_DIM)

    # control row
    cy = H - osd_h + 100
    icons = ["⏮", "⏪", "▶", "⏩", "⏭"]
    sizes = [32, 32, 56, 32, 32]
    cols = [TEXT_DIM, TEXT_DIM, TEXT, TEXT_DIM, TEXT_DIM]
    spacing = W // (len(icons) + 1)
    for i, (ic, sz, col) in enumerate(zip(icons, sizes, cols)):
        if ic == "▶":
            d.ellipse((spacing * (i + 1) - 36, cy - 36, spacing * (i + 1) + 36, cy + 36), fill=BRAND)
            d.polygon([(spacing * (i + 1) - 12, cy - 18),
                       (spacing * (i + 1) - 12, cy + 18),
                       (spacing * (i + 1) + 18, cy)], fill=TEXT)
        else:
            d.text((spacing * (i + 1) - sz // 2, cy - sz // 2), ic, font=font(sz), fill=col)

    # bottom action row
    by = H - 36
    d.text((40, by - 16), "★ Favorite", font=font(15), fill=ACCENT)
    d.text((W // 2 - 40, by - 16), "🔊  100%", font=font(15), fill=TEXT_DIM)
    d.text((W - 130, by - 16), "📺 Cast", font=font(15), fill=TEXT_DIM)
    return img


def render_guide(W, H):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    _draw_status_bar(d, W)
    y = _draw_app_bar(d, W, "Guide", 36)
    # date row
    d.text((24, y + 12), "Today  •  Tuesday, May 5", font=font(17), fill=TEXT_DIM)
    rounded_rect(d, (W - 130, y + 8, W - 16, y + 40), 8, fill=BRAND, outline=None)
    d.text((W - 110, y + 14), "Now ▾", font=font(15, bold=True), fill=TEXT)
    y += 56

    # time header
    th = 32
    d.rectangle((0, y, W, y + th), fill=SURFACE_2)
    times = ["09:00", "09:30", "10:00", "10:30"]
    col_w = (W - 140) // 4
    for i, t in enumerate(times):
        d.text((140 + col_w * i + 8, y + 8), t, font=font(13, bold=True), fill=TEXT_DIM)
    y += th

    # rows
    rows = [
        ("BBC News", LIVE, [("News at 9", 0.4, True), ("Hard Talk", 0.3), ("Click", 0.3)]),
        ("Sky Sports", BRAND_LIGHT, [("Live: PL Match", 0.7, True), ("Highlights", 0.3)]),
        ("Discovery", "#43A047", [("Wild Earth", 0.5, True), ("Mythbusters", 0.5)]),
        ("History", "#FB8C00", [("Ancient Rome", 0.5, True), ("WW2 Stories", 0.5)]),
        ("Cartoon", "#8E24AA", [("Adventure Time", 0.4, True), ("Looney Tunes", 0.3), ("Ben 10", 0.3)]),
        ("ESPN", BRAND_LIGHT, [("SportsCenter", 0.5, True), ("Live: NBA", 0.5)]),
        ("CNN", LIVE, [("Anderson Cooper", 0.6, True), ("Amanpour", 0.4)]),
    ]
    rh = 64
    bottom_limit = H - 90
    for ch_name, swatch, progs in rows:
        if y + rh > bottom_limit:
            break
        d.rectangle((0, y, 140, y + rh), fill=SURFACE)
        rounded_rect(d, (12, y + 10, 12 + 36, y + 10 + 36), 6, fill=swatch)
        d.text((22, y + 18), ch_name[0], font=font(20, bold=True), fill=TEXT)
        d.text((58, y + 14), ch_name, font=font(14, bold=True), fill=TEXT)
        d.text((58, y + 34), "Live", font=font(11), fill=TEXT_MUTED)
        # programs
        x = 140
        avail = W - 140
        for prog in progs:
            name, frac = prog[0], prog[1]
            now = len(prog) > 2 and prog[2]
            pw = int(avail * frac)
            fill = BRAND if now else SURFACE
            rounded_rect(d, (x + 2, y + 4, x + pw - 2, y + rh - 4), 6, fill=fill,
                         outline=BRAND_LIGHT if now else BORDER, width=1)
            d.text((x + 10, y + 10), name, font=font(13, bold=True), fill=TEXT)
            d.text((x + 10, y + 32), "30 min", font=font(11), fill=TEXT_DIM if now else TEXT_MUTED)
            x += pw
        y += rh
        d.rectangle((0, y - 1, W, y), fill=BORDER)

    _draw_bottom_nav(d, W, H, active=1)
    return img


def render_favorites(W, H):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    _draw_status_bar(d, W)
    y = _draw_app_bar(d, W, "Favorites", 36)
    d.text((24, y + 12), "Your starred channels", font=font(15), fill=TEXT_MUTED)
    y += 44

    # grid 2 cols
    cols = 2
    pad = 16
    gap = 14
    cw = (W - pad * 2 - gap * (cols - 1)) // cols
    ch = int(cw * 0.85)
    favs = [
        ("BBC News", "News", LIVE),
        ("Sky Sports", "Sports", BRAND_LIGHT),
        ("Discovery", "Docs", "#43A047"),
        ("HBO Max", "Movies", "#8E24AA"),
        ("ESPN", "Sports", BRAND_LIGHT),
        ("Cartoon", "Kids", "#FB8C00"),
    ]
    bottom_limit = H - 90
    for i, (n, c, sw) in enumerate(favs):
        col = i % cols
        row = i // cols
        x = pad + col * (cw + gap)
        cy = y + row * (ch + gap)
        if cy + ch > bottom_limit:
            break
        rounded_rect(d, (x, cy, x + cw, cy + ch), 14, fill=SURFACE, outline=BORDER)
        rounded_rect(d, (x, cy, x + cw, cy + int(ch * 0.6)), 14, fill=sw)
        # center letter
        bbox = d.textbbox((0, 0), n[0], font=font(72, bold=True))
        tw, th_ = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text((x + (cw - tw) // 2, cy + int(ch * 0.6) // 2 - th_ // 2 - 8),
               n[0], font=font(72, bold=True), fill=TEXT)
        # star
        d.text((x + cw - 36, cy + 12), "★", font=font(24), fill=ACCENT)
        # text
        d.text((x + 14, cy + int(ch * 0.6) + 12), n, font=font(17, bold=True), fill=TEXT)
        d.text((x + 14, cy + int(ch * 0.6) + 36), c, font=font(13), fill=TEXT_MUTED)

    _draw_bottom_nav(d, W, H, active=2)
    return img


def render_settings_privacy(W, H):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    _draw_status_bar(d, W)
    y = _draw_app_bar(d, W, "Settings", 36)
    d.text((24, y + 12), "Privacy & data", font=font(15), fill=TEXT_MUTED)
    y += 50

    # privacy hero card
    rounded_rect(d, (16, y, W - 16, y + 220), 16, fill=SURFACE, outline=BORDER)
    # shield icon
    cx = W // 2
    d.ellipse((cx - 36, y + 20, cx + 36, y + 92), fill=BRAND)
    d.text((cx - 16, y + 38), "🛡", font=font(36), fill=TEXT)
    bbox = d.textbbox((0, 0), "Your privacy, your choice", font=font(22, bold=True))
    tw = bbox[2] - bbox[0]
    d.text(((W - tw) // 2, y + 110), "Your privacy, your choice", font=font(22, bold=True), fill=TEXT)
    sub = "One toggle controls all data sharing"
    bbox = d.textbbox((0, 0), sub, font=font(15))
    tw = bbox[2] - bbox[0]
    d.text(((W - tw) // 2, y + 142), sub, font=font(15), fill=TEXT_DIM)
    # master toggle
    tg_x = W // 2 + 60
    tg_y = y + 175
    d.rounded_rectangle((tg_x, tg_y, tg_x + 70, tg_y + 36), 18, fill=BRAND)
    d.ellipse((tg_x + 36, tg_y + 4, tg_x + 66, tg_y + 32), fill=TEXT)
    d.text((W // 2 - 110, tg_y + 6), "Help improve TV Viewer", font=font(15, bold=True), fill=TEXT)

    y += 240

    # individual rows (collapsed under master)
    items = [
        ("📊", "Anonymous analytics", "Crash & usage stats"),
        ("🌐", "Crowd-sourced channel DB", "Shared with community"),
        ("📍", "Approximate location", "For region-relevant lists"),
    ]
    bottom_limit = H - 90
    for icon, title, sub in items:
        if y + 76 > bottom_limit:
            break
        rounded_rect(d, (16, y, W - 16, y + 64), 12, fill=SURFACE, outline=BORDER)
        d.text((28, y + 18), icon, font=font(24), fill=BRAND_LIGHT)
        d.text((76, y + 12), title, font=font(17, bold=True), fill=TEXT)
        d.text((76, y + 36), sub, font=font(13), fill=TEXT_MUTED)
        d.text((W - 50, y + 22), "✓", font=font(22, bold=True), fill="#43A047")
        y += 76

    _draw_bottom_nav(d, W, H, active=3)
    return img


SCREENS = [
    ("01_channels", "Browse 1000+ live channels",   render_channel_list),
    ("02_player",   "Smooth playback with full OSD", render_player),
    ("03_guide",    "Built-in EPG TV guide",         render_guide),
    ("04_favorites","One-tap favorites",             render_favorites),
    ("05_privacy",  "Privacy-first  •  one toggle",  render_settings_privacy),
]


def add_caption(img: Image.Image, caption: str) -> Image.Image:
    """Overlay a marketing banner at the top of the screenshot."""
    W, H = img.size
    band_h = max(120, H // 12)
    banner = Image.new("RGBA", (W, band_h), (21, 101, 192, 235))
    img2 = img.copy()
    img2.paste(banner, (0, 0), banner)
    d = ImageDraw.Draw(img2)
    fnt = font(max(28, W // 32), bold=True)
    bbox = d.textbbox((0, 0), caption, font=fnt)
    tw = bbox[2] - bbox[0]
    th_ = bbox[3] - bbox[1]
    d.text(((W - tw) // 2, (band_h - th_) // 2 - bbox[1]), caption, font=fnt, fill=TEXT)
    return img2


def make_screens(folder: str, W: int, H: int):
    out = OUT / folder
    out.mkdir(exist_ok=True)
    for fname, caption, fn in SCREENS:
        img = fn(W, H).convert("RGB")
        img = add_caption(img, caption)
        path = out / f"{fname}.png"
        img.save(path, "PNG", optimize=True)
        print(f"  {folder}/{path.name}  {W}x{H}")


def make_landscape_screens(folder: str, W: int, H: int):
    """Generate 16:9 landscape screens for Chromebook / XR."""
    out = OUT / folder
    out.mkdir(exist_ok=True)
    # Reuse player rendering at 16:9 native, plus desktop-style channel list
    for fname, caption, fn in SCREENS[:4]:
        # render in portrait then composite onto desktop frame
        portrait = fn(640, 1138).convert("RGB")
        canvas = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(canvas)
        # left rail / desktop chrome
        d.rectangle((0, 0, 240, H), fill=SURFACE)
        lg = logo_mark(72)
        canvas.paste(lg, (84, 30), lg)
        d.text((72, 110), "TV Viewer", font=font(22, bold=True), fill=TEXT)
        items = ["Channels", "Guide", "Favorites", "Recordings", "Settings"]
        for i, it in enumerate(items):
            yy = 180 + i * 56
            if i == SCREENS.index((fname, caption, fn)):
                d.rectangle((12, yy - 8, 228, yy + 32), fill=BRAND_DARK)
                d.rectangle((12, yy - 8, 16, yy + 32), fill=BRAND_LIGHT)
            d.text((36, yy), it, font=font(18), fill=TEXT)

        # paste phone preview to the right
        max_h = H - 80
        ph = portrait.resize((int(640 * max_h / 1138), max_h))
        canvas.paste(ph, ((W + 240 - ph.width) // 2, 40))
        canvas = add_caption(canvas, caption)
        canvas.save(out / f"{fname}.png", "PNG", optimize=True)
        print(f"  {folder}/{fname}.png  {W}x{H}")


# =============================================================================
def main():
    print(f"Output: {OUT}\n")
    print("Feature graphic:")
    make_feature_graphic()

    print("\nPhone (1080x1920):")
    make_screens("phone", 1080, 1920)

    print("\n7-inch tablet (1200x2133):")
    make_screens("tablet_7", 1200, 2133)

    print("\n10-inch tablet (1600x2844):")
    make_screens("tablet_10", 1600, 2844)

    print("\nChromebook (1920x1080):")
    make_landscape_screens("chromebook", 1920, 1080)

    print("\nAndroid XR (1920x1080):")
    make_landscape_screens("android_xr", 1920, 1080)

    print(f"\n✅ All assets written to: {OUT}")


if __name__ == "__main__":
    main()
