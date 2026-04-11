"""
fill_visual.py (tier7)

Draws resolved fill values onto the form page image.

  - right_space fields: text drawn left-aligned, vertically centered in space
  - bottom_space fields: text drawn left-aligned, near top of space

Output: 3_output/tier7/fill_visual.png
"""

import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE       = Path(__file__).parent.parent.parent
INPUT_DIR  = BASE / "1_input"
TIER3_DIR  = BASE / "2_process" / "tier3"
TIER4_DIR  = BASE / "2_process" / "tier4"
TIER5_DIR  = BASE / "2_process" / "tier5"
TIER7_DIR  = BASE / "2_process" / "tier7"
OUT_DIR    = BASE / "3_output" / "tier7"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Path(__file__).parents[5]
FONTS_DIR    = PROJECT_ROOT / "data" / "fonts"
FONT_PATH    = FONTS_DIR / "Arial.ttf"

FILL_COLOR       = (0, 0, 180)
X_GAP_COEFF      = 1.3   # left padding = font_size * X_GAP_COEFF
Y_GAP_COEFF      = 0.3   # top padding  = font_size * Y_GAP_COEFF


def load_words():
    """Load per-word positions from ocr_fine_tuned.json."""
    with open(TIER3_DIR / "words" / "ocr_fine_tuned.json") as f:
        return json.load(f)["words"]


def first_word_left(phrase_text, phrase_top, phrase_height, words, W, H):
    """
    Find the leftmost X of the first non-numeric word in the phrase.
    Matches words that overlap vertically with the phrase row.
    Returns pixel X or None if not found.
    """
    # Tokenize phrase, find first non-numeric token
    tokens = phrase_text.split()
    first_word = None
    for t in tokens:
        clean = t.strip(".,;:()")
        if not clean.replace(".", "").replace(",", "").isdigit():
            first_word = clean.lower()
            break

    if not first_word:
        return None

    p_top    = phrase_top
    p_bottom = phrase_top + phrase_height

    for w in words:
        w_top    = w["top"]
        w_bottom = w["top"] + w["height"]
        # Vertical overlap with phrase row
        if w_top >= p_bottom or w_bottom <= p_top:
            continue
        if w["text"].lower().startswith(first_word[:4]):
            return round(w["left"] * W)

    return None


def main_font_size_px(H):
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        phrases = json.load(f)["phrases"]
    main = [p for p in phrases if p["font_group"] == "main"]
    avg_h = sum(p["height"] for p in main) / len(main)
    return round(avg_h * H)


def fit_text(text, font, draw, max_width):
    bbox = draw.textbbox((0, 0), text, font=font)
    if bbox[2] - bbox[0] <= max_width:
        return text
    while text:
        text = text[:-1]
        bbox = draw.textbbox((0, 0), text + "…", font=font)
        if bbox[2] - bbox[0] <= max_width:
            return text + "…"
    return ""


def run(page="page_1"):
    resolved_path = TIER7_DIR / "resolved_fields.json"
    if not resolved_path.exists():
        print("ERROR: resolved_fields.json not found. Run resolver first.")
        sys.exit(1)

    with open(resolved_path) as f:
        data = json.load(f)

    with open(TIER5_DIR / "field_map.json") as f:
        fm = json.load(f)
    W = fm["image_size"]["w"]
    H = fm["image_size"]["h"]

    font_size = round(main_font_size_px(H) * 1.2)
    x_pad = round(font_size * X_GAP_COEFF)
    y_pad = round(font_size * Y_GAP_COEFF)
    try:
        font = ImageFont.truetype(str(FONT_PATH), font_size)
    except Exception:
        font = ImageFont.load_default()

    words = load_words()

    img  = Image.open(INPUT_DIR / f"{page}.png").convert("RGB")
    draw = ImageDraw.Draw(img)

    filled = 0
    for field in data["resolved"]:
        value = field.get("value")
        if not value:
            continue

        zone = field["fill_zone"]

        if zone == "right" and field.get("right_space"):
            rs   = field["right_space"]
            x0   = round(rs["left"] * W) + x_pad
            xmax = round((rs["left"] + rs["width"]) * W) - x_pad

            # Align vertically with the label text, not the space
            label_top    = round(field["top"] * H)
            label_height = round(field["height"] * H)
            bbox         = draw.textbbox((0, 0), value, font=font)
            text_h       = bbox[3] - bbox[1]
            y_text       = label_top + max(0, (label_height - text_h) // 2) - bbox[1]

            value = fit_text(value, font, draw, xmax - x0)
            draw.text((x0, y_text), value, fill=FILL_COLOR, font=font)
            filled += 1

        elif zone == "bottom" and field.get("bottom_space"):
            bs   = field["bottom_space"]
            xmax = round((bs["left"] + bs["width"]) * W) - x_pad
            y0   = round(bs["top"] * H) + y_pad

            # Align X to first non-numeric word in phrase if found
            word_x = first_word_left(
                field["text"], field["top"], field["height"], words, W, H
            )
            x0 = word_x if word_x is not None else round(bs["left"] * W) + x_pad

            value = fit_text(value, font, draw, xmax - x0)
            draw.text((x0, y0), value, fill=FILL_COLOR, font=font)
            filled += 1

    out_path = OUT_DIR / "fill_visual.png"
    img.save(out_path)
    print(f"  Font size: {font_size}px")
    print(f"  Fields filled: {filled}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
