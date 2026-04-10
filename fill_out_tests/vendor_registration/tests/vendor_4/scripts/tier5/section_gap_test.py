"""
section_gap_test.py

Minimal fine-tuned OCR test for Section -> number pairing.

Rules tested:
  - Y difference uses top edge in pixels
  - Horizontal gap uses Section.right -> number.left in pixels
  - Candidate must be to the right of Section

Output: prints a table only
"""

import json
import re
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
TIER3_DIR = BASE / "2_process" / "tier3" / "words"

Y_TOLERANCE_PX = 10
X_GAP_MAX_PX = 60
NUMBER_RE = re.compile(r"^\D*(\d+)\D*$")


def px_box(word, width, height):
    left = word["left"] * width
    top = word["top"] * height
    right = (word["left"] + word["width"]) * width
    bottom = (word["top"] + word["height"]) * height
    return left, top, right, bottom


def parse_number(text):
    match = NUMBER_RE.match(text.strip())
    return match.group(1) if match else None


def run(page="page_1"):
    with open(TIER3_DIR / "ocr_fine_tuned.json") as f:
        data = json.load(f)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]
    words = data["words"]

    sections = [w for w in words if w["text"] == "Section"]
    numbers = [w for w in words if parse_number(w["text"])]

    print("section_left | section_top | number | number_left | number_top | y_diff_px | x_gap_px | pass")
    print("-" * 98)

    for section in sections:
        sx0, sy0, sx1, sy1 = px_box(section, W, H)
        printed = False

        for number in numbers:
            wx0, wy0, wx1, wy1 = px_box(number, W, H)
            y_diff_px = abs(wy0 - sy0)
            x_gap_px = wx0 - sx1

            passes = (
                wx0 >= sx1
                and y_diff_px <= Y_TOLERANCE_PX
                and x_gap_px < X_GAP_MAX_PX
            )

            if passes:
                printed = True
                print(
                    f"{sx0:12.1f} | {sy0:11.1f} | {number['text']:<6} | "
                    f"{wx0:11.1f} | {wy0:10.1f} | {y_diff_px:9.1f} | {x_gap_px:8.1f} | yes"
                )

        if not printed:
            print(
                f"{sx0:12.1f} | {sy0:11.1f} | {'NONE':<6} | "
                f"{'-':>11} | {'-':>10} | {'-':>9} | {'-':>8} | no"
            )


if __name__ == "__main__":
    run("page_1")
