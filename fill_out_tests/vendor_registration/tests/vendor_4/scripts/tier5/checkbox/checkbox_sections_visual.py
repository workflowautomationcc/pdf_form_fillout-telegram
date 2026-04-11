"""
Visualize checkbox sections on original page PNG.

Draws:
  - blue unfilled rectangle = full section (section_top to section_bottom)
  - red rectangle = header phrase
  - green rectangle = each checkbox

Output: 3_output/tier5/checkbox/checkbox_sections_visual.png
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
    with open(TIER5_DIR / "checkbox_sections.json") as f:
        data = json.load(f)

    with open(TIER5_DIR / "checkbox_phrases.json") as f:
        phrases_data = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    draw = ImageDraw.Draw(img)

    for section in data["sections"]:
        # Section border (blue)
        if section["section_top"] is not None and section["section_bottom"] is not None:
            y0 = round(section["section_top"] * H)
            y1 = round(section["section_bottom"] * H)
            draw.rectangle([-2, y0 - 2, W + 1, y1 + 2], outline=(0, 0, 0), width=2)
            draw.rectangle([0, y0, W - 1, y1], outline=(0, 0, 220), width=2)

        # Header phrase (red)
        p = section["header_phrase"]
        if p:
            px = round(p["left"] * W)
            py = round(p["top"] * H)
            pw = round(p["width"] * W)
            ph = round(p["height"] * H)
            draw.rectangle([px, py, px + pw, py + ph], outline=(220, 0, 0), width=3)

    # Checkboxes (green)
    for item in phrases_data["items"]:
        cb = item["checkbox"]
        draw.rectangle(
            [cb["x"] - 2, cb["y"] - 2, cb["x"] + cb["w"] + 2, cb["y"] + cb["h"] + 2],
            outline=(0, 0, 0), width=2
        )
        draw.rectangle(
            [cb["x"], cb["y"], cb["x"] + cb["w"], cb["y"] + cb["h"]],
            outline=(0, 220, 0), width=2
        )

    out_path = OUT_DIR / "checkbox_sections_visual.png"
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
