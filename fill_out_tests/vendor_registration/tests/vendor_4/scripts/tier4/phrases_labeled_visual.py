"""
Visualize phrase containers with labels.

Output: 3_output/tier4/phrases_labeled_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER4_DIR = BASE / "2_process" / "tier4"
OUT_DIR = BASE / "3_output" / "tier4"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUP_COLORS = {
    "tiny":  (255, 165,   0),
    "main":  (0,   160,   0),
    "large": (30,  100, 220),
    "giant": (200,   0,   0),
    "other": (160, 160, 160),
}

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
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        data = json.load(f)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]
    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    draw = ImageDraw.Draw(img)
    font = load_font()

    for phrase in data["phrases"]:
        color = GROUP_COLORS.get(phrase["font_group"], GROUP_COLORS["other"])
        x0 = round(phrase["left"] * W)
        y0 = round(phrase["top"] * H)
        x1 = round((phrase["left"] + phrase["width"]) * W)
        y1 = round((phrase["top"] + phrase["height"]) * H)
        if x1 <= x0 or y1 <= y0:
            continue

        draw.rectangle([x0, y0, x1, y1], outline=color, width=2)

        label = phrase["text"]
        tx0, ty0, tx1, ty1 = draw.textbbox((x0, y0), label, font=font)
        text_h = ty1 - ty0
        label_top = max(0, y0 - text_h - 4)
        bg = [x0, label_top, x0 + (tx1 - tx0) + 4, label_top + text_h + 2]
        draw.rectangle(bg, fill=TEXT_BG)
        draw.text((x0 + 2, label_top + 1), label, fill=TEXT_FG, font=font)

    out_path = OUT_DIR / "phrases_labeled_visual.png"
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
