#!/usr/bin/env python3
"""Generate a 15-second vertical "fortune-telling slot" promo video.

Renders frames with Pillow and encodes them into an MP4 with ffmpeg,
sized for posting on X (H.264 / yuv420p, 1080x1920, ~15s).
"""
import math
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH, HEIGHT = 1080, 1920
FPS = 30
DURATION = 15
N_FRAMES = FPS * DURATION

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "_frames")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "slot_fortune_15s.mp4")

FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

# ---------- colors ----------
BG_TOP = (18, 10, 38)
BG_BOTTOM = (48, 16, 62)
GOLD = (255, 205, 90)
GOLD_DARK = (150, 105, 30)
WHITE = (255, 255, 255)
PANEL = (26, 14, 44)
PANEL_EDGE = (255, 205, 90)

SYMBOLS = [
    ("大吉", (255, 196, 64)),
    ("中吉", (255, 140, 140)),
    ("小吉", (140, 200, 255)),
    ("吉", (150, 255, 180)),
    ("末吉", (210, 160, 255)),
    ("凶", (150, 150, 165)),
]
WIN_INDEX = 0  # 大吉

CELL_H = 220
REEL_W = 280
GAP = 24
N_REELS = 3
TOTAL_W = REEL_W * N_REELS + GAP * (N_REELS - 1)
WIN_X0 = (WIDTH - TOTAL_W) // 2
WIN_TOP = 540
WIN_H = CELL_H * 3

SPIN_START = 42
STOP_FRAMES = [262, 300, 338]
Y_TOTAL = [220 * 113, 220 * 131, 220 * 149]  # each % 6 == 5 -> WIN_INDEX lands in middle row

FLASH_FRAME = STOP_FRAMES[-1]

random.seed(7)
STARS = [
    (random.uniform(0, WIDTH), random.uniform(0, HEIGHT * 0.34),
     random.uniform(0, math.tau), random.uniform(0.05, 0.16),
     random.uniform(1.2, 3.0))
    for _ in range(70)
]

CONFETTI = [
    (random.uniform(0, WIDTH), random.uniform(-HEIGHT, 0),
     random.uniform(0.35, 1.0), random.uniform(-2, 2),
     random.choice([GOLD, WHITE, (255, 140, 140), (150, 255, 180), (140, 200, 255)]),
     random.uniform(0, math.tau))
    for _ in range(140)
]

_font_cache = {}


def font(size):
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype(FONT_PATH, size)
    return _font_cache[size]


def ease_out_quart(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 4


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def draw_text_center(draw, cx, cy, text, size, fill, stroke_fill=None, stroke_width=0, alpha=255):
    f = font(size)
    bbox = draw.textbbox((0, 0), text, font=f, stroke_width=stroke_width)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = cx - w / 2 - bbox[0]
    y = cy - h / 2 - bbox[1]
    if alpha >= 255:
        draw.text((x, y), text, font=f, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
    else:
        txt_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(txt_layer)
        fc = fill + (alpha,) if len(fill) == 3 else fill
        sc = (stroke_fill + (alpha,)) if stroke_fill and len(stroke_fill) == 3 else stroke_fill
        d2.text((x, y), text, font=f, fill=fc, stroke_width=stroke_width, stroke_fill=sc)
        return txt_layer
    return None


def draw_background(img, draw, frame):
    for y in range(0, HEIGHT, 4):
        t = y / HEIGHT
        c = lerp_color(BG_TOP, BG_BOTTOM, t)
        draw.rectangle([0, y, WIDTH, y + 4], fill=c)

    for (sx, sy, phase, speed, r) in STARS:
        tw = 0.5 + 0.5 * math.sin(frame * speed + phase)
        a = int(60 + 140 * tw)
        rr = r * (0.7 + 0.5 * tw)
        draw.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=(255, 255, 255, a))

    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = WIDTH // 2, WIN_TOP + WIN_H // 2
    for i, rad in enumerate(range(520, 60, -20)):
        a = int(3 + i * 0.6)
        gd.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(255, 190, 90, a))
    img.alpha_composite(glow)


