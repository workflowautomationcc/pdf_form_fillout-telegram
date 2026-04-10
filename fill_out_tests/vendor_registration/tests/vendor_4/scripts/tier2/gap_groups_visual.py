"""
Visualize gap groups as filled vertical rectangles between adjacent words.

Colors:
    tiny-friend   → orange
    main-friend   → green
    large-friend  → blue
    giant-friend  → purple
    separate      → red

Rectangles extend 8px above and below the word band.

Output: 3_output/tier2/gap_groups_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER2_DIR = BASE / "2_process" / "tier2"
OUT_DIR   = BASE / "3_output" / "tier2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GAP_EXTEND = 8

GROUP_COLORS = {
    "tiny-friend":  (255, 165,   0, 180),
    "main-friend":  (  0, 160,   0, 180),
    "large-friend": ( 30, 100, 220, 180),
    "giant-friend": (140,   0, 200, 180),
    "separate":     (200,   0,   0, 180),
}


def run(page="page_1"):
    with open(TIER2_DIR / "word_gaps" / "gap_groups.json") as f:
        gap_data = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for group_name, gaps in gap_data["groups"].items():
        color = GROUP_COLORS[group_name]
        for g in gaps:
            x0 = g["left_x_end"]
            x1 = g["right_x_start"]
            if x1 <= x0:
                continue
            top_y    = g["band_top"] - GAP_EXTEND
            bottom_y = g["band_bottom"] + GAP_EXTEND
            draw.rectangle([x0, top_y, x1, bottom_y], fill=color)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    out_path = OUT_DIR / "gap_groups_visual.png"
    result.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
