"""
section_detect.py (tier5)

Detect sections using only fine-tuned OCR words.

Rules:
  - find OCR word "Section"
  - find the nearest number word to the right on the same row
  - build a full-width horizontal band from the combined word heights

Output: 2_process/tier5/section.json
"""

import json
import re
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
TIER3_DIR = BASE / "2_process" / "tier3"
TIER5_DIR = BASE / "2_process" / "tier5"

Y_TOLERANCE_PX = 10
X_GAP_MAX_PX = 60
NUMBER_RE = re.compile(r"^\D*(\d+)\D*$")


def parse_number(text):
    match = NUMBER_RE.match(text.strip())
    return match.group(1) if match else None


def px_box(word, width, height):
    left = word["left"] * width
    top = word["top"] * height
    right = (word["left"] + word["width"]) * width
    bottom = (word["top"] + word["height"]) * height
    return left, top, right, bottom


def run(page="page_1"):
    with open(TIER3_DIR / "words" / "ocr_fine_tuned.json") as f:
        data = json.load(f)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]
    words = data["words"]

    section_words = [w for w in words if w["text"] == "Section"]
    number_words = [w for w in words if parse_number(w["text"])]

    sections = []

    for section_word in section_words:
        sx0, sy0, sx1, sy1 = px_box(section_word, W, H)
        best = None

        for number_word in number_words:
            nx0, ny0, nx1, ny1 = px_box(number_word, W, H)
            if nx0 < sx1:
                continue

            y_diff_px = abs(ny0 - sy0)
            x_gap_px = nx0 - sx1

            if y_diff_px > Y_TOLERANCE_PX:
                continue
            if x_gap_px > X_GAP_MAX_PX:
                continue

            score = (y_diff_px * y_diff_px) + (x_gap_px * x_gap_px)
            if best is None or score < best[0]:
                best = (score, number_word, x_gap_px, y_diff_px)

        if best is None:
            continue

        _, number_word, x_gap_px, y_diff_px = best
        _, ny0, _, ny1 = px_box(number_word, W, H)

        top_px = min(sy0, ny0)
        bottom_px = max(sy1, ny1)
        height_px = bottom_px - top_px

        sections.append({
            "text": f"Section {parse_number(number_word['text'])}",
            "left": 0.0,
            "top": top_px / H,
            "width": 1.0,
            "height": height_px / H,
            "x_gap_px": round(x_gap_px, 2),
            "y_diff_px": round(y_diff_px, 2),
            "ocr_section_word": {
                "text": section_word["text"],
                "left": section_word["left"],
                "top": section_word["top"],
                "width": section_word["width"],
                "height": section_word["height"],
            },
            "ocr_number_word": {
                "text": number_word["text"],
                "left": number_word["left"],
                "top": number_word["top"],
                "width": number_word["width"],
                "height": number_word["height"],
            },
        })

    sections.sort(key=lambda item: item["top"])

    output = {
        "page": page,
        "image_size": {"w": W, "h": H},
        "y_tolerance_px": Y_TOLERANCE_PX,
        "x_gap_max_px": X_GAP_MAX_PX,
        "section_count": len(sections),
        "sections": sections,
    }

    TIER5_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TIER5_DIR / "section.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Sections found: {len(sections)}")
    for section in sections:
        print(f"    {section['text']} top={section['top']:.4f} height={section['height']:.4f}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
