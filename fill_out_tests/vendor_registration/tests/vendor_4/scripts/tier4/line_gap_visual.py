"""
Visualize vertical line gaps from line_gap_raw.json as filled rectangles.

Output: 3_output/tier4/line_gap_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER4_DIR = BASE / "2_process" / "tier4"
OUT_DIR   = BASE / "3_output" / "tier4"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GAP_EXTEND = 8
COLOR      = (0, 200, 0, 160)


def run(page="page_1"):
    with open(TIER4_DIR / "line_gaps" / "line_gap_raw.json") as f:
        data = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for g in data["gaps"]:
        y0 = round(g["top_bottom"] * H)
        y1 = round(g["bottom_top"] * H)
        if y1 <= y0:
            continue
        draw.rectangle([GAP_EXTEND, y0, W - GAP_EXTEND, y1], fill=COLOR)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    out_path = OUT_DIR / "line_gap_visual.png"
    result.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
