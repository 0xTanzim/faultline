# Faultline

[![Version](https://img.shields.io/badge/version-0.5.0--beta.1-blue.svg)](VERSION)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](install.py)
[![Standard](https://img.shields.io/badge/standard-Agent%20Skills-purple.svg)](skills/)
[![Multi--Host](https://img.shields.io/badge/hosts-Antigravity%20%7C%20OpenCode%20%7C%20Claude%20%7C%20Kiro%20%7C%20Cursor%20%7C%20Copilot-orange.svg)](docs/compatibility.md)

**Portable adversarial engineering intelligence for AI coding agents.**

Faultline forces coding agents to map real repositories, trace actual execution paths, and try to falsify behavior **before** a specification or implementation is finalized — not after. Designed for brownfield (existing) projects first, stopping bugs, broken invariants, and regressions before they are written into code.

---

## Why Faultline?

Most agent workflows jump straight from a user prompt to code generation. In production systems, the most dangerous unknowns live in the existing codebase: implicit invariants, brittle contracts, legacy side effects, unhandled error paths, and failure combinations that only become apparent when you trace what the code actually does.

Faultline enforces a **pre-implementation falsification gate**:
1. **Map** the real system (components, entry points, data flows, trust boundaries).
2. **Trace** affected code paths and state transitions.
3. **Falsify** assumptions using adversarial specialists (runtime, concurrency, security, scale).
4. **Rank** risks with qualitative evidence (Severity, Likelihood, blast radius).
5. **Output** concrete Given/When/Then test scenarios before any production code is touched.

---

## Multi-Host Support Matrix

Faultline is host-agnostic and strictly DRY. Specialist definitions are authored **once** in `definitions/specialists.json` and compiled **dynamically at runtime** into target environments by `install.py`:

| Host Environment | Skills Location | Dynamic Subagent Adapters | Instruction & Gate Integration | Auto-Detection Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **Google Antigravity** | `.agents/skills/` (symlink) | `.agents/agents/` (rendered) | `AGENTS.md` (marked block) | Default |
| **OpenCode** | `.agents/skills/` (symlink) | `.opencode/agents/` (rendered) | `AGENTS.md` | Default |
| **Claude Code** | `.claude/skills/` | `.claude/agents/` (rendered) | `CLAUDE.md` (marked block) | `.claude/` or `CLAUDE.md` |
| **Amazon Kiro** | `.kiro/skills/` | `.kiro/agents/` (rendered) | `.kiro/hooks/faultline-gate.json` | `.kiro/` |
| **Cursor** | `skills/` or `.agents/skills/` | N/A (Rules-based) | `.cursor/rules/faultline.mdc` | `.cursor/` or `.cursorrules` |
| **GitHub Copilot** | `skills/` or `.agents/skills/` | N/A (Instruction-based) | `.github/copilot-instructions.md` | `.github/` |
| **Zed / Codex / Other** | `skills/` or `.agents/skills/` | Sequential passes | `AGENTS.md` | Default |

---

## What's Included

### 1. Portable Agent Skills (Canonical Root `skills/`)

Conforms to the open **Agent Skills standard** (`anthropics/skills` layout) with a backward-compatible `.agents/skills` symlink:

| Skill | Description | Primary Command |
|---|---|---|
| `faultline-preflight` | Full brownfield preflight: system mapping, failure analysis, specialist orchestration, and durable report generation | `/faultline-preflight` |
| `faultline-break-sweep` | Focused adversarial sweep of existing code; uncover regressions and test gaps without modifying code | `/faultline-break-sweep` |
| `faultline-spec-audit` | Audit an OpenSpec proposal against preflight findings; verify risks become concrete Given/When/Then scenarios | `/faultline-spec-audit` |

### 2. Six Specialist Subagent Roles

When the problem scope justifies it, the orchestrator delegates to independent read-only specialists:

| Specialist Role | Focus Area |
|---|---|
| `system-mapper` | Packages, entry points, call/dependency graph, data stores, trust boundaries, configuration |
| `runtime-breaker` | Execution paths, branches, errors, cancellation, timeouts, partial writes, crash points, recovery |
| `state-concurrency-breaker` | State machines, invariants, transactions, locks, races, ordering, idempotency, stale reads |
| `security-abuser` | Authentication, authorization, trust boundaries, injection, data exposure, tenant isolation |
| `scale-operations-breaker` | Resource ceilings, queues, backpressure, startup/shutdown, deployment, telemetry, logging |
| `skeptical-synthesizer` | Independent verification: challenges draft findings, flags false positives, checks evidence |

> **Single Source of Truth (SSOT):** Specialist prompts are authored once in `definitions/specialists.json` and compiled across Antigravity, OpenCode, Claude Code, and Kiro via `scripts/build_adapters.py`.

### 3. Supporting Methodologies & References

Located inside `skills/faultline-preflight/references/`:
- **Failure Taxonomy:** Multi-method coverage including FMEA, STRIDE, pre-mortem, state/invariant analysis, and fault-tree analysis.
- **Risk Model:** Qualitative severity/likelihood matrix with explicit blast radius criteria.
- **System-Level Checklist:** Core break scenarios across state, distributed boundaries, resources, and dependencies.
- **Delegation Protocol:** Rules for parallel subagent invocation, result schema, and synthesis.
- **Report Schema & Template:** Machine-validatable Markdown report template with Given/When/Then scenario structures.

---

## Installation

Faultline features a universal, zero-dependency installer (`install.py`) written in pure Python 3 standard library, with shell wrappers supporting local execution and modern streamed one-liner installation.

### 1-Line Remote Install (No Clone Required)

Install directly from GitHub into any target project:

```bash
# POSIX (Linux, macOS)
curl -fsSL https://raw.githubusercontent.com/0xTanzim/faultline/main/install.sh | bash -s -- /path/to/project

# Windows PowerShell
irm https://raw.githubusercontent.com/0xTanzim/faultline/main/install.ps1 | iex
```

### Local Project Installation

```bash
# Pure Python (Linux, macOS, Windows)
python3 install.py /path/to/project

# POSIX Shell
./install.sh /path/to/project

# Windows PowerShell
.\install.ps1 C:\path\to\project
```

The installer detects your project markers (e.g. `.github/`, `.cursor/`, `.claude/`, `.kiro/`) and configures only the relevant host adapters and rules automatically.

### Global Installation (User Scope)

To use Faultline across all repositories on your system without installing into every individual repository:

```bash
python3 install.py --global
```

This installs portable skills to `~/.agents/skills/`, `~/.claude/skills/`, and `~/.kiro/skills/`.

### Clean Uninstallation / Rollback

To cleanly remove Faultline skills, generated adapters, and strip all marked instruction blocks without touching your custom rules:

```bash
python3 install.py --uninstall /path/to/project

# Global uninstall:
python3 install.py --uninstall --global
```

### Advanced Options & Flags

```bash
# Preview what would be created/modified without writing files:
python3 install.py --dry-run /path/to/project

# Install adapters for all supported environments regardless of auto-detection:
python3 install.py --all /path/to/project

# Force overwrite existing Faultline files and refresh marked instruction blocks:
python3 install.py --force /path/to/project

# Cleanly remove Faultline from a project or global scope:
python3 install.py --uninstall /path/to/project
```

### Delimited Marker Safety

When adding instructions to `AGENTS.md`, `CLAUDE.md`, or `.github/copilot-instructions.md`, Faultline encloses its additions inside explicit safety markers:

```markdown
<!-- faultline:start -->
## Faultline Preflight Gate
...
<!-- faultline:end -->
```

Running `python3 install.py --force` replaces **only** the content inside the markers, leaving all of your existing configuration, rules, and notes completely intact.

---

## Workflows & Usage

### 1. Preflight Before a Feature or Spec

Before writing a spec or beginning an implementation, run `faultline-preflight`:

#### In Google Antigravity:
```text
/faultline-preflight Analyze the proposed caching layer against our existing database access paths.
Map affected components, trace failure paths, and identify broken invariants. Do not edit code.
```

#### In OpenCode:
Select `faultline-orchestrator` as the primary agent (press `Tab` to open agent selector), then prompt:
```text
Run Faultline preflight against the payment processing service.
Map real entry points, trace partial write behaviors, and delegate to specialist agents.
```

#### In Claude Code:
```text
/faultline-preflight on the order cancellation flow.
Check database transactions, out-of-order webhooks, and retry policies.
```

#### In Cursor / GitHub Copilot:
Ask the assistant to follow the installed Faultline rules before proposing code changes:
```text
Apply Faultline preflight rules to this change. Trace affected call paths and
identify high-risk failure modes with Given/When/Then test scenarios before proposing diffs.
```

---

### 2. Adversarial Codebase Audit (Brownfield Sweep)

To inspect an existing codebase for edge cases, missing tests, and brittle invariants without a specific feature request:

```text
/faultline-break-sweep Inspect the authentication and session management subsystem.
Trace actual entry points, evaluate token refresh races and clock drift, and check existing test coverage.
Do not modify any files.
```

---

### 3. Spec Audit (Post-OpenSpec)

Once a specification or OpenSpec proposal has been drafted, verify that preflight findings were faithfully incorporated:

```text
/faultline-spec-audit Audit proposal at openspec/changes/payment-v2 against docs/engineering/pre-spec/payment-v2.md.
Confirm all Critical and High risks were converted into explicit, testable Given/When/Then scenarios.
```

---

## Safety & Security Model

Faultline is **strictly read-only by default**:

- **No Code Modifications:** Does not edit production source files, test fixtures, schema migrations, or configurations during analysis.
- **Permission Sandboxing:** OpenCode adapters enforce explicit read-only permissions (`edit: deny`, `shell: ask`, `web: deny`). Antigravity adapters use `commandExecutionPolicy: sandbox`.
- **Safe Command Execution:** Only non-destructive inspection commands (e.g., `git status`, test runners) are permitted. Destructive commands or live network probes are forbidden.
- **Secret Hygiene:** Detects and redacts credentials, tokens, and keys found in code; never reproduces secrets in reports.
- **Untrusted Input Handling:** Treats all repository code and configuration files as untrusted data, preventing prompt injection attacks from adversarial codebases.

---

## Report Artifacts, Scaffolding & CI Export

Every completed preflight generates a durable, reviewable markdown report:

- **Pre-spec Reports:** `docs/engineering/pre-spec/<change-slug>.md`
- **Brownfield Audits:** `docs/engineering/faultline/<scope-slug>.md`

### 1. Scaffolding a Valid Report Skeleton

Generate an immediately-valid skeleton report pre-populated with all required sections:

```bash
npm run new:report -- payment-flow --title "Payment Gateway Audit"
# or: python3 scripts/scaffold_report.py payment-flow --title "Payment Gateway Audit"
```

### 2. Validating Reports

Validate report formatting, risk schemas, and required Given/When/Then verification scenarios:

```bash
python3 scripts/validate_report.py docs/engineering/pre-spec/payment-flow.md
```

### 3. Exporting to SARIF (GitHub Code Scanning) & JSON

Export validated preflight findings to standard **SARIF v2.1.0** for GitHub Security dashboard integration, or structured **JSON** for automated CI gates:

```bash
# Export to SARIF
npm run export:report -- docs/engineering/pre-spec/payment-flow.md --format sarif -o report.sarif

# Export to structured JSON
npm run export:report -- docs/engineering/pre-spec/payment-flow.md --format json -o report.json
```

---

## Repository Structure

```
skills/                         # Canonical root skills (Agent Skills open standard)
  faultline-preflight/          # Main preflight skill
    SKILL.md
    references/                 # Methods, taxonomy, schema, delegation protocol
    templates/                  # Durable preflight report template
  faultline-break-sweep/        # Adversarial sweep of existing code
    SKILL.md
  faultline-spec-audit/         # Post-OpenSpec audit
    SKILL.md
    references/                 # Audit checklist and verification rules
definitions/
  specialists.json              # Single Source of Truth for specialist roles
templates/                      # Clean reusable integration templates & rules
  cursor/faultline.mdc          # Cursor rule template
  kiro/faultline-gate.json      # Kiro event hook template
  snippets/AGENTS.md.snippet    # Injected into project AGENTS.md
  snippets/CLAUDE.md.snippet    # Injected into project CLAUDE.md
  snippets/copilot-instructions.md.snippet # Injected into project copilot-instructions.md
.agents/
  skills -> ../skills           # Relative symlink for local Antigravity compatibility
install.py                      # Pure Python 3 dynamic runtime compiler & installer
install.sh                      # POSIX wrapper
install.ps1                     # PowerShell wrapper
scripts/
  build_adapters.py             # Dynamic adapter compiler & schema validator
  validate_skills.py            # Structural validator for skills, templates & compilation
  validate_report.py            # Structural validator for preflight reports
tests/                          # Unittest test suite (22 tests passing)
```

---

## Development & Testing

Faultline maintains strict test coverage and zero runtime dependencies outside Python 3 standard library:

```bash
# Run all unit tests
python3 -m unittest discover -s tests -v

# Or using npm
npm test

# Check adapter synchronization against Single Source of Truth
npm run check:adapters
# or: python3 scripts/build_adapters.py --check

# Compile adapters after modifying definitions/specialists.json
npm run build:adapters
# or: python3 scripts/build_adapters.py

# Validate skills, schema, and host adapters
npm run validate:skills
# or: python3 scripts/validate_skills.py
```

---

## License

[MIT](LICENSE) © 2026 Tanzim & Contributors
