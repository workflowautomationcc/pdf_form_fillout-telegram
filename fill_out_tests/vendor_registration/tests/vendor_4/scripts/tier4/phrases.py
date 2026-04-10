"""
Build phrases.json (tier4).

Merges words from ocr_fine_tuned.json into phrases using gap_groups.json.
Words connected by friendly gaps are merged into one container.
A 'separate' gap (or no connection) breaks the phrase.

Matching: each gap's left_x_end matches a word's (left+width),
          each gap's right_x_start matches a word's left.
          Rounded to 4 decimals; ties broken by closest y.

Output format matches ocr_fine_tuned.json but per phrase:
  text, left, top, width, height, height_px, font_group (all normalized)

Output: 2_process/tier4/phrases/phrases.json
"""

import json
from pathlib import Path

BASE      = Path(__file__).parent.parent.parent
TIER3_DIR = BASE / "2_process" / "tier3"
TIER4_DIR = BASE / "2_process" / "tier4"


def run(page="page_1"):
    with open(TIER3_DIR / "words" / "ocr_fine_tuned.json") as f:
        ocr = json.load(f)

    with open(TIER3_DIR / "word_gaps" / "gap_groups.json") as f:
        groups = json.load(f)

    words = ocr["words"]
    n     = len(words)

    # Index words by right edge and left edge (rounded to 4 dp)
    by_right = {}   # right_edge -> [word_idx, ...]
    by_left  = {}   # left_edge  -> [word_idx, ...]
    for i, w in enumerate(words):
        r = round(w["left"] + w["width"], 4)
        l = round(w["left"], 4)
        by_right.setdefault(r, []).append(i)
        by_left.setdefault(l, []).append(i)

    # Union-Find
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[b] = a

    # For each friendly gap, find both words and union them
    for group_name, gaps in groups["groups"].items():
        if group_name == "separate":
            continue
        for g in gaps:
            r_key = round(g["left_x_end"],  4)
            l_key = round(g["right_x_start"], 4)
            g_top = g["top"]

            candidates_left  = by_right.get(r_key, [])
            candidates_right = by_left.get(l_key, [])

            if not candidates_left or not candidates_right:
                continue

            # Pick closest by y
            li = min(candidates_left,  key=lambda i: abs(words[i]["top"] - g_top))
            ri = min(candidates_right, key=lambda i: abs(words[i]["top"] - g_top))

            union(li, ri)

    # Group words by root
    from collections import defaultdict
    groups_map = defaultdict(list)
    for i in range(n):
        groups_map[find(i)].append(i)

    # Build phrase containers
    phrases = []
    for root, indices in groups_map.items():
        group_words = [words[i] for i in indices]
        group_words.sort(key=lambda w: w["left"])

        text      = " ".join(w["text"] for w in group_words)
        left      = min(w["left"] for w in group_words)
        top       = min(w["top"]  for w in group_words)
        right     = max(w["left"] + w["width"]  for w in group_words)
        bottom    = max(w["top"]  + w["height"] for w in group_words)
        height_px = max(w["height_px"] for w in group_words)
        font_group = group_words[0]["font_group"]

        phrases.append({
            "text":       text,
            "left":       left,
            "top":        top,
            "width":      right - left,
            "height":     bottom - top,
            "height_px":  height_px,
            "font_group": font_group,
        })

    # Sort phrases in reading order
    phrases.sort(key=lambda p: (round(p["top"], 3), p["left"]))

    output = {
        "page":         page,
        "image_size":   ocr["image_size"],
        "phrase_count": len(phrases),
        "phrases":      phrases,
    }

    out_dir = TIER4_DIR / "phrases"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phrases.json"

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Words in:    {ocr['word_count']}")
    print(f"  Phrases out: {len(phrases)}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
