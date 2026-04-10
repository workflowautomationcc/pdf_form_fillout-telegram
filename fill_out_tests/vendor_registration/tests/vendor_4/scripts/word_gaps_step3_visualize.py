"""
Visualize word boxes and inter-word gaps for the 'main' font group.

- Word boxes: thin blue outline
- Gap ≤ 20px between adjacent main words: dark green filled vertical rect (extends 10px above/below)
- First 5 gaps > 20px: red filled vertical rect (same extension)

Output: 3_output/word_gaps_step3_visualize.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent
INPUT_DIR = BASE / "1_input"
OUT_DIR   = BASE / "3_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GAP_THRESHOLD  = 25   # px — green below, red above
GAP_EXTEND     = 10   # px — how much the gap rect extends above/below word box
MAX_RED        = 5    # first N large gaps shown in red

WORD_Y_TOLERANCE = 5

with open(BASE / "2_prep" / "font_sizes" / "font_groups.json") as _f:
    _raw = json.load(_f)
FONT_GROUPS = {k: {"min": v["min_px"], "max": v["max_px"]} for k, v in _raw.items()}


def get_font_group(h):
    for name, bounds in FONT_GROUPS.items():
        if bounds["min"] <= h <= bounds["max"]:
            return name
    return "other"


def run(page="page_1"):
    with open(INPUT_DIR / f"{page}_ocr.json") as f:
        ocr = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    words = ocr.get("google", {}).get("bounding_boxes", [])
    words = [w for w in words if any(c.isalnum() for c in w["text"])]

    for w in words:
        w["px_x"]      = round(w["left"] * W, 1)
        w["px_y"]      = round(w["top"] * H, 1)
        w["px_w"]      = round(w["width"] * W, 1)
        w["px_h"]      = round(w["height"] * H, 1)
        w["px_x_end"]  = round(w["px_x"] + w["px_w"], 1)
        w["font_group"] = get_font_group(w["px_h"])

    # Group into rows
    sorted_words = sorted(words, key=lambda w: w["px_y"])
    rows = []
    for w in sorted_words:
        matched = False
        for row in rows:
            if abs(w["px_y"] - row["y"]) <= WORD_Y_TOLERANCE:
                row["words"].append(w)
                matched = True
                break
        if not matched:
            rows.append({"y": w["px_y"], "words": [w]})

    for row in rows:
        row["words"].sort(key=lambda w: w["px_x"])

    # Draw word boxes (main group only)
    draw_base = ImageDraw.Draw(img)
    for row in rows:
        for w in row["words"]:
            if w["font_group"] != "main":
                continue
            draw_base.rectangle(
                [w["px_x"], w["px_y"], w["px_x_end"], w["px_y"] + w["px_h"]],
                outline=(30, 100, 220),
                width=2,
            )

    # Collect gaps, draw colored rects
    red_count = 0
    for row in rows:
        ws = [w for w in row["words"] if w["font_group"] == "main"]
        for i in range(len(ws) - 1):
            left_w  = ws[i]
            right_w = ws[i + 1]
            gap = round(right_w["px_x"] - left_w["px_x_end"], 1)
            if gap < 0:
                continue

            # Vertical rect fills the gap space
            x0 = left_w["px_x_end"]
            x1 = right_w["px_x"]
            top_y    = min(left_w["px_y"], right_w["px_y"]) - GAP_EXTEND
            bottom_y = max(left_w["px_y"] + left_w["px_h"], right_w["px_y"] + right_w["px_h"]) + GAP_EXTEND

            if gap <= GAP_THRESHOLD:
                color = (0, 120, 0, 180)   # dark green semi-transparent
            else:
                if red_count >= MAX_RED:
                    continue
                color = (200, 0, 0, 180)   # red semi-transparent
                red_count += 1

            draw.rectangle([x0, top_y, x1, bottom_y], fill=color)

    img = Image.alpha_composite(img, overlay).convert("RGB")
    out_path = OUT_DIR / "word_gaps_step3_visualize.png"
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
