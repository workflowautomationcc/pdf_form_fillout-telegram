"""
Font size profiling.
Groups OCR word heights (px) into tiers with ±2px tolerance.
Outputs frequency distribution as percentage of total words.
"""

import json
from pathlib import Path
from collections import defaultdict

BASE         = Path(__file__).parent.parent
DETECTED_DIR = BASE / "tests"
IMAGES_DIR   = BASE / "images"

TOLERANCE = 2  # px


def get_image_size(vendor, page="page_1"):
    from PIL import Image
    with Image.open(IMAGES_DIR / vendor / f"{page}.png") as img:
        return img.size


def profile_fonts(vendor, page="page_1"):
    W, H = get_image_size(vendor, page)

    with open(DETECTED_DIR / vendor / "debug" / f"{page}_ocr.json") as f:
        ocr = json.load(f)

    words = ocr.get("google", {}).get("bounding_boxes", [])
    heights = [round(w["height"] * H) for w in words if w["height"] > 0]

    if not heights:
        return {}

    # Group heights with ±tolerance
    groups = {}  # representative_height -> count
    for h in sorted(heights):
        matched = None
        for rep in groups:
            if abs(h - rep) <= TOLERANCE:
                matched = rep
                break
        if matched is not None:
            groups[matched] += 1
        else:
            groups[h] = 1

    total = sum(groups.values())
    tiers = [
        {"height_px": rep, "count": count, "pct": round(count / total * 100, 1)}
        for rep, count in sorted(groups.items())
    ]

    return tiers


if __name__ == "__main__":
    vendors = sorted([d.name for d in DETECTED_DIR.iterdir() if d.is_dir()])
    for vendor in vendors:
        print(f"\n=== {vendor} ===")
        try:
            tiers = profile_fonts(vendor)
            profile_dir = DETECTED_DIR / vendor / "profile"
            profile_dir.mkdir(parents=True, exist_ok=True)
            out_path = profile_dir / "font_size_tiers.json"
            with open(out_path, "w") as f:
                json.dump(tiers, f, indent=2)
            for t in tiers:
                print(f"  {t['height_px']}px — {t['count']} words ({t['pct']}%)")
            print(f"  Saved: {out_path}")
        except Exception as e:
            import traceback; traceback.print_exc()

    print("\nDone.")
