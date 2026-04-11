"""
Build fillable_fields.json (tier6).

Takes all phrases + their right/bottom empty spaces.
Excludes any that fall within blocked zones:
  - header zone
  - footer zone
  - checkbox sections

Result: only the fillable form fields remain, each with:
  - phrase text, position, font_group
  - right_space (if any)
  - bottom_space (if any)

Output: 2_process/tier6/fillable_fields.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER5_DIR = BASE / "2_process" / "tier5"
TIER6_DIR = BASE / "2_process" / "tier6"
TIER6_DIR.mkdir(parents=True, exist_ok=True)


def overlaps_zone(top, bottom, zone_top, zone_bottom):
    """Returns True if the phrase vertically overlaps the zone."""
    return top < zone_bottom and bottom > zone_top


def run(page="page_1"):
    with open(TIER5_DIR / "field_map.json") as f:
        field_map = json.load(f)

    phrases = field_map["fields"]

    with open(TIER5_DIR / "header.json") as f:
        header_box = json.load(f)["safe_header_box"]

    with open(TIER5_DIR / "footer.json") as f:
        footer_box = json.load(f)["safe_footer_box"]

    with open(TIER5_DIR / "checkbox" / "checkbox_sections.json") as f:
        checkbox_sections = json.load(f)["sections"]

    with open(TIER5_DIR / "section.json") as f:
        sections = json.load(f)["sections"]

    # Find top of first numbered/content phrase to use as header zone bottom
    content_phrases = [p for p in phrases if any(c.isdigit() for c in p["text"][:3])]
    content_phrases.sort(key=lambda p: p["top"])
    first_content_top = content_phrases[0]["top"] if content_phrases else header_box["bottom"]

    # Collect all blocked zones as (top, bottom) pairs
    blocked_zones = [
        (0, first_content_top),
        (footer_box["top"], footer_box["bottom"]),
    ]
    for s in checkbox_sections:
        if s["section_top"] is not None and s["section_bottom"] is not None:
            blocked_zones.append((s["section_top"], s["section_bottom"]))

    for s in sections:
        blocked_zones.append((s["top"], s["top"] + s["height"]))

    fields = []
    excluded = []

    for p in phrases:
        p_top    = p["top"]
        p_bottom = p["top"] + p["height"]

        # Check if phrase overlaps any blocked zone
        blocked = any(overlaps_zone(p_top, p_bottom, z[0], z[1]) for z in blocked_zones)

        if blocked:
            excluded.append(p["text"])
            continue

        fields.append({
            "text":         p["text"],
            "left":         p["left"],
            "top":          p["top"],
            "width":        p["width"],
            "height":       p["height"],
            "font_group":   p["font_group"],
            "fill_zone":    p["fill_zone"],
            "right_space":  p["right_space"],
            "bottom_space": p["bottom_space"],
        })

    output = {
        "page":          page,
        "field_count":   len(fields),
        "excluded_count": len(excluded),
        "excluded":      excluded,
        "fields":        fields,
    }

    out_path = TIER6_DIR / "fillable_fields.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Fields:   {len(fields)}")
    print(f"  Excluded: {len(excluded)}")
    for e in excluded:
        print(f"    - {e}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
