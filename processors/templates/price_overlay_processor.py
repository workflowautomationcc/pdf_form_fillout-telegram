import os
import json
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
TEMPLATE_PATH = os.path.join(BASE_DIR, "data/templates/broker_001/template.json")
FONT_PATH = os.path.join(BASE_DIR, "data/fonts/arial.ttf")

TEST_VALUE = "4,200.00"
Y_OFFSET_RATIO = -0.15


def fit_font_to_box(draw, text, font_path, target_w, target_h, max_size=300):
    best_font = None

    for size in range(1, max_size + 1):
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        if text_w <= target_w and text_h <= target_h:
            best_font = font
        else:
            break

    return best_font


def main(png_job_folder):
    with open(TEMPLATE_PATH, "r") as f:
        template = json.load(f)

    boxes = template["price_boxes"]

    img_path = os.path.join(png_job_folder, "page_1.png")

    image = Image.open(img_path)
    draw = ImageDraw.Draw(image)

    img_w, img_h = image.size

    for box in boxes:
        x = box["left"] * img_w
        y = box["top"] * img_h
        bw = box["width"] * img_w
        bh = box["height"] * img_h

        draw.rectangle([x, y, x + bw, y + bh], fill="white")

        font = fit_font_to_box(draw, TEST_VALUE, FONT_PATH, bw, bh)

        bbox = draw.textbbox((0, 0), TEST_VALUE, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        text_x = x + (bw - text_w) / 2
        offset = bh * Y_OFFSET_RATIO
        text_y = y + (bh - text_h) / 2 + offset

        draw.text((text_x, text_y), TEST_VALUE, fill="#333333", font=font)

    image.save(img_path)