"""
Visualize per-word boxes using precise pixel positions from word_positions.json.

Color per font group:
    tiny  → orange
    main  → green
    large → blue
    giant → red
    other → gray

Output: 3_output/tier2/word_boxes_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER1_DIR = BASE / "2_process" / "tier1"
TIER2_DIR = BASE / "2_process" / "tier2" / "font_groups"
OUT_DIR   = BASE / "3_output" / "tier2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUP_COLORS = {
    "tiny":  (255, 165,   0),
    "main":  (  0, 160,   0),
    "large": ( 30, 100, 220),
    "giant": (200,   0,   0),
    "other": (160, 160, 160),
}


def get_font_group(h, groups):
    for name, bounds in groups.items():
        if bounds["min_px"] <= h <= bounds["max_px"]:
            return name
    return "other"


def run(page="page_1"):
    with open(TIER2_DIR / "font_groups.json") as f:
        groups = json.load(f)

    with open(TIER1_DIR / f"{page}_word_positions.json") as f:
        data = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    W = img.width
    H = img.height
    draw = ImageDraw.Draw(img)

    for w in data["words"]:
        height_px = round(w["height"] * H, 1)
        group = get_font_group(height_px, groups)
        color = GROUP_COLORS[group]
        x0 = round(w["left"] * W)
        x1 = round((w["left"] + w["width"]) * W)
        y0 = round(w["top"] * H)
        y1 = round((w["top"] + w["height"]) * H)
        if x1 <= x0 or y1 <= y0:
            continue
        draw.rectangle([x0, y0, x1, y1], outline=color, width=2)

    out_path = OUT_DIR / "word_boxes_visual.png"
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
