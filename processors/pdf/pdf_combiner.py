import os
from PIL import Image

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

OUTPUT_PDF_PATH = os.path.join(BASE_DIR, "data/output/final_output.pdf")


def main(png_job_folder):
    pages = []

    # page 1 (updated)
    page1_path = os.path.join(png_job_folder, "page_1.png")
    pages.append(page1_path)

    # page 2+
    i = 2
    while True:
        path = os.path.join(png_job_folder, f"page_{i}.png")
        if not os.path.exists(path):
            break
        pages.append(path)
        i += 1

    images = [Image.open(p).convert("RGB") for p in pages]

    first = images[0]
    rest = images[1:]

    os.makedirs(os.path.dirname(OUTPUT_PDF_PATH), exist_ok=True)

    first.save(
        OUTPUT_PDF_PATH,
        save_all=True,
        append_images=rest
    )