#!/usr/bin/env python3
"""Structural validation of portable skills, symlinks, definitions, and host adapters."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []

# 1. Validate canonical root skills/ directory
canonical_skills = ROOT / "skills"
if not canonical_skills.is_dir():
    errors.append(f"{canonical_skills}: root skills/ directory does not exist or is not a directory")
else:
    for d in sorted(canonical_skills.glob("*")):
        if not d.is_dir():
            continue
        p = d / "SKILL.md"
        if not p.is_file():
            errors.append(f"{d}: missing SKILL.md")
            continue
        s = p.read_text(encoding="utf-8")
        if not s.startswith("---\n") or "\n---\n" not in s[4:]:
            errors.append(f"{p}: invalid/unterminated YAML frontmatter")
            continue
        fm = s[4 : s.find("\n---\n", 4)]
        m = re.search(r"^name:\s*([a-z0-9-]+)\s*$", fm, re.M)
        if not m:
            errors.append(f"{p}: missing/invalid name")
        elif m.group(1) != d.name:
            errors.append(f"{p}: frontmatter name does not match directory")
        if not re.search(r"^description:\s*>?-?\s*\S", fm, re.M):
            errors.append(f"{p}: missing description")
        if len(s.splitlines()) > 500:
            print(f"WARN {p}: over 500 lines; move detail to references")

# 2. Validate .agents/skills symlink
agents_skills_link = ROOT / ".agents" / "skills"
if not agents_skills_link.is_symlink():
    errors.append(f"{agents_skills_link}: expected a symlink pointing to ../skills")
else:
    target_resolved = agents_skills_link.resolve()
    if target_resolved != canonical_skills.resolve():
        errors.append(f"{agents_skills_link}: symlink resolves to {target_resolved}, expected {canonical_skills.resolve()}")

# 3. Validate definitions/specialists.json Single Source of Truth
specialists_file = ROOT / "definitions" / "specialists.json"
if not specialists_file.is_file():
    errors.append(f"{specialists_file}: missing definitions/specialists.json")
else:
    try:
        with open(specialists_file, "r", encoding="utf-8") as f:
            specs = json.load(f)
        if not isinstance(specs, list) or len(specs) != 6:
            errors.append(f"{specialists_file}: expected exactly 6 specialist definitions")
        else:
            required_keys = {"id", "name", "title", "description", "role_prompt", "tools", "execution_policy"}
            for idx, spec in enumerate(specs):
                missing = required_keys - set(spec.keys())
                if missing:
                    errors.append(f"{specialists_file}[{idx}]: missing required keys {missing}")
                if spec.get("name") != f"faultline-{spec.get('id')}":
                    errors.append(f"{specialists_file}[{idx}]: name '{spec.get('name')}' does not match 'faultline-{spec.get('id')}'")
                if not isinstance(spec.get("tools"), list) or not spec["tools"]:
                    errors.append(f"{specialists_file}[{idx}]: 'tools' must be a non-empty list")
    except Exception as e:
        errors.append(f"{specialists_file}: invalid JSON: {e}")

# 4. Validate host agent adapters
# Antigravity
for p in sorted((ROOT / ".agents" / "agents").glob("*.md")):
    s = p.read_text(encoding="utf-8")
    if not s.startswith("---\n") or "\n---\n" not in s[4:]:
        errors.append(f"{p}: missing frontmatter")
    elif not re.search(r"^subagent:\s*true\s*$", s, re.M):
        errors.append(f"{p}: missing Antigravity subagent: true")

# OpenCode
for p in sorted((ROOT / ".opencode" / "agents").glob("*.md")):
    s = p.read_text(encoding="utf-8")
    if not s.startswith("---\n") or "\n---\n" not in s[4:]:
        errors.append(f"{p}: missing frontmatter")
    elif "mode:" not in s.split("\n---\n", 1)[0]:
        errors.append(f"{p}: missing OpenCode mode")

# Claude Code
for p in sorted((ROOT / ".claude" / "agents").glob("*.md")):
    s = p.read_text(encoding="utf-8")
    if not s.startswith("---\n") or "\n---\n" not in s[4:]:
        errors.append(f"{p}: missing frontmatter")
    else:
        fm = s.split("\n---\n", 1)[0]
        if "description:" not in fm:
            errors.append(f"{p}: missing description in Claude agent frontmatter")

# Amazon Kiro
for p in sorted((ROOT / ".kiro" / "agents").glob("*.md")):
    s = p.read_text(encoding="utf-8")
    if not s.startswith("---\n") or "\n---\n" not in s[4:]:
        errors.append(f"{p}: missing frontmatter")
    else:
        fm = s.split("\n---\n", 1)[0]
        if "description:" not in fm:
            errors.append(f"{p}: missing description in Kiro agent frontmatter")

# 5. Validate Integration Templates and Rules
integration_snippets = [
    ROOT / "integrations" / "AGENTS.md.snippet",
    ROOT / "integrations" / "CLAUDE.md.snippet",
    ROOT / "integrations" / "copilot-instructions.md.snippet",
]
for snip in integration_snippets:
    if not snip.is_file():
        errors.append(f"{snip}: missing integration snippet")
    else:
        txt = snip.read_text(encoding="utf-8")
        if "<!-- faultline:start -->" not in txt or "<!-- faultline:end -->" not in txt:
            errors.append(f"{snip}: missing faultline marker boundaries")

cursor_rule = ROOT / ".cursor" / "rules" / "faultline.mdc"
if not cursor_rule.is_file():
    errors.append(f"{cursor_rule}: missing Cursor rule")
else:
    c_txt = cursor_rule.read_text(encoding="utf-8")
    if not c_txt.startswith("---\n") or "\n---\n" not in c_txt[4:]:
        errors.append(f"{cursor_rule}: invalid YAML frontmatter")

kiro_hook = ROOT / ".kiro" / "hooks" / "faultline-gate.json"
if not kiro_hook.is_file():
    errors.append(f"{kiro_hook}: missing Kiro hook configuration")
else:
    try:
        with open(kiro_hook, "r", encoding="utf-8") as f:
            kh = json.load(f)
        if "events" not in kh or "action" not in kh:
            errors.append(f"{kiro_hook}: missing 'events' or 'action' property")
    except Exception as e:
        errors.append(f"{kiro_hook}: invalid JSON: {e}")

# 6. Check zero drift with build_adapters.py --check
res = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_adapters.py"), "--check"], capture_output=True, text=True)
if res.returncode != 0:
    errors.append(f"Adapter parity check failed:\n{res.stderr.strip() or res.stdout.strip()}")

if errors:
    print("\n".join("ERROR " + e for e in errors), file=sys.stderr)
    sys.exit(1)

print("Portable skills, definitions, and host adapters: structurally valid")
