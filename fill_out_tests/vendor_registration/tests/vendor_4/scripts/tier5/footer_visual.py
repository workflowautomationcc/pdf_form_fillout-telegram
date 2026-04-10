"""
footer_visual.py (tier5)

Draws the detected footer zone as a large semi-transparent rectangle
over the page image. Also outlines each matched phrase with a colored
border by group.

Colors:
  footer zone box      → red rectangle (border only, semi-transparent fill)
  group_1_issuer_info  → orange
  group_2_legal        → purple
  group_3_page_number  → cyan
  group_4_date         → yellow
  group_5_annotations  → green
  group_6_copyright    → pink
  unmatched            → gray

Input:  2_process/tier5/footer.json
        1_input/page_1.png
Output: 3_output/tier5/footer_visual.png
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE      = Path(__file__).parent.parent.parent
INPUT_DIR = BASE / "1_input"
TIER5_DIR = BASE / "2_process" / "tier5"
OUT_DIR   = BASE / "3_output" / "tier5"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUP_COLORS = {
    "group_1_issuer_info":          (255, 140,   0, 160),
    "group_2_legal_footnote":       (160,  32, 240, 160),
    "group_3_page_number":          (  0, 220, 220, 160),
    "group_4_date":                 (220, 200,   0, 160),
    "group_5_annotations":          (  0, 180,  60, 160),
    "group_6_copyright_branding":   (255, 105, 180, 160),
    "unmatched":                    (160, 160, 160, 120),
}

COLOR_FOOTER_FILL   = (220,  30,  30,  35)
COLOR_FOOTER_BORDER = (220,  30,  30, 220)


def run(page="page_1"):
    with open(TIER5_DIR / "footer.json") as f:
        data = json.load(f)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]

    img     = Image.open(INPUT_DIR / f"{page}.png").convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    # ── Footer zone rectangle ─────────────────────────────────────────────
    box = data["safe_footer_box"]
    fx0 = round(box["left"]   * W)
    fy0 = round(box["top"]    * H)
    fx1 = round(box["right"]  * W)
    fy1 = round(box["bottom"] * H)
    draw.rectangle([fx0, fy0, fx1, fy1], fill=COLOR_FOOTER_FILL, outline=COLOR_FOOTER_BORDER, width=4)

    # ── Matched phrases ───────────────────────────────────────────────────
    for p in data["footer_phrases"]:
        # Use first matched group for color
        group_id = p["groups"][0]["group"]
        color    = GROUP_COLORS.get(group_id, (200, 200, 200, 160))
        x0 = round(p["left"] * W)
        y0 = round(p["top"]  * H)
        x1 = round((p["left"] + p["width"])  * W)
        y1 = round((p["top"]  + p["height"]) * H)
        draw.rectangle([x0, y0, x1, y1], outline=color[:3] + (255,), width=2)
        draw.rectangle([x0, y0, x1, y1], fill=color)

    # ── Unmatched phrases ─────────────────────────────────────────────────
    for p in data["unmatched"]:
        color = GROUP_COLORS["unmatched"]
        x0 = round(p["left"] * W)
        y0 = round(p["top"]  * H)
        x1 = round((p["left"] + p["width"])  * W)
        y1 = round((p["top"]  + p["height"]) * H)
        draw.rectangle([x0, y0, x1, y1], outline=color[:3] + (200,), width=1)
        draw.rectangle([x0, y0, x1, y1], fill=color)

    result   = Image.alpha_composite(img, overlay).convert("RGB")
    out_path = OUT_DIR / "footer_visual.png"
    result.save(out_path)

    zone = data["group_0_footer_zone"]
    print(f"  Footer y_start:  {zone['y_start']:.4f}  ({zone['method']})")
    print(f"  Tiny font:       {zone['tiny_font_present']}")
    print(f"  Matched:         {data['matched_count']}")
    print(f"  Unmatched:       {data['unmatched_count']}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
