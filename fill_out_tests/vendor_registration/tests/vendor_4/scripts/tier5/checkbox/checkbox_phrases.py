"""
For each checkbox candidate, find the nearest phrase to its left
(phrase right edge < checkbox left, closest vertical center match).

Output: 2_process/tier5/checkbox/checkbox_phrases.json
"""

import json
import re
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent.parent
TIER4_DIR = BASE / "2_process" / "tier4"
TIER5_DIR = BASE / "2_process" / "tier5" / "checkbox"
OUT_DIR   = BASE / "3_output" / "tier5" / "checkbox"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 2550, 3608

OTHER_PATTERN = re.compile(r"\bother\b", re.IGNORECASE)


def is_other_option(text):
    return bool(OTHER_PATTERN.search(text)) if text else False


def run(page="page_1"):
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        phrases = json.load(f)["phrases"]

    with open(TIER5_DIR / "checkbox_candidates.json") as f:
        data = json.load(f)

    results = []
    for c in data["candidates"]:
        cb_left   = c["x"] / W
        cb_top    = c["y"] / H
        cb_bottom = cb_top + c["h"] / H
        cb_cy     = (cb_top + cb_bottom) / 2

        best = None
        best_dist = 9999
        for p in phrases:
            p_right = p["left"] + p["width"]
            p_cy    = p["top"] + p["height"] / 2

            if p_right > cb_left:
                continue  # not to the left

            if p_cy < cb_top or p_cy > cb_bottom:
                continue  # outside checkbox vertical bounds

            horiz_dist = cb_left - p_right  # smaller = closer
            if horiz_dist < best_dist:
                best_dist = horiz_dist
                best = p

        phrase_text = best["text"] if best else None
        is_other    = is_other_option(phrase_text)

        # If "other" option — find right_space to the right of the checkbox
        # (empty zone where user types their custom answer)
        other_write_zone = None
        if is_other and best:
            cb_right = cb_left + c["w"] / W
            # Look for empty space to the right of the checkbox on same row
            # Approximate: zone starts at checkbox right, ends at page right boundary
            # We'll store a simple estimated zone; can be refined with right_space later
            other_write_zone = {
                "left":   round(cb_right, 6),
                "top":    round(cb_top, 6),
                "width":  round(1.0 - cb_right - 0.02, 6),   # to near right edge
                "height": round(c["h"] / H, 6),
            }

        results.append({
            "checkbox": {
                "x": c["x"], "y": c["y"], "w": c["w"], "h": c["h"],
                "x_norm": round(cb_left, 6),
                "y_norm": round(cb_top, 6),
            },
            "phrase":          best,
            "vert_dist":       round(best_dist, 6) if best else None,
            "is_other":        is_other,
            "other_write_zone": other_write_zone,
        })

    # Group checkboxes by vertical proximity (gap < checkbox height = same group)
    sorted_results = sorted(results, key=lambda r: r["checkbox"]["y_norm"])
    groups = []
    current_group = [sorted_results[0]]
    band_bottom = sorted_results[0]["checkbox"]["y_norm"] + sorted_results[0]["checkbox"]["h"] / H

    for r in sorted_results[1:]:
        cb_top = r["checkbox"]["y_norm"]
        cb_bottom = cb_top + r["checkbox"]["h"] / H
        if cb_top < band_bottom:  # overlaps with current band
            current_group.append(r)
            band_bottom = max(band_bottom, cb_bottom)
        else:
            groups.append(current_group)
            current_group = [r]
            band_bottom = cb_bottom
    groups.append(current_group)

    bands = []
    for g in groups:
        band_top    = min(r["checkbox"]["y_norm"] for r in g)
        band_bottom = max(r["checkbox"]["y_norm"] + r["checkbox"]["h"] / H for r in g)
        bands.append({
            "band_top":    round(band_top, 6),
            "band_bottom": round(band_bottom, 6),
            "checkbox_count": len(g),
            "checkboxes": [r["checkbox"]["y_norm"] for r in g],
        })
        print(f"  Band: top={round(band_top,4)} bottom={round(band_bottom,4)} ({len(g)} checkboxes)")

    output = {"page": page, "count": len(results), "bands": bands, "items": results}

    out_path = TIER5_DIR / "checkbox_phrases.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    for r in results:
        print(f"  [{round(r['checkbox']['x_norm'],3)}, {round(r['checkbox']['y_norm'],3)}] → \"{r['phrase']['text'] if r['phrase'] else 'NONE'}\"")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
