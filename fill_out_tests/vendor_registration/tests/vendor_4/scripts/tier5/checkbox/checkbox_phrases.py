"""
For each checkbox candidate, find the nearest phrase to its left
(phrase right edge < checkbox left, closest vertical center match).

Output: 2_process/tier5/checkbox/checkbox_phrases.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent.parent
TIER4_DIR = BASE / "2_process" / "tier4"
TIER5_DIR = BASE / "2_process" / "tier5" / "checkbox"
OUT_DIR   = BASE / "3_output" / "tier5" / "checkbox"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 2550, 3608


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

        results.append({
            "checkbox": {
                "x": c["x"], "y": c["y"], "w": c["w"], "h": c["h"],
                "x_norm": round(cb_left, 6),
                "y_norm": round(cb_top, 6),
            },
            "phrase": best,
            "vert_dist": round(best_dist, 6) if best else None,
        })

    output = {"page": page, "count": len(results), "items": results}

    out_path = TIER5_DIR / "checkbox_phrases.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    for r in results:
        print(f"  [{round(r['checkbox']['x_norm'],3)}, {round(r['checkbox']['y_norm'],3)}] → \"{r['phrase']['text'] if r['phrase'] else 'NONE'}\"")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
