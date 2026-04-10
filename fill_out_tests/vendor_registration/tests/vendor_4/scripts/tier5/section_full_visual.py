"""
section_full_visual.py (tier5)

Draw the full-width section bands.

Output: 3_output/tier5/section_full_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER5_DIR = BASE / "2_process" / "tier5"
OUT_DIR = BASE / "3_output" / "tier5"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COLOR_FILL = (0, 160, 220, 50)
COLOR_BORDER = (0, 160, 220, 255)


def run(page="page_1"):
    with open(TIER5_DIR / "section.json") as f:
        data = json.load(f)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for section in data["sections"]:
        x0 = round(section["left"] * W)
        y0 = round(section["top"] * H)
        x1 = round((section["left"] + section["width"]) * W)
        y1 = round((section["top"] + section["height"]) * H)
        draw.rectangle([x0, y0, x1, y1], fill=COLOR_FILL, outline=COLOR_BORDER, width=3)

    out_path = OUT_DIR / "section_full_visual.png"
    result = Image.alpha_composite(img, overlay).convert("RGB")
    result.save(out_path)

    print(f"  Sections: {data['section_count']}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
