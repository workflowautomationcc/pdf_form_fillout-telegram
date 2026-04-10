"""
Build right_space.json and bottom_space.json (tier4).

For each phrase, computes:
  - right space:  from phrase right edge → nearest boundary going right
  - bottom space: from phrase bottom     → nearest boundary going down

Boundaries checked (whichever is closest wins):
  - Other phrases
  - Visible lines (horizontal for bottom, vertical for right)
  - Page margins (fallback when no visible lines)

Output: 2_process/tier4/empty_space/right_space.json
        2_process/tier4/empty_space/bottom_space.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER4_DIR = BASE / "2_process" / "tier4"


def run(page="page_1"):
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        data = json.load(f)

    with open(TIER4_DIR / "visible_lines" / "visible_lines.json") as f:
        lines_data = json.load(f)

    with open(TIER4_DIR / "page_margins.json") as f:
        margins = json.load(f)["margins"]

    phrases = data["phrases"]
    h_lines = [l for l in lines_data["lines"] if l["type"] == "horizontal"]
    v_lines = [l for l in lines_data["lines"] if l["type"] == "vertical"]

    right_spaces  = []
    bottom_spaces = []

    for p in phrases:
        p_left   = p["left"]
        p_top    = p["top"]
        p_right  = p["left"] + p["width"]
        p_bottom = p["top"]  + p["height"]

        # ── RIGHT SPACE ──────────────────────────────────────────────
        # Start from margin as outer boundary
        best_right = margins["right"]

        # Closest phrase to the right (vertically overlapping)
        for q in phrases:
            if q["left"] <= p_right:
                continue
            if q["top"] + q["height"] <= p_top or q["top"] >= p_bottom:
                continue
            if q["left"] < best_right:
                best_right = q["left"]

        # Closest vertical line to the right (vertically overlapping)
        for l in v_lines:
            lx = l["x_norm"]
            if lx <= p_right:
                continue
            if l["y_norm"] + l["h_norm"] <= p_top or l["y_norm"] >= p_bottom:
                continue
            if lx < best_right:
                best_right = lx

        r_width = best_right - p_right
        if r_width > 0:
            right_spaces.append({
                "phrase":     p["text"],
                "left":       round(p_right, 6),
                "top":        round(p_top, 6),
                "width":      round(r_width, 6),
                "height":     round(p_bottom - p_top, 6),
                "font_group": p["font_group"],
            })

        # ── BOTTOM SPACE ─────────────────────────────────────────────
        # Start from margin as outer boundary
        best_bottom = margins["bottom"]

        # Closest phrase below
        for q in phrases:
            if q["top"] > p_bottom and q["top"] < best_bottom:
                best_bottom = q["top"]

        # Closest horizontal line below
        for l in h_lines:
            ly = l["y_norm"]
            if p_bottom < ly < best_bottom:
                best_bottom = ly

        # Left/right bounds: start from margins, trim by vertical lines
        b_left  = margins["left"]
        b_right = margins["right"]
        for l in v_lines:
            lx       = l["x_norm"]
            l_top    = l["y_norm"]
            l_bottom = l_top + l["h_norm"]
            if l_bottom <= p_bottom or l_top >= best_bottom:
                continue
            if lx < p_left and lx > b_left:
                b_left = lx
            elif lx > p_right and lx < b_right:
                b_right = lx

        b_height = best_bottom - p_bottom
        b_width  = b_right - b_left
        if b_height > 0 and b_width > 0:
            bottom_spaces.append({
                "phrase":     p["text"],
                "left":       round(b_left, 6),
                "top":        round(p_bottom, 6),
                "width":      round(b_width, 6),
                "height":     round(b_height, 6),
                "gap_px":     round(b_height * data["image_size"]["h"], 1),
                "font_group": p["font_group"],
            })

    out_dir = TIER4_DIR / "empty_space"
    out_dir.mkdir(parents=True, exist_ok=True)

    right_output = {
        "page":        page,
        "image_size":  data["image_size"],
        "space_count": len(right_spaces),
        "spaces":      right_spaces,
    }
    with open(out_dir / "right_space.json", "w") as f:
        json.dump(right_output, f, indent=2)

    bottom_output = {
        "page":        page,
        "image_size":  data["image_size"],
        "space_count": len(bottom_spaces),
        "spaces":      bottom_spaces,
    }
    with open(out_dir / "bottom_space.json", "w") as f:
        json.dump(bottom_output, f, indent=2)

    print(f"  Right spaces:  {len(right_spaces)}")
    print(f"  Bottom spaces: {len(bottom_spaces)}")
    print(f"  Saved: {out_dir}/right_space.json")
    print(f"  Saved: {out_dir}/bottom_space.json")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
