"""
section_word_visual.py (tier5)

Visualize raw section detection using only the fine-tuned OCR word boxes.

Output: 3_output/tier5/section_word_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER5_DIR = BASE / "2_process" / "tier5"
OUT_DIR = BASE / "3_output" / "tier5"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COLOR_SECTION_FILL = (255, 140, 0, 70)
COLOR_SECTION_BORDER = (255, 140, 0, 255)
COLOR_NUMBER_FILL = (0, 170, 220, 70)
COLOR_NUMBER_BORDER = (0, 170, 220, 255)


def draw_box(draw, box, W, H, fill, outline, width):
    x0 = round(box["left"] * W)
    y0 = round(box["top"] * H)
    x1 = round((box["left"] + box["width"]) * W)
    y1 = round((box["top"] + box["height"]) * H)
    draw.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=width)


def run(page="page_1"):
    with open(TIER5_DIR / "section.json") as f:
        data = json.load(f)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for section in data["sections"]:
        draw_box(
            draw,
            section["ocr_section_word"],
            W,
            H,
            COLOR_SECTION_FILL,
            COLOR_SECTION_BORDER,
            3,
        )
        draw_box(
            draw,
            section["ocr_number_word"],
            W,
            H,
            COLOR_NUMBER_FILL,
            COLOR_NUMBER_BORDER,
            3,
        )

    out_path = OUT_DIR / "section_word_visual.png"
    result = Image.alpha_composite(img, overlay).convert("RGB")
    result.save(out_path)

    print(f"  Sections: {data['section_count']}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
