"""
doc_loader.py

Loads client documents, matches each to its schema, extracts canonical key→value pairs.

Usage:
    from processors.resolver.doc_loader import load_client_docs
    values = load_client_docs("/path/to/client_docs/")
    # returns: {"company_name": "Brightline Trading...", "ein": "47-3829104", ...}
"""

import json
from pathlib import Path

SCHEMAS_DIR = Path(__file__).parents[2] / "data" / "doc_schemas"


def _get_nested(obj, dot_path):
    """Traverse nested dict using dot-path string. Returns None if not found."""
    keys = dot_path.split(".")
    for k in keys:
        if isinstance(obj, dict):
            obj = obj.get(k)
        else:
            return None
        if obj is None:
            return None
    return obj


def _format_value(v):
    """Convert any value to a clean fill string."""
    if v is None:
        return None
    if isinstance(v, list):
        if not v:
            return "N/A"
        parts = []
        for item in v:
            if isinstance(item, dict):
                name = item.get("name", "")
                role = item.get("role", item.get("title", ""))
                pct  = item.get("ownership_pct")
                if pct is not None:
                    parts.append(f"{name} ({role}, {pct}%)")
                elif role:
                    parts.append(f"{name} ({role})")
                else:
                    parts.append(str(name))
            else:
                parts.append(str(item))
        return ", ".join(parts) if parts else "N/A"
    if isinstance(v, bool):
        return "Yes" if v else "No"
    return str(v)


def _load_schema_index():
    """Build index: document_type → schema provides dict."""
    index = {}
    for f in SCHEMAS_DIR.rglob("*.json"):
        if f.name in ("canonical_keys.json", "field_synonyms.json"):
            continue
        with open(f) as fp:
            schema = json.load(fp)
        doc_type = schema.get("document_type")
        if doc_type:
            index[doc_type.lower()] = schema.get("provides", {})
    return index


def load_client_docs(client_docs_dir):
    """
    Load all JSON files from client_docs_dir.
    Match each to a schema by document_type.
    Extract and return merged canonical key → value dict.

    Later docs override earlier ones for the same key.
    Priority: more specific docs (banking, tax) over general ones.
    """
    client_docs_dir = Path(client_docs_dir)
    schema_index    = _load_schema_index()

    # Priority order — higher = more trusted for overlapping keys
    GROUP_PRIORITY = {
        "01_business_identity":   5,
        "04_banking_payments":    5,
        "05_tax_documents":       5,
        "02_licenses_permits":    4,
        "03_insurance":           3,
        "09_address_proof":       3,
        "10_vehicle_equipment":   3,
        "06_contracts_agreements": 2,
        "07_employee_worker":     2,
        "08_certifications_compliance": 2,
        "11_invoices_financial":  1,
        "12_personal":            2,
    }

    # Collect all (key, value, priority) from all docs
    collected = {}  # key → (value, priority)

    for doc_file in sorted(client_docs_dir.glob("*.json")):
        with open(doc_file) as f:
            try:
                doc_data = json.load(f)
            except Exception:
                continue

        doc_type = doc_data.get("document_type", "").lower()
        if not doc_type:
            continue

        provides = schema_index.get(doc_type)
        if not provides:
            print(f"  [warn] No schema found for: {doc_data.get('document_type')}")
            continue

        # Find group priority
        group = doc_data.get("group", "")
        priority = GROUP_PRIORITY.get(group, 1)

        for canonical_key, dot_path in provides.items():
            raw = _get_nested(doc_data, dot_path)
            if raw is None:
                continue
            value = _format_value(raw)
            if not value or value == "None":
                continue

            # Only override if new priority >= existing
            existing = collected.get(canonical_key)
            if existing is None or priority >= existing[1]:
                collected[canonical_key] = (value, priority)

    # Return flat key→value
    return {k: v for k, (v, _) in collected.items()}
