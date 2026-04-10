"""
Visualize three_lines_test.json — draw word boxes for 3 test lines.

Output: 3_output/tier3/three_lines_test_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
OUT_DIR   = BASE / "3_output" / "tier3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LINE_COLORS = {
    "line_4_tel":          (200,   0,   0),
    "line_6_email":        (  0, 160,   0),
    "line_8_contact_name": ( 30, 100, 220),
}


def run(page="page_1"):
    with open(OUT_DIR / "three_lines_test.json") as f:
        data = json.load(f)

    img = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    for line_name, words in data.items():
        color = LINE_COLORS.get(line_name, (160, 160, 160))
        for w in words:
            x0 = round(w["left"] * W)
            y0 = round(w["top"] * H)
            x1 = round((w["left"] + w["width"]) * W)
            y1 = round((w["top"] + w["height"]) * H)
            if x1 > x0 and y1 > y0:
                draw.rectangle([x0, y0, x1, y1], outline=color, width=2)

    out_path = OUT_DIR / "three_lines_test_visual.png"
    img.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
