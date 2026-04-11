"""
resolver.py

Main entry point for the fill resolver.

Given:
  - fillable_fields.json  (form fields with coordinates)
  - client_docs/          (dropped client documents)

Produces:
  - resolved_fields.json  (each field with matched value + fill zone)

Usage:
    from processors.resolver.resolver import resolve
    result = resolve(fillable_fields_path, client_docs_dir, output_path)
"""

import json
from pathlib import Path

from processors.resolver.doc_loader import load_client_docs
from processors.resolver.field_matcher import match_field, build_index


def resolve(fillable_fields_path, client_docs_dir, output_path):
    fillable_fields_path = Path(fillable_fields_path)
    client_docs_dir      = Path(client_docs_dir)
    output_path          = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: load all client docs → flat canonical key→value lookup
    print("Loading client documents...")
    values = load_client_docs(client_docs_dir)
    print(f"  Canonical values loaded: {len(values)}")

    # Step 2: load form fields sorted top→bottom, left→right
    with open(fillable_fields_path) as f:
        data = json.load(f)

    fields = sorted(data["fields"], key=lambda f: (round(f["top"], 3), f["left"]))

    # Step 3: match each field label → canonical key → value
    index       = build_index()
    recent_keys = []
    resolved    = []
    unresolved  = []
    skipped     = []

    for field in fields:
        text = field["text"]

        canonical, match_type = match_field(text, index, recent_keys[-5:])

        if match_type == "instruction":
            skipped.append(text)
            continue

        if canonical:
            value = values.get(canonical)
            recent_keys.append(canonical)
            resolved.append({
                "text":          text,
                "canonical_key": canonical,
                "match_type":    match_type,
                "value":         value,
                "fill_zone":     field["fill_zone"],
                "left":          field["left"],
                "top":           field["top"],
                "width":         field["width"],
                "height":        field["height"],
                "right_space":   field["right_space"],
                "bottom_space":  field["bottom_space"],
            })
        else:
            unresolved.append({
                "text":      text,
                "fill_zone": field["fill_zone"],
                "left":      field["left"],
                "top":       field["top"],
            })

    output = {
        "resolved_count":   len(resolved),
        "unresolved_count": len(unresolved),
        "skipped_count":    len(skipped),
        "resolved":         resolved,
        "unresolved":       unresolved,
        "skipped":          skipped,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Resolved:   {len(resolved)}")
    print(f"  Unresolved: {len(unresolved)}")
    print(f"  Skipped:    {len(skipped)}")
    if unresolved:
        print("  Unresolved fields:")
        for u in unresolved:
            print(f"    - {u['text']}")

    return output


if __name__ == "__main__":
    BASE = Path(__file__).parents[2]
    resolve(
        fillable_fields_path = BASE / "fill_out_tests/vendor_registration/tests/vendor_4/2_process/tier6/fillable_fields.json",
        client_docs_dir      = BASE / "fill_out_tests/vendor_registration/tests/vendor_4/1_input/client_docs",
        output_path          = BASE / "fill_out_tests/vendor_registration/tests/vendor_4/2_process/tier7/resolved_fields.json",
    )
    print("Done.")
