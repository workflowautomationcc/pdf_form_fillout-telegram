"""
Build line_gap_raw.json (tier4).

For each phrase, finds the closest phrase below it and measures
the vertical gap: next_phrase.top - this_phrase.bottom.

Output: 2_process/tier4/line_gaps/line_gap_raw.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER4_DIR = BASE / "2_process" / "tier4"


def run(page="page_1"):
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        data = json.load(f)

    H = data["image_size"]["h"]
    phrases = data["phrases"]

    gaps = []

    for i, p in enumerate(phrases):
        p_bottom = p["top"] + p["height"]

        # Find closest phrase whose top is below this phrase's bottom
        best = None
        best_dist = float("inf")
        for j, q in enumerate(phrases):
            if i == j:
                continue
            if q["top"] > p_bottom:
                dist = q["top"] - p_bottom
                if dist < best_dist:
                    best_dist = dist
                    best = q

        if best is None:
            continue

        gap_norm = best_dist
        gap_px   = round(best_dist * H, 1)

        gaps.append({
            "top_phrase":    p["text"],
            "bottom_phrase": best["text"],
            "gap":           round(gap_norm, 6),
            "gap_px":        gap_px,
            "top_bottom":    round(p_bottom, 6),
            "bottom_top":    round(best["top"], 6),
        })

    # Sort by position (top of upper phrase)
    gaps.sort(key=lambda g: g["top_bottom"])

    output = {
        "page":      page,
        "gap_count": len(gaps),
        "gaps":      gaps,
    }

    out_dir = TIER4_DIR / "line_gaps"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "line_gap_raw.json"

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Phrases in:  {len(phrases)}")
    print(f"  Gaps out:    {len(gaps)}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
