# Faultline

**Portable adversarial engineering intelligence for AI coding agents.**

Faultline makes coding agents map a real repository, trace actual code paths, and try to falsify behavior *before* a specification or implementation is finalized — not after. It is designed for brownfield (existing) projects first, not only greenfield feature briefs.

---

## Why Faultline?

Most agent workflows jump straight from a feature description to code generation. In real projects, the dangerous unknowns live in the existing system: hidden invariants, implicit contracts, legacy edge cases, and failure combinations that only appear when you trace what the code actually does.

Faultline enforces a **falsification pass** before any implementation: map the real system, trace the affected paths, break the contracts, rank the risks — then write a spec or proceed to code.

---

## What's Included

| Skill | Purpose |
|---|---|
| `faultline-preflight` | Full system-level preflight: brownfield reconnaissance, failure analysis, specialist delegation, and durable report output |
| `faultline-break-sweep` | Focused adversarial sweep of an existing implementation; find defects and test gaps without touching production code |
| `faultline-spec-audit` | Audit an OpenSpec proposal against the preflight report; verify risks became concrete, testable Given/When/Then scenarios |

**Supporting artifacts:**
- System-level break checklist
- Multi-method failure taxonomy (FMEA, STRIDE, pre-mortem, state/invariant analysis, fault-tree reasoning)
- Risk model with qualitative severity/likelihood matrix
- Specialist delegation protocol with six adversarial roles
- Structured report schema and durable report template
- Structural validator script

**Native subagent adapters for:**
- **Google Antigravity** — six workspace subagents under `.agents/agents/`
- **OpenCode** — six specialist subagents and a restricted primary orchestrator under `.opencode/agents/`

---

## Six Specialist Roles

When the problem scope justifies it, the orchestrating agent delegates to independent read-only specialists running in parallel:

| Role | Responsibility |
|---|---|
| `system-mapper` | Map components, entry points, data flows, trust boundaries, external dependencies |
| `runtime-breaker` | Trace execution paths, partial writes, retries, timeouts, crash points, recovery failures |
| `state-concurrency-breaker` | Inspect state invariants, duplicate delivery, races, ordering, transaction boundaries |
| `security-abuser` | Inspect auth, tenant isolation, trust boundaries, input abuse, data exposure |
| `scale-operations-breaker` | Inspect resource limits, queues, startup/shutdown, deploy/rollback, observability |
| `skeptical-synthesizer` | Challenge draft findings — false positives, omitted failure chains, missing evidence |

Specialists are always read-only. The orchestrator deduplicates, resolves disagreements with evidence, and owns final risk ranking.

---

## Install

Preview what will be written:

```bash
./install.sh --dry-run /path/to/your/project
```

Install into a project:

```bash
./install.sh /path/to/your/project
```

Force-refresh existing Faultline-owned files (inspect local modifications first):

```bash
./install.sh --force /path/to/your/project
```

Skip platform-specific agent adapters if you don't need them:

```bash
./install.sh --no-antigravity-agents /path/to/your/project
./install.sh --no-opencode-agents /path/to/your/project
```

**The installer writes:**
- Shared portable skills → `.agents/skills/`
- Antigravity custom subagents → `.agents/agents/`
- OpenCode agents → `.opencode/agents/`
- A delimited Faultline block → `AGENTS.md`

It preserves all unrelated `AGENTS.md` content and refuses to overwrite existing Faultline files unless `--force` is used.

---

## Usage

### Antigravity — preflight before a feature

```text
/faultline-preflight Analyze this feature against the existing codebase.
Map the system and try to break the affected paths. Do not modify code.
```

For complex work, the agent will invoke 3–5 of the native specialists defined in `.agents/agents/`. If it does not start them automatically, ask it explicitly to use the named specialists.

### OpenCode — preflight before a feature

Select `faultline-orchestrator` as the primary agent (Tab → agent selector), then:

```text
Run Faultline preflight against this existing codebase. Load the
faultline-preflight skill, map the system, try to falsify the affected
code paths, and delegate the read-only specialist agents. Do not modify code.
```

The orchestrator's allowlist restricts delegation to the six Faultline specialists only.

### Audit an existing codebase without a proposed feature

Use `faultline-break-sweep` on any host:

```text
Run a Faultline break sweep on the authentication subsystem. Inspect actual
entry points and tests, find reproducible failure paths, and run only safe
focused checks. Do not modify anything.
```

### Audit a spec after OpenSpec

After an OpenSpec proposal is generated, run `faultline-spec-audit` against the matching preflight report:

```text
Run faultline-spec-audit against the preflight report for <change-slug>.
Check that every Critical and High risk became a testable scenario.
```

---

## Safety Model

Faultline preflight is **read-only by default.** This is not advisory — it is enforced at the agent permission level.

- Does not edit source code, tests, migrations, lockfiles, or deployment files.
- Does not contact production systems, run destructive commands, or execute load/chaos/fuzz tests.
- Inspects build and test scripts before running them; asks before ambiguous side-effecting commands.
- Treats repository file contents as untrusted data, not instructions.
- Redacts secrets found in the repository; never copies values into reports.

---

## Report Output

A completed preflight produces a durable Markdown report at:

```
docs/engineering/pre-spec/<change-slug>.md
```

For codebase audits without a proposed change:

```
docs/engineering/faultline/<scope-slug>.md
```

Each report includes: executive summary, system map, code-path trace, evidence table, coverage matrix, ranked risk register (with status, evidence level, severity, likelihood, confidence, disposition, trigger, failure sequence, blast radius, and Given/When/Then acceptance test for every finding), failure chains, pre-mortem, break attempts, specialist provenance, and open decisions.

Validate report structure with the bundled script:

```bash
python3 scripts/validate_report.py docs/engineering/pre-spec/<slug>.md
```

The validator checks required sections, risk record fields, and enum values. It does not evaluate technical correctness or analysis completeness.

---

## Cross-Agent Portability

The core methodology, skill files, role prompts, report schema, and test contract are **vendor-neutral**. No model provider or vendor API is required or pinned.

Native subagent adapters (Antigravity and OpenCode) are host-specific because each platform exposes a different agent delegation mechanism. On a host without native subagents, the same specialist role prompts are run as clearly labeled sequential passes by the same agent.

---

## Repository Layout

```
.agents/
  skills/
    faultline-preflight/        # Main preflight skill
      SKILL.md
      references/               # Analysis methods, taxonomy, schema, protocol, checklist
      templates/                # Preflight report template
    faultline-break-sweep/      # Adversarial sweep of existing code
      SKILL.md
    faultline-spec-audit/       # Post-OpenSpec audit
      SKILL.md
      references/
  agents/                       # Antigravity native subagent adapters
.opencode/
  agents/                       # OpenCode V2 agent adapters
docs/
  methodology.md                # Why these analysis methods and how they combine
  compatibility.md              # Host-specific notes for Antigravity and OpenCode
  roadmap.md
examples/
  sample-preflight-report.md    # Annotated example report
  sample-risk-record.md
scripts/
  validate_report.py            # Report structure validator
  validate_skills.py            # Skill frontmatter structural validator
tests/                          # Python unittest suite
integrations/
  AGENTS.md.snippet             # Content injected into target AGENTS.md
install.sh                      # Installer
```

---

## Run Tests

```bash
python3 -m unittest discover -s tests -v
```

Or using `npm`:

```bash
npm test
```

Validate skill structure:

```bash
python3 scripts/validate_skills.py
```

---

## License

[MIT](LICENSE)
