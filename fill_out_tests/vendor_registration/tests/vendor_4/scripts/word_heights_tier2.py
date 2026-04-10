"""
Build word_heights_raw.json (tier2).

For each word from OCR, look up its corrected band height from text_band.json.
Output one entry per word with text, position (OCR x/y), and corrected height.

Output: 2_process/tier2/font_groups/word_heights_raw.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent
TIER1_DIR = BASE / "2_process" / "tier1"
TIER2_DIR = BASE / "2_process" / "tier2" / "font_groups"


def run(page="page_1"):
    with open(TIER1_DIR / f"{page}_text_band.json") as f:
        band_data = json.load(f)

    H = band_data["image_size"]["h"]

    results = []
    for w in band_data["words"]:
        results.append({
            "text":        w["text"],
            "left":        w["ocr_box"]["left"],
            "top":         w["ocr_box"]["top"],
            "band_top":    w["band"]["top"],
            "band_bottom": w["band"]["bottom"],
            "height":      w["band"]["height"],
            "height_px":   round(w["band"]["height"] * H, 1),
        })

    results.sort(key=lambda w: (w["top"], w["left"]))

    output = {
        "page": page,
        "word_count": len(results),
        "words": results,
    }

    out_path = TIER2_DIR / "word_heights_raw.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Words: {len(results)}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
