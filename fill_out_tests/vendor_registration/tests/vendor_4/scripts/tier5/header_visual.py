"""
header_visual.py (tier5)

Draws detected header/title zone as a large rectangle.
  giant phrases  → red box
  large phrases  → blue box
  header zone    → red border rectangle

Output: 3_output/tier5/header_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER5_DIR = BASE / "2_process" / "tier5"
OUT_DIR   = BASE / "3_output" / "tier5"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COLOR_GIANT_FILL   = (200,   0,   0,  80)
COLOR_GIANT_BORDER = (200,   0,   0, 255)
COLOR_LARGE_FILL   = ( 30, 100, 220,  80)
COLOR_LARGE_BORDER = ( 30, 100, 220, 255)
COLOR_ZONE_FILL    = (220,  30,  30,  25)
COLOR_ZONE_BORDER  = (220,  30,  30, 220)


def run(page="page_1"):
    with open(TIER5_DIR / "header.json") as f:
        data = json.load(f)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]

    img     = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    # Zone rectangle
    box = data["safe_header_box"]
    draw.rectangle(
        [round(box["left"] * W), round(box["top"] * H),
         round(box["right"] * W), round(box["bottom"] * H)],
        fill=COLOR_ZONE_FILL, outline=COLOR_ZONE_BORDER, width=4
    )

    # Individual phrases
    for p in data["headers"]:
        if p["font_group"] == "giant":
            fill, border = COLOR_GIANT_FILL, COLOR_GIANT_BORDER
        else:
            fill, border = COLOR_LARGE_FILL, COLOR_LARGE_BORDER

        x0 = round(p["left"] * W)
        y0 = round(p["top"]  * H)
        x1 = round((p["left"] + p["width"])  * W)
        y1 = round((p["top"]  + p["height"]) * H)
        draw.rectangle([x0, y0, x1, y1], fill=fill, outline=border, width=2)

    result   = Image.alpha_composite(img, overlay).convert("RGB")
    out_path = OUT_DIR / "header_visual.png"
    result.save(out_path)

    print(f"  Headers:  {data['header_count']}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
