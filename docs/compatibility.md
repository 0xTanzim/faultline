# Compatibility Reference (v0.4.1)

## Shared Agent Skills Specification

- Canonical skills source: `skills/<name>/SKILL.md` at repository root, following the Agent Skills open standard.
- Backward compatibility: `.agents/skills` is maintained as a relative symlink pointing to `../skills`.
- Each skill package contains:
  - `SKILL.md` (mandatory entry point with YAML frontmatter)
  - `references/` (methodology, protocols, checklists, schemas)
  - `templates/` (structured report templates)

## Multi-Host Support Matrix

| Host Environment | Skills Location | Dynamic Subagent Adapters | Instruction / Gate Integration | Auto-Detection Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **Google Antigravity** | `.agents/skills/` | `.agents/agents/` (rendered) | `AGENTS.md` (marked block) | Default |
| **OpenCode** | `.agents/skills/` | `.opencode/agents/` (rendered) | `AGENTS.md` | Default |
| **Claude Code** | `.claude/skills/` | `.claude/agents/` (rendered) | `CLAUDE.md` (marked block) | `.claude/` or `CLAUDE.md` |
| **Amazon Kiro** | `.kiro/skills/` | `.kiro/agents/` (rendered) | `.kiro/hooks/faultline-gate.json` | `.kiro/` |
| **Cursor** | `.agents/skills/` | N/A (Rules-based) | `.cursor/rules/faultline.mdc` | `.cursor/` or `.cursorrules` |
| **GitHub Copilot** | `skills/` or `.agents/skills/` | N/A (Instruction-based) | `.github/copilot-instructions.md` | `.github/` |
| **Zed / Codex / Other** | `skills/` or `.agents/skills/` | Sequential passes | `AGENTS.md` | Default |

## Single Source of Truth & Dynamic Runtime Compiler

- Specialist definitions are maintained in `definitions/specialists.json` (the sole authoritative source for roles, tools, prompts, and sandboxing).
- `install.py` dynamically compiles host-specific adapters directly into the target project or user environment at install time.
- The source repository stays strictly DRY and contains zero duplicate markdown adapter files.
- `python3 scripts/build_adapters.py --check` validates schema completeness and syntactic correctness.

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
