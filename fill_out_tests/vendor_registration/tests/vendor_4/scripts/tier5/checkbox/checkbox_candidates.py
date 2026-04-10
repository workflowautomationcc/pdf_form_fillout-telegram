"""
checkbox_candidates.py (tier5)

Detect checkbox-like candidates on the 4x text-removed image by:
  - finding horizontal and vertical line components
  - pairing nearby horizontal/vertical components into square-like boxes
  - rejecting boxes outside the configured size range

Outputs:
  - 2_process/tier5/checkbox_candidates.json
  - 3_output/tier5/checkbox_candidates_visual.png
"""

import json
from pathlib import Path

import cv2

BASE = Path(__file__).parent.parent.parent.parent
TIER5_DIR = BASE / "2_process" / "tier5" / "checkbox"
OUT_DIR = BASE / "3_output" / "tier5" / "checkbox"
OUT_DIR.mkdir(parents=True, exist_ok=True)

UPSCALE_FACTOR = 4
MIN_SIZE_PX_ORIGINAL = 20
MAX_SIZE_PX_ORIGINAL = 200
MIN_SIZE_PX_4X = MIN_SIZE_PX_ORIGINAL * UPSCALE_FACTOR
MAX_SIZE_PX_4X = MAX_SIZE_PX_ORIGINAL * UPSCALE_FACTOR
MAX_RATIO = 1.2
MIN_RATIO = 1 / MAX_RATIO
LINE_GAP_TOLERANCE_PX = 12


def run(page="page_1"):
    with open(TIER5_DIR / "checkbox_prep.json") as f:
        prep = json.load(f)

    image_path = BASE / prep["outputs"]["text_removed_4x"]
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    H4, W4 = img.shape

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 21))

    horizontal_mask = cv2.morphologyEx(img, cv2.MORPH_OPEN, h_kernel, iterations=1)
    vertical_mask = cv2.morphologyEx(img, cv2.MORPH_OPEN, v_kernel, iterations=1)

    horizontal_lines = []
    for cnt in cv2.findContours(horizontal_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(cnt)
        if w < MIN_SIZE_PX_4X or w > MAX_SIZE_PX_4X:
            continue
        horizontal_lines.append({"x": x, "y": y, "w": w, "h": h})

    vertical_lines = []
    for cnt in cv2.findContours(vertical_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(cnt)
        if h < MIN_SIZE_PX_4X or h > MAX_SIZE_PX_4X:
            continue
        vertical_lines.append({"x": x, "y": y, "w": w, "h": h})

    candidates = []
    for hline in horizontal_lines:
        for vline in vertical_lines:
            width = hline["w"]
            height = vline["h"]
            ratio = width / height if height else 999

            if ratio < MIN_RATIO or ratio > MAX_RATIO:
                continue
            if abs(hline["x"] - vline["x"]) > LINE_GAP_TOLERANCE_PX:
                continue
            if abs(hline["y"] - vline["y"]) > LINE_GAP_TOLERANCE_PX:
                continue

            candidates.append({
                "x_4x": min(hline["x"], vline["x"]),
                "y_4x": min(hline["y"], vline["y"]),
                "w_4x": width,
                "h_4x": height,
                "ratio": round(ratio, 4),
                "x": round(min(hline["x"], vline["x"]) / UPSCALE_FACTOR, 3),
                "y": round(min(hline["y"], vline["y"]) / UPSCALE_FACTOR, 3),
                "w": round(width / UPSCALE_FACTOR, 3),
                "h": round(height / UPSCALE_FACTOR, 3),
            })

    candidates.sort(key=lambda c: (c["y_4x"], c["x_4x"]))

    output = {
        "page": page,
        "upscale_factor": UPSCALE_FACTOR,
        "size_filter_original_px": {
            "min": MIN_SIZE_PX_ORIGINAL,
            "max": MAX_SIZE_PX_ORIGINAL,
        },
        "size_filter_4x_px": {
            "min": MIN_SIZE_PX_4X,
            "max": MAX_SIZE_PX_4X,
        },
        "ratio_filter": {
            "min": round(MIN_RATIO, 4),
            "max": round(MAX_RATIO, 4),
        },
        "horizontal_line_count": len(horizontal_lines),
        "vertical_line_count": len(vertical_lines),
        "candidate_count": len(candidates),
        "horizontal_lines": horizontal_lines,
        "vertical_lines": vertical_lines,
        "candidates": candidates,
    }

    out_path = TIER5_DIR / "checkbox_candidates.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    vis[:] = (0, 0, 0)
    for line in horizontal_lines:
        cv2.rectangle(
            vis,
            (line["x"], line["y"]),
            (line["x"] + line["w"], line["y"] + line["h"]),
            (0, 0, 220),
            -1,
        )
    for line in vertical_lines:
        cv2.rectangle(
            vis,
            (line["x"], line["y"]),
            (line["x"] + line["w"], line["y"] + line["h"]),
            (0, 180, 0),
            -1,
        )
    for c in candidates:
        x, y, w, h = c["x_4x"], c["y_4x"], c["w_4x"], c["h_4x"]
        cv2.rectangle(vis, (x, y), (x + w, y + h), (220, 180, 0), 3)

    vis_path = OUT_DIR / "checkbox_candidates_visual.png"
    cv2.imwrite(str(vis_path), vis)

    print(f"  Horizontal lines: {len(horizontal_lines)}")
    print(f"  Vertical lines:   {len(vertical_lines)}")
    print(f"  Candidates:       {len(candidates)}")
    print(f"  Saved: {out_path}")
    print(f"  Saved: {vis_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
