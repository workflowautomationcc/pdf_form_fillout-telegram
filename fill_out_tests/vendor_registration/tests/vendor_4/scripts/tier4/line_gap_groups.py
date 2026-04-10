"""
Build line_gap_groups.json (tier4).

Classifies each vertical line gap as 'friend' or 'separate'
using per-font-group thresholds (smallest observed gap x2).

Thresholds (px):
    tiny:  74
    main:  30
    large: 52
    giant: 40
    other: 88

Output: 2_process/tier4/line_gaps/line_gap_groups.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER4_DIR = BASE / "2_process" / "tier4"

THRESHOLDS = {
    "tiny":  74,
    "main":  30,
    "large": 52,
    "giant": 40,
    "other": 88,
}


def run(page="page_1"):
    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        phrases = json.load(f)

    with open(TIER4_DIR / "line_gaps" / "line_gap_raw.json") as f:
        raw = json.load(f)

    phrase_map = {p["text"]: p["font_group"] for p in phrases["phrases"]}

    groups = {"friend": [], "separate": []}

    for g in raw["gaps"]:
        fg        = phrase_map.get(g["top_phrase"], "other")
        threshold = THRESHOLDS.get(fg, 88)
        g["font_group"] = fg
        if g["gap_px"] <= threshold:
            groups["friend"].append(g)
        else:
            groups["separate"].append(g)

    summary = {name: len(items) for name, items in groups.items()}

    output = {
        "page":       page,
        "thresholds": THRESHOLDS,
        "summary":    summary,
        "groups":     groups,
    }

    out_path = TIER4_DIR / "line_gaps" / "line_gap_groups.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    for name, count in summary.items():
        print(f"  {name:10s}: {count}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
