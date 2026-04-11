"""
Visualize combined empty spaces (right + bottom) from tier4.

    right space  → blue
    bottom space → green

Output: 3_output/tier4/empty_space_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER4_DIR = BASE / "2_process" / "tier4"
OUT_DIR   = BASE / "3_output" / "tier4"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COLOR_RIGHT  = (30, 100, 220, 140)
COLOR_BOTTOM = (0, 180, 0, 140)


def run(page="page_1"):
    with open(TIER4_DIR / "empty_space" / "right_space.json") as f:
        right = json.load(f)

    with open(TIER4_DIR / "empty_space" / "bottom_space.json") as f:
        bottom = json.load(f)

    W = right["image_size"]["w"]
    H = right["image_size"]["h"]

    img     = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    for s in bottom["spaces"]:
        x0 = round(s["left"] * W)
        y0 = round(s["top"] * H)
        x1 = round((s["left"] + s["width"]) * W)
        y1 = round((s["top"] + s["height"]) * H)
        if x1 > x0 and y1 > y0:
            draw.rectangle([x0, y0, x1, y1], fill=COLOR_BOTTOM, outline=(0, 0, 0), width=2)

    for s in right["spaces"]:
        x0 = round(s["left"] * W)
        y0 = round(s["top"] * H)
        x1 = round((s["left"] + s["width"]) * W)
        y1 = round((s["top"] + s["height"]) * H)
        if x1 > x0 and y1 > y0:
            draw.rectangle([x0, y0, x1, y1], fill=COLOR_RIGHT, outline=(0, 0, 0), width=2)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    out_path = OUT_DIR / "empty_space_visual.png"
    result.save(out_path)
    print(f"  Right spaces:  {right['space_count']}")
    print(f"  Bottom spaces: {bottom['space_count']}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
