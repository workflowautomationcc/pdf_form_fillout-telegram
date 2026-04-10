"""
Build ocr_fine_tuned.json (tier3) — definitive per-word record.

For each OCR word, find closest word_positions entry by center distance
(same logic confirmed in three_lines_test.py).
Output format matches OCR JSON: text, left, top, width, height (normalized 0-1).
Also includes height_px and font_group for downstream use.

Output: 2_process/tier3/words/ocr_fine_tuned.json
"""

import json
import math
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER1_DIR = BASE / "2_process" / "tier1"
TIER2_DIR = BASE / "2_process" / "tier2"
TIER3_DIR = BASE / "2_process" / "tier3" / "words"


def get_font_group(h_px, groups):
    for name, bounds in groups.items():
        if bounds["min_px"] <= h_px <= bounds["max_px"]:
            return name
    return "other"


def run(page="page_1"):
    with open(TIER1_DIR / f"{page}_ocr.json") as f:
        ocr_raw = json.load(f)

    with open(TIER1_DIR / f"{page}_word_positions.json") as f:
        pos_data = json.load(f)

    with open(TIER2_DIR / "font_groups" / "font_groups.json") as f:
        groups = json.load(f)

    W = pos_data["image_size"]["w"]
    H = pos_data["image_size"]["h"]

    ocr_words = [w for w in ocr_raw.get("google", {}).get("bounding_boxes", [])
                 if any(c.isalnum() for c in w["text"])]

    pos_words = pos_data["words"]
    used = set()
    results = []
    errors = []

    for ocr_w in ocr_words:
        text   = ocr_w["text"]
        ocr_cx = ocr_w["left"] + ocr_w["width"] / 2
        ocr_cy = ocr_w["top"] + abs(ocr_w["height"]) / 2

        best_idx, best_dist = None, 9999

        for i, pw in enumerate(pos_words):
            if i in used:
                continue
            pw_cx = pw["left"] + pw["width"] / 2
            pw_cy = pw["top"] + pw["height"] / 2
            dist = math.sqrt((ocr_cx - pw_cx)**2 + (ocr_cy - pw_cy)**2)
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        if best_idx is not None:
            used.add(best_idx)
            pw = pos_words[best_idx]
            height_px = round(pw["height"] * H, 1)
            results.append({
                "text":       text,
                "left":       pw["left"],
                "top":        pw["top"],
                "width":      pw["width"],
                "height":     pw["height"],
                "height_px":  height_px,
                "font_group": get_font_group(height_px, groups),
            })
        else:
            errors.append(f"NO MATCH: '{text}' left={ocr_w['left']:.4f} top={ocr_w['top']:.4f}")
            oh = abs(ocr_w["height"])
            height_px = round(oh * H, 1)
            results.append({
                "text":       text,
                "left":       ocr_w["left"],
                "top":        ocr_w["top"],
                "width":      ocr_w["width"],
                "height":     oh,
                "height_px":  height_px,
                "font_group": get_font_group(height_px, groups),
                "match":      "fallback_ocr",
            })

    results.sort(key=lambda w: (w["top"], w["left"]))

    for e in errors:
        print(f"  ERROR: {e}")

    output = {
        "page": page,
        "image_size": {"w": W, "h": H},
        "word_count": len(results),
        "error_count": len(errors),
        "words": results,
    }

    out_path = TIER3_DIR / "ocr_fine_tuned.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Words: {len(results)}  Errors: {len(errors)}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
