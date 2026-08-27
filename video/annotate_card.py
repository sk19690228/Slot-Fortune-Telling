#!/usr/bin/env python3
"""Overlay a circled Roman-numeral number and the filename above the card
name banner on a tarot card image."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

ROMAN_TO_CIRCLED = {
    0: "⓪",   # ⓪
    1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤",
    6: "⑥", 7: "⑦", 8: "⑧", 9: "⑨", 10: "⑩",
    11: "⑪", 12: "⑫", 13: "⑬", 14: "⑭", 15: "⑮",
    16: "⑯", 17: "⑰", 18: "⑱", 19: "⑲", 20: "⑳",
    21: "㉑",  # ㉑
}


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


def annotate(image_path, roman_number, caption_ja, out_path):
    img = Image.open(image_path).convert("RGBA")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    gold = (240, 200, 110, 255)
    dark = (20, 14, 8, 255)

    num_font = ImageFont.truetype(FONT_PATH, 68)
    name_font = ImageFont.truetype(FONT_PATH, 48)
    gap = 26

    num_text = ROMAN_TO_CIRCLED[roman_number]
    num_bbox = draw.textbbox((0, 0), num_text, font=num_font, stroke_width=4)
    num_w = num_bbox[2] - num_bbox[0]
    name_bbox = draw.textbbox((0, 0), caption_ja, font=name_font, stroke_width=4)
    name_w = name_bbox[2] - name_bbox[0]

    total_w = num_w + gap + name_w
    start_x = (W - total_w) / 2

    banner_top_y = detect_banner_top_y(img.convert("RGB"))

    pad_x, pad_y = 30, 20
    badge_h = max(num_bbox[3] - num_bbox[1], name_bbox[3] - name_bbox[1]) + pad_y * 2
    margin = 14
    cy = banner_top_y - margin - badge_h / 2
    badge = [W / 2 - total_w / 2 - pad_x, cy - badge_h / 2,
             W / 2 + total_w / 2 + pad_x, cy + badge_h / 2]
    badge_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge_layer)
    bd.rounded_rectangle(badge, radius=badge_h / 2, fill=(10, 8, 6, 190),
                          outline=(200, 165, 90, 200), width=2)
    img.alpha_composite(badge_layer)
    draw = ImageDraw.Draw(img)

    num_h = num_bbox[3] - num_bbox[1]
    draw.text((start_x - num_bbox[0], cy - num_h / 2 - num_bbox[1]), num_text,
              font=num_font, fill=gold, stroke_width=4, stroke_fill=dark)

    name_h = name_bbox[3] - name_bbox[1]
    name_x = start_x + num_w + gap
    draw.text((name_x - name_bbox[0], cy - name_h / 2 - name_bbox[1]), caption_ja,
              font=name_font, fill=gold, stroke_width=4, stroke_fill=dark)

    img.convert("RGB").save(out_path, quality=95)
    print("wrote", out_path)


if __name__ == "__main__":
    src = "/home/user/Slot-Fortune-Telling/video/cards/13_the_magus.webp"
    annotate(src, 1, "蛇と杖を掲げる星辰の魔術師",
             "/home/user/Slot-Fortune-Telling/video/cards/sample_13_the_magus.jpg")
