"""
Run OCR on all converted form images.

Output structure:
  tests/{vendor}/debug/ - OCR JSON per page
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

IMAGES_DIR   = Path(__file__).parent.parent / "images"
DETECTED_DIR = Path(__file__).parent.parent / "tests"
EDEN_API_URL = "https://api.edenai.run/v2/ocr/ocr"


def run_ocr(image_path):
    api_key = os.getenv("EDEN_AI_API_KEY")
    if not api_key:
        raise RuntimeError("EDEN_AI_API_KEY not set")
    with open(image_path, "rb") as f:
        response = requests.post(
            EDEN_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": f},
            data={"providers": "google", "language": "en"},
            timeout=120
        )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    form_dirs = sorted(IMAGES_DIR.iterdir()) if IMAGES_DIR.exists() else []
    if not form_dirs:
        print("No images found. Run run_test.py first.")
        sys.exit(1)

    for form_dir in form_dirs:
        if not form_dir.is_dir():
            continue

        debug_dir = DETECTED_DIR / form_dir.name / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)

        pages = sorted(form_dir.glob("page_*.png"))
        for page_path in pages:
            out_path = debug_dir / f"{page_path.stem}_ocr.json"

            if out_path.exists():
                print(f"  Skipping (exists): {form_dir.name}/{page_path.name}")
                continue

            print(f"  OCR: {form_dir.name}/{page_path.name} ...")
            try:
                result = run_ocr(page_path)
                with open(out_path, "w") as f:
                    json.dump(result, f, indent=2)
                print(f"  Saved: {out_path}")
            except Exception as e:
                print(f"  Failed: {e}")

    print("\nDone.")
