from __future__ import annotations
import re
from typing import List, Dict, Any

# Canonical required docs for Company Incorporation (simplified POC list)
REQUIRED_INCORP_DOCS: List[str] = [
    "Articles of Association",
    "Memorandum of Association",
    "Board Resolution",
    "Shareholder Resolution",
    "Incorporation Application Form",
    "UBO Declaration Form",
    "Register of Members and Directors",
    "Change of Registered Address Notice",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def classify_document_type(text: str, filename: str | None = None) -> str:
    content = normalize(text)
    name = normalize(filename or "")

    mapping = {
        "articles of association": "Articles of Association",
        "memorandum of association": "Memorandum of Association",
        "board resolution": "Board Resolution",
        "shareholder resolution": "Shareholder Resolution",
        "incorporation application": "Incorporation Application Form",
        "ubo": "UBO Declaration Form",
        "register of members": "Register of Members and Directors",
        "change of registered address": "Change of Registered Address Notice",
    }

    for key, label in mapping.items():
        if key in content or key in name:
            return label

    return "Unknown"


def detect_red_flags_rule_based(text: str, doc_type: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    lower = text.lower()

    # Jurisdiction check: must reference ADGM
    if "adgm" not in lower and "abu dhabi global market" not in lower:
        findings.append({
            "section": None,
            "issue": "Jurisdiction reference missing or not specific to ADGM",
            "severity": "Medium",
            "suggestion": "Specify jurisdiction as ADGM Courts per ADGM Companies Regulations.",
            "snippet": text[:200],
        })

    # Signature block presence (simple heuristic)
    if not re.search(r"signature|signed by|authorised signatory|authorized signatory", lower):
        findings.append({
            "section": None,
            "issue": "Signature section may be missing",
            "severity": "Medium",
            "suggestion": "Add a signatory section with name, title, and date.",
            "snippet": text[:200],
        })

    # Placeholder detection
    if re.search(r"\b(TBD|TBA|\[\s*insert[^\]]*\]|<\s*insert[^>]*>)\b", text, flags=re.IGNORECASE):
        findings.append({
            "section": None,
            "issue": "Template placeholders detected",
            "severity": "Medium",
            "suggestion": "Replace placeholders with finalized values.",
            "snippet": text[:200],
        })

    # Document-specific heuristic checks
    if doc_type == "Articles of Association":
        if "objects" not in lower and "purpose" not in lower:
            findings.append({
                "section": None,
                "issue": "Objects/purpose clause not found",
                "severity": "Medium",
                "suggestion": "Include company objects/purpose consistent with ADGM templates.",
                "snippet": text[:200],
            })

    return findings


def detect_process_by_content(document_analysis: List[Dict[str, Any]]) -> str:
    # POC: if any doc matches incorporation set, assume Company Incorporation
    for d in document_analysis:
        if d.get("document_type") in REQUIRED_INCORP_DOCS:
            return "Company Incorporation"
    return "Unknown"


