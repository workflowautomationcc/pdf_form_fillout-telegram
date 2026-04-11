"""
Visualize field_map.json on original page PNG.

Draws:
  - red outline = phrase label
  - blue filled (transparent) = right space
  - green filled (transparent) = bottom space

Output: 3_output/tier5/field_map_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER5_DIR = BASE / "2_process" / "tier5"
OUT_DIR   = BASE / "3_output" / "tier5"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run(page="page_1"):
    with open(TIER5_DIR / "field_map.json") as f:
        data = json.load(f)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]

    img     = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    for field in data["fields"]:
        bs = field["bottom_space"]
        if bs:
            draw.rectangle(
                [round(bs["left"]*W), round(bs["top"]*H),
                 round((bs["left"]+bs["width"])*W), round((bs["top"]+bs["height"])*H)],
                fill=(0, 180, 0, 140), outline=(0, 0, 0), width=2
            )

        rs = field["right_space"]
        if rs:
            draw.rectangle(
                [round(rs["left"]*W), round(rs["top"]*H),
                 round((rs["left"]+rs["width"])*W), round((rs["top"]+rs["height"])*H)],
                fill=(30, 100, 220, 140), outline=(0, 0, 0), width=2
            )

        px = round(field["left"] * W)
        py = round(field["top"] * H)
        pw = round(field["width"] * W)
        ph = round(field["height"] * H)
        draw.rectangle([px, py, px+pw, py+ph], outline=(220, 0, 0, 255), width=2)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    out_path = OUT_DIR / "field_map_visual.png"
    result.save(out_path)
    print(f"  Fields: {data['field_count']}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
