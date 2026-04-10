"""
Detect checkboxes by:
1. Loading the form image
2. Masking out all text regions (from OCR JSON)
3. Running contour detection on what remains — only structural elements (boxes, lines)
4. Filtering for near-square shapes in realistic checkbox size ranges

Output: {vendor}/debug/page_X_boxes.json
        {vendor}/annotated/page_X_boxes.png
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path

BASE         = Path(__file__).parent.parent
IMAGES_DIR   = BASE / "images"
DETECTED_DIR = BASE / "tests"


def mask_text(thresh, ocr_data, img_w, img_h, padding=5):
    """Black out all OCR text regions from the threshold image."""
    masked = thresh.copy()
    boxes = ocr_data.get("google", {}).get("bounding_boxes", [])
    for box in boxes:
        x = int(box["left"] * img_w) - padding
        y = int(box["top"] * img_h) - padding
        w = int(box["width"] * img_w) + padding * 2
        h = int(box["height"] * img_h) + padding * 2
        x, y = max(0, x), max(0, y)
        cv2.rectangle(masked, (x, y), (x + w, y + h), 0, -1)
    return masked


def detect_boxes(image_path, ocr_path):
    img = cv2.imread(str(image_path))
    img_h, img_w = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    with open(ocr_path) as f:
        ocr_data = json.load(f)

    # Remove text from threshold image
    clean = mask_text(thresh, ocr_data, img_w, img_h)

    boxes = []
    contours, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Size filter: realistic checkbox range (both sizes you mentioned: ~30px and ~74px)
        if w < 20 or h < 20 or w > 100 or h > 100:
            continue
        # Aspect ratio: roughly square
        if not (0.6 <= w / h <= 1.6):
            continue
        boxes.append({"x": x, "y": y, "w": w, "h": h, "type": "box"})

    return boxes, clean


def run(vendor_name):
    img_dir   = IMAGES_DIR / vendor_name
    debug_dir = DETECTED_DIR / vendor_name / "debug"
    ann_dir   = DETECTED_DIR / vendor_name / "annotated"

    pages = sorted(img_dir.glob("page_*.png"))
    for page_path in pages:
        stem = page_path.stem
        ocr_path = debug_dir / f"{stem}_ocr.json"

        if not ocr_path.exists():
            print(f"  No OCR found for {vendor_name}/{stem}, skipping")
            continue

        print(f"  Detecting boxes: {vendor_name}/{stem}")
        boxes, clean_thresh = detect_boxes(page_path, ocr_path)
        print(f"  Found {len(boxes)} box(es)")

        boxes_dir = DETECTED_DIR / vendor_name / "boxes"
        boxes_dir.mkdir(parents=True, exist_ok=True)

        # 1. Original page
        import shutil
        shutil.copy(str(page_path), str(boxes_dir / f"{stem}_original.png"))

        # 2. Clean thresh with detected boxes drawn on it
        clean_rgb = cv2.cvtColor(clean_thresh, cv2.COLOR_GRAY2BGR)
        for b in boxes:
            cv2.rectangle(clean_rgb, (b["x"], b["y"]), (b["x"] + b["w"], b["y"] + b["h"]), (255, 100, 0), 2)
        cv2.imwrite(str(boxes_dir / f"{stem}_detected.png"), clean_rgb)
        print(f"  Saved: {boxes_dir}/{stem}_detected.png")


if __name__ == "__main__":
    vendors = [d.name for d in IMAGES_DIR.iterdir() if d.is_dir()]
    for vendor in sorted(vendors):
        print(f"\n=== {vendor} ===")
        run(vendor)
    print("\nDone.")
