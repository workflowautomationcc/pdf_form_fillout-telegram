import json

OCR_PATH = "processors/templates/matching_test/input/ocr.json"
TEMPLATE_PATH = "data/templates/ATS_001/template.json"


def load_data():
    with open(OCR_PATH, "r") as f:
        ocr = json.load(f)

    with open(TEMPLATE_PATH, "r") as f:
        template = json.load(f)

    return ocr, template


def main():
    ocr, template = load_data()

    page_width = template["page_width"]
    page_height = template["page_height"]

    print("\n--- PAGE SIZE ---")
    print(f"width: {page_width}, height: {page_height}")

    # get template anchor
    anchor = next(a for a in template["anchors"] if a["name"] == "TRUCKLOAD_RATE_CONFIRMATION")

    print("\n--- TEMPLATE ANCHOR ---")
    print(anchor)

    # find TRUCKLOAD in OCR
    ocr_boxes = ocr["google"]["bounding_boxes"]

    truckload_boxes = [b for b in ocr_boxes if b["text"].upper() == "TRUCKLOAD"]

    print("\n--- OCR TRUCKLOAD MATCHES ---")
    for i, b in enumerate(truckload_boxes):
        print(f"{i}: top={b['top']}, left={b['left']}")

    if not truckload_boxes:
        print("\nNo TRUCKLOAD found in OCR")
        return

    # pick the one closest to top (likely header)
    selected = sorted(truckload_boxes, key=lambda b: b["top"])[0]

    print("\n--- SELECTED OCR BOX ---")
    print(selected)

    # convert to pixels
    pixel_box = {
        "x": selected["left"] * page_width,
        "y": selected["top"] * page_height,
        "w": selected["width"] * page_width,
        "h": selected["height"] * page_height
    }

    print("\n--- OCR PIXEL BOX ---")
    print(pixel_box)

    print("\n--- TEMPLATE BOX (FULL ANCHOR) ---")
    print(anchor)

    print("\n--- DIFFERENCE ---")
    print(f"x diff: {pixel_box['x'] - anchor['x']}")
    print(f"y diff: {pixel_box['y'] - anchor['y']}")


if __name__ == "__main__":
    main()