def draw_cabinet(img, draw):
    pad = 22
    x0, y0 = WIN_X0 - pad, WIN_TOP - pad
    x1, y1 = WIN_X0 + TOTAL_W + pad, WIN_TOP + WIN_H + pad
    draw.rounded_rectangle([x0 - 14, y0 - 70, x1 + 14, y1 + 14], radius=36,
                            fill=PANEL, outline=PANEL_EDGE, width=6)
    draw_text_center(draw, WIDTH // 2, y0 - 34, "占 い ス ロ ッ ト", 40, GOLD)
    for i in range(N_REELS):
        rx0 = WIN_X0 + i * (REEL_W + GAP)
        draw.rounded_rectangle([rx0 - 6, WIN_TOP - 6, rx0 + REEL_W + 6, WIN_TOP + WIN_H + 6],
                                radius=18, outline=GOLD_DARK, width=4)
    my = WIN_TOP + WIN_H // 2
    draw.line([x0 - 4, my, x0 + 18, my], fill=GOLD, width=4)
    draw.line([x1 - 18, my, x1 + 4, my], fill=GOLD, width=4)


def reel_speed(reel_idx, frame):
    start, stop = SPIN_START, STOP_FRAMES[reel_idx]
    if frame < start or frame >= stop:
        return 0.0
    span = stop - start
    t = (frame - start) / span
    dt = 1.0 / span
    e1 = ease_out_quart(t)
    e2 = ease_out_quart(min(t + dt, 1.0))
    return (e2 - e1) * Y_TOTAL[reel_idx]


def reel_y(reel_idx, frame):
    start, stop = SPIN_START, STOP_FRAMES[reel_idx]
    if frame < start:
        return 0.0
    if frame >= stop:
        return float(Y_TOTAL[reel_idx])
    t = (frame - start) / (stop - start)
    return ease_out_quart(t) * Y_TOTAL[reel_idx]


def draw_reel(img, draw, reel_idx, frame):
    rx0 = WIN_X0 + reel_idx * (REEL_W + GAP)
    cx = rx0 + REEL_W // 2
    y = reel_y(reel_idx, frame)
    speed = reel_speed(reel_idx, frame)

    win_box = (rx0, WIN_TOP, rx0 + REEL_W, WIN_TOP + WIN_H)

    if speed > 40:
        strip = Image.new("RGBA", (REEL_W, WIN_H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(strip)
        band_h = 26
        offset = int(y) % (band_h * len(SYMBOLS))
        for i in range(-1, WIN_H // band_h + 2):
            by = i * band_h - (offset % band_h)
            sym_idx = int((y // band_h) + i) % len(SYMBOLS)
            col = SYMBOLS[sym_idx][1]
            sd.rectangle([0, by, REEL_W, by + band_h - 4], fill=col + (200,))
        strip = strip.filter(ImageFilter.GaussianBlur(radius=min(10, speed / 12)))
        img.alpha_composite(strip, (rx0, WIN_TOP))
        streak = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        st = ImageDraw.Draw(streak)
        for k in range(3):
            sy = (WIN_TOP + (frame * 9 + k * 90) % WIN_H)
            st.rectangle([rx0 + 6, sy, rx0 + REEL_W - 6, sy + 6], fill=(255, 255, 255, 60))
        img.alpha_composite(streak)
    else:
        layer = Image.new("RGBA", (REEL_W, WIN_H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        lcx = REEL_W // 2
        base_index = int(y // CELL_H)
        frac = y % CELL_H
        for r in range(-1, 4):
            sym_idx = (base_index + r) % len(SYMBOLS)
            text, col = SYMBOLS[sym_idx]
            draw_y = r * CELL_H - frac + CELL_H / 2
            if draw_y < -CELL_H or draw_y > WIN_H + CELL_H:
                continue
            is_winner = (frame >= STOP_FRAMES[reel_idx] and r == 1 and sym_idx == WIN_INDEX)
            size = 108 if not is_winner else int(108 + 14 * (0.5 + 0.5 * math.sin(frame * 0.35)))
            if is_winner:
                glow = Image.new("RGBA", (REEL_W, WIN_H), (0, 0, 0, 0))
                gd = ImageDraw.Draw(glow)
                for rad, a in [(90, 40), (65, 60), (45, 90)]:
                    gd.ellipse([lcx - rad, draw_y - rad, lcx + rad, draw_y + rad], fill=col + (a,))
                glow = glow.filter(ImageFilter.GaussianBlur(8))
                layer.alpha_composite(glow)
            draw_text_center(ld, lcx, draw_y, text, size, col,
                              stroke_fill=(30, 20, 10), stroke_width=4)
        img.alpha_composite(layer, (rx0, WIN_TOP))

    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle(win_box, fill=255)
    # re-clip: draw a soft dark vignette at top/bottom edges of the window for depth
    shade = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rectangle([rx0, WIN_TOP, rx0 + REEL_W, WIN_TOP + 26], fill=(0, 0, 0, 130))
    sd.rectangle([rx0, WIN_TOP + WIN_H - 26, rx0 + REEL_W, WIN_TOP + WIN_H], fill=(0, 0, 0, 130))
    img.alpha_composite(shade)


def draw_spin_button(img, draw, frame):
    if frame > SPIN_START + 6:
        return
    cy = WIN_TOP + WIN_H + 150
    pulse = 0.5 + 0.5 * math.sin(frame * 0.35)
    pressed = frame >= SPIN_START - 4
    r = 92 if not pressed else 80
    col = lerp_color(GOLD, WHITE, pulse * 0.3)
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([WIDTH // 2 - r - 20, cy - r - 20, WIDTH // 2 + r + 20, cy + r + 20],
               fill=GOLD + (int(50 + 40 * pulse),))
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(glow)
    draw.ellipse([WIDTH // 2 - r, cy - r, WIDTH // 2 + r, cy + r], fill=(60, 30, 20), outline=GOLD, width=6)
    draw_text_center(draw, WIDTH // 2, cy, "SPIN", 46, GOLD)


def draw_intro(img, draw, frame):
    if frame > 70:
        return
    a = int(255 * min(1.0, frame / 18)) if frame < 60 else int(255 * max(0.0, (70 - frame) / 10))
    layer = draw_text_center(draw, WIDTH // 2, 240, "今日の運勢は?", 66, WHITE, alpha=a)
    if layer:
        img.alpha_composite(layer)
    layer2 = draw_text_center(draw, WIDTH // 2, 320, "一回転で占う ミニスロット占い", 34, (220, 200, 255), alpha=a)
    if layer2:
        img.alpha_composite(layer2)


def draw_flash(img, frame):
    fdur = 10
    if FLASH_FRAME <= frame < FLASH_FRAME + fdur:
        t = (frame - FLASH_FRAME) / fdur
        a = int(220 * (1 - t))
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, a))
        img.alpha_composite(overlay)


def draw_confetti(img, draw, frame):
    if frame < FLASH_FRAME:
        return
    t = frame - FLASH_FRAME
    for (cx0, cy0, speed, drift, col, phase) in CONFETTI:
        y = cy0 + speed * t * 9
        if y < -30 or y > HEIGHT + 30:
            continue
        x = cx0 + drift * 20 * math.sin(t * 0.05 + phase)
        size = 10
        ang = (t * 6 + phase * 40) % 360
        cell = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        cd = ImageDraw.Draw(cell)
        cd.rectangle([0, 0, size * 2, size], fill=col + (230,))
        cell = cell.rotate(ang, expand=True)
        img.alpha_composite(cell, (int(x), int(y)))


def draw_result(img, draw, frame):
    if frame < FLASH_FRAME:
        return
    t = frame - FLASH_FRAME
    if t < 24:
        scale = ease_out_quart(min(t / 14, 1.0))
        overshoot = 1.0 + 0.25 * math.sin(min(t / 14, 1.0) * math.pi) * (1 - min(t / 14, 1.0))
        size = int(150 * scale * (1 + (overshoot - 1)))
    else:
        size = int(150 + 12 * math.sin((t - 24) * 0.25))
    size = max(size, 1)
    cy = 190
    if t >= 4:
        glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        for rad, a in [(160, 30), (120, 45), (85, 70)]:
            gd.ellipse([WIDTH // 2 - rad, cy - rad, WIDTH // 2 + rad, cy + rad], fill=GOLD + (a,))
        glow = glow.filter(ImageFilter.GaussianBlur(18))
        img.alpha_composite(glow)
        draw_text_center(draw, WIDTH // 2, cy, "大吉", size, GOLD, stroke_fill=(90, 40, 10), stroke_width=8)
    if t >= 30:
        a = min(255, int((t - 30) * 12))
        layer = draw_text_center(draw, WIDTH // 2, cy + 130, "幸運が舞い込む一日に!", 40, WHITE, alpha=a)
        if layer:
            img.alpha_composite(layer)


def draw_endcard(img, draw, frame):
    start = N_FRAMES - 60
    if frame < start:
        return
    t = (frame - start) / 60
    a = int(255 * min(1.0, t / 0.35))
    dim = Image.new("RGBA", (WIDTH, HEIGHT), (10, 6, 20, int(236 * min(1.0, t / 0.35))))
    img.alpha_composite(dim)
    layer = draw_text_center(draw, WIDTH // 2, HEIGHT // 2 - 60, "Slot Fortune Telling", 54, GOLD, alpha=a)
    if layer:
        img.alpha_composite(layer)
    layer2 = draw_text_center(draw, WIDTH // 2, HEIGHT // 2 + 10, "占いスロット", 40, WHITE, alpha=a)
    if layer2:
        img.alpha_composite(layer2)
    layer3 = draw_text_center(draw, WIDTH // 2, HEIGHT // 2 + 90, "今すぐ運試し!", 36, (220, 200, 255), alpha=a)
    if layer3:
        img.alpha_composite(layer3)


def render_frame(frame):
    img = Image.new("RGBA", (WIDTH, HEIGHT), BG_TOP + (255,))
    draw = ImageDraw.Draw(img)
    draw_background(img, draw, frame)
    draw_cabinet(img, draw)
    for i in range(N_REELS):
        draw_reel(img, draw, i, frame)
    draw_spin_button(img, draw, frame)
    draw_intro(img, draw, frame)
    draw_confetti(img, draw, frame)
    draw_flash(img, frame)
    draw_result(img, draw, frame)
    draw_endcard(img, draw, frame)
    return img.convert("RGB")


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    only = None
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        only = [0, 20, 41, 45, 100, 200, 260, 262, 300, 338, 345, 360, 400, 440, 449]

    frames_range = only if only else range(N_FRAMES)
    for i in frames_range:
        img = render_frame(i)
        img.save(os.path.join(FRAMES_DIR, f"frame_{i:04d}.jpg"), quality=92)
        if i % 30 == 0:
            print(f"rendered frame {i}/{N_FRAMES}")

    if only:
        print("Preview frames written, skipping ffmpeg encode.")
        return

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "frame_%04d.jpg"),
        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "medium",
        "-movflags", "+faststart",
        OUTPUT_PATH,
    ]
    subprocess.run(cmd, check=True)
    print("Wrote", OUTPUT_PATH)


if __name__ == "__main__":
    main()
