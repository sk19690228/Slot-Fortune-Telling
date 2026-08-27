#!/usr/bin/env python3
"""Overlay a hand-drawn circled number (converted from the card's Roman
numeral) and a Japanese scene caption just above the card's name banner."""
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

STROKE_WIDTH = 4
SIDE_MARGIN = 60  # keep clear of the card's decorative border
CIRCLE_TO_NAME_RATIO = 66 / 48   # circle diameter relative to name_size
DIGIT_TO_CIRCLE_RATIO = 0.58     # digit font size relative to circle diameter
GAP_TO_NAME_RATIO = 26 / 48

GOLD = (240, 200, 110, 255)
DARK = (20, 14, 8, 255)


def detect_banner_top_y(img_rgb, search_from_frac=0.75, search_to_frac=0.98):
    """Scan down the vertical center line to find where the card's dark
    name-banner begins (first sustained near-black run)."""
    W, H = img_rgb.size
    px = img_rgb.load()
    x = W // 2
    for y in range(int(H * search_from_frac), int(H * search_to_frac)):
        if sum(px[x, y]) < 90 and all(sum(px[x, y + k]) < 140 for k in range(15)):
            return y
    return int(H * search_to_frac)


def circle_diameter(name_size, number):
    d = round(name_size * CIRCLE_TO_NAME_RATIO)
    return round(d * 1.25) if number >= 10 else d  # two digits need more room


def draw_number_circle(draw, cx, cy, number, name_size):
    diameter = circle_diameter(name_size, number)
    r = diameter / 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=STROKE_WIDTH,
                 fill=(10, 8, 6, 190))
    digit_font = ImageFont.truetype(FONT_PATH, round(diameter * DIGIT_TO_CIRCLE_RATIO))
    text = str(number)
    bbox = draw.textbbox((0, 0), text, font=digit_font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - w / 2 - bbox[0], cy - h / 2 - bbox[1]), text, font=digit_font, fill=GOLD)
    return diameter


def fit_font_size(draw, caption_ja, roman_number, max_width, max_size=100, min_size=20):
    """Largest name_size (circle/gap scaled to match) whose combined
    single-line width fits within max_width."""
    for size in range(max_size, min_size - 1, -1):
        name_font = ImageFont.truetype(FONT_PATH, size)
        num_w = circle_diameter(size, roman_number)
        gap = round(size * GAP_TO_NAME_RATIO)
        name_w = draw.textbbox((0, 0), caption_ja, font=name_font,
                                stroke_width=STROKE_WIDTH)[2]
        if num_w + gap + name_w <= max_width:
            return size
    return min_size


def annotate(image_path, roman_number, caption_ja, out_path, name_size=None, banner_top_y=None):
    img = Image.open(image_path).convert("RGBA")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    if name_size is None:
        name_size = fit_font_size(draw, caption_ja, roman_number, W - 2 * SIDE_MARGIN)

    name_font = ImageFont.truetype(FONT_PATH, name_size)
    gap = round(name_size * GAP_TO_NAME_RATIO)
    num_w = circle_diameter(name_size, roman_number)

    name_bbox = draw.textbbox((0, 0), caption_ja, font=name_font, stroke_width=STROKE_WIDTH)
    name_w = name_bbox[2] - name_bbox[0]
    name_h = name_bbox[3] - name_bbox[1]

    total_w = num_w + gap + name_w
    start_x = (W - total_w) / 2

    if banner_top_y is None:
        banner_top_y = detect_banner_top_y(img.convert("RGB"))

    pad_x, pad_y = 30, 14
    badge_h = max(num_w, name_h) + pad_y * 2
    margin = 0
    cy = banner_top_y - margin - badge_h / 2
    badge = [W / 2 - total_w / 2 - pad_x, cy - badge_h / 2,
             W / 2 + total_w / 2 + pad_x, cy + badge_h / 2]
    badge_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge_layer)
    bd.rounded_rectangle(badge, radius=badge_h / 2, fill=(10, 8, 6, 190),
                          outline=(200, 165, 90, 200), width=2)
    img.alpha_composite(badge_layer)
    draw = ImageDraw.Draw(img)

    circle_cx = start_x + num_w / 2
    draw_number_circle(draw, circle_cx, cy, roman_number, name_size)

    name_x = start_x + num_w + gap
    draw.text((name_x - name_bbox[0], cy - name_h / 2 - name_bbox[1]), caption_ja,
              font=name_font, fill=GOLD, stroke_width=STROKE_WIDTH, stroke_fill=DARK)

    img.convert("RGB").save(out_path, quality=95)
    print("wrote", out_path)


if __name__ == "__main__":
    ref = Image.open(
        "/home/user/Slot-Fortune-Telling/video/cards/13_the_magus.webp").convert("RGB")
    fixed_banner_top_y = detect_banner_top_y(ref)
    print("fixed_banner_top_y (from card 1, The Magus):", fixed_banner_top_y)

    src = "/home/user/Slot-Fortune-Telling/video/cards/18_the_fool.webp"
    caption = "虎と鰐に見守られ舞う虹色の旅人"
    annotate(src, 0, caption,
             "/home/user/Slot-Fortune-Telling/video/cards/sample_18_the_fool.jpg",
             name_size=39, banner_top_y=fixed_banner_top_y)
