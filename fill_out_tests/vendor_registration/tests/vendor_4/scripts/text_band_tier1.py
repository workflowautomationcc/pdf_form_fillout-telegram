"""
Build text_band.json (tier1).

For each word from OCR, scan actual pixels in the image to find
the real text body band — top and bottom of the core text height,
cutting through ascenders and descenders.

All coordinates are normalized 0-1 (same as OCR JSON).

Output: 2_process/tier1/page_1_text_band.json
"""

import json
import numpy as np
from pathlib import Path
from PIL import Image

BASE      = Path(__file__).parent.parent
INPUT_DIR = BASE / "1_input"
TIER1_DIR = BASE / "2_process" / "tier1"

DARK_THRESHOLD = 180   # pixel value below this = dark (text)
DENSITY_CUTOFF = 0.20  # row must have >= 20% of peak density to count as text


def find_band(crop_gray):
    h, w = crop_gray.shape
    if h < 3 or w < 2:
        return None
    dark = (crop_gray < DARK_THRESHOLD).astype(np.uint8)
    row_counts = dark.sum(axis=1)
    peak = row_counts.max()
    if peak == 0:
        return None
    active_indices = np.where(row_counts >= peak * DENSITY_CUTOFF)[0]
    if len(active_indices) == 0:
        return None
    return int(active_indices[0]), int(active_indices[-1])


def run(page="page_1"):
    with open(TIER1_DIR / f"{page}_ocr.json") as f:
        ocr = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("L")
    arr = np.array(img)
    H, W = arr.shape

    words = ocr.get("google", {}).get("bounding_boxes", [])
    words = [w for w in words if any(c.isalnum() for c in w["text"])]

    results = []
    skipped = 0

    for w in words:
        px_x = round(w["left"] * W)
        px_y = round(w["top"] * H)
        px_w = round(w["width"] * W)
        px_h = round(abs(w["height"]) * H)

        if px_h <= 0 or px_w <= 0:
            skipped += 1
            continue

        x0 = max(0, px_x)
        y0 = max(0, px_y)
        x1 = min(W, px_x + px_w)
        y1 = min(H, px_y + px_h)

        if x1 <= x0 or y1 <= y0:
            skipped += 1
            continue

        crop = arr[y0:y1, x0:x1]
        band = find_band(crop)

        if band is None:
            skipped += 1
            continue

        rel_top, rel_bottom = band
        abs_top    = y0 + rel_top
        abs_bottom = y0 + rel_bottom
        band_h     = abs_bottom - abs_top

        results.append({
            "text": w["text"],
            "ocr_box": {
                "left":   w["left"],
                "top":    w["top"],
                "width":  w["width"],
                "height": abs(w["height"]),
            },
            "band": {
                "top":    abs_top / H,
                "bottom": abs_bottom / H,
                "height": band_h / H,
            },
        })

    output = {
        "page": page,
        "image_size": {"w": W, "h": H},
        "dark_threshold": DARK_THRESHOLD,
        "density_cutoff": DENSITY_CUTOFF,
        "words": results,
    }

    out_path = TIER1_DIR / f"{page}_text_band.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Words processed: {len(results)}  Skipped: {skipped}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
