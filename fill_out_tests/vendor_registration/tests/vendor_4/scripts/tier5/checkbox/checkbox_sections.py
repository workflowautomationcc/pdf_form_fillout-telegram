"""
For each checkbox band, walk upward to find the section header phrase.

Logic:
  - Look above the band
  - If another checkbox band is closer → same section, look above that band
  - Repeat until a phrase is found
  - That phrase's top = section top border

Output: 2_process/tier5/checkbox/checkbox_sections.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent.parent
TIER4_DIR = BASE / "2_process" / "tier4"
TIER5_DIR = BASE / "2_process" / "tier5" / "checkbox"
OUT_DIR   = BASE / "3_output" / "tier5" / "checkbox"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_section_header(search_top, bands, phrases):
    """Walk upward from search_top, skipping over checkbox bands, until a phrase is found."""
    current_top = search_top

    while True:
        nearest_phrase = None
        nearest_phrase_dist = 9999
        for p in phrases:
            p_bottom = p["top"] + p["height"]
            if p_bottom > current_top:
                continue
            dist = current_top - p_bottom
            if dist < nearest_phrase_dist:
                nearest_phrase_dist = dist
                nearest_phrase = p

        nearest_band = None
        nearest_band_dist = 9999
        for b in bands:
            if b["band_bottom"] > current_top:
                continue
            dist = current_top - b["band_bottom"]
            if dist < nearest_band_dist:
                nearest_band_dist = dist
                nearest_band = b

        if nearest_phrase is None:
            return None
        if nearest_band is None or nearest_phrase_dist <= nearest_band_dist:
            return nearest_phrase
        current_top = nearest_band["band_top"]


def find_section_footer(search_bottom, bands, phrases):
    """Walk downward from search_bottom, skipping over checkbox bands, until a phrase is found."""
    current_bottom = search_bottom

    while True:
        nearest_phrase = None
        nearest_phrase_dist = 9999
        for p in phrases:
            if p["top"] < current_bottom:
                continue
            dist = p["top"] - current_bottom
            if dist < nearest_phrase_dist:
                nearest_phrase_dist = dist
                nearest_phrase = p

        nearest_band = None
        nearest_band_dist = 9999
        for b in bands:
            if b["band_top"] < current_bottom:
                continue
            dist = b["band_top"] - current_bottom
            if dist < nearest_band_dist:
                nearest_band_dist = dist
                nearest_band = b

        if nearest_phrase is None:
            return None
        if nearest_band is None or nearest_phrase_dist <= nearest_band_dist:
            return nearest_phrase
        current_bottom = nearest_band["band_bottom"]


def run(page="page_1"):
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        phrases = json.load(f)["phrases"]

    with open(TIER5_DIR / "checkbox_phrases.json") as f:
        data = json.load(f)

    bands = data["bands"]
    sections = []

    for band in bands:
        header = find_section_header(band["band_top"], bands, phrases)
        footer = find_section_footer(band["band_bottom"], bands, phrases)

        section_top    = round(header["top"], 6) if header else None
        section_bottom = round(band["band_bottom"], 6)

        sections.append({
            "section_top":    section_top,
            "section_bottom": section_bottom,
            "section_header": header["text"] if header else None,
            "section_footer": footer["text"] if footer else None,
            "header_phrase":  header,
            "footer_phrase":  footer,
            "band":           band,
        })
        print(f"  Band [{round(band['band_top'],4)}-{round(band['band_bottom'],4)}]")
        print(f"    top:    \"{header['text'] if header else 'NONE'}\" @ {section_top}")
        print(f"    bottom: \"{footer['text'] if footer else 'NONE'}\" @ {section_bottom}")

    output = {"page": page, "section_count": len(sections), "sections": sections}

    out_path = TIER5_DIR / "checkbox_sections.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
