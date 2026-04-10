"""
checkbox_prep.py (tier5)

Prepare a checkbox-detection image by:
  - converting page to grayscale
  - thresholding to black/white
  - removing text using fine-tuned OCR word boxes
  - upscaling the text-removed image 4x

Outputs:
  - 2_process/tier5/checkbox_prep.json
  - 3_output/tier5/checkbox_gray.png
  - 3_output/tier5/checkbox_thresh.png
  - 3_output/tier5/checkbox_text_removed.png
  - 3_output/tier5/checkbox_text_removed_4x.png
"""

import json
from pathlib import Path

import cv2

BASE = Path(__file__).parent.parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER3_DIR = BASE / "2_process" / "tier3"
TIER5_DIR = BASE / "2_process" / "tier5" / "checkbox"
OUT_DIR = BASE / "3_output" / "tier5" / "checkbox"
OUT_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLD = 210
TEXT_PAD_PX = 2
UPSCALE_FACTOR = 4


def run(page="page_1"):
    img_path = INPUT_DIR / f"{page}.png"
    img = cv2.imread(str(img_path))
    H, W = img.shape[:2]

    with open(TIER3_DIR / "words" / "ocr_fine_tuned.json") as f:
        words_data = json.load(f)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, THRESHOLD, 255, cv2.THRESH_BINARY_INV)
    text_removed = thresh.copy()

    removed_boxes = []
    for word in words_data["words"]:
        x0 = max(0, round(word["left"] * W) - TEXT_PAD_PX)
        y0 = max(0, round(word["top"] * H) - TEXT_PAD_PX)
        x1 = min(W, round((word["left"] + word["width"]) * W) + TEXT_PAD_PX)
        y1 = min(H, round((word["top"] + word["height"]) * H) + TEXT_PAD_PX)
        if x1 <= x0 or y1 <= y0:
            continue

        # threshold image is black background with white foreground,
        # so wiping text means painting those text boxes black.
        text_removed[y0:y1, x0:x1] = 0
        removed_boxes.append({
            "text": word["text"],
            "x": x0,
            "y": y0,
            "w": x1 - x0,
            "h": y1 - y0,
        })

    upscaled = cv2.resize(
        text_removed,
        (W * UPSCALE_FACTOR, H * UPSCALE_FACTOR),
        interpolation=cv2.INTER_CUBIC,
    )

    gray_path = OUT_DIR / "checkbox_gray.png"
    thresh_path = OUT_DIR / "checkbox_thresh.png"
    removed_path = OUT_DIR / "checkbox_text_removed.png"
    upscaled_path = OUT_DIR / "checkbox_text_removed_4x.png"

    cv2.imwrite(str(gray_path), gray)
    cv2.imwrite(str(thresh_path), thresh)
    cv2.imwrite(str(removed_path), text_removed)
    cv2.imwrite(str(upscaled_path), upscaled)

    output = {
        "page": page,
        "image_size": {"w": W, "h": H},
        "threshold": THRESHOLD,
        "text_pad_px": TEXT_PAD_PX,
        "upscale_factor": UPSCALE_FACTOR,
        "removed_word_count": len(removed_boxes),
        "outputs": {
            "gray": str(gray_path.relative_to(BASE)),
            "thresh": str(thresh_path.relative_to(BASE)),
            "text_removed": str(removed_path.relative_to(BASE)),
            "text_removed_4x": str(upscaled_path.relative_to(BASE)),
        },
    }

    out_path = TIER5_DIR / "checkbox_prep.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Removed words: {len(removed_boxes)}")
    print(f"  Saved: {out_path}")
    print(f"  Saved: {gray_path}")
    print(f"  Saved: {thresh_path}")
    print(f"  Saved: {removed_path}")
    print(f"  Saved: {upscaled_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
