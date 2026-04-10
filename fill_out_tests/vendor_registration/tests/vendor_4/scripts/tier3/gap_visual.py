"""
Visualize all gaps from gap_raw.json as green filled rectangles.

Output: 3_output/tier3/gap_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER3_DIR = BASE / "2_process" / "tier3"
OUT_DIR   = BASE / "3_output" / "tier3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GAP_EXTEND = 8
COLOR      = (0, 200, 0, 160)


def run(page="page_1"):
    with open(TIER3_DIR / "word_gaps" / "gap_raw.json") as f:
        data = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for g in data["gaps"]:
        x0 = round(g["left_x_end"] * W)
        x1 = round(g["right_x_start"] * W)
        if x1 <= x0:
            continue
        top_y    = round(g["top"] * H) - GAP_EXTEND
        bottom_y = round(g["bottom"] * H) + GAP_EXTEND
        draw.rectangle([x0, top_y, x1, bottom_y], fill=COLOR)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    out_path = OUT_DIR / "gap_visual.png"
    result.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
