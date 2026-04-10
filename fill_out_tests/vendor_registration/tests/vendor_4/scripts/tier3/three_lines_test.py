"""
Build precise JSON for 3 test lines using distance matching.

Lines:
  - Line 4: Tel    (Y~0.281)
  - Line 6: Email  (Y~0.3032)
  - Line 8: Contact Name (Y~0.324)

For each OCR word on those lines, find closest word_positions entry
by center distance, replace coords with precise values.

Output format matches OCR JSON: text, left, top, width, height (normalized 0-1)

Output: 3_output/tier3/three_lines_test.json
"""

import json
import math
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER1_DIR = BASE / "2_process" / "tier1"
OUT_DIR   = BASE / "3_output" / "tier3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LINES = {
    "line_4_tel":          0.281,
    "line_6_email":        0.3032,
    "line_8_contact_name": 0.324,
}
Y_TOLERANCE = 0.005


def run(page="page_1"):
    with open(TIER1_DIR / f"{page}_ocr.json") as f:
        ocr_raw = json.load(f)

    with open(TIER1_DIR / f"{page}_word_positions.json") as f:
        pos_data = json.load(f)

    H = pos_data["image_size"]["h"]
    W = pos_data["image_size"]["w"]

    ocr_words = [w for w in ocr_raw.get("google", {}).get("bounding_boxes", [])
                 if any(c.isalnum() for c in w["text"])]
    pos_words = pos_data["words"]

    output = {}
    used = set()

    for line_name, target_y in LINES.items():
        line_ocr = [w for w in ocr_words
                    if abs((w["top"] + abs(w["height"]) / 2) - target_y) <= Y_TOLERANCE]
        line_ocr.sort(key=lambda w: w["left"])

        words_out = []
        for ocr_w in line_ocr:
            ocr_cx = ocr_w["left"] + ocr_w["width"] / 2
            ocr_cy = ocr_w["top"] + abs(ocr_w["height"]) / 2

            best_idx, best_dist = None, 9999
            for i, pw in enumerate(pos_words):
                if i in used:
                    continue
                pw_cx = pw["left"] + pw["width"] / 2
                pw_cy = pw["top"] + pw["height"] / 2
                dist = math.sqrt((ocr_cx - pw_cx) ** 2 + (ocr_cy - pw_cy) ** 2)
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i

            if best_idx is not None:
                used.add(best_idx)
                pw = pos_words[best_idx]
                words_out.append({
                    "text":   ocr_w["text"],
                    "left":   pw["left"],
                    "top":    pw["top"],
                    "width":  pw["width"],
                    "height": pw["height"],
                })
            else:
                words_out.append({
                    "text":   ocr_w["text"],
                    "left":   ocr_w["left"],
                    "top":    ocr_w["top"],
                    "width":  ocr_w["width"],
                    "height": abs(ocr_w["height"]),
                    "match":  "fallback_ocr",
                })

        output[line_name] = words_out
        print(f"  {line_name}: {len(words_out)} words")

    out_path = OUT_DIR / "three_lines_test.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
