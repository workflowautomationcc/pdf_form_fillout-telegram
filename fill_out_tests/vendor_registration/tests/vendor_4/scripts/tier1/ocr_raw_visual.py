"""
Visualize raw OCR word boxes — no image processing, pure OCR coords.

Output: 3_output/tier3/ocr_raw_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER1_DIR = BASE / "2_process" / "tier1"
OUT_DIR   = BASE / "3_output" / "tier1"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run(page="page_1"):
    with open(TIER1_DIR / f"{page}_ocr.json") as f:
        ocr_raw = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    words = [w for w in ocr_raw.get("google", {}).get("bounding_boxes", [])
             if any(c.isalnum() for c in w["text"])]

    for w in words:
        x0 = round(w["left"] * W)
        y0 = round(w["top"] * H)
        x1 = round((w["left"] + w["width"]) * W)
        y1 = round((w["top"] + abs(w["height"])) * H)
        if x1 > x0 and y1 > y0:
            draw.rectangle([x0, y0, x1, y1], outline=(200, 0, 0), width=2)

    out_path = OUT_DIR / "ocr_raw_visual.png"
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
