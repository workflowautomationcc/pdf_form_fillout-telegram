"""
Build page_margins.json (tier4).

Detects the effective page margins by finding the outermost text boundaries
across all phrases. Used as fallback boundaries when no visible lines define
the page border.

Output: 2_process/tier4/page_margins.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER4_DIR = BASE / "2_process" / "tier4"


def run(page="page_1"):
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        data = json.load(f)

    phrases = data["phrases"]

    left_margin   = min(p["left"]                    for p in phrases)
    top_margin    = min(p["top"]                     for p in phrases)
    right_margin  = max(p["left"] + p["width"]       for p in phrases)
    bottom_margin = max(p["top"]  + p["height"]      for p in phrases)

    W = data["image_size"]["w"]
    H = data["image_size"]["h"]

    output = {
        "page":       page,
        "image_size": data["image_size"],
        "margins": {
            "left":   round(left_margin, 6),
            "top":    round(top_margin, 6),
            "right":  round(right_margin, 6),
            "bottom": round(bottom_margin, 6),
        },
        "margins_px": {
            "left":   round(left_margin * W, 1),
            "top":    round(top_margin * H, 1),
            "right":  round(right_margin * W, 1),
            "bottom": round(bottom_margin * H, 1),
        },
    }

    out_path = TIER4_DIR / "page_margins.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Left:   {round(left_margin * W, 1)}px")
    print(f"  Top:    {round(top_margin * H, 1)}px")
    print(f"  Right:  {round(right_margin * W, 1)}px")
    print(f"  Bottom: {round(bottom_margin * H, 1)}px")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
