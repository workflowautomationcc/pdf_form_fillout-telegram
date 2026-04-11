"""
fill_resolver.py (tier7)

Matches each fillable field phrase against client docs to produce a fill value.

Logic per field:
  1. Normalize phrase text (strip leading number/punct, lowercase)
  2. Match against field_synonyms.json synonyms → canonical key
  3. If no match, look back at last 3 matched fields for domain context,
     try a relaxed match within that domain
  4. Resolve value: hardcoded 'value' in synonyms, or source path in client docs
  5. Format lists/complex values as human-readable strings

Output: 2_process/tier7/resolved_fields.json
"""

import json
import re
from pathlib import Path

BASE       = Path(__file__).parent.parent.parent
CLIENT_DIR = BASE / "1_input" / "client_docs"
TIER6_DIR  = BASE / "2_process" / "tier6"
TIER7_DIR  = BASE / "2_process" / "tier7"
TIER7_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Load client documents into a flat source-path → value lookup
# source path format: "<doc_name>.<key>.<subkey>..."
# ---------------------------------------------------------------------------

def _flatten(obj, prefix=""):
    """Recursively flatten nested dict into dot-path keys."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        out[prefix] = obj  # keep lists as-is for formatting
    else:
        out[prefix] = obj
    return out


def load_client_docs():
    docs = {}
    for path in CLIENT_DIR.glob("*.json"):
        if path.name == "field_synonyms.json":
            continue
        doc_name = path.stem  # e.g. "certificate_of_formation"
        with open(path) as f:
            data = json.load(f)
        flat = _flatten(data)
        for k, v in flat.items():
            docs[f"{doc_name}.{k}"] = v
    return docs


def format_value(v):
    """Turn any value into a fill string."""
    if v is None:
        return None
    if isinstance(v, list):
        if not v:
            return "N/A"
        parts = []
        for item in v:
            if isinstance(item, dict):
                name = item.get("name", "")
                role = item.get("role", "")
                pct  = item.get("ownership_pct")
                if pct is not None:
                    parts.append(f"{name} ({role}, {pct}%)")
                elif role:
                    parts.append(f"{name} ({role})")
                else:
                    parts.append(name)
            else:
                parts.append(str(item))
        return ", ".join(parts)
    return str(v)


# ---------------------------------------------------------------------------
# Synonym matching
# ---------------------------------------------------------------------------

def normalize(text):
    """Strip leading number+punct, lowercase, collapse whitespace."""
    text = re.sub(r"^[\d\s.,:;)(-]+", "", text)  # strip "3. " or "1)" etc.
    text = text.lower().strip().rstrip(":").strip()
    return text


def build_synonym_index(synonyms_path):
    """
    Returns:
      index: dict { synonym_text → canonical_key }
      meta:  dict { canonical_key → {source, value} }
    """
    with open(synonyms_path) as f:
        raw = json.load(f)

    index = {}
    meta  = {}
    for key, entry in raw.items():
        if key.startswith("_"):
            continue
        meta[key] = {
            "source": entry.get("source"),
            "value":  entry.get("value"),
        }
        for syn in entry.get("synonyms", []):
            index[syn.lower().strip()] = key
    return index, meta


NOTE_PATTERNS = re.compile(
    r"\b(attach|attachment|list|if necessary|if applicable|see reverse|note:|refer to|as applicable)\b",
    re.IGNORECASE
)

def is_instruction(text):
    """Returns True if the phrase is a form note/instruction, not a field label."""
    return bool(NOTE_PATTERNS.search(text))


def match_phrase(text, index):
    """
    Try to match normalized phrase text to a canonical key.
    Returns canonical key or None.
    Ambiguous phrases (matching multiple distinct keys) return None.
    """
    norm = normalize(text)

    # Exact match
    if norm in index:
        return index[norm]

    # Partial: collect all synonyms contained in the phrase, track position
    # key → (earliest position, longest synonym length)
    matches = {}
    for syn, key in index.items():
        pos = norm.find(syn)
        if pos == -1:
            continue
        if key not in matches or pos < matches[key][0] or (pos == matches[key][0] and len(syn) > matches[key][1]):
            matches[key] = (pos, len(syn))

    if not matches:
        return None

    if len(matches) == 1:
        return next(iter(matches))

    # Multiple keys matched — pick the one whose synonym starts earliest in the phrase
    best_key = min(matches, key=lambda k: (matches[k][0], -matches[k][1]))
    best_pos = matches[best_key][0]

    # Only accept if best is clearly earlier than the rest (gap > 5 chars)
    others = [v[0] for k, v in matches.items() if k != best_key]
    if all(o - best_pos > 5 for o in others):
        return best_key

    # Too close — ambiguous
    return None


def resolve_value(canonical_key, meta, client_docs):
    """
    Returns fill string for a canonical key.
    Priority: source path in client docs → hardcoded value → None
    """
    entry  = meta[canonical_key]
    source = entry["source"]
    hvalue = entry["value"]

    if source:
        v = client_docs.get(source)
        if v is not None:
            formatted = format_value(v)
            if formatted:
                return formatted

    if hvalue is not None:
        return str(hvalue)

    return None


# ---------------------------------------------------------------------------
# Context / domain fallback
# ---------------------------------------------------------------------------

DOMAIN_GROUPS = {
    "company":  ["company_name", "type_of_business", "nature_of_business",
                  "year_established", "employees", "parent_company",
                  "owners_principals", "international_offices"],
    "address":  ["street_address", "po_box", "city", "state", "country", "postal_code"],
    "contact":  ["tel", "fax", "email", "website", "contact_name", "job_title"],
    "license":  ["licence_number", "licence_state", "licence_expiry",
                  "vat_number", "ein"],
    "banking":  ["bank_name", "bank_id", "branch_name", "branch_code",
                  "branch_address", "account_number", "account_name", "account_currency"],
}

def key_to_domain(key):
    for domain, keys in DOMAIN_GROUPS.items():
        if key in keys:
            return domain
    return None

def context_match(text, index, recent_keys):
    """
    Look at the last few matched keys, infer active domain,
    then try matching only synonyms within that domain.
    """
    if not recent_keys:
        return None

    # Find most recent domain
    active_domain = None
    for k in reversed(recent_keys):
        d = key_to_domain(k)
        if d:
            active_domain = d
            break

    if not active_domain:
        return None

    domain_keys = set(DOMAIN_GROUPS[active_domain])
    norm = normalize(text)

    best = None
    best_len = 0
    for syn, key in index.items():
        if key not in domain_keys:
            continue
        if syn in norm and len(syn) > best_len:
            best = key
            best_len = len(syn)

    return best


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(page="page_1"):
    synonyms_path = CLIENT_DIR / "field_synonyms.json"
    index, meta   = build_synonym_index(synonyms_path)
    client_docs   = load_client_docs()

    with open(TIER6_DIR / "fillable_fields.json") as f:
        data = json.load(f)

    # Sort top→bottom, left→right
    fields = sorted(data["fields"], key=lambda f: (round(f["top"], 3), f["left"]))

    resolved   = []
    unresolved = []
    recent_matched_keys = []  # last N canonical keys successfully matched

    for field in fields:
        text = field["text"]

        # Skip instruction/note phrases entirely
        if is_instruction(text):
            continue

        # Try direct match
        canonical = match_phrase(text, index)

        # If no match, try context fallback
        if canonical is None:
            canonical = context_match(text, index, recent_matched_keys[-3:])

        if canonical:
            value = resolve_value(canonical, meta, client_docs)
            recent_matched_keys.append(canonical)
            resolved.append({
                "text":          text,
                "canonical_key": canonical,
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
        "page":             page,
        "resolved_count":   len(resolved),
        "unresolved_count": len(unresolved),
        "resolved":         resolved,
        "unresolved":       unresolved,
    }

    out_path = TIER7_DIR / "resolved_fields.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Resolved:   {len(resolved)}")
    print(f"  Unresolved: {len(unresolved)}")
    if unresolved:
        print("  Unresolved fields:")
        for u in unresolved:
            print(f"    - {u['text']}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    run("page_1")
    print("Done.")
