"""
TV Viewer Icon Generator — 3 Concept Options
Generates high-res 1024x1024 PNG icons for Android (Play Store requires 512x512 min).

Option A: "Globe Play" — Globe with play button, worldwide streaming
Option B: "Signal Screen" — Modern TV screen with broadcast waves  
Option C: "Prism Play" — Play button refracting into rainbow channels
"""

import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SIZE = 1024
CENTER = SIZE // 2
ANDROID_SIZES = {
    'xxxhdpi': 192,
    'xxhdpi': 144,
    'xhdpi': 96,
    'hdpi': 72,
    'mdpi': 48,
}


def lerp_color(c1, c2, t):
    """Linear interpolate between two RGB colors."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_gradient_rect(draw, bbox, color_top, color_bottom, steps=256):
    """Draw a vertical gradient rectangle."""
    x0, y0, x1, y1 = bbox
    h = y1 - y0
    for i in range(steps):
        t = i / (steps - 1)
        y_start = y0 + int(h * i / steps)
        y_end = y0 + int(h * (i + 1) / steps)
        color = lerp_color(color_top, color_bottom, t)
        draw.rectangle([x0, y_start, x1, y_end], fill=color)


def draw_radial_gradient(img, center, radius, color_center, color_edge):
    """Draw a radial gradient on an image."""
    pixels = img.load()
    cx, cy = center
    for y in range(max(0, cy - radius), min(img.height, cy + radius)):
        for x in range(max(0, cx - radius), min(img.width, cx + radius)):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if dist <= radius:
                t = dist / radius
                r = int(color_center[0] + (color_edge[0] - color_center[0]) * t)
                g = int(color_center[1] + (color_edge[1] - color_center[1]) * t)
                b = int(color_center[2] + (color_edge[2] - color_center[2]) * t)
                a = int(color_center[3] + (color_edge[3] - color_center[3]) * t) if len(color_center) > 3 else 255
                pixels[x, y] = (r, g, b, a)


def create_rounded_mask(size, radius):
    """Create a rounded rectangle mask."""
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def draw_play_triangle(draw, center_x, center_y, size, color, outline=None, outline_width=0):
    """Draw a play triangle (equilateral-ish, pointing right)."""
    h = size
    w = size * 0.866  # sqrt(3)/2
    # Shift right slightly for optical centering
    offset_x = size * 0.08
    points = [
        (center_x - w / 2 + offset_x, center_y - h / 2),
        (center_x + w / 2 + offset_x, center_y),
        (center_x - w / 2 + offset_x, center_y + h / 2),
    ]
    draw.polygon(points, fill=color, outline=outline, width=outline_width)
    return points


# ============================================================
# OPTION A: "Globe Play" — World + Play button
# UVP: 8000+ channels WORLDWIDE, global streaming
# Colors: Deep space blue → electric cyan gradient
# ============================================================
def generate_option_a():
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background: rounded square with deep gradient
    bg = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)

    # Draw gradient background
    for y in range(SIZE):
        t = y / SIZE
        # Deep navy to rich blue
        r = int(8 + (15 - 8) * t)
        g = int(20 + (35 - 20) * t)
        b = int(60 + (90 - 60) * t)
        bg_draw.line([(0, y), (SIZE, y)], fill=(r, g, b, 255))

    mask = create_rounded_mask(SIZE, SIZE // 5)
    img.paste(bg, mask=mask)
    draw = ImageDraw.Draw(img)

    # Globe: circle with latitude/longitude lines
    globe_cx, globe_cy = CENTER, CENTER - 20
    globe_r = 340

    # Globe glow (soft cyan)
    glow = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw_radial_gradient(glow, (globe_cx, globe_cy), globe_r + 60,
                         (0, 180, 255, 50), (0, 100, 200, 0))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Globe outline
    globe_color = (0, 200, 255, 180)  # Cyan
    lw = 5

    # Outer circle
    draw.ellipse(
        [globe_cx - globe_r, globe_cy - globe_r,
         globe_cx + globe_r, globe_cy + globe_r],
        outline=globe_color, width=lw
    )

    # Latitude lines (horizontal ellipses)
    for lat in [-0.6, -0.3, 0, 0.3, 0.6]:
        y_offset = int(globe_r * lat)
        # Width of the latitude circle at this point
        w = int(globe_r * math.cos(math.asin(abs(lat))))
        draw.ellipse(
            [globe_cx - w, globe_cy + y_offset - int(globe_r * 0.05),
             globe_cx + w, globe_cy + y_offset + int(globe_r * 0.05)],
            outline=(0, 180, 240, 120), width=3
        )

    # Longitude lines (vertical ellipses)
    for angle in [-60, -20, 20, 60]:
        w = int(globe_r * math.cos(math.radians(angle)))
        draw.ellipse(
            [globe_cx - w, globe_cy - globe_r,
             globe_cx + w, globe_cy + globe_r],
            outline=(0, 180, 240, 120), width=3
        )

    # Play button in center of globe — white with slight glow
    play_size = 280

    # Play button glow
    glow2 = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    glow2_draw = ImageDraw.Draw(glow2)
    # Draw enlarged play for glow
    h = play_size + 40
    w = h * 0.866
    offset_x = (play_size + 40) * 0.08
    glow_pts = [
        (globe_cx - w / 2 + offset_x, globe_cy - h / 2),
        (globe_cx + w / 2 + offset_x, globe_cy),
        (globe_cx - w / 2 + offset_x, globe_cy + h / 2),
    ]
    glow2_draw.polygon(glow_pts, fill=(0, 200, 255, 40))
    glow2 = glow2.filter(ImageFilter.GaussianBlur(20))
    img = Image.alpha_composite(img, glow2)
    draw = ImageDraw.Draw(img)

    # Solid white play button
    draw_play_triangle(draw, globe_cx, globe_cy, play_size, (255, 255, 255, 240))

    # Small accent dots around globe (like stars/channels)
    import random
    random.seed(42)
    for _ in range(30):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(globe_r + 20, globe_r + 80)
        px = int(globe_cx + dist * math.cos(angle))
        py = int(globe_cy + dist * math.sin(angle))
        if 40 < px < SIZE - 40 and 40 < py < SIZE - 40:
            s = random.randint(3, 8)
            alpha = random.randint(100, 200)
            draw.ellipse([px - s, py - s, px + s, py + s],
                         fill=(0, 220, 255, alpha))

    return img


# ============================================================
# OPTION B: "Signal Screen" — Modern TV + broadcast waves
# UVP: Live TV streaming, real-time signal reception
# Colors: Purple → vibrant blue gradient, warm orange accents
# ============================================================
def generate_option_b():
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))

    # Background gradient: rich purple to deep blue
    bg = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(SIZE):
        t = y / SIZE
        r = int(40 + (10 - 40) * t)
        g = int(10 + (20 - 10) * t)
        b = int(80 + (100 - 80) * t)
        bg_draw.line([(0, y), (SIZE, y)], fill=(r, g, b, 255))

    mask = create_rounded_mask(SIZE, SIZE // 5)
    img.paste(bg, mask=mask)
    draw = ImageDraw.Draw(img)

    # TV screen shape — rounded rectangle
    screen_w, screen_h = 520, 380
    screen_x = CENTER - screen_w // 2
    screen_y = CENTER - screen_h // 2 - 40
    screen_radius = 30

    # Screen glow
    glow = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.rounded_rectangle(
        [screen_x - 20, screen_y - 20, screen_x + screen_w + 20, screen_y + screen_h + 20],
        radius=screen_radius + 10, fill=(100, 140, 255, 40)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(25))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Screen border (bright)
    draw.rounded_rectangle(
        [screen_x, screen_y, screen_x + screen_w, screen_y + screen_h],
        radius=screen_radius, outline=(140, 180, 255, 220), width=6
    )

    # Screen inner area — slightly lighter
    draw.rounded_rectangle(
        [screen_x + 8, screen_y + 8, screen_x + screen_w - 8, screen_y + screen_h - 8],
        radius=screen_radius - 4, fill=(20, 25, 60, 200)
    )

    # TV stand
    stand_w = 120
    stand_h = 30
    stand_x = CENTER - stand_w // 2
    stand_y = screen_y + screen_h + 10
    draw.rounded_rectangle(
        [stand_x, stand_y, stand_x + stand_w, stand_y + stand_h],
        radius=8, fill=(100, 140, 255, 150)
    )
    # Stand base
    base_w = 200
    base_h = 12
    base_x = CENTER - base_w // 2
    base_y = stand_y + stand_h
    draw.rounded_rectangle(
        [base_x, base_y, base_x + base_w, base_y + base_h],
        radius=6, fill=(100, 140, 255, 150)
    )

    # Play button inside screen
    play_cx = CENTER
    play_cy = screen_y + screen_h // 2
    play_size = 180
    draw_play_triangle(draw, play_cx, play_cy, play_size, (255, 255, 255, 230))

    # Broadcast signal waves (top-right of screen)
    wave_cx = screen_x + screen_w - 40
    wave_cy = screen_y + 40
    for i, r in enumerate([50, 90, 130]):
        alpha = 200 - i * 50
        color = (255, 165, 0, alpha)  # Orange signal waves
        # Draw arc (upper-right quadrant)
        draw.arc(
            [wave_cx - r, wave_cy - r, wave_cx + r, wave_cy + r],
            start=-120, end=-30, fill=color, width=6
        )

    # Small signal dot
    draw.ellipse([wave_cx - 8, wave_cy - 8, wave_cx + 8, wave_cy + 8],
                 fill=(255, 165, 0, 255))

    # Channel number indicators floating around
    # Small colored dots representing different channels
    channel_colors = [
        (255, 100, 100), (100, 255, 100), (255, 200, 50),
        (100, 200, 255), (255, 150, 200), (200, 150, 255),
    ]
    positions = [
        (screen_x + 50, screen_y + 50), (screen_x + screen_w - 80, screen_y + screen_h - 50),
        (screen_x + 60, screen_y + screen_h - 60), (screen_x + screen_w - 60, screen_y + 80),
        (screen_x + screen_w // 2 - 100, screen_y + 60),
        (screen_x + screen_w // 2 + 80, screen_y + screen_h - 50),
    ]
    for (px, py), color in zip(positions, channel_colors):
        draw.ellipse([px - 10, py - 10, px + 10, py + 10], fill=(*color, 150))

    return img


# ============================================================
# OPTION C: "Prism Play" — Play button refracting into rainbow
# UVP: One app → thousands of diverse channels, content variety
# Colors: Bold gradient play + rainbow light beams
# ============================================================
def generate_option_c():
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))

    # Background: dark gradient
    bg = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(SIZE):
        t = y / SIZE
        r = int(12 + (8 - 12) * t)
        g = int(12 + (10 - 12) * t)
        b = int(20 + (30 - 20) * t)
        bg_draw.line([(0, y), (SIZE, y)], fill=(r, g, b, 255))

    mask = create_rounded_mask(SIZE, SIZE // 5)
    img.paste(bg, mask=mask)
    draw = ImageDraw.Draw(img)

    # Rainbow light beams emanating from the right side of the play button
    beam_origin_x = CENTER + 80
    beam_origin_y = CENTER
    rainbow_colors = [
        (255, 50, 50),    # Red
        (255, 140, 0),    # Orange
        (255, 220, 0),    # Yellow
        (0, 220, 100),    # Green
        (0, 150, 255),    # Blue
        (100, 50, 255),   # Indigo
        (180, 50, 255),   # Violet
    ]

    # Draw beams as tapered lines going to the right edge
    beam_layer = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    beam_draw = ImageDraw.Draw(beam_layer)

    spread_angle = 50  # Total spread in degrees
    start_angle = -spread_angle / 2
    for i, color in enumerate(rainbow_colors):
        angle = start_angle + (spread_angle / (len(rainbow_colors) - 1)) * i
        angle_rad = math.radians(angle)

        # Beam endpoint
        beam_length = SIZE
        end_x = beam_origin_x + beam_length * math.cos(angle_rad)
        end_y = beam_origin_y + beam_length * math.sin(angle_rad)

        # Draw thick beam line
        for w in range(12, 0, -1):
            alpha = int(180 * (w / 12))
            beam_draw.line(
                [(beam_origin_x, beam_origin_y), (end_x, end_y)],
                fill=(*color, alpha), width=w * 3
            )

    # Apply gaussian blur to beams for glow effect
    beam_layer = beam_layer.filter(ImageFilter.GaussianBlur(8))

    # Mask beams to rounded rect
    beam_masked = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    beam_masked.paste(beam_layer, mask=mask)
    img = Image.alpha_composite(img, beam_masked)
    draw = ImageDraw.Draw(img)

    # Main play triangle — gradient from cyan to blue-purple
    play_size = 420

    # Create play button with internal gradient
    play_layer = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    play_draw = ImageDraw.Draw(play_layer)

    # Draw play button shadow
    shadow = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    h = play_size
    w = h * 0.866
    offset_x = play_size * 0.08
    shadow_pts = [
        (CENTER - w / 2 + offset_x + 8, CENTER - h / 2 + 8),
        (CENTER + w / 2 + offset_x + 8, CENTER + 8),
        (CENTER - w / 2 + offset_x + 8, CENTER + h / 2 + 8),
    ]
    shadow_draw.polygon(shadow_pts, fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(15))
    img = Image.alpha_composite(img, shadow)
    draw = ImageDraw.Draw(img)

    # Play button: draw with gradient by horizontal slices
    play_pts = [
        (CENTER - w / 2 + offset_x, CENTER - h / 2),
        (CENTER + w / 2 + offset_x, CENTER),
        (CENTER - w / 2 + offset_x, CENTER + h / 2),
    ]

    # Create gradient play button
    # Top color: bright cyan (#00D4FF)
    # Bottom color: electric blue (#0066FF)
    grad_top = (0, 212, 255)
    grad_bottom = (0, 80, 255)

    # Draw the play triangle row by row for gradient effect
    play_img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    play_pix = play_img.load()

    left_x = CENTER - w / 2 + offset_x
    right_x = CENTER + w / 2 + offset_x
    top_y = CENTER - h / 2
    bot_y = CENTER + h / 2

    for y in range(int(top_y), int(bot_y) + 1):
        t = (y - top_y) / h
        # Color gradient
        color = lerp_color(grad_top, grad_bottom, t)

        # Calculate x bounds of triangle at this y
        if y <= CENTER:
            # Top half: left edge stays, right edge moves right
            progress = (y - top_y) / (h / 2)
            x_right = left_x + (right_x - left_x) * progress
            x_left = left_x
        else:
            # Bottom half: left edge stays, right edge moves left
            progress = (y - CENTER) / (h / 2)
            x_right = right_x - (right_x - left_x) * progress
            x_left = left_x

        for x in range(int(x_left), int(x_right) + 1):
            if 0 <= x < SIZE and 0 <= y < SIZE:
                play_pix[x, y] = (*color, 245)

    img = Image.alpha_composite(img, play_img)
    draw = ImageDraw.Draw(img)

    # Bright edge highlight on play button
    draw.line([play_pts[0], play_pts[1]], fill=(150, 230, 255, 120), width=3)

    # Small sparkle/star effects
    sparkle_positions = [
        (CENTER + 200, CENTER - 180, 6), (CENTER - 250, CENTER + 150, 5),
        (CENTER + 280, CENTER + 100, 4), (CENTER - 200, CENTER - 200, 7),
        (CENTER + 100, CENTER - 280, 5), (CENTER - 150, CENTER + 250, 4),
    ]
    for sx, sy, ss in sparkle_positions:
        if 50 < sx < SIZE - 50 and 50 < sy < SIZE - 50:
            draw.ellipse([sx - ss, sy - ss, sx + ss, sy + ss],
                         fill=(255, 255, 255, 180))

    return img


def save_all():
    """Generate and save all 3 options."""
    options = [
        ('option_a_globe_play', generate_option_a, 'Globe Play — worldwide streaming'),
        ('option_b_signal_screen', generate_option_b, 'Signal Screen — live TV broadcast'),
        ('option_c_prism_play', generate_option_c, 'Prism Play — one app, rainbow of channels'),
    ]

    for name, gen_func, desc in options:
        print(f"\n🎨 Generating {desc}...")
        icon = gen_func()

        # Save 1024x1024 (Play Store / master)
        path_1024 = f'assets/icons/{name}_1024.png'
        icon.save(path_1024, 'PNG')
        print(f"   ✅ {path_1024} (1024x1024)")

        # Save 512x512 (Play Store listing)
        icon_512 = icon.resize((512, 512), Image.LANCZOS)
        path_512 = f'assets/icons/{name}_512.png'
        icon_512.save(path_512, 'PNG')
        print(f"   ✅ {path_512} (512x512)")

        # Save Android mipmap sizes
        for density, px in ANDROID_SIZES.items():
            icon_sized = icon.resize((px, px), Image.LANCZOS)
            path_mipmap = f'assets/icons/{name}_{density}_{px}.png'
            icon_sized.save(path_mipmap, 'PNG')
            print(f"   ✅ {path_mipmap} ({px}x{px})")

    print("\n✨ All icons generated in assets/icons/")


if __name__ == '__main__':
    save_all()
