#!/usr/bin/env python3
"""Structural validation of portable skills, symlinks, definitions, templates, and dynamic compilation."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_adapters import (
    load_definitions,
    validate_definitions,
    build_host_adapters,
    RENDERERS,
)

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
        specs = load_definitions(specialists_file)
        valid, msg = validate_definitions(specs)
        if not valid:
            errors.append(f"{specialists_file}: {msg}")
    except Exception as e:
        errors.append(f"{specialists_file}: invalid JSON: {e}")

# 4. Validate Templates and Reusable Rules
templates_root = ROOT / "templates"
snippets = [
    templates_root / "snippets" / "AGENTS.md.snippet",
    templates_root / "snippets" / "CLAUDE.md.snippet",
    templates_root / "snippets" / "copilot-instructions.md.snippet",
]
for snip in snippets:
    if not snip.is_file():
        errors.append(f"{snip}: missing template snippet")
    else:
        txt = snip.read_text(encoding="utf-8")
        if "<!-- faultline:start -->" not in txt or "<!-- faultline:end -->" not in txt:
            errors.append(f"{snip}: missing faultline marker boundaries")

cursor_rule = templates_root / "cursor" / "faultline.mdc"
if not cursor_rule.is_file():
    errors.append(f"{cursor_rule}: missing Cursor rule template")
else:
    c_txt = cursor_rule.read_text(encoding="utf-8")
    if not c_txt.startswith("---\n") or "\n---\n" not in c_txt[4:]:
        errors.append(f"{cursor_rule}: invalid YAML frontmatter")

kiro_hook = templates_root / "kiro" / "faultline-gate.json"
if not kiro_hook.is_file():
    errors.append(f"{kiro_hook}: missing Kiro hook template")
else:
    try:
        with open(kiro_hook, "r", encoding="utf-8") as f:
            kh = json.load(f)
        if "events" not in kh or "action" not in kh:
            errors.append(f"{kiro_hook}: missing 'events' or 'action' property")
    except Exception as e:
        errors.append(f"{kiro_hook}: invalid JSON: {e}")

# 5. Validate Dynamic Adapter Compilation in Memory (DRY verification)
if specialists_file.is_file():
    try:
        specs = load_definitions(specialists_file)
        for host in ["antigravity", "opencode", "claude", "kiro"]:
            renderer = RENDERERS[host]
            for spec in specs:
                out = renderer(spec)
                if not out.startswith("---\n") or "\n---\n" not in out[4:]:
                    errors.append(f"Dynamic renderer for {host}/{spec['name']} produced invalid YAML frontmatter")
    except Exception as e:
        errors.append(f"Dynamic renderer check failed: {e}")

if errors:
    print("Portable skills, definitions, and templates: INVALID", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)

print("Portable skills, definitions, templates, and dynamic compilers: structurally valid")
