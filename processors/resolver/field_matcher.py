"""
field_matcher.py

Matches form field labels (from OCR) to canonical keys using field_synonyms.json.
Context-aware: uses previous matched keys to resolve ambiguous labels.
"""

import json
import re
from pathlib import Path

SCHEMAS_DIR   = Path(__file__).parents[2] / "data" / "doc_schemas"
SYNONYMS_PATH = SCHEMAS_DIR / "field_synonyms.json"

# Phrases that are form instructions, not fillable labels
NOTE_PATTERN = re.compile(
    r"\b(attach|attachment|if necessary|if applicable|see reverse|note:|refer to|as applicable|specify below)\b",
    re.IGNORECASE
)

# Domain groupings for context fallback
DOMAIN_GROUPS = {
    "company":  ["company_name", "entity_type", "nature_of_business", "year_established",
                  "date_of_incorporation", "state_of_formation", "owners_principals",
                  "registered_agent_name", "file_number", "dba_name"],
    "address":  ["street_address", "city", "state", "zip", "country"],
    "contact":  ["tel", "fax", "email", "website", "signatory_name", "signatory_title"],
    "license":  ["licence_number", "licence_state", "licence_expiry", "licence_class",
                  "registration_number", "registration_state"],
    "tax":      ["ein", "ssn", "tax_classification", "tax_year"],
    "banking":  ["bank_name", "bank_id", "branch_name", "branch_code", "branch_address",
                  "account_number", "account_name", "account_currency"],
    "insurance": ["insurer_name", "policy_number", "policy_expiry", "coverage_type", "coverage_limit"],
    "vehicle":  ["vehicle_vin", "vehicle_make", "vehicle_model", "vehicle_year",
                  "vehicle_plate", "dot_number", "mc_number"],
}


def _load_synonym_index():
    """Returns dict: normalized_synonym → canonical_key"""
    with open(SYNONYMS_PATH) as f:
        raw = json.load(f)
    index = {}
    for key, synonyms in raw.items():
        if key.startswith("_"):
            continue
        for syn in synonyms:
            index[syn.lower().strip()] = key
    return index


def normalize(text):
    """Strip leading number/punctuation, lowercase, collapse whitespace."""
    text = re.sub(r"^[\d\s.,:;)(\-]+", "", text)
    return text.lower().strip().rstrip(":").strip()


def is_instruction(text):
    return bool(NOTE_PATTERN.search(text))


def _key_domain(key):
    for domain, keys in DOMAIN_GROUPS.items():
        if key in keys:
            return domain
    return None


def _match(norm, index, restrict_to=None):
    """
    Match normalized text against synonym index.
    restrict_to: set of canonical keys to limit search (for context matching).
    Returns canonical key or None.
    """
    # Exact
    if norm in index:
        key = index[norm]
        if restrict_to and key not in restrict_to:
            return None
        return key

    # Partial — collect all matches with position + length
    matches = {}
    for syn, key in index.items():
        if restrict_to and key not in restrict_to:
            continue
        pos = norm.find(syn)
        if pos == -1:
            continue
        # Require word boundaries: char before must not be alpha, char after must not be alpha (space ok)
        before_ok = (pos == 0 or not norm[pos - 1].isalpha())
        after_ch  = norm[pos + len(syn)] if pos + len(syn) < len(norm) else " "
        after_ok  = not after_ch.isalpha() or after_ch == " "
        if not (before_ok and after_ok):
            continue
        if key not in matches or pos < matches[key][0] or (pos == matches[key][0] and len(syn) > matches[key][1]):
            matches[key] = (pos, len(syn))

    if not matches:
        return None
    if len(matches) == 1:
        return next(iter(matches))

    # Multiple — pick earliest, only if clearly ahead of others (gap > 5 chars)
    best_key = min(matches, key=lambda k: (matches[k][0], -matches[k][1]))
    best_pos = matches[best_key][0]
    others   = [v[0] for k, v in matches.items() if k != best_key]
    if all(o - best_pos > 5 for o in others):
        return best_key

    return None  # ambiguous


def match_field(text, index, recent_keys):
    """
    Match a form label to a canonical key.
    Returns (canonical_key, match_type) or (None, None).
    match_type: 'direct' | 'context'
    """
    if is_instruction(text):
        return None, "instruction"

    norm = normalize(text)

    # Direct match
    key = _match(norm, index)
    if key:
        return key, "direct"

    # Context fallback — infer active domain from recent matched keys
    if recent_keys:
        active_domain = None
        for k in reversed(recent_keys):
            d = _key_domain(k)
            if d:
                active_domain = d
                break

        if active_domain:
            domain_keys = set(DOMAIN_GROUPS[active_domain])
            key = _match(norm, index, restrict_to=domain_keys)
            if key:
                return key, "context"

    return None, None


def build_index():
    return _load_synonym_index()
