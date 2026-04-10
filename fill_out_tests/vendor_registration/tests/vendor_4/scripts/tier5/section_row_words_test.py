"""
section_row_words_test.py

Print each fine-tuned OCR "Section" word and all words whose top y
is within a fixed pixel tolerance of that Section word.
"""

import json
from pathlib import Path

BASE = Path(__file__).parent.parent.parent
TIER3_DIR = BASE / "2_process" / "tier3" / "words"

Y_TOLERANCE_PX = 20


def run(page="page_1"):
    with open(TIER3_DIR / "ocr_fine_tuned.json") as f:
        data = json.load(f)

    H = data["image_size"]["h"]
    words = data["words"]

    sections = [w for w in words if w["text"] == "Section"]

    for i, section in enumerate(sections, start=1):
        section_top_px = section["top"] * H
        row_words = []

        for word in words:
            word_top_px = word["top"] * H
            if abs(word_top_px - section_top_px) <= Y_TOLERANCE_PX:
                row_words.append((word["left"], word["text"]))

        row_words.sort(key=lambda item: item[0])
        row_text = " + ".join(text for _, text in row_words)

        print(f"{i}. Section")
        print(row_text)
        print()


if __name__ == "__main__":
    run("page_1")
