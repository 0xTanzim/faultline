#!/usr/bin/env python3
"""Cross-platform installer for Faultline portable skills, native agent adapters, and integration gates.

Dynamically renders host adapters directly from definitions/specialists.json at install time.
Supports project scope, global user scope, dry-run, force refresh, and clean uninstallation.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import sys

# Ensure repo root is in python path to import build_adapters
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_adapters import (
    load_definitions,
    validate_definitions,
    build_host_adapters,
    RENDERERS,
)

START_MARKER = "<!-- faultline:start -->"
END_MARKER = "<!-- faultline:end -->"
RE_START_MARKER = re.compile(r"<!--\s*faultline:start\s*-->")
RE_END_MARKER = re.compile(r"<!--\s*faultline:end\s*-->")


def get_repo_root() -> Path:
    return REPO_ROOT


def get_version(repo_root: Path) -> str:
    version_file = repo_root / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.5.0-beta.1"


def find_skills(repo_root: Path) -> list[str]:
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
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


def remove_delimited_block(text: str) -> str:
    """Safely strip only the marked Faultline block from text, leaving all surrounding content intact."""
    start_matches = list(RE_START_MARKER.finditer(text))
    end_matches = list(RE_END_MARKER.finditer(text))

    if len(start_matches) == 1 and len(end_matches) == 1 and start_matches[0].start() < end_matches[0].end():
        start_m = start_matches[0]
        end_m = end_matches[0]
        line_start = text.rfind("\n", 0, start_m.start())
        prefix = text[: line_start + 1 if line_start != -1 else 0].rstrip()
        line_end = text.find("\n", end_m.end())
        suffix = text[line_end + 1 if line_end != -1 else len(text) :].lstrip("\r\n")

        parts = [p for p in [prefix, suffix] if p]
        return "\n\n".join(parts) + ("\n" if parts else "")
    return text


def update_delimited_file(file_path: Path, snippet_path: Path, force: bool, dry_run: bool) -> tuple[bool, str]:
    """Check and update a delimited marker file (e.g. AGENTS.md, CLAUDE.md)."""
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


def uninstall(target_arg: str | None, is_global: bool, dry_run: bool) -> int:
    """Cleanly remove Faultline skills, generated adapters, and delimited rule blocks."""
    repo_root = get_repo_root()
    version = get_version(repo_root)

    if is_global and target_arg:
        print("ERROR: Cannot specify both a target directory and --global.", file=sys.stderr)
        return 2

    if not is_global and not target_arg:
        target = Path.cwd()
        scope_name = f"project directory: {target}"
    elif is_global:
        target = Path.home()
        scope_name = f"user global directory: {target}"
    else:
        target = Path(target_arg).resolve()
        scope_name = f"project directory: {target}"

    skills = find_skills(repo_root)
    try:
        specs = load_definitions(repo_root / "definitions" / "specialists.json")
    except Exception:
        specs = []

    actions: list[str] = []

    def remove_file(f: Path) -> None:
        if f.is_file() or f.is_symlink():
            if dry_run:
                actions.append(f"Would delete file: {f}")
            else:
                f.unlink()
                actions.append(f"Deleted file: {f}")

    def remove_dir(d: Path) -> None:
        if d.is_dir() or d.is_symlink():
            if dry_run:
                actions.append(f"Would delete directory: {d}")
            else:
                safe_rmpath(d)
                actions.append(f"Deleted directory: {d}")

    def strip_marker_file(f: Path) -> None:
        if not f.is_file():
            return
        text = f.read_text(encoding="utf-8")
        if START_MARKER in text and END_MARKER in text:
            cleaned = remove_delimited_block(text)
            if dry_run:
                actions.append(f"Would remove marked Faultline block from: {f}")
            else:
                if not cleaned.strip():
                    f.unlink()
                    actions.append(f"Deleted empty rule file after stripping markers: {f}")
                else:
                    f.write_text(cleaned, encoding="utf-8")
                    actions.append(f"Stripped marked Faultline block from: {f}")

    # 1. Skills removal
    for s in skills:
        remove_dir(target / ".agents" / "skills" / s)
        remove_dir(target / ".claude" / "skills" / s)
        remove_dir(target / ".kiro" / "skills" / s)

    # 2. Host adapters removal
    for spec in specs:
        fname = f"{spec['name']}.md"
        remove_file(target / ".agents" / "agents" / fname)
        remove_file(target / ".claude" / "agents" / fname)
        remove_file(target / ".kiro" / "agents" / fname)
        remove_file(target / ".opencode" / "agents" / fname)
    remove_file(target / ".opencode" / "agents" / "faultline-orchestrator.md")

    # 3. Rules and hooks removal
    remove_file(target / ".cursor" / "rules" / "faultline.mdc")
    remove_file(target / ".kiro" / "hooks" / "faultline-gate.json")

    # 4. Marker blocks stripping
    strip_marker_file(target / "AGENTS.md")
    strip_marker_file(target / "CLAUDE.md")
    strip_marker_file(target / ".github" / "copilot-instructions.md")

    # 5. Prune empty parent directories
    def prune_empty(d: Path) -> None:
        if d.is_dir() and not any(d.iterdir()):
            if not dry_run:
                try:
                    d.rmdir()
                    actions.append(f"Pruned empty directory: {d}")
                except Exception:
                    pass

    prune_empty(target / ".agents" / "skills")
    prune_empty(target / ".agents" / "agents")
    prune_empty(target / ".agents")
    prune_empty(target / ".claude" / "skills")
    prune_empty(target / ".claude" / "agents")
    prune_empty(target / ".claude")
    prune_empty(target / ".kiro" / "skills")
    prune_empty(target / ".kiro" / "agents")
    prune_empty(target / ".kiro" / "hooks")
    prune_empty(target / ".kiro")
    prune_empty(target / ".opencode" / "agents")
    prune_empty(target / ".opencode")
    prune_empty(target / ".cursor" / "rules")
    prune_empty(target / ".cursor")

    status_word = "Would uninstall" if dry_run else "Uninstalled"
    print(f"Faultline {version} {status_word} from {scope_name}")
    if actions:
        for act in actions:
            print(f"  - {act}")
    else:
        print("  (no Faultline files or rule blocks found)")

    return 0


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
        home = Path.home()
        target = home
        scope_name = f"user global directory: {home}"
    else:
        target = Path(target_arg).resolve()
        scope_name = f"project directory: {target}"

    skills = find_skills(repo_root)
    if not skills:
        print(f"ERROR: No skills found in {repo_root / 'skills'}", file=sys.stderr)
        return 1

    try:
        specs = load_definitions(repo_root / "definitions" / "specialists.json")
    except Exception as e:
        print(f"ERROR: Cannot load specialist definitions: {e}", file=sys.stderr)
        return 1

    valid, msg = validate_definitions(specs)
    if not valid:
        print(f"ERROR: Specialist definitions invalid: {msg}", file=sys.stderr)
        return 1

    # Auto-detection triggers
    has_claude_marker = (target / ".claude").is_dir() or (target / "CLAUDE.md").is_file()
    has_kiro_marker = (target / ".kiro").is_dir()
    has_cursor_marker = (target / ".cursor").is_dir() or (target / ".cursorrules").is_file()
    has_copilot_marker = (target / ".github").is_dir()

    enable_antigravity = not no_antigravity
    enable_antigravity_agents = enable_antigravity and not no_antigravity_agents
    enable_opencode = not no_opencode
    enable_claude = (install_all or has_claude_marker or is_global) and not no_claude
    enable_kiro = (install_all or has_kiro_marker or is_global) and not no_kiro
    enable_cursor = (install_all or has_cursor_marker) and not no_cursor and not is_global
    enable_copilot = (install_all or has_copilot_marker) and not no_copilot and not is_global

    # Templates location
    templates_root = repo_root / "templates"
    ag_snippet = templates_root / "snippets" / "AGENTS.md.snippet"
    claude_snippet = templates_root / "snippets" / "CLAUDE.md.snippet"
    copilot_snippet = templates_root / "snippets" / "copilot-instructions.md.snippet"
    cursor_rule_template = templates_root / "cursor" / "faultline.mdc"
    kiro_hook_template = templates_root / "kiro" / "faultline-gate.json"

    # Collision pre-flight checks
    collision_errors: list[str] = []

    def check_file_collision(dest: Path) -> None:
        if (dest.exists() or dest.is_symlink()) and not force:
            collision_errors.append(f"ERROR: Destination already exists: {dest}. Use --force to replace it.")

    def check_dir_collision(dest: Path) -> None:
        if (dest.exists() or dest.is_symlink()) and not force:
            collision_errors.append(f"ERROR: Destination directory already exists: {dest}. Use --force to replace it.")

    # 1. Antigravity Skills & Dynamic Agents
    ag_skills_dst = target / ".agents" / "skills"
    ag_agents_dst = target / ".agents" / "agents"
    agents_md = target / "AGENTS.md"

    if enable_antigravity:
        for s in skills:
            check_dir_collision(ag_skills_dst / s)
        if enable_antigravity_agents:
            for spec in specs:
                check_file_collision(ag_agents_dst / f"{spec['name']}.md")
        if not is_global and ag_snippet.is_file():
            err = check_delimited_collision(agents_md, force=force)
            if err:
                collision_errors.append(err)

    # 2. OpenCode Dynamic Agents
    oc_agents_dst = target / ".opencode" / "agents"
    if enable_opencode:
        for spec in specs:
            check_file_collision(oc_agents_dst / f"{spec['name']}.md")
        check_file_collision(oc_agents_dst / "faultline-orchestrator.md")

    # 3. Claude Code
    claude_skills_dst = target / ".claude" / "skills"
    claude_agents_dst = target / ".claude" / "agents"
    claude_md = target / "CLAUDE.md"

    if enable_claude:
        for s in skills:
            check_dir_collision(claude_skills_dst / s)
        for spec in specs:
            check_file_collision(claude_agents_dst / f"{spec['name']}.md")
        if not is_global and claude_snippet.is_file():
            err = check_delimited_collision(claude_md, force=force)
            if err:
                collision_errors.append(err)

    # 4. Amazon Kiro
    kiro_skills_dst = target / ".kiro" / "skills"
    kiro_agents_dst = target / ".kiro" / "agents"
    kiro_hook_dst = target / ".kiro" / "hooks" / "faultline-gate.json"

    if enable_kiro:
        for s in skills:
            check_dir_collision(kiro_skills_dst / s)
        for spec in specs:
            check_file_collision(kiro_agents_dst / f"{spec['name']}.md")
        if not is_global and kiro_hook_template.is_file():
            check_file_collision(kiro_hook_dst)

    # 5. Cursor
    cursor_rule_dst = target / ".cursor" / "rules" / "faultline.mdc"
    if enable_cursor and cursor_rule_template.is_file():
        check_file_collision(cursor_rule_dst)

    # 6. Copilot
    copilot_instructions_dst = target / ".github" / "copilot-instructions.md"
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
        spec_names = [f"{s['name']}.md" for s in specs]
        print(f"Would install skills: {' '.join(skills)}")
        print(f"Would dynamically render Antigravity agents: {' '.join(spec_names) if enable_antigravity_agents else '(none)'}")
        print(f"Would dynamically render OpenCode agents: {' '.join(spec_names + ['faultline-orchestrator.md']) if enable_opencode else '(none)'}")
        if not is_global and enable_antigravity:
            print(f"Would append/refresh only the marked Faultline block in: {agents_md}")
        if enable_claude:
            print(f"Would dynamically render Claude Code adapters into: {target / '.claude'}")
            if not is_global:
                print(f"Would append/refresh only the marked Faultline block in: {claude_md}")
        if enable_kiro:
            if is_global:
                print(f"Would dynamically render Kiro adapters into: {target / '.kiro'}")
            else:
                print(f"Would dynamically render Kiro adapters and hooks into: {target / '.kiro'}")
        if enable_cursor:
            print(f"Would install Cursor rule into: {cursor_rule_dst}")
        if enable_copilot:
            print(f"Would append/refresh only the marked Faultline block in: {copilot_instructions_dst}")
        return 0

    # Execute Installation
    installed_actions: list[str] = []
    source_skills_dir = repo_root / "skills"
    if not source_skills_dir.is_dir():
        source_skills_dir = repo_root / ".agents" / "skills"

    def install_skill_dir(src: Path, dst: Path) -> None:
        if dst.exists() or dst.is_symlink():
            safe_rmpath(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)

    # 1. Antigravity Skills & Dynamic Agents
    if enable_antigravity:
        for s in skills:
            src = source_skills_dir / s
            dst = ag_skills_dst / s
            install_skill_dir(src, dst)
            installed_actions.append(f"Installed {s} -> {dst}")

        if enable_antigravity_agents:
            build_host_adapters("antigravity", ag_agents_dst, specs, dry_run=False)
            installed_actions.append(f"Dynamically generated Antigravity adapters ({len(specs)} roles) -> {ag_agents_dst}")

        if not is_global and ag_snippet.is_file():
            changed, msg = update_delimited_file(agents_md, ag_snippet, force=force, dry_run=False)
            if changed:
                installed_actions.append(msg)

    # 2. OpenCode Dynamic Agents
    if enable_opencode:
        build_host_adapters("opencode", oc_agents_dst, specs, dry_run=False)
        installed_actions.append(f"Dynamically generated OpenCode adapters ({len(specs) + 1} agents) -> {oc_agents_dst}")

    # 3. Claude Code
    if enable_claude:
        for s in skills:
            src = source_skills_dir / s
            dst = claude_skills_dst / s
            install_skill_dir(src, dst)
            installed_actions.append(f"Installed {s} -> {dst}")

        build_host_adapters("claude", claude_agents_dst, specs, dry_run=False)
        installed_actions.append(f"Dynamically generated Claude Code adapters ({len(specs)} roles) -> {claude_agents_dst}")

        if not is_global and claude_snippet.is_file():
            changed, msg = update_delimited_file(claude_md, claude_snippet, force=force, dry_run=False)
            if changed:
                installed_actions.append(msg)

    # 4. Amazon Kiro
    if enable_kiro:
        for s in skills:
            src = source_skills_dir / s
            dst = kiro_skills_dst / s
            install_skill_dir(src, dst)
            installed_actions.append(f"Installed {s} -> {dst}")

        build_host_adapters("kiro", kiro_agents_dst, specs, dry_run=False)
        installed_actions.append(f"Dynamically generated Kiro adapters ({len(specs)} roles) -> {kiro_agents_dst}")

        if not is_global and kiro_hook_template.is_file():
            if kiro_hook_dst.exists() or kiro_hook_dst.is_symlink():
                safe_rmpath(kiro_hook_dst)
            kiro_hook_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(kiro_hook_template, kiro_hook_dst)
            installed_actions.append(f"Installed Kiro gate hook -> {kiro_hook_dst}")

    # 5. Cursor
    if enable_cursor and cursor_rule_template.is_file():
        if cursor_rule_dst.exists() or cursor_rule_dst.is_symlink():
            safe_rmpath(cursor_rule_dst)
        cursor_rule_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cursor_rule_template, cursor_rule_dst)
        installed_actions.append(f"Installed Cursor preflight rule -> {cursor_rule_dst}")

    # 6. Copilot
    if enable_copilot and copilot_snippet.is_file():
        changed, msg = update_delimited_file(copilot_instructions_dst, copilot_snippet, force=force, dry_run=False)
        if changed:
            installed_actions.append(msg)

    print(f"Faultline {version} installed successfully to {scope_name}")
    for act in installed_actions:
        print(f"  + {act}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-platform installer for Faultline skills, dynamic host adapters, and integration gates."
    )
    parser.add_argument("target", nargs="?", default=None, help="Target project directory")
    parser.add_argument("--global", dest="is_global", action="store_true", help="Install to user home directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview planned actions without modifying files")
    parser.add_argument("--force", action="store_true", help="Replace existing files and refresh marked instruction blocks")
    parser.add_argument("--uninstall", action="store_true", help="Cleanly remove Faultline skills, adapters, rules, and markers")
    parser.add_argument("--all", dest="install_all", action="store_true", help="Install adapters for all supported environments")
    parser.add_argument("--no-antigravity", action="store_true", help="Skip Google Antigravity skills, adapters, and AGENTS.md")
    parser.add_argument("--no-antigravity-agents", action="store_true", help="Skip Antigravity .agents/agents/ adapters only")
    parser.add_argument("--no-opencode", action="store_true", help="Skip OpenCode .opencode/agents/ adapters")
    parser.add_argument("--no-claude", action="store_true", help="Skip Claude Code skills, adapters, and CLAUDE.md")
    parser.add_argument("--no-kiro", action="store_true", help="Skip Amazon Kiro skills, adapters, and hooks")
    parser.add_argument("--no-cursor", action="store_true", help="Skip Cursor .cursor/rules/faultline.mdc")
    parser.add_argument("--no-copilot", action="store_true", help="Skip GitHub Copilot instructions")

    args = parser.parse_args()

    if args.uninstall:
        return uninstall(
            target_arg=args.target,
            is_global=args.is_global,
            dry_run=args.dry_run,
        )

    return install(
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


if __name__ == "__main__":
    sys.exit(main())
