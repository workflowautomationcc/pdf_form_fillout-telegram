"""
Visualize phrase containers (tier4).

Draws a bounding box around each phrase.

Color per font_group:
    tiny  → orange
    main  → green
    large → blue
    giant → red
    other → gray

Output: 3_output/tier4/phrases_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER4_DIR = BASE / "2_process" / "tier4"
OUT_DIR   = BASE / "3_output" / "tier4"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUP_COLORS = {
    "tiny":  (255, 165,   0),
    "main":  (  0, 160,   0),
    "large": ( 30, 100, 220),
    "giant": (200,   0,   0),
    "other": (160, 160, 160),
}


def run(page="page_1"):
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        data = json.load(f)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]

    img  = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    draw = ImageDraw.Draw(img)

    for p in data["phrases"]:
        color = GROUP_COLORS.get(p["font_group"], GROUP_COLORS["other"])
        x0 = round(p["left"] * W)
        y0 = round(p["top"] * H)
        x1 = round((p["left"] + p["width"]) * W)
        y1 = round((p["top"] + p["height"]) * H)
        if x1 <= x0 or y1 <= y0:
            continue
        draw.rectangle([x0, y0, x1, y1], outline=color, width=2)

    out_path = OUT_DIR / "phrases_visual.png"
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
