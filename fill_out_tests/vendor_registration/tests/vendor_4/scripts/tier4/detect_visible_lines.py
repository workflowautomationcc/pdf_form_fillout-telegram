"""
Detect visible horizontal and vertical lines in vendor_4 page_1.

Uses morphological operations to find drawn rules/borders (not text lines).
Outputs pixel coordinates + normalized coordinates.

Output: 2_process/tier4/visible_lines/visible_lines.json
        3_output/tier4/visible_lines_visual.png
"""

import json
import cv2
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER4_DIR = BASE / "2_process" / "tier4"
OUT_DIR   = BASE / "3_output" / "tier4"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run(page="page_1"):
    img_path = INPUT_DIR / f"{page}.png"
    img  = cv2.imread(str(img_path))
    H, W = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY_INV)

    # Horizontal lines
    h_kernel   = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
    horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=2)

    # Vertical lines
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
    vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel, iterations=2)

    shapes = []

    for cnt in cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > h * 10 and w >= 50:
            shapes.append({
                "x": x, "y": y, "w": w, "h": h,
                "x_norm": round(x / W, 6), "y_norm": round(y / H, 6),
                "w_norm": round(w / W, 6), "h_norm": round(h / H, 6),
                "type": "horizontal"
            })

    for cnt in cv2.findContours(vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(cnt)
        if h > w * 10 and h >= 50:
            shapes.append({
                "x": x, "y": y, "w": w, "h": h,
                "x_norm": round(x / W, 6), "y_norm": round(y / H, 6),
                "w_norm": round(w / W, 6), "h_norm": round(h / H, 6),
                "type": "vertical"
            })

    # Remove lines that overlap with any phrase bounding box (text glitches)
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        phrases = json.load(f)["phrases"]

    def overlaps_phrase(s):
        lx0 = s["x_norm"]
        ly0 = s["y_norm"]
        lx1 = lx0 + s["w_norm"]
        ly1 = ly0 + s["h_norm"]
        for p in phrases:
            px0 = p["left"]
            py0 = p["top"]
            px1 = px0 + p["width"]
            py1 = py0 + p["height"]
            if lx0 < px1 and lx1 > px0 and ly0 < py1 and ly1 > py0:
                return True
        return False

    shapes = [s for s in shapes if not overlaps_phrase(s)]
    shapes.sort(key=lambda s: s["y"])

    output = {
        "page":       page,
        "image_size": {"w": W, "h": H},
        "line_count": len(shapes),
        "lines":      shapes,
    }

    out_dir = TIER4_DIR / "visible_lines"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "visible_lines.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    # Visual
    vis = img.copy()
    colors = {"horizontal": (0, 0, 220), "vertical": (0, 180, 0)}
    for s in shapes:
        color = colors.get(s["type"], (128, 128, 128))
        cv2.rectangle(vis, (s["x"], s["y"]), (s["x"] + s["w"], s["y"] + s["h"]), color, 2)
    cv2.imwrite(str(OUT_DIR / "visible_lines_visual.png"), vis)

    h_count = sum(1 for s in shapes if s["type"] == "horizontal")
    v_count = sum(1 for s in shapes if s["type"] == "vertical")
    print(f"  Horizontal: {h_count}")
    print(f"  Vertical:   {v_count}")
    print(f"  Saved: {out_path}")
    print(f"  Saved: {OUT_DIR / 'visible_lines_visual.png'}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
