"""
header_detect.py (tier5)

Identifies header/title phrases.

Rules:
  - giant font_group → always header
  - large font_group → header only if nothing above it except giant phrases

Output: 2_process/tier5/header.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER4_DIR = BASE / "2_process" / "tier4"
TIER5_DIR = BASE / "2_process" / "tier5"


def run(page="page_1"):
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        data = json.load(f)

    phrases = data["phrases"]
    W = data["image_size"]["w"]
    H = data["image_size"]["h"]

    # Topmost y of any non-giant phrase (to judge if large has nothing above it)
    giant_phrases = [p for p in phrases if p["font_group"] == "giant"]
    giant_bottom  = max((p["top"] + p["height"] for p in giant_phrases), default=0)

    headers   = []
    discarded = []

    for p in phrases:
        if p["font_group"] == "giant":
            headers.append({**p, "reason": "giant"})

        elif p["font_group"] == "large":
            # Discard only if main font appears above it
            above = [
                x for x in phrases
                if x["font_group"] == "main"
                and x["top"] < p["top"]
            ]
            if not above:
                headers.append({**p, "reason": "large_topmost"})
            else:
                discarded.append({**p, "reason": "large_mid_page"})

    # Bounding box — full width, bottom extended to top of first content phrase
    if headers:
        safe_top    = 0
        header_bottom = max(p["top"] + p["height"] for p in headers)
        # First phrase below the header area (not a header itself)
        content = [p for p in phrases if p not in headers and p["top"] >= header_bottom]
        content.sort(key=lambda p: p["top"])
        safe_bottom = content[0]["top"] if content else header_bottom
        safe_left   = 0
        safe_right  = 1
    else:
        safe_top = safe_bottom = safe_left = safe_right = 0

    output = {
        "page":       page,
        "image_size": {"w": W, "h": H},
        "safe_header_box": {
            "top":    safe_top,
            "left":   safe_left,
            "bottom": safe_bottom,
            "right":  safe_right,
        },
        "header_count":    len(headers),
        "discarded_count": len(discarded),
        "headers":         headers,
        "discarded":       discarded,
    }

    TIER5_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TIER5_DIR / "header.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Headers found:    {len(headers)}")
    print(f"  Large discarded:  {len(discarded)}")
    print(f"  Safe header box:  top={safe_top:.4f}  bottom={safe_bottom:.4f}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
