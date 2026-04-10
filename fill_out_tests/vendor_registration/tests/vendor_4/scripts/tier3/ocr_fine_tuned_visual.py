"""
Visualize all words from words.json with precise boxes.

Color per font group:
    tiny  → orange
    main  → green
    large → blue
    giant → red
    other → gray

Output: 3_output/tier3/words_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER3_DIR = BASE / "2_process" / "tier3"
OUT_DIR   = BASE / "3_output" / "tier3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUP_COLORS = {
    "tiny":  (255, 165,   0),
    "main":  (  0, 160,   0),
    "large": ( 30, 100, 220),
    "giant": (200,   0,   0),
    "other": (160, 160, 160),
}


def run(page="page_1"):
    with open(TIER3_DIR / "words" / "ocr_fine_tuned.json") as f:
        data = json.load(f)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    draw = ImageDraw.Draw(img)

    for w in data["words"]:
        color = GROUP_COLORS.get(w["font_group"], (160, 160, 160))
        x0 = round(w["left"] * W)
        x1 = round((w["left"] + w["width"]) * W)
        y0 = round(w["top"] * H)
        y1 = round((w["top"] + w["height"]) * H)
        if x1 <= x0 or y1 <= y0:
            continue
        draw.rectangle([x0, y0, x1, y1], outline=color, width=2)

    out_path = OUT_DIR / "ocr_fine_tuned_visual.png"
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
