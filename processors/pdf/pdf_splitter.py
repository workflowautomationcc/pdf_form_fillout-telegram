import os
from pdf2image import convert_from_path

def split_pdf_to_images(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    images = convert_from_path(pdf_path)

    image_paths = []

    for i, image in enumerate(images):
        path = os.path.join(output_dir, f"page_{i+1}.png")
        image.save(path, "PNG")
        image_paths.append(path)

    return image_paths