import os
import json
from PIL import Image, ImageDraw

# paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
TEMPLATE_PATH = os.path.join(BASE_DIR, "data/templates/broker_001/template.json")
IMAGES_DIR = os.path.join(BASE_DIR, "data/input/images")
OUTPUT_PATH = os.path.join(BASE_DIR, "data/output/previews/test.png")


def get_latest_png():
    folders = sorted(os.listdir(IMAGES_DIR), reverse=True)
    for folder in folders:
        path = os.path.join(IMAGES_DIR, folder, "page_1.png")
        if os.path.exists(path):
            return path
    return None


def main():
    # load template
    with open(TEMPLATE_PATH, "r") as f:
        template = json.load(f)

    boxes = template["price_boxes"]

    # get image
    img_path = get_latest_png()
    if not img_path:
        print("No PNG found")
        return

    image = Image.open(img_path)
    draw = ImageDraw.Draw(image)

    w, h = image.size

    # loop through all boxes
    for box in boxes:
        x = box["left"] * w
        y = box["top"] * h
        bw = box["width"] * w
        bh = box["height"] * h

        draw.rectangle([x, y, x + bw, y + bh], fill="white")

    # save
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    image.save(OUTPUT_PATH)

    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()