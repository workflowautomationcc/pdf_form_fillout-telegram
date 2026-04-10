"""
Scratch test for one row only: "2. Street Address".

Uses:
  - original OCR row words
  - word_positions row boxes

Matching is intentionally simple:
  - isolate the row around OCR word "2."
  - take the full x range for that y band
  - isolate word_positions row by the same y band
  - pair left-to-right by index

Outputs:
  - 2_process/tier3/street_address_row_test.json
"""

import json
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
TIER1_DIR = BASE / "2_process" / "tier1"
TIER3_DIR = BASE / "2_process" / "tier3"

ROW_TOLERANCE_PX = 20


def px_top(word, height):
    return word["top"] * height


def run(page="page_1"):
    with open(TIER1_DIR / f"{page}_ocr.json") as f:
        ocr_data = json.load(f)

    with open(TIER1_DIR / f"{page}_word_positions.json") as f:
        pos_data = json.load(f)

    W = pos_data["image_size"]["w"]
    H = pos_data["image_size"]["h"]

    ocr_words = [w for w in ocr_data["google"]["bounding_boxes"] if w.get("text")]
    pos_words = pos_data["words"]

    anchor = next(w for w in ocr_words if w["text"] == "2.")
    anchor_top_px = px_top(anchor, H)

    ocr_row = []
    for w in sorted(ocr_words, key=lambda item: (item["top"], item["left"])):
        if abs(px_top(w, H) - anchor_top_px) > ROW_TOLERANCE_PX:
            continue
        ocr_row.append(w)

    pos_row = [
        w for w in pos_words
        if abs(px_top(w, H) - anchor_top_px) <= ROW_TOLERANCE_PX
    ]

    ocr_row.sort(key=lambda item: item["left"])
    pos_row.sort(key=lambda item: item["left"])

    pair_count = min(len(ocr_row), len(pos_row))
    pairs = []
    for i in range(pair_count):
        ow = ocr_row[i]
        pw = pos_row[i]
        pairs.append({
            "index": i,
            "ocr_text": ow["text"],
            "ocr_left": ow["left"],
            "ocr_top": ow["top"],
            "position_text": pw["text"],
            "position_left": pw["left"],
            "position_top": pw["top"],
            "position_width": pw["width"],
            "position_height": pw["height"],
        })

    output = {
        "page": page,
        "image_size": {"w": W, "h": H},
        "row_name": "2. Street Address",
        "row_tolerance_px": ROW_TOLERANCE_PX,
        "ocr_row_words": ocr_row,
        "position_row_words": pos_row,
        "pairs": pairs,
    }

    out_path = TIER3_DIR / "street_address_row_test.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  OCR row words:      {len(ocr_row)}")
    print(f"  Position row words: {len(pos_row)}")
    print(f"  Pairs:              {len(pairs)}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
