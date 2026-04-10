"""
Build gap_raw.json (tier3).

For each word in ocr_fine_tuned.json:
  - find nearest word to the RIGHT in the same Y band → compute gap
  - find nearest word to the LEFT in the same Y band → compute gap

Uses box edges (not centers). Deduplicates by (left_x_end, right_x_start).

Output: 2_process/tier3/word_gaps/gap_raw.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER3_DIR = BASE / "2_process" / "tier3"

WORD_Y_TOLERANCE = 0.003


def run(page="page_1"):
    with open(TIER3_DIR / "words" / "ocr_fine_tuned.json") as f:
        data = json.load(f)

    H     = data["image_size"]["h"]
    words = data["words"]

    seen = set()   # (left_x_end, right_x_start) — dedup key
    gaps = []

    for i, w in enumerate(words):
        w_right = w["left"] + w["width"]

        # --- nearest to the RIGHT ---
        best_r, best_r_dist = None, 9999
        for j, other in enumerate(words):
            if i == j:
                continue
            if abs(other["top"] - w["top"]) > WORD_Y_TOLERANCE:
                continue
            if other["left"] <= w_right:
                continue
            dist = other["left"] - w_right
            if dist < best_r_dist:
                best_r_dist = dist
                best_r = other

        # --- nearest to the LEFT ---
        best_l, best_l_dist = None, 9999
        for j, other in enumerate(words):
            if i == j:
                continue
            if abs(other["top"] - w["top"]) > WORD_Y_TOLERANCE:
                continue
            other_right = other["left"] + other["width"]
            if other_right >= w["left"]:
                continue
            dist = w["left"] - other_right
            if dist < best_l_dist:
                best_l_dist = dist
                best_l = other

        # --- record gaps (left_w always left, right_w always right) ---
        for left_w, right_w in [(w, best_r), (best_l, w)]:
            if left_w is None or right_w is None:
                continue
            lx  = round(left_w["left"] + left_w["width"], 6)
            rx  = round(right_w["left"], 6)
            gap = round(rx - lx, 6)
            if gap < 0:
                continue
            key = (lx, rx)
            if key in seen:
                continue
            seen.add(key)

            top    = min(left_w["top"], right_w["top"])
            bottom = max(left_w["top"] + left_w["height"],
                         right_w["top"] + right_w["height"])
            gaps.append({
                "left_word":     left_w["text"],
                "right_word":    right_w["text"],
                "gap":           gap,
                "gap_px":        round(gap * H, 1),
                "font_group":    left_w["font_group"],
                "left_x_end":    lx,
                "right_x_start": rx,
                "top":           top,
                "bottom":        bottom,
                "y":             left_w["top"],
            })

    gaps.sort(key=lambda g: g["gap"])

    output = {
        "page":      page,
        "gap_count": len(gaps),
        "gaps":      gaps,
    }

    out_path = TIER3_DIR / "word_gaps" / "gap_raw.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Gaps: {len(gaps)}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
