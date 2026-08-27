#!/usr/bin/env python3
"""Annotate all 22 tarot card images with their circled number + Japanese
scene caption, using a common font size fitted to the longest caption."""
import os

from annotate_card import annotate, detect_banner_top_y
from PIL import Image

CARDS_DIR = "/home/user/Slot-Fortune-Telling/video/cards"
OUT_DIR = "/home/user/Slot-Fortune-Telling/video/cards/annotated"
REFERENCE_CARD = "13_the_magus.webp"  # card ① — its caption position is the shared target

# (filename, roman_number, japanese caption)
CARDS = [
    ("01_the_sun.webp", 19, "ひまわりの庭で舞う光の精霊"),
    ("02_the_hermit.webp", 9, "灯りを掲げ狼を従える隠者の賢者"),
    ("03_the_universe.webp", 21, "銀河を纏い天球の上で舞う宇宙の踊り手"),
    ("04_the_aeon.webp", 20, "門の間で目覚める黄金の新生児"),
    ("05_the_emperor.webp", 4, "牡羊の玉座に君臨する火の皇帝"),
    ("06_the_hanged_man.webp", 12, "水面に逆さに漂う瞑想の行者"),
    ("07_adjustment.webp", 8, "剣を掲げ天秤を操る調整の女神"),
    ("08_the_star.webp", 17, "星空の下二つの壺から水を注ぐ乙女"),
    ("09_the_devil.webp", 15, "日食の下に座す山羊頭の魔王"),
    ("10_the_priestess.webp", 2, "月と柱の間に座す静寂の巫女"),
    ("11_the_moon.webp", 18, "月の運河を見守るアヌビスの守護者"),
    ("12_the_hierophant.webp", 5, "鍵と牡牛を掲げる大司教の神官"),
    ("13_the_magus.webp", 1, "蛇と杖を掲げる星辰の魔術師"),
    ("14_lust.webp", 11, "薔薇と七頭の獅子を従え杯を掲げる情熱の女神"),
    ("15_the_empress.webp", 3, "薔薇と麦穂に囲まれる豊穣の女帝"),
    ("16_fortune.webp", 10, "孔雀が見守る運命の輪廻"),
    ("17_the_tower.webp", 16, "雷に貫かれ崩れゆく獅子の塔"),
    ("18_the_fool.webp", 0, "虎と鰐に見守られ舞う虹色の旅人"),
    ("19_the_lovers.webp", 6, "天使に見守られ杯を囲む恋人たち"),
    ("20_art.webp", 14, "陰陽の雫を注ぐ調和の天使"),
    ("21_the_chariot.webp", 7, "四体のスフィンクスが牽く聖杯の戦車"),
    ("22_death.webp", 13, "三日月と炎の鳳凰を従える氷の死神"),
]

COMMON_NAME_SIZE = 39  # fitted to the longest caption (Lust, 21 chars)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    ref_img = Image.open(os.path.join(CARDS_DIR, REFERENCE_CARD)).convert("RGB")
    fixed_banner_top_y = detect_banner_top_y(ref_img)
    print(f"using fixed banner_top_y={fixed_banner_top_y} (from {REFERENCE_CARD})")

    for fname, roman, caption in CARDS:
        src = os.path.join(CARDS_DIR, fname)
        out = os.path.join(OUT_DIR, os.path.splitext(fname)[0] + ".jpg")
        annotate(src, roman, caption, out, name_size=COMMON_NAME_SIZE,
                 banner_top_y=fixed_banner_top_y)


if __name__ == "__main__":
    main()
