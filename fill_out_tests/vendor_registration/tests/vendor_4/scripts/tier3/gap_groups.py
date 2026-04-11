"""
Build gap_groups.json (tier3).

Assigns each gap from gap_raw.json to one of 5 groups:
  tiny-friend   — tiny font,  gap <= 13px
  main-friend   — main font,  gap <= 18px
  large-friend  — large font, gap <= 25px
  giant-friend  — giant font, gap <= 35px
  separate      — gap above its font's friendship threshold

Output: 2_process/tier3/word_gaps/gap_groups.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER3_DIR = BASE / "2_process" / "tier3"

FRIENDSHIP = {
    "tiny":  50,
    "main":  100,
    "large": 80,
    "giant": 110,
    "other": 0,
}


def run(page="page_1"):
    with open(TIER3_DIR / "word_gaps" / "gap_raw.json") as f:
        raw = json.load(f)

    groups = {
        "tiny-friend":  [],
        "main-friend":  [],
        "large-friend": [],
        "giant-friend": [],
        "separate":     [],
    }

    for g in raw["gaps"]:
        fg        = g["font_group"]
        threshold = FRIENDSHIP.get(fg, 0)
        if fg in ("tiny", "main", "large", "giant") and g["gap_px"] <= threshold:
            key = f"{fg}-friend"
        else:
            key = "separate"
        groups[key].append(g)

    summary = {name: len(items) for name, items in groups.items()}

    output = {
        "page":                    page,
        "friendship_thresholds_px": FRIENDSHIP,
        "summary":                 summary,
        "groups":                  groups,
    }

    out_path = TIER3_DIR / "word_gaps" / "gap_groups.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    for name, count in summary.items():
        print(f"  {name:15s}: {count}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
