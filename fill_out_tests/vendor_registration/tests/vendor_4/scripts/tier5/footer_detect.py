"""
footer_detect.py (tier5)

Identifies the footer zone and classifies footer phrases by group.

Group 0 (footer zone) is computed from document data:
  - Lowermost wide horizontal line (w_norm > 0.5) as structural separator
  - Fallback: bottom 15% of page (y_norm >= 0.85)
  - Confirmation: tiny font present in zone

Groups 1-6 matched using universal_footer_detection.json keywords + regex.

Inputs:
  - universal_footer_detection.json  (project-level rules)
  - 2_process/tier4/phrases/phrases.json
  - 2_process/tier4/visible_lines/visible_lines.json

Output:
  - 2_process/tier5/footer.json
"""

import json
import re
from pathlib import Path

BASE        = Path(__file__).parent.parent.parent
TIER4_DIR   = BASE / "2_process" / "tier4"
TIER5_DIR   = BASE / "2_process" / "tier5"
RULES_PATH  = BASE.parent.parent / "universal_footer_detection.json"

FALLBACK_FOOTER_Y    = 0.85   # bottom 15%
MIN_HLINE_WIDTH_NORM = 0.5    # wide lines only (ignore checkbox lines)


# ── helpers ──────────────────────────────────────────────────────────────────

def match_keywords(text, keywords):
    """Return list of matched keywords (case-insensitive)."""
    t = text.lower()
    if isinstance(keywords, list):
        return [k for k in keywords if k.lower() in t]
    if isinstance(keywords, dict):
        hits = {}
        for cat, kws in keywords.items():
            matched = [k for k in kws if k.lower() in t]
            if matched:
                hits[cat] = matched
        return hits
    return []


def match_regex(text, patterns):
    """Return dict of pattern_name -> first match string."""
    hits = {}
    for name, pattern in patterns.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            hits[name] = m.group(0)
    return hits


def classify_phrase(text, font_group, rules):
    """Try each group 1-6. Return list of (group_id, evidence) matches."""
    matches = []
    for group_id in ["group_1_issuer_info", "group_2_legal_footnote",
                     "group_3_page_number", "group_4_date",
                     "group_5_annotations", "group_6_copyright_branding"]:
        g = rules.get(group_id, {})
        evidence = {}

        kw = g.get("keywords")
        if kw:
            hit = match_keywords(text, kw)
            if hit:
                evidence["keywords"] = hit

        rx = g.get("regex")
        if rx:
            hit = match_regex(text, rx)
            if hit:
                evidence["regex"] = hit

        if evidence:
            matches.append({"group": group_id, "evidence": evidence})

    return matches


# ── main ─────────────────────────────────────────────────────────────────────

def run(page="page_1"):
    with open(RULES_PATH) as f:
        rules = json.load(f)

    with open(TIER4_DIR / "phrases" / "phrases.json") as f:
        phrases_data = json.load(f)

    with open(TIER4_DIR / "visible_lines" / "visible_lines.json") as f:
        lines_data = json.load(f)

    W = phrases_data["image_size"]["w"]
    H = phrases_data["image_size"]["h"]
    phrases = phrases_data["phrases"]

    # ── Group 0: determine footer zone start y ────────────────────────────
    wide_hlines = [
        l for l in lines_data["lines"]
        if l["type"] == "horizontal" and l["w_norm"] >= MIN_HLINE_WIDTH_NORM
    ]

    if wide_hlines:
        last_hline_y = max(l["y_norm"] for l in wide_hlines)
    else:
        last_hline_y = None

    # Use the lowermost wide h-line if it falls within bottom 20% of page
    # (a structural separator). Otherwise fall back to 15% threshold.
    if last_hline_y and last_hline_y >= 0.80:
        footer_y_start = last_hline_y
        footer_y_method = "lowermost_wide_hline"
    else:
        footer_y_start = FALLBACK_FOOTER_Y
        footer_y_method = "fallback_bottom_15pct"

    # Tiny font confirmation
    tiny_in_zone = any(
        p["font_group"] in ("tiny", "other") and p["top"] >= footer_y_start
        for p in phrases
    )

    # ── Classify phrases in footer zone ───────────────────────────────────
    footer_phrases = []
    unmatched      = []

    for p in phrases:
        if p["top"] < footer_y_start:
            continue
        matches = classify_phrase(p["text"], p["font_group"], rules)
        entry = {
            "text":       p["text"],
            "top":        p["top"],
            "left":       p["left"],
            "width":      p["width"],
            "height":     p["height"],
            "font_group": p["font_group"],
        }
        if matches:
            entry["groups"] = matches
            footer_phrases.append(entry)
        else:
            unmatched.append(entry)

    # ── Safe footer bounding box ──────────────────────────────────────────
    all_in_zone = footer_phrases + unmatched
    if all_in_zone:
        safe_top    = min(p["top"]  for p in all_in_zone)
        safe_bottom = max(p["top"] + p["height"] for p in all_in_zone)
        safe_left   = min(p["left"] for p in all_in_zone)
        safe_right  = max(p["left"] + p["width"] for p in all_in_zone)
    else:
        safe_top    = footer_y_start
        safe_bottom = 1.0
        safe_left   = 0.0
        safe_right  = 1.0

    output = {
        "page":        page,
        "image_size":  {"w": W, "h": H},
        "group_0_footer_zone": {
            "y_start":          footer_y_start,
            "method":           footer_y_method,
            "last_wide_hline_y": last_hline_y,
            "tiny_font_present": tiny_in_zone,
        },
        "safe_footer_box": {
            "top":    safe_top,
            "left":   safe_left,
            "bottom": safe_bottom,
            "right":  safe_right,
        },
        "matched_count":   len(footer_phrases),
        "unmatched_count": len(unmatched),
        "footer_phrases":  footer_phrases,
        "unmatched":       unmatched,
    }

    TIER5_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TIER5_DIR / "footer.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Footer zone start y:   {footer_y_start:.4f}  ({footer_y_method})")
    print(f"  Tiny font in zone:     {tiny_in_zone}")
    print(f"  Phrases matched:       {len(footer_phrases)}")
    print(f"  Phrases unmatched:     {len(unmatched)}")
    print(f"  Safe footer box:       top={safe_top:.4f}  bottom={safe_bottom:.4f}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
