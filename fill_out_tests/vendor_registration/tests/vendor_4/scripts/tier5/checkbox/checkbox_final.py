"""
Draw detected checkboxes on the original page PNG (2550px wide).

Reads original coords (x, y, w, h) from checkbox_candidates.json
and overlays green rectangles on page_1.png.

Output: 3_output/tier5/checkbox_final.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER5_DIR = BASE / "2_process" / "tier5" / "checkbox"
OUT_DIR   = BASE / "3_output" / "tier5" / "checkbox"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run(page="page_1"):
    with open(TIER5_DIR / "checkbox_candidates.json") as f:
        data = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    draw = ImageDraw.Draw(img)

    for c in data["candidates"]:
        x, y, w, h = round(c["x"]), round(c["y"]), round(c["w"]), round(c["h"])
        draw.rectangle([x, y, x + w, y + h], outline=(0, 220, 0), width=3)

    out_path = OUT_DIR / "checkbox_final.png"
    img.save(out_path)
    print(f"  Candidates: {data['candidate_count']}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
