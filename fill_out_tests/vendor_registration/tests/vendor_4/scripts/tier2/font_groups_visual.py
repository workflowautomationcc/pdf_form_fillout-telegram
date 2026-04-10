"""
Visualize font groups on page image.

For each word in word_heights_raw.json, draw a full-width horizontal band
at the word's band_top / band_bottom, colored by font group:
    tiny  → orange
    main  → green
    large → blue
    giant → red
    other → gray

Output: 3_output/tier2/font_groups_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER2_DIR = BASE / "2_process" / "tier2" / "font_groups"
OUT_DIR   = BASE / "3_output" / "tier2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUP_COLORS = {
    "tiny":  (255, 165,   0, 140),
    "main":  (  0, 160,   0, 140),
    "large": ( 30, 100, 220, 140),
    "giant": (200,   0,   0, 140),
    "other": (160, 160, 160, 140),
}


def get_font_group(h, groups):
    for name, bounds in groups.items():
        if bounds["min_px"] <= h <= bounds["max_px"]:
            return name
    return "other"


def run(page="page_1"):
    with open(TIER2_DIR / "font_groups.json") as f:
        groups = json.load(f)

    with open(TIER2_DIR / "word_heights_raw.json") as f:
        data = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    W = img.width
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    H = img.height
    for w in data["words"]:
        group = get_font_group(w["height_px"], groups)
        color = GROUP_COLORS[group]
        y0 = round(w["band_top"] * H)
        y1 = round(w["band_bottom"] * H)
        draw.rectangle([0, y0, W, y1], fill=color)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    out_path = OUT_DIR / "font_groups_visual.png"
    result.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
