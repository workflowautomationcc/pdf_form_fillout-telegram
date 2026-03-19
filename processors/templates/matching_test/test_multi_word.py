import json

OCR_PATH = "processors/templates/matching_test/input/ocr.json"
TEMPLATE_PATH = "data/templates/ATS_001/template.json"


def load_data():
    with open(OCR_PATH, "r") as f:
        ocr = json.load(f)

    with open(TEMPLATE_PATH, "r") as f:
        template = json.load(f)

    return ocr, template


def process_anchor(anchor, ocr_boxes, page_width, page_height):
    words = anchor["name"].split("_")

    print("\n==============================")
    print("ANCHOR:", anchor["name"])
    print("WORDS:", words)

    # find matches
    matches = []
    for box in ocr_boxes:
        if box["text"].upper() in words:
            matches.append(box)

    print("\nMATCHED WORDS:")
    for m in matches:
        print(m["text"], "top:", m["top"], "left:", m["left"])

    # group by line
    lines = []
    for box in matches:
        placed = False
        for line in lines:
            if abs(box["top"] - line[0]["top"]) < 0.005:
                line.append(box)
                placed = True
                break
        if not placed:
            lines.append([box])

    print("\nLINES:")
    for i, line in enumerate(lines):
        print(i, [b["text"] for b in line])

    # find valid line
    valid_line = None
    for line in lines:
        texts = [b["text"].upper() for b in line]
        if all(word in texts for word in words):
            valid_line = line
            break

    if not valid_line:
        print("❌ NO VALID LINE FOUND")
        return

    print("\nSELECTED LINE:", [b["text"] for b in valid_line])

    # convert to pixel
    pixel_boxes = []
    for b in valid_line:
        pb = {
            "x": b["left"] * page_width,
            "y": b["top"] * page_height,
            "w": b["width"] * page_width,
            "h": b["height"] * page_height
        }
        pixel_boxes.append(pb)

    # combine
    min_x = min(b["x"] for b in pixel_boxes)
    min_y = min(b["y"] for b in pixel_boxes)
    max_x = max(b["x"] + b["w"] for b in pixel_boxes)
    max_y = max(b["y"] + b["h"] for b in pixel_boxes)

    combined = {
        "x": min_x,
        "y": min_y,
        "w": max_x - min_x,
        "h": max_y - min_y
    }

    print("\nOCR BOX:", combined)
    print("TEMPLATE BOX:", anchor)

    # compare with tolerance
    TOLERANCE = 10

    dx = abs(combined["x"] - anchor["x"])
    dy = abs(combined["y"] - anchor["y"])
    dw = abs(combined["w"] - anchor["w"])
    dh = abs(combined["h"] - anchor["h"])

    print("\nDIFF:")
    print("x:", dx, "y:", dy, "w:", dw, "h:", dh)

    if dx <= TOLERANCE and dy <= TOLERANCE and dw <= TOLERANCE and dh <= TOLERANCE:
        print("✅ MATCH")
    else:
        print("❌ NO MATCH")


def main():
    ocr, template = load_data()

    page_width = template["page_width"]
    page_height = template["page_height"]

    ocr_boxes = ocr["google"]["bounding_boxes"]

    anchors = template["anchors"]

    for anchor in anchors:
        process_anchor(anchor, ocr_boxes, page_width, page_height)


if __name__ == "__main__":
    main()