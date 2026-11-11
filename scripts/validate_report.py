#!/usr/bin/env python3
"""Validate Faultline report structure, required sections, risk records, and scenarios."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

REQUIRED_SECTIONS = [
    "Executive summary",
    "Scope and success conditions",
    "Reconnaissance and system map",
    "Code-path and change-impact analysis",
    "Evidence, assumptions, and unknowns",
    "Coverage matrix",
    "Risk register",
    "Failure chains and pre-mortem",
    "Break attempts and test results",
    "Specialist review provenance",
    "Proposed requirements and scenarios",
    "Decisions required before specification",
    "Limitations",
]

RISK_HEADING = re.compile(r"^###\s+((?:FL|RISK)-\d{3,})\s*(?:—|--|-|:)\s*(.+)$", re.MULTILINE)

FIELD_LABELS = [
    "Status",
    "Evidence level",
    "Priority",
    "Severity",
    "Likelihood",
    "Confidence",
    "Disposition",
    "Domain",
    "Components/paths",
    "Evidence",
    "Preconditions",
    "Trigger",
    "Failure sequence",
    "Expected behavior",
    "Observed behavior",
    "Impact",
    "Detection/recovery",
    "Mitigation",
    "Reproduction/test",
    "Acceptance test",
]

ALLOWED = {
    "Status": {"CONFIRMED", "LIKELY", "POSSIBLE", "NOT_REPRODUCED"},
    "Evidence level": {"OBSERVED", "INFERRED", "HYPOTHESIS"},
    "Priority": {"CRITICAL", "HIGH", "MEDIUM", "LOW"},
    "Severity": {"CRITICAL", "HIGH", "MEDIUM", "LOW"},
    "Likelihood": {"EXPECTED", "LIKELY", "POSSIBLE", "UNLIKELY", "RARE"},
    "Confidence": {"HIGH", "MEDIUM", "LOW"},
    "Disposition": {"MITIGATE", "ACCEPT", "DEFER", "INVESTIGATE"},
}


def blocks(text: str) -> list[tuple[str, str, str]]:
    """Extract (risk_id, title, block_text) tuples."""
    ms = list(RISK_HEADING.finditer(text))
    result = []
    for i, m in enumerate(ms):
        rid = m.group(1)
        rtitle = m.group(2).strip()
        end_idx = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        block = text[m.end() : end_idx]
        result.append((rid, rtitle, block))
    return result


def validate(path: Path) -> int:
    if not path.is_file():
        print(f"ERROR: report not found: {path}", file=sys.stderr)
        return 2

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"ERROR: cannot read UTF-8 report: {e}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []

    # 1. Required Sections (Case-insensitive & whitespace tolerant)
    for h in REQUIRED_SECTIONS:
        pattern = rf"^##\s+{re.escape(h)}\s*$"
        if not re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
            errors.append(f"Missing required section: ## {h}")

    # 2. Risk Records
    rs = blocks(text)
    ids = [i for i, _, _ in rs]
    dups = sorted({x for x in ids if ids.count(x) > 1})
    if dups:
        errors.append("Duplicate risk IDs: " + ", ".join(dups))

    for rid, title, b in rs:
        vals = {}
        for label in FIELD_LABELS:
            # Matches `- **Label:** ...` or `- **Label**: ...`
            pattern = rf"^[-*]\s+\*\*{re.escape(label)}(?::\*\*|\*\*:\s*)\s*(.+)$"
            m = re.search(pattern, b, re.MULTILINE | re.IGNORECASE)
            if not m:
                errors.append(f"{rid}: missing or empty field '{label}'")
            else:
                vals[label] = m.group(1).strip()

        for label, choices in ALLOWED.items():
            if label in vals and vals[label].upper() not in choices:
                errors.append(
                    f"{rid}: invalid {label} value '{vals[label]}' (expected one of: {', '.join(sorted(choices))})"
                )

        for label in ("Given", "When", "Then"):
            pattern = rf"^\s*[-*]\s+\*\*{label}(?::\*\*|\*\*)\s*\S.+$"
            if not re.search(pattern, b, re.MULTILINE | re.IGNORECASE):
                errors.append(f"{rid}: acceptance test must contain non-empty {label}")

    if not rs:
        warnings.append(
            "No risks retained; ensure coverage rows explain what was assessed and why no material risks were retained."
        )

    statuses = set(re.findall(r"\|[^\n]*\b(covered|not-applicable|not-assessed)\b[^\n]*\|", text, re.IGNORECASE))
    if not statuses:
        warnings.append("No recognized coverage status found; inspect the coverage matrix manually.")

    for w in warnings:
        print("WARNING:", w)
    for e in errors:
        print("ERROR:", e)

    if errors:
        print(f"\nFAIL: {len(errors)} structural issue(s); {len(warnings)} warning(s).")
        return 1

    print(f"PASS: report structure looks valid ({len(rs)} risk record(s), {len(warnings)} warning(s)).")
    print("NOTE: structural validation does not prove technical truth, completeness, or sufficient testing.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", type=Path, help="Path to Faultline markdown report")
    args = ap.parse_args()
    return validate(args.report)


if __name__ == "__main__":
    raise SystemExit(main())
