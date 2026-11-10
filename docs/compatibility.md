# Compatibility Reference (v0.4.0)

## Shared Agent Skills Specification

- Canonical skills source: `skills/<name>/SKILL.md` at repository root, following the Agent Skills open standard.
- Backward compatibility: `.agents/skills` is maintained as a relative symlink pointing to `../skills`.
- Each skill package contains:
  - `SKILL.md` (mandatory entry point with YAML frontmatter)
  - `references/` (methodology, protocols, checklists, schemas)
  - `templates/` (structured report templates)

## Multi-Host Support Matrix

| Host Environment | Skills Location | Agent Adapters | Instruction / Gate Integration | Auto-Detection Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **Google Antigravity** | `.agents/skills/` | `.agents/agents/` | `AGENTS.md` (marked block) | Default |
| **OpenCode** | `.agents/skills/` | `.opencode/agents/` | `AGENTS.md` | Default |
| **Claude Code** | `.claude/skills/` | `.claude/agents/` | `CLAUDE.md` (marked block) | `.claude/` or `CLAUDE.md` |
| **Amazon Kiro** | `.kiro/skills/` | `.kiro/agents/` | `.kiro/hooks/faultline-gate.json` | `.kiro/` |
| **Cursor** | `.agents/skills/` | N/A | `.cursor/rules/faultline.mdc` | `.cursor/` or `.cursorrules` |
| **GitHub Copilot** | `skills/` or `.agents/skills/` | N/A | `.github/copilot-instructions.md` | `.github/` |
| **Zed / Codex / Other** | `skills/` or `.agents/skills/` | Sequential passes | `AGENTS.md` | Default |

## Host Details

### Google Antigravity
- Workspace skills: `.agents/skills/` (resolves to `skills/`).
- Workspace subagents: `.agents/agents/<name>.md`.
- Frontmatter uses `subagent: true`, `commandExecutionPolicy: sandbox`, and standard tool IDs (`view_file`, `grep_search`, `run_command`).
- Native subagent invocation via `invoke_subagent`.

### OpenCode
- Project skills: `.agents/skills/` (resolves to `skills/`).
- Project agent definitions: `.opencode/agents/<name>.md`.
- Specialists use `mode: subagent` with explicit `permissions` lists (read/glob/grep/list allowed, edit denied, shell ask, web denied).
- `faultline-orchestrator` is a `mode: primary` agent with a delegation allowlist restricted to the 6 Faultline specialists.

### Claude Code
- Project skills: `.claude/skills/`.
- Project subagents: `.claude/agents/<name>.md`.
- Global skills: `~/.claude/skills/`.
- Instruction block: `CLAUDE.md` delimited by `<!-- faultline:start -->` and `<!-- faultline:end -->`.

### Amazon Kiro
- Project skills: `.kiro/skills/`.
- Project agents: `.kiro/agents/<name>.md`.
- Event hook: `.kiro/hooks/faultline-gate.json` configures pre-implementation gate enforcement.

### Cursor
- Rule file: `.cursor/rules/faultline.mdc` configures agent behavior to invoke Faultline preflight prior to code generation.

### GitHub Copilot
- Instructions file: `.github/copilot-instructions.md` provides architectural and adversarial preflight guidance delimited by marker comments.

## Single Source of Truth & Adapter Compiler

- Specialist definitions are maintained in `definitions/specialists.json`.
- `scripts/build_adapters.py` compiles all specialist markdown files across `.agents/agents/`, `.opencode/agents/`, `.claude/agents/`, and `.kiro/agents/`.
- Run `python3 scripts/build_adapters.py --check` in CI to ensure zero drift.

## Universal Installer (`install.py`)

- **Zero External Dependencies**: Pure Python 3 standard library.
- **Dual Scopes**:
  - Project scope: `python3 install.py /path/to/project`
  - Global user scope: `python3 install.py --global` (installs to `~/.agents/skills/`, `~/.claude/skills/`, `~/.kiro/skills/`, etc.)
- **Smart Auto-Detection**: Inspects directory markers (`.github/`, `.cursor/`, `.claude/`, `.kiro/`) and installs corresponding integrations automatically. Use `--all` to force installation of all environments.
- **Delimited Block Safety**: Refreshes only content between `<!-- faultline:start -->` and `<!-- faultline:end -->` in instruction files without touching user configuration.
- **Cross-Platform Wrappers**:
  - POSIX: `./install.sh [options] [target]`
  - PowerShell: `.\install.ps1 [options] [target]`

## Portability Limits

- Core skills and prompts are vendor-neutral.
- Native agent definitions and delegation configurations are host-specific adapters.
- When subagents are not supported by a host, run the roles as sequential analysis passes and clearly label them as not independently verified.
