"""
Word gap analysis — horizontal distance between adjacent words on the same row.

Output:
  1. word_gaps_raw.json     — every word with its left/right neighbor gap, font height
  2. word_gaps_tiers.json   — per font size group: gap distribution with counts
                              = the "friendship threshold" for phrase detection
"""

import json
from pathlib import Path
from collections import defaultdict

BASE         = Path(__file__).parent.parent
TESTS_DIR    = BASE / "tests"
IMAGES_DIR   = BASE / "images"

WORD_Y_TOLERANCE  = 5   # px — words within this Y = same row
FONT_TOLERANCE    = 4   # px — font heights within this = same font group
GAP_TOLERANCE     = 5   # px — gaps within this = same gap tier


def get_image_size(vendor, page="page_1"):
    from PIL import Image
    with Image.open(IMAGES_DIR / vendor / f"{page}.png") as img:
        return img.size


def group_by_tolerance(values, tolerance):
    """Group values within tolerance. Returns sorted list of {representative_px, count}."""
    groups = []
    for v in sorted(values):
        matched = None
        for g in groups:
            if abs(v - g["sum"] / g["count"] - 0) <= tolerance:
                # recheck against current mean
                if abs(v - g["sum"] / g["count"]) <= tolerance:
                    matched = g
                    break
        if matched:
            matched["sum"] += v
            matched["count"] += 1
        else:
            groups.append({"sum": v, "count": 1})
    return [
        {"representative_px": round(g["sum"] / g["count"], 1), "count": g["count"]}
        for g in sorted(groups, key=lambda g: g["sum"] / g["count"])
    ]


def run(vendor, page="page_1"):
    W, H = get_image_size(vendor, page)

    with open(TESTS_DIR / vendor / f"{page}_ocr.json") as f:
        ocr = json.load(f)

    words = ocr.get("google", {}).get("bounding_boxes", [])

    # Convert to pixels
    for w in words:
        w["px_x"]      = round(w["left"] * W, 1)
        w["px_y"]      = round(w["top"] * H, 1)
        w["px_w"]      = round(w["width"] * W, 1)
        w["px_h"]      = round(w["height"] * H, 1)
        w["px_x_end"]  = round(w["px_x"] + w["px_w"], 1)

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

    # -----------------------------------------------
    # 1. Raw gaps — adjacent word pairs per row
    # -----------------------------------------------
    raw_gaps = []
    for row in rows:
        ws = row["words"]
        for i, w in enumerate(ws):
            left_gap  = round(w["px_x"] - ws[i-1]["px_x_end"], 1) if i > 0 else None
            right_gap = round(ws[i+1]["px_x"] - w["px_x_end"], 1) if i < len(ws) - 1 else None
            raw_gaps.append({
                "text":       w["text"],
                "font_h_px":  w["px_h"],
                "x":          w["px_x"],
                "y":          w["px_y"],
                "left_gap_px":  left_gap,
                "right_gap_px": right_gap,
            })

    # -----------------------------------------------
    # 2. Gap tiers per font size group
    # -----------------------------------------------
    # First cluster font heights into groups
    all_font_heights = sorted(set(round(w["px_h"]) for w in words if w["px_h"] > 0))
    font_groups = []
    for fh in all_font_heights:
        matched = False
        for g in font_groups:
            if abs(fh - g["rep"]) <= FONT_TOLERANCE:
                g["members"].append(fh)
                g["rep"] = sum(g["members"]) / len(g["members"])
                matched = True
                break
        if not matched:
            font_groups.append({"rep": fh, "members": [fh]})

    font_groups.sort(key=lambda g: g["rep"])
    # Label tiers
    labels = ["tiny", "main", "large"] if len(font_groups) >= 3 else [f"tier_{i+1}" for i in range(len(font_groups))]
    if len(font_groups) == 2:
        labels = ["main", "large"]

    gap_tiers = []
    for i, fg in enumerate(font_groups):
        label = labels[i] if i < len(labels) else f"tier_{i+1}"
        font_min = min(fg["members"])
        font_max = max(fg["members"])

        # Collect all adjacent gaps for words in this font group
        gaps_in_group = []
        for entry in raw_gaps:
            if font_min - FONT_TOLERANCE <= entry["font_h_px"] <= font_max + FONT_TOLERANCE:
                if entry["right_gap_px"] is not None and entry["right_gap_px"] >= 0:
                    gaps_in_group.append(entry["right_gap_px"])

        tiers = group_by_tolerance(gaps_in_group, GAP_TOLERANCE) if gaps_in_group else []

        gap_tiers.append({
            "font_group":    label,
            "font_h_range":  {"min_px": font_min, "max_px": font_max},
            "gap_tolerance_px": GAP_TOLERANCE,
            "gap_distribution": tiers,
        })

    # -----------------------------------------------
    # Save
    # -----------------------------------------------
    out_dir = TESTS_DIR / vendor / "profile"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "word_gaps_raw.json", "w") as f:
        json.dump(raw_gaps, f, indent=2)

    with open(out_dir / "word_gaps_tiers.json", "w") as f:
        json.dump(gap_tiers, f, indent=2)

    print(f"  Words: {len(words)}  |  Rows: {len(rows)}  |  Font groups: {len(font_groups)}")
    for g in gap_tiers:
        print(f"  [{g['font_group']}] {g['font_h_range']} → {len(g['gap_distribution'])} gap tiers")
    print(f"  Saved to: {out_dir}/")


if __name__ == "__main__":
    vendor = "vendor_4"
    page   = "page_1"
    print(f"\n=== {vendor} / {page} ===")
    run(vendor, page)
    print("\nDone.")
