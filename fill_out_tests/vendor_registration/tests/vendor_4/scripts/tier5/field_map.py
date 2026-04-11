"""
Build field_map.json (tier5).

Combines phrases + right_space + bottom_space into one record per phrase.
No exclusions — raw complete map of all detected fields and their spaces.

Output: 2_process/tier5/field_map.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER4_DIR = BASE / "2_process" / "tier4"
TIER5_DIR = BASE / "2_process" / "tier5"
TIER5_DIR.mkdir(parents=True, exist_ok=True)


def run(page="page_1"):
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        data = json.load(f)

    with open(TIER4_DIR / "empty_space" / "right_space.json") as f:
        right_spaces = {s["phrase"]: s for s in json.load(f)["spaces"]}

    with open(TIER4_DIR / "empty_space" / "bottom_space.json") as f:
        bottom_spaces = {s["phrase"]: s for s in json.load(f)["spaces"]}

    fields = []
    for p in data["phrases"]:
        right  = right_spaces.get(p["text"])
        bottom = bottom_spaces.get(p["text"])

        if bottom and right and bottom["height"] >= right["height"] * 1.5:
            fill_zone = "bottom"
        elif right:
            fill_zone = "right"
        elif bottom:
            fill_zone = "bottom"
        else:
            fill_zone = None

        fields.append({
            "text":        p["text"],
            "left":        p["left"],
            "top":         p["top"],
            "width":       p["width"],
            "height":      p["height"],
            "font_group":  p["font_group"],
            "fill_zone":   fill_zone,
            "right_space": right,
            "bottom_space": bottom,
        })

    output = {
        "page":        page,
        "image_size":  data["image_size"],
        "field_count": len(fields),
        "fields":      fields,
    }

    out_path = TIER5_DIR / "field_map.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Fields: {len(fields)}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
