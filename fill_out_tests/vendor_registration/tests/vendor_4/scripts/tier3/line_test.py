"""
Test: extract one line by Y coord.

For each OCR word near target Y:
  - find closest word_positions entry by center distance (X+Y)
  - take precise coords from word_positions
  - take band from text_band at same index

Output: printed to console + 3_output/tier3/line_test.json
"""

import json
import math
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER1_DIR = BASE / "2_process" / "tier1"
OUT_DIR   = BASE / "3_output" / "tier3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_Y    = 0.3999  # normalized
Y_TOLERANCE = 0.005   # normalized


def run(page="page_1"):
    with open(TIER1_DIR / f"{page}_ocr.json") as f:
        ocr_raw = json.load(f)

    with open(TIER1_DIR / f"{page}_word_positions.json") as f:
        pos_data = json.load(f)

    with open(TIER1_DIR / f"{page}_text_band.json") as f:
        band_data = json.load(f)

    H = pos_data["image_size"]["h"]
    W = pos_data["image_size"]["w"]

    ocr_words = [w for w in ocr_raw.get("google", {}).get("bounding_boxes", [])
                 if any(c.isalnum() for c in w["text"])]

    pos_words  = pos_data["words"]
    band_words = band_data["words"]

    # Filter OCR to target line
    line_ocr = [w for w in ocr_words
                if abs((w["top"] + abs(w["height"]) / 2) - TARGET_Y) <= Y_TOLERANCE]
    line_ocr.sort(key=lambda w: w["left"])

    used = set()
    results = []

    for ocr_w in line_ocr:
        text   = ocr_w["text"]
        ocr_cx = ocr_w["left"] + ocr_w["width"] / 2
        ocr_cy = ocr_w["top"] + abs(ocr_w["height"]) / 2

        best_idx  = None
        best_dist = 9999

        for i, pw in enumerate(pos_words):
            if i in used:
                continue
            pw_cx = (pw["left"] + pw["right"]) / 2
            pw_cy = (pw["band_top"] + pw["band_bottom"]) / 2
            dist = math.sqrt((ocr_cx - pw_cx)**2 + (ocr_cy - pw_cy)**2)
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        if best_idx is not None:
            used.add(best_idx)
            pw = pos_words[best_idx]
            bw = band_words[best_idx] if best_idx < len(band_words) else None
            band_top    = bw["band"]["top"]    if bw else pw["band_top"]
            band_bottom = bw["band"]["bottom"] if bw else pw["band_bottom"]
            results.append({
                "text":        text,
                "left":        pw["left"],
                "right":       pw["right"],
                "width":       pw["width"],
                "band_top":    band_top,
                "band_bottom": band_bottom,
            })

    print(f"\n  Line at Y={TARGET_Y} (~{round(TARGET_Y*H)}px) — {len(results)} words:\n")
    for r in results:
        print(f"  '{r['text']:20s}'  left={round(r['left']*W):4d}  right={round(r['right']*W):4d}"
              f"  band={round(r['band_top']*H)}-{round(r['band_bottom']*H)}")

    out_path = OUT_DIR / "line_test.json"
    with open(out_path, "w") as f:
        json.dump({"target_y": TARGET_Y, "words": results}, f, indent=2)
    print(f"\n  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
