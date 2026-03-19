import os
from pdf2image import convert_from_path

def split_pdf_to_images(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    images = convert_from_path(pdf_path)

    image_paths = []

    TARGET_WIDTH = 2550

    for i, image in enumerate(images):
        # scale image to fixed width while keeping aspect ratio
        width_percent = TARGET_WIDTH / float(image.width)
        new_height = int(float(image.height) * width_percent)

        resized_image = image.resize((TARGET_WIDTH, new_height))

        path = os.path.join(output_dir, f"page_{i+1}.png")
        resized_image.save(path, "PNG")
        image_paths.append(path)

    return image_paths