"""
For each unique gap value in the 'main' font group:
- show qty of that gap
- show one example word pair (left word + right word) with text, coords, size

Output: 2_prep/word_gaps/word_gaps_main_samples.json
"""

import json
from pathlib import Path
from PIL import Image

BASE      = Path(__file__).parent.parent
INPUT_DIR = BASE / "1_input"
PREP_DIR  = BASE / "2_prep" / "word_gaps"

WORD_Y_TOLERANCE = 5

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

    # Group into rows
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

    # Collect all main-group gaps
    gap_map = {}  # gap_value -> {count, example}
    for row in rows:
        ws = row["words"]
        for i, w in enumerate(ws):
            if w["font_group"] != "main":
                continue

            # Check right gap
            if i < len(ws) - 1:
                gap = round(ws[i+1]["px_x"] - w["px_x_end"], 1)
                if gap >= 0 and gap not in gap_map:
                    gap_map[gap] = {
                        "gap_px": gap,
                        "count": 0,
                        "example": {
                            "main_word": {"text": w["text"], "x": w["px_x"], "y": w["px_y"], "w": w["px_w"], "h": w["px_h"]},
                            "neighbor":  {"text": ws[i+1]["text"], "x": ws[i+1]["px_x"], "y": ws[i+1]["px_y"], "side": "right"},
                        }
                    }
                if gap >= 0:
                    gap_map.setdefault(gap, {"gap_px": gap, "count": 0, "example": {}})["count"] += 1

            # Check left gap
            if i > 0:
                gap = round(w["px_x"] - ws[i-1]["px_x_end"], 1)
                if gap >= 0 and gap not in gap_map:
                    gap_map[gap] = {
                        "gap_px": gap,
                        "count": 0,
                        "example": {
                            "main_word": {"text": w["text"], "x": w["px_x"], "y": w["px_y"], "w": w["px_w"], "h": w["px_h"]},
                            "neighbor":  {"text": ws[i-1]["text"], "x": ws[i-1]["px_x"], "y": ws[i-1]["px_y"], "side": "left"},
                        }
                    }
                if gap >= 0:
                    gap_map.setdefault(gap, {"gap_px": gap, "count": 0, "example": {}})["count"] += 1

    output = {
        "font_group": "main",
        "font_h_range_px": {"min": FONT_GROUPS["main"]["min"], "max": FONT_GROUPS["main"]["max"]},
        "gaps": sorted(gap_map.values(), key=lambda e: e["gap_px"])
    }

    with open(PREP_DIR / "word_gaps_step2_sample_main.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Unique gap values (main): {len(output['gaps'])}")
    print(f"  Saved: {PREP_DIR}/word_gaps_step2_sample_main.json")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
