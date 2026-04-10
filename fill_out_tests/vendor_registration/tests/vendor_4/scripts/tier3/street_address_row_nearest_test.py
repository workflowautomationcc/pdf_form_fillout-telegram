"""
Scratch nearest-match test for one row only: "2. Street Address".

Logic:
  - take original OCR words from the row
  - take word_positions words from the same row
  - process OCR words left-to-right
  - for each OCR word, compare against all remaining position words
  - score by dx^2 + dy^2 using top-left coordinates
  - pick the smallest score and mark that position word as used

Output:
  - 2_process/tier3/street_address_row_nearest_test.json
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

    ocr_row = [
        w for w in ocr_words
        if abs(px_top(w, H) - anchor_top_px) <= ROW_TOLERANCE_PX
    ]
    pos_row = [
        w for w in pos_words
        if abs(px_top(w, H) - anchor_top_px) <= ROW_TOLERANCE_PX
    ]

    ocr_row.sort(key=lambda item: item["left"])
    pos_row.sort(key=lambda item: item["left"])

    remaining = list(range(len(pos_row)))
    pairs = []

    for index, ow in enumerate(ocr_row):
        best_idx = None
        best_score = None
        best_dx = None
        best_dy = None

        for candidate_idx in remaining:
            pw = pos_row[candidate_idx]
            dx = (pw["left"] - ow["left"]) * W
            dy = (pw["top"] - ow["top"]) * H
            score = (dx * dx) + (dy * dy)

            if best_score is None or score < best_score:
                best_idx = candidate_idx
                best_score = score
                best_dx = dx
                best_dy = dy

        if best_idx is None:
            break

        pw = pos_row[best_idx]
        remaining.remove(best_idx)
        pairs.append({
            "index": index,
            "ocr_text": ow["text"],
            "ocr_left": ow["left"],
            "ocr_top": ow["top"],
            "position_text": pw["text"],
            "position_left": pw["left"],
            "position_top": pw["top"],
            "position_width": pw["width"],
            "position_height": pw["height"],
            "dx_px": round(best_dx, 3),
            "dy_px": round(best_dy, 3),
            "distance_sq": round(best_score, 3),
        })

    output = {
        "page": page,
        "image_size": {"w": W, "h": H},
        "row_name": "2. Street Address",
        "row_tolerance_px": ROW_TOLERANCE_PX,
        "ocr_row_words": ocr_row,
        "position_row_words": pos_row,
        "pairs": pairs,
        "unmatched_position_words": [pos_row[i] for i in remaining],
    }

    out_path = TIER3_DIR / "street_address_row_nearest_test.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  OCR row words:      {len(ocr_row)}")
    print(f"  Position row words: {len(pos_row)}")
    print(f"  Pairs:              {len(pairs)}")
    print(f"  Unmatched boxes:    {len(remaining)}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
