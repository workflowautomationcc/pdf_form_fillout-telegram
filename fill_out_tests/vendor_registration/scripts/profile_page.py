"""
Step 2: Document profiling — page 1 of each vendor form.

Collects:
1. Font size tiers
2. Text line spacing tiers (between lines of text)
3. Structural line spacing tiers (between detected lines, h and v separately)
4. Empty area containers (large regions with no text and no lines)
5. Numbering sequence (1,2,3... with increasing Y)
6. Word gap tiers (horizontal distance between words: phrase vs block)
"""

import json
import re
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans

BASE         = Path(__file__).parent.parent
DETECTED_DIR = BASE / "tests"
IMAGES_DIR   = BASE / "images"


def load_ocr(vendor, page="page_1"):
    with open(DETECTED_DIR / vendor / "debug" / f"{page}_ocr.json") as f:
        return json.load(f)


def load_lines(vendor, page="page_1"):
    with open(DETECTED_DIR / vendor / "debug" / f"{page}_lines.json") as f:
        return json.load(f)


def get_image_size(vendor, page="page_1"):
    from PIL import Image
    with Image.open(IMAGES_DIR / vendor / f"{page}.png") as img:
        return img.size  # (W, H)


def cluster_values(values, n_clusters=3):
    """Cluster a list of values into n groups, return tier boundaries."""
    if len(values) < n_clusters:
        return sorted(set(round(v, 1) for v in values))
    arr = np.array(values).reshape(-1, 1)
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=0).fit(arr)
    centers = sorted([round(float(c[0]), 1) for c in km.cluster_centers_])
    return centers


