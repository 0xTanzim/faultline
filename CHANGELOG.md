# Changelog

## 0.5.0-beta.1 — Streamed 1-line installer, report scaffolder, uninstaller, and SARIF export

- Added streamed remote 1-liner installation via `curl | bash` (POSIX) and `irm | iex` (PowerShell) fetching GitHub release archives dynamically without requiring manual git clone.
- Added clean rollback and uninstallation (`install.py --uninstall`) safely stripping marked instruction blocks while preserving user rules.
- Added report scaffolder (`scripts/scaffold_report.py` / `npm run new:report`) generating 100% structurally valid skeleton reports ready for analysis.
- Made `scripts/validate_report.py` case-insensitive and whitespace-tolerant on required section titles and flexible on risk heading syntax.
- Added enterprise CI/CD report exporter (`scripts/export_report.py` / `npm run export:report`) supporting standard SARIF v2.1.0 for GitHub Code Scanning and structured JSON.
- Expanded automated test suite to 26 unit tests covering uninstallation, scaffolding, SARIF export, and validator robustness.

## 0.4.1 — Strict DRY & Dynamic Runtime Compilation

- Enforced strict DRY (Don't Repeat Yourself) architecture: deleted 24 committed static markdown adapter files across `.claude/`, `.kiro/`, `.opencode/`, and `.agents/` from git.
- Made `definitions/specialists.json` the sole authoritative source for specialist roles, tools, prompts, and sandboxing policies.
- Implemented in-memory dynamic runtime adapter compilation in `install.py` and `scripts/build_adapters.py`, rendering host-specific adapters directly into target projects on the fly during installation.
- Reorganized integration templates, rules, and snippets cleanly into `templates/` (`templates/cursor/`, `templates/kiro/`, `templates/snippets/`).
- Updated `subagent-protocol.md` to reference the canonical JSON single source of truth, eliminating prose duplication.
- Updated validation scripts and test suite (22 unit tests passing) to enforce the DRY repository structure and dynamic compiler invariants.

## 0.4.0 — Canonical skills, multi-host compiler, and universal cross-OS installer

- Moved portable skills to canonical root `skills/` directory (`skills/faultline-preflight/`, `skills/faultline-break-sweep/`, `skills/faultline-spec-audit/`) conforming to Agent Skills standard, with `.agents/skills` maintained as a backward-compatible symlink.
- Established Single Source of Truth for specialist roles in `definitions/specialists.json` (system-mapper, runtime-breaker, state-concurrency-breaker, security-abuser, scale-operations-breaker, skeptical-synthesizer).
- Added `scripts/build_adapters.py` compiler with `--check` parity verification, automatically generating adapters for Google Antigravity, OpenCode, Claude Code, and Amazon Kiro.
- Implemented pure Python 3 cross-platform installer (`install.py`) with zero external dependencies, supporting project scope and global user scope (`--global`).
- Added smart environment auto-detection for GitHub Copilot (`.github/`), Cursor (`.cursor/`, `.cursorrules`), Claude Code (`.claude/`, `CLAUDE.md`), and Amazon Kiro (`.kiro/`).
- Added delimited marker block injection (`<!-- faultline:start -->` ... `<!-- faultline:end -->`) for `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` with non-destructive refresh.
- Added cross-platform shell wrapper `install.sh` and PowerShell wrapper `install.ps1`.
- Added integration templates for Claude Code (`integrations/CLAUDE.md.snippet`), GitHub Copilot (`integrations/copilot-instructions.md.snippet`), Cursor rules (`.cursor/rules/faultline.mdc`), and Amazon Kiro hooks (`.kiro/hooks/faultline-gate.json`).
- Updated validation scripts and expanded test suite covering multi-host adapter generation, auto-detection, global install, and dry-run safety.

## 0.3.0 — Brownfield break-testing upgrade

- Added `faultline-break-sweep` for deliberate, read-only attempts to falsify existing implementation behavior.
- Added mandatory system-level repository reconnaissance and actual code-path tracing.
- Added safe test execution classification and mutation-oriented test-sensitivity review.
- Added six specialist agent roles.
- Added Antigravity native subagent definitions and OpenCode V2 agent definitions.
- Added a restricted OpenCode primary orchestrator and named subagent allowlist.
- Expanded report schema/template and validator for system map, path analysis, break attempts and provenance.
- Updated OpenSpec audit to check brownfield compatibility and existing contracts.
- Preserved vendor-neutral core methodology; no provider/model pinning.

## 0.2.0 — Brownfield reconnaissance groundwork

- Added system-level repository map, code-path tracing and specialist protocol.

## 0.1.0 — Initial portable skill pack

- Added preflight and OpenSpec spec-audit skills.
- Added evidence-aware risk register and structural report validator.
