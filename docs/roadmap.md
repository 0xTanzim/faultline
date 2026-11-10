# Roadmap

## 0.3.0 — Brownfield break analysis and specialist adapters
- Mandatory system-level reconnaissance for existing repositories.
- Actual code-path/side-effect trace and impact analysis.
- Active break-session protocol with safe tests and mutation-oriented challenges.
- Dedicated `faultline-break-sweep` skill.
- Six specialist role prompts and native Antigravity/OpenCode adapters.
- OpenCode V2 agent permission configuration and restricted orchestrator.

## 0.4.0 — Evaluation harness
- Seeded benchmark repositories and known defect scenarios.
- Negative controls where the correct answer is no finding.
- Cross-agent/model runs with repeatable prompts and configs.
- Metrics: recall, false-positive rate, severity calibration, scenario precision,
  reproducibility, coverage and cost.

## 0.5.0 — Test adapters
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
