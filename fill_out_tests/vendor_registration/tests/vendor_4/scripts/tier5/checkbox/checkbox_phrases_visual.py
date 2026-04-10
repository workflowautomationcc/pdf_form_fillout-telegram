"""
Visualize checkbox + matched phrase on original page PNG.

Draws green rectangle for checkbox, red rectangle for matched phrase.

Output: 3_output/tier5/checkbox/checkbox_phrases_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER5_DIR = BASE / "2_process" / "tier5" / "checkbox"
OUT_DIR   = BASE / "3_output" / "tier5" / "checkbox"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 2550, 3608


def run(page="page_1"):
    with open(TIER5_DIR / "checkbox_phrases.json") as f:
        data = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    draw = ImageDraw.Draw(img)

    for item in data["items"]:
        cb = item["checkbox"]
        draw.rectangle(
            [cb["x"], cb["y"], cb["x"] + cb["w"], cb["y"] + cb["h"]],
            outline=(0, 220, 0), width=3
        )

        p = item["phrase"]
        if p:
            px = round(p["left"] * W)
            py = round(p["top"] * H)
            pw = round(p["width"] * W)
            ph = round(p["height"] * H)
            draw.rectangle([px, py, px + pw, py + ph], outline=(220, 0, 0), width=3)

    out_path = OUT_DIR / "checkbox_phrases_visual.png"
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
