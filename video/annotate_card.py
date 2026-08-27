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


def annotate(image_path, roman_number, banner_top_frac, out_path):
    img = Image.open(image_path).convert("RGBA")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    filename = os.path.splitext(os.path.basename(image_path))[0]

    gold = (240, 200, 110, 255)
    dark = (20, 14, 8, 255)

    num_font = ImageFont.truetype(FONT_PATH, 48)
    name_font = ImageFont.truetype(FONT_PATH, 34)
    gap = 20

    num_text = ROMAN_TO_CIRCLED[roman_number]
    num_bbox = draw.textbbox((0, 0), num_text, font=num_font, stroke_width=3)
    num_w = num_bbox[2] - num_bbox[0]
    name_bbox = draw.textbbox((0, 0), filename, font=name_font, stroke_width=3)
    name_w = name_bbox[2] - name_bbox[0]

    total_w = num_w + gap + name_w
    start_x = (W - total_w) / 2

    banner_top_y = int(H * banner_top_frac)
    cy = banner_top_y - 44

    pad_x, pad_y = 22, 14
    badge_h = max(num_bbox[3] - num_bbox[1], name_bbox[3] - name_bbox[1]) + pad_y * 2
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
              font=num_font, fill=gold, stroke_width=3, stroke_fill=dark)

    name_h = name_bbox[3] - name_bbox[1]
    name_x = start_x + num_w + gap
    draw.text((name_x - name_bbox[0], cy - name_h / 2 - name_bbox[1]), filename,
              font=name_font, fill=gold, stroke_width=3, stroke_fill=dark)

    img.convert("RGB").save(out_path, quality=95)
    print("wrote", out_path)


if __name__ == "__main__":
    src = "/home/user/Slot-Fortune-Telling/video/cards/01_the_sun.webp"
    annotate(src, 19, 0.895, "/home/user/Slot-Fortune-Telling/video/cards/sample_01_the_sun.jpg")
