"""
checkbox_resolver.py (tier7)

Resolves checkbox sections — determines which checkbox to check based on client docs.

For each checkbox section:
  1. Match section header → canonical key via field_synonyms
  2. Get value from client docs
  3. Fuzzy-match value against option labels
  4. If matched → mark checkbox
  5. If not matched → flag for user input (Telegram later)

Output: 2_process/tier7/checkbox_resolved.json
"""

import json
import re
import sys
from pathlib import Path

BASE       = Path(__file__).parent.parent.parent
TIER5_DIR  = BASE / "2_process" / "tier5"
TIER7_DIR  = BASE / "2_process" / "tier7"
TIER7_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Path(__file__).parents[5]
sys.path.insert(0, str(PROJECT_ROOT))

from processors.resolver.doc_loader import load_client_docs
from processors.resolver.field_matcher import build_index, normalize, _match


CLIENT_DOCS_DIR = BASE / "1_input" / "client_docs"


def fuzzy_match(value, options):
    """
    Try to match a value string against a list of option label strings.
    Returns matched option label or None.
    Tries: exact → value-in-option → option-in-value → word overlap.
    """
    v = value.lower().strip()

    for opt in options:
        o = opt.lower().strip()
        if v == o:
            return opt

    for opt in options:
        o = opt.lower().strip()
        if v in o or o in v:
            return opt

    # Word overlap — any significant word in value matches option
    v_words = set(w for w in re.split(r"\W+", v) if len(w) > 3)
    for opt in options:
        o_words = set(w for w in re.split(r"\W+", opt.lower()) if len(w) > 3)
        if v_words & o_words:
            return opt

    return None


def run():
    # Load client doc values
    values    = load_client_docs(CLIENT_DOCS_DIR)
    syn_index = build_index()

    # Load checkbox data
    with open(TIER5_DIR / "checkbox" / "checkbox_sections.json") as f:
        sections_data = json.load(f)

    with open(TIER5_DIR / "checkbox" / "checkbox_phrases.json") as f:
        phrases_data = json.load(f)

    # Index items by band_top for quick lookup
    # Each band_top → list of {option_label, checkbox_coords}
    band_items = {}
    for item in phrases_data["items"]:
        bt = item["checkbox"]["y_norm"]
        # Find which band this belongs to
        for band in phrases_data["bands"]:
            if band["band_top"] <= bt <= band["band_bottom"]:
                key = band["band_top"]
                if key not in band_items:
                    band_items[key] = []
                band_items[key].append(item)
                break

    results = []

    for section in sections_data["sections"]:
        header_text = section["section_header"]
        band_top    = section["band"]["band_top"]
        items       = band_items.get(band_top, [])
        options     = [item["phrase"]["text"] for item in items]

        # Match section header → canonical key
        norm        = normalize(header_text)
        canonical   = _match(norm, syn_index)

        status           = None
        checked_opt      = None
        checked_cb       = None
        other_write_zone = None
        client_value     = values.get(canonical) if canonical else None

        if canonical and client_value:
            matched_label = fuzzy_match(client_value, options)

            if matched_label:
                for item in items:
                    if item["phrase"]["text"] == matched_label:
                        checked_cb  = item["checkbox"]
                        checked_opt = matched_label
                        break
                status = "matched"
            else:
                # No direct match — look for "other" option in this band
                other_item = next((i for i in items if i.get("is_other")), None)
                if other_item:
                    checked_cb       = other_item["checkbox"]
                    checked_opt      = other_item["phrase"]["text"]
                    other_write_zone = other_item.get("other_write_zone")
                    status           = "other"
                else:
                    status = "needs_input"
        else:
            status = "needs_input"

        results.append({
            "section_header":    header_text,
            "canonical_key":     canonical,
            "client_value":      client_value,
            "options":           options,
            "status":            status,
            "checked_option":    checked_opt,
            "checked_checkbox":  checked_cb,
            "other_write_zone":  other_write_zone,
            "needs_input_prompt": {
                "question": f"Please select the correct option for: {header_text}",
                "options":  options,
            } if status == "needs_input" else None,
        })

    output = {
        "page":          "page_1",
        "section_count": len(results),
        "matched":       sum(1 for r in results if r["status"] == "matched"),
        "needs_input":   sum(1 for r in results if r["status"] == "needs_input"),
        "sections":      results,
    }

    out_path = TIER7_DIR / "checkbox_resolved.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Sections: {len(results)}")
    print(f"  Matched:     {output['matched']}")
    print(f"  Other:       {sum(1 for r in results if r['status'] == 'other')}")
    print(f"  Needs input: {output['needs_input']}")
    for r in results:
        if r["status"] == "matched":
            print(f"  ✓ [{r['section_header'][:40]}] → '{r['checked_option']}'")
        elif r["status"] == "other":
            print(f"  ~ [{r['section_header'][:40]}] → 'Other' + write: '{r['client_value']}'")
        else:
            print(f"  ? [{r['section_header'][:40]}] → needs input | options: {r['options']}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run()
    print("Done.")
