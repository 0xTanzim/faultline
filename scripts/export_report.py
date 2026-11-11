#!/usr/bin/env python3
"""Export Faultline preflight reports to standard SARIF v2.1.0 or structured JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_report import FIELD_LABELS, blocks, RISK_HEADING


def parse_report_to_dict(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")

    # Title & slug
    title_m = re.search(r"^#\s+Faultline Preflight\s*[—–-]\s*(.+)$", text, re.MULTILINE)
    slug = title_m.group(1).strip() if title_m else path.stem

    # Metadata lines (- **Key:** Value)
    metadata = {}
    for m in re.finditer(r"^[-*]\s+\*\*([^:]+):\*\*\s*(.+)$", text[:1000], re.MULTILINE):
        metadata[m.group(1).strip().lower()] = m.group(2).strip()

    # Risks
    raw_risks = blocks(text)
    parsed_risks = []
    for rid, title, b in raw_risks:
        r_dict = {"id": rid, "title": title}
        for label in FIELD_LABELS:
            pattern = rf"^[-*]\s+\*\*{re.escape(label)}(?::\*\*|\*\*:\s*)\s*(.+)$"
            m = re.search(pattern, b, re.MULTILINE | re.IGNORECASE)
            if m:
                r_dict[label.lower().replace("/", "_").replace(" ", "_")] = m.group(1).strip()

        # Extract Given/When/Then acceptance scenario
        scenario = {}
        for stage in ("Given", "When", "Then"):
            s_m = re.search(rf"^\s*[-*]\s+\*\*{stage}(?::\*\*|\*\*)\s*(\S.+)$", b, re.MULTILINE | re.IGNORECASE)
            if s_m:
                scenario[stage.lower()] = s_m.group(1).strip()
        if scenario:
            r_dict["acceptance_scenario"] = scenario

        parsed_risks.append(r_dict)

    return {
        "slug": slug,
        "source_file": str(path),
        "metadata": metadata,
        "risks": parsed_risks,
    }


def to_sarif(data: dict) -> dict:
    level_map = {
        "CRITICAL": "error",
        "HIGH": "error",
        "MEDIUM": "warning",
        "LOW": "note",
    }

    rules = []
    results = []

    for r in data["risks"]:
        rid = r["id"]
        title = r["title"]
        sev = r.get("severity", "HIGH").upper()
        level = level_map.get(sev, "warning")
        impact = r.get("impact", "")
        mitigation = r.get("mitigation", "")
        evidence = r.get("evidence", "")

        help_md = f"### {rid}: {title}\n\n**Severity:** {sev}\n\n**Impact:** {impact}\n\n**Mitigation:** {mitigation}"
        if "acceptance_scenario" in r:
            sc = r["acceptance_scenario"]
            help_md += f"\n\n**Acceptance Test:**\n- **Given** {sc.get('given', '')}\n- **When** {sc.get('when', '')}\n- **Then** {sc.get('then', '')}"

        rules.append({
            "id": rid,
            "name": title.replace(" ", "_"),
            "shortDescription": {"text": title},
            "fullDescription": {"text": f"{title}. {impact}"},
            "defaultConfiguration": {"level": level},
            "help": {"text": help_md, "markdown": help_md},
        })

        # Parse file location from components_paths
        comp = r.get("components_paths", "")
        file_path = "UNKNOWN"
        line_num = 1
        if comp:
            file_match = re.search(r"([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)(?::L?(\d+))?", comp)
            if file_match:
                file_path = file_match.group(1)
                if file_match.group(2):
                    line_num = int(file_match.group(2))

        results.append({
            "ruleId": rid,
            "level": level,
            "message": {"text": f"[{sev}] {title}: {impact}"},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": file_path,
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {"startLine": line_num},
                    }
                }
            ],
        })

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Faultline",
                        "version": "0.5.0-beta.1",
                        "informationUri": "https://github.com/0xTanzim/faultline",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Faultline preflight report to SARIF or JSON.")
    parser.add_argument("report", type=Path, help="Path to Faultline markdown report")
    parser.add_argument("--format", choices=["json", "sarif"], default="sarif", help="Export format (default: sarif)")
    parser.add_argument("-o", "--output", type=Path, help="Output destination file path (prints to stdout if omitted)")
    args = parser.parse_args()

    if not args.report.is_file():
        print(f"ERROR: Report file not found: {args.report}", file=sys.stderr)
        return 1

    parsed = parse_report_to_dict(args.report)

    if args.format == "sarif":
        output_data = to_sarif(parsed)
    else:
        output_data = parsed

    json_text = json.dumps(output_data, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json_text + "\n", encoding="utf-8")
        print(f"Exported {args.format.upper()} report to: {args.output}")
    else:
        print(json_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
