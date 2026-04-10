"""
Count horizontal gaps between adjacent words on the same row.
Groups by font size tier.

Font groups:
  giant: 55-85px
  large: 45-50px
  main:  25.8-44px
  tiny:  below 25.7px

Output:
  2_prep/word_gaps/raw.json - every word with left/right neighbor gap + font group
"""

import json
from pathlib import Path
from PIL import Image

BASE      = Path(__file__).parent.parent
INPUT_DIR = BASE / "1_input"
PREP_DIR  = BASE / "2_prep" / "word_gaps"

WORD_Y_TOLERANCE = 5  # px — words within this Y = same row

with open(BASE / "2_prep" / "font_sizes" / "font_groups.json") as _f:
    _raw = json.load(_f)
FONT_GROUPS = {k: {"min": v["min_px"], "max": v["max_px"]} for k, v in _raw.items()}


def get_font_group(h):
    for name, bounds in FONT_GROUPS.items():
        if bounds["min"] <= h <= bounds["max"]:
            return name
    return "other"


def run(page="page_1"):
    with open(INPUT_DIR / f"{page}_ocr.json") as f:
        ocr = json.load(f)

    with Image.open(INPUT_DIR / f"{page}.png") as img:
        W, H = img.size

    words = ocr.get("google", {}).get("bounding_boxes", [])

    # Filter out punctuation-only tokens
    words = [w for w in words if any(c.isalnum() for c in w["text"])]

    for w in words:
        w["px_x"]      = round(w["left"] * W, 1)
        w["px_y"]      = round(w["top"] * H, 1)
        w["px_w"]      = round(w["width"] * W, 1)
        w["px_h"]      = round(w["height"] * H, 1)
        w["px_x_end"]  = round(w["px_x"] + w["px_w"], 1)
        w["font_group"] = get_font_group(w["px_h"])

    # Group words into rows by Y proximity
    sorted_words = sorted(words, key=lambda w: w["px_y"])
    rows = []
    for w in sorted_words:
        matched = False
        for row in rows:
            if abs(w["px_y"] - row["y"]) <= WORD_Y_TOLERANCE:
                row["words"].append(w)
                matched = True
                break
        if not matched:
            rows.append({"y": w["px_y"], "words": [w]})

    for row in rows:
        row["words"].sort(key=lambda w: w["px_x"])

    # Collect all right-side gaps per font group
    gaps_by_group = {name: [] for name in FONT_GROUPS}

    for row in rows:
        ws = row["words"]
        for i, w in enumerate(ws):
            if i < len(ws) - 1:
                right_gap = round(ws[i+1]["px_x"] - w["px_x_end"], 1)
                if right_gap >= 0:
                    group = w["font_group"]
                    if group in gaps_by_group:
                        gaps_by_group[group].append(right_gap)

    raw = {
        name: {
            "font_h_range_px": {"min": FONT_GROUPS[name]["min"], "max": FONT_GROUPS[name]["max"]},
            "gaps": sorted(gaps_by_group[name])
        }
        for name in FONT_GROUPS
    }

    with open(PREP_DIR / "word_gaps_step1_count_raw.json", "w") as f:
        json.dump(raw, f, indent=2)

    print(f"  Words: {len(words)}  Rows: {len(rows)}")
    for name, data in raw.items():
        print(f"  [{name}] {len(data['gaps'])} gaps")
    print(f"  Saved: {PREP_DIR}/word_gaps_step1_count_raw.json")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
