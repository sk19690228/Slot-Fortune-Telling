#!/usr/bin/env python3
"""Build a 15-second video that randomly flashes through the 22 annotated
tarot cards, each shown for exactly 1/22 second."""
import os
import random
import subprocess

ANNOTATED_DIR = "/home/user/Slot-Fortune-Telling/video/cards/annotated"
OUT_DIR = "/home/user/Slot-Fortune-Telling/video/output"
LIST_PATH = "/home/user/Slot-Fortune-Telling/video/_concat_list.txt"
OUT_PATH = os.path.join(OUT_DIR, "tarot_random_flash_15s.mp4")

DURATION = 15
SLOT_SECONDS = 1 / 22
N_SLOTS = round(DURATION / SLOT_SECONDS)  # 330
FPS = 44  # 1/22s == exactly 2 frames at 44fps

random.seed(42)


def build_sequence(images, n_slots):
    seq = []
    prev = None
    for _ in range(n_slots):
        choices = [im for im in images if im != prev]
        pick = random.choice(choices)
        seq.append(pick)
        prev = pick
    return seq


def main():
    images = sorted(
        os.path.join(ANNOTATED_DIR, f) for f in os.listdir(ANNOTATED_DIR) if f.endswith(".jpg")
    )
    assert len(images) == 22, f"expected 22 annotated cards, found {len(images)}"

    seq = build_sequence(images, N_SLOTS)

    with open(LIST_PATH, "w") as f:
        for path in seq:
            f.write(f"file '{path}'\n")
            f.write(f"duration {SLOT_SECONDS:.10f}\n")
        f.write(f"file '{seq[-1]}'\n")  # concat demuxer quirk: repeat last entry

    os.makedirs(OUT_DIR, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", LIST_PATH,
        "-vf", f"fps={FPS},scale=768:1152,format=yuv420p",
        "-c:v", "libx264", "-crf", "34", "-preset", "medium",
        "-movflags", "+faststart",
        OUT_PATH,
    ]
    subprocess.run(cmd, check=True)
    print("wrote", OUT_PATH)


if __name__ == "__main__":
    main()
