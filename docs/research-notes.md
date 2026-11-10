# Research notes — checked 2026-11-10

These notes record methodology inspiration, not copied implementations.

- `mattnowdev/thinking-partner` (MIT): useful for assumption-challenging, inversion, second-order thinking, systems thinking and selecting a small number of relevant mental models. Avoid a 150-model dump; its own workflow warns against that anti-pattern. GitHub metadata checked 2026-11-10: last push reported 2026-03-31; `updated_at` was 2026-11-05. The latter does not necessarily mean source code changed.
- `MADEVAL/Pre-Mortem-Skill` (GPL-3.0): useful for prospective hindsight, boring/base-rate failures, balanced internal/external causes, likelihood/impact discussion, parallel deep dives, synthesis and an explicit gap check. GitHub metadata checked 2026-11-10: last push reported 2026-06-30; `updated_at` was 2026-11-09. `updated_at` can reflect repository activity, not necessarily a code push.
- Agent Skills specification: portable package is a directory containing `SKILL.md` plus optional references/scripts/assets. The format does not standardize host subagent APIs.
- Antigravity: workspace custom subagents live in `.agents/agents/`; `subagent: true` agents are invoked through `invoke_subagent` and can run concurrently with fresh context.
- OpenCode current docs: custom agent files live in `.opencode/agents/`; use `mode: subagent` for specialists, a primary orchestrator for delegation, and `permissions` to scope access. OpenCode V2 uses current permissions-list syntax, not deprecated V1 fields.
- OpenSpec's current support matrix lists both Antigravity and OpenCode; OpenSpec workflow delivery and Faultline are separate.

Checked links:
- https://github.com/mattnowdev/thinking-partner
- https://github.com/mattnowdev/thinking-partner/blob/main/skills/thinking-partner/SKILL.md
- https://github.com/MADEVAL/Pre-Mortem-Skill
- https://github.com/MADEVAL/Pre-Mortem-Skill/blob/main/Skill.md
- https://agentskills.io/specification
- https://antigravity.google/docs/subagents
- https://opencode.ai/docs/agents/
- https://openspec.dev/docs/supported-tools
