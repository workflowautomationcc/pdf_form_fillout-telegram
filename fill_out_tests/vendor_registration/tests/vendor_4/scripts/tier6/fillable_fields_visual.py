"""
Visualize fillable fields on original page PNG.

Draws:
  - gray filled = blocked zones (header, footer, checkbox sections)
  - red outline = phrase label
  - blue filled (transparent) = right space
  - green filled (transparent) = bottom space

Output: 3_output/tier6/fillable_fields_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER5_DIR = BASE / "2_process" / "tier5"
TIER6_DIR = BASE / "2_process" / "tier6"
OUT_DIR   = BASE / "3_output" / "tier6"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run(page="page_1"):
    with open(TIER6_DIR / "fillable_fields.json") as f:
        data = json.load(f)

    with open(TIER5_DIR / "field_map.json") as f:
        fm = json.load(f)
    W = fm["image_size"]["w"]
    H = fm["image_size"]["h"]

    with open(TIER5_DIR / "header.json") as f:
        header_box = json.load(f)["safe_header_box"]

    with open(TIER5_DIR / "footer.json") as f:
        footer_box = json.load(f)["safe_footer_box"]

    with open(TIER5_DIR / "checkbox" / "checkbox_sections.json") as f:
        checkbox_sections = json.load(f)["sections"]

    with open(TIER5_DIR / "section.json") as f:
        sections = json.load(f)["sections"]

    img     = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    # Blocked zones (gray outline only — no fill wash)
    def block(top, bottom, left=0.0, right=1.0):
        x0, y0 = round(left*W), round(top*H)
        x1, y1 = round(right*W), round(bottom*H)
        draw.rectangle([x0, y0, x1, y1], fill=(80, 80, 80, 160), outline=(40, 40, 40, 255), width=3)

    block(header_box["top"], header_box["bottom"], header_box["left"], header_box["right"])
    block(footer_box["top"], footer_box["bottom"], footer_box["left"], footer_box["right"])
    for s in checkbox_sections:
        if s["section_top"] and s["section_bottom"]:
            block(s["section_top"], s["section_bottom"])
    for s in sections:
        block(s["top"], s["top"] + s["height"], 0.0, 1.0)

    # Fillable fields
    for field in data["fields"]:
        # Bottom space (green) — drawn first so blue sits on top
        bs = field["bottom_space"]
        if bs:
            draw.rectangle(
                [round(bs["left"]*W), round(bs["top"]*H),
                 round((bs["left"]+bs["width"])*W), round((bs["top"]+bs["height"])*H)],
                fill=(0, 180, 0, 140), outline=(0, 0, 0), width=2
            )

        # Right space (blue)
        rs = field["right_space"]
        if rs:
            draw.rectangle(
                [round(rs["left"]*W), round(rs["top"]*H),
                 round((rs["left"]+rs["width"])*W), round((rs["top"]+rs["height"])*H)],
                fill=(30, 100, 220, 140), outline=(0, 0, 0), width=2
            )

        # Phrase label (red outline)
        px = round(field["left"] * W)
        py = round(field["top"] * H)
        pw = round(field["width"] * W)
        ph = round(field["height"] * H)
        draw.rectangle([px, py, px+pw, py+ph], outline=(220, 0, 0, 255), width=2)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    out_path = OUT_DIR / "fillable_fields_visual.png"
    result.save(out_path)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
