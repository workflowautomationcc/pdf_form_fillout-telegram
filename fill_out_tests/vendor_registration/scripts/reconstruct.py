"""
Reconstruct form from scratch using lines JSON + OCR JSON.
White canvas, black lines and text — confirms coordinates are correct.
Page 1 only.
"""

import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"

def fit_font_to_height(target_h, text):
    target_h = max(1, int(round(target_h)))
    low, high = 1, target_h * 4
    best = None
    while low <= high:
        mid = (low + high) // 2
        font = ImageFont.truetype(FONT_PATH, mid)
        bbox = font.getbbox(text or "A")
        visible_h = max(1, bbox[3] - bbox[1])
        if visible_h <= target_h:
            best = font
            low = mid + 1
        else:
            high = mid - 1
    return best or ImageFont.truetype(FONT_PATH, 1)

BASE      = Path(__file__).parent.parent
DEBUG_DIR = BASE / "tests" / "Vendor_1" / "debug"
IMAGES_DIR = BASE / "images" / "Vendor_1"

LINES_JSON = DEBUG_DIR / "page_1_lines.json"
OCR_JSON   = DEBUG_DIR / "page_1_ocr.json"
OUTPUT     = DEBUG_DIR / "page_1_reconstructed.png"

# Get actual image dimensions from the original
original = Image.open(IMAGES_DIR / "page_1.png")
W, H = original.size
original.close()

# White canvas
canvas = Image.new("RGB", (W, H), color=(255, 255, 255))
draw = ImageDraw.Draw(canvas)

# Draw lines
with open(LINES_JSON) as f:
    lines = json.load(f)

for line in lines:
    x, y, w, h = line["x"], line["y"], line["w"], line["h"]
    draw.rectangle([x, y, x + w, y + h], fill=(0, 0, 0))

# Draw OCR text
with open(OCR_JSON) as f:
    ocr = json.load(f)

boxes = ocr.get("google", {}).get("bounding_boxes", [])

font = ImageFont.truetype(FONT_PATH, 22)
for box in boxes:
    text = box["text"]
    x = int(box["left"] * W)
    y = int(box["top"] * H)
    draw.text((x, y), text, fill=(0, 0, 0), font=font)

canvas.save(OUTPUT)
print(f"Saved: {OUTPUT}")
