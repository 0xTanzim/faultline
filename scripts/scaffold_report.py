#!/usr/bin/env python3
"""Scaffold a structurally valid Faultline preflight or break-sweep report skeleton."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def scaffold_report(
    slug: str,
    title: str | None = None,
    mode: str = "brownfield-preflight",
    output_path: Path | None = None,
) -> Path:
    clean_slug = slug.strip().lower().replace(" ", "-")
    clean_title = title or clean_slug.replace("-", " ").title()
    today = date.today().isoformat()

    content = f"""# Faultline Preflight — {clean_slug}

- **Date:** {today}
- **Repository revision:** HEAD
- **Working-tree state:** clean
- **Mode:** {mode}
- **Analyst:** Faultline Scaffolded Report

## Executive summary
- Overall risk posture: [LOW / MEDIUM / HIGH / CRITICAL]
- Confirmed defects: [Count or None]
- Critical/High risks: [Count or None]
- Key decisions before specification: [Brief summary]
- Most important unknown: [Key technical unknown]

## Scope and success conditions
### Intended outcome
{clean_title}

### Affected actors
[End users, operators, administrators, external services]

### In scope / out of scope
In scope: [Subsystem / Components]. Out of scope: [Unrelated modules].

### Success conditions and invariants
[Observable invariants and business rules that must be preserved]

## Reconnaissance and system map
### Repository structure and entry points
[Entry point functions, HTTP handlers, CLI commands, workers]

### Runtime/process model
[Process topology, threading, concurrency, async tasks]

### Components and dependencies
[Internal modules, third-party libraries, services]

### Data stores, schemas and transactions
[Databases, tables, collections, transaction boundaries]

### State machines and invariants
[Valid state transitions and terminal states]

### Trust boundaries and permissions
[Authentication, authorization, untrusted input boundaries]

### Build, tests, CI/CD and deployment
[Existing tests, build tools, deployment target]

### Observability, backup and recovery
[Metrics, structured logs, alarms, recovery procedures]

### Unknown or uninspected areas
[Modules or paths not inspected during this pass]

## Code-path and change-impact analysis
| Operation/entry point | Path traced | Side effects | Existing contract | Affected consumers | Test coverage |
|---|---|---|---|---|---|
| `entry_point_name` | `caller` -> `callee` | State mutation | Must preserve return shape | API consumers | [e.g. 80% / 0%] |

## Evidence, assumptions, and unknowns
| ID | Statement | Type (Observed / Assumed / Hypothesis) | Evidence | Impact if wrong |
|---|---|---|---|---|
| E-01 | Baseline architectural assumption | Observed | `path/to/file:L10` | High |

## Coverage matrix
| Layer/domain | Status (covered / not-applicable / not-assessed) | Inspected evidence or reason |
|---|---|---|
| State/concurrency | covered | Traced state transitions and concurrency safety |
| Security/auth | covered | Verified trust boundaries and access controls |
| Scale/operability | covered | Checked resource limits, queues, and timeouts |

## Risk register

### FL-001 — Example risk record title
- **Status:** CONFIRMED
- **Evidence level:** OBSERVED
- **Priority:** HIGH
- **Severity:** HIGH
- **Likelihood:** LIKELY
- **Confidence:** HIGH
- **Disposition:** MITIGATE
- **Domain:** Runtime / Logic
- **Components/paths:** `path/to/source.py:function_name`
- **Evidence:** Concrete code snippet, test output, or reproduction trace.
- **Preconditions:** Pre-state or caller permissions required to reach path.
- **Trigger:** Exact input, event, or concurrency interleaving.
- **Failure sequence:** Step-by-step causal chain leading to failure.
- **Expected behavior:** Correct invariant or observable outcome.
- **Observed behavior:** Actual failure, unhandled exception, or corrupt state.
- **Impact:** Blast radius, data loss, security exposure, or degradation.
- **Detection/recovery:** Observability signal and rollback mechanism.
- **Mitigation:** Recommended concrete code or architectural remediation.
- **Reproduction/test:** Safe verification command or test scenario.
- **Acceptance test:**
  - **Given** specific initial state and valid preconditions.
  - **When** the trigger action or event occurs.
  - **Then** expected observable behavior is verified and invariants hold.

## Failure chains and pre-mortem
[Pre-mortem failure scenarios: how this subsystem could fail under stress, bad deploy, or dependency failure]

## Break attempts and test results
[Safe inspection commands run, tests executed, or static trace results]

## Specialist review provenance
- `faultline-system-mapper`: Mapped components and entry points.
- `faultline-runtime-breaker`: Traced execution paths and error propagation.
- `faultline-state-concurrency-breaker`: Evaluated state machine transitions and locking.
- `faultline-security-abuser`: Inspected trust boundaries and input sanitization.
- `faultline-scale-operations-breaker`: Assessed resource limits and recovery.
- `faultline-skeptical-synthesizer`: Challenged findings and refined risk ranking.

## Proposed requirements and scenarios
1. [Concrete requirement derived from FL-001]

## Decisions required before specification
[Decisions needed before finalizing implementation design]

## Limitations
[Scope boundaries, unverified third-party APIs, environment constraints]
"""

    if output_path is not None:
        target_file = output_path
    else:
        if mode == "break-existing-system":
            target_dir = ROOT / "docs" / "engineering" / "faultline"
        else:
            target_dir = ROOT / "docs" / "engineering" / "pre-spec"
        target_file = target_dir / f"{clean_slug}.md"

    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(content.strip() + "\n", encoding="utf-8")
    return target_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a structurally valid Faultline preflight report.")
    parser.add_argument("slug", help="Slug identifier for the report (e.g. payment-flow, auth-v2)")
    parser.add_argument("--title", help="Human-readable title (defaults to title-cased slug)")
    parser.add_argument(
        "--mode",
        choices=["brownfield-preflight", "greenfield-preflight", "break-existing-system"],
        default="brownfield-preflight",
        help="Preflight mode (default: brownfield-preflight)",
    )
    parser.add_argument("-o", "--output", type=Path, help="Custom output file path")
    args = parser.parse_args()

    out = scaffold_report(slug=args.slug, title=args.title, mode=args.mode, output_path=args.output)
    print(f"Scaffolded valid Faultline report at: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
