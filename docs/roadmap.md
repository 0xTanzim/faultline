# Roadmap

## 0.4.0 — Canonical skills, multi-host compiler, and universal installer
- Portable skills moved to standard visible root `skills/` directory (`.agents/skills` symlink for dogfooding).
- Single Source of Truth for specialist roles in `definitions/specialists.json`.
- Adapter compiler (`scripts/build_adapters.py`) generating adapters for Antigravity, OpenCode, Claude Code, and Kiro.
- Pure Python 3 universal installer (`install.py`) with `--global` and project scopes.
- Smart auto-detection for GitHub Copilot, Cursor, Claude Code, and Amazon Kiro.
- Delimited marker block injection (`<!-- faultline:start -->` ... `<!-- faultline:end -->`) preserving user configurations.
- Cross-platform wrappers (`install.sh`, `install.ps1`).

## 0.5.0 — Evaluation harness
- Seeded benchmark repositories and known defect scenarios.
- Negative controls where the correct answer is no finding.
- Cross-agent/model runs with repeatable prompts and configs.
- Metrics: recall, false-positive rate, severity calibration, scenario precision,
  reproducibility, coverage and cost.

## 0.6.0 — Test adapters
- Optional adapters for property-based, model-based, mutation, contract and fuzz tools.
- Stack-aware detection without forced dependency installation.
- Disposable test environment checks, timeouts and stop conditions.
- JSON risk output and SARIF export.

## 1.0.0 — Stable preflight system
- Published compatibility matrix backed by CI and live-host tests.
- Stable report schema/version migration.
- Optional host-specific hooks/CI gates for enforceable policy.

## Non-goals
- Claim every possible failure can be discovered by prompting.
- Execute uncontrolled/destructive tests on real systems.
- Require any model provider or vendor subagent API.
- Modify application code during preflight.
