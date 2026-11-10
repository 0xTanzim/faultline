#!/usr/bin/env python3
"""Validate Faultline report structure, not technical correctness."""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path
REQUIRED_SECTIONS = [
    "Executive summary", "Scope and success conditions", "Reconnaissance and system map",
    "Code-path and change-impact analysis", "Evidence, assumptions, and unknowns",
    "Coverage matrix", "Risk register", "Failure chains and pre-mortem",
    "Break attempts and test results", "Specialist review provenance",
    "Proposed requirements and scenarios", "Decisions required before specification", "Limitations"
]
RISK_HEADING = re.compile(r"^###\s+(FL-\d{3,})\s+—\s+.+$", re.MULTILINE)
FIELD_LABELS = ["Status", "Evidence level", "Priority", "Severity", "Likelihood", "Confidence",
 "Disposition", "Domain", "Components/paths", "Evidence", "Preconditions", "Trigger",
 "Failure sequence", "Expected behavior", "Observed behavior", "Impact", "Detection/recovery",
 "Mitigation", "Reproduction/test", "Acceptance test"]
ALLOWED = {
 "Status": {"CONFIRMED", "LIKELY", "POSSIBLE", "NOT_REPRODUCED"},
 "Evidence level": {"OBSERVED", "INFERRED", "HYPOTHESIS"},
 "Priority": {"CRITICAL", "HIGH", "MEDIUM", "LOW"},
 "Severity": {"CRITICAL", "HIGH", "MEDIUM", "LOW"},
 "Likelihood": {"EXPECTED", "LIKELY", "POSSIBLE", "UNLIKELY", "RARE"},
 "Confidence": {"HIGH", "MEDIUM", "LOW"},
 "Disposition": {"MITIGATE", "ACCEPT", "DEFER", "INVESTIGATE"},
}
def blocks(text: str):
    ms=list(RISK_HEADING.finditer(text))
    return [(m.group(1),text[m.end():ms[i+1].start() if i+1<len(ms) else len(text)]) for i,m in enumerate(ms)]
def validate(path: Path) -> int:
    if not path.is_file(): print(f"ERROR: report not found: {path}"); return 2
    try: text=path.read_text(encoding="utf-8")
    except (OSError,UnicodeDecodeError) as e: print(f"ERROR: cannot read UTF-8 report: {e}"); return 2
    errors=[]; warnings=[]
    for h in REQUIRED_SECTIONS:
        if not re.search(rf"^##\s+{re.escape(h)}\s*$",text,re.M): errors.append(f"Missing required section: ## {h}")
    rs=blocks(text); ids=[i for i,_ in rs]
    dups=sorted({x for x in ids if ids.count(x)>1})
    if dups: errors.append("Duplicate risk IDs: "+", ".join(dups))
    for rid,b in rs:
        vals={}
        for label in FIELD_LABELS:
            m=re.search(rf"^[-*]\s+\*\*{re.escape(label)}:\*\*\s*(.+)$",b,re.M)
            if not m: errors.append(f"{rid}: missing or empty field '{label}'")
            else: vals[label]=m.group(1).strip()
        for label, choices in ALLOWED.items():
            if label in vals and vals[label].upper() not in choices:
                errors.append(f"{rid}: invalid {label} value '{vals[label]}'")
        for label in ("Given","When","Then"):
            if not re.search(rf"^\s*[-*]\s+\*\*{label}\*\*\s*\S.+$",b,re.M):
                errors.append(f"{rid}: acceptance test must contain non-empty {label}")
    if not rs: warnings.append("No risks retained; ensure coverage rows explain what was assessed and why no material risks were retained.")
    statuses=set(re.findall(r"\|[^\n]*\b(covered|not-applicable|not-assessed)\b[^\n]*\|",text,re.I))
    if not statuses: warnings.append("No recognized coverage status found; inspect the coverage matrix manually.")
    for w in warnings: print("WARNING:",w)
    for e in errors: print("ERROR:",e)
    if errors: print(f"\nFAIL: {len(errors)} structural issue(s); {len(warnings)} warning(s)."); return 1
    print(f"PASS: report structure looks valid ({len(rs)} risk record(s), {len(warnings)} warning(s)).")
    print("NOTE: structural validation does not prove technical truth, completeness, or sufficient testing.")
    return 0
def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("report",type=Path); return validate(ap.parse_args().report)
if __name__=="__main__": raise SystemExit(main())
