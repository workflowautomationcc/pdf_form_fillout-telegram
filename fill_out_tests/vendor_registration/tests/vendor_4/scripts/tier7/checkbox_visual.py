"""
checkbox_visual.py (tier7)

Draws checkmarks on matched checkboxes on top of fill_visual.png.
Uses an X drawn with two diagonal lines inside the checkbox bounds.

Output: 3_output/tier7/fill_visual.png (updates in place)
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE      = Path(__file__).parent.parent.parent
TIER7_DIR = BASE / "2_process" / "tier7"
OUT_DIR   = BASE / "3_output" / "tier7"

CHECK_COLOR = (0, 0, 180)
PROJECT_ROOT = Path(__file__).parents[5]
FONT_PATH    = PROJECT_ROOT / "data" / "fonts" / "Arial.ttf"


def run():
    resolved_path   = TIER7_DIR / "checkbox_resolved.json"
    fill_visual     = OUT_DIR / "fill_visual.png"
    checkbox_visual = OUT_DIR / "fill_checkbox_visual.png"

    with open(resolved_path) as f:
        data = json.load(f)

    img  = Image.open(fill_visual).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Font for checkbox v and other write-in text
    cb_font_cache = {}

    def draw_v(cb):
        x = round(cb["x"])
        y = round(cb["y"])
        w = round(cb["w"])
        h = round(cb["h"])
        font_size = round(min(w, h) * 0.9)
        if font_size not in cb_font_cache:
            try:
                cb_font_cache[font_size] = ImageFont.truetype(str(FONT_PATH), font_size)
            except Exception:
                cb_font_cache[font_size] = ImageFont.load_default()
        font = cb_font_cache[font_size]
        bbox = draw.textbbox((0, 0), "v", font=font)
        tx   = x + (w - (bbox[2] - bbox[0])) // 2 - bbox[0]
        ty   = y + (h - (bbox[3] - bbox[1])) // 2 - bbox[1]
        draw.text((tx, ty), "v", fill=CHECK_COLOR, font=font)
        return x, y, w, h

    # Load image dimensions from field_map
    with open(BASE / "2_process" / "tier5" / "field_map.json") as f:
        fm = json.load(f)
    W = fm["image_size"]["w"]
    H = fm["image_size"]["h"]

    # Write-in font — same size as fill_visual
    try:
        write_font = ImageFont.truetype(str(FONT_PATH), 31)
    except Exception:
        write_font = ImageFont.load_default()

    for section in data["sections"]:
        if section["status"] not in ("matched", "other"):
            continue

        cb = section["checked_checkbox"]
        x, y, w, h = draw_v(cb)

        if section["status"] == "other" and section.get("other_write_zone") and section.get("client_value"):
            zone  = section["other_write_zone"]
            x0    = round(zone["left"] * W) + 10
            y0    = round(zone["top"] * H)
            zone_h = round(zone["height"] * H)
            bbox  = draw.textbbox((0, 0), section["client_value"], font=write_font)
            th    = bbox[3] - bbox[1]
            ty    = y0 + max(0, (zone_h - th) // 2) - bbox[1]
            draw.text((x0, ty), section["client_value"], fill=CHECK_COLOR, font=write_font)
            print(f"  ~ Other checked + wrote: '{section['client_value']}'")
        else:
            print(f"  ✓ Checked: {section['checked_option']} at ({x},{y})")

    img.save(checkbox_visual)
    print(f"  Base visual:     {fill_visual}")
    print(f"  Checkbox visual: {checkbox_visual}")


if __name__ == "__main__":
    run()
    print("Done.")
