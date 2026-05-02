"""
Play Store asset generator for TV Viewer.

Produces:
  - feature_graphic.png            1024x500   (Play Store feature graphic)
  - phone/01..05.png               1080x1920  (9:16 phone, eligible for promotion)
  - tablet_7/01..04.png            1200x1920  (9:16 7" tablet)
  - tablet_10/01..04.png           1600x2560  (10:16 10" tablet, all sides >=1080)
  - chromebook/01..05.png          1920x1080  (16:9 landscape Chromebook)

Run:   python store_assets/generate_assets.py
"""
from __future__ import annotations

import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

random.seed(7)

ROOT = Path(__file__).parent

# ── TV Viewer brand palette (from docs/index.html) ─────────────────────────
BG          = "#0d1117"
SURFACE     = "#161b22"
SURFACE_2   = "#21262d"
BORDER      = "#30363d"
TEXT        = "#e6edf3"
TEXT_MUTED  = "#8b949e"
ACCENT      = "#58a6ff"
ACCENT_2    = "#79c0ff"
SUCCESS     = "#3fb950"
WARNING     = "#d29922"
DANGER      = "#f85149"

# Tile palette for fake channel logos (high contrast, brand-friendly)
TILE_COLORS = [
    "#1f6feb", "#238636", "#a371f7", "#db61a2", "#f0883e",
    "#bf4b8a", "#3fb950", "#388bfd", "#d29922", "#7c3aed",
    "#0e7490", "#b91c1c", "#0891b2", "#9a3412", "#15803d",
]

CHANNEL_NAMES = [
    "BBC", "CNN", "RTL", "ARD", "TF1", "Globo", "DW", "France 24",
    "NHK", "RAI", "ABC", "CTV", "M6", "ZDF", "Al Jazeera",
    "ARTE", "SBT", "RTÉ", "ORF", "TVE", "RT", "CGTN", "TRT",
    "CBC", "PBS", "Bloomberg", "Euronews", "TV5", "ANT1", "MTV",
]

