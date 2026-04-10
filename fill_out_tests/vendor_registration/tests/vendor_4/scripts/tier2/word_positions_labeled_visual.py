"""
Visualize all word_positions entries with labels.

Output:
  3_output/tier2/word_positions_labeled_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER1_DIR = BASE / "2_process" / "tier1"
OUT_DIR = BASE / "3_output" / "tier2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BOX_COLOR = (20, 120, 220)
TEXT_BG = (255, 255, 255)
TEXT_FG = (0, 0, 0)
FONT_SIZE = 20


def load_font():
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, FONT_SIZE)
        except OSError:
            continue
    return ImageFont.load_default()


def run(page="page_1"):
    with open(TIER1_DIR / f"{page}_word_positions.json") as f:
        data = json.load(f)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]
    words = data["words"]

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    draw = ImageDraw.Draw(img)
    font = load_font()

    for w in words:
        x0 = round(w["left"] * W)
        y0 = round(w["top"] * H)
        x1 = round((w["left"] + w["width"]) * W)
        y1 = round((w["top"] + w["height"]) * H)
        if x1 <= x0 or y1 <= y0:
            continue

        draw.rectangle([x0, y0, x1, y1], outline=BOX_COLOR, width=2)

        label = w["text"]
        tx0, ty0, tx1, ty1 = draw.textbbox((x0, y0), label, font=font)
        text_h = ty1 - ty0
        label_top = max(0, y0 - text_h - 4)
        bg = [x0, label_top, x0 + (tx1 - tx0) + 4, label_top + text_h + 2]
        draw.rectangle(bg, fill=TEXT_BG)
        draw.text((x0 + 2, label_top + 1), label, fill=TEXT_FG, font=font)

    out_path = OUT_DIR / "word_positions_labeled_visual.png"
    img.save(out_path)
    print(f"  Words: {len(words)}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