def profile(vendor):
    W, H = get_image_size(vendor)
    ocr   = load_ocr(vendor)
    lines = load_lines(vendor)
    words = ocr.get("google", {}).get("bounding_boxes", [])

    # Convert to pixels
    for w in words:
        w["px_x"] = w["left"] * W
        w["px_y"] = w["top"] * H
        w["px_w"] = w["width"] * W
        w["px_h"] = w["height"] * H

    # -------------------------
    # 1. Font size tiers
    # -------------------------
    heights = [w["px_h"] for w in words if w["px_h"] > 2]
    font_tiers = cluster_values(heights, n_clusters=3)

    # -------------------------
    # 2. Text line spacing tiers
    # Group words into text rows by Y proximity (within 5px = same row)
    # -------------------------
    sorted_words = sorted(words, key=lambda w: w["px_y"])
    text_rows = []
    current_row_y = None
    for w in sorted_words:
        if current_row_y is None or abs(w["px_y"] - current_row_y) > 5:
            text_rows.append(w["px_y"])
            current_row_y = w["px_y"]

    text_row_gaps = [text_rows[i+1] - text_rows[i] for i in range(len(text_rows)-1) if text_rows[i+1] - text_rows[i] > 2]
    text_line_spacing_tiers = cluster_values(text_row_gaps, n_clusters=2) if len(text_row_gaps) >= 2 else text_row_gaps

    # -------------------------
    # 3. Structural line spacing tiers
    # -------------------------
    h_lines = sorted([l for l in lines if l["type"] == "horizontal"], key=lambda l: l["y"])
    v_lines = sorted([l for l in lines if l["type"] == "vertical"],   key=lambda l: l["x"])

    h_gaps = [h_lines[i+1]["y"] - h_lines[i]["y"] for i in range(len(h_lines)-1) if h_lines[i+1]["y"] - h_lines[i]["y"] > 0]
    v_gaps = [v_lines[i+1]["x"] - v_lines[i]["x"] for i in range(len(v_lines)-1) if v_lines[i+1]["x"] - v_lines[i]["x"] > 0]

    h_line_spacing_tiers = cluster_values(h_gaps, n_clusters=2) if len(h_gaps) >= 2 else h_gaps
    v_line_spacing_tiers = cluster_values(v_gaps, n_clusters=2) if len(v_gaps) >= 2 else v_gaps

    # -------------------------
    # 4. Empty area containers
    # Scan page in horizontal strips, find strips with no text and no lines
    # -------------------------
    STRIP_H = 20  # px per strip
    occupied_ys = set()
    for w in words:
        for y in range(int(w["px_y"]), int(w["px_y"] + w["px_h"]) + 1):
            occupied_ys.add(y // STRIP_H)
    for l in lines:
        for y in range(int(l["y"]), int(l["y"] + l["h"]) + 1):
            occupied_ys.add(y // STRIP_H)

    all_strips = set(range(H // STRIP_H))
    empty_strips = sorted(all_strips - occupied_ys)

    # Group consecutive empty strips into containers
    empty_containers = []
    if empty_strips:
        group_start = empty_strips[0]
        prev = empty_strips[0]
        for s in empty_strips[1:]:
            if s - prev > 1:
                h = (prev - group_start + 1) * STRIP_H
                if h > 40:  # ignore tiny gaps
                    empty_containers.append({"x": 0, "y": group_start * STRIP_H, "w": W, "h": h})
                group_start = s
            prev = s
        h = (prev - group_start + 1) * STRIP_H
        if h > 40:
            empty_containers.append({"x": 0, "y": group_start * STRIP_H, "w": W, "h": h})

    # -------------------------
    # 5. Numbering sequence
    # -------------------------
    number_re = re.compile(r'^\d+[\.\)]?$')
    numbered = [(w["text"], w["px_y"]) for w in words if number_re.match(w["text"].strip())]
    numbered.sort(key=lambda x: x[1])
    nums_only = [int(re.sub(r'\D', '', n[0])) for n in numbered if re.sub(r'\D', '', n[0])]
    has_sequence = False
    if len(nums_only) >= 3:
        for i in range(len(nums_only)-2):
            if nums_only[i+1] == nums_only[i]+1 and nums_only[i+2] == nums_only[i]+2:
                has_sequence = True
                break

    # -------------------------
    # 6. Word gap tiers (horizontal)
    # -------------------------
    row_map = {}
    for w in words:
        row_key = round(w["px_y"] / 10)
        row_map.setdefault(row_key, []).append(w)

    h_word_gaps = []
    for row_words in row_map.values():
        sorted_row = sorted(row_words, key=lambda w: w["px_x"])
        for i in range(len(sorted_row)-1):
            gap = sorted_row[i+1]["px_x"] - (sorted_row[i]["px_x"] + sorted_row[i]["px_w"])
            if gap > 0:
                h_word_gaps.append(round(gap, 1))

    word_gap_tiers = cluster_values(h_word_gaps, n_clusters=2) if len(h_word_gaps) >= 2 else h_word_gaps

    return {
        "vendor": vendor,
        "page": "page_1",
        "image_size": {"w": W, "h": H},
        "font_size_tiers_px": font_tiers,
        "text_line_spacing_tiers_px": text_line_spacing_tiers,
        "structural_line_spacing": {
            "horizontal_tiers_px": h_line_spacing_tiers,
            "vertical_tiers_px": v_line_spacing_tiers,
        },
        "empty_area_containers": empty_containers,
        "numbering_sequence": {
            "detected": has_sequence,
            "numbers_found": [n[0] for n in numbered],
        },
        "word_gap_tiers_px": word_gap_tiers,
    }


if __name__ == "__main__":
    vendors = sorted([d.name for d in DETECTED_DIR.iterdir() if d.is_dir()])
    for vendor in vendors:
        print(f"\n=== {vendor} ===")
        try:
            p = profile(vendor)
            profile_dir = DETECTED_DIR / vendor / "profile"
            profile_dir.mkdir(parents=True, exist_ok=True)

            for key in ["font_size_tiers_px", "text_line_spacing_tiers_px", "structural_line_spacing",
                        "empty_area_containers", "numbering_sequence", "word_gap_tiers_px"]:
                with open(profile_dir / f"{key}.json", "w") as f:
                    json.dump(p[key], f, indent=2)

            out_path = profile_dir / "full_profile.json"
            with open(out_path, "w") as f:
                json.dump(p, f, indent=2)
            print(f"  Font tiers:      {p['font_size_tiers_px']}")
            print(f"  Text line gaps:  {p['text_line_spacing_tiers_px']}")
            print(f"  H-line gaps:     {p['structural_line_spacing']['horizontal_tiers_px']}")
            print(f"  V-line gaps:     {p['structural_line_spacing']['vertical_tiers_px']}")
            print(f"  Empty areas:     {len(p['empty_area_containers'])}")
            print(f"  Numbered:        {p['numbering_sequence']['detected']}")
            print(f"  Word gap tiers:  {p['word_gap_tiers_px']}")
            print(f"  Saved: {profile_dir}/")
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  Failed: {e}")

    print("\nDone.")
