"""
Run line detection on all vendor registration forms.

Output structure:
  tests/{vendor}/annotated/  - annotated PNGs
  tests/{vendor}/debug/      - lines JSON + intermediate images
"""

import os
import sys
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))

from processors.pdf.pdf_splitter import split_pdf_to_images
from detect_fields import find_lines, annotate_lines

BASE      = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
FORMS_DIR = os.path.join(BASE, "forms")
IMAGES_DIR = os.path.join(BASE, "images")
DETECTED_DIR = os.path.join(BASE, "tests")


def process_form(pdf_path):
    name = os.path.splitext(os.path.basename(pdf_path))[0]
    print(f"\n=== Processing: {name} ===")

    img_out_dir = os.path.join(IMAGES_DIR, name)
    pages = split_pdf_to_images(pdf_path, img_out_dir)
    print(f"  Converted {len(pages)} page(s)")

    annotated_dir = os.path.join(DETECTED_DIR, name, "annotated")
    debug_dir     = os.path.join(DETECTED_DIR, name, "debug")
    os.makedirs(annotated_dir, exist_ok=True)
    os.makedirs(debug_dir, exist_ok=True)

    for page_path in pages:
        page_name = os.path.splitext(os.path.basename(page_path))[0]

        lines = find_lines(page_path, debug_dir=debug_dir)
        print(f"  Found {len(lines)} line(s) on {page_name}")

        json_path = os.path.join(debug_dir, f"{page_name}_lines.json")
        with open(json_path, "w") as f:
            json.dump(lines, f, indent=2)

        annotated_path = os.path.join(annotated_dir, f"{page_name}_annotated.png")
        annotate_lines(page_path, lines, annotated_path)


if __name__ == "__main__":
    pdfs = [f for f in os.listdir(FORMS_DIR) if f.lower().endswith(".pdf")]
    if not pdfs:
        print("No PDFs found in forms/")
        sys.exit(1)

    for pdf_file in sorted(pdfs):
        process_form(os.path.join(FORMS_DIR, pdf_file))

    print("\nDone. Check fill_out_tests/vendor_registration/tests/")
