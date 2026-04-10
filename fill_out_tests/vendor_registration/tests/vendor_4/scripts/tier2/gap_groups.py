"""
Build gap_groups.json (tier2).

Assigns each gap from gap_raw.json to one of 5 groups:
  tiny-friend   — tiny font,  gap <= 4px
  main-friend   — main font,  gap <= 9px
  large-friend  — large font, gap <= 13px
  giant-friend  — giant font, gap <= 18px
  separate      — any font,   gap above its friendship threshold

Output: 2_process/tier2/word_gaps/gap_groups.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER2_DIR = BASE / "2_process" / "tier2"

FRIENDSHIP = {
    "tiny":  13,
    "main":  18,
    "large": 25,
    "giant": 35,
    "other": 0,
}


def run(page="page_1"):
    with open(TIER2_DIR / "word_gaps" / "gap_raw.json") as f:
        raw = json.load(f)

    groups = {
        "tiny-friend":  [],
        "main-friend":  [],
        "large-friend": [],
        "giant-friend": [],
        "separate":     [],
    }

    for g in raw["gaps"]:
        fg = g["font_group"]
        threshold = FRIENDSHIP.get(fg, 0)
        if g["gap_px"] <= threshold:
            key = f"{fg}-friend" if fg in FRIENDSHIP and fg != "other" else "separate"
        else:
            key = "separate"
        groups[key].append(g)

    summary = {name: len(items) for name, items in groups.items()}

    output = {
        "page": page,
        "friendship_thresholds_px": FRIENDSHIP,
        "summary": summary,
        "groups": groups,
    }

    out_path = TIER2_DIR / "word_gaps" / "gap_groups.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    for name, count in summary.items():
        print(f"  {name:15s}: {count}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
