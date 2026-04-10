"""
Visualize original OCR words with labels above each box.

Output: 3_output/tier1/ocr_original_labeled_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER1_DIR = BASE / "2_process" / "tier1"
OUT_DIR   = BASE / "3_output" / "tier1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BOX_COLOR = (220, 40, 40)
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
    with open(TIER1_DIR / f"{page}_ocr.json") as f:
        data = json.load(f)

    words = data.get("google", {}).get("bounding_boxes", [])
    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)
    font = load_font()

    for w in words:
        text = w.get("text", "")
        if not text:
            continue

        x0 = round(w["left"] * W)
        x1 = round((w["left"] + w["width"]) * W)
        y0 = round(w["top"] * H)
        y1 = round((w["top"] + abs(w["height"])) * H)
        if x1 <= x0 or y1 <= y0:
            continue

        draw.rectangle([x0, y0, x1, y1], outline=BOX_COLOR, width=2)

        tx0, ty0, tx1, ty1 = draw.textbbox((x0, y0), text, font=font)
        text_h = ty1 - ty0
        label_top = max(0, y0 - text_h - 4)
        bg = [x0, label_top, x0 + (tx1 - tx0) + 4, label_top + text_h + 2]
        draw.rectangle(bg, fill=TEXT_BG)
        draw.text((x0 + 2, label_top + 1), text, fill=TEXT_FG, font=font)

    out_path = OUT_DIR / "ocr_original_labeled_visual.png"
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
