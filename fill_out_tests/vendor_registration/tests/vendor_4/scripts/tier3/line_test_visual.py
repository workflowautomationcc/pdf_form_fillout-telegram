"""
Visualize line_test.json — draw word boxes on the page image for one line.

Output: 3_output/tier3/line_test_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
OUT_DIR   = BASE / "3_output" / "tier3"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run(page="page_1"):
    with open(OUT_DIR / "line_test.json") as f:
        data = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    for w in data["words"]:
        x0 = round(w["left"] * W)
        x1 = round(w["right"] * W)
        y0 = round(w["band_top"] * H)
        y1 = round(w["band_bottom"] * H)
        if x1 > x0 and y1 > y0:
            draw.rectangle([x0, y0, x1, y1], outline=(0, 160, 0), width=2)

    out_path = OUT_DIR / "line_test_visual.png"
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
