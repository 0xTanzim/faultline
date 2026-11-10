# Compatibility Notes (v0.3.0)

## Shared Agent Skills

The portable core uses `.agents/skills/<name>/SKILL.md`. Agent Skills standardizes the package structure (`SKILL.md`, optional scripts/references/assets), not host discovery, command syntax, permissions or subagent APIs.

## Google Antigravity

- Workspace skills: `.agents/skills/`.
- Workspace custom subagents: `.agents/agents/<name>.md` or `<name>/agent.md`.
- Subagents: frontmatter `subagent: true`; parent invokes native `invoke_subagent`.
- Faultline adapters use only documented generic tool IDs (`view_file`, `grep_search`, `run_command`) and sandbox command execution. Verify tool availability in your Antigravity build before relying on execution; the shared role prompts remain usable if a tool is unavailable.

## OpenCode

- Project skills: `.agents/skills/` is a documented agent-compatible skill location.
- Project agent definitions: `.opencode/agents/<name>.md`.
- Current OpenCode V2 docs use `mode` and a `permissions` list. Faultline specialists are `mode: subagent` with editing denied. `faultline-orchestrator` is a primary agent with delegation allowed only to named Faultline roles.
- OpenCode agent configuration is host-specific and can evolve. Validate against the installed OpenCode version; do not copy old V1 `permission`/`tools` fields into V2 configuration.

## OpenSpec

OpenSpec's current support matrix lists Antigravity and OpenCode. OpenSpec workflows are separate from Faultline; the report is an input to explore/propose and an audit target after proposal creation.

## Existing repositories

Installer writes only Faultline-owned paths and a delimited section in `AGENTS.md`. It does not edit application files. It refuses existing Faultline-owned skill/agent paths unless `--force` is supplied. Back up or review local modifications before forced updates.

## Portability limits

- Shared skills and role prompts are vendor-neutral.
- Native agent definitions and delegation are host adapters.
- Skill auto-selection is not guaranteed; invoke explicitly.
- `AGENTS.md` is instruction guidance, not a hard lock.
- Without subagent support, sequential passes are not independent and must be labeled accordingly.
