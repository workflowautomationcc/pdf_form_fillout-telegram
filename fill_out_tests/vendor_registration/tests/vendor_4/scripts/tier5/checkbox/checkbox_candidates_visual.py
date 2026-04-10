"""
Visualize checkbox candidates over the 4x text-removed PNG.

Draws:
  - green rectangles for detected candidates

Output: 3_output/tier5/checkbox_candidates_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent.parent
TIER5_DIR = BASE / "2_process" / "tier5" / "checkbox"
OUT_DIR   = BASE / "3_output" / "tier5" / "checkbox"
OUT_DIR.mkdir(parents=True, exist_ok=True)

IMG_PATH = OUT_DIR / "checkbox_text_removed_4x.png"


def run():
    img = Image.open(IMG_PATH).convert("RGB")
    draw = ImageDraw.Draw(img)

    with open(TIER5_DIR / "checkbox_candidates.json") as f:
        data = json.load(f)

    for c in data["candidates"]:
        x, y, w, h = c["x_4x"], c["y_4x"], c["w_4x"], c["h_4x"]
        draw.rectangle([x, y, x + w, y + h], outline=(0, 220, 0), width=24)

    out_path = OUT_DIR / "checkbox_candidates_visual.png"
    img.save(out_path)
    print(f"  Candidates: {data['candidate_count']}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run()
    print("Done.")