# ── Font loading ────────────────────────────────────────────────────────────
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try Segoe UI on Windows, fall back to DejaVu Sans on others."""
    candidates = []
    if bold:
        candidates += [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/seguisb.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    candidates += [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


# ── Drawing helpers ─────────────────────────────────────────────────────────
def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore


def rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: str | None = None,
    outline: str | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text_centered(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((xy[0] - w // 2, xy[1] - h // 2 - bbox[1]), text, font=font, fill=fill)


def gradient_bg(size: tuple[int, int], top: str, bottom: str) -> Image.Image:
    img = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(img)
    t = hex_to_rgb(top)
    b = hex_to_rgb(bottom)
    h = size[1]
    for y in range(h):
        ratio = y / max(1, h - 1)
        r = int(t[0] + (b[0] - t[0]) * ratio)
        g = int(t[1] + (b[1] - t[1]) * ratio)
        bb = int(t[2] + (b[2] - t[2]) * ratio)
        draw.line([(0, y), (size[0], y)], fill=(r, g, bb))
    return img


def channel_tile(size: int, name: str, color: str) -> Image.Image:
    """Circular tile with channel acronym."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(2, size // 16)
    draw.ellipse([pad, pad, size - pad, size - pad], fill=color)
    # subtle inner ring
    draw.ellipse(
        [pad, pad, size - pad, size - pad],
        outline=(255, 255, 255, 40),
        width=max(1, size // 64),
    )
    short = name if len(name) <= 4 else "".join(w[0] for w in name.split()[:3]).upper()
    if len(short) > 4:
        short = short[:4]
    font_size = max(10, int(size * (0.42 if len(short) <= 2 else 0.30 if len(short) == 3 else 0.24)))
    font = load_font(font_size, bold=True)
    text_centered(draw, (size // 2, size // 2), short, font, "#ffffff")
    return img


# ── Common chrome ───────────────────────────────────────────────────────────
def status_bar(draw: ImageDraw.ImageDraw, w: int, *, white: bool = True) -> None:
    """Mock Android status bar."""
    color = "#ffffff" if white else "#000000"
    f = load_font(28, bold=True)
    draw.text((40, 18), "9:41", font=f, fill=color)
    # right-side icons (signal / wifi / battery as simple shapes)
    f2 = load_font(22, bold=True)
    draw.text((w - 230, 22), "5G", font=f2, fill=color)
    draw.rectangle([w - 180, 28, w - 130, 46], outline=color, width=2)
    draw.rectangle([w - 130, 32, w - 122, 42], fill=color)
    # battery
    draw.rectangle([w - 100, 26, w - 50, 48], outline=color, width=2)
    draw.rectangle([w - 50, 31, w - 44, 43], fill=color)
    draw.rectangle([w - 98, 28, w - 70, 46], fill=color)


def app_header(draw: ImageDraw.ImageDraw, w: int, y: int = 80) -> int:
    """TV Viewer top bar. Returns the y-coordinate where content should start."""
    draw.text((40, y), "📺", font=load_font(48), fill=ACCENT)
    draw.text((100, y + 8), "TV Viewer", font=load_font(36, bold=True), fill=TEXT)
    # right side: search + menu
    rounded_rect(draw, (w - 260, y + 10, w - 110, y + 56), 23,
                 fill=SURFACE_2, outline=BORDER, width=1)
    draw.text((w - 240, y + 18), "🔍 Search", font=load_font(20), fill=TEXT_MUTED)
    rounded_rect(draw, (w - 90, y + 10, w - 40, y + 56), 12,
                 fill=SURFACE_2, outline=BORDER, width=1)
    draw.text((w - 78, y + 14), "≡", font=load_font(32, bold=True), fill=TEXT)
    return y + 90


def caption_card(
    img: Image.Image,
    title: str,
    subtitle: str,
    y_pct: float = 0.04,
) -> None:
    """Draw a translucent caption card at top of an image."""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    box_h = int(h * 0.16)
    y = int(h * y_pct)
    rounded_rect(od, (40, y, w - 40, y + box_h), 24,
                 fill=(13, 17, 23, 220),
                 outline=(88, 166, 255, 180), width=3)
    title_font = load_font(int(h * 0.038), bold=True)
    sub_font = load_font(int(h * 0.022))
    od.text((70, y + 28), title, font=title_font, fill=TEXT)
    od.text((70, y + 28 + int(h * 0.05)), subtitle, font=sub_font, fill=ACCENT_2)
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay), (0, 0))


# ── Mockup 1: Channel grid (TV-style UI) ────────────────────────────────────
def mockup_channel_grid(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = gradient_bg(size, BG, "#05080d").convert("RGBA")
    draw = ImageDraw.Draw(img)
    status_bar(draw, w)
    content_y = app_header(draw, w)

    # Filter chips
    chips = ["🌍 All", "🇺🇸 US", "🇬🇧 UK", "🇫🇷 FR", "🇩🇪 DE", "📰 News", "🎵 Music"]
    x = 40
    chip_y = content_y
    for i, c in enumerate(chips):
        f = load_font(20, bold=(i == 0))
        bbox = draw.textbbox((0, 0), c, font=f)
        cw = bbox[2] - bbox[0] + 36
        ch = 48
        rounded_rect(
            draw,
            (x, chip_y, x + cw, chip_y + ch),
            22,
            fill=ACCENT if i == 0 else SURFACE_2,
            outline=BORDER if i != 0 else None,
            width=1,
        )
        fill = "#ffffff" if i == 0 else TEXT_MUTED
        draw.text((x + 18, chip_y + 12), c, font=f, fill=fill)
        x += cw + 12
        if x > w - 200:
            break

    # Section title
    section_y = chip_y + 80
    draw.text((40, section_y), "📍 Local Channels", font=load_font(28, bold=True), fill=TEXT)
    draw.text((40, section_y + 42), "From your country, updated by the community",
              font=load_font(18), fill=TEXT_MUTED)

    # Channel grid
    grid_y = section_y + 100
    cols = 3
    tile_size = (w - 40 * 2 - 30 * (cols - 1)) // cols
    label_font = load_font(int(tile_size * 0.13), bold=True)
    sub_font = load_font(int(tile_size * 0.10))

    rows = (h - grid_y - 80) // (tile_size + 60)
    rows = max(2, min(rows, 4))

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cx = 40 + c * (tile_size + 30)
            cy = grid_y + r * (tile_size + 60)
            color = TILE_COLORS[idx % len(TILE_COLORS)]
            name = CHANNEL_NAMES[idx % len(CHANNEL_NAMES)]
            # Card background
            rounded_rect(
                draw,
                (cx - 10, cy - 10, cx + tile_size + 10, cy + tile_size + 70),
                18,
                fill=SURFACE,
                outline=BORDER,
                width=1,
            )
            tile = channel_tile(tile_size, name, color)
            img.paste(tile, (cx, cy), tile)
            # Label
            text_centered(draw, (cx + tile_size // 2, cy + tile_size + 22),
                          name, label_font, TEXT)
            text_centered(draw, (cx + tile_size // 2, cy + tile_size + 48),
                          "● LIVE", sub_font, SUCCESS)
            idx += 1

    # Bottom nav
    nav_h = 110
    nav_y = h - nav_h
    rounded_rect(draw, (0, nav_y, w, h), 0, fill=SURFACE)
    draw.line([(0, nav_y), (w, nav_y)], fill=BORDER, width=2)
    nav_items = [("📺", "Channels", True), ("⭐", "Favorites", False),
                 ("🔍", "Search", False), ("⚙", "Settings", False)]
    nav_w = w // len(nav_items)
    for i, (icon, label, active) in enumerate(nav_items):
        ix = i * nav_w + nav_w // 2
        col = ACCENT if active else TEXT_MUTED
        text_centered(draw, (ix, nav_y + 32), icon, load_font(28), col)
        text_centered(draw, (ix, nav_y + 72), label, load_font(16, bold=active), col)

    return img


# ── Mockup 2: Now playing / video player with OSD ───────────────────────────
def mockup_now_playing(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, BG)
    draw = ImageDraw.Draw(img)

    # Fake "video" area (top half) — gradient + abstract shapes
    video_h = int(h * 0.55)
    video = gradient_bg((w, video_h), "#0d2942", "#1f6feb")
    img.paste(video, (0, 0))
    draw_v = ImageDraw.Draw(img)

    # Decorative noise/glow shapes for the "live broadcast" look
    for _ in range(6):
        cx = random.randint(0, w)
        cy = random.randint(0, video_h)
        r = random.randint(80, 240)
        glow = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse((0, 0, r * 2, r * 2), fill=(121, 192, 255, 60))
        glow = glow.filter(ImageFilter.GaussianBlur(40))
        img.paste(glow, (cx - r, cy - r), glow)

    # LIVE badge
    rounded_rect(draw_v, (40, 100, 170, 150), 12, fill=DANGER)
    draw_v.text((58, 110), "● LIVE", font=load_font(24, bold=True), fill="#ffffff")

    # Channel name overlay center
    text_centered(draw_v, (w // 2, video_h // 2 - 40), "BBC News",
                  load_font(72, bold=True), "#ffffff")
    text_centered(draw_v, (w // 2, video_h // 2 + 30),
                  "World news at the top of the hour",
                  load_font(28), "#cce4ff")

    # OSD controls bar at the bottom of the video
    osd_y = video_h - 120
    rounded_rect(draw_v, (40, osd_y, w - 40, osd_y + 90), 18,
                 fill=(0, 0, 0, 180))
    # Progress bar
    draw_v.rectangle((70, osd_y + 18, w - 70, osd_y + 26), fill=BORDER)
    draw_v.rectangle((70, osd_y + 18, w // 2 + 100, osd_y + 26), fill=ACCENT)
    # Buttons
    btn_y = osd_y + 50
    for i, icon in enumerate(["⏮", "⏯", "⏭", "🔊", "⛶"]):
        cx = 80 + i * 90
        text_centered(draw_v, (cx, btn_y + 10), icon, load_font(28), "#ffffff")
    # Time display right side
    draw_v.text((w - 220, btn_y), "Live · HD",
                font=load_font(20, bold=True), fill="#ffffff")

    # Lower content: channel info + related
    info_y = video_h + 30
    draw.text((40, info_y), "BBC News", font=load_font(40, bold=True), fill=TEXT)
    draw.text((40, info_y + 56),
              "🇬🇧 United Kingdom · News · 1080p", font=load_font(22), fill=TEXT_MUTED)

    # Action chips
    chip_y = info_y + 110
    chips = [("⭐", "Favorite", False), ("📤", "Cast", False),
             ("🎬", "VLC", False), ("📋", "Copy URL", False)]
    x = 40
    for icon, label, active in chips:
        chip_w = 200
        rounded_rect(draw, (x, chip_y, x + chip_w, chip_y + 56), 16,
                     fill=SURFACE_2, outline=BORDER, width=1)
        draw.text((x + 18, chip_y + 14), f"{icon}  {label}",
                  font=load_font(20, bold=True), fill=TEXT)
        x += chip_w + 16
        if x > w - chip_w:
            break

    # "Up next" section
    up_y = chip_y + 100
    draw.text((40, up_y), "Up next on this channel",
              font=load_font(24, bold=True), fill=TEXT)
    for i in range(3):
        row_y = up_y + 60 + i * 90
        if row_y + 80 > h:
            break
        rounded_rect(draw, (40, row_y, w - 40, row_y + 78), 14,
                     fill=SURFACE, outline=BORDER, width=1)
        # thumbnail
        rounded_rect(draw, (54, row_y + 12, 54 + 80, row_y + 66), 8,
                     fill=TILE_COLORS[i])
        draw.text((158, row_y + 16),
                  ["World At One", "Newsnight", "BBC Breakfast"][i],
                  font=load_font(22, bold=True), fill=TEXT)
        draw.text((158, row_y + 44),
                  ["13:00 · 30 min", "22:30 · 50 min", "06:00 · 3 hr"][i],
                  font=load_font(18), fill=TEXT_MUTED)

    return img


# ── Mockup 3: Search & filter ───────────────────────────────────────────────
def mockup_search_filter(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, BG)
    draw = ImageDraw.Draw(img)
    status_bar(draw, w)

    # Header
    draw.text((40, 80), "🔍 Find Channels", font=load_font(40, bold=True), fill=TEXT)

    # Search input
    sb_y = 160
    rounded_rect(draw, (40, sb_y, w - 40, sb_y + 80), 18,
                 fill=SURFACE_2, outline=ACCENT, width=2)
    draw.text((70, sb_y + 24), "🔍", font=load_font(28), fill=ACCENT)
    draw.text((120, sb_y + 24), "news", font=load_font(28), fill=TEXT)
    draw.line([(180, sb_y + 22), (180, sb_y + 58)], fill=ACCENT, width=2)

    # Filter sections
    filter_y = sb_y + 120

    def filter_section(y: int, label: str, opts: list[tuple[str, bool]]) -> int:
        draw.text((40, y), label, font=load_font(22, bold=True), fill=TEXT_MUTED)
        y += 40
        x = 40
        row_h = 56
        for opt, sel in opts:
            f = load_font(20, bold=sel)
            bbox = draw.textbbox((0, 0), opt, font=f)
            cw = bbox[2] - bbox[0] + 36
            if x + cw > w - 40:
                x = 40
                y += row_h + 12
            rounded_rect(draw, (x, y, x + cw, y + row_h), 26,
                         fill=ACCENT if sel else SURFACE_2,
                         outline=BORDER if not sel else None, width=1)
            draw.text((x + 18, y + 16), opt,
                      font=f, fill="#ffffff" if sel else TEXT_MUTED)
            x += cw + 12
        return y + row_h + 24

    filter_y = filter_section(filter_y, "COUNTRY",
                              [("🌍 All", False), ("🇺🇸 USA", True),
                               ("🇬🇧 UK", True), ("🇫🇷 France", False),
                               ("🇩🇪 Germany", False), ("🇧🇷 Brazil", False),
                               ("🇮🇳 India", False), ("🇯🇵 Japan", False)])

    filter_y = filter_section(filter_y, "CATEGORY",
                              [("📰 News", True), ("🎵 Music", False),
                               ("🎬 Movies", False), ("🌎 General", False),
                               ("📚 Education", False), ("🍳 Lifestyle", False)])

    filter_y = filter_section(filter_y, "LANGUAGE",
                              [("English", True), ("Español", False),
                               ("Français", False), ("Deutsch", False),
                               ("中文", False), ("العربية", False)])

    # Results count
    rounded_rect(draw, (40, filter_y + 16, w - 40, filter_y + 96), 18,
                 fill=SURFACE, outline=ACCENT, width=2)
    draw.text((60, filter_y + 32), "✓ 247 channels match",
              font=load_font(28, bold=True), fill=ACCENT)
    draw.text((60, filter_y + 66), "Tap 'Show Results' to browse",
              font=load_font(18), fill=TEXT_MUTED)

    # Show results button
    btn_y = h - 200
    rounded_rect(draw, (40, btn_y, w - 40, btn_y + 90), 24, fill=ACCENT)
    text_centered(draw, (w // 2, btn_y + 45),
                  "Show 247 Results →",
                  load_font(28, bold=True), "#ffffff")

    return img


# ── Mockup 4: Privacy / open-source highlight ───────────────────────────────
def mockup_privacy(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = gradient_bg(size, "#05080d", "#0d1117").convert("RGBA")
    draw = ImageDraw.Draw(img)
    status_bar(draw, w)

    # Hero
    text_centered(draw, (w // 2, int(h * 0.13)),
                  "🛡️", load_font(int(h * 0.10)), ACCENT)
    text_centered(draw, (w // 2, int(h * 0.22)),
                  "Privacy First", load_font(int(h * 0.05), bold=True), TEXT)
    text_centered(draw, (w // 2, int(h * 0.27)),
                  "What we do — and don't do — with your data",
                  load_font(int(h * 0.022)), TEXT_MUTED)

    # Cards
    items = [
        ("✅", "No account required", "No email, no password, no sign-up.", SUCCESS),
        ("✅", "No advertising",
         "Zero ads, zero ad SDKs, zero advertising IDs.", SUCCESS),
        ("✅", "Analytics is opt-in",
         "Off by default. Anonymous if you turn it on.", SUCCESS),
        ("✅", "Open source — MIT licence",
         "Audit every line of code on GitHub.", SUCCESS),
        ("ℹ", "Anonymous channel-health pings",
         "URL hash only. No device ID. Helps prune dead streams.", ACCENT),
    ]

    card_y = int(h * 0.36)
    card_h = int(h * 0.10)
    for icon, title, desc, color in items:
        if card_y + card_h > h - 60:
            break
        rounded_rect(draw, (40, card_y, w - 40, card_y + card_h), 18,
                     fill=SURFACE, outline=BORDER, width=1)
        # icon disc
        disc_size = int(card_h * 0.55)
        disc_x = 70
        disc_y = card_y + (card_h - disc_size) // 2
        draw.ellipse([disc_x, disc_y, disc_x + disc_size, disc_y + disc_size],
                     fill=color)
        text_centered(draw, (disc_x + disc_size // 2, disc_y + disc_size // 2),
                      icon, load_font(int(disc_size * 0.55), bold=True), "#ffffff")
        # text
        draw.text((disc_x + disc_size + 30, card_y + 18),
                  title, font=load_font(int(card_h * 0.28), bold=True), fill=TEXT)
        draw.text((disc_x + disc_size + 30, card_y + 18 + int(card_h * 0.34)),
                  desc, font=load_font(int(card_h * 0.20)), fill=TEXT_MUTED)
        card_y += card_h + 20

    return img


# ── Mockup 5: Submit channel (community) ────────────────────────────────────
def mockup_submit_channel(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, BG)
    draw = ImageDraw.Draw(img)
    status_bar(draw, w)

    # Header
    draw.text((40, 80), "🤝 Submit a Channel",
              font=load_font(36, bold=True), fill=TEXT)
    draw.text((40, 130),
              "Found a working stream? Share it with the community.",
              font=load_font(20), fill=TEXT_MUTED)

    y = 200

    def field(y: int, label: str, value: str, hint: str = "") -> int:
        draw.text((40, y), label, font=load_font(20, bold=True), fill=TEXT_MUTED)
        rounded_rect(draw, (40, y + 32, w - 40, y + 32 + 76), 14,
                     fill=SURFACE_2, outline=BORDER, width=1)
        draw.text((60, y + 32 + 22), value, font=load_font(24), fill=TEXT)
        if hint:
            draw.text((40, y + 32 + 88), hint,
                      font=load_font(16), fill=TEXT_MUTED)
        return y + 32 + 76 + (28 if hint else 16) + 24

    y = field(y, "CHANNEL NAME", "France 24 English", "")
    y = field(y, "STREAM URL", "https://live.france24.com/hls/live/france24.m3u8",
              "Must be a publicly accessible HLS / DASH / MP4 URL.")
    y = field(y, "COUNTRY", "🇫🇷 France")
    y = field(y, "CATEGORY", "📰 News")
    y = field(y, "LANGUAGE", "English")

    # Notice
    notice_h = 130
    rounded_rect(draw, (40, y, w - 40, y + notice_h), 16,
                 fill="#1d2a44", outline=ACCENT, width=2)
    draw.text((60, y + 16), "ℹ Submission is anonymous",
              font=load_font(20, bold=True), fill=ACCENT_2)
    draw.text((60, y + 46),
              "No device ID is attached. The stream becomes",
              font=load_font(18), fill=TEXT)
    draw.text((60, y + 72),
              "part of the public catalogue and is auto-removed",
              font=load_font(18), fill=TEXT)
    draw.text((60, y + 98),
              "if it consistently fails for other users.",
              font=load_font(18), fill=TEXT)
    y += notice_h + 30

    # Submit button
    btn_h = 90
    if y + btn_h > h - 40:
        y = h - 40 - btn_h
    rounded_rect(draw, (40, y, w - 40, y + btn_h), 22, fill=ACCENT)
    text_centered(draw, (w // 2, y + btn_h // 2),
                  "Submit to community catalogue",
                  load_font(26, bold=True), "#ffffff")

    return img


# ── Mockup 6 (landscape): Chromebook channel browser ────────────────────────
def mockup_landscape_grid(size: tuple[int, int]) -> Image.Image:
    w, h = size  # landscape
    img = Image.new("RGBA", size, BG)
    draw = ImageDraw.Draw(img)

    # Sidebar
    sb_w = 280
    rounded_rect(draw, (0, 0, sb_w, h), 0, fill=SURFACE)
    draw.line([(sb_w, 0), (sb_w, h)], fill=BORDER, width=1)
    draw.text((30, 30), "📺", font=load_font(40), fill=ACCENT)
    draw.text((90, 38), "TV Viewer", font=load_font(28, bold=True), fill=TEXT)
    nav = [("📺", "Channels", True), ("⭐", "Favorites", False),
           ("📜", "History", False), ("🤝", "Submit", False),
           ("🛡", "Privacy", False), ("⚙", "Settings", False)]
    for i, (icon, label, active) in enumerate(nav):
        y = 130 + i * 64
        if active:
            rounded_rect(draw, (16, y, sb_w - 16, y + 52), 12,
                         fill="#1d2a44")
            draw.rectangle([16, y, 22, y + 52], fill=ACCENT)
        col = ACCENT if active else TEXT_MUTED
        draw.text((40, y + 12), icon, font=load_font(26), fill=col)
        draw.text((90, y + 16), label,
                  font=load_font(20, bold=active), fill=col)

    # Main area
    mx = sb_w + 40
    draw.text((mx, 30), "Channels", font=load_font(40, bold=True), fill=TEXT)
    draw.text((mx, 84), "20,096 streams · 33 countries · updated daily",
              font=load_font(18), fill=TEXT_MUTED)

    # Search bar top right
    sb_x = w - 380
    rounded_rect(draw, (sb_x, 36, w - 40, 86), 14,
                 fill=SURFACE_2, outline=BORDER, width=1)
    draw.text((sb_x + 16, 50), "🔍  Search 20,000+ channels",
              font=load_font(18), fill=TEXT_MUTED)

    # Filter chips row
    chips_y = 130
    chips = [("🌍 All", True), ("🇺🇸 USA", False), ("🇬🇧 UK", False),
             ("🇫🇷 France", False), ("🇩🇪 Germany", False),
             ("📰 News", False), ("🎵 Music", False), ("🌎 General", False)]
    x = mx
    for label, sel in chips:
        f = load_font(16, bold=sel)
        bbox = draw.textbbox((0, 0), label, font=f)
        cw = bbox[2] - bbox[0] + 28
        ch = 40
        rounded_rect(draw, (x, chips_y, x + cw, chips_y + ch), 18,
                     fill=ACCENT if sel else SURFACE_2,
                     outline=BORDER if not sel else None, width=1)
        draw.text((x + 14, chips_y + 10), label,
                  font=f, fill="#ffffff" if sel else TEXT_MUTED)
        x += cw + 10

    # Channel grid
    grid_x = mx
    grid_y = 200
    cols = 6
    gap = 24
    avail_w = w - grid_x - 40
    tile_size = (avail_w - gap * (cols - 1)) // cols
    label_font = load_font(int(tile_size * 0.13), bold=True)
    sub_font = load_font(int(tile_size * 0.10))

    rows = (h - grid_y - 40) // (tile_size + 60)
    rows = max(2, min(rows, 4))

    idx = 0
    for r in range(rows):
        for c in range(cols):
            cx = grid_x + c * (tile_size + gap)
            cy = grid_y + r * (tile_size + 60)
            color = TILE_COLORS[idx % len(TILE_COLORS)]
            name = CHANNEL_NAMES[idx % len(CHANNEL_NAMES)]
            tile = channel_tile(tile_size, name, color)
            img.paste(tile, (cx, cy), tile)
            text_centered(draw, (cx + tile_size // 2, cy + tile_size + 16),
                          name, label_font, TEXT)
            text_centered(draw, (cx + tile_size // 2, cy + tile_size + 38),
                          "● LIVE", sub_font, SUCCESS)
            idx += 1

    return img


# ── Feature graphic (1024x500) ──────────────────────────────────────────────
def feature_graphic() -> Image.Image:
    size = (1024, 500)
    w, h = size
    img = gradient_bg(size, "#0d1117", "#1d2a44").convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Decorative background tiles (right side)
    for i, (name, color) in enumerate(zip(CHANNEL_NAMES[:9], TILE_COLORS[:9])):
        c = i % 3
        r = i // 3
        cx = w - 320 + c * 100
        cy = 70 + r * 120
        tile = channel_tile(80, name, color)
        # fade them out
        tile.putalpha(Image.eval(tile.split()[3], lambda x: int(x * 0.55)))
        img.paste(tile, (cx, cy), tile)

    # Big title
    draw.text((50, 100), "📺", font=load_font(96), fill=ACCENT)
    draw.text((180, 110), "TV Viewer",
              font=load_font(80, bold=True), fill=TEXT)
    draw.text((180, 200), "Open-source IPTV player",
              font=load_font(34, bold=True), fill=ACCENT_2)
    # Tagline
    draw.text((50, 290),
              "Thousands of community-contributed live streams.",
              font=load_font(24), fill=TEXT)
    draw.text((50, 326),
              "No ads. No tracking. No account.",
              font=load_font(24), fill=TEXT_MUTED)

    # Pills row
    pills = [("🆓", "Free"), ("🛡", "Privacy-first"),
             ("🌍", "Worldwide"), ("📡", "Crowdsourced")]
    px = 50
    for icon, label in pills:
        f = load_font(20, bold=True)
        bbox = draw.textbbox((0, 0), f"{icon}  {label}", font=f)
        cw = bbox[2] - bbox[0] + 36
        rounded_rect(draw, (px, 400, px + cw, 452), 26,
                     fill=SURFACE_2, outline=ACCENT, width=2)
        draw.text((px + 18, 412), f"{icon}  {label}", font=f, fill=TEXT)
        px += cw + 16

    return img


# ── Generators per device ───────────────────────────────────────────────────
PHONE_MOCKUPS = [
    ("01_channels", mockup_channel_grid,
     "All your live streams", "Browse by country, category, language"),
    ("02_now_playing", mockup_now_playing,
     "Watch in a clean player", "Cast, favorite, or open in VLC"),
    ("03_search_filter", mockup_search_filter,
     "Filter the catalogue", "Country · category · language"),
    ("04_privacy", mockup_privacy,
     "Privacy by design", "Open source · MIT licensed"),
    ("05_submit", mockup_submit_channel,
     "Built by the community", "Submit channels you find"),
]


def render_all() -> None:
    print(f"Output dir: {ROOT}")

    # Feature graphic
    fg = feature_graphic()
    fg.convert("RGB").save(ROOT / "feature_graphic.png", optimize=True)
    print("  feature_graphic.png")

    # Phone (1080×1920, 9:16)
    for name, fn, title, sub in PHONE_MOCKUPS:
        img = fn((1080, 1920))
        img.convert("RGB").save(ROOT / "phone" / f"{name}.png", optimize=True)
        print(f"  phone/{name}.png")

    # 7-inch tablet (1200×1920 — keeps 16:9-friendly height-major aspect, all sides ≥1080)
    # Spec is "16:9 OR 9:16". Using portrait 9:16 1080×1920 is allowed for tablets too.
    for name, fn, _, _ in PHONE_MOCKUPS[:4]:
        img = fn((1080, 1920))
        img.convert("RGB").save(ROOT / "tablet_7" / f"{name}.png", optimize=True)
        print(f"  tablet_7/{name}.png")

    # 10-inch tablet (1440×2560 — 9:16 portrait, both sides ≥1080)
    for name, fn, _, _ in PHONE_MOCKUPS[:4]:
        img = fn((1440, 2560))
        img.convert("RGB").save(ROOT / "tablet_10" / f"{name}.png", optimize=True)
        print(f"  tablet_10/{name}.png")

    # Chromebook (1920×1080 landscape 16:9)
    for i, (name, _, _, _) in enumerate(PHONE_MOCKUPS[:5]):
        if i == 0 or i == 4:
            img = mockup_landscape_grid((1920, 1080))
        elif i == 1:
            img = mockup_now_playing((1920, 1080))
        elif i == 2:
            img = mockup_search_filter((1920, 1080))
        else:
            img = mockup_privacy((1920, 1080))
        img.convert("RGB").save(ROOT / "chromebook" / f"{name}.png", optimize=True)
        print(f"  chromebook/{name}.png")

    print("Done.")


if __name__ == "__main__":
    render_all()
