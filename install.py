#!/usr/bin/env python3
"""Cross-platform installer for Faultline portable skills, native agent adapters, and integration gates."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import sys

START_MARKER = "<!-- faultline:start -->"
END_MARKER = "<!-- faultline:end -->"
RE_START_MARKER = re.compile(r"<!--\s*faultline:start\s*-->")
RE_END_MARKER = re.compile(r"<!--\s*faultline:end\s*-->")


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent


def get_version(repo_root: Path) -> str:
    version_file = repo_root / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.4.0"


def find_skills(repo_root: Path) -> list[str]:
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        # Fallback to .agents/skills if canonical skills directory not found
        skills_dir = repo_root / ".agents" / "skills"
    if not skills_dir.exists():
        return []
    skills = [
        d.name for d in sorted(skills_dir.iterdir())
        if d.is_dir() and (d / "SKILL.md").is_file()
    ]
    return skills


def safe_rmpath(p: Path) -> None:
    """Safely remove a file, symlink, or directory tree without throwing OSError on symlinked dirs."""
    if p.is_symlink() or p.is_file():
        p.unlink()
    elif p.is_dir():
        shutil.rmtree(p)


def check_delimited_collision(file_path: Path, force: bool) -> str | None:
    """Validate marker block integrity and collision state for a delimited file."""
    if not file_path.is_file():
        return None
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"ERROR: Cannot read {file_path}: {e}"

    start_matches = list(RE_START_MARKER.finditer(text))
    end_matches = list(RE_END_MARKER.finditer(text))

    if len(start_matches) == 0 and len(end_matches) == 0:
        return None
    if len(start_matches) == 1 and len(end_matches) == 0:
        return f"ERROR: {file_path} has an unmatched Faultline start marker. Repair it manually; refusing to truncate existing rules."
    if len(start_matches) == 0 and len(end_matches) == 1:
        return f"ERROR: {file_path} has an unmatched Faultline end marker. Repair it manually; refusing to truncate existing rules."
    if len(start_matches) > 1 or len(end_matches) > 1:
        return f"ERROR: {file_path} has multiple Faultline marker blocks. Repair it manually; refusing to truncate existing rules."
    if start_matches[0].start() > end_matches[0].start():
        return f"ERROR: {file_path} has corrupted Faultline marker ordering (end marker precedes start marker). Repair it manually; refusing to truncate existing rules."
    if not force:
        return f"ERROR: Faultline block already exists in {file_path}. Use --force to refresh it."
    return None


def replace_delimited_block(text: str, snippet_content: str) -> str:
    """Replace an existing marked block in-place, or append cleanly if no block exists."""
    start_matches = list(RE_START_MARKER.finditer(text))
    end_matches = list(RE_END_MARKER.finditer(text))

    if len(start_matches) == 1 and len(end_matches) == 1 and start_matches[0].start() < end_matches[0].end():
        start_m = start_matches[0]
        end_m = end_matches[0]
        line_start = text.rfind("\n", 0, start_m.start())
        prefix = text[: line_start + 1 if line_start != -1 else 0].rstrip()
        line_end = text.find("\n", end_m.end())
        suffix = text[line_end + 1 if line_end != -1 else len(text) :].lstrip("\r\n")

        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(snippet_content.strip())
        if suffix:
            parts.append(suffix)
        return "\n\n".join(parts) + "\n"

    content_before = text.rstrip()
    if content_before:
        return content_before + "\n\n" + snippet_content.strip() + "\n"
    return snippet_content.strip() + "\n"


def update_delimited_file(file_path: Path, snippet_path: Path, force: bool, dry_run: bool) -> tuple[bool, str]:
    """Check and update a delimited marker file (e.g. AGENTS.md, CLAUDE.md).

    Returns (changed, message).
    """
    err = check_delimited_collision(file_path, force=force)
    if err:
        return False, err

    if dry_run:
        return True, f"Would append/refresh only the marked Faultline block in: {file_path}"

    snippet_content = snippet_path.read_text(encoding="utf-8").strip()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.is_file():
        text = file_path.read_text(encoding="utf-8")
        final_text = replace_delimited_block(text, snippet_content)
    else:
        final_text = snippet_content + "\n"

    file_path.write_text(final_text, encoding="utf-8")
    return True, f"Updated {file_path}"


def install(
    target_arg: str | None,
    is_global: bool,
    dry_run: bool,
    force: bool,
    install_all: bool,
    no_antigravity: bool,
    no_antigravity_agents: bool,
    no_opencode: bool,
    no_claude: bool,
    no_kiro: bool,
    no_cursor: bool,
    no_copilot: bool,
) -> int:
    repo_root = get_repo_root()
    version = get_version(repo_root)

    if not is_global and not target_arg:
        if os.environ.get("npm_lifecycle_event") == "install":
            print(
                "Faultline installation requires a target directory or --global.\n"
                "Example: python3 install.py /path/to/project\n"
                "Or: npm run install -- /path/to/project\n"
                "Or: python3 install.py --global"
            )
            return 0
        print("Usage: install.py [options] <target-project>\nOr: install.py --global", file=sys.stderr)
        return 2

    if is_global and target_arg:
        print("ERROR: Cannot specify both a target directory and --global.", file=sys.stderr)
        return 2

    if is_global:
        target = Path.home().resolve()
    else:
        target = Path(target_arg).resolve()
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)

    skills_source = repo_root / "skills"
    if not skills_source.is_dir():
        skills_source = repo_root / ".agents" / "skills"
    skills = find_skills(repo_root)

    # Determine which integrations to install
    enable_antigravity = not no_antigravity
    enable_antigravity_agents = enable_antigravity and not no_antigravity_agents
    enable_opencode = not no_opencode

    if is_global:
        enable_claude = not no_claude
        enable_kiro = not no_kiro
        enable_cursor = False
        enable_copilot = False
    else:
        enable_claude = not no_claude and (install_all or (target / ".claude").is_dir() or (target / "CLAUDE.md").is_file())
        enable_kiro = not no_kiro and (install_all or (target / ".kiro").is_dir())
        enable_cursor = not no_cursor and (install_all or (target / ".cursor").is_dir() or (target / ".cursorrules").is_file())
        enable_copilot = not no_copilot and (install_all or (target / ".github").is_dir())

    # Pre-flight Collision Checks
    collision_errors: list[str] = []

    def check_file_collision(p: Path) -> None:
        if (p.exists() or p.is_symlink()) and not force:
            collision_errors.append(f"ERROR: {p} already exists. Use --force to replace Faultline-owned content.")

    def check_dir_collision(p: Path) -> None:
        if (p.exists() or p.is_symlink()) and not force:
            collision_errors.append(f"ERROR: {p} already exists. Use --force to replace Faultline-owned content.")

    # 1. Antigravity / Universal Skills & Agents
    ag_skills_dst = target / ".agents" / "skills"
    ag_agents_dst = target / ".agents" / "agents"
    agents_md = target / "AGENTS.md"
    ag_snippet = repo_root / "integrations" / "AGENTS.md.snippet"

    if enable_antigravity:
        for s in skills:
            check_dir_collision(ag_skills_dst / s)
        if enable_antigravity_agents:
            ag_agents_src = repo_root / ".agents" / "agents"
            if ag_agents_src.is_dir():
                for f in ag_agents_src.glob("faultline-*.md"):
                    check_file_collision(ag_agents_dst / f.name)
        if not is_global and ag_snippet.is_file():
            err = check_delimited_collision(agents_md, force=force)
            if err:
                collision_errors.append(err)

    # 2. OpenCode Agents
    oc_agents_dst = target / ".opencode" / "agents"
    if enable_opencode:
        oc_agents_src = repo_root / ".opencode" / "agents"
        if oc_agents_src.is_dir():
            for f in oc_agents_src.glob("faultline-*.md"):
                check_file_collision(oc_agents_dst / f.name)

    # 3. Claude Code
    claude_skills_dst = target / ".claude" / "skills"
    claude_agents_dst = target / ".claude" / "agents"
    claude_md = target / "CLAUDE.md"
    claude_snippet = repo_root / "integrations" / "CLAUDE.md.snippet"

    if enable_claude:
        for s in skills:
            check_dir_collision(claude_skills_dst / s)
        claude_agents_src = repo_root / ".claude" / "agents"
        if claude_agents_src.is_dir():
            for f in claude_agents_src.glob("faultline-*.md"):
                check_file_collision(claude_agents_dst / f.name)
        if not is_global and claude_snippet.is_file():
            err = check_delimited_collision(claude_md, force=force)
            if err:
                collision_errors.append(err)

    # 4. Amazon Kiro
    kiro_skills_dst = target / ".kiro" / "skills"
    kiro_agents_dst = target / ".kiro" / "agents"
    kiro_hook_dst = target / ".kiro" / "hooks" / "faultline-gate.json"
    kiro_hook_src = repo_root / ".kiro" / "hooks" / "faultline-gate.json"

    if enable_kiro:
        for s in skills:
            check_dir_collision(kiro_skills_dst / s)
        kiro_agents_src = repo_root / ".kiro" / "agents"
        if kiro_agents_src.is_dir():
            for f in kiro_agents_src.glob("faultline-*.md"):
                check_file_collision(kiro_agents_dst / f.name)
        if not is_global and kiro_hook_src.is_file():
            check_file_collision(kiro_hook_dst)

    # 5. Cursor
    cursor_rule_dst = target / ".cursor" / "rules" / "faultline.mdc"
    cursor_rule_src = repo_root / ".cursor" / "rules" / "faultline.mdc"
    if enable_cursor and cursor_rule_src.is_file():
        check_file_collision(cursor_rule_dst)

    # 6. Copilot
    copilot_instructions_dst = target / ".github" / "copilot-instructions.md"
    copilot_snippet = repo_root / "integrations" / "copilot-instructions.md.snippet"
    if enable_copilot and copilot_snippet.is_file():
        err = check_delimited_collision(copilot_instructions_dst, force=force)
        if err:
            collision_errors.append(err)

    if collision_errors:
        for err in collision_errors:
            print(err, file=sys.stderr)
        return 1

    # Dry-Run Reporting
    if dry_run:
        ag_agent_files = [f.name for f in sorted((repo_root / ".agents" / "agents").glob("faultline-*.md"))] if enable_antigravity_agents else []
        oc_agent_files = [f.name for f in sorted((repo_root / ".opencode" / "agents").glob("faultline-*.md"))] if enable_opencode else []

        print(f"Would install skills: {' '.join(skills)}")
        print(f"Would install Antigravity agents: {' '.join(ag_agent_files) if ag_agent_files else '(none)'}")
        print(f"Would install OpenCode agents: {' '.join(oc_agent_files) if oc_agent_files else '(none)'}")
        if not is_global and enable_antigravity:
            print(f"Would append/refresh only the marked Faultline block in: {agents_md}")
        if enable_claude:
            print(f"Would install Claude Code adapters into: {target / '.claude'}")
            if not is_global:
                print(f"Would append/refresh only the marked Faultline block in: {claude_md}")
        if enable_kiro:
            if is_global:
                print(f"Would install Kiro adapters into: {target / '.kiro'}")
            else:
                print(f"Would install Kiro adapters and hooks into: {target / '.kiro'}")
        if enable_cursor:
            print(f"Would install Cursor rule: {cursor_rule_dst}")
        if enable_copilot:
            print(f"Would append/refresh only the marked Faultline block in: {copilot_instructions_dst}")
        return 0

    # Execution Phase
    # 1. Antigravity skills & agents
    if enable_antigravity:
        ag_skills_dst.mkdir(parents=True, exist_ok=True)
        for s in skills:
            dst = ag_skills_dst / s
            safe_rmpath(dst)
            shutil.copytree(skills_source / s, dst)
            print(f"Installed skill: {s}")

        if enable_antigravity_agents:
            ag_agents_dst.mkdir(parents=True, exist_ok=True)
            ag_agents_src = repo_root / ".agents" / "agents"
            for f in sorted(ag_agents_src.glob("faultline-*.md")):
                safe_rmpath(ag_agents_dst / f.name)
                shutil.copy2(f, ag_agents_dst / f.name)

        if not is_global and ag_snippet.is_file():
            ok, msg = update_delimited_file(agents_md, ag_snippet, force=force, dry_run=False)
            if not ok:
                print(msg, file=sys.stderr)
                return 1
            print(msg)

    # 2. OpenCode agents
    if enable_opencode:
        oc_agents_dst.mkdir(parents=True, exist_ok=True)
        oc_agents_src = repo_root / ".opencode" / "agents"
        for f in sorted(oc_agents_src.glob("faultline-*.md")):
            safe_rmpath(oc_agents_dst / f.name)
            shutil.copy2(f, oc_agents_dst / f.name)

    # 3. Claude Code
    if enable_claude:
        claude_skills_dst.mkdir(parents=True, exist_ok=True)
        for s in skills:
            dst = claude_skills_dst / s
            safe_rmpath(dst)
            shutil.copytree(skills_source / s, dst)
        claude_agents_dst.mkdir(parents=True, exist_ok=True)
        claude_agents_src = repo_root / ".claude" / "agents"
        for f in sorted(claude_agents_src.glob("faultline-*.md")):
            safe_rmpath(claude_agents_dst / f.name)
            shutil.copy2(f, claude_agents_dst / f.name)
        if not is_global and claude_snippet.is_file():
            ok, msg = update_delimited_file(claude_md, claude_snippet, force=force, dry_run=False)
            if not ok:
                print(msg, file=sys.stderr)
                return 1
            print(msg)

    # 4. Amazon Kiro
    if enable_kiro:
        kiro_skills_dst.mkdir(parents=True, exist_ok=True)
        for s in skills:
            dst = kiro_skills_dst / s
            safe_rmpath(dst)
            shutil.copytree(skills_source / s, dst)
        kiro_agents_dst.mkdir(parents=True, exist_ok=True)
        kiro_agents_src = repo_root / ".kiro" / "agents"
        for f in sorted(kiro_agents_src.glob("faultline-*.md")):
            safe_rmpath(kiro_agents_dst / f.name)
            shutil.copy2(f, kiro_agents_dst / f.name)
        if not is_global and kiro_hook_src.is_file():
            kiro_hook_dst.parent.mkdir(parents=True, exist_ok=True)
            safe_rmpath(kiro_hook_dst)
            shutil.copy2(kiro_hook_src, kiro_hook_dst)
            print(f"Installed Kiro hook: {kiro_hook_dst}")

    # 5. Cursor
    if enable_cursor and cursor_rule_src.is_file():
        cursor_rule_dst.parent.mkdir(parents=True, exist_ok=True)
        safe_rmpath(cursor_rule_dst)
        shutil.copy2(cursor_rule_src, cursor_rule_dst)
        print(f"Installed Cursor rule: {cursor_rule_dst}")

    # 6. Copilot
    if enable_copilot and copilot_snippet.is_file():
        ok, msg = update_delimited_file(copilot_instructions_dst, copilot_snippet, force=force, dry_run=False)
        if not ok:
            print(msg, file=sys.stderr)
            return 1
        print(msg)

    print(f"Faultline {version} installed into {target}")
    print("Reload the agent. Use faultline-preflight or faultline-break-sweep; review changes before committing.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install/update portable Faultline skills, native agent adapters, and integration gates.",
        add_help=True,
    )
    parser.add_argument("target", nargs="?", default=None, help="Target project directory")
    parser.add_argument("--global", dest="is_global", action="store_true", help="Install into global user directory (~/.agents/skills/, etc.)")
    parser.add_argument("--dry-run", action="store_true", help="Preview intended changes only.")
    parser.add_argument("--force", action="store_true", help="Replace existing Faultline-owned skills/agent files and refresh marked blocks.")
    parser.add_argument("--all", dest="install_all", action="store_true", help="Install all environment adapters regardless of auto-detection.")
    parser.add_argument("--no-antigravity", action="store_true", help="Skip .agents/ skills and adapters.")
    parser.add_argument("--no-antigravity-agents", action="store_true", help="Skip .agents/agents/ adapters.")
    parser.add_argument("--no-opencode", action="store_true", help="Skip .opencode/agents/ adapters.")
    parser.add_argument("--no-opencode-agents", dest="no_opencode", action="store_true", help="Alias for --no-opencode.")
    parser.add_argument("--no-claude", action="store_true", help="Skip Claude Code skills and adapters.")
    parser.add_argument("--no-kiro", action="store_true", help="Skip Kiro skills and adapters.")
    parser.add_argument("--no-cursor", action="store_true", help="Skip Cursor rules.")
    parser.add_argument("--no-copilot", action="store_true", help="Skip GitHub Copilot instructions.")

    args = parser.parse_args()

    exit_code = install(
        target_arg=args.target,
        is_global=args.is_global,
        dry_run=args.dry_run,
        force=args.force,
        install_all=args.install_all,
        no_antigravity=args.no_antigravity,
        no_antigravity_agents=args.no_antigravity_agents,
        no_opencode=args.no_opencode,
        no_claude=args.no_claude,
        no_kiro=args.no_kiro,
        no_cursor=args.no_cursor,
        no_copilot=args.no_copilot,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
