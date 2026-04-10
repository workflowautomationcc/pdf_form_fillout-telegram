"""
Build ocr_fine_tuned_v2.json (tier3).

Version 2 uses word_positions.json directly as the word source.
It keeps the same output structure as ocr_fine_tuned.json and only
derives height_px and font_group from the precise word_positions boxes.

Output: 2_process/tier3/words/ocr_fine_tuned_v2.json
"""

import json
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
TIER1_DIR = BASE / "2_process" / "tier1"
TIER2_DIR = BASE / "2_process" / "tier2"
TIER3_DIR = BASE / "2_process" / "tier3" / "words"


def get_font_group(h_px, groups):
    for name, bounds in groups.items():
        if bounds["min_px"] <= h_px <= bounds["max_px"]:
            return name
    return "other"


def run(page="page_1"):
    with open(TIER1_DIR / f"{page}_word_positions.json") as f:
        pos_data = json.load(f)

    with open(TIER2_DIR / "font_groups" / "font_groups.json") as f:
        groups = json.load(f)

    W = pos_data["image_size"]["w"]
    H = pos_data["image_size"]["h"]

    results = []
    for word in pos_data["words"]:
        height_px = round(word["height"] * H, 1)
        results.append({
            "text": word["text"],
            "left": word["left"],
            "top": word["top"],
            "width": word["width"],
            "height": word["height"],
            "height_px": height_px,
            "font_group": get_font_group(height_px, groups),
        })

    results.sort(key=lambda w: (w["top"], w["left"]))

    output = {
        "page": page,
        "image_size": {"w": W, "h": H},
        "word_count": len(results),
        "error_count": 0,
        "words": results,
    }

    out_path = TIER3_DIR / "ocr_fine_tuned_v2.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Words: {len(results)}  Errors: 0")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
