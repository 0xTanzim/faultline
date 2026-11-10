#!/usr/bin/env python3
"""Lightweight structural validation of portable skills and host adapters."""
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]; errors=[]
for d in sorted((ROOT/'.agents/skills').glob('*')):
    if not d.is_dir(): continue
    p=d/'SKILL.md'
    if not p.is_file(): errors.append(f'{d}: missing SKILL.md'); continue
    s=p.read_text(encoding='utf-8')
    if not s.startswith('---\n') or '\n---\n' not in s[4:]: errors.append(f'{p}: invalid/unterminated YAML frontmatter'); continue
    fm=s[4:s.find('\n---\n',4)]
    m=re.search(r'^name:\s*([a-z0-9-]+)\s*$',fm,re.M)
    if not m: errors.append(f'{p}: missing/invalid name')
    elif m.group(1)!=d.name: errors.append(f'{p}: frontmatter name does not match directory')
    if not re.search(r'^description:\s*>?-?\s*\S',fm,re.M): errors.append(f'{p}: missing description')
    if len(s.splitlines())>500: print(f'WARN {p}: over 500 lines; move detail to references')
for p in sorted((ROOT/'.agents/agents').glob('*.md')):
    s=p.read_text(encoding='utf-8')
    if not s.startswith('---\n') or '\n---\n' not in s[4:]: errors.append(f'{p}: missing frontmatter')
    elif not re.search(r'^subagent:\s*true\s*$',s,re.M): errors.append(f'{p}: missing Antigravity subagent: true')
for p in sorted((ROOT/'.opencode/agents').glob('*.md')):
    s=p.read_text(encoding='utf-8')
    if not s.startswith('---\n') or '\n---\n' not in s[4:]: errors.append(f'{p}: missing frontmatter')
    elif 'mode:' not in s.split('\n---\n',1)[0]: errors.append(f'{p}: missing OpenCode mode')
if errors: print('\n'.join('ERROR '+e for e in errors)); sys.exit(1)
print('Portable skills and host adapters: structurally valid')
