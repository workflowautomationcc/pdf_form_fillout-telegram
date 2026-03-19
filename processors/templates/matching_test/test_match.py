import json
import os

OCR_PATH = "processors/templates/matching_test/input/ocr.json"
TEMPLATE_PATH = "data/templates/ATS_001/template.json"

TOLERANCE = 10


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

    anchor = next(a for a in template["anchors"] if a["name"] == "TRUCKLOAD_RATE_CONFIRMATION")

    print("\n--- TEMPLATE ANCHOR ---")
    print(anchor)

    words = anchor["name"].split("_")
    print("\n--- BROKEN INTO WORDS ---")
    print(words)

    ocr_boxes = ocr["google"]["bounding_boxes"]

    word_matches = {word: [] for word in words}

    for box in ocr_boxes:
        text = box["text"].upper()
        if text in word_matches:
            word_matches[text].append(box)

    print("\n--- WORD MATCH COUNTS ---")
    for word, matches in word_matches.items():
        print(f"{word}: {len(matches)} matches")

    print("\n--- WORD MATCH DETAILS ---")
    for word, matches in word_matches.items():
        for m in matches:
            print(f"{word} -> top: {m['top']}, left: {m['left']}")

    # flatten all matches
    all_matches = []
    for matches in word_matches.values():
        all_matches.extend(matches)

    # group by same line
    lines = []
    for box in all_matches:
        placed = False
        for line in lines:
            if abs(box["top"] - line[0]["top"]) < 0.005:
                line.append(box)
                placed = True
                break
        if not placed:
            lines.append([box])

    print("\n--- GROUPED LINES ---")
    for i, line in enumerate(lines):
        texts = [b["text"] for b in line]
        print(f"Line {i}: {texts}")

    # find valid line
    valid_line = None
    for line in lines:
        texts = [b["text"].upper() for b in line]
        if all(word in texts for word in words):
            valid_line = line
            break

    if not valid_line:
        print("\nNO MATCH: words not aligned into one line")
        return

    print("\n--- VALID LINE FOUND ---")
    print([b["text"] for b in valid_line])

    # convert to pixel boxes
    pixel_boxes = []
    for b in valid_line:
        px = {
            "x": b["left"] * page_width,
            "y": b["top"] * page_height,
            "w": b["width"] * page_width,
            "h": b["height"] * page_height
        }
        pixel_boxes.append(px)

    print("\n--- INDIVIDUAL PIXEL BOXES ---")
    for pb in pixel_boxes:
        print(pb)

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

    print("\n--- COMBINED OCR BOX ---")
    print(combined)

    print("\n--- TEMPLATE BOX ---")
    print(anchor)

    # compare
    match = (
        abs(combined["x"] - anchor["x"]) <= TOLERANCE and
        abs(combined["y"] - anchor["y"]) <= TOLERANCE
    )

    print("\n--- RESULT ---")
    if match:
        print("MATCH")
    else:
        print("NO MATCH (position mismatch)")


if __name__ == "__main__":
    main()