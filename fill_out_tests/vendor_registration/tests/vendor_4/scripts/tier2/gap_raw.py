"""
Build gap_raw.json (tier2).

For each row of words, compute precise pixel gap between adjacent words
using x_start/x_end from word_positions.json.

Output: 2_process/tier2/word_gaps/gap_raw.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER1_DIR = BASE / "2_process" / "tier1"
TIER2_DIR = BASE / "2_process" / "tier2"

WORD_Y_TOLERANCE = 3  # px — words within this Y = same row


def get_font_group(h, groups):
    for name, bounds in groups.items():
        if bounds["min_px"] <= h <= bounds["max_px"]:
            return name
    return "other"


def run(page="page_1"):
    with open(TIER1_DIR / f"{page}_word_positions.json") as f:
        pos_data = json.load(f)

    with open(TIER2_DIR / "font_groups" / "font_groups.json") as f:
        groups = json.load(f)

    words = pos_data["words"]

    # Group into rows by band_top proximity
    sorted_words = sorted(words, key=lambda w: w["band_top"])
    rows = []
    for w in sorted_words:
        matched = False
        for row in rows:
            if abs(w["band_top"] - row["y"]) <= WORD_Y_TOLERANCE:
                row["words"].append(w)
                matched = True
                break
        if not matched:
            rows.append({"y": w["band_top"], "words": [w]})

    for row in rows:
        row["words"].sort(key=lambda w: w["x_start"])

    # Collect gaps
    gaps = []
    for row in rows:
        ws = row["words"]
        for i in range(len(ws) - 1):
            left_w  = ws[i]
            right_w = ws[i + 1]
            gap = round(right_w["x_start"] - left_w["x_end"], 1)
            if gap < 0:
                continue
            gaps.append({
                "left_word":     left_w["text"],
                "right_word":    right_w["text"],
                "gap_px":        gap,
                "font_group":    get_font_group(left_w["height_px"], groups),
                "left_x_end":    left_w["x_end"],
                "right_x_start": right_w["x_start"],
                "band_top":      min(left_w["band_top"], right_w["band_top"]),
                "band_bottom":   max(left_w["band_bottom"], right_w["band_bottom"]),
                "y":             row["y"],
            })

    output = {
        "page": page,
        "gap_count": len(gaps),
        "gaps": sorted(gaps, key=lambda g: g["gap_px"]),
    }

    out_path = TIER2_DIR / "word_gaps" / "gap_raw.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Gaps: {len(gaps)}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
