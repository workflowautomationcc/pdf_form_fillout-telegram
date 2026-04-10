"""
Build word_positions.json (tier1).

For each word, scan pixel columns within the OCR bounding box
(using band top/bottom for vertical extent) to find the precise
left and right edge of actual dark pixels.

All coordinates are normalized 0-1 (same as OCR JSON).

Output: 2_process/tier1/page_1_word_positions.json
"""

import json
import numpy as np
from pathlib import Path
from PIL import Image

BASE      = Path(__file__).parent.parent
INPUT_DIR = BASE / "1_input"
TIER1_DIR = BASE / "2_process" / "tier1"

DARK_THRESHOLD = 180
DENSITY_CUTOFF = 0.001  # any dark pixel in column counts


def find_x_edges(crop_gray):
    h, w = crop_gray.shape
    if w < 1 or h < 1:
        return None
    dark = (crop_gray < DARK_THRESHOLD).astype(np.uint8)
    col_counts = dark.sum(axis=0)
    peak = col_counts.max()
    if peak == 0:
        return None
    active_indices = np.where(col_counts >= peak * DENSITY_CUTOFF)[0]
    if len(active_indices) == 0:
        return None
    return int(active_indices[0]), int(active_indices[-1])


def run(page="page_1"):
    with open(TIER1_DIR / f"{page}_text_band.json") as f:
        band_data = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("L")
    arr = np.array(img)
    H, W = arr.shape

    results = []
    skipped = 0

    for w in band_data["words"]:
        ocr  = w["ocr_box"]
        band = w["band"]

        # Convert normalized to pixels for image scanning
        y0 = max(0, round(band["top"] * H))
        y1 = min(H, round(band["bottom"] * H) + 1)
        x0 = max(0, round(ocr["left"] * W))
        x1 = min(W, round((ocr["left"] + ocr["width"]) * W))

        if x1 <= x0 or y1 <= y0:
            skipped += 1
            continue

        crop = arr[y0:y1, x0:x1]
        edges = find_x_edges(crop)

        if edges is None:
            skipped += 1
            continue

        rel_left, rel_right = edges
        abs_left  = x0 + rel_left
        abs_right = x0 + rel_right

        results.append({
            "text":   w["text"],
            "left":   abs_left / W,
            "top":    band["top"],
            "width":  (abs_right - abs_left) / W,
            "height": band["height"],
        })

    results.sort(key=lambda w: (w["top"], w["left"]))

    output = {
        "page": page,
        "image_size": {"w": W, "h": H},
        "dark_threshold": DARK_THRESHOLD,
        "density_cutoff": DENSITY_CUTOFF,
        "word_count": len(results),
        "words": results,
    }

    out_path = TIER1_DIR / f"{page}_word_positions.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Words processed: {len(results)}  Skipped: {skipped}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